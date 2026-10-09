# 사용법

[Artificial Analysis](https://artificialanalysis.ai/leaderboards/models)와 [LiveBench](https://livebench.ai/) 데이터를 모아 AI 모델의 비용·시간·코딩 성능을 한 표로 비교한다. 페이지와 공개 CSV를 내려받아 로컬에서 처리하므로 AI API 토큰은 쓰지 않는다.

| 열 | 내용 | 출처 |
|---|---|---|
| Cost | 작업당 비용 (Intelligence Index 실행 비용 / 작업) | Artificial Analysis |
| Time | 총 응답 시간 (요청 1회 중앙값) | Artificial Analysis |
| Score | Intelligence Index | Artificial Analysis |
| Terminal | Terminal-Bench 4.0 — 터미널 에이전트 코딩 | Artificial Analysis |
| Agentic | Agentic Coding (JS/TS/Python 저장소 작업) 평균 | LiveBench |

색: ★ 열 최고 값 · 연두 상위 25% · 회색 하위 25%. 모델명은 Claude 주황 · OpenAI 민트 · Google 파랑.
LiveBench는 주로 max/xhigh 설정만 측정해서, 나머지 설정은 Agentic 칸이 `-`로 나온다.

## 실행

필요한 것: [uv](https://docs.astral.sh/uv/), 인터넷.

`run.py`를 더블클릭하거나 `ai-analysis`를 실행하면 루트의 `report.html`을 최신 데이터로 다시 만들고 브라우저로 연다.

```bash
ai-analysis                               # report.html 갱신 후 브라우저로 열기
ai-analysis --maker claude --sort tb      # 브라우저에서 처음 보일 탭과 정렬
ai-analysis --refresh                     # 캐시 무시하고 데이터 새로 받기
ai-analysis --out 경로.html               # 다른 위치에 저장 (브라우저는 열지 않음)
ai-analysis --print --top 10              # 브라우저 대신 터미널에 표 출력
ai-analysis --markdown --sort agentic     # 마크다운 표 출력
```

브라우저 화면

| 조작 | 동작 |
|---|---|
| 상단 탭 | 제조사: All · Claude · OpenAI · Google · Other |
| Top 선택 | 점수 상위 10 / 20 / 40 / 전체 |
| 검색창 | 모델명 검색(정규식, 예: `opus\|sol`) |
| 열 제목 클릭 | 그 열로 정렬, 다시 클릭하면 역순 |
| 행 클릭 | 아래에 가격·속도·컨텍스트 등 상세 |

- `ai-analysis` 명령 설치: 프로젝트 폴더에서 `uv tool install --editable .` 한 번. 설치 없이 `uv run run.py`도 같다.
- Windows: 루트의 `run.py` 더블클릭으로도 실행된다.
- Linux: `./run.py` (`chmod +x run.py` 한 번).
- `python run.py`로 실행해도 스스로 `uv run`으로 다시 실행한다.
- 받은 데이터는 `.cache/`에 6시간 보관한다 (`AA_CACHE_TTL_HOURS`, `AA_CACHE_DIR`). 출처 주소는 `AA_URL`, `LB_URL`로 바꿀 수 있다.

사이트 구조가 바뀌면 "모델 데이터를 찾지 못했습니다"가 출력된다. LiveBench를 못 받으면 Agentic 열만 비고 나머지는 그대로 나온다.
