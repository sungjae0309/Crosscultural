"""Last.fm 360K 원본 파일을 읽어서 정리된 표로 돌려주는 함수 모음.

원본 파일 형식 (데이터 README.txt와 파일을 직접 열어서 확인함)
- 두 파일 모두 탭 구분, 첫 줄에 컬럼 이름 없음, UTF-8
- usersha1-profile.tsv: 사용자ID, 성별, 나이, 나라, 가입일
- usersha1-artmbid-artname-plays.tsv: 사용자ID, 아티스트 mbid, 아티스트 이름, 재생 횟수
"""

import csv

import pandas as pd

from config import RAW_LASTFM_DIR

LASTFM_DIR = RAW_LASTFM_DIR / "lastfm-dataset-360K"
PROFILE_PATH = LASTFM_DIR / "usersha1-profile.tsv"
PLAYS_PATH = LASTFM_DIR / "usersha1-artmbid-artname-plays.tsv"

PROFILE_COLUMNS = ["user_id", "gender", "age", "country", "signup"]
PLAYS_COLUMNS = ["user_id", "artist_mbid", "artist_name", "plays"]


def _read_tsv(path, column_names, dtype):
    # 아티스트 이름에 따옴표가 섞여 있어서 따옴표 해석을 끈다
    # 빈 칸을 NaN 대신 빈 문자열로 받아야 "값 없음"을 일관되게 다룰 수 있다
    return pd.read_csv(
        path,
        sep="\t",
        header=None,
        names=column_names,
        quoting=csv.QUOTE_NONE,
        dtype=dtype,
        keep_default_na=False,
    )


def load_profiles():
    """사용자 프로필 표. 한 줄 = 사용자 한 명."""
    profiles = _read_tsv(PROFILE_PATH, PROFILE_COLUMNS, dtype=str)
    profiles["country"] = profiles["country"].str.strip()
    return profiles


def load_plays():
    """사용자-아티스트 재생 기록 표. 한 줄 = (사용자, 아티스트) 한 쌍.

    정리 규칙
    - artist_id: mbid가 있으면 mbid, 없으면 "name:" + 아티스트 이름.
      같은 mbid가 여러 이름 표기로 나오는 경우가 많아서 mbid를 우선한다.
    - 같은 사용자-아티스트가 여러 줄이면 재생 횟수를 합친다.
    - 재생 횟수가 0 이하인 줄은 "들었다"고 볼 수 없어서 뺀다.
    """
    raw_plays = _read_tsv(
        PLAYS_PATH,
        PLAYS_COLUMNS,
        dtype={"user_id": str, "artist_mbid": str, "artist_name": str, "plays": "int64"},
    )

    has_mbid = raw_plays["artist_mbid"] != ""
    raw_plays["artist_id"] = raw_plays["artist_mbid"].where(
        has_mbid, "name:" + raw_plays["artist_name"]
    )

    raw_plays = raw_plays[raw_plays["plays"] > 0]

    # 보고서에서 아티스트 이름을 보여줄 때 쓰려고 대표 이름 하나를 남긴다
    plays = raw_plays.groupby(["user_id", "artist_id"], as_index=False).agg(
        artist_name=("artist_name", "first"),
        plays=("plays", "sum"),
    )
    return plays
