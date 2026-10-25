"""src/popularity.py, src/stats.py, src/run_h1.py의 계산 규칙 확인용 테스트 (가짜 데이터).

실행: python tests/test_popularity.py
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config import N_SHOWN_ARTISTS  # noqa: E402
from metrics import top_k  # noqa: E402
from popularity import PopularityData, popularity_share, recommend_from_head  # noqa: E402
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
