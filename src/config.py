"""프로젝트 전체에서 쓰는 경로와 숫자 기준값을 한 곳에 모아둔 파일.

기준값을 바꿀 때는 코드 여러 곳을 고치지 말고 여기만 고친다.
'초안'이라고 적힌 값은 데이터 확인 결과를 보고 팀이 다시 정한다.
"""

from pathlib import Path

# ---------- 경로 ----------
# 어느 폴더에서 실행해도 같은 경로를 쓰도록 이 파일 위치 기준으로 잡는다
PROJECT_DIR = Path(__file__).resolve().parent.parent

RAW_LASTFM_DIR = PROJECT_DIR / "data" / "raw" / "lastfm"
RAW_WVS_DIR = PROJECT_DIR / "data" / "raw" / "wvs"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
TABLES_DIR = PROJECT_DIR / "results" / "tables"
FIGURES_DIR = PROJECT_DIR / "results" / "figures"

# ---------- 재현성 ----------
# 무작위로 나누는 모든 단계에서 같은 결과가 나오게 고정
RANDOM_SEED = 42

# ---------- 나라 고르기 (초안) ----------
# 사용자가 이보다 적은 나라는 나라별 비교에서 뺀다
MIN_USERS_PER_COUNTRY = 100

# ---------- 사용자 나누기 (초안) ----------
# 사용자 단위로 학습용 / 검증용 / 시험용으로 나눈다 (합이 1이어야 함)
TRAIN_USER_RATIO = 0.70
VALID_USER_RATIO = 0.15
TEST_USER_RATIO = 0.15

# ---------- 평가 (초안) ----------
# 평가 사용자에게 미리 보여주는 아티스트 수. 나머지를 맞히게 한다
N_SHOWN_ARTISTS = 5
# 추천 목록 길이. Recall@K, NDCG@K의 K
TOP_K = 10

# ---------- 새 나라 실험 H2 (초안) ----------
# 새 나라에서 인기 목록을 만들 때 쓰는 초기 사용자 수
N_EARLY_USERS = 50
