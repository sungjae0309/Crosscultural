"""src/metrics.py 확인용 테스트.

실행: python tests/test_metrics.py
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from metrics import item_coverage, ndcg_at_k, recall_at_k, top_k  # noqa: E402


def test_course_example():
    # 과제 자료(Midterm 16쪽) 예시: K=3, 정답 2개, 1위와 3위에서 맞힘
    recommended = ["a", "x", "b"]
    relevant = {"a", "b"}
    assert recall_at_k(recommended, relevant, 3) == 1.0
    assert round(ndcg_at_k(recommended, relevant, 3), 3) == 0.920


def test_recall_uses_all_relevant():
    # 정답이 K보다 많으면 Recall@K는 1이 될 수 없다 (min으로 나누지 않음)
    relevant = set(range(20))
    assert recall_at_k(list(range(10)), relevant, 10) == 0.5


def test_ndcg_perfect_and_empty():
    assert ndcg_at_k([1, 2, 3], {1, 2, 3, 4, 5}, 3) == 1.0
    assert ndcg_at_k([9, 8, 7], {1}, 3) == 0.0
    assert math.isnan(ndcg_at_k([1], set(), 3))


def test_top_k_order_and_tie_break():
    scores = [0.5, 0.9, 0.5, 0.5, 0.1]
    listeners = [10, 1, 30, 30, 99]
    # 0.9가 먼저. 0.5 셋은 청취자 수 → 번호 순: 2(30), 3(30), 0(10)
    assert list(top_k(scores, listeners, exclude=[], k=4)) == [1, 2, 3, 0]


def test_top_k_exclude():
    scores = [0.5, 0.9, 0.5, 0.5, 0.1]
    listeners = [10, 1, 30, 30, 99]
    assert list(top_k(scores, listeners, exclude=[1, 2], k=3)) == [3, 0, 4]


def test_top_k_ties_at_boundary():
    # 경계 점수가 같은 아티스트가 여럿이어도 동점 규칙대로 골라야 한다
    scores = [1.0, 0.2, 0.2, 0.2, 0.2]
    listeners = [0, 1, 5, 3, 5]
    assert list(top_k(scores, listeners, exclude=[], k=2)) == [0, 2]


def test_item_coverage():
    assert item_coverage([[0, 1], [1, 2]], catalog_size=10) == 0.3


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print(f"통과: {test.__name__}")
    print(f"{len(tests)}개 모두 통과")
