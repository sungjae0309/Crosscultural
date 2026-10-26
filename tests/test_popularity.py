"""src/popularity.py, src/stats.py, src/run_h1.py의 계산 규칙 확인용 테스트 (가짜 데이터).

실행: python tests/test_popularity.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config import N_SHOWN_ARTISTS  # noqa: E402
from metrics import ndcg_at_k, recall_at_k, top_k  # noqa: E402
from popularity import (  # noqa: E402
    build_popularity_data,
    evaluate_shared_scores,
    listener_counts,
    pick_early_users,
    popularity_share,
    relevant_in_catalog_share,
    user_listener_counts,
)
from run_h1 import best_weight  # noqa: E402
from stats import holm_adjust, paired_summary  # noqa: E402


def _fake_frames():
    split = pd.DataFrame(
        [("t1", "AAA", "train"), ("t2", "AAA", "train"), ("t3", "BBB", "train"),
         ("v1", "AAA", "valid"), ("s1", "AAA", "test")],
        columns=["user_id", "iso3", "split"],
    )
    rows = [("t1", "a", 3), ("t1", "b", 1), ("t2", "a", 2), ("t3", "c", 5)]
    rows += [("v1", artist, 1) for artist in ["a", "b", "x1", "x2", "x3", "zzz"]]
    rows += [("s1", artist, 1) for artist in ["a", "b", "c", "d", "e", "f"]]
    plays = pd.DataFrame(rows, columns=["user_id", "artist_id", "plays"])
    shown = pd.DataFrame(
        [("v1", artist) for artist in ["a", "x1", "x2", "x3", "zzz"]]
        + [("s1", artist) for artist in ["a", "b", "c", "d", "e"]],
        columns=["user_id", "artist_id"],
    )
    return split, shown, plays


def test_build_uses_train_only():
    split, shown, plays = _fake_frames()
    data = build_popularity_data(split, shown, plays, "valid")
    # 순위 대상과 인기 재료는 학습 사용자(t1, t2, t3)로만
    assert list(data.universe) == ["a", "b", "c"]
    assert list(data.country_listeners["AAA"]) == [2, 1, 0]
    assert data.country_train_users == {"AAA": 2, "BBB": 1}
    assert list(data.train_users["AAA"]) == ["t1", "t2"]
    assert list(data.train_items["t1"]) == [0, 1]
    # 이번 단계 사용자만
    assert list(data.eval_users["user_id"]) == ["v1"]
    # 정답 = 보여준 5개를 뺀 나머지 = b 하나. 정답 수에는 universe 밖 정답도 들어간다
    assert data.n_relevant.tolist() == [1]
    assert data.relevant_matrix.toarray().tolist() == [[False, True, False]]
    # 보여준 것 중 universe 안에 있는 것만 행렬에 들어간다
    assert data.shown_matrix.toarray().tolist() == [[True, False, False]]


def test_valid_data_ignores_test_rows():
    split, shown, plays = _fake_frames()
    before = build_popularity_data(split, shown, plays, "valid")
    changed = plays.copy()
    changed.loc[changed["user_id"] == "s1", "artist_id"] = "changed"
    after = build_popularity_data(split, shown[shown["user_id"] != "s1"], changed, "valid")
    assert list(before.universe) == list(after.universe)
    assert (before.relevant_matrix != after.relevant_matrix).nnz == 0
    assert (before.shown_matrix != after.shown_matrix).nnz == 0
    assert np.array_equal(before.n_relevant, after.n_relevant)


def test_relevant_in_catalog_share():
    split, shown, plays = _fake_frames()
    data = build_popularity_data(split, shown, plays, "test")
    # s1 정답은 f 하나, universe(a, b, c) 밖
    assert list(relevant_in_catalog_share(data, "AAA")) == [0.0]


def _random_frames(rng, n_artists=40, n_train=30, n_eval=25):
    artists = [f"art{index:03d}" for index in range(n_artists)]
    split_rows, play_rows, shown_rows = [], [], []
    for index in range(n_train):
        user = f"tr{index:03d}"
        split_rows.append((user, "AAA" if index % 2 else "BBB", "train"))
        # 학습 사용자는 앞쪽 30개 아티스트만 들어서, 뒤쪽은 universe 밖이 된다
        for artist in rng.choice(artists[:30], size=int(rng.integers(1, 12)), replace=False):
            play_rows.append((user, artist, int(rng.integers(1, 9))))
    for index in range(n_eval):
        user = f"ev{index:03d}"
        split_rows.append((user, "AAA", "valid"))
        listened = rng.choice(artists, size=int(rng.integers(N_SHOWN_ARTISTS + 1, 25)), replace=False)
        play_rows.extend((user, artist, 1) for artist in listened)
        shown_rows.extend((user, artist) for artist in listened[:N_SHOWN_ARTISTS])
    return (
        pd.DataFrame(split_rows, columns=["user_id", "iso3", "split"]),
        pd.DataFrame(shown_rows, columns=["user_id", "artist_id"]),
        pd.DataFrame(play_rows, columns=["user_id", "artist_id", "plays"]),
    )


def test_matrix_evaluation_matches_reference():
    # 행렬로 한꺼번에 계산한 NDCG, Recall이 사용자마다 metrics.py로 계산한 값과 같은지
    rng = np.random.default_rng(0)
    for trial in range(30):
        split, shown, plays = _random_frames(rng)
        data = build_popularity_data(split, shown, plays, "valid")
        n = len(data.universe)
        scores = rng.integers(0, 4, n).astype(float)
        tie = listener_counts(data, ["AAA", "BBB"])
        mask = rng.random(n) < 0.7 if trial % 2 else None
        ndcg, recall, recommended = evaluate_shared_scores(data, scores, tie, "AAA", 10, mask)

        allowed = np.ones(n, bool) if mask is None else mask
        expected_items = set()
        users = data.eval_users.set_index("row")["user_id"]
        for row in range(len(users)):
            shown_index = data.shown_matrix[row].indices
            excluded = set(shown_index) | set(np.flatnonzero(~allowed))
            recommended_index = top_k(scores, tie, excluded, 10)
            expected_items.update(int(index) for index in recommended_index)
            relevant_ids = set(
                plays.loc[plays["user_id"] == users[row], "artist_id"]
            ) - set(shown.loc[shown["user_id"] == users[row], "artist_id"])
            recommended_ids = list(data.universe[recommended_index])
            assert abs(ndcg[row] - ndcg_at_k(recommended_ids, relevant_ids, 10)) < 1e-12
            assert abs(recall[row] - recall_at_k(recommended_ids, relevant_ids, 10)) < 1e-12
        assert recommended == expected_items


def test_early_users():
    split, shown, plays = _fake_frames()
    data = build_popularity_data(split, shown, plays, "valid")
    first = pick_early_users(data, "AAA", 1, repeat=0)
    assert len(first) == 1 and first[0] in {"t1", "t2"}
    # 같은 키면 같은 결과
    assert list(first) == list(pick_early_users(data, "AAA", 1, repeat=0))
    assert list(user_listener_counts(data, ["t1", "t2"])) == [2, 1, 0]
    try:
        pick_early_users(data, "BBB", 2, repeat=0)
    except ValueError:
        pass
    else:
        raise AssertionError("학습 사용자보다 많이 뽑으면 오류여야 한다")


def test_popularity_share():
    split, shown, plays = _fake_frames()
    data = build_popularity_data(split, shown, plays, "valid")
    # 청취자 비율: a 2/3, b 1/3, c 1/3
    assert np.allclose(popularity_share(data, ["AAA", "BBB"], "listeners"), [2 / 3, 1 / 3, 1 / 3])
    assert np.allclose(popularity_share(data, ["AAA"], "listeners"), [1.0, 0.5, 0.0])
    # 재생 수 비율: 전체 11 중 a 5, b 1, c 5
    assert np.allclose(popularity_share(data, ["AAA", "BBB"], "plays"), [5 / 11, 1 / 11, 5 / 11])


def test_best_weight_prefers_smaller_on_tie():
    weights = [0.0, 0.1, 0.2, 0.3]
    assert best_weight(weights, [0.1, 0.3, 0.3, 0.2]) == 0.1
    assert best_weight(weights, [0.4, 0.3, 0.3, 0.2]) == 0.0


def test_paired_summary():
    result = paired_summary([0.1, 0.2, -0.1, 0.0], n_bootstrap=2000, seed=1)
    assert result["n_countries"] == 4
    assert abs(result["mean_diff"] - 0.05) < 1e-12
    assert result["share_better"] == 0.5 and result["share_worse"] == 0.25
    assert result["ci_low"] <= result["mean_diff"] <= result["ci_high"]
    assert paired_summary([0.0, 0.0])["wilcoxon_p"] == 1.0


def test_holm():
    # 손으로 계산: 정렬 0.01, 0.03, 0.04 -> 0.03, 0.06, 0.06
    assert np.allclose(holm_adjust([0.04, 0.01, 0.03]), [0.06, 0.03, 0.06])
    assert np.allclose(holm_adjust([0.5, 0.9]), [1.0, 1.0])


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print(f"통과: {test.__name__}")
    print(f"{len(tests)}개 모두 통과")
