#!/usr/bin/env python3
"""실행 파일. 더블클릭하거나 `python ai_compare.py` / `uv run ai_compare.py`로 실행한다.

의존성이 없는 Python으로 실행되면(예: Windows 더블클릭) 이 프로젝트의 uv 환경으로 다시 실행한다.
기본으로 루트의 report.html을 갱신해 브라우저로 연다. 옵션은 `ai-analysis`와 같다 (ai_compare.py --print ...).
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
        try:
            input("\nEnter를 누르면 닫힙니다...")
        except EOFError:
            pass


def execute() -> int:
    try:
        from ai_analysis.cli import main
    except ImportError as e:
        if (not isinstance(e, ModuleNotFoundError) or e.name not in {"ai_analysis", "rich"}
                or os.environ.get("AA_REEXEC") == "1"):
            print(f"불러오지 못했습니다: {e}", file=sys.stderr)
            return 1
        # 자식은 대기하지 않고, 최초 실행한 창에서만 결과에 따라 대기한다.
        env = dict(os.environ, AA_PAUSE="0", AA_REEXEC="1")
        try:
            return subprocess.call(["uv", "run", "--quiet", "--project", ROOT, "python", os.path.join(ROOT, "ai_compare.py"), *sys.argv[1:]], env=env)
        except FileNotFoundError:
            print("uv를 찾지 못했습니다: https://docs.astral.sh/uv/ 에서 설치하세요.", file=sys.stderr)
            return 1
    return main()


def run() -> int:
    paused = opened_by_double_click()
    try:
        code = execute()
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else (1 if e.code else 0)
    except OSError as e:
        print(f"실행하지 못했습니다: {e}", file=sys.stderr)
        code = 1
    pause_if_double_clicked(paused and (code != 0 or "--print" in sys.argv or "--markdown" in sys.argv))
    return code


if __name__ == "__main__":
    sys.exit(run())
