# ai-analysis

AI 모델의 비용·응답 시간·코딩 성능을 한 표로 비교한다. 데이터는 [Artificial Analysis](https://artificialanalysis.ai/leaderboards/models)와 [LiveBench](https://livebench.ai/)에서 가져오며 AI API 토큰은 쓰지 않는다.

## 빠른 실행

| 하고 싶은 것 | 방법 |
|---|---|
| 그냥 보기 | 루트의 **`run.py` 더블클릭** |
| 터미널 어디서나 | `ai-analysis` |
| 브라우저로 보기 | `ai-analysis --web` → 루트에 `report.html` 생성 |

준비: [uv](https://docs.astral.sh/uv/) 설치 후, 프로젝트 폴더에서 `uv tool install --editable .` 한 번.

## 폴더 구조

```
ai-analysis/
├─ run.py            실행 파일 (더블클릭)
├─ report.html       --web 결과 (자동 생성, git 제외)
├─ docs/             문서
│  ├─ usage.md       옵션 · 키 · 열 설명
│  └─ tech-stack.md  기술 스택 · 코드 구조 · 데이터 흐름
└─ src/ai_analysis/  코드
   ├─ cli.py         명령 옵션 처리, 출력 방식 선택
   ├─ data.py        데이터 수집 · 캐시 · 정렬
   ├─ tui.py         터미널 대화형 화면
   ├─ web.py         HTML 리포트
   └─ style.py       열 구성 · 색 규칙
```

자세한 사용법은 [docs/usage.md](docs/usage.md).
