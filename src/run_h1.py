"""H1 실험: 나라별 비중 vs 공통 비중 (report/실험설계.md 7절).

두 단계로 나눠 돌린다. 시험 사용자는 비중을 다 고른 뒤 한 번만 쓰기 위해서다.

1. 검증 단계: python src/run_h1.py --stage valid
   나라마다 w별 검증 NDCG@10을 계산하고, 나라별 비중 w_c와 공통 비중을 고른다.
2. 시험 단계: python src/run_h1.py --stage test
   검증 단계에서 고른 비중을 그대로 읽어서 시험 사용자로 P0~P3를 비교한다.

인기 기준을 바꾼 보조 분석: --measure plays (결과 파일 이름에 _plays가 붙는다)

비중을 고를 때 검증 NDCG가 같은 w가 여럿이면 작은 w(전체 인기에 가까운 쪽)를 고른다.
"""

import argparse

import numpy as np
import pandas as pd

from config import (
    FIGURES_DIR,
    H1_SIZE_BINS,
    POPULARITY_MEASURE,
    TABLES_DIR,
    TOP_K,
    WEIGHT_GRID,
)
from metrics import item_coverage
from popularity import (
    evaluate_shared_scores,
    listener_counts,
    load_popularity_data,
    popularity_share,
    relevant_in_catalog_share,
)
from stats import paired_summary


def h1_countries():
    counts = pd.read_csv(TABLES_DIR / "split_counts.csv", keep_default_na=False)
    return counts[counts["in_h1"]].reset_index(drop=True)


def output_name(name, measure):
    suffix = "" if measure == POPULARITY_MEASURE else f"_{measure}"
    return f"h1{suffix}_{name}"


def best_weight(weights, ndcg_values):
    """NDCG가 가장 높은 w. 같으면 작은 w."""
    ndcg_values = np.asarray(ndcg_values)
    best = ndcg_values.max()
    return weights[int(np.flatnonzero(ndcg_values >= best - 1e-12)[0])]


def mixed_scores(global_share, country_share, weight):
    return (1 - weight) * global_share + weight * country_share


def run_valid(data, countries, measure):
    all_countries = list(data.country_listeners)
    global_share = popularity_share(data, all_countries, measure)
    tie_listeners = listener_counts(data, all_countries)
    valid_users = data.eval_users[data.eval_users["split"] == "valid"]

    rows = []
    for country in countries.itertuples():
        country_share = popularity_share(data, [country.iso3], measure)
        user_ids = valid_users.loc[valid_users["iso3"] == country.iso3, "user_id"]
        for weight in WEIGHT_GRID:
            scores = mixed_scores(global_share, country_share, weight)
            ndcg, recall, _ = evaluate_shared_scores(data, scores, tie_listeners, user_ids, TOP_K)
            rows.append((country.iso3, weight, ndcg.mean(), recall.mean(), len(user_ids)))
        print(f"검증: {country.iso3} 완료")
    curves = pd.DataFrame(rows, columns=["iso3", "w", "ndcg", "recall", "n_users"])
    curves.to_csv(TABLES_DIR / output_name("valid_curves.csv", measure), index=False)

    weights = []
    for iso3, curve in curves.groupby("iso3", sort=False):
        w_country = best_weight(curve["w"].to_numpy(), curve["ndcg"].to_numpy())
        weights.append((iso3, w_country))
    weights = countries[["country", "iso3", "users"]].merge(
        pd.DataFrame(weights, columns=["iso3", "w_country"]), on="iso3"
    )

    # 공통 비중: 나라마다 같은 무게로 평균 (주 분석), 검증 사용자 수 가중 (보조)
    macro = curves.groupby("w")["ndcg"].mean()
    weighted = curves.assign(total=curves["ndcg"] * curves["n_users"]).groupby("w")
    user_weighted = weighted["total"].sum() / weighted["n_users"].sum()
    common = pd.DataFrame(
        [
            ("common_macro", best_weight(macro.index.to_numpy(), macro.to_numpy())),
            ("common_user_weighted", best_weight(user_weighted.index.to_numpy(), user_weighted.to_numpy())),
        ],
        columns=["name", "w"],
    )
    weights.to_csv(TABLES_DIR / output_name("weights.csv", measure), index=False)
    common.to_csv(TABLES_DIR / output_name("common_weights.csv", measure), index=False)

    lines = [
        f"# H1 검증 단계 결과 (인기 기준: {measure})",
        "",
        "`python src/run_h1.py --stage valid`로 만든 파일. 시험 사용자는 아직 쓰지 않았다.",
        "",
        "## 공통 비중",
        common.to_markdown(index=False),
        "",
        "## 나라별 비중 w_c의 분포 (설명용)",
        weights["w_country"].value_counts().sort_index().rename_axis("w").reset_index(name="나라 수").to_markdown(index=False),
        "",
        "## 나라별 비중",
        weights.to_markdown(index=False),
        "",
    ]
    (TABLES_DIR / output_name("valid.md", measure)).write_text("\n".join(lines), encoding="utf-8")
    print(common.to_string(index=False))


def size_bin_labels(users):
    edges = H1_SIZE_BINS + [np.inf]
    labels = [f"{low:,}~{high - 1:,}" if np.isfinite(high) else f"{low:,} 이상" for low, high in zip(edges[:-1], edges[1:])]
    return pd.cut(users, bins=edges, right=False, labels=labels)


def run_test(data, countries, measure):
    weights_path = TABLES_DIR / output_name("weights.csv", measure)
    if not weights_path.exists():
        raise SystemExit("검증 단계를 먼저 돌려야 한다: python src/run_h1.py --stage valid")
    weights = pd.read_csv(weights_path, keep_default_na=False).set_index("iso3")["w_country"]
    common = pd.read_csv(TABLES_DIR / output_name("common_weights.csv", measure)).set_index("name")["w"]

    all_countries = list(data.country_listeners)
    global_share = popularity_share(data, all_countries, measure)
    tie_listeners = listener_counts(data, all_countries)
    test_users = data.eval_users[data.eval_users["split"] == "test"]

    methods = {
        "P0_global": lambda iso3: 0.0,
        "P1_country": lambda iso3: 1.0,
        "P2_common": lambda iso3: common["common_macro"],
        "P2u_common_user_weighted": lambda iso3: common["common_user_weighted"],
        "P3_country_weight": lambda iso3: weights[iso3],
    }
    rows, recommended, overlap_rows = [], {name: set() for name in methods}, []
    for country in countries.itertuples():
        country_share = popularity_share(data, [country.iso3], measure)
        user_ids = test_users.loc[test_users["iso3"] == country.iso3, "user_id"]
        overlap_rows.append((country.iso3, relevant_in_catalog_share(data, user_ids).mean()))
        for name, weight_of in methods.items():
            weight = weight_of(country.iso3)
            scores = mixed_scores(global_share, country_share, weight)
            ndcg, recall, items = evaluate_shared_scores(data, scores, tie_listeners, user_ids, TOP_K)
            recommended[name].update(items)
            rows.append((country.iso3, name, weight, ndcg.mean(), recall.mean(), len(user_ids)))
    results = pd.DataFrame(rows, columns=["iso3", "method", "w", "ndcg", "recall", "n_users"])
    results.to_csv(TABLES_DIR / output_name("test_by_country.csv", measure), index=False)
    overlap = pd.DataFrame(overlap_rows, columns=["iso3", "relevant_in_catalog"])
    overlap.to_csv(TABLES_DIR / output_name("item_overlap.csv", measure), index=False)

    by_method = results.groupby("method").agg(ndcg=("ndcg", "mean"), recall=("recall", "mean"))
    by_method["coverage"] = [
        item_coverage([list(recommended[name])], len(data.catalog)) for name in by_method.index
    ]

    ndcg = results.pivot(index="iso3", columns="method", values="ndcg")
    comparisons = {
        "주: P3 - P2 (나라별 - 공통)": ndcg["P3_country_weight"] - ndcg["P2_common"],
        "보조: P3 - P2u (나라별 - 사용자 가중 공통)": ndcg["P3_country_weight"] - ndcg["P2u_common_user_weighted"],
        "보조: P2 - P0 (공통 - 전체 인기)": ndcg["P2_common"] - ndcg["P0_global"],
        "보조: P1 - P0 (나라 인기 - 전체 인기)": ndcg["P1_country"] - ndcg["P0_global"],
    }
    summary = pd.DataFrame(
        [{"비교": name, **paired_summary(diff.to_numpy())} for name, diff in comparisons.items()]
    )
    summary.to_csv(TABLES_DIR / output_name("test_summary.csv", measure), index=False)

    primary = (ndcg["P3_country_weight"] - ndcg["P2_common"]).rename("diff").reset_index()
    primary = primary.merge(countries[["iso3", "users"]], on="iso3")
    primary["size"] = size_bin_labels(primary["users"])
    by_size = pd.DataFrame(
        [
            {"나라 크기(사용자 수)": str(label), **paired_summary(group["diff"].to_numpy())}
            for label, group in primary.groupby("size", observed=True)
        ]
    )

    plot_weights(weights, countries, measure)

    lines = [
        f"# H1 시험 결과 (인기 기준: {measure})",
        "",
        "`python src/run_h1.py --stage test`로 만든 파일.",
        "",
        "## 방법별 평균 (나라마다 같은 무게)",
        by_method.round(4).to_markdown(),
        "",
        "## 나라별 차이 (NDCG@10)",
        "Holm 보정은 H1~H3 주 비교 p값이 모두 나온 뒤 한꺼번에 한다.",
        "",
        summary.round(4).to_markdown(index=False),
        "",
        "## 주 비교를 나라 크기별로",
        by_size.round(4).to_markdown(index=False),
        "",
        "## 아이템 겹침",
        "시험 사용자의 정답 중 순위 대상(학습 사용자가 들은 아티스트)에 들어 있는 비율. 나라별 평균의 요약.",
        "전체 목록은 `" + output_name("item_overlap.csv", measure) + "`.",
        "",
        overlap["relevant_in_catalog"].describe().round(4).rename_axis("통계").reset_index(name="값").to_markdown(index=False),
        "",
    ]
    (TABLES_DIR / output_name("test.md", measure)).write_text("\n".join(lines), encoding="utf-8")
    print(summary.round(4).to_string(index=False))


def plot_weights(weights, countries, measure):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    frame = countries[["iso3", "users"]].merge(weights.rename("w_country").reset_index(), on="iso3")
    figure, axis = plt.subplots(figsize=(6, 4))
    axis.scatter(frame["users"], frame["w_country"], s=18)
    axis.set_xscale("log")
    axis.set_xlabel("Last.fm users in country (log scale)")
    axis.set_ylabel("country weight w_c (chosen on validation)")
    axis.set_title("H1: country weight vs country size")
    figure.tight_layout()
    figure.savefig(FIGURES_DIR / output_name("weights_vs_size.png", measure), dpi=150)
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["valid", "test"], required=True)
    parser.add_argument("--measure", choices=["listeners", "plays"], default=POPULARITY_MEASURE)
    args = parser.parse_args()

    print("자료 준비 중...")
    data = load_popularity_data(args.stage)
    countries = h1_countries()
    if args.stage == "valid":
        run_valid(data, countries, args.measure)
    else:
        run_test(data, countries, args.measure)


if __name__ == "__main__":
    main()
