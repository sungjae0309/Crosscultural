"""H1~H3 주 비교를 한 표로 모으고 Holm 보정을 한다 (report/실험설계.md 11절).

실행: python src/summarize_results.py  (H1~H3 시험 단계를 모두 돌린 뒤)
결과: results/tables/final_summary.md, final_summary.csv
"""

import pandas as pd

from config import ALPHA, TABLES_DIR
from stats import holm_adjust

PRIMARY = [
    ("H1", "h1_test_summary.csv", "나라별 비중 - 공통 비중 (인기 모델, 75개국)"),
    ("H2", "h2_test_summary.csv", "WVS 유사국 비중 - 공통 비중 (인기 모델, 새 나라 42개국)"),
    ("H3", "h3_test_summary.csv", "CF + WVS 유사국 비중 - CF + 공통 비중 (새 나라 42개국)"),
]


def main():
    rows = []
    for hypothesis, file_name, description in PRIMARY:
        summary = pd.read_csv(TABLES_DIR / file_name)
        primary = summary[summary["비교"].str.startswith("주:")]
        if len(primary) != 1:
            raise SystemExit(f"{file_name}에 주 비교가 하나여야 한다")
        rows.append({"가설": hypothesis, "주 비교": description, **primary.iloc[0].drop("비교").to_dict()})
    table = pd.DataFrame(rows)
    table["holm_p"] = holm_adjust(table["wilcoxon_p"].to_numpy())
    table[f"Holm 보정 후 유의 (α={ALPHA})"] = table["holm_p"] < ALPHA
    table["신뢰구간이 0을 포함"] = (table["ci_low"] <= 0) & (table["ci_high"] >= 0)
    table.to_csv(TABLES_DIR / "final_summary.csv", index=False)

    lines = [
        "# H1~H3 주 비교 요약",
        "",
        "`python src/summarize_results.py`로 만든 파일. NDCG@10의 나라별 차이.",
        "신뢰구간(95%, 나라 부트스트랩)과 효과 크기를 먼저 해석하고, Wilcoxon p값은 보조로 본다 (설계 11절).",
        "",
        table.round(4).to_markdown(index=False),
        "",
    ]
    (TABLES_DIR / "final_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(table.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
