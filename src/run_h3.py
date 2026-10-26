"""H3 실험: CF 위에서 H2와 같은 비교 (report/실험설계.md 6, 6.1, 9절).

단계 (앞 단계를 먼저 돌려야 한다)
1. python src/run_h3.py --stage tune     CF 설정(요인 수, 정규화) 고르기
   ALS를 전체 학습 사용자로 학습하고, H2 대상이 아닌 나라(사용자 100명 이상)의 검증 사용자로 CF만의 NDCG@10을 본다.
2. python src/run_h3.py --stage models   나라 묶음별 ALS 21개 학습 (data/processed/cf/에 저장)
3. python src/run_h3.py --stage valid    새 나라 t마다 빌려올 나라의 검증 곡선을 만들고 비중을 고른다
4. python src/run_h3.py --stage test     고른 비중으로 t의 시험 사용자를 평가한다

나라 묶음 (9절): H2 대상 나라를 사용자 수 순으로 정렬해 차례로 N_CF_GROUPS개 묶음에 넣는다.
- t(묶음 g) 평가: g를 뺀 ALS
- t에 빌려줄 c(묶음 h)의 곡선: g와 h를 뺀 ALS (h = g이면 g를 뺀 ALS)
인기 점수 쪽 조건(전체 인기, 순위 대상, 동점용 청취자 수, 초기 사용자)은 H2와 같다.
"""

import argparse
from itertools import combinations

import numpy as np
import pandas as pd

from cf import CFModel, evaluate_mix, prepare_users, train_cf
from config import (
    CF_FACTORS_GRID,
    CF_REG_GRID,
    N_CF_GROUPS,
    N_EARLY_REPEATS,
    N_EARLY_USERS,
    PROCESSED_DIR,
    TABLES_DIR,
    TOP_K,
    WEIGHT_GRID,
    WVS_NEIGHBORS_K,
)
from popularity import listener_counts, load_popularity_data
from run_h2 import Conditions, choose_weights, h2_countries, method_values
from seeds import seeded_rng
from stats import paired_summary
from wvs_distance import country_index_means, nearest_countries

CF_DIR = PROCESSED_DIR / "cf"

# H2의 방법 이름 -> H3에서의 이름. 고르는 규칙은 같고 섞는 대상만 전체 인기 대신 CF다
RENAME = {
    "P0_global": "C0_cf",
    "P1_country": "C_country_only",
    "P2_common": "C1_common",
    "P3_oracle": "C_oracle",
    "P4_wvs": "C2_wvs",
    "P5_random": "C3_random",
}
H3_METHODS = list(RENAME.values())


def output_name(name):
    return f"h3_{name}"


def country_groups(targets):
    """H2 대상 나라(사용자 수 순으로 정렬됨) -> 묶음 번호."""
    return {iso3: position % N_CF_GROUPS for position, iso3 in enumerate(targets)}


def model_key(groups):
    return "_".join(f"g{group}" for group in sorted(set(groups)))


def all_model_keys():
    singles = [(g,) for g in range(N_CF_GROUPS)]
    pairs = list(combinations(range(N_CF_GROUPS), 2))
    return [model_key(groups) for groups in singles + pairs]


def load_model(key):
    return CFModel.load(CF_DIR / f"{key}.npz")


def cf_settings():
    settings = pd.read_csv(TABLES_DIR / output_name("cf_settings.csv"))
    return int(settings.loc[0, "factors"]), float(settings.loc[0, "regularization"])


# ---------- 1. CF 설정 고르기 ----------


def run_tune(data):
    counts = pd.read_csv(TABLES_DIR / "split_counts.csv", keep_default_na=False)
    tune_countries = counts.loc[counts["in_h1"] & ~counts["in_h2"], "iso3"].tolist()
    all_countries = list(data.country_listeners)
    listeners = listener_counts(data, all_countries)
    global_share = listeners / sum(data.country_train_users.values())
    no_country = np.zeros(len(data.universe))
    mask = listeners > 0

    rows = []
    for factors in CF_FACTORS_GRID:
        for regularization in CF_REG_GRID:
            model = train_cf(data, all_countries, factors, regularization)
            per_country = []
            for iso3 in tune_countries:
                users = prepare_users(data, model, iso3)
                ndcg, _, _, _ = evaluate_mix(
                    data, model, users, 0.0, no_country, global_share, listeners, mask, iso3, TOP_K
                )
                per_country.append(ndcg.mean())
            rows.append((factors, regularization, float(np.mean(per_country)), len(per_country)))
            print(f"설정 factors={factors}, reg={regularization}: NDCG@10 {rows[-1][2]:.4f}")
    tuning = pd.DataFrame(rows, columns=["factors", "regularization", "ndcg", "n_countries"])
    tuning.to_csv(TABLES_DIR / output_name("cf_tuning.csv"), index=False)
    # 가장 높은 설정. 같으면 표의 앞쪽(요인 수, 정규화가 작은 쪽)
    best = tuning.loc[[int(np.flatnonzero(tuning["ndcg"] >= tuning["ndcg"].max() - 1e-12)[0])]]
    best[["factors", "regularization"]].to_csv(TABLES_DIR / output_name("cf_settings.csv"), index=False)
    print(best.to_string(index=False))


# ---------- 2. 나라 묶음별 ALS ----------


def run_models(data, targets):
    CF_DIR.mkdir(parents=True, exist_ok=True)
    factors, regularization = cf_settings()
    groups = country_groups(targets)
    all_countries = list(data.country_listeners)
    rows = []
    for key in all_model_keys():
        removed_groups = {int(part[1:]) for part in key.split("_")}
        removed = sorted(iso3 for iso3, group in groups.items() if group in removed_groups)
        countries = [iso3 for iso3 in all_countries if iso3 not in removed]
        model = train_cf(data, countries, factors, regularization)
        model.save(CF_DIR / f"{key}.npz")
        rows.append((key, " ".join(removed), int(model.in_model.sum())))
        print(f"ALS {key} 학습 완료 (뺀 나라 {len(removed)}개)")
    table = pd.DataFrame(rows, columns=["model", "removed_countries", "artists_in_model"])
    table.to_csv(TABLES_DIR / output_name("cf_models.csv"), index=False)


# ---------- 3. 검증 단계 ----------


def run_valid(data, targets, n_early, k):
    groups = country_groups(targets)
    conditions = Conditions(data, targets, n_early)
    means = country_index_means()

    # 어떤 ALS로 어떤 (t, c) 곡선을 만드는지 정리. ALS를 한 번씩만 불러오려고 ALS별로 묶는다
    jobs = {key: [] for key in all_model_keys()}
    for target in targets:
        for country in targets:
            role = "self" if country == target else "donor"
            jobs[model_key([groups[target], groups[country]])].append((target, country, role))

    curves, fallback_rows, exact_users = {}, [], 0
    for number, (key, pairs) in enumerate(jobs.items(), start=1):
        model = load_model(key)
        prepared = {}
        for target, country, role in pairs:
            if country not in prepared:
                prepared[country] = prepare_users(data, model, country)
                fallback_rows.append((key, country, int((~prepared[country].usable).sum()), len(prepared[country].rows)))
            users = prepared[country]
            excluded = [target] if role == "self" else [target, country]
            curve = np.zeros((N_EARLY_REPEATS, len(WEIGHT_GRID)))
            for repeat in range(N_EARLY_REPEATS):
                global_share, country_share, tie, mask = conditions.make(excluded, country, repeat)
                for column, weight in enumerate(WEIGHT_GRID):
                    ndcg, _, _, n_exact = evaluate_mix(
                        data, model, users, weight, country_share, global_share, tie, mask, country, TOP_K
                    )
                    curve[repeat, column] = ndcg.mean()
                    exact_users += n_exact
            curves[(target, country)] = curve.mean(axis=0)
        print(f"검증 ALS {number}/{len(jobs)} ({key}): 곡선 {len(pairs)}개 완료")

    curve_rows, weight_rows, draw_rows = [], [], []
    for target in targets:
        pool = [iso3 for iso3 in targets if iso3 != target]
        donor = {c: curves[(target, c)] for c in pool}
        own = curves[(target, target)]
        for c, curve in donor.items():
            curve_rows.extend((target, "donor", c, w, v) for w, v in zip(WEIGHT_GRID, curve))
        curve_rows.extend((target, "self", target, w, v) for w, v in zip(WEIGHT_GRID, own))
        neighbors = nearest_countries(means, target, pool, k)
        # 무작위 나라는 H2와 같은 시드라서 같은 나라 조합이 뽑힌다
        fixed, draws = choose_weights(donor, own, neighbors, pool, seeded_rng("random", target, k), k)
        neighbor_text = " ".join(f"{iso3}:{distance:.3f}" for iso3, distance in neighbors)
        for method, weight in fixed.items():
            weight_rows.append((target, method, weight, neighbor_text if method == "P4_wvs" else ""))
        draw_rows.extend((target, draw, " ".join(chosen), weight) for draw, (chosen, weight) in enumerate(draws))

    pd.DataFrame(curve_rows, columns=["target", "role", "country", "w", "ndcg"]).to_csv(
        TABLES_DIR / output_name("valid_curves.csv"), index=False
    )
    weights = pd.DataFrame(weight_rows, columns=["target", "method", "w", "detail"])
    weights.to_csv(TABLES_DIR / output_name("weights.csv"), index=False)
    draws = pd.DataFrame(draw_rows, columns=["target", "draw", "countries", "w"])
    draws.to_csv(TABLES_DIR / output_name("random_draws.csv"), index=False)
    fallback = pd.DataFrame(fallback_rows, columns=["model", "country", "fallback_users", "users"])
    fallback.to_csv(TABLES_DIR / output_name("valid_fallback.csv"), index=False)

    chosen = weights.pivot(index="target", columns="method", values="w").rename(columns=RENAME)
    distribution = pd.DataFrame(
        {method: chosen[method].value_counts() for method in ["C1_common", "C_oracle", "C2_wvs"]}
    ).reindex(WEIGHT_GRID).fillna(0).astype(int)
    distribution["C3_random(뽑기 전체)"] = draws["w"].value_counts().reindex(WEIGHT_GRID).fillna(0).astype(int)
    lines = [
        f"# H3 검증 단계 결과 (초기 사용자 {n_early}명, 유사국 {k}개)",
        "",
        "`python src/run_h3.py --stage valid`로 만든 파일. 시험 사용자는 아직 쓰지 않았다.",
        "",
        f"- CF 설정: factors={cf_settings()[0]}, regularization={cf_settings()[1]}",
        f"- fold-in에 쓸 아티스트가 없어 전체 인기로 대체한 검증 사용자: {fallback['fallback_users'].sum()}명 "
        f"(ALS·나라 조합 {len(fallback)}개에 걸친 연인원 {fallback['users'].sum()}명 중)",
        f"- 빠른 계산 대신 전체 계산으로 평가한 사용자: 연인원 {exact_users}명",
        "",
        "## 방법별로 고른 w의 분포 (나라 수)",
        distribution.rename_axis("w").to_markdown(),
        "",
        "## 새 나라별 비중",
        chosen[[m for m in H3_METHODS if m != "C3_random"]].to_markdown(),
        "",
    ]
    (TABLES_DIR / output_name("valid.md")).write_text("\n".join(lines), encoding="utf-8")


# ---------- 4. 시험 단계 ----------


def run_test(data, targets, n_early):
    weights_path = TABLES_DIR / output_name("weights.csv")
    if not weights_path.exists():
        raise SystemExit("검증 단계를 먼저 돌려야 한다: python src/run_h3.py --stage valid")
    weights = pd.read_csv(weights_path, keep_default_na=False)
    draws = pd.read_csv(TABLES_DIR / output_name("random_draws.csv"), keep_default_na=False)
    groups = country_groups(targets)
    conditions = Conditions(data, targets, n_early)

    repeat_rows, fallback_rows, exact_users = [], [], 0
    for group in range(N_CF_GROUPS):
        model = load_model(model_key([group]))
        for target in [iso3 for iso3 in targets if groups[iso3] == group]:
            users = prepare_users(data, model, target)
            fallback_rows.append((target, int((~users.usable).sum()), len(users.rows)))
            fixed = weights[weights["target"] == target].set_index("method")["w"]
            needed = sorted(set(fixed) | set(draws.loc[draws["target"] == target, "w"]))
            for repeat in range(N_EARLY_REPEATS):
                global_share, country_share, tie, mask = conditions.make([target], target, repeat)
                for weight in needed:
                    ndcg, recall, items, n_exact = evaluate_mix(
                        data, model, users, weight, country_share, global_share, tie, mask, target, TOP_K
                    )
                    exact_users += n_exact
                    repeat_rows.append(
                        (target, repeat, weight, ndcg.mean(), recall.mean(), len(items) / mask.sum(), len(ndcg))
                    )
        print(f"시험 묶음 {group + 1}/{N_CF_GROUPS} 완료")

    by_repeat = pd.DataFrame(
        repeat_rows, columns=["target", "repeat", "w", "ndcg", "recall", "coverage", "n_users"]
    )
    by_repeat.to_csv(TABLES_DIR / output_name("test_by_repeat.csv"), index=False)
    fallback = pd.DataFrame(fallback_rows, columns=["target", "fallback_users", "users"])
    fallback.to_csv(TABLES_DIR / output_name("test_fallback.csv"), index=False)

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
    )
    results["method"] = results["method"].map(RENAME)
    results = results[["target", "method", "w", "ndcg", "recall", "coverage", "ndcg_sd_over_repeats"]]
    results.to_csv(TABLES_DIR / output_name("test_by_country.csv"), index=False)

    ndcg = results.pivot(index="target", columns="method", values="ndcg")
    h2 = pd.read_csv(TABLES_DIR / "h2_test_by_country.csv", keep_default_na=False)
    h2_ndcg = h2.pivot(index="target", columns="method", values="ndcg").reindex(ndcg.index)
    comparisons = {
        "주: C2 - C1 (CF+WVS 비중 - CF+공통 비중)": ndcg["C2_wvs"] - ndcg["C1_common"],
        "보조: C2 - C0 (CF+WVS 비중 - CF만)": ndcg["C2_wvs"] - ndcg["C0_cf"],
        "보조: C2 - C3 (CF+WVS 비중 - CF+무작위 나라 비중)": ndcg["C2_wvs"] - ndcg["C3_random"],
        "참고: C1 - C0 (CF+공통 비중 - CF만)": ndcg["C1_common"] - ndcg["C0_cf"],
        "참고: C_oracle - C1 (상한 - 공통)": ndcg["C_oracle"] - ndcg["C1_common"],
        "참고: C0 - P0 (CF만 - 전체 인기, H2 결과 사용)": ndcg["C0_cf"] - h2_ndcg["P0_global"],
        "참고: C1 - P2 (CF+공통 - 인기+공통, H2 결과 사용)": ndcg["C1_common"] - h2_ndcg["P2_common"],
    }
    summary = pd.DataFrame(
        [{"비교": name, **paired_summary(diff.to_numpy())} for name, diff in comparisons.items()]
    )
    summary.to_csv(TABLES_DIR / output_name("test_summary.csv"), index=False)

    by_method = results.groupby("method")[["ndcg", "recall", "coverage", "ndcg_sd_over_repeats"]].mean()
    lines = [
        f"# H3 시험 결과 (초기 사용자 {n_early}명)",
        "",
        "`python src/run_h3.py --stage test`로 만든 파일.",
        "",
        f"- fold-in에 쓸 아티스트가 없어 전체 인기로 대체한 시험 사용자: {fallback['fallback_users'].sum()}명 / {fallback['users'].sum()}명. 나라별은 `{output_name('test_fallback.csv')}`",
        f"- 빠른 계산 대신 전체 계산으로 평가한 사용자: 연인원 {exact_users}명",
        "",
        "## 방법별 평균 (나라마다 같은 무게)",
        by_method.reindex(H3_METHODS).round(4).to_markdown(),
        "",
        "## 나라별 차이 (NDCG@10)",
        "신뢰구간은 나라 사이의 차이로 생기는 불확실성만 나타낸다. Holm 보정은 H1~H3 주 비교 p값이 모두 나온 뒤 한다.",
        "",
        summary.round(4).to_markdown(index=False),
        "",
    ]
    (TABLES_DIR / output_name("test.md")).write_text("\n".join(lines), encoding="utf-8")
    print(summary.round(4).to_string(index=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["tune", "models", "valid", "test"], required=True)
    args = parser.parse_args()

    print("자료 준비 중...")
    data = load_popularity_data("test" if args.stage == "test" else "valid")
    targets = h2_countries()["iso3"].tolist()
    if args.stage == "tune":
        run_tune(data)
    elif args.stage == "models":
        run_models(data, targets)
    elif args.stage == "valid":
        run_valid(data, targets, N_EARLY_USERS, WVS_NEIGHBORS_K)
    else:
        run_test(data, targets, N_EARLY_USERS)


if __name__ == "__main__":
    main()
