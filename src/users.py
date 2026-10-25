"""사용자 단위 표: 한 줄 = 사용자 한 명 (나라, ISO 코드, 들은 아티스트 수)."""

from config import EXCLUDED_ISO3
from country_codes import country_name_to_iso3


def build_user_table(profiles, plays):
    """(남길 사용자 표, 제외한 국가값의 사용자 표)를 돌려준다.

    프로필과 재생 기록이 둘 다 있는 사용자만 쓴다.
    실제 거주지로 보기 어려운 국가값(config.EXCLUDED_ISO3)의 사용자는 따로 뺀다.
    """
    artists_per_user = plays.groupby("user_id").size().rename("n_artists")
    users = profiles.merge(artists_per_user, left_on="user_id", right_index=True, how="inner")

    iso_results = {name: country_name_to_iso3(name) for name in users["country"].unique()}
    users["iso3"] = users["country"].map(lambda name: iso_results[name][0])
    users["iso_match"] = users["country"].map(lambda name: iso_results[name][1])

    is_excluded = users["iso3"].isin(EXCLUDED_ISO3)
    return users[~is_excluded].copy(), users[is_excluded].copy()
