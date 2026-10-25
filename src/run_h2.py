"""H2 실험: 새 나라에 어떤 비중을 쓸지 (report/실험설계.md 8절).

H2 대상 나라를 하나씩 새 나라 t로 두고, t의 학습 사용자 중 초기 사용자 N명만 있는 상황을 만든다.

두 단계로 나눠 돌린다. 시험 사용자는 비중을 다 고른 뒤 한 번만 쓰기 위해서다.
1. 검증 단계: python src/run_h2.py --stage valid  (20분쯤)
   t마다 빌려올 나라 c의 검증 곡선(w별 검증 NDCG@10)을 만들고 P2, P3, P4, P5의 비중을 고른다.
2. 시험 단계: python src/run_h2.py --stage test
   고른 비중을 그대로 읽어서 t의 시험 사용자로 비교한다.

보조 분석: --early-users 20, --neighbors 1 등 (결과 파일 이름에 붙는다)

조건 (8.1, 8.2절)
- t를 평가할 때: 전체 인기 = t를 뺀 모든 나라의 학습 사용자. 나라 인기 = t의 초기 사용자.
  순위 대상과 동점용 청취자 수 = t를 뺀 학습 사용자 + t의 초기 사용자.
- t에 빌려줄 나라 c의 곡선: 위와 같은 방식에서 t와 c를 모두 빼고, c의 초기 사용자를 쓴다.
- 초기 사용자 뽑기는 N_EARLY_REPEATS번 반복하고, 곡선과 시험 결과 모두 반복을 먼저 평균 낸다.
"""

import argparse

import numpy as np
import pandas as pd

from config import (
    GLOBAL_TOP_N,
    LOCAL_TOP_N,
    N_EARLY_REPEATS,
    N_EARLY_USERS,
    N_RANDOM_REPEATS,
    TABLES_DIR,
    TOP_K,
    WEIGHT_GRID,
    WVS_NEIGHBORS_K,
)
from metrics import top_k
from popularity import (
    evaluate_shared_scores,
    listener_counts,
    load_popularity_data,
    pick_early_users,
    relevant_in_catalog_share,
    user_listener_counts,
)
from run_h1 import best_weight
from seeds import seeded_rng
from stats import paired_summary
from wvs_distance import country_index_means, nearest_countries

METHODS = ["P0_global", "P1_country", "P2_common", "P3_oracle", "P4_wvs", "P5_random"]


def h2_countries():
    counts = pd.read_csv(TABLES_DIR / "split_counts.csv", keep_default_na=False)
    return counts[counts["in_h2"]].reset_index(drop=True)


def output_name(name, n_early, k):
    parts = ["h2"]
    if n_early != N_EARLY_USERS:
        parts.append(f"early{n_early}")
    if k != WVS_NEIGHBORS_K:
        parts.append(f"k{k}")
    return "_".join(parts) + "_" + name


class Conditions:
    """조건별 인기 점수 재료를 만든다. 초기 사용자 청취자 수는 한 번만 센다."""

    def __init__(self, data, targets, n_early):
        self.data = data
        self.n_early = n_early
        all_countries = list(data.country_listeners)
        self.total_listeners = listener_counts(data, all_countries)
        self.total_users = sum(data.country_train_users[iso3] for iso3 in all_countries)
        self.early_counts = {
            (iso3, repeat): user_listener_counts(data, pick_early_users(data, iso3, n_early, repeat))
            for iso3 in targets
            for repeat in range(N_EARLY_REPEATS)
        }

    def make(self, excluded, early_country, repeat):
        """(전체 인기, 나라 인기, 동점용 청취자 수, 순위 대상) for 이 조건."""
        listeners = self.total_listeners.copy()
        users = self.total_users
        for iso3 in excluded:
            listeners -= self.data.country_listeners[iso3]
            users -= self.data.country_train_users[iso3]
        early = self.early_counts[(early_country, repeat)]
        global_share = listeners / users
        country_share = early / self.n_early
        tie_listeners = listeners + early
        return global_share, country_share, tie_listeners, tie_listeners > 0


def valid_curve(data, conditions, country, excluded):
    """그 나라 검증 사용자의 w별 NDCG@10. 반복을 평균 낸 값."""
    curves = np.zeros((N_EARLY_REPEATS, len(WEIGHT_GRID)))
    for repeat in range(N_EARLY_REPEATS):
        global_share, country_share, tie, mask = conditions.make(excluded, country, repeat)
        for column, weight in enumerate(WEIGHT_GRID):
            scores = (1 - weight) * global_share + weight * country_share
            ndcg, _, _ = evaluate_shared_scores(data, scores, tie, country, TOP_K, mask)
            curves[repeat, column] = ndcg.mean()
    return curves.mean(axis=0)


def choose_weights(donor_curves, own_curve, neighbors, pool, rng, k):
    """검증 곡선으로 방법별 w를 고른다 (설계 8.3절).

    donor_curves: 빌려줄 나라 -> w별 검증 NDCG (WEIGHT_GRID 순). own_curve: t 자신의 곡선.
    여러 나라를 쓸 때는 그 나라들 곡선의 평균이 가장 높은 w를 고른다.
    돌려주는 값: (방법 -> w, [(무작위로 뽑은 나라 목록, w), ...])
    """

    def pooled_best(countries):
        return best_weight(WEIGHT_GRID, np.mean([donor_curves[c] for c in countries], axis=0))

    fixed = {
        "P0_global": 0.0,
        "P1_country": 1.0,
        "P2_common": pooled_best(pool),
        "P3_oracle": best_weight(WEIGHT_GRID, own_curve),
        "P4_wvs": pooled_best([iso3 for iso3, _ in neighbors]),
    }
    draws = []
    for _ in range(N_RANDOM_REPEATS):
        chosen = sorted(str(iso3) for iso3 in rng.choice(pool, size=k, replace=False))
        draws.append((chosen, pooled_best(chosen)))
    return fixed, draws


def method_values(target_repeats, fixed, draw_weights):
    """한 나라의 반복별 시험 결과에서 방법별 값을 가져온다.

    target_repeats: repeat, w, ndcg, recall, coverage 열. 방법마다 검증 단계에서 정한 w의 행만 쓴다.
    P5는 뽑기마다 고른 w의 값을 (같은 w가 여러 번 뽑혔으면 그 횟수만큼) 평균 낸다.
    반복을 먼저 평균 내고, 반복 사이 표준편차도 돌려준다.
    """
    indexed = target_repeats.set_index(["repeat", "w"])[["ndcg", "recall", "coverage"]]
    repeats = sorted(target_repeats["repeat"].unique())
    rows = []
    for method in METHODS:
        chosen = list(draw_weights) if method == "P5_random" else [fixed[method]]
        per_repeat = np.array(
            [indexed.loc[[(repeat, w) for w in chosen]].mean().to_numpy() for repeat in repeats]
        )
        rows.append(
            {
                "method": method,
                "w": fixed.get(method, np.nan),
                "ndcg": per_repeat[:, 0].mean(),
                "recall": per_repeat[:, 1].mean(),
                "coverage": per_repeat[:, 2].mean(),
                "ndcg_sd_over_repeats": per_repeat[:, 0].std(ddof=1) if len(repeats) > 1 else 0.0,
            }
        )
    return pd.DataFrame(rows)


def local_taste_share(data, target):
    """자기 나라 취향 대리 지표 (실패 분석용, 학습 사용자만 사용).

    t 학습 사용자 상위 LOCAL_TOP_N개 아티스트 중, t를 뺀 나라 학습 사용자 상위 GLOBAL_TOP_N개에 없는 비율.
    """
    own = data.country_listeners[target]
    others = listener_counts(data, [iso3 for iso3 in data.country_listeners if iso3 != target])
    local_top = top_k(own.astype(float), own, exclude=[], k=LOCAL_TOP_N)
    global_top = set(top_k(others.astype(float), others, exclude=[], k=GLOBAL_TOP_N).tolist())
    return float(np.mean([index not in global_top for index in local_top]))


def run_valid(data, targets, n_early, k):
    conditions = Conditions(data, targets, n_early)
    means = country_index_means()

    curve_rows, weight_rows, draw_rows = [], [], []
    for number, target in enumerate(targets, start=1):
        pool = [iso3 for iso3 in targets if iso3 != target]
        donor = {c: valid_curve(data, conditions, c, excluded=[target, c]) for c in pool}
        own = valid_curve(data, conditions, target, excluded=[target])
        for c, curve in donor.items():
            curve_rows.extend((target, "donor", c, w, v) for w, v in zip(WEIGHT_GRID, curve))
        curve_rows.extend((target, "self", target, w, v) for w, v in zip(WEIGHT_GRID, own))

        neighbors = nearest_countries(means, target, pool, k)
        fixed, draws = choose_weights(donor, own, neighbors, pool, seeded_rng("random", target, k), k)
        neighbor_text = " ".join(f"{iso3}:{distance:.3f}" for iso3, distance in neighbors)
        for method, weight in fixed.items():
            detail = neighbor_text if method == "P4_wvs" else ""
            nearest = neighbors[0][1] if method == "P4_wvs" else np.nan
            weight_rows.append((target, method, weight, detail, nearest))
        draw_rows.extend((target, draw, " ".join(chosen), weight) for draw, (chosen, weight) in enumerate(draws))
        print(f"검증 {number}/{len(targets)}: {target} 완료")

    curves = pd.DataFrame(curve_rows, columns=["target", "role", "country", "w", "ndcg"])
    weights = pd.DataFrame(weight_rows, columns=["target", "method", "w", "detail", "nearest_distance"])
    draws = pd.DataFrame(draw_rows, columns=["target", "draw", "countries", "w"])
    curves.to_csv(TABLES_DIR / output_name("valid_curves.csv", n_early, k), index=False)
    weights.to_csv(TABLES_DIR / output_name("weights.csv", n_early, k), index=False)
    draws.to_csv(TABLES_DIR / output_name("random_draws.csv", n_early, k), index=False)

    chosen = weights.pivot(index="target", columns="method", values="w")
    distribution = pd.DataFrame(
        {method: chosen[method].value_counts() for method in ["P2_common", "P3_oracle", "P4_wvs"]}
    ).reindex(WEIGHT_GRID).fillna(0).astype(int)
    distribution["P5_random(뽑기 전체)"] = draws["w"].value_counts().reindex(WEIGHT_GRID).fillna(0).astype(int)
    lines = [
        f"# H2 검증 단계 결과 (초기 사용자 {n_early}명, 유사국 {k}개)",
        "",
        "`python src/run_h2.py --stage valid`로 만든 파일. 시험 사용자는 아직 쓰지 않았다.",
        "",
        "## 방법별로 고른 w의 분포 (나라 수)",
        distribution.rename_axis("w").to_markdown(),
        "",
        "## 새 나라별 비중과 WVS 유사국",
        weights.pivot(index="target", columns="method", values="w")[METHODS[:5]].join(
            weights[weights["method"] == "P4_wvs"].set_index("target")["detail"].rename("WVS 유사국:거리")
        ).to_markdown(),
        "",
    ]
    (TABLES_DIR / output_name("valid.md", n_early, k)).write_text("\n".join(lines), encoding="utf-8")


def run_test(data, targets, countries, n_early, k):
    weights_path = TABLES_DIR / output_name("weights.csv", n_early, k)
    if not weights_path.exists():
        raise SystemExit("검증 단계를 먼저 돌려야 한다: python src/run_h2.py --stage valid")
    weights = pd.read_csv(weights_path, keep_default_na=False)
    draws = pd.read_csv(TABLES_DIR / output_name("random_draws.csv", n_early, k), keep_default_na=False)
    conditions = Conditions(data, targets, n_early)

    repeat_rows, overlap_rows = [], []
    for number, target in enumerate(targets, start=1):
        fixed = weights[weights["target"] == target].set_index("method")["w"]
        needed = sorted(set(fixed) | set(draws.loc[draws["target"] == target, "w"]))
        for repeat in range(N_EARLY_REPEATS):
            global_share, country_share, tie, mask = conditions.make([target], target, repeat)
            overlap_rows.append((target, repeat, relevant_in_catalog_share(data, target, mask).mean()))
            for weight in needed:
                scores = (1 - weight) * global_share + weight * country_share
                ndcg, recall, items = evaluate_shared_scores(data, scores, tie, target, TOP_K, mask)
                repeat_rows.append(
                    (target, repeat, weight, ndcg.mean(), recall.mean(), len(items) / mask.sum(), len(ndcg))
                )
        print(f"시험 {number}/{len(targets)}: {target} 완료")

    by_repeat = pd.DataFrame(
        repeat_rows, columns=["target", "repeat", "w", "ndcg", "recall", "coverage", "n_users"]
    )
    by_repeat.to_csv(TABLES_DIR / output_name("test_by_repeat.csv", n_early, k), index=False)
    overlap = pd.DataFrame(overlap_rows, columns=["target", "repeat", "relevant_in_catalog"])

    # 방법마다 w는 검증 단계에서 정해졌다. 그 w의 시험 값을 반복 평균으로 가져온다
    results = pd.concat(
        [
            method_values(
                by_repeat[by_repeat["target"] == target],
                weights[weights["target"] == target].set_index("method")["w"].to_dict(),
                draws.loc[draws["target"] == target, "w"].to_numpy(),
            ).assign(target=target)
            for target in targets
        ],
        ignore_index=True,
    )[["target", "method", "w", "ndcg", "recall", "coverage", "ndcg_sd_over_repeats"]]
    results.to_csv(TABLES_DIR / output_name("test_by_country.csv", n_early, k), index=False)

    ndcg = results.pivot(index="target", columns="method", values="ndcg")
    comparisons = {
        "주: P4 - P2 (WVS 유사국 - 공통)": ndcg["P4_wvs"] - ndcg["P2_common"],
        "보조: P4 - P5 (WVS 유사국 - 무작위 나라)": ndcg["P4_wvs"] - ndcg["P5_random"],
        "보조: P4 - P1 (WVS 유사국 - 나라 인기만)": ndcg["P4_wvs"] - ndcg["P1_country"],
        "참고: P2 - P0 (공통 - 전체 인기)": ndcg["P2_common"] - ndcg["P0_global"],
        "참고: P3 - P2 (상한 - 공통)": ndcg["P3_oracle"] - ndcg["P2_common"],
    }
    summary = pd.DataFrame(
        [{"비교": name, **paired_summary(diff.to_numpy())} for name, diff in comparisons.items()]
    )
    summary.to_csv(TABLES_DIR / output_name("test_summary.csv", n_early, k), index=False)

    # 실패 분석 재료 (12절): WVS 비중이 공통보다 나빴던 나라를 따로 본다
    wvs_rows = weights[weights["method"] == "P4_wvs"].set_index("target")
    chosen = weights.pivot(index="target", columns="method", values="w")
    failure = pd.DataFrame(
        {
            "users": countries.set_index("iso3").loc[targets, "users"],
            "relevant_in_catalog": overlap.groupby("target")["relevant_in_catalog"].mean(),
            "local_taste_share": pd.Series({target: local_taste_share(data, target) for target in targets}),
            "nearest_wvs_distance": wvs_rows["nearest_distance"].astype(float),
            "wvs_neighbors": wvs_rows["detail"],
            "w_P2": chosen["P2_common"],
            "w_P4": chosen["P4_wvs"],
            "w_P3_oracle": chosen["P3_oracle"],
            "diff_P4_minus_P2": ndcg["P4_wvs"] - ndcg["P2_common"],
        }
    ).rename_axis("target")
    failure["w_gap_P4_vs_oracle"] = (failure["w_P4"] - failure["w_P3_oracle"]).abs()
    failure.to_csv(TABLES_DIR / output_name("failure_analysis.csv", n_early, k))

    by_method = results.groupby("method")[["ndcg", "recall", "coverage", "ndcg_sd_over_repeats"]].mean()
    lines = [
        f"# H2 시험 결과 (초기 사용자 {n_early}명, 유사국 {k}개)",
        "",
        "`python src/run_h2.py --stage test`로 만든 파일.",
        "",
        "## 방법별 평균 (나라마다 같은 무게)",
        "ndcg_sd_over_repeats: 초기 사용자 뽑기 반복 사이의 표준편차 (나라별 값의 평균).",
        "",
        by_method.reindex(METHODS).round(4).to_markdown(),
        "",
        "## 나라별 차이 (NDCG@10)",
        "신뢰구간은 나라 사이의 차이로 생기는 불확실성만 나타낸다. Holm 보정은 H1~H3 주 비교 p값이 모두 나온 뒤 한다.",
        "",
        summary.round(4).to_markdown(index=False),
        "",
        "## 실패 분석: WVS 비중이 공통 비중보다 나빴던 나라",
        "전체 목록은 `" + output_name("failure_analysis.csv", n_early, k) + "`.",
        "",
        failure[failure["diff_P4_minus_P2"] < 0].sort_values("diff_P4_minus_P2").round(4).to_markdown(),
        "",
    ]
    (TABLES_DIR / output_name("test.md", n_early, k)).write_text("\n".join(lines), encoding="utf-8")
    print(summary.round(4).to_string(index=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["valid", "test"], required=True)
    parser.add_argument("--early-users", type=int, default=N_EARLY_USERS)
    parser.add_argument("--neighbors", type=int, default=WVS_NEIGHBORS_K)
    args = parser.parse_args()

    print("자료 준비 중...")
    data = load_popularity_data(args.stage)
    countries = h2_countries()
    targets = countries["iso3"].tolist()
    if args.stage == "valid":
        run_valid(data, targets, args.early_users, args.neighbors)
    else:
        run_test(data, targets, countries, args.early_users, args.neighbors)


if __name__ == "__main__":
    main()
