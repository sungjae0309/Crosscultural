"""데이터 확인: 실험에 쓸 만큼 나라와 사용자가 충분한지 숫자로 본다.

실행: python src/check_data.py
결과: results/tables/ 아래 CSV 파일들과 data_check.md
"""

import pandas as pd

from config import (
    EXCLUDED_ISO3,
    MIN_ARTISTS_EVAL_USER,
    MIN_USERS_PER_COUNTRY,
    TABLES_DIR,
    WVS_CSV_PATH,
    WVS_INDEX_COLUMNS,
)
from country_codes import country_name_to_iso3
from load_lastfm import load_plays, load_profiles
from load_wvs import load_wvs

# 나라를 몇 명 기준으로 자를지 감을 잡으려고 여러 기준을 한 번에 본다
USER_COUNT_THRESHOLDS = [50, 100, 200, 500, 1000]


def wvs_country_table(country_user_counts):
    """WVS 나라별 응답자 수, 지표 응답 비율, Last.fm 사용자 수를 한 표로."""
    wvs = load_wvs(WVS_INDEX_COLUMNS)
    by_country = wvs.groupby(["V2", "iso3"])
    table = by_country.size().rename("wvs_respondents").reset_index()
    for name in WVS_INDEX_COLUMNS:
        valid_share = by_country[name].count() / by_country.size() * 100
        table[f"{name}_valid_pct"] = valid_share.round(0).values
    lastfm_users = country_user_counts.dropna(subset=["iso3"])[["iso3", "country", "users"]]
    table = table.merge(lastfm_users, on="iso3", how="left")
    table["users"] = table["users"].fillna(0).astype(int)
    return table.sort_values("users", ascending=False)


def main():
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    print("프로필 읽는 중...")
    profiles = load_profiles()
    print("재생 기록 읽는 중... (1.6GB라 30초쯤 걸림)")
    plays = load_plays()

    # ---------- 사용자 단위 표 만들기 ----------
    artists_per_user = plays.groupby("user_id").size().rename("n_artists")
    users = profiles.merge(artists_per_user, left_on="user_id", right_index=True, how="inner")

    iso_results = {name: country_name_to_iso3(name) for name in users["country"].unique()}
    users["iso3"] = users["country"].map(lambda name: iso_results[name][0])
    users["iso_match"] = users["country"].map(lambda name: iso_results[name][1])

    # 실제 거주지로 보기 어려운 국가값은 이후 모든 표에서 뺀다
    is_excluded = users["iso3"].isin(EXCLUDED_ISO3)
    excluded_users = users[is_excluded]
    users = users[~is_excluded]

    users_with_country = users[users["country"] != ""]
    users_with_iso = users_with_country[users_with_country["iso3"].notna()]

    # ---------- 1. 전체 요약 ----------
    summary = pd.DataFrame(
        [
            ("프로필에 있는 사용자", len(profiles)),
            ("재생 기록이 있는 사용자", plays["user_id"].nunique()),
            ("프로필과 재생 기록이 둘 다 있는 사용자", len(users) + len(excluded_users)),
            ("그중 제외한 국가값의 사용자", len(excluded_users)),
            ("제외 후 남은 사용자", len(users)),
            ("그중 국가 정보가 있는 사용자", len(users_with_country)),
            ("그중 ISO 나라 코드로 바뀐 사용자", len(users_with_iso)),
            ("나라 수 (Last.fm 표기 기준)", users_with_country["country"].nunique()),
            ("아티스트 수 (정리 후)", plays["artist_id"].nunique()),
            ("사용자-아티스트 쌍 수 (정리 후)", len(plays)),
            (
                f"아티스트가 {MIN_ARTISTS_EVAL_USER}개 미만이라 평가에 못 쓰는 사용자",
                int((users_with_iso["n_artists"] < MIN_ARTISTS_EVAL_USER).sum()),
            ),
        ],
        columns=["항목", "값"],
    )

    # ---------- 2. 나라별 사용자 수 ----------
    country_user_counts = (
        users_with_country.groupby(["country", "iso3", "iso_match"], dropna=False)
        .agg(
            users=("user_id", "size"),
            median_artists_per_user=("n_artists", "median"),
        )
        .reset_index()
        .sort_values("users", ascending=False)
    )
    country_user_counts.to_csv(TABLES_DIR / "country_user_counts.csv", index=False)

    # ---------- 3. 기준 사용자 수별로 남는 나라 수 ----------
    threshold_rows = []
    for threshold in USER_COUNT_THRESHOLDS:
        kept = country_user_counts[country_user_counts["users"] >= threshold]
        threshold_rows.append((threshold, len(kept), int(kept["users"].sum())))
    threshold_table = pd.DataFrame(
        threshold_rows, columns=["최소 사용자 수", "남는 나라 수", "남는 사용자 합"]
    )

    # ---------- 4. 사용자당 아티스트 수 분포 ----------
    artist_count_bins = [0, 5, 10, 20, 30, 40, 50, 60, 80, 1000]
    artist_count_distribution = (
        pd.cut(users_with_iso["n_artists"], bins=artist_count_bins)
        .value_counts()
        .sort_index()
        .rename_axis("사용자당 아티스트 수 구간")
        .reset_index(name="사용자 수")
    )
    artist_count_distribution["사용자당 아티스트 수 구간"] = artist_count_distribution[
        "사용자당 아티스트 수 구간"
    ].astype(str)
    artist_count_describe = (
        users_with_iso["n_artists"]
        .describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])
        .round(1)
        .rename_axis("통계")
        .reset_index(name="값")
    )
    artist_count_distribution.to_csv(TABLES_DIR / "artists_per_user_distribution.csv", index=False)

    # ---------- 5. ISO 코드로 못 바꾼 나라 ----------
    unmatched_countries = country_user_counts[country_user_counts["iso3"].isna()]
    manual_countries = country_user_counts[country_user_counts["iso_match"] == "manual"]
    excluded_counts = (
        excluded_users.groupby(["country", "iso3"]).size().rename("users").reset_index()
        .sort_values("users", ascending=False)
    )

    # ---------- 6. WVS 연결 ----------
    if WVS_CSV_PATH.exists():
        print("WVS 읽는 중...")
        wvs_table = wvs_country_table(country_user_counts)
        wvs_table.to_csv(TABLES_DIR / "wvs_lastfm_common_countries.csv", index=False)
        common_count_table = pd.DataFrame(
            {
                "Last.fm 최소 사용자 수": USER_COUNT_THRESHOLDS,
                "WVS와 공통인 나라 수": [
                    int((wvs_table["users"] >= threshold).sum())
                    for threshold in USER_COUNT_THRESHOLDS
                ],
            }
        )
        unmapped = wvs_table[wvs_table["iso3"].isna()]
        wvs_section = "\n".join(
            [
                f"WVS 나라 수: {len(wvs_table)}. "
                f"ISO 코드로 못 바꾼 WVS 나라: {len(unmapped)}개. "
                "음수 결측 코드는 빼고 응답 비율을 셌다.",
                "",
                common_count_table.to_markdown(index=False),
                "",
                "전체 목록 (`wvs_lastfm_common_countries.csv`)",
                "",
                wvs_table.to_markdown(index=False),
            ]
        )
    else:
        wvs_section = f"`{WVS_CSV_PATH.name}`이 없어서 이 단계는 건너뛰었다."

    # ---------- 결과를 마크다운 한 파일로 ----------
    main_countries = country_user_counts[country_user_counts["users"] >= MIN_USERS_PER_COUNTRY]
    report_lines = [
        "# 데이터 확인 결과",
        "",
        "`python src/check_data.py`로 만든 파일. 직접 고치지 말고 코드를 다시 돌린다.",
        "",
        "## 1. 전체 요약",
        summary.to_markdown(index=False),
        "",
        "## 2. 사용자당 아티스트 수",
        "ISO 코드가 있는 사용자 기준.",
        "",
        artist_count_describe.to_markdown(index=False),
        "",
        artist_count_distribution.to_markdown(index=False),
        "",
        "## 3. 최소 사용자 수 기준에 따라 남는 나라",
        threshold_table.to_markdown(index=False),
        "",
        f"## 4. 사용자 {MIN_USERS_PER_COUNTRY}명 이상인 나라 ({len(main_countries)}개)",
        "전체 목록은 `country_user_counts.csv`.",
        "",
        main_countries.to_markdown(index=False),
        "",
        "## 5. 나라 이름 맞추기",
        "### 수동으로 ISO 코드를 지정한 나라",
        manual_countries.to_markdown(index=False) if len(manual_countries) else "없음",
        "",
        "### ISO 코드로 못 바꾼 나라",
        unmatched_countries.to_markdown(index=False) if len(unmatched_countries) else "없음",
        "",
        "### 제외한 국가값",
        "실제 거주지로 보기 어려워 뺐다. 목록은 `config.EXCLUDED_ISO3`. 위 표들은 모두 제외 후 숫자다.",
        "",
        excluded_counts.to_markdown(index=False) if len(excluded_counts) else "없음",
        "",
        "## 6. WVS Wave 5와 공통 나라",
        wvs_section,
        "",
    ]
    report_path = TABLES_DIR / "data_check.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print(summary.to_string(index=False))
    print(threshold_table.to_string(index=False))
    print(f"\n저장: {report_path}")


if __name__ == "__main__":
    main()
