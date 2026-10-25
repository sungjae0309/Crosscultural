"""WVS 가치관으로 나라 사이 거리 재기 (report/실험설계.md 10절).

- 나라값: 응답자 가중치(V259)를 쓴 나라별 평균. 결측은 지표마다 뺀다.
- 거리: 지표를 표준화한 뒤 유클리드 거리. 표준화의 평균과 표준편차(표본 표준편차)는
  새 나라 t를 뺀 후보 나라 풀로 구하고, t에는 같은 변환만 적용한다.
"""

import numpy as np
import pandas as pd

from config import WVS_INDEX_COLUMNS, WVS_WEIGHT_COLUMN
from load_wvs import load_wvs


def country_index_means():
    """나라(iso3)별 WVS 지표의 가중 평균 표."""
    wvs = load_wvs(WVS_INDEX_COLUMNS + [WVS_WEIGHT_COLUMN])
    rows = []
    for iso3, group in wvs.groupby("iso3", sort=True):
        row = {"iso3": iso3}
        for column in WVS_INDEX_COLUMNS:
            usable = group[column].notna() & group[WVS_WEIGHT_COLUMN].notna()
            row[column] = (
                np.average(group.loc[usable, column], weights=group.loc[usable, WVS_WEIGHT_COLUMN])
                if usable.any()
                else np.nan
            )
        rows.append(row)
    return pd.DataFrame(rows).set_index("iso3")


def nearest_countries(means, target, pool, k):
    """target과 가장 가까운 pool 나라 k개. [(iso3, 거리), ...] 가까운 순.

    거리가 같으면 iso3 순으로 정한다.
    """
    pool = [iso3 for iso3 in pool if iso3 != target]
    values = means.loc[pool + [target], WVS_INDEX_COLUMNS]
    if values.isna().any().any():
        raise ValueError("WVS 지표가 비어 있는 나라가 있다: " + ", ".join(values.index[values.isna().any(axis=1)]))
    pool_values = values.loc[pool]
    center = pool_values.mean()
    scale = pool_values.std(ddof=1)
    standardized_pool = (pool_values - center) / scale
    standardized_target = (values.loc[target] - center) / scale
    distance = np.sqrt(((standardized_pool - standardized_target) ** 2).sum(axis=1))
    ordered = sorted(distance.items(), key=lambda item: (item[1], item[0]))
    return [(iso3, float(value)) for iso3, value in ordered[:k]]
