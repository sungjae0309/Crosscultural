"""협업 필터링(ALS)과 "CF + 나라 인기" 섞기 평가 (report/실험설계.md 6, 6.1, 9절).

섞은 점수 = (1 - w) * CF 점수 + w * 나라 인기
- 두 점수 모두 사용자마다 그 조건의 순위 대상 안에서 최소-최대로 0~1에 맞춘다.
- ALS 학습에 없던 아티스트는 CF 점수가 없으므로 최솟값(변환 후 0)으로 둔다.
- 나라 인기는 초기 사용자로만 만든 값이라 순위 대상 대부분이 0이다. 그래서 최소-최대 변환은 최댓값으로 나누기와 같다.
- 보여준 아티스트 중 ALS에 있는 것만으로 사용자 벡터를 계산한다 (fold-in).
  쓸 수 있는 것이 하나도 없으면 그 사용자의 CF 점수 대신 그 조건의 전체 인기를 쓴다.

빠른 계산 (결과는 전체 계산과 같다)
- 사용자마다 후보 = CF 상위 A개 ∪ 나라 인기 상위 A개. 보여준 아티스트는 뺀다.
- 후보 밖 아티스트의 섞은 점수는 (1 - w) * (CF A번째 값) + w * (나라 인기 A번째 값)을 넘을 수 없다.
  이 상한이 후보 중 K번째 점수보다 작고 후보 상위 K+1개에 동점이 없을 때만 후보 안에서 순위를 정한다.
  아니면 그 사용자만 전체 순위 대상으로 metrics.top_k를 써서 계산한다.
- w = 1이면 CF를 쓰지 않으므로 모두에게 같은 순위가 되어 popularity.evaluate_shared_scores로 계산한다.
"""

from dataclasses import dataclass

import numpy as np
from implicit.cpu.als import AlternatingLeastSquares
from scipy import sparse

from config import CF_ITERATIONS, RANDOM_SEED
from metrics import top_k
from popularity import evaluate_shared_scores

CANDIDATES_PER_SOURCE = 100


# ---------- 모델 ----------


@dataclass
class CFModel:
    item_factors: np.ndarray  # universe 길이 × 요인 수
    in_model: np.ndarray  # ALS 학습 자료에 한 번이라도 나온 아티스트 (universe 길이)
    regularization: float

    def __post_init__(self):
        # 점수 계산은 float64로 한다. 계산 경로가 달라도(행렬곱, 벡터곱) 값이 거의 같게 하려고
        self.item_factors64 = np.asarray(self.item_factors, dtype=np.float64)

    def solver(self):
        """fold-in 계산용 ALS 객체."""
        als = AlternatingLeastSquares(
            factors=self.item_factors.shape[1], regularization=self.regularization, random_state=RANDOM_SEED
        )
        als.item_factors = self.item_factors
        return als

    def save(self, path):
        np.savez(path, item_factors=self.item_factors, in_model=self.in_model, regularization=self.regularization)

    @classmethod
    def load(cls, path):
        stored = np.load(path)
        return cls(stored["item_factors"], stored["in_model"], float(stored["regularization"]))


def train_matrix(data, countries):
    """주어진 나라들의 학습 사용자 × universe 행렬. 들었으면 1."""
    users = [user for iso3 in sorted(countries) for user in data.train_users[iso3]]
    items = [data.train_items[user] for user in users]
    indptr = np.r_[0, np.cumsum([len(row) for row in items])]
    indices = np.concatenate(items) if items else np.array([], dtype=int)
    values = np.ones(len(indices), dtype=np.float32)
    return sparse.csr_matrix((values, indices, indptr), shape=(len(users), len(data.universe)))


def train_cf(data, countries, factors, regularization):
    matrix = train_matrix(data, countries)
    als = AlternatingLeastSquares(
        factors=factors,
        regularization=regularization,
        iterations=CF_ITERATIONS,
        random_state=RANDOM_SEED,
    )
    als.fit(matrix, show_progress=False)
    in_model = np.asarray(matrix.getnnz(axis=0)).ravel() > 0
    return CFModel(np.asarray(als.item_factors), in_model, regularization)


# ---------- 평가 사용자 준비 (모델과 나라마다 한 번) ----------


@dataclass
class CFUsers:
    rows: np.ndarray  # 평가 사용자 행 번호
    usable: np.ndarray  # fold-in에 쓸 보여준 아티스트가 하나 이상 있는 사용자
    factors: np.ndarray  # 사용자 벡터 (usable인 사용자만 의미 있음)
    low: np.ndarray  # 사용자별 CF 점수 최솟값 (ALS 아티스트 중)
    high: np.ndarray  # 사용자별 CF 점수 최댓값
    top_index: np.ndarray  # 사용자별 CF 상위 A개 (보여준 것 제외), universe 번호
    top_norm: np.ndarray  # 그 아티스트들의 변환된 CF 점수
    top_relevant: np.ndarray  # 그 아티스트들이 정답인지


def prepare_users(data, model, iso3, candidates=CANDIDATES_PER_SOURCE, batch=250):
    rows, _, _ = data.country_rows(iso3)
    shown = data.shown_matrix[rows].astype(np.float32).tocsr()
    shown_in_model = shown.multiply(model.in_model.astype(np.float32)[None, :]).tocsr()
    shown_in_model.eliminate_zeros()
    usable = np.asarray(shown_in_model.getnnz(axis=1)).ravel() > 0

    factors = np.zeros((len(rows), model.item_factors.shape[1]), dtype=np.float64)
    if usable.any():
        factors[usable] = model.solver().recalculate_user(np.arange(usable.sum()), shown_in_model[usable])

    n = len(rows)
    low, high = np.zeros(n), np.zeros(n)
    count = min(candidates, int(model.in_model.sum()))
    top_index = np.zeros((n, count), dtype=np.int64)
    top_norm = np.zeros((n, count))
    model_items = np.flatnonzero(model.in_model)
    for start in range(0, n, batch):
        stop = min(start + batch, n)
        scores = factors[start:stop] @ model.item_factors64[model_items].T
        low[start:stop] = scores.min(axis=1)
        high[start:stop] = scores.max(axis=1)
        # 보여준 아티스트는 후보에서 뺀다 (메모리를 아끼려고 제자리에서 바꾼다)
        shown_block = shown[start:stop][:, model_items].tocoo()
        scores[shown_block.row, shown_block.col] = -np.inf
        part = np.argpartition(-scores, count - 1, axis=1)[:, :count]
        part_scores = np.take_along_axis(scores, part, axis=1)
        order = np.argsort(-part_scores, axis=1, kind="stable")
        top_index[start:stop] = model_items[np.take_along_axis(part, order, axis=1)]
        top_norm[start:stop] = _normalize(
            np.take_along_axis(part_scores, order, axis=1), low[start:stop], high[start:stop]
        )
    top_relevant = _lookup(data.relevant_matrix, rows, top_index)
    return CFUsers(rows, usable, factors, low, high, top_index, top_norm, top_relevant)


def _normalize(values, low, high):
    span = (high - low)[:, None]
    with np.errstate(invalid="ignore", divide="ignore"):
        result = np.where(span > 0, (values - low[:, None]) / span, 0.0)
    return np.where(np.isfinite(values), result, -np.inf)


def _lookup(matrix, rows, columns):
    """matrix[rows[i], columns[i, j]]를 (len(rows) × columns 열 수) 참/거짓 배열로."""
    if columns.size == 0:
        return np.zeros(columns.shape, dtype=bool)
    flat_rows = np.repeat(rows, columns.shape[1])
    return np.asarray(matrix[flat_rows, columns.ravel()]).reshape(columns.shape).astype(bool)


# ---------- 섞은 점수로 평가 ----------


def evaluate_mix(data, model, users, weight, country_share, global_share, tie_listeners, catalog_mask, iso3, k):
    """CF + 나라 인기 섞기로 한 나라 평가 사용자를 평가한다.

    country_share: 나라 인기 (universe 길이). global_share: 이 조건의 전체 인기 (대체용).
    돌려주는 값: 사용자별 NDCG, Recall, 추천된 universe 번호 집합, 전체 계산으로 돌아간 사용자 수.
    """
    country_norm = _share_norm(country_share, catalog_mask)
    if weight == 1.0:
        ndcg, recall, items = evaluate_shared_scores(data, country_norm, tie_listeners, iso3, k, catalog_mask)
        return ndcg, recall, items, 0

    n = len(users.rows)
    ndcg, recall = np.zeros(n), np.zeros(n)
    recommended = set()
    exact_rows = list(np.flatnonzero(~users.usable))

    fast = np.flatnonzero(users.usable)
    if len(fast):
        count = min(CANDIDATES_PER_SOURCE, int(catalog_mask.sum()))
        country_top = np.flatnonzero(catalog_mask)[
            top_k(country_norm[catalog_mask], tie_listeners[catalog_mask], exclude=[], k=count)
        ]
        country_bound = country_norm[country_top[-1]] if len(country_top) else 0.0

        # 후보 = 나라 인기 상위 (모두 같음) + CF 상위 (사용자마다 다름, 나라 인기 상위와 겹치면 뺌)
        cf_on_country_top = _cf_norm_at(model, users, fast, country_top)
        country_part = (1 - weight) * cf_on_country_top + weight * country_norm[country_top][None, :]
        country_shown = _lookup(data.shown_matrix, users.rows[fast], np.broadcast_to(country_top, (len(fast), len(country_top))))
        country_part[country_shown] = -np.inf

        cf_index = users.top_index[fast]
        cf_part = (1 - weight) * users.top_norm[fast] + weight * country_norm[cf_index]
        cf_part[np.isin(cf_index, country_top) | ~catalog_mask[cf_index]] = -np.inf

        scores = np.concatenate([country_part, cf_part], axis=1)
        index = np.concatenate([np.broadcast_to(country_top, (len(fast), len(country_top))), cf_index], axis=1)
        relevant = np.concatenate(
            [_lookup(data.relevant_matrix, users.rows[fast], np.broadcast_to(country_top, (len(fast), len(country_top)))),
             users.top_relevant[fast]],
            axis=1,
        )

        take = min(k + 1, scores.shape[1])
        part = np.argpartition(-scores, take - 1, axis=1)[:, :take]
        part_scores = np.take_along_axis(scores, part, axis=1)
        order = np.argsort(-part_scores, axis=1, kind="stable")
        best = np.take_along_axis(part, order, axis=1)
        best_scores = np.take_along_axis(scores, best, axis=1)

        # 후보 밖 상한과 동점 확인. 걸리는 사용자는 전체 계산
        cf_bound = users.top_norm[fast][:, -1] if users.top_norm.shape[1] else np.zeros(len(fast))
        outside_bound = (1 - weight) * np.maximum(cf_bound, 0.0) + weight * country_bound
        kth = best_scores[:, k - 1] if best_scores.shape[1] >= k else np.full(len(fast), -np.inf)
        with np.errstate(invalid="ignore"):  # -inf끼리 빼면 nan. nan은 동점이 아니다
            has_tie = (np.diff(best_scores, axis=1) == 0).any(axis=1)
        too_few = ~np.isfinite(kth)
        need_exact = (outside_bound >= kth) | has_tie | too_few
        exact_rows.extend(fast[need_exact])

        good = ~need_exact
        top_best = best[good][:, :k]
        hits = np.take_along_axis(relevant[good], top_best, axis=1)
        discount = 1.0 / np.log2(np.arange(2, k + 2))
        n_relevant = data.n_relevant[users.rows[fast][good]]
        ideal = np.r_[0.0, np.cumsum(discount)]
        ndcg[fast[good]] = (hits * discount[None, : top_best.shape[1]]).sum(axis=1) / ideal[np.minimum(k, n_relevant)]
        recall[fast[good]] = hits.sum(axis=1) / n_relevant
        recommended.update(np.take_along_axis(index[good], top_best, axis=1).ravel().tolist())

    global_norm = _share_norm(global_share, catalog_mask)
    for position in exact_rows:
        user_ndcg, user_recall, items = _exact_user(
            data, model, users, position, weight, country_norm, global_norm, tie_listeners, catalog_mask, k
        )
        ndcg[position], recall[position] = user_ndcg, user_recall
        recommended.update(items)
    return ndcg, recall, recommended, len(exact_rows)


def _share_norm(share, catalog_mask):
    values = share[catalog_mask]
    low, high = (values.min(), values.max()) if len(values) else (0.0, 0.0)
    normalized = (share - low) / (high - low) if high > low else np.zeros_like(share, dtype=float)
    return np.where(catalog_mask, normalized, 0.0)


def _cf_norm_at(model, users, positions, items):
    """사용자들의 주어진 아티스트 CF 점수 (변환 후). ALS에 없는 아티스트는 0."""
    raw = users.factors[positions] @ model.item_factors64[items].T
    normalized = _normalize(raw, users.low[positions], users.high[positions])
    return np.where(model.in_model[items][None, :], normalized, 0.0)


def full_cf_norm(model, users, position, global_norm):
    """한 사용자의 universe 전체 CF 점수 (변환 후). fold-in이 안 되는 사용자는 전체 인기."""
    if not users.usable[position]:
        return global_norm
    raw = model.item_factors64 @ users.factors[position]
    normalized = _normalize(raw[None, :], users.low[[position]], users.high[[position]])[0]
    return np.where(model.in_model, normalized, 0.0)


def _exact_user(data, model, users, position, weight, country_norm, global_norm, tie_listeners, catalog_mask, k):
    row = users.rows[position]
    scores = (1 - weight) * full_cf_norm(model, users, position, global_norm) + weight * country_norm
    candidates = np.flatnonzero(catalog_mask)
    exclude = np.flatnonzero(np.isin(candidates, data.shown_matrix[row].indices))
    best = candidates[top_k(scores[candidates], tie_listeners[candidates], exclude, k)]
    relevant = data.relevant_matrix[row, best].toarray().ravel() if len(best) else np.array([], bool)
    discount = 1.0 / np.log2(np.arange(2, len(best) + 2))
    n_relevant = data.n_relevant[row]
    ideal = np.sum(1.0 / np.log2(np.arange(2, min(k, n_relevant) + 2)))
    return float((relevant * discount).sum() / ideal), float(relevant.sum() / n_relevant), best.tolist()
