"""추천 목록 만들기와 평가 지표 (report/실험설계.md 4.1, 4.2절).

아티스트는 순위 대상 집합(catalog) 안의 번호(index)로 다룬다.
catalog는 artist_id 순으로 정렬해 두고, 동점이면 번호가 작은 쪽(= artist_id가 앞선 쪽)이 먼저 온다.
"""

import numpy as np


def top_k(scores, listeners, exclude, k):
    """점수가 높은 순으로 k개 번호를 돌려준다. exclude에 있는 번호는 뺀다.

    동점 처리: 점수 → 청취자 수(많은 쪽) → 번호(작은 쪽).
    listeners는 그 조건에서 쓸 수 있는 학습 자료로만 센 값이어야 한다.
    """
    scores = np.asarray(scores, dtype=float)
    listeners = np.asarray(listeners)
    exclude = set(int(index) for index in exclude)

    # 빼야 할 개수만큼 여유를 두고 후보를 고른다.
    # 경계 점수와 같은 점수를 가진 아티스트는 모두 후보에 넣어야 동점 처리가 정확하다
    needed = min(k + len(exclude), len(scores))
    if needed == 0:
        return np.array([], dtype=int)
    boundary = np.partition(scores, len(scores) - needed)[len(scores) - needed]
    candidates = np.flatnonzero(scores >= boundary)

    order = np.lexsort((candidates, -listeners[candidates], -scores[candidates]))
    ranked = candidates[order]
    if exclude:
        ranked = ranked[~np.isin(ranked, list(exclude))]
    return ranked[:k]


def recall_at_k(recommended, relevant, k):
    """맞힌 정답 수 / 전체 정답 수. 정답이 없으면 NaN."""
    relevant = set(relevant)
    if not relevant:
        return float("nan")
    hits = sum(1 for item in recommended[:k] if item in relevant)
    return hits / len(relevant)


def ndcg_at_k(recommended, relevant, k):
    """정답 여부(0/1) 기준 NDCG@k. 정답이 없으면 NaN.

    DCG = 맞힌 위치 r(1부터)마다 1 / log2(r + 1)
    IDCG = 정답 min(k, 정답 수)개가 맨 위에 있을 때의 DCG
    """
    relevant = set(relevant)
    if not relevant:
        return float("nan")
    dcg = sum(
        1.0 / np.log2(position + 2)
        for position, item in enumerate(recommended[:k])
        if item in relevant
    )
    ideal_hits = min(k, len(relevant))
    idcg = sum(1.0 / np.log2(position + 2) for position in range(ideal_hits))
    return dcg / idcg


def item_coverage(recommended_lists, catalog_size):
    """추천된 서로 다른 아티스트 수 / 순위 대상 아티스트 수."""
    distinct = set()
    for recommended in recommended_lists:
        distinct.update(int(item) for item in recommended)
    return len(distinct) / catalog_size
