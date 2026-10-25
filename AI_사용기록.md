# AI 사용 기록

과제 규정에 따라 AI(Claude)로 한 작업을 적는다. 결과는 팀원이 직접 확인한다.

## 프로젝트 세팅

- 사용한 도구: Claude Code (Anthropic Claude)
- 폴더 구조, `.gitignore`, `requirements.txt`, 가상환경 세팅
- 설정 파일 `src/config.py` 초안 작성 (기준값은 초안이고 팀이 다시 정함)
- README 첫 버전 작성
- Zenodo에서 Last.fm 360K 파일 크기와 라이선스 표기 확인

## 데이터 확인

- Last.fm 360K 다운로드, MD5 확인, 파일을 직접 열어서 컬럼 구조 확인
- 데이터 정리 규칙 제안 (아티스트 구분 기준, 중복 합치기) 및 `load_lastfm.py` 작성
- 나라 이름 -> ISO 코드 변환 `country_codes.py` 작성. 자동 변환이 안 된 10개 나라는 수동 표로 지정
- 데이터 확인 표를 만드는 `check_data.py` 작성 및 실행
- WVS Wave 5 코드북에서 국가 목록(58개)을 확인하고 Last.fm 국가별 사용자 수와 대조 (CSV 확인 전 임시 결과)
- WVS Wave 5 CSV를 직접 열어 형식 확인 (세미콜론 구분, 쉼표 소수점, 빈칸, 음수 결측 코드) 후 `load_wvs.py` 작성
- `check_data.py`에 WVS-Last.fm 공통 나라 표 추가 및 재실행
- 실제 거주지로 보기 어려운 국가값 4개 제외 규칙을 `config.py`에 추가하고 데이터 확인 표 재생성 (제외 결정은 팀)
- 실험 설계 초안 `report/실험설계_초안.md` 작성, 관련 기준값 초안을 `config.py`에 추가, README의 WVS 항목 갱신 (확정은 팀 검토 후)

## 실험 설계 외부 검토

- 사용한 도구: ChatGPT (코드 편집기 확장 프로그램). 프로젝트 폴더와 강의 자료를 읽기만 하게 하고 설계 초안 검토를 맡김
- Claude가 검토 의견을 과제 자료(`Midterm_CrossCulturalRecommendationSystems.pdf`, `Guideline.pdf`)와 데이터로 다시 확인한 뒤 설계 초안 2판에 반영. 반영 내역은 `report/실험설계_초안.md` 16절
- MBID 없는 아티스트 중복 규모 측정 (전체 기록의 0.06%)
- `check_data.py`의 평가 불가 사용자 기준을 설계 문서와 같은 10개로 수정
- 팀 결정(H3 추가, 15절 기준값 확정)을 설계 문서와 `config.py`에 표시
- ChatGPT 2차 검토(2판 대상) 의견을 Claude가 문서와 코드로 확인한 뒤 설계 초안 3판에 반영. H3의 CF 학습 범위는 계산량 때문에 나라 묶음 방식으로 바꿔 반영. 반영 내역은 `report/실험설계_초안.md` 16절
- `check_data.py`에 MBID 없는 아티스트 중복 집계(7번 항목) 추가. 이전에 0.1%로 적었던 값을 0.06%로 정정
