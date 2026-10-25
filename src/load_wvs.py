"""WVS Wave 5 CSV(v20180912)를 읽는 함수.

파일을 직접 열어서 확인한 형식:
- 구분자는 세미콜론(;), 첫 줄에 BOM이 있고 줄바꿈은 CRLF
- 한 줄이 응답자 한 명. 83,975명, 414개 열, 58개 나라
- 소수점이 쉼표로 적혀 있고 앞의 0이 빠져 있다 (예: ",942961" = 0.942961)
- 값이 없으면 빈칸(" ")이다
- 음수(-1 ~ -5)는 모름, 무응답, 질문 안 함 같은 결측 코드다 (코드북 기준)
- V2는 ISO 3166 숫자 나라 코드다 (예: 410 = 한국)
"""

import pandas as pd
import pycountry

from config import WVS_CSV_PATH


def _to_number(column):
    """쉼표 소수점과 빈칸이 섞인 열을 숫자로 바꾼다. 빈칸은 NaN."""
    text = column.astype(str).str.strip().str.replace(",", ".", regex=False)
    return pd.to_numeric(text.where(text != ""), errors="coerce")


def iso_numeric_to_iso3(code):
    """V2 숫자 코드 -> ISO3. 못 찾으면 None."""
    country = pycountry.countries.get(numeric=f"{int(code):03d}")
    return country.alpha_3 if country else None


def load_wvs(columns):
    """필요한 열만 읽는다. V2는 항상 포함하고 iso3 열을 붙인다.

    음수 결측 코드는 NaN으로 바꾼다. V2는 나라 코드라 그대로 둔다.
    """
    use_columns = ["V2"] + [name for name in columns if name != "V2"]
    wvs = pd.read_csv(
        WVS_CSV_PATH,
        sep=";",
        encoding="utf-8-sig",
        usecols=use_columns,
        dtype=str,
    )
    for name in use_columns:
        wvs[name] = _to_number(wvs[name])
        if name != "V2":
            wvs[name] = wvs[name].where(wvs[name] >= 0)
    wvs["V2"] = wvs["V2"].astype(int)
    wvs["iso3"] = wvs["V2"].map(iso_numeric_to_iso3)
    return wvs
