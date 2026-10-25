"""src/popularity.py, src/stats.py, src/run_h1.py의 계산 규칙 확인용 테스트 (가짜 데이터).

실행: python tests/test_popularity.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config import N_SHOWN_ARTISTS  # noqa: E402
from metrics import top_k  # noqa: E402
from popularity import (  # noqa: E402
    PopularityData,
    build_popularity_data,
    popularity_share,
    recommend_from_head,
    relevant_in_catalog_share,
)
from run_h1 import best_weight  # noqa: E402
from stats import holm_adjust, paired_summary  # noqa: E402


def test_head_shortcut_matches_direct_top_k():
    # 모두에게 같은 순위에서 보여준 것을 빼는 방식 = 사용자마다 직접 top_k
    rng = np.random.default_rng(0)
    for _ in range(300):
        n = int(rng.integers(N_SHOWN_ARTISTS + 1, 60))
        scores = rng.integers(0, 5, n).astype(float)
        listeners = rng.integers(0, 4, n)
        shown = rng.choice(n, size=int(rng.integers(0, N_SHOWN_ARTISTS + 1)), replace=False)
        head = top_k(scores, listeners, exclude=[], k=10 + N_SHOWN_ARTISTS)
        assert recommend_from_head(head, shown, 10) == list(top_k(scores, listeners, shown, 10))


def _fake_data():
    return PopularityData(
        catalog=np.array(["a", "b", "c"]),
        country_listeners={"AAA": np.array([2, 1, 0]), "BBB": np.array([0, 3, 3])},
        country_plays={"AAA": np.array([10.0, 5.0, 0.0]), "BBB": np.array([0.0, 30.0, 55.0])},
        country_train_users={"AAA": 2, "BBB": 4},
        eval_users=None,
        shown_index={},
        relevant={},
    )


def _fake_frames():
    split = pd.DataFrame(
        [("t1", "AAA", "train"), ("t2", "AAA", "train"), ("v1", "AAA", "valid"), ("s1", "AAA", "test")],
        columns=["user_id", "iso3", "split"],
    )
    rows = [("t1", "a", 3), ("t1", "b", 1), ("t2", "a", 2)]
    rows += [("v1", artist, 1) for artist in ["a", "b", "x1", "x2", "x3", "zzz"]]
    rows += [("s1", artist, 1) for artist in ["a", "b", "c", "d", "e", "f"]]
    plays = pd.DataFrame(rows, columns=["user_id", "artist_id", "plays"])
    shown = pd.DataFrame(
        [("v1", artist) for artist in ["a", "x1", "x2", "x3", "zzz"]]
        + [("s1", artist) for artist in ["a", "b", "c", "d", "e"]],
        columns=["user_id", "artist_id"],
    )
    return split, shown, plays


def test_build_uses_train_only_for_catalog_and_counts():
    split, shown, plays = _fake_frames()
    data = build_popularity_data(split, shown, plays, "valid")
    # 순위 대상과 인기 재료는 학습 사용자(t1, t2)로만
    assert list(data.catalog) == ["a", "b"]
    assert list(data.country_listeners["AAA"]) == [2, 1]
    assert data.country_train_users["AAA"] == 2
    # 이번 단계 사용자만
    assert list(data.eval_users["user_id"]) == ["v1"]
    assert set(data.relevant) == {"v1"} and set(data.shown_index) == {"v1"}
    # 정답 = 보여준 5개를 뺀 나머지. 순위 대상 밖이어도 남는다
    assert data.relevant["v1"] == {"b"}
    # 보여준 것 중 순위 대상 안에 있는 것만 번호로 바뀐다
    assert list(data.shown_index["v1"]) == [0]


def test_valid_data_ignores_test_rows():
    split, shown, plays = _fake_frames()
    before = build_popularity_data(split, shown, plays, "valid")
    changed = plays.copy()
    changed.loc[changed["user_id"] == "s1", "artist_id"] = "changed"
    changed_shown = shown[shown["user_id"] != "s1"]
    after = build_popularity_data(split, changed_shown, changed, "valid")
    assert list(before.catalog) == list(after.catalog)
    assert before.relevant == after.relevant
    assert all(np.array_equal(before.shown_index[u], after.shown_index[u]) for u in before.shown_index)
    assert np.array_equal(before.country_listeners["AAA"], after.country_listeners["AAA"])


def test_relevant_in_catalog_share():
    split, shown, plays = _fake_frames()
    data = build_popularity_data(split, shown, plays, "test")
    # s1 정답은 f 하나, 순위 대상(a, b) 밖
    assert list(relevant_in_catalog_share(data, ["s1"])) == [0.0]


def test_popularity_share():
    data = _fake_data()
    # 청취자 비율: (2+0)/6, (1+3)/6, (0+3)/6
    assert np.allclose(popularity_share(data, ["AAA", "BBB"], "listeners"), [2 / 6, 4 / 6, 3 / 6])
    assert np.allclose(popularity_share(data, ["AAA"], "listeners"), [1.0, 0.5, 0.0])
    # 재생 수 비율: 전체 100 중
    assert np.allclose(popularity_share(data, ["AAA", "BBB"], "plays"), [0.10, 0.35, 0.55])


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
