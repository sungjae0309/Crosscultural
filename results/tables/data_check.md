# 데이터 확인 결과

`python src/check_data.py`로 만든 파일. 직접 고치지 말고 코드를 다시 돌린다.

## 1. 전체 요약
| 항목                        |        값 |
|:--------------------------|---------:|
| 프로필에 있는 사용자               |   359347 |
| 재생 기록이 있는 사용자             |   359349 |
| 프로필과 재생 기록이 둘 다 있는 사용자    |   359347 |
| 그중 국가 정보가 있는 사용자          |   359347 |
| 그중 ISO 나라 코드로 바뀐 사용자      |   359347 |
| 나라 수 (Last.fm 표기 기준)      |      239 |
| 아티스트 수 (정리 후)             |   268775 |
| 사용자-아티스트 쌍 수 (정리 후)       | 17559161 |
| 아티스트가 5개 이하라 평가에 못 쓰는 사용자 |      283 |

## 2. 사용자당 아티스트 수
ISO 코드가 있는 사용자 기준.

| 통계    |        값 |
|:------|---------:|
| count | 359347   |
| mean  |     48.9 |
| std   |      8.5 |
| min   |      1   |
| 5%    |     36   |
| 25%   |     46   |
| 50%   |     49   |
| 75%   |     51   |
| 95%   |     63   |
| max   |    166   |

| 사용자당 아티스트 수 구간   |   사용자 수 |
|:-----------------|--------:|
| (0, 5]           |     283 |
| (5, 10]          |     527 |
| (10, 20]         |    2268 |
| (20, 30]         |    6535 |
| (30, 40]         |   24273 |
| (40, 50]         |  226510 |
| (50, 60]         |   73390 |
| (60, 80]         |   24004 |
| (80, 1000]       |    1557 |

## 3. 최소 사용자 수 기준에 따라 남는 나라
|   최소 사용자 수 |   남는 나라 수 |   남는 사용자 합 |
|-----------:|----------:|-----------:|
|         50 |       104 |     356659 |
|        100 |        79 |     354910 |
|        200 |        66 |     353112 |
|        500 |        50 |     347595 |
|       1000 |        44 |     343790 |

## 4. 사용자 100명 이상인 나라 (79개)
전체 목록은 `country_user_counts.csv`.

| country                              | iso3   | iso_match   |   users |   median_artists_per_user |
|:-------------------------------------|:-------|:------------|--------:|--------------------------:|
| United States                        | USA    | auto        |   67044 |                      49   |
| Germany                              | DEU    | auto        |   31651 |                      49   |
| United Kingdom                       | GBR    | auto        |   29902 |                      49   |
| Poland                               | POL    | auto        |   20987 |                      48   |
| Russian Federation                   | RUS    | auto        |   19833 |                      46   |
| Brazil                               | BRA    | auto        |   14534 |                      48   |
| Sweden                               | SWE    | auto        |   13122 |                      50   |
| Spain                                | ESP    | auto        |   13051 |                      49   |
| Finland                              | FIN    | auto        |   11579 |                      49   |
| Netherlands                          | NLD    | auto        |    9650 |                      49   |
| Canada                               | CAN    | auto        |    8679 |                      49   |
| France                               | FRA    | auto        |    7529 |                      49   |
| Italy                                | ITA    | auto        |    7525 |                      49   |
| Australia                            | AUS    | auto        |    7135 |                      49   |
| Japan                                | JPN    | auto        |    6637 |                      45   |
| Turkey                               | TUR    | manual      |    6452 |                      47   |
| Norway                               | NOR    | auto        |    5155 |                      49   |
| Mexico                               | MEX    | auto        |    4834 |                      48   |
| Czech Republic                       | CZE    | auto        |    4774 |                      48   |
| Ukraine                              | UKR    | auto        |    4396 |                      45   |
| Belgium                              | BEL    | auto        |    3803 |                      49   |
| Portugal                             | PRT    | auto        |    3196 |                      49   |
| Switzerland                          | CHE    | auto        |    3053 |                      49   |
| Bulgaria                             | BGR    | auto        |    2800 |                      48   |
| Austria                              | AUT    | auto        |    2796 |                      48   |
| Chile                                | CHL    | auto        |    2794 |                      48   |
| Argentina                            | ARG    | auto        |    2640 |                      49   |
| Romania                              | ROU    | auto        |    2636 |                      49   |
| Denmark                              | DNK    | auto        |    2508 |                      49   |
| Hungary                              | HUN    | auto        |    1985 |                      48   |
| Lithuania                            | LTU    | auto        |    1979 |                      48   |
| Croatia                              | HRV    | auto        |    1917 |                      48   |
| Greece                               | GRC    | auto        |    1849 |                      48   |
| Colombia                             | COL    | auto        |    1849 |                      48   |
| Latvia                               | LVA    | auto        |    1736 |                      48   |
| Ireland                              | IRL    | auto        |    1634 |                      49   |
| Slovakia                             | SVK    | auto        |    1566 |                      48   |
| Serbia                               | SRB    | auto        |    1452 |                      49   |
| China                                | CHN    | auto        |    1309 |                      43   |
| New Zealand                          | NZL    | auto        |    1247 |                      49   |
| Belarus                              | BLR    | auto        |    1215 |                      47   |
| Israel                               | ISR    | auto        |    1178 |                      47   |
| Estonia                              | EST    | auto        |    1159 |                      48   |
| India                                | IND    | auto        |    1020 |                      48   |
| Venezuela                            | VEN    | auto        |     745 |                      49   |
| Slovenia                             | SVN    | auto        |     673 |                      48   |
| South Africa                         | ZAF    | auto        |     622 |                      49   |
| Thailand                             | THA    | auto        |     602 |                      45   |
| Indonesia                            | IDN    | auto        |     597 |                      47   |
| Philippines                          | PHL    | auto        |     566 |                      49   |
| Singapore                            | SGP    | auto        |     499 |                      48   |
| Peru                                 | PER    | auto        |     490 |                      48   |
| Taiwan                               | TWN    | auto        |     429 |                      45   |
| Korea, Republic of                   | KOR    | auto        |     427 |                      45   |
| Malaysia                             | MYS    | auto        |     417 |                      46   |
| Hong Kong                            | HKG    | auto        |     372 |                      43   |
| Iceland                              | ISL    | auto        |     368 |                      48   |
| Antarctica                           | ATA    | auto        |     365 |                      49   |
| Costa Rica                           | CRI    | auto        |     325 |                      49   |
| Kazakhstan                           | KAZ    | auto        |     317 |                      43   |
| Macedonia                            | MKD    | manual      |     290 |                      48   |
| Moldova                              | MDA    | auto        |     271 |                      46   |
| Uruguay                              | URY    | auto        |     263 |                      48   |
| Bosnia and Herzegovina               | BIH    | auto        |     253 |                      47   |
| Georgia                              | GEO    | auto        |     220 |                      47   |
| Puerto Rico                          | PRI    | auto        |     211 |                      49   |
| Iran, Islamic Republic of            | IRN    | auto        |     198 |                      45   |
| Ecuador                              | ECU    | auto        |     196 |                      49   |
| Guatemala                            | GTM    | auto        |     176 |                      49   |
| Egypt                                | EGY    | auto        |     170 |                      47   |
| Viet Nam                             | VNM    | auto        |     136 |                      47   |
| Andorra                              | AND    | auto        |     130 |                      49   |
| United States Minor Outlying Islands | UMI    | auto        |     130 |                      49   |
| Jamaica                              | JAM    | auto        |     128 |                      48   |
| Holy See (Vatican City State)        | VAT    | auto        |     122 |                      50   |
| Luxembourg                           | LUX    | auto        |     110 |                      49   |
| United Arab Emirates                 | ARE    | auto        |     102 |                      49.5 |
| Cyprus                               | CYP    | auto        |     100 |                      48   |
| Cocos (Keeling) Islands              | CCK    | auto        |     100 |                      49   |

## 5. 나라 이름 맞추기
### 수동으로 ISO 코드를 지정한 나라
| country                         | iso3   | iso_match   |   users |   median_artists_per_user |
|:--------------------------------|:-------|:------------|--------:|--------------------------:|
| Turkey                          | TUR    | manual      |    6452 |                      47   |
| Macedonia                       | MKD    | manual      |     290 |                      48   |
| Reunion                         | REU    | manual      |      49 |                      49   |
| Palestinian Territory, Occupied | PSE    | manual      |      46 |                      49   |
| Cote D'Ivoire                   | CIV    | manual      |      33 |                      50   |
| Cape Verde                      | CPV    | manual      |      22 |                      50.5 |
| Netherlands Antilles            | ANT    | manual      |      17 |                      49   |
| Saint Helena                    | SHN    | manual      |      16 |                      47   |
| Libyan Arab Jamahiriya          | LBY    | manual      |      14 |                      46.5 |
| Swaziland                       | SWZ    | manual      |      14 |                      49   |

### ISO 코드로 못 바꾼 나라
없음

## 6. WVS Wave 5와 공통 나라
`data/raw/wvs/`에 WVS 파일이 없어서 이 단계는 건너뛰었다.
