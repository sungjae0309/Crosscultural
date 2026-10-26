"""프로젝트 전체에서 쓰는 경로와 숫자 기준값을 한 곳에 모아둔 파일.

기준값을 바꿀 때는 코드 여러 곳을 고치지 말고 여기만 고친다.
값의 근거는 report/실험설계.md에 있다. 실험 설계를 확정했으므로 결과를 보고 바꾸지 않는다.
"""

from pathlib import Path

# ---------- 경로 ----------
# 어느 폴더에서 실행해도 같은 경로를 쓰도록 이 파일 위치 기준으로 잡는다
PROJECT_DIR = Path(__file__).resolve().parent.parent

RAW_LASTFM_DIR = PROJECT_DIR / "data" / "raw" / "lastfm"
RAW_WVS_DIR = PROJECT_DIR / "data" / "raw" / "wvs"
WVS_CSV_PATH = RAW_WVS_DIR / "WV5_Data_csv_v20180912.csv"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
TABLES_DIR = PROJECT_DIR / "results" / "tables"
FIGURES_DIR = PROJECT_DIR / "results" / "figures"

# ---------- 재현성 ----------
# 무작위로 나누는 모든 단계에서 같은 결과가 나오게 고정
RANDOM_SEED = 42

# ---------- 나라 고르기 ----------
# 사용자가 이보다 적은 나라는 나라별 비교에서 뺀다
MIN_USERS_PER_COUNTRY = 100

# 실제 거주지로 보기 어려운 Last.fm 국가값. 이 나라 사용자는 처음부터 뺀다
# (가입 때 장난으로 고른 값으로 보임. 합쳐서 717명, 전체의 0.2%)
EXCLUDED_ISO3 = {
    "ATA": "Antarctica",
    "VAT": "Holy See (Vatican City State)",
    "CCK": "Cocos (Keeling) Islands",
    "UMI": "United States Minor Outlying Islands",
}

# ---------- 사용자 나누기 ----------
# 사용자 단위로 학습용 / 검증용 / 시험용으로 나눈다 (합이 1이어야 함)
TRAIN_USER_RATIO = 0.70
VALID_USER_RATIO = 0.15
TEST_USER_RATIO = 0.15

# ---------- 평가 ----------
# 평가 사용자에게 미리 보여주는 아티스트 수. 나머지를 맞히게 한다
N_SHOWN_ARTISTS = 5
# 추천 목록 길이. Recall@K, NDCG@K의 K
TOP_K = 10

# 평가 사용자로 쓰려면 아티스트가 이만큼은 있어야 한다 (보여줄 5개 + 정답)
MIN_ARTISTS_EVAL_USER = 10

# ---------- 섞기 ----------
# 섞은 점수 = (1 - w) * 전체 인기 + w * 나라 인기. w 후보
WEIGHT_GRID = [round(step / 10, 1) for step in range(11)]
# 인기 점수 기준: "listeners" = 들은 사용자 비율, "plays" = 재생 수 합 (보조 분석)
POPULARITY_MEASURE = "listeners"

# ---------- H1 ----------
# 결과를 나라 크기별로 나눠 볼 때의 경계 (사용자 수). 100~499 / 500~4,999 / 5,000 이상
H1_SIZE_BINS = [100, 500, 5000]

# ---------- 새 나라 실험 H2 ----------
# H2 대상 나라의 최소 사용자 수 (초기 사용자를 뽑고도 시험 사용자가 30명은 남게)
MIN_USERS_H2 = 200
# 새 나라에서 인기 목록을 만들 때 쓰는 초기 사용자 수
N_EARLY_USERS = 50
# 초기 사용자 뽑기 반복 횟수
N_EARLY_REPEATS = 10
# WVS 거리가 가까운 나라 몇 개를 쓸지. 이 나라들의 검증 NDCG 평균이 가장 높은 w를 고른다
WVS_NEIGHBORS_K = 3
# 무작위 나라 비교를 몇 번 반복할지
N_RANDOM_REPEATS = 100
# 실패 분석의 "자기 나라 취향" 대리 지표: 그 나라 상위 LOCAL_TOP_N개 중
# 그 나라를 뺀 전체의 상위 GLOBAL_TOP_N개에 없는 비율 (학습 사용자 기준)
LOCAL_TOP_N = 100
GLOBAL_TOP_N = 1000

# ---------- 협업 필터링 H3 ----------
# ALS 설정 후보. 검증 사용자로 고른다
CF_FACTORS_GRID = [64, 128]
CF_REG_GRID = [0.01, 0.1]
CF_ITERATIONS = 15
# ALS 입력값: "binary" = 들었으면 1, "log_plays" = log(1 + 재생 수) (보조 분석)
CF_INPUT = "binary"
# CF를 새 나라마다 따로 학습하지 않고, H2 대상 나라를 이 수만큼 묶어 묶음 단위로 빼고 학습한다
N_CF_GROUPS = 6

# ---------- 통계 ----------
# 나라 단위 부트스트랩 반복 횟수
N_BOOTSTRAP = 10000
# Wilcoxon 부호순위 검정 유의수준 (양측)
ALPHA = 0.05

# ---------- WVS ----------
# 나라 거리에 쓰는 WVS 종합 지수 (Welzel). 결과를 보기 전에 고정한다
WVS_INDEX_COLUMNS = ["SACSECVAL", "RESEMAVAL"]
# 응답자 가중치
WVS_WEIGHT_COLUMN = "V259"
