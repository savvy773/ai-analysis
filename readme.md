# ai-analysis

AI 모델의 비용·응답 시간·코딩 성능을 한 표로 비교한다. 데이터는 [Artificial Analysis](https://artificialanalysis.ai/leaderboards/models)와 [LiveBench](https://livebench.ai/)에서 가져오며 AI API 토큰은 쓰지 않는다.

## 화면

![모델 비교 화면](docs/images/overview.png)

최소 Intelligence·Terminal 조건을 AND로 적용하고, 최대 4개 모델을 VS로 비교한다. 하단 추천은 비용 60%·시간 40%의 상대 부담으로 계산하며, 시간 배수의 1.5승을 반영해 느린 모델의 점수를 크게 낮춘다. 비중은 조절할 수 있다. 즐겨찾기와 필터·정렬·추천 비중은 자동 저장한다. Save는 즐겨찾기까지 기본값에 포함하고 Reset은 마지막 Save 상태로 돌아간다.

계산과 조작은 [사용법](docs/usage.md), 수집 경로와 데이터 흐름도는 [기술 문서](docs/tech-stack.md)를 참고한다.

## 빠른 실행

| 하고 싶은 것 | 방법 |
|---|---|
| 그냥 보기 | 루트의 **`ai_compare.py` 더블클릭** → `report.html` 갱신 후 브라우저로 열림 |
| 터미널 어디서나 | `ai-analysis` (위와 같음) |
| 터미널에 표로 | `ai-analysis --print` |

준비: [uv](https://docs.astral.sh/uv/) 설치 후, 프로젝트 폴더에서 `uv tool install --editable .` 한 번.

## 폴더 구조

```
ai-analysis/
├─ ai_compare.py            실행 파일 (더블클릭)
├─ report.html       결과 화면 (실행할 때마다 갱신, git 제외)
├─ docs/             문서
│  ├─ usage.md       옵션 · 키 · 열 설명
│  └─ tech-stack.md  기술 스택 · 코드 구조 · 데이터 흐름
└─ src/ai_analysis/  코드
   ├─ cli.py         명령 옵션 처리, 출력 방식 선택
   ├─ data.py        데이터 수집 · 캐시 · 정렬
   ├─ web.py         HTML 리포트
   └─ style.py       열 구성 · 색 규칙
```

자세한 사용법은 [docs/usage.md](docs/usage.md).
