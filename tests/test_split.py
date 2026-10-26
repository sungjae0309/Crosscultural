"""src/split_users.py 확인용 테스트. 가짜 데이터로 나누기 규칙만 본다.

실행: python tests/test_split.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config import (  # noqa: E402
    MIN_ARTISTS_EVAL_USER,
    N_SHOWN_ARTISTS,
    TEST_USER_RATIO,
    VALID_USER_RATIO,
)
from split_users import pick_shown_artists, split_users  # noqa: E402


def _fake_users():
    rows = []
    for iso3, n_users in [("AAA", 200), ("BBB", 37), ("CCC", 3)]:
        for index in range(n_users):
            # 열 명 중 한 명은 아티스트가 적은 사용자
            n_artists = 4 if index % 10 == 0 else 30
            rows.append((f"{iso3}-{index:04d}", "Country " + iso3, iso3, n_artists))
    return pd.DataFrame(rows, columns=["user_id", "country", "iso3", "n_artists"])


def test_few_artists_go_to_train():
    users = split_users(_fake_users())
    few = users["n_artists"] < MIN_ARTISTS_EVAL_USER
    assert (users.loc[few, "split"] == "train").all()


def test_each_user_has_one_split():
    users = split_users(_fake_users())
    assert users["user_id"].is_unique
    assert set(users["split"]) <= {"train", "valid", "test"}


def test_split_sizes_per_country():
    users = split_users(_fake_users())
    eligible = users[users["n_artists"] >= MIN_ARTISTS_EVAL_USER]
    for iso3, group in eligible.groupby("iso3"):
        counts = group["split"].value_counts()
        assert counts.get("valid", 0) == round(len(group) * VALID_USER_RATIO), iso3
        assert counts.get("test", 0) == round(len(group) * TEST_USER_RATIO), iso3


def test_split_ignores_row_order_and_other_countries():
    base = split_users(_fake_users()).set_index("user_id")["split"]
    shuffled = _fake_users().sample(frac=1, random_state=1)
    assert split_users(shuffled).set_index("user_id")["split"].equals(base.sort_index())
    # 다른 나라를 빼도 남은 나라의 결과는 그대로
    only_aaa = _fake_users().query("iso3 == 'AAA'")
    aaa = split_users(only_aaa).set_index("user_id")["split"]
    assert aaa.equals(base[aaa.index])


def _fake_plays():
    rows = []
    for user_index in range(30):
        for artist_index in range(10 + user_index % 7):
            rows.append((f"u{user_index:03d}", f"a{(user_index * 3 + artist_index) % 50:03d}"))
    return pd.DataFrame(rows, columns=["user_id", "artist_id"])


def test_shown_artists():
    plays = _fake_plays()
    user_ids = plays["user_id"].unique()
    shown = pick_shown_artists(plays, user_ids)
    assert (shown.groupby("user_id").size() == N_SHOWN_ARTISTS).all()
    assert set(shown["user_id"]) == set(user_ids)
    # 보여준 아티스트는 그 사용자가 실제로 들은 것이어야 한다
    listened = set(map(tuple, plays[["user_id", "artist_id"]].to_numpy()))
    assert all(pair in listened for pair in map(tuple, shown.to_numpy()))
    assert not shown.duplicated().any()


def test_shown_artists_stable_per_user():
    plays = _fake_plays()
    user_ids = plays["user_id"].unique()
    everyone = pick_shown_artists(plays, user_ids).set_index(["user_id", "artist_id"])
    half = pick_shown_artists(plays, user_ids[10:]).set_index(["user_id", "artist_id"])
    # 다른 사용자가 빠져도 각 사용자의 선택은 그대로
    assert set(half.index) <= set(everyone.index)


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print(f"통과: {test.__name__}")
    print(f"{len(tests)}개 모두 통과")
