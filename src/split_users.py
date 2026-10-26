"""사용자를 학습 / 검증 / 시험으로 나누고, 평가 사용자에게 보여줄 아티스트를 고른다.
(report/실험설계.md 3, 4절)

실행: python src/split_users.py
결과
- data/processed/user_split.csv: user_id, iso3, split(train/valid/test), n_artists
- data/processed/shown_artists.csv: 검증·시험 사용자에게 보여준 아티스트 (user_id, artist_id)
- results/tables/split_counts.csv, split_counts.md: 나라별 사용자 수와 H1/H2 대상 여부

규칙
- 아티스트가 MIN_ARTISTS_EVAL_USER개 미만인 사용자는 평가에 못 쓰므로 모두 학습으로 보낸다.
- 나머지 사용자는 나라마다 학습 70% / 검증 15% / 시험 15%로 무작위로 나눈다.
- 무작위 시드는 나라마다 RANDOM_SEED와 나라 코드로 따로 만든다.
  그래서 다른 나라가 추가되거나 빠져도 한 나라의 나누기 결과는 바뀌지 않는다.
- 보여줄 아티스트는 사용자마다 N_SHOWN_ARTISTS개를 무작위로 고른다. 나머지가 정답이다.
  이것도 사용자마다 RANDOM_SEED와 user_id로 시드를 따로 만든다.
"""

import pandas as pd

from config import (
    MIN_ARTISTS_EVAL_USER,
    MIN_USERS_H2,
    MIN_USERS_PER_COUNTRY,
    N_SHOWN_ARTISTS,
    PROCESSED_DIR,
    TABLES_DIR,
    TEST_USER_RATIO,
    VALID_USER_RATIO,
)
from load_lastfm import load_plays, load_profiles
from load_wvs import load_wvs
from seeds import seeded_rng
from users import build_user_table


def split_users(users):
    """users에 split 열을 붙여 돌려준다."""
    users = users.sort_values("user_id").reset_index(drop=True)
    users["split"] = "train"

    can_evaluate = users["n_artists"] >= MIN_ARTISTS_EVAL_USER
    for iso3, group in users[can_evaluate].groupby("iso3", sort=True):
        shuffled = group.index.to_numpy()[seeded_rng("split", iso3).permutation(len(group))]
        n_valid = round(len(group) * VALID_USER_RATIO)
        n_test = round(len(group) * TEST_USER_RATIO)
        users.loc[shuffled[:n_valid], "split"] = "valid"
        users.loc[shuffled[n_valid : n_valid + n_test], "split"] = "test"
    return users


def pick_shown_artists(plays, eval_user_ids):
    """평가 사용자마다 보여줄 아티스트 N_SHOWN_ARTISTS개를 무작위로 고른다.

    사용자마다 시드를 따로 만들어서, 다른 사용자가 추가되거나 빠져도 결과가 바뀌지 않는다.
    """
    eval_plays = (
        plays.loc[plays["user_id"].isin(eval_user_ids), ["user_id", "artist_id"]]
        .sort_values(["user_id", "artist_id"])
    )
    shown_rows = []
    for user_id, artist_ids in eval_plays.groupby("user_id", sort=True)["artist_id"]:
        picked = seeded_rng("shown", user_id).choice(
            artist_ids.to_numpy(), size=N_SHOWN_ARTISTS, replace=False
        )
        shown_rows.extend((user_id, artist_id) for artist_id in sorted(picked))
    return pd.DataFrame(shown_rows, columns=["user_id", "artist_id"])


def count_table(users, wvs_iso3):
    """나라별 사용자 수와 H1, H2 대상 여부."""
    counts = (
        users.pivot_table(index=["country", "iso3"], columns="split", values="user_id", aggfunc="size")
        .reindex(columns=["train", "valid", "test"])
        .fillna(0)
        .astype(int)
        .reset_index()
    )
    counts.insert(2, "users", counts[["train", "valid", "test"]].sum(axis=1))
    counts["in_h1"] = counts["users"] >= MIN_USERS_PER_COUNTRY
    counts["in_wvs"] = counts["iso3"].isin(wvs_iso3)
    counts["in_h2"] = counts["in_wvs"] & (counts["users"] >= MIN_USERS_H2)
    return counts.sort_values("users", ascending=False).reset_index(drop=True)


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    print("Last.fm 읽는 중...")
    profiles = load_profiles()
    plays = load_plays()
    users, _ = build_user_table(profiles, plays)
    users = users[users["iso3"].notna()]

    users = split_users(users)
    eval_user_ids = users.loc[users["split"] != "train", "user_id"]
    shown = pick_shown_artists(plays, eval_user_ids)

    # 보여준 개수가 모두 N_SHOWN_ARTISTS개인지, 정답이 남는지 확인
    shown_per_user = shown.groupby("user_id").size()
    assert len(shown_per_user) == len(eval_user_ids)
    assert (shown_per_user == N_SHOWN_ARTISTS).all()
    hidden_per_user = users.set_index("user_id").loc[eval_user_ids, "n_artists"] - N_SHOWN_ARTISTS
    assert (hidden_per_user > 0).all()

    users[["user_id", "iso3", "split", "n_artists"]].to_csv(
        PROCESSED_DIR / "user_split.csv", index=False
    )
    shown.to_csv(PROCESSED_DIR / "shown_artists.csv", index=False)

    wvs_iso3 = set(load_wvs([])["iso3"].dropna())
    counts = count_table(users, wvs_iso3)
    counts.to_csv(TABLES_DIR / "split_counts.csv", index=False)

    h1 = counts[counts["in_h1"]]
    h2 = counts[counts["in_h2"]]
    overall = users["split"].value_counts().reindex(["train", "valid", "test"])
    summary = pd.DataFrame(
        [
            ("전체 사용자", len(users)),
            ("학습", int(overall["train"])),
            ("검증", int(overall["valid"])),
            ("시험", int(overall["test"])),
            (f"아티스트 {MIN_ARTISTS_EVAL_USER}개 미만이라 학습으로만 쓴 사용자",
             int((users["n_artists"] < MIN_ARTISTS_EVAL_USER).sum())),
            ("H1 대상 나라 수", len(h1)),
            ("H2·H3 대상 나라 수", len(h2)),
            ("H2·H3 대상 나라 중 시험 사용자가 가장 적은 수", int(h2["test"].min())),
        ],
        columns=["항목", "값"],
    )
    report_lines = [
        "# 사용자 나누기 결과",
        "",
        "`python src/split_users.py`로 만든 파일. 직접 고치지 말고 코드를 다시 돌린다.",
        "",
        "## 요약",
        summary.to_markdown(index=False),
        "",
        f"## H1 대상 나라 ({len(h1)}개)",
        "users = train + valid + test. 전체 목록은 `split_counts.csv`.",
        "",
        h1.drop(columns=["in_h1"]).to_markdown(index=False),
        "",
    ]
    (TABLES_DIR / "split_counts.md").write_text("\n".join(report_lines), encoding="utf-8")

    print(summary.to_string(index=False))
    print(f"\n저장: {PROCESSED_DIR / 'user_split.csv'}, {PROCESSED_DIR / 'shown_artists.csv'}")
    print(f"저장: {TABLES_DIR / 'split_counts.md'}")


if __name__ == "__main__":
    main()
