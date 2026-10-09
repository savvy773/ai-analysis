#!/usr/bin/env python3
"""실행 파일. 더블클릭하거나 `python run.py` / `uv run run.py`로 실행한다.

의존성이 없는 Python으로 실행되면(예: Windows 더블클릭) 이 프로젝트의 uv 환경으로 다시 실행한다.
기본으로 루트의 report.html을 갱신해 브라우저로 연다. 옵션은 `ai-analysis`와 같다 (run.py --print ...).
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def opened_by_double_click() -> bool:
    # 탐색기 더블클릭이면 새 콘솔에 python만 붙어 있다. 터미널에서 실행하면 셸이 함께 있다.
    if "AA_PAUSE" in os.environ:
        return os.environ["AA_PAUSE"] == "1"
    if os.name != "nt" or not sys.stdin.isatty():
        return False
    import ctypes

    buf = (ctypes.c_uint32 * 16)()
    return ctypes.windll.kernel32.GetConsoleProcessList(buf, 16) <= 2  # type: ignore[attr-defined]


def pause_if_double_clicked(paused: bool) -> None:
    if paused:
        input("\nEnter를 누르면 닫힙니다...")


if __name__ == "__main__":
    paused = opened_by_double_click()
    try:
        from ai_analysis.cli import main
    except ImportError:
        env = dict(os.environ, AA_PAUSE="1" if paused else "0")
        try:
            rc = subprocess.call(["uv", "run", "--quiet", "--project", ROOT, "python", __file__, *sys.argv[1:]], env=env)
        except FileNotFoundError:
            print("uv를 찾지 못했습니다: https://docs.astral.sh/uv/ 에서 설치하세요.", file=sys.stderr)
            pause_if_double_clicked(paused)
            rc = 1
        sys.exit(rc)

    code = main()
    # 브라우저로 여는 기본 동작은 창을 바로 닫고, 터미널에 표를 출력한 경우에만 창을 붙잡아 둔다
    pause_if_double_clicked(paused and ("--print" in sys.argv or "--markdown" in sys.argv))
    sys.exit(code)
