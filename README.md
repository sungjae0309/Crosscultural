# 새 국가 진출 시 음악 추천의 현지 인기 비중

비즈니스 인텔리전스 중간 과제. 공개 데이터로 "한 나라의 사용자 기록이 다른 나라 추천에 도움이 되는가"를 확인하는 과제이고, Last.fm 청취 기록과 WVS 가치관 조사를 함께 썼다.

예를 들어 음악 서비스가 한국에 처음 진출하면, 전 세계 차트 상위 아티스트만 추천해서는 한국에서 인기 있는 국내 아티스트를 놓친다. 반대로 초기 가입자 50명의 기록만 보면 그 몇 명의 취향이 한국 전체 취향처럼 반영된다. 그래서 두 인기를 어떤 비중으로 섞을지, 그 비중을 가치관이 비슷한 나라에서 빌려 올 수 있는지를 실험했다.

## 세 줄 요약

- 추천 점수 = (1 - w) × 전 세계 인기 + w × 현지 인기. 이 w를 어떻게 정할지 비교했다.
- H1: 나라마다 w를 따로 정하기 / H2: 가치관(WVS)이 비슷한 나라의 w 빌려 쓰기 / H3: 개인 맞춤 추천(CF)에 섞을 때 H2 다시 확인.
- 결과: 세 가설 모두 모든 나라에 같은 w를 쓰는 방법보다 낫지 않았다. 현지 인기를 섞는 것과 CF는 효과가 컸다(`results/tables/final_summary.md`).

## 용어

- **아티스트**: 추천 단위. 곡이 아니라 아티스트를 추천한다.
- **비중 w**: 현지 인기를 반영하는 정도(0~1). 0이면 전 세계 인기만, 1이면 현지 인기만 쓴다.
- **협업 필터링(CF)**: 취향이 비슷한 사람들이 들은 아티스트를 추천하는 방법. 여기서는 ALS를 썼다.
- **Recall@K**: 추천한 K개 안에 사용자가 실제로 들은 아티스트가 얼마나 들어 있는지.
- **NDCG@K**: Recall@K와 비슷하지만, 맞힌 아티스트가 목록 위쪽에 있을수록 점수를 더 준다.
- **WVS (World Values Survey)**: 나라별 가치관 설문. 나라끼리 얼마나 비슷한지 재는 데 썼다.

## 폴더 구성

```
Crosscultural/
├── data/
│   ├── raw/lastfm/     Last.fm 원본 (직접 받아서 넣기, git에 안 올라감)
│   ├── raw/wvs/        WVS 원본 (직접 받아서 넣기, git에 안 올라감)
│   └── processed/      코드가 만든 중간 파일 (git에 안 올라감)
├── src/
│   ├── config.py         경로와 숫자 기준값(K, 보여줄 아티스트 수 등)을 모아둔 곳
│   ├── load_lastfm.py    Last.fm 원본을 읽고 정리하는 함수
│   ├── load_wvs.py       WVS Wave 5 CSV를 읽는 함수
│   ├── country_codes.py  나라 이름을 ISO 세 글자 코드(예: KOR)로 바꾸는 함수
│   ├── users.py          사용자 단위 표 (나라 코드, 제외 국가값 처리)
│   ├── check_data.py     데이터 확인 표를 만드는 코드
│   ├── split_users.py    사용자를 학습/검증/시험으로 나누고 보여줄 아티스트 고르기
│   ├── metrics.py        추천 목록 만들기와 평가 지표 (NDCG, Recall, 커버리지)
│   ├── popularity.py     인기 점수 실험에 같이 쓰는 자료 준비와 평가
│   ├── stats.py          나라 단위 비교 통계 (부트스트랩, Wilcoxon, Holm)
│   ├── seeds.py          무작위 단계의 시드 만들기
│   ├── wvs_distance.py   WVS 가치관으로 나라 사이 거리 재기
│   ├── run_h1.py         H1 실험 (--stage valid, --stage test)
│   ├── run_h2.py         H2 실험 (--stage valid, --stage test)
│   ├── cf.py             ALS 학습, fold-in, CF + 나라 인기 섞기 평가
│   ├── run_h3.py         H3 실험 (--stage tune, models, valid, test)
│   └── summarize_results.py H1~H3 주 비교 요약과 Holm 보정
├── tests/
│   ├── test_metrics.py   평가 지표 확인
│   ├── test_split.py     사용자 나누기 규칙 확인 (가짜 데이터)
│   ├── test_popularity.py 인기 점수, 행렬 평가, 비중 고르기, 통계 확인
│   ├── test_h2.py        H2 조건(빼는 나라, 초기 사용자), WVS 거리 확인
│   └── test_cf.py        CF 빠른 순위 계산이 전체 계산과 같은지, 나라 묶음 확인
├── results/
│   ├── tables/         결과 표 (data_check.md에 데이터 확인 결과)
│   └── figures/        결과 그림
├── report/             실험 설계와 보고서 정리 자료
├── requirements.txt    필요한 파이썬 패키지 목록
└── AI_사용기록.md       AI로 한 작업 기록
```

## 실행 방법

맥/리눅스 터미널, 파이썬 3.12 기준.

**1. 환경 준비**

```bash
cd Crosscultural
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. 데이터 넣기**

Last.fm은 아래 명령으로 받는다(약 543MB). WVS는 아래 "데이터" 항목을 보고 직접 받아 `data/raw/wvs/`에 넣는다.

```bash
curl -L -o data/raw/lastfm/lastfm-dataset-360K.tar.gz "https://zenodo.org/api/records/6090214/files/lastfm-dataset-360K.tar.gz/content"
tar -xzf data/raw/lastfm/lastfm-dataset-360K.tar.gz -C data/raw/lastfm
```

**3. 데이터 확인과 사용자 나누기**

```bash
python src/check_data.py    # 결과: results/tables/data_check.md
python src/split_users.py   # 결과: data/processed/, results/tables/split_counts.md
```

**4. 테스트** (원본 데이터 없이도 돈다)

```bash
python tests/test_metrics.py
python tests/test_split.py
python tests/test_popularity.py
python tests/test_h2.py
python tests/test_cf.py
```

**5. 실험** (각 가설은 검증 단계를 먼저 돌려야 시험 단계가 돈다)

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

| 단계 | 걸리는 시간 | 메모리 |
|---|---|---|
| 데이터 확인 | 약 1분 | 약 4GB |
| H1 | 단계마다 약 1분 | |
| H2 검증 | 약 7분 | 약 6GB |
| H3 | 설정 고르기 6분, ALS 학습 12분, 검증 55분, 시험 3분 | 5~6GB |

시드가 고정되어 있어 다시 돌려도 같은 결과가 나온다. ALS 모델은 `data/processed/cf/`에 저장된다.

## 데이터

### Last.fm 360K

- 받는 곳: https://zenodo.org/records/6090214 (파일 이름 `lastfm-dataset-360K.tar.gz`)
- 넣는 곳: `data/raw/lastfm/`
- 내용: 사용자별로 많이 들은 아티스트와 재생 횟수, 사용자 프로필(국가 포함)
- 2008~2009년에 수집한 한 시점의 기록이라 "언제 들었는지" 순서 정보는 없다.
- 압축을 풀면 `data/raw/lastfm/lastfm-dataset-360K/` 안에 tsv 파일 두 개가 생긴다. 파일이 맞는지는 같이 들어있는 README.txt의 MD5 값으로 확인할 수 있다.
- 나라는 사용자가 프로필에 직접 고른 값이다. "Antarctica"(365명)처럼 실제 거주지로 보기 어려운 값 4개(사용자 717명)는 뺀다. 목록은 `src/config.py`의 `EXCLUDED_ISO3`.

정리 규칙 (`src/load_lastfm.py`)
- 아티스트 구분: MusicBrainz ID(mbid, 아티스트마다 붙은 고유 번호)가 있으면 그걸 쓰고, 없으면 아티스트 이름을 쓴다. 같은 mbid가 여러 이름 표기로 나오는 경우가 많아서 mbid를 먼저 쓴다.
- 같은 사용자-아티스트가 두 줄 이상이면 재생 횟수를 합친다.
- 재생 횟수가 0인 줄은 뺀다.
- 재생 기록은 있는데 프로필이 없는 사용자 2명은 나라를 몰라서 뺀다.
- 만든 사람: Òscar Celma
- 이용 조건: 비상업적 용도만 가능 (Zenodo 라이선스 표기 `other-nc`). 쓸 때 Last.fm 출처를 밝혀야 한다.

### WVS Wave 5 (조사 연도 2004~2009)

- 받는 곳: https://www.worldvaluessurvey.org (Data & Documentation → Wave 5)
- 넣는 곳: `data/raw/wvs/`
- 받을 파일: `WV5_Data_csv_v20180912` (CSV). 같은 페이지의 Codebook, Questionnaire RootVersion, WVSA Citation format PDF도 같이 받는다.
- 사이트에서 이름, 소속, 사용 목적을 적고 이용 조건에 동의해야 받을 수 있다.
- 이용 조건: 비영리 목적만, 데이터 파일 재배포 금지, 결과를 쓸 때 참고문헌에 인용.
- 파일 형식 (`src/load_wvs.py`): 세미콜론 구분, 쉼표 소수점(예: `,94` = 0.94), 빈칸과 음수(-1~-5)는 결측. V2가 ISO 숫자 나라 코드.
- 조사 연도는 나라마다 다르다(V260 열 기준 2004~2009년).
- 인용: Inglehart, R., C. Haerpfer, A. Moreno, C. Welzel, K. Kizilova, J. Diez-Medrano, M. Lagos, P. Norris, E. Ponarin & B. Puranen et al. (eds.). 2018. World Values Survey: Round Five - Country-Pooled Datafile. Madrid, Spain & Vienna, Austria: JD Systems Institute & WVSA Secretariat. doi.org/10.14281/18241.7

### 재배포 금지

두 데이터 모두 원본을 다른 곳에 다시 올리면 안 된다. 그래서 `data/raw/`, `data/processed/` 안의 파일과 압축 파일은 `.gitignore`로 막아뒀다. 팀원은 각자 위 방법으로 받는다.
