# ai-analysis

[Artificial Analysis](https://artificialanalysis.ai/leaderboards/models) 리더보드를 읽어서 기준 점수 이상인 AI 모델을 표로 비교한다. 페이지 한 번을 내려받아 로컬에서 처리하므로 AI API 토큰은 쓰지 않는다.

| 열 | 내용 |
|---|---|
| 작업당 비용 | Intelligence Index 실행 비용 / 작업 |
| 총 응답 시간 | 요청 1회 중앙값 |
| 점수 | Intelligence Index |
| 터미널 | Terminal-Bench 4.0 (터미널 에이전트 코딩) |

열마다 가장 좋은 값에 ★, 모델명은 GPT 초록 · Claude 주황.

## 실행

필요한 것: [uv](https://docs.astral.sh/uv/), 인터넷.

```bash
uv run aa_value.py                  # 50점 이상, 작업당 비용 순
uv run aa_value.py --sort tb        # score | time | cost | tb
uv run aa_value.py --min 45 --filter "opus|sol" --top 10
uv run aa_value.py --markdown       # 마크다운 표
```

- Windows: `aa_value.py` 더블클릭 → 결과 표시 후 Enter로 닫힘.
- Linux: `./aa_value.py` (`chmod +x` 한 번).
- uv 없이 `python aa_value.py`로 실행해도 스스로 `uv run`으로 다시 실행한다.
- 다른 페이지를 읽으려면 `AA_URL` 환경 변수, 저장된 HTML은 `--html <파일>`.

사이트 구조가 바뀌면 "모델 데이터를 찾지 못했습니다"가 출력된다.
