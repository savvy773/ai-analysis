# ai-analysis

- `ai_compare.py` — 루트 실행 파일(더블클릭). 의존성 없으면 uv 환경으로 재실행
- `src/ai_analysis/cli.py` — `ai-analysis` 명령 진입점. 기본 HTML 리포트, `--print`/`--markdown`이면 터미널 표
- `src/ai_analysis/data.py` — 수집·파싱·캐시(`load`), LiveBench 연결(`fetch_livebench`, `model_key`), 선별·정렬(`select`)
- `src/ai_analysis/style.py` — 열 정의(`METRICS`)와 색 규칙
- `src/ai_analysis/web.py` — 단일 HTML 리포트(`report.html`)
- `assets/ai-compare.svg` / `assets/ai-compare.ico` — 앱 아이콘 원본과 Windows 바로가기 아이콘
- [docs/usage.md](docs/usage.md) — 사용법 · [docs/tech-stack.md](docs/tech-stack.md) — 기술 스택, 코드 구조, 데이터 흐름
