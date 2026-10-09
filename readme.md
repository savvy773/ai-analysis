# ai-analysis

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

```bash
uv run aa_value.py                         # 대화형 화면 (TUI)
uv run aa_value.py --maker claude          # 제조사 탭을 골라 시작
uv run aa_value.py --print --top 10        # 표만 출력
uv run aa_value.py --markdown --sort agentic
uv run aa_value.py --web                   # HTML 리포트를 만들어 브라우저로 열기
uv run aa_value.py --refresh               # 캐시 무시하고 새로 받기
```

TUI 키

| 키 | 동작 |
|---|---|
| `1`–`5` | 제조사: All · Claude · OpenAI · Google · Other |
| `c` `t` `s` `b` `g` | 정렬: Cost · Time · Score · Terminal · Agentic (같은 키 다시 → 역순) |
| `+` `-` / `a` | 표시 개수 ±5 / 점수 상위 20 ↔ 전체 |
| `/`, `Esc` | 모델명 검색(정규식), 검색 지우기 |
| `m` | 현재 표를 마크다운으로 클립보드 복사 |
| `w` | HTML 리포트를 브라우저로 열기 |
| `r` / `q` | 새로고침 / 종료 |

- 어디서나 `ai-analysis` 명령으로 실행: 프로젝트 폴더에서 `uv tool install --editable .` 한 번.
- Windows: `aa_value.py` 더블클릭으로도 실행된다.
- Linux: `./aa_value.py` (`chmod +x` 한 번).
- `python aa_value.py`로 실행해도 스스로 `uv run`으로 다시 실행한다.
- 받은 데이터는 `.cache/`에 6시간 보관한다 (`AA_CACHE_TTL_HOURS`, `AA_CACHE_DIR`). 출처 주소는 `AA_URL`, `LB_URL`로 바꿀 수 있다.

사이트 구조가 바뀌면 "모델 데이터를 찾지 못했습니다"가 출력된다. LiveBench를 못 받으면 Agentic 열만 비고 나머지는 그대로 나온다.
