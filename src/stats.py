"""나라 단위 비교 통계 (report/실험설계.md 11절).

모든 비교는 나라 하나를 표본 하나로 둔다.
"""

import numpy as np
from scipy.stats import wilcoxon

from config import N_BOOTSTRAP, RANDOM_SEED


def paired_summary(differences, n_bootstrap=N_BOOTSTRAP, seed=RANDOM_SEED):
    """나라별 차이(방법 A - 방법 B)의 요약.

    - 평균, 중앙값, 좋아진 나라 / 나빠진 나라 비율
    - 평균의 95% 부트스트랩 신뢰구간 (나라를 다시 뽑기). 나라 사이의 차이로 생기는 불확실성만 나타낸다
    - Wilcoxon 부호순위 검정 p값 (양측, 차이 0은 Pratt 방식). 보조 검정
    """
    differences = np.asarray(differences, dtype=float)
    if differences.ndim != 1 or len(differences) == 0 or not np.isfinite(differences).all():
        raise ValueError("차이는 비어 있지 않은 1차원 유한값 배열이어야 한다")
    n = len(differences)

    rng = np.random.default_rng(seed)
    resampled = differences[rng.integers(0, n, size=(n_bootstrap, n))]
    ci_low, ci_high = np.percentile(resampled.mean(axis=1), [2.5, 97.5])

    if np.all(differences == 0):
        p_value = 1.0
    else:
        p_value = float(wilcoxon(differences, zero_method="pratt", alternative="two-sided").pvalue)

    return {
        "n_countries": n,
        "mean_diff": float(differences.mean()),
        "median_diff": float(np.median(differences)),
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
        "share_better": float((differences > 0).mean()),
        "share_worse": float((differences < 0).mean()),
        "wilcoxon_p": p_value,
    }


def holm_adjust(p_values):
    """Holm 보정 p값. 입력 순서대로 돌려준다."""
    p_values = np.asarray(p_values, dtype=float)
    m = len(p_values)
    order = np.argsort(p_values)
    adjusted = np.empty(m)
    running_max = 0.0
    for rank, index in enumerate(order):
        running_max = max(running_max, (m - rank) * p_values[index])
        adjusted[index] = min(1.0, running_max)
    return adjusted
