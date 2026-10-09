# ai-analysis

- `run.py` — 루트 실행 파일(더블클릭). 의존성 없으면 uv 환경으로 재실행
- `src/ai_analysis/cli.py` — `ai-analysis` 명령 진입점. 옵션 처리, TUI·표·마크다운·HTML 분기
- `src/ai_analysis/data.py` — 수집·파싱·캐시(`load`), LiveBench 연결(`fetch_livebench`, `model_key`), 선별·정렬(`select`)
- `src/ai_analysis/style.py` — 열 정의(`METRICS`)와 색 규칙
- `src/ai_analysis/tui.py` — Textual 대화형 화면
- `src/ai_analysis/web.py` — 단일 HTML 리포트(`report.html`)
- [docs/usage.md](docs/usage.md) — 사용법 · [docs/tech-stack.md](docs/tech-stack.md) — 기술 스택, 코드 구조, 데이터 흐름
