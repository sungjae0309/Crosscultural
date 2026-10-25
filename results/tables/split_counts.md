# 사용자 나누기 결과

`python src/split_users.py`로 만든 파일. 직접 고치지 말고 코드를 다시 돌린다.

## 요약
| 항목                            |      값 |
|:------------------------------|-------:|
| 전체 사용자                        | 358630 |
| 학습                            | 251250 |
| 검증                            |  53690 |
| 시험                            |  53690 |
| 아티스트 10개 미만이라 학습으로만 쓴 사용자     |    665 |
| H1 대상 나라 수                    |     75 |
| H2·H3 대상 나라 수                 |     42 |
| H2·H3 대상 나라 중 시험 사용자가 가장 적은 수 |     33 |

## H1 대상 나라 (75개)
users = train + valid + test. 전체 목록은 `split_counts.csv`.

| country                   | iso3   |   users |   train |   valid |   test | in_wvs   | in_h2   |
|:--------------------------|:-------|--------:|--------:|--------:|-------:|:---------|:--------|
| United States             | USA    |   67044 |   46962 |   10041 |  10041 | True     | True    |
| Germany                   | DEU    |   31651 |   22171 |    4740 |   4740 | True     | True    |
| United Kingdom            | GBR    |   29902 |   20948 |    4477 |   4477 | True     | True    |
| Poland                    | POL    |   20987 |   14703 |    3142 |   3142 | True     | True    |
| Russian Federation        | RUS    |   19833 |   13903 |    2965 |   2965 | True     | True    |
| Brazil                    | BRA    |   14534 |   10180 |    2177 |   2177 | True     | True    |
| Sweden                    | SWE    |   13122 |    9188 |    1967 |   1967 | True     | True    |
| Spain                     | ESP    |   13051 |    9141 |    1955 |   1955 | True     | True    |
| Finland                   | FIN    |   11579 |    8107 |    1736 |   1736 | True     | True    |
| Netherlands               | NLD    |    9650 |    6756 |    1447 |   1447 | True     | True    |
| Canada                    | CAN    |    8679 |    6079 |    1300 |   1300 | True     | True    |
| France                    | FRA    |    7529 |    5273 |    1128 |   1128 | True     | True    |
| Italy                     | ITA    |    7525 |    5271 |    1127 |   1127 | True     | True    |
| Australia                 | AUS    |    7135 |    4997 |    1069 |   1069 | True     | True    |
| Japan                     | JPN    |    6637 |    4653 |     992 |    992 | True     | True    |
| Turkey                    | TUR    |    6452 |    4520 |     966 |    966 | True     | True    |
| Norway                    | NOR    |    5155 |    3609 |     773 |    773 | True     | True    |
| Mexico                    | MEX    |    4834 |    3386 |     724 |    724 | True     | True    |
| Czech Republic            | CZE    |    4774 |    3342 |     716 |    716 | False    | False   |
| Ukraine                   | UKR    |    4396 |    3084 |     656 |    656 | True     | True    |
| Belgium                   | BEL    |    3803 |    2663 |     570 |    570 | False    | False   |
| Portugal                  | PRT    |    3196 |    2238 |     479 |    479 | False    | False   |
| Switzerland               | CHE    |    3053 |    2139 |     457 |    457 | True     | True    |
| Bulgaria                  | BGR    |    2800 |    1962 |     419 |    419 | True     | True    |
| Austria                   | AUT    |    2796 |    1958 |     419 |    419 | False    | False   |
| Chile                     | CHL    |    2794 |    1958 |     418 |    418 | True     | True    |
| Argentina                 | ARG    |    2640 |    1848 |     396 |    396 | True     | True    |
| Romania                   | ROU    |    2636 |    1846 |     395 |    395 | True     | True    |
| Denmark                   | DNK    |    2508 |    1756 |     376 |    376 | False    | False   |
| Hungary                   | HUN    |    1985 |    1391 |     297 |    297 | True     | True    |
| Lithuania                 | LTU    |    1979 |    1385 |     297 |    297 | False    | False   |
| Croatia                   | HRV    |    1917 |    1343 |     287 |    287 | False    | False   |
| Greece                    | GRC    |    1849 |    1299 |     275 |    275 | False    | False   |
| Colombia                  | COL    |    1849 |    1295 |     277 |    277 | True     | True    |
| Latvia                    | LVA    |    1736 |    1216 |     260 |    260 | False    | False   |
| Ireland                   | IRL    |    1634 |    1144 |     245 |    245 | False    | False   |
| Slovakia                  | SVK    |    1566 |    1096 |     235 |    235 | False    | False   |
| Serbia                    | SRB    |    1452 |    1016 |     218 |    218 | True     | True    |
| China                     | CHN    |    1309 |     923 |     193 |    193 | True     | True    |
| New Zealand               | NZL    |    1247 |     873 |     187 |    187 | True     | True    |
| Belarus                   | BLR    |    1215 |     851 |     182 |    182 | False    | False   |
| Israel                    | ISR    |    1178 |     824 |     177 |    177 | False    | False   |
| Estonia                   | EST    |    1159 |     813 |     173 |    173 | False    | False   |
| India                     | IND    |    1020 |     716 |     152 |    152 | True     | True    |
| Venezuela                 | VEN    |     745 |     521 |     112 |    112 | False    | False   |
| Slovenia                  | SVN    |     673 |     471 |     101 |    101 | True     | True    |
| South Africa              | ZAF    |     622 |     436 |      93 |     93 | True     | True    |
| Thailand                  | THA    |     602 |     422 |      90 |     90 | True     | True    |
| Indonesia                 | IDN    |     597 |     417 |      90 |     90 | True     | True    |
| Philippines               | PHL    |     566 |     396 |      85 |     85 | False    | False   |
| Singapore                 | SGP    |     499 |     351 |      74 |     74 | False    | False   |
| Peru                      | PER    |     490 |     344 |      73 |     73 | True     | True    |
| Taiwan                    | TWN    |     429 |     301 |      64 |     64 | True     | True    |
| Korea, Republic of        | KOR    |     427 |     299 |      64 |     64 | True     | True    |
| Malaysia                  | MYS    |     417 |     293 |      62 |     62 | True     | True    |
| Hong Kong                 | HKG    |     372 |     274 |      49 |     49 | True     | True    |
| Iceland                   | ISL    |     368 |     258 |      55 |     55 | False    | False   |
| Costa Rica                | CRI    |     325 |     227 |      49 |     49 | False    | False   |
| Kazakhstan                | KAZ    |     317 |     223 |      47 |     47 | False    | False   |
| Macedonia                 | MKD    |     290 |     202 |      44 |     44 | False    | False   |
| Moldova                   | MDA    |     271 |     191 |      40 |     40 | True     | True    |
| Uruguay                   | URY    |     263 |     185 |      39 |     39 | True     | True    |
| Bosnia and Herzegovina    | BIH    |     253 |     177 |      38 |     38 | False    | False   |
| Georgia                   | GEO    |     220 |     154 |      33 |     33 | True     | True    |
| Puerto Rico               | PRI    |     211 |     147 |      32 |     32 | False    | False   |
| Iran, Islamic Republic of | IRN    |     198 |     140 |      29 |     29 | True     | False   |
| Ecuador                   | ECU    |     196 |     138 |      29 |     29 | False    | False   |
| Guatemala                 | GTM    |     176 |     124 |      26 |     26 | True     | False   |
| Egypt                     | EGY    |     170 |     120 |      25 |     25 | True     | False   |
| Viet Nam                  | VNM    |     136 |      96 |      20 |     20 | True     | False   |
| Andorra                   | AND    |     130 |      90 |      20 |     20 | True     | False   |
| Jamaica                   | JAM    |     128 |      90 |      19 |     19 | False    | False   |
| Luxembourg                | LUX    |     110 |      78 |      16 |     16 | False    | False   |
| United Arab Emirates      | ARE    |     102 |      72 |      15 |     15 | False    | False   |
| Cyprus                    | CYP    |     100 |      70 |      15 |     15 | True     | False   |
