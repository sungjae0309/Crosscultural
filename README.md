# 과제 설명

비즈니스 인텔리전스 중간 과제의 코드 저장소이다. 음악 서비스가 새 국가에 진출할 때 전 세계 인기와 현지 인기를 어떤 비중으로 섞어 추천해야 하는지, 그리고 그 비중을 가치관이 비슷한 국가에서 빌려 올 수 있는지를 Last.fm 청취 기록과 WVS(World Values Survey) 가치관 조사로 분석하였다.

예를 들어 한국에 처음 진출하여 전 세계 차트 상위 아티스트만 추천하면 한국에서 인기 있는 국내 아티스트를 놓친다. 반대로 초기 가입자 50명의 기록만 반영하면 그 몇 명의 취향이 한국 전체의 취향처럼 반영된다.

## 요약

```
추천 점수 = (1 - w) × 기준 점수 + w × 현지 인기
```

- 기준 점수: H1, H2는 전 세계 인기, H3는 개인 맞춤 추천(CF) 점수
- w: 현지 인기 반영 비중(0~1). 0부터 1까지 0.1 간격의 11개 값 중 검증 사용자에서 NDCG@10이 가장 높은 값을 선택

| 가설 | 내용 | 대상 | 결과 |
|---|---|---|---|
| H1 | 국가마다 w를 따로 정하면 모든 국가에 공통 w를 적용할 때보다 낫다 | 사용자 100명 이상 75개국 | 지지되지 않음 (차이 +0.0001, Holm p 0.61) |
| H2 | 새 국가(초기 사용자 50명)에 가치관이 비슷한 3개국의 w를 적용하면 공통 w보다 낫다 | 42개국을 차례로 새 국가로 가정 | 지지되지 않음 (차이 -0.0014, Holm p 0.11) |
| H3 | CF와 현지 인기를 결합할 때도 가치관이 비슷한 국가의 w가 공통 w보다 낫다 | H2와 같은 42개국 | 지지되지 않음 (차이 -0.0009, Holm p 0.38) |

차이는 두 방법의 NDCG@10 국가 평균 차이이다. 가설 외에 확인된 결과는 다음과 같다.

- 현지 인기를 결합하면 전 세계 인기만 사용할 때보다 NDCG@10이 약 16%(H1), 약 7%(H2) 높았다.
- CF는 전 세계 인기보다 약 54% 높았고(42개국 모두 개선), 여기에 현지 인기를 공통 w(0.2)로 결합하면 약 6% 더 높았다.
- 다만 CF에 현지 인기를 결합하면 아이템 커버리지가 약 21% 감소하였다(42개국 모두 감소).

전체 수치는 `results/tables/final_summary.md`와 가설별 `h1_test.md`, `h2_test.md`, `h3_test.md`에 있다.

## 실험 방식

- **사용자 분할:** 국가별로 무작위 분할하여 학습 70%, 검증 15%, 시험 15%로 나누었다(시드 42). 들은 아티스트가 10개 미만인 사용자 665명은 학습에만 사용하였다.
- **평가:** 데이터에 청취 시점이 없으므로, 검증과 시험 사용자가 들은 아티스트 중 5명만 모델에 제공하고 나머지를 정답으로 숨긴 뒤 상위 10개 추천으로 평가하였다. 제공한 5명은 추천 목록에서 제외하였다.
- **지표:** NDCG@10을 주 지표로, Recall@10과 아이템 커버리지를 보조 지표로 사용하였다. 국가별 평균을 먼저 구한 뒤 다시 평균하여 모든 국가에 같은 가중치를 주었다.
- **새 국가 상황(H2, H3):** 42개국을 차례로 새 국가로 두고 초기 사용자 50명으로 현지 인기를 계산하였다(50명 추출 10회 반복). 공통 w, 가치관이 비슷한 국가, 무작위 국가는 새 국가를 제외한 41개국에서 정하였고, 무작위 3개국은 100회 추출하였다.
- **통계:** 국가 단위 부트스트랩 95% 신뢰구간과 Wilcoxon 검정을 사용하였고, 세 가설의 p값은 Holm 방법으로 보정하였다.

## 방법 이름

결과 파일에 나오는 방법 이름이다.

| 이름 | 의미 |
|---|---|
| P0 | 전 세계 인기만 사용 |
| P1 | 현지 인기만 사용 |
| P2 | 모든 국가에 공통 w 적용 |
| P3 | 국가별로 해당 국가 검증 사용자에서 가장 성능이 높은 w 적용 (H2에서는 실제로 알 수 없는 값이므로 참고용 상한) |
| P4 | WVS 가치관이 가장 비슷한 3개국의 w 적용 |
| P5 | 무작위로 선택한 3개국의 w 적용 |
| C0 | 개인 맞춤 추천(CF)만 사용 |
| C1 | CF와 현지 인기를 공통 w로 결합 |
| C2 | CF와 현지 인기를 가치관이 비슷한 3개국의 w로 결합 |
| C3 | CF와 현지 인기를 무작위 3개국의 w로 결합 |

## 용어

- **아티스트:** 추천 단위. 곡이 아니라 아티스트를 추천한다.
- **전 세계 인기, 현지 인기:** 학습 사용자 중 해당 아티스트를 들은 사용자의 비율. 현지 인기는 해당 국가 사용자만으로 계산하며, H2와 H3의 전 세계 인기는 새 국가를 제외하고 계산한다.
- **협업 필터링(CF):** 취향이 비슷한 사용자들이 많이 들은 아티스트를 추천하는 방법. implicit 패키지의 ALS를 사용하였다.
- **NDCG@10:** 상위 10개 추천에 정답이 많고 위쪽에 있을수록 높은 점수.
- **Recall@10:** 숨긴 정답 중 상위 10개 추천에 포함된 비율.
- **아이템 커버리지:** 추천 가능한 아티스트 중 한 번 이상 추천 목록에 포함된 아티스트의 비율. 높을수록 다양한 아티스트를 추천한 것이다.
- **WVS 거리:** WVS 지수 SACSECVAL(세속적 가치)과 RESEMAVAL(해방적 가치)의 국가별 가중 평균을 표준화하여 계산한 국가 간 거리. 가까울수록 가치관이 비슷한 국가로 본다.

## 폴더 구성

```
Crosscultural/
├── data/
│   ├── raw/lastfm/     Last.fm 원본 (직접 받아서 넣음, git에 올리지 않음)
│   ├── raw/wvs/        WVS 원본 (직접 받아서 넣음, git에 올리지 않음)
│   └── processed/      코드가 만든 중간 파일 (git에 올리지 않음)
├── src/
│   ├── config.py         경로와 기준값(K, 제공 아티스트 수, 최소 사용자 수 등)을 모아 둔 설정 파일
│   ├── load_lastfm.py    Last.fm 원본 읽기와 정리
│   ├── load_wvs.py       WVS Wave 5 CSV 읽기
│   ├── country_codes.py  국가 이름을 ISO 세 글자 코드(예: KOR)로 변환
│   ├── users.py          사용자 단위 표 생성 (국가 코드 변환, 제외 국가 처리)
│   ├── check_data.py     데이터 확인 표 생성
│   ├── split_users.py    사용자를 학습, 검증, 시험으로 나누고 평가용으로 제공할 아티스트 5명 선택
│   ├── metrics.py        추천 목록 생성과 평가 지표 (NDCG, Recall, 커버리지)
│   ├── popularity.py     인기 점수 계산과 평가 (H1, H2 공통)
│   ├── stats.py          국가 단위 비교 통계 (부트스트랩, Wilcoxon, Holm)
│   ├── seeds.py          무작위 단계별 시드 생성
│   ├── wvs_distance.py   WVS 지수로 국가 간 거리 계산
│   ├── run_h1.py         H1 실험 (--stage valid, --stage test)
│   ├── run_h2.py         H2 실험 (--stage valid, --stage test)
│   ├── cf.py             ALS 학습, 평가 사용자 취향 계산, CF와 현지 인기 결합 평가
│   ├── run_h3.py         H3 실험 (--stage tune, models, valid, test)
│   └── summarize_results.py H1~H3 가설별 비교 요약과 Holm 보정
├── tests/
│   ├── test_metrics.py   평가 지표 확인
│   ├── test_split.py     사용자 분할 규칙 확인 (가짜 데이터)
│   ├── test_popularity.py 인기 점수, 평가, w 선택, 통계 확인
│   ├── test_h2.py        H2 조건(새 국가 제외, 초기 사용자)과 WVS 거리 확인
│   └── test_cf.py        CF 순위 계산 결과가 전체 계산과 같은지, 국가 묶음 확인
├── results/
│   ├── tables/         결과 표
│   └── figures/        결과 그림
├── report/             실험 설계와 정리 자료
├── requirements.txt    필요한 파이썬 패키지 목록
└── AI_사용기록.md       AI로 한 작업 기록
```

## 결과 파일

| 파일 | 내용 |
|---|---|
| `results/tables/final_summary.md` | H1~H3 가설 판정 요약 (차이, 신뢰구간, p값) |
| `results/tables/h1_test.md`, `h2_test.md`, `h3_test.md` | 가설별 시험 결과와 방법별 지표 |
| `results/tables/h*_test_by_country.csv` | 국가별 시험 결과 |
| `results/tables/h2_failure_analysis.csv` | WVS 방식의 성능이 낮았던 국가 분석 (자국 취향 지표, WVS 거리) |
| `results/tables/data_check.md` | 데이터 확인 (사용자 수, 국가 수, 제외 국가, WVS 공통 국가) |
| `results/tables/split_counts.md` | 학습, 검증, 시험 인원 |
| `results/figures/h1_weights_vs_size.png` | 국가별 w와 사용자 수 |

## 실행 방법

macOS 또는 Linux 터미널, Python 3.12 기준이다.

**1. 환경 준비**

```bash
git clone https://github.com/sungjae0309/Crosscultural.git
cd Crosscultural
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. 데이터 넣기**

Last.fm은 아래 명령으로 받는다(약 543MB). WVS는 아래 "데이터" 항목을 참고하여 직접 받은 뒤 `data/raw/wvs/`에 넣는다.

```bash
curl -L -o data/raw/lastfm/lastfm-dataset-360K.tar.gz "https://zenodo.org/api/records/6090214/files/lastfm-dataset-360K.tar.gz/content"
tar -xzf data/raw/lastfm/lastfm-dataset-360K.tar.gz -C data/raw/lastfm
```

**3. 데이터 확인과 사용자 분할**

```bash
python src/check_data.py    # 결과: results/tables/data_check.md
python src/split_users.py   # 결과: data/processed/, results/tables/split_counts.md
```

**4. 테스트** (원본 데이터 없이도 실행 가능)

```bash
python tests/test_metrics.py
python tests/test_split.py
python tests/test_popularity.py
python tests/test_h2.py
python tests/test_cf.py
```

**5. 실험** (각 가설은 검증 단계를 먼저 실행해야 시험 단계를 실행할 수 있음)

```bash
python src/run_h1.py --stage valid
python src/run_h1.py --stage test
python src/run_h2.py --stage valid
python src/run_h2.py --stage test
python src/run_h3.py --stage tune
python src/run_h3.py --stage models
python src/run_h3.py --stage valid
python src/run_h3.py --stage test
python src/summarize_results.py
```

| 단계 | 소요 시간 | 메모리 |
|---|---|---|
| 데이터 확인 | 약 1분 | 약 4GB |
| H1 | 단계마다 약 1분 | - |
| H2 검증 | 약 7분 | 약 6GB |
| H3 | 설정 선택 6분, ALS 학습 12분, 검증 55분, 시험 3분 | 5~6GB |

결과는 `results/tables/`에 저장되고, ALS 모델은 `data/processed/cf/`에 저장된다. 시드가 고정되어 있어 다시 실행해도 같은 결과가 나온다.

## 데이터

### Last.fm 360K

- 받는 곳: https://zenodo.org/records/6090214 (파일 이름 `lastfm-dataset-360K.tar.gz`)
- 넣는 곳: `data/raw/lastfm/`
- 내용: 사용자별로 많이 들은 아티스트와 재생 횟수, 사용자 프로필(국가 포함). 2008~2009년에 수집한 한 시점의 기록이라 청취 시점 정보는 없다.
- 압축을 풀면 `data/raw/lastfm/lastfm-dataset-360K/` 안에 tsv 파일 두 개가 생긴다. 함께 들어 있는 README.txt의 MD5 값으로 파일을 확인할 수 있다.
- 만든 사람: Òscar Celma
- 이용 조건: 비상업적 용도만 가능(Zenodo 라이선스 표기 `other-nc`). 사용할 때 Last.fm 출처를 밝혀야 한다.

정리 규칙 (`src/load_lastfm.py`, `src/users.py`)

- 아티스트는 MusicBrainz ID(mbid, 아티스트마다 부여된 고유 번호)로 구분하고, mbid가 없으면 이름으로 구분한다. 같은 mbid가 여러 이름 표기로 나오는 경우가 많기 때문이다.
- 같은 사용자와 아티스트의 기록이 여러 줄이면 재생 횟수를 합산하고, 재생 횟수가 0인 줄은 제외한다.
- 재생 기록은 있으나 프로필이 없는 사용자 2명은 국가를 알 수 없어 제외한다.
- 국가는 사용자가 프로필에서 직접 선택한 값이다. 실제 거주지로 보기 어려운 값 4개(Antarctica 365명, United States Minor Outlying Islands 130명, Vatican 122명, Cocos Islands 100명, 합계 717명)는 제외한다. 목록은 `src/config.py`의 `EXCLUDED_ISO3`에 있다.

### WVS Wave 5 (조사 연도 2004~2009)

- 받는 곳: https://www.worldvaluessurvey.org (Data & Documentation → Wave 5)
- 넣는 곳: `data/raw/wvs/`
- 받을 파일: `WV5_Data_csv_v20180912` (CSV). 같은 페이지의 Codebook, Questionnaire RootVersion, WVSA Citation format PDF도 함께 받는다.
- 사이트에서 이름, 소속, 사용 목적을 입력하고 이용 조건에 동의해야 받을 수 있다.
- 이용 조건: 비영리 목적만 가능, 데이터 파일 재배포 금지, 결과를 사용할 때 참고문헌에 인용.
- 사용한 열: V2(ISO 숫자 국가 코드), SACSECVAL과 RESEMAVAL(가치관 지수), V259(응답자 가중치), V260(조사 연도).
- 파일 형식 (`src/load_wvs.py`): 세미콜론 구분, 쉼표 소수점(예: `,94` = 0.94). 빈칸과 음수(-1~-5)는 결측으로 처리한다.
- 조사 연도는 국가마다 다르다(V260 기준 2004~2009년).
- 인용: Inglehart, R., C. Haerpfer, A. Moreno, C. Welzel, K. Kizilova, J. Diez-Medrano, M. Lagos, P. Norris, E. Ponarin & B. Puranen et al. (eds.). 2018. World Values Survey: Round Five - Country-Pooled Datafile. Madrid, Spain & Vienna, Austria: JD Systems Institute & WVSA Secretariat. doi.org/10.14281/18241.7

### 재배포 금지

두 데이터 모두 원본을 다른 곳에 다시 올릴 수 없다. 따라서 `data/raw/`, `data/processed/` 안의 파일과 압축 파일은 `.gitignore`로 제외하였다. 실행하려면 위 방법으로 각자 데이터를 받아야 한다.
