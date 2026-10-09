# ai-analysis

- `aa_value.py` — 진입점. uv 재실행 부트스트랩, 인자 처리, TUI 또는 표 출력 분기
- `aa_data.py` — 수집·파싱·캐시(`load`), LiveBench 연결(`fetch_livebench`, `model_key`로 이름 매칭), 선별·정렬(`select`)
- `aa_style.py` — 열 정의(`METRICS`)와 색 규칙(제조사 색, 상위/하위 25% 등급)
- `aa_tui.py` — Textual 대화형 화면 (제조사 탭, 정렬 키, 검색, 상세 패널)
- `readme.md` — 사용법 · `pyproject.toml` / `uv.lock` — 의존성(rich, textual)
