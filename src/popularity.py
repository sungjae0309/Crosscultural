"""인기 점수 실험(H1, H2)에 같이 쓰는 데이터 준비와 평가 (report/실험설계.md 4, 5, 8절).

아티스트 번호
- universe: 학습 사용자 누구라도 한 번 들은 아티스트 전체. artist_id 순으로 정렬.
- 실험 조건마다 쓸 수 있는 학습 자료가 다르다 (H2에서 새 나라 t를 빼는 등).
  그 조건의 순위 대상(catalog)은 universe 중 "그 조건의 학습 자료에 나온 아티스트"이고,
  catalog_mask(universe 길이의 참/거짓 배열)로 나타낸다. H1은 universe 전체가 순위 대상이다.

평가
- 정답과 보여준 아티스트는 (평가 사용자 × universe) 희소 행렬로 들고 있는다.
- universe 밖 정답(학습 사용자가 아무도 안 들은 아티스트)은 행렬에 없지만 정답 수(n_relevant)에는 들어 있다.
- 지표 정의는 metrics.py와 같다. 같은 값을 내는지 tests/test_popularity.py에서 대조한다.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import sparse

from config import N_SHOWN_ARTISTS, PROCESSED_DIR
from load_lastfm import load_plays
from metrics import top_k
from seeds import seeded_rng


@dataclass
class PopularityData:
    universe: np.ndarray  # artist_id, 정렬됨
    country_listeners: dict  # iso3 -> 아티스트별 학습 청취자 수 (universe 길이)
    country_plays: dict  # iso3 -> 아티스트별 학습 재생 수 합
    country_train_users: dict  # iso3 -> 학습 사용자 수
    train_users: dict  # iso3 -> 그 나라 학습 사용자 user_id 배열 (정렬됨)
    train_items: dict  # user_id -> 그 사용자가 들은 아티스트의 universe 번호 배열
    eval_users: pd.DataFrame  # user_id, iso3, split, row (이번 단계의 평가 사용자만)
    relevant_matrix: sparse.csr_matrix  # (평가 사용자 × universe) 정답
    shown_matrix: sparse.csr_matrix  # (평가 사용자 × universe) 보여준 아티스트
    n_relevant: np.ndarray  # 평가 사용자별 정답 수 (universe 밖 정답 포함)
    _country_cache: dict = field(default_factory=dict)

    def country_rows(self, iso3):
        """그 나라 평가 사용자의 행 번호와, 열을 빨리 고르기 위한 CSC 행렬."""
        if iso3 not in self._country_cache:
            rows = self.eval_users.loc[self.eval_users["iso3"] == iso3, "row"].to_numpy()
            self._country_cache[iso3] = (
                rows,
                self.relevant_matrix[rows].tocsc(),
                self.shown_matrix[rows].tocsc(),
            )
        return self._country_cache[iso3]


def load_popularity_data(stage):
    """나누기 결과(split_users.py)와 재생 기록으로 실험 자료를 만든다.

    stage("valid" 또는 "test")의 평가 사용자 자료만 읽는다.
    """
    split = pd.read_csv(PROCESSED_DIR / "user_split.csv", dtype=str, keep_default_na=False)
    shown = pd.read_csv(PROCESSED_DIR / "shown_artists.csv", dtype=str, keep_default_na=False)
    plays = load_plays()[["user_id", "artist_id", "plays"]]
    return build_popularity_data(split, shown, plays, stage)


def _universe_index(universe, artist_ids):
    """artist_id -> universe 번호. universe에 없으면 -1."""
    artist_ids = np.asarray(artist_ids)
    position = np.searchsorted(universe, artist_ids)
    position = np.minimum(position, max(len(universe) - 1, 0))
    found = (universe[position] == artist_ids) if len(universe) else np.zeros(len(artist_ids), bool)
    return np.where(found, position, -1)


def build_popularity_data(split, shown, plays, stage):
    """학습 사용자로 인기 점수 재료를, stage 사용자로 평가 자료를 만든다.

    다른 단계의 평가 사용자 기록은 아예 쓰지 않는다.
    """
    if stage not in ("valid", "test"):
        raise ValueError("stage는 valid 또는 test")
    plays = plays.merge(split[["user_id", "iso3", "split"]], on="user_id", how="inner")
    plays = plays[plays["split"].isin(["train", stage])]

    # ---------- 학습 사용자로만 인기 점수 재료를 만든다 ----------
    train = plays[plays["split"] == "train"].sort_values(["user_id", "artist_id"])
    universe = np.sort(train["artist_id"].unique())
    train = train.assign(artist_index=_universe_index(universe, train["artist_id"].to_numpy()))

    country_listeners, country_plays, train_users = {}, {}, {}
    for iso3, rows in train.groupby("iso3", sort=True):
        index = rows["artist_index"].to_numpy()
        country_listeners[iso3] = np.bincount(index, minlength=len(universe))
        country_plays[iso3] = np.bincount(
            index, weights=rows["plays"].to_numpy(dtype=float), minlength=len(universe)
        )
        train_users[iso3] = np.sort(rows["user_id"].unique())
    country_train_users = {iso3: len(users) for iso3, users in train_users.items()}

    user_ids = train["user_id"].to_numpy()
    starts = np.flatnonzero(np.r_[True, user_ids[1:] != user_ids[:-1]])
    ends = np.r_[starts[1:], len(user_ids)]
    artist_index = train["artist_index"].to_numpy()
    train_items = {user_ids[s]: artist_index[s:e] for s, e in zip(starts, ends)}

    # ---------- 이번 단계의 평가 사용자: 보여준 것과 정답 ----------
    eval_users = split.loc[split["split"] == stage, ["user_id", "iso3", "split"]]
    eval_users = eval_users.sort_values("user_id").reset_index(drop=True)
    eval_users["row"] = np.arange(len(eval_users))
    row_of = dict(zip(eval_users["user_id"], eval_users["row"]))

    shown = shown[shown["user_id"].isin(row_of)]
    eval_plays = plays.loc[plays["split"] == stage, ["user_id", "artist_id"]]
    shown_pairs = set(zip(shown["user_id"], shown["artist_id"]))
    is_shown = np.fromiter(
        (pair in shown_pairs for pair in zip(eval_plays["user_id"], eval_plays["artist_id"])),
        dtype=bool,
        count=len(eval_plays),
    )
    relevant = eval_plays[~is_shown]
    relevant_rows = relevant["user_id"].map(row_of).to_numpy()
    n_relevant = np.bincount(relevant_rows, minlength=len(eval_users))
    relevant_index = _universe_index(universe, relevant["artist_id"].to_numpy())
    keep = relevant_index >= 0
    relevant_matrix = sparse.csr_matrix(
        (np.ones(keep.sum(), dtype=bool), (relevant_rows[keep], relevant_index[keep])),
        shape=(len(eval_users), len(universe)),
    )

    shown_rows = shown["user_id"].map(row_of).to_numpy()
    shown_index = _universe_index(universe, shown["artist_id"].to_numpy())
    keep = shown_index >= 0
    shown_matrix = sparse.csr_matrix(
        (np.ones(keep.sum(), dtype=bool), (shown_rows[keep], shown_index[keep])),
        shape=(len(eval_users), len(universe)),
    )

    return PopularityData(
        universe=universe,
        country_listeners=country_listeners,
        country_plays=country_plays,
        country_train_users=country_train_users,
        train_users=train_users,
        train_items=train_items,
        eval_users=eval_users,
        relevant_matrix=relevant_matrix,
        shown_matrix=shown_matrix,
        n_relevant=n_relevant,
    )


# ---------- 인기 점수 재료 ----------


def listener_counts(data, countries):
    """주어진 나라들의 학습 사용자로 센 아티스트별 청취자 수."""
    total = np.zeros(len(data.universe), dtype=np.int64)
    for iso3 in countries:
        total += data.country_listeners[iso3]
    return total


def user_listener_counts(data, user_ids):
    """주어진 학습 사용자들로 센 아티스트별 청취자 수 (초기 사용자용)."""
    if len(user_ids) == 0:
        return np.zeros(len(data.universe), dtype=np.int64)
    items = np.concatenate([data.train_items[user_id] for user_id in user_ids])
    return np.bincount(items, minlength=len(data.universe))


def popularity_share(data, countries, measure):
    """주어진 나라들의 학습 사용자로 만든 인기 점수 (0~1).

    listeners: 들은 학습 사용자 비율. plays: 전체 재생 수 중 그 아티스트의 비율.
    """
    if measure == "listeners":
        counts = listener_counts(data, countries)
        total = sum(data.country_train_users[iso3] for iso3 in countries)
    elif measure == "plays":
        counts = sum(data.country_plays[iso3] for iso3 in countries)
        total = counts.sum()
    else:
        raise ValueError(f"알 수 없는 인기 기준: {measure}")
    return counts / total


def pick_early_users(data, iso3, n_users, repeat):
    """새 나라 상황의 초기 사용자: 그 나라 학습 사용자 중 무작위 n_users명.

    나라, 인원, 반복 번호로 시드를 정하므로 같은 나라는 새 나라 역할이든 빌려줄 나라 역할이든
    같은 반복 번호에서 같은 사람들이 뽑힌다.
    """
    candidates = data.train_users[iso3]
    if len(candidates) < n_users:
        raise ValueError(f"{iso3}의 학습 사용자가 {n_users}명보다 적다")
    rng = seeded_rng("early", iso3, n_users, repeat)
    return np.sort(rng.choice(candidates, size=n_users, replace=False))


# ---------- 평가 ----------


def evaluate_shared_scores(data, scores, tie_listeners, iso3, k, catalog_mask=None):
    """한 나라의 평가 사용자 전원이 같은 점수를 쓸 때의 평가.

    - 순위 대상은 catalog_mask가 참인 아티스트 (None이면 universe 전체).
    - 점수가 모두에게 같으므로 순위는 한 번만 매긴다. 사용자마다 빼는 아티스트가
      최대 N_SHOWN_ARTISTS개라서 상위 k + N_SHOWN_ARTISTS개면 충분하다.
    돌려주는 값: 사용자별 NDCG, Recall 배열과 추천된 universe 번호 집합.
    """
    rows, relevant_csc, shown_csc = data.country_rows(iso3)
    if catalog_mask is None:
        head = top_k(scores, tie_listeners, exclude=[], k=k + N_SHOWN_ARTISTS)
    else:
        candidates = np.flatnonzero(catalog_mask)
        head = candidates[
            top_k(scores[candidates], tie_listeners[candidates], exclude=[], k=k + N_SHOWN_ARTISTS)
        ]
    if len(rows) == 0:
        return np.array([]), np.array([]), set()

    is_relevant = relevant_csc[:, head].toarray()
    not_shown = ~shown_csc[:, head].toarray()
    rank = np.cumsum(not_shown, axis=1)  # 보여준 것을 빼고 몇 번째인지 (1부터)
    in_list = not_shown & (rank <= k)
    hits = is_relevant & in_list

    # 보여준 아티스트 칸은 순번이 앞 칸과 같거나 0이라 할인값을 계산하지 않는다 (목록에 없는 칸은 0)
    discount = np.zeros(rank.shape)
    discount[in_list] = 1.0 / np.log2(rank[in_list] + 1)
    dcg = (hits * discount).sum(axis=1)
    n_relevant = data.n_relevant[rows]
    ideal_discount = np.r_[0.0, np.cumsum(1.0 / np.log2(np.arange(2, k + 2)))]
    idcg = ideal_discount[np.minimum(k, n_relevant)]
    ndcg = dcg / idcg
    recall = hits.sum(axis=1) / n_relevant

    recommended = set(int(head[j]) for j in np.flatnonzero(in_list.any(axis=0)))
    return ndcg, recall, recommended


def relevant_in_catalog_share(data, iso3, catalog_mask=None):
    """그 나라 평가 사용자마다 정답 중 순위 대상에 들어 있는 비율 (아이템 겹침, 설계 4.1절)."""
    rows, relevant_csc, _ = data.country_rows(iso3)
    if catalog_mask is None:
        in_catalog = np.asarray(relevant_csc.sum(axis=1)).ravel()
    else:
        in_catalog = relevant_csc @ catalog_mask.astype(np.int64)
    return in_catalog / data.n_relevant[rows]
