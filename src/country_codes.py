"""나라 이름을 ISO 3166 세 글자 코드(예: KOR)로 바꾸는 함수.

Last.fm과 WVS는 나라 이름 표기가 서로 다를 수 있어서,
이름끼리 바로 맞추지 않고 ISO 코드로 바꾼 뒤에 연결한다.
"""

import pycountry

# pycountry가 자동으로 못 찾은 Last.fm 나라 이름 (데이터를 직접 돌려서 확인한 목록)
# 옛날 이름이거나 표기가 조금 달라서 생긴 문제다
MANUAL_ISO3 = {
    "Turkey": "TUR",
    "Macedonia": "MKD",
    "Reunion": "REU",
    "Palestinian Territory, Occupied": "PSE",
    "Cote D'Ivoire": "CIV",
    "Cape Verde": "CPV",
    "Netherlands Antilles": "ANT",  # 2010년에 해체된 지역. 지금 ISO 목록에는 없음
    "Saint Helena": "SHN",
    "Libyan Arab Jamahiriya": "LBY",
    "Swaziland": "SWZ",
}


def country_name_to_iso3(country_name):
    """나라 이름 -> (ISO3 코드, 찾은 방법). 못 찾으면 (None, "unmatched")."""
    if country_name in MANUAL_ISO3:
        return MANUAL_ISO3[country_name], "manual"
    try:
        return pycountry.countries.lookup(country_name).alpha_3, "auto"
    except LookupError:
        return None, "unmatched"
