"""src/run_h2.py, src/wvs_distance.py 규칙 확인용 테스트 (가짜 데이터).

실행: python tests/test_h2.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config import WVS_INDEX_COLUMNS  # noqa: E402
from popularity import build_popularity_data, pick_early_users  # noqa: E402
from run_h2 import Conditions  # noqa: E402
from wvs_distance import nearest_countries  # noqa: E402


def _fake_data():
    split = pd.DataFrame(
        [("a1", "AAA", "train"), ("a2", "AAA", "train"), ("b1", "BBB", "train"),
         ("c1", "CCC", "train"), ("c2", "CCC", "train"), ("v1", "AAA", "valid")],
        columns=["user_id", "iso3", "split"],
    )
    rows = [("a1", "x", 1), ("a2", "y", 1), ("b1", "x", 1), ("b1", "z", 1),
            ("c1", "w", 1), ("c2", "w", 1), ("c2", "x", 1)]
    rows += [("v1", artist, 1) for artist in ["x", "y", "z", "w", "q", "r"]]
    plays = pd.DataFrame(rows, columns=["user_id", "artist_id", "plays"])
    shown = pd.DataFrame([("v1", artist) for artist in ["q", "r", "w", "x", "y"]], columns=["user_id", "artist_id"])
    return build_popularity_data(split, shown, plays, "valid")


def test_target_condition_excludes_target_and_adds_early_users():
    data = _fake_data()  # universe: w, x, y, z
    conditions = Conditions(data, ["AAA", "BBB", "CCC"], n_early=1)
    for repeat in range(3):
        early = pick_early_users(data, "AAA", 1, repeat)[0]
        global_share, country_share, tie, mask = conditions.make(["AAA"], "AAA", repeat)
        # 전체 인기: AAA를 뺀 BBB(1명), CCC(2명)
        assert np.allclose(global_share, np.array([2, 2, 0, 1]) / 3)
        # 나라 인기: AAA 초기 사용자 1명만
        expected_early = {"a1": [0, 1, 0, 0], "a2": [0, 0, 1, 0]}[early]
        assert np.allclose(country_share, expected_early)
        # 동점용 청취자 수와 순위 대상: AAA 나머지 학습 사용자는 들어가지 않는다
        assert list(tie) == list(np.array([2, 2, 0, 1]) + expected_early)
        assert list(mask) == [value > 0 for value in tie]


def test_donor_condition_excludes_target_and_donor():
    data = _fake_data()
    conditions = Conditions(data, ["AAA", "BBB", "CCC"], n_early=1)
    early = pick_early_users(data, "CCC", 1, repeat=0)[0]
    global_share, country_share, tie, mask = conditions.make(["AAA", "CCC"], "CCC", 0)
    # 전체 인기: AAA와 CCC를 모두 빼고 BBB(1명)만
    assert np.allclose(global_share, [0, 1, 0, 1])
    expected_early = {"c1": [1, 0, 0, 0], "c2": [1, 1, 0, 0]}[early]
    assert np.allclose(country_share, expected_early)
    assert list(tie) == list(np.array([0, 1, 0, 1]) + expected_early)


def test_nearest_countries_standardize_without_target():
    means = pd.DataFrame(
        {WVS_INDEX_COLUMNS[0]: [0.0, 1.0, 2.0, 100.0], WVS_INDEX_COLUMNS[1]: [0.0, 0.0, 0.0, 0.0]},
        index=["P1", "P2", "P3", "T"],
    )
    means[WVS_INDEX_COLUMNS[1]] = [0.0, 1.0, 0.5, 0.0]
    result = nearest_countries(means, "T", ["P1", "P2", "P3", "T"], k=2)
    # t 값(100)이 표준화에 들어가지 않았는지: 풀로만 구한 평균, 표준편차로 직접 계산
    pool = means.loc[["P1", "P2", "P3"]]
    z_pool = (pool - pool.mean()) / pool.std(ddof=1)
    z_target = (means.loc["T"] - pool.mean()) / pool.std(ddof=1)
    expected = np.sqrt(((z_pool - z_target) ** 2).sum(axis=1)).sort_values()
    assert [iso3 for iso3, _ in result] == list(expected.index[:2])
    assert np.allclose([distance for _, distance in result], expected.to_numpy()[:2])
    # 풀에 t가 들어 있어도 후보에서 빠진다
    assert "T" not in [iso3 for iso3, _ in result]


def test_nearest_countries_rejects_missing_values():
    means = pd.DataFrame({column: [0.0, np.nan, 1.0] for column in WVS_INDEX_COLUMNS}, index=["P1", "P2", "T"])
    try:
        nearest_countries(means, "T", ["P1", "P2"], k=1)
    except ValueError:
        return
    raise AssertionError("WVS 값이 비어 있으면 오류여야 한다")


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print(f"통과: {test.__name__}")
    print(f"{len(tests)}개 모두 통과")
