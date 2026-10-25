# 나라별 인기 아티스트 섞기 실험

비즈니스 인텔리전스 중간고사 과제 (교수님 제시 옵션 A: Last.fm + WVS 기반).

## 세 줄 요약

- 음악 서비스가 새 나라에 막 진출해서 초기 사용자가 조금밖에 없는 상황을 가정한다.
- 추천 목록에서 "전체 국가 인기 아티스트"와 "그 나라 인기 아티스트"를 어떤 비중으로 섞어야 추천이 잘 맞는지 실험한다.
- 비중을 나라마다 따로 정하는 게 나은지(H1), 가치관(WVS)이 비슷한 나라의 비중을 빌려 쓰면 나은지(H2)를 확인한다.

앱을 만드는 과제가 아니라, 공개 데이터로 하는 오프라인 실험이다.

## 지금 진행 상황

- [x] 폴더, 가상환경, 패키지 세팅
- [x] Last.fm 360K 받기
- [x] 데이터 확인: Last.fm 쪽 (나라별 사용자 수, 사용자당 아티스트 수)
- [ ] 데이터 확인: WVS와 겹치는 나라 (WVS 파일 받은 뒤)
- [ ] 모델 실험
- [ ] 보고서

## 용어 정리

- **인기 아티스트**: 많이 들린 아티스트. 이 프로젝트의 추천 단위는 "곡"이 아니라 "아티스트"다.
- **섞기**: 전체 인기 점수와 나라 인기 점수를 같은 범위(0~1)로 맞춘 뒤, 정한 비중으로 더하는 것.
- **협업 필터링**: 나와 취향이 비슷한 사람들이 들은 아티스트를 추천하는 방법. 여기서는 ALS나 BPR 중 하나를 쓴다.
- **베이스라인**: 비교의 기준이 되는 가장 단순한 방법. 여기서는 "전체 인기 아티스트를 그대로 추천"이다.
- **Recall@K**: 추천한 K개 안에 사용자가 실제로 들은 아티스트가 얼마나 들어있는지.
- **NDCG@K**: Recall@K와 비슷한데, 맞힌 아티스트가 목록 위쪽에 있을수록 점수를 더 준다.
- **WVS (World Values Survey)**: 나라별로 사람들의 가치관을 조사한 설문. 나라끼리 얼마나 비슷한지 재는 데 쓴다.

## 폴더 구성

```
bi-crosscultural-rec/
├── data/
│   ├── raw/lastfm/     Last.fm 원본 (직접 받아서 넣기, git에 안 올라감)
│   ├── raw/wvs/        WVS 원본 (직접 받아서 넣기, git에 안 올라감)
│   └── processed/      코드가 만든 중간 파일 (git에 안 올라감)
├── src/
│   ├── config.py         경로와 숫자 기준값(K, 보여줄 아티스트 수 등)을 모아둔 곳
│   ├── load_lastfm.py    Last.fm 원본을 읽고 정리하는 함수
│   ├── country_codes.py  나라 이름을 ISO 세 글자 코드(예: KOR)로 바꾸는 함수
│   └── check_data.py     데이터 확인 표를 만드는 코드
├── results/
│   ├── tables/         결과 표 (data_check.md에 데이터 확인 결과)
│   └── figures/        결과 그림
├── report/             보고서에 넣을 자료
├── requirements.txt    필요한 파이썬 패키지 목록
└── AI_사용기록.md       AI로 한 작업 기록 (보고서에 밝혀야 함)
```

## 처음 받은 사람이 할 일

맥/리눅스 터미널 기준이다. 순서대로 복사해서 실행하면 된다.

1. 프로젝트 폴더로 이동

   ```bash
   cd bi-crosscultural-rec
   ```

2. 가상환경 만들기 (파이썬 3.12에서 확인함)

   ```bash
   python3 -m venv .venv
   ```

3. 가상환경 켜기

   ```bash
   source .venv/bin/activate
   ```

4. 패키지 설치

   ```bash
   pip install -r requirements.txt
   ```

5. Last.fm 360K 받기 (약 543MB, 시간이 좀 걸림)

   ```bash
   curl -L -o data/raw/lastfm/lastfm-dataset-360K.tar.gz "https://zenodo.org/api/records/6090214/files/lastfm-dataset-360K.tar.gz/content"
   ```

6. 압축 풀기

   ```bash
   tar -xzf data/raw/lastfm/lastfm-dataset-360K.tar.gz -C data/raw/lastfm
   ```

7. WVS Wave 5 받기: 아래 "데이터" 항목을 보고 직접 받아서 `data/raw/wvs/` 에 넣는다.

8. 데이터 확인 코드 실행 (1분쯤 걸림, 메모리 4GB 정도 씀)

   ```bash
   python src/check_data.py
   ```

   결과는 `results/tables/data_check.md`에서 본다.

## 데이터

### Last.fm 360K

- 받는 곳: https://zenodo.org/records/6090214 (파일 이름 `lastfm-dataset-360K.tar.gz`)
- 넣는 곳: `data/raw/lastfm/`
- 내용: 사용자별로 많이 들은 아티스트와 재생 횟수, 사용자 프로필(국가 포함)
- 2008~2009년쯤 모은 한 시점의 기록이라 "언제 들었는지" 순서 정보는 없다.
- 압축을 풀면 `data/raw/lastfm/lastfm-dataset-360K/` 안에 tsv 파일 두 개가 생긴다. 파일이 맞는지는 같이 들어있는 README.txt의 MD5 값으로 확인할 수 있다.
- 나라는 사용자가 프로필에 직접 고른 값이다. "Antarctica"(365명)처럼 실제 거주지로 보기 어려운 값도 있다.

정리 규칙 (`src/load_lastfm.py`)
- 아티스트 구분: MusicBrainz ID(mbid, 아티스트마다 붙은 고유 번호)가 있으면 그걸 쓰고, 없으면 아티스트 이름을 쓴다. 같은 mbid가 여러 이름 표기로 나오는 경우가 많아서 mbid를 먼저 쓴다.
- 같은 사용자-아티스트가 두 줄 이상이면 재생 횟수를 합친다.
- 재생 횟수가 0인 줄은 뺀다.
- 재생 기록은 있는데 프로필이 없는 사용자 2명은 나라를 몰라서 뺀다.
- 만든 사람: Òscar Celma
- 이용 조건: 비상업적 용도만 가능 (Zenodo 라이선스 표기 `other-nc`). 쓸 때 Last.fm 출처를 밝혀야 한다.

### WVS Wave 5 (2005~2009)

- 받는 곳: https://www.worldvaluessurvey.org (Data & Documentation → Wave 5)
- 넣는 곳: `data/raw/wvs/`
- 사이트에서 이름과 사용 목적을 적어야 받을 수 있다.
- 다운로드 조건과 인용 형식은 받을 때 확인해서 여기에 적는다. (아직 미정)

### 재배포 금지

두 데이터 모두 원본을 다른 곳에 다시 올리면 안 된다. 그래서 `data/raw/`, `data/processed/` 안의 파일과 압축 파일은 `.gitignore`로 막아뒀다. 팀원은 각자 위 방법으로 받는다.

## 작업 규칙

- 브랜치 이름: 영어 소문자 단어를 하이픈으로 연결 (예: `data-check`, `popular-mix`, `cf-model`, `wvs-link`, `report`)
- 커밋 메시지: 한국어로 무엇을 했는지 한 줄 (예: "나라별 사용자 수 확인 코드 추가")
- 숫자 기준값은 `src/config.py`에서만 바꾼다.
