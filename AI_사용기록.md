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
