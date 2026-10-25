# 데이터 확인 결과

`python src/check_data.py`로 만든 파일. 직접 고치지 말고 코드를 다시 돌린다.

## 1. 전체 요약
| 항목                          |        값 |
|:----------------------------|---------:|
| 프로필에 있는 사용자                 |   359347 |
| 재생 기록이 있는 사용자               |   359349 |
| 프로필과 재생 기록이 둘 다 있는 사용자      |   359347 |
| 그중 제외한 국가값의 사용자             |      717 |
| 제외 후 남은 사용자                 |   358630 |
| 그중 국가 정보가 있는 사용자            |   358630 |
| 그중 ISO 나라 코드로 바뀐 사용자        |   358630 |
| 나라 수 (Last.fm 표기 기준)        |      235 |
| 아티스트 수 (정리 후)               |   268775 |
| 사용자-아티스트 쌍 수 (정리 후)         | 17559161 |
| 아티스트가 10개 미만이라 평가에 못 쓰는 사용자 |      665 |

## 2. 사용자당 아티스트 수
ISO 코드가 있는 사용자 기준.

| 통계    |        값 |
|:------|---------:|
| count | 358630   |
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
| (0, 5]           |     281 |
| (5, 10]          |     525 |
| (10, 20]         |    2266 |
| (20, 30]         |    6529 |
| (30, 40]         |   24236 |
| (40, 50]         |  226090 |
| (50, 60]         |   73224 |
| (60, 80]         |   23929 |
| (80, 1000]       |    1550 |

## 3. 최소 사용자 수 기준에 따라 남는 나라
|   최소 사용자 수 |   남는 나라 수 |   남는 사용자 합 |
|-----------:|----------:|-----------:|
|         50 |       100 |     355942 |
|        100 |        75 |     354193 |
|        200 |        65 |     352747 |
|        500 |        50 |     347595 |
|       1000 |        44 |     343790 |

## 4. 사용자 100명 이상인 나라 (75개)
전체 목록은 `country_user_counts.csv`.

| country                   | iso3   | iso_match   |   users |   median_artists_per_user |
|:--------------------------|:-------|:------------|--------:|--------------------------:|
| United States             | USA    | auto        |   67044 |                      49   |
| Germany                   | DEU    | auto        |   31651 |                      49   |
| United Kingdom            | GBR    | auto        |   29902 |                      49   |
| Poland                    | POL    | auto        |   20987 |                      48   |
| Russian Federation        | RUS    | auto        |   19833 |                      46   |
| Brazil                    | BRA    | auto        |   14534 |                      48   |
| Sweden                    | SWE    | auto        |   13122 |                      50   |
| Spain                     | ESP    | auto        |   13051 |                      49   |
| Finland                   | FIN    | auto        |   11579 |                      49   |
| Netherlands               | NLD    | auto        |    9650 |                      49   |
| Canada                    | CAN    | auto        |    8679 |                      49   |
| France                    | FRA    | auto        |    7529 |                      49   |
| Italy                     | ITA    | auto        |    7525 |                      49   |
| Australia                 | AUS    | auto        |    7135 |                      49   |
| Japan                     | JPN    | auto        |    6637 |                      45   |
| Turkey                    | TUR    | manual      |    6452 |                      47   |
| Norway                    | NOR    | auto        |    5155 |                      49   |
| Mexico                    | MEX    | auto        |    4834 |                      48   |
| Czech Republic            | CZE    | auto        |    4774 |                      48   |
| Ukraine                   | UKR    | auto        |    4396 |                      45   |
| Belgium                   | BEL    | auto        |    3803 |                      49   |
| Portugal                  | PRT    | auto        |    3196 |                      49   |
| Switzerland               | CHE    | auto        |    3053 |                      49   |
| Bulgaria                  | BGR    | auto        |    2800 |                      48   |
| Austria                   | AUT    | auto        |    2796 |                      48   |
| Chile                     | CHL    | auto        |    2794 |                      48   |
| Argentina                 | ARG    | auto        |    2640 |                      49   |
| Romania                   | ROU    | auto        |    2636 |                      49   |
| Denmark                   | DNK    | auto        |    2508 |                      49   |
| Hungary                   | HUN    | auto        |    1985 |                      48   |
| Lithuania                 | LTU    | auto        |    1979 |                      48   |
| Croatia                   | HRV    | auto        |    1917 |                      48   |
| Greece                    | GRC    | auto        |    1849 |                      48   |
| Colombia                  | COL    | auto        |    1849 |                      48   |
| Latvia                    | LVA    | auto        |    1736 |                      48   |
| Ireland                   | IRL    | auto        |    1634 |                      49   |
| Slovakia                  | SVK    | auto        |    1566 |                      48   |
| Serbia                    | SRB    | auto        |    1452 |                      49   |
| China                     | CHN    | auto        |    1309 |                      43   |
| New Zealand               | NZL    | auto        |    1247 |                      49   |
| Belarus                   | BLR    | auto        |    1215 |                      47   |
| Israel                    | ISR    | auto        |    1178 |                      47   |
| Estonia                   | EST    | auto        |    1159 |                      48   |
| India                     | IND    | auto        |    1020 |                      48   |
| Venezuela                 | VEN    | auto        |     745 |                      49   |
| Slovenia                  | SVN    | auto        |     673 |                      48   |
| South Africa              | ZAF    | auto        |     622 |                      49   |
| Thailand                  | THA    | auto        |     602 |                      45   |
| Indonesia                 | IDN    | auto        |     597 |                      47   |
| Philippines               | PHL    | auto        |     566 |                      49   |
| Singapore                 | SGP    | auto        |     499 |                      48   |
| Peru                      | PER    | auto        |     490 |                      48   |
| Taiwan                    | TWN    | auto        |     429 |                      45   |
| Korea, Republic of        | KOR    | auto        |     427 |                      45   |
| Malaysia                  | MYS    | auto        |     417 |                      46   |
| Hong Kong                 | HKG    | auto        |     372 |                      43   |
| Iceland                   | ISL    | auto        |     368 |                      48   |
| Costa Rica                | CRI    | auto        |     325 |                      49   |
| Kazakhstan                | KAZ    | auto        |     317 |                      43   |
| Macedonia                 | MKD    | manual      |     290 |                      48   |
| Moldova                   | MDA    | auto        |     271 |                      46   |
| Uruguay                   | URY    | auto        |     263 |                      48   |
| Bosnia and Herzegovina    | BIH    | auto        |     253 |                      47   |
| Georgia                   | GEO    | auto        |     220 |                      47   |
| Puerto Rico               | PRI    | auto        |     211 |                      49   |
| Iran, Islamic Republic of | IRN    | auto        |     198 |                      45   |
| Ecuador                   | ECU    | auto        |     196 |                      49   |
| Guatemala                 | GTM    | auto        |     176 |                      49   |
| Egypt                     | EGY    | auto        |     170 |                      47   |
| Viet Nam                  | VNM    | auto        |     136 |                      47   |
| Andorra                   | AND    | auto        |     130 |                      49   |
| Jamaica                   | JAM    | auto        |     128 |                      48   |
| Luxembourg                | LUX    | auto        |     110 |                      49   |
| United Arab Emirates      | ARE    | auto        |     102 |                      49.5 |
| Cyprus                    | CYP    | auto        |     100 |                      48   |

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
| Swaziland                       | SWZ    | manual      |      14 |                      49   |
| Libyan Arab Jamahiriya          | LBY    | manual      |      14 |                      46.5 |

### ISO 코드로 못 바꾼 나라
없음

### 제외한 국가값
실제 거주지로 보기 어려워 뺐다. 목록은 `config.EXCLUDED_ISO3`. 위 표들은 모두 제외 후 숫자다.

| country                              | iso3   |   users |
|:-------------------------------------|:-------|--------:|
| Antarctica                           | ATA    |     365 |
| United States Minor Outlying Islands | UMI    |     130 |
| Holy See (Vatican City State)        | VAT    |     122 |
| Cocos (Keeling) Islands              | CCK    |     100 |

## 6. WVS Wave 5와 공통 나라
WVS 나라 수: 58. ISO 코드로 못 바꾼 WVS 나라: 0개. 음수 결측 코드는 빼고 응답 비율을 셌다.

|   Last.fm 최소 사용자 수 |   WVS와 공통인 나라 수 |
|-------------------:|----------------:|
|                 50 |              49 |
|                100 |              48 |
|                200 |              42 |
|                500 |              34 |
|               1000 |              30 |

전체 목록 (`wvs_lastfm_common_countries.csv`)

|   V2 | iso3   |   wvs_respondents |   SACSECVAL_valid_pct |   RESEMAVAL_valid_pct | country                   |   users |
|-----:|:-------|------------------:|----------------------:|----------------------:|:--------------------------|--------:|
|  840 | USA    |              1249 |                    96 |                    99 | United States             |   67044 |
|  276 | DEU    |              2064 |                    99 |                    99 | Germany                   |   31651 |
|  826 | GBR    |              1041 |                   100 |                    99 | United Kingdom            |   29902 |
|  616 | POL    |              1000 |                    99 |                    98 | Poland                    |   20987 |
|  643 | RUS    |              2033 |                    98 |                    99 | Russian Federation        |   19833 |
|   76 | BRA    |              1500 |                   100 |                   100 | Brazil                    |   14534 |
|  752 | SWE    |              1003 |                   100 |                   100 | Sweden                    |   13122 |
|  724 | ESP    |              1200 |                   100 |                    98 | Spain                     |   13051 |
|  246 | FIN    |              1014 |                   100 |                   100 | Finland                   |   11579 |
|  528 | NLD    |              1050 |                    99 |                    99 | Netherlands               |    9650 |
|  124 | CAN    |              2164 |                   100 |                   100 | Canada                    |    8679 |
|  250 | FRA    |              1001 |                   100 |                   100 | France                    |    7529 |
|  380 | ITA    |              1012 |                    99 |                    99 | Italy                     |    7525 |
|   36 | AUS    |              1421 |                    99 |                   100 | Australia                 |    7135 |
|  392 | JPN    |              1096 |                    99 |                    97 | Japan                     |    6637 |
|  792 | TUR    |              1346 |                   100 |                   100 | Turkey                    |    6452 |
|  578 | NOR    |              1025 |                    99 |                    99 | Norway                    |    5155 |
|  484 | MEX    |              1560 |                    99 |                    98 | Mexico                    |    4834 |
|  804 | UKR    |              1000 |                    97 |                    98 | Ukraine                   |    4396 |
|  756 | CHE    |              1241 |                   100 |                   100 | Switzerland               |    3053 |
|  100 | BGR    |              1001 |                    98 |                    98 | Bulgaria                  |    2800 |
|  152 | CHL    |              1000 |                   100 |                   100 | Chile                     |    2794 |
|   32 | ARG    |              1002 |                   100 |                    98 | Argentina                 |    2640 |
|  642 | ROU    |              1776 |                    97 |                    96 | Romania                   |    2636 |
|  348 | HUN    |              1007 |                   100 |                   100 | Hungary                   |    1985 |
|  170 | COL    |              3025 |                   100 |                   100 | Colombia                  |    1849 |
|  688 | SRB    |              1220 |                    97 |                    96 | Serbia                    |    1452 |
|  156 | CHN    |              1991 |                    88 |                    89 | China                     |    1309 |
|  554 | NZL    |               954 |                    97 |                    96 | New Zealand               |    1247 |
|  356 | IND    |              2001 |                    95 |                    86 | India                     |    1020 |
|  705 | SVN    |              1037 |                    98 |                    98 | Slovenia                  |     673 |
|  710 | ZAF    |              2988 |                   100 |                   100 | South Africa              |     622 |
|  764 | THA    |              1534 |                   100 |                   100 | Thailand                  |     602 |
|  360 | IDN    |              2015 |                    99 |                    98 | Indonesia                 |     597 |
|  604 | PER    |              1500 |                    93 |                    97 | Peru                      |     490 |
|  158 | TWN    |              1227 |                   100 |                   100 | Taiwan                    |     429 |
|  410 | KOR    |              1200 |                   100 |                   100 | Korea, Republic of        |     427 |
|  458 | MYS    |              1201 |                   100 |                   100 | Malaysia                  |     417 |
|  344 | HKG    |              1252 |                    99 |                    97 | Hong Kong                 |     372 |
|  498 | MDA    |              1046 |                   100 |                   100 | Moldova                   |     271 |
|  858 | URY    |              1000 |                   100 |                    99 | Uruguay                   |     263 |
|  268 | GEO    |              1500 |                    98 |                    99 | Georgia                   |     220 |
|  364 | IRN    |              2667 |                   100 |                   100 | Iran, Islamic Republic of |     198 |
|  320 | GTM    |              1000 |                   100 |                   100 | Guatemala                 |     176 |
|  818 | EGY    |              3051 |                   100 |                   100 | Egypt                     |     170 |
|  704 | VNM    |              1495 |                    99 |                    99 | Viet Nam                  |     136 |
|   20 | AND    |              1003 |                   100 |                   100 | Andorra                   |     130 |
|  196 | CYP    |              1050 |                   100 |                   100 | Cyprus                    |     100 |
|  504 | MAR    |              1200 |                   100 |                    99 | Morocco                   |      82 |
|  780 | TTO    |              1002 |                   100 |                   100 | Trinidad and Tobago       |      46 |
|  854 | BFA    |              1534 |                    97 |                    99 | Burkina Faso              |      29 |
|  400 | JOR    |              1200 |                   100 |                   100 | Jordan                    |      28 |
|  288 | GHA    |              1534 |                   100 |                   100 | Ghana                     |      21 |
|  231 | ETH    |              1500 |                   100 |                    99 | Ethiopia                  |      17 |
|  894 | ZMB    |              1500 |                    99 |                    99 | Zambia                    |      13 |
|  368 | IRQ    |              2701 |                     0 |                    98 | Iraq                      |      13 |
|  646 | RWA    |              1507 |                   100 |                   100 | Rwanda                    |       8 |
|  466 | MLI    |              1534 |                    99 |                    99 | Mali                      |       7 |

## 7. MBID가 없어서 따로 남은 아티스트
제외한 국가값 사용자를 포함한 전체 재생 기록 기준.

| 항목                      |        값 | 전체 기록 대비 %   |
|:------------------------|---------:|:-------------|
| 전체 사용자-아티스트 기록          | 17559161 | 100.0        |
| MBID 없이 이름만 있는 기록       |   226451 | 1.29         |
| 그중 이름이 MBID 하나와 맞는 기록   |    10276 | 0.06         |
| 그 기록의 아티스트 수            |     1711 | -            |
| 그중 이름이 MBID 여러 개와 맞는 기록 |       21 | 0.0          |
