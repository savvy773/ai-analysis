# ai-analysis 기술 스택

ai-analysis는 공개 AI 모델 리더보드의 비용·응답 시간·성능 데이터를 모아 터미널에서 비교하는 Python 애플리케이션이다. Textual로 대화형 화면을 구성하고, Rich로 일반 표를 출력하며 Markdown 내보내기도 지원한다. 모델 API를 호출해 직접 벤치마크를 실행하는 프로그램은 아니다.

기준일: 2026-10-09. 버전은 프로젝트 설정과 잠금 파일을 기준으로 한다.

## 주요 기술

| 구분 | 기술 및 버전 | 프로젝트에서의 역할 |
|---|---|---|
| 언어 및 런타임 | Python 3.14 계열 | `.python-version`은 `3.14`, `pyproject.toml`의 요구 버전은 `>=3.14`. 확인된 로컬 가상환경은 3.14.8이다. |
| 환경 및 의존성 관리 | uv | `.venv`와 `uv.lock`으로 실행 환경과 의존성을 관리한다. uv 자체 버전은 프로젝트에서 고정하지 않는다. |
| 패키지 빌드 | setuptools >=80 | `setuptools.build_meta`로 Python 모듈을 패키징하고 `ai-analysis` 실행 명령을 등록한다. |
| 대화형 터미널 UI | Textual 8.2.8 | 제조사 탭, 검색창, 데이터 표, 상세 패널, 키보드 및 마우스 이벤트를 구성한다. |
| 표와 스타일 출력 | Rich 15.0.0 | 일반 표와 색상, 최고 값 강조, 출력 폭 조절을 담당한다. TUI 셀에도 `Text`를 사용한다. |
| 명령행 인자 | `argparse` | 제조사, 정렬, 표시 개수, 점수 하한, 검색, 새로고침, 출력 형식을 받는다. |
| HTTP 수집 | `urllib.request` | 공개 페이지와 데이터 파일을 가져온다. 요청별 제한 시간은 60초다. |
| 데이터 파싱 | `re`, `json`, `csv`, `io` | HTML 내 JSON 추출, 모델명 정규화, LiveBench CSV 및 분류 JSON 처리를 담당한다. |
| 데이터 모델 | `dataclasses`, 타입 힌트 | 모델명, 제작사, 비용, 시간, 점수와 벤치마크 지표를 `Model`에 담는다. |
| 캐시 및 시간 | `pathlib`, `datetime` | JSON 파일 캐시를 저장한다. 수집 시각은 UTC로 저장하고 화면에서는 로컬 시간으로 표시한다. |

Rich와 Textual은 직접 의존성으로 정확한 버전을 고정한다. `uv.lock`에는 Markdown 렌더링 관련 패키지, Pygments, platformdirs, typing-extensions 등의 전이 의존성도 기록되어 있다. 별도 데이터베이스나 웹 서버는 사용하지 않는다.

## Textual과 Rich의 차이

Textual은 Python으로 터미널 안에 대화형 화면을 만드는 라이브러리다. 이 프로젝트에서는 제조사 탭을 바꾸거나, 검색어를 입력하거나, 방향키로 모델을 선택하면 화면의 표와 상세 정보가 갱신된다. 화면 배치는 `src/ai_analysis/tui.py` 안의 Textual CSS로 정의한다.

Rich는 텍스트와 표를 읽기 좋게 출력하는 역할을 맡는다. `--print`로 한 번 출력하는 표는 Rich로 만들고, 계속 조작하는 대화형 화면은 Textual로 구성한다. Textual 화면의 셀에도 Rich의 `Text` 객체로 색상과 강조를 적용한다.

## 코드 구성

| 파일 | 책임 |
|---|---|
| [`run.py`](../run.py) | 루트 실행 파일(더블클릭용). 의존성이 없으면 `uv run --project`로 다시 실행하고, 더블클릭 실행이면 종료 전에 대기한다. |
| [`src/ai_analysis/cli.py`](../src/ai_analysis/cli.py) | CLI 인자 처리, TUI·표·Markdown·HTML 출력 선택, Rich 및 Markdown 표 생성. `ai-analysis` 명령의 진입점. |
| [`src/ai_analysis/data.py`](../src/ai_analysis/data.py) | 데이터 수집·파싱·캐시, 모델명과 추론 강도 정규화, 모델 선별 및 정렬. |
| [`src/ai_analysis/style.py`](../src/ai_analysis/style.py) | 공통 열 정의, 제작사 색상, 최고 값과 상위·하위 25% 구간의 스타일 규칙. |
| [`src/ai_analysis/tui.py`](../src/ai_analysis/tui.py) | Textual 위젯과 이벤트 처리, 데이터 로딩 작업, 모델 상세 패널, Markdown 클립보드 복사. |
| [`src/ai_analysis/web.py`](../src/ai_analysis/web.py) | 브라우저용 단일 HTML 리포트(`report.html`) 생성. 필터·정렬·검색은 페이지 안의 JavaScript가 처리한다. |
| [`pyproject.toml`](../pyproject.toml) | 프로젝트 정보, Python 요구 버전, 직접 의존성, setuptools 빌드 설정. `ai-analysis` 명령을 `ai_analysis.cli:main`에 연결한다. |
| [`uv.lock`](../uv.lock) | 직접 및 전이 의존성의 해석 결과와 버전 고정. |

## 데이터 흐름

1. 유효한 캐시가 있으면 저장된 데이터를 읽는다. 기본 유효 기간은 6시간이며 `--refresh`로 다시 수집할 수 있다.
2. Artificial Analysis 리더보드 HTML에 포함된 Next.js 데이터에서 JSON 객체를 정규식으로 추출한다. Next.js는 수집 대상 사이트의 기술이며 이 프로젝트의 실행 의존성은 아니다.
3. LiveBench 홈페이지의 JavaScript 번들에서 날짜 후보를 찾고, 최신 날짜부터 CSV 표와 분류 JSON을 요청한다. 모델명과 추론 강도를 정규화해 Agentic Coding 및 Coding 점수를 결합한다.
4. 작업당 비용이 있는 모델을 `Model`로 변환한다. 제조사·점수·검색 조건을 적용한 다음 점수 상위 N개를 고르고, 요청한 지표로 정렬한다. 지표가 없는 모델은 마지막에 배치한다.
5. 대화형 터미널에서는 TUI, 파이프 출력이나 `--print`에서는 일반 표, `--markdown`에서는 Markdown 표, `--web`에서는 루트의 `report.html`을 만들어 브라우저로 연다.

TUI의 데이터 로딩은 Textual의 `@work(thread=True, exclusive=True)` 작업으로 실행한다. 작업 스레드는 `call_from_thread`를 통해 화면에 결과를 전달한다. 브라우저 자동화나 JavaScript 실행 엔진은 사용하지 않는다.

기본 캐시 파일은 `.cache/models.json`이며 원본 모델 데이터, LiveBench 데이터, 수집 시각과 표 날짜를 저장한다. `--from-html`은 Artificial Analysis 입력을 로컬 HTML로 대체하지만 LiveBench 수집은 여전히 시도하므로 완전한 오프라인 모드는 아니다.

## 환경 설정

| 환경 변수 | 기본값 | 용도 |
|---|---|---|
| `AA_URL` | `https://artificialanalysis.ai/leaderboards/models` | Artificial Analysis 수집 주소 |
| `LB_URL` | `https://livebench.ai` | LiveBench 기본 주소 |
| `AA_CACHE_DIR` | 프로젝트의 `.cache` 디렉터리 | 캐시 저장 위치 |
| `AA_CACHE_TTL_HOURS` | `6` | 캐시 유효 기간 |
| `AA_PAUSE` | 실행 환경에서 판단 | 더블클릭 실행 및 종료 대기 판단에 사용. `1`로 활성화하고 `0`으로 비활성화한다. |

Windows 탐색기 더블클릭 감지는 `ctypes`의 Windows API로 처리하며 Windows에서만 실행하도록 조건이 걸려 있다. 일반 실행 명령은 `ai-analysis` 또는 `uv run run.py`다. 사용법은 [`usage.md`](usage.md)를 참고한다.

## 유지보수 시 참고

- Artificial Analysis의 내장 데이터 형식과 LiveBench의 번들·파일명 규칙에 의존한다. 대상 사이트 구조가 바뀌면 수집·파싱 코드를 조정해야 한다.
- LiveBench 수집에서 지정된 네트워크·파싱 오류를 처리하면 해당 지표 없이 나머지 모델 데이터를 반환한다.
- 오류는 CLI의 표준 오류 출력 또는 TUI 상태 영역에 표시한다. 현재 별도 로그 파일 회전, 테스트 도구, CI 설정은 프로젝트 구성에 포함되어 있지 않다.
- 프로젝트 패키지 버전은 `pyproject.toml`과 `uv.lock`으로 관리한다. Python 런타임 업데이트와 프로젝트 의존성 업데이트는 별개다.
