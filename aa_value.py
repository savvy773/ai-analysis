#!/usr/bin/env python3
# 의존성이 없으면 이 프로젝트의 uv 환경으로 다시 실행한다 (아래 try/except ImportError)
USAGE = """Artificial Analysis 리더보드로 AI 모델의 비용·시간·성능을 비교한다.

터미널에서는 대화형 화면(TUI), 파이프·--print에서는 표를 출력한다.
  ./aa_value.py                      # TUI: 1-5 제조사, c/t/s/b/g 정렬, / 검색, r 새로고침, q 종료
  ./aa_value.py --maker claude       # 제조사 탭을 골라서 시작
  ./aa_value.py --print --maker google --top 10
  ./aa_value.py --markdown --sort tb
"""
import argparse
import os
import sys


def opened_by_double_click() -> bool:
    # 탐색기 더블클릭이면 새 콘솔에 python만 붙어 있다. 터미널에서 실행하면 셸이 함께 있다.
    if "AA_PAUSE" in os.environ:
        return os.environ["AA_PAUSE"] == "1"
    if os.name != "nt" or not sys.stdin.isatty():
        return False
    import ctypes

    buf = (ctypes.c_uint32 * 16)()
    return ctypes.windll.kernel32.GetConsoleProcessList(buf, 16) <= 2  # type: ignore[attr-defined]


try:
    import textual  # noqa: F401
    from rich import box
    from rich.console import Console
    from rich.table import Table
except ImportError:
    # uv 없이 실행된 경우(예: Windows 더블클릭) 프로젝트 환경으로 다시 실행한다
    import subprocess

    env = dict(os.environ, AA_PAUSE="1" if opened_by_double_click() else "0")
    try:
        rc = subprocess.call(
            ["uv", "run", "--quiet", "--project", os.path.dirname(os.path.abspath(__file__)),
             "python", __file__, *sys.argv[1:]],
            env=env,
        )
    except FileNotFoundError:
        print("uv를 찾지 못했습니다: https://docs.astral.sh/uv/ 에서 설치하세요.", file=sys.stderr)
        rc = 1
        if env["AA_PAUSE"] == "1":
            input("\nEnter를 누르면 닫힙니다...")
    sys.exit(rc)

import aa_data as d
import aa_style as st

def render_markdown(rows: list[d.Model]) -> str:
    lines = ["| " + " | ".join(st.HEAD) + " |", "|" + "---|" * len(st.HEAD)]
    for i, m in enumerate(rows, 1):
        v = d.cells(m)
        lines.append("| " + " | ".join([str(i), m.name, *(v[k] for _, k in st.METRICS)]) + " |")
    return "\n".join(lines)


def render_table(rows: list[d.Model], title: str) -> Table:
    tier = st.tiers(rows)
    table = Table(title=title, box=box.ROUNDED, header_style="bold #c0caf5", border_style="#3b4261")
    for c, h in enumerate(st.HEAD):
        table.add_column(h, justify="left" if c == 1 else "right", no_wrap=True)
    for i, m in enumerate(rows, 1):
        v = d.cells(m)
        color = st.MAKER_COLOR.get(m.creator)
        row = [f"[{st.MISSING}]{i}[/]", f"[{color}]{m.name}[/]" if color else m.name]
        for _, k in st.METRICS:
            style, is_best = st.cell_style(k, m.get(k), tier)
            if k == "cost" and not is_best:
                style = f"bold {style}".strip()
            text = ("★ " if is_best else "") + v[k]
            row.append(f"[{style}]{text}[/]" if style else text)
        table.add_row(*row)
    table.caption = f"[{st.BEST}]★ best[/]  [{st.GOOD}]top 25%[/]  [{st.POOR}]bottom 25%[/]  · Agentic = LiveBench Agentic Coding"
    return table


def print_table(args, rows: list[d.Model], title: str) -> None:
    if args.markdown:
        print(f"{title} (source: {d.URL})\n\n{render_markdown(rows)}")
        return
    table = render_table(rows, title)
    console = Console()
    # 좁은 창이나 파이프 출력에서도 열이 잘리지 않도록 표 본래 폭을 보장
    need = Console(width=1000).measure(table).maximum
    if console.width < need:
        console = Console(width=need)
    console.print(table)
    console.print(f"[dim]source: {d.URL}[/]")


def main() -> int:
    ap = argparse.ArgumentParser(description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--maker", choices=d.MAKERS, default="all", help="제조사 (기본 all)")
    ap.add_argument("--sort", choices=d.SORTS, default="cost", help="정렬 기준 (기본 cost=작업당 비용)")
    ap.add_argument("--top", type=int, default=20, help="점수 상위 N개만 표시 (기본 20, 0=전부)")
    ap.add_argument("--min", type=float, default=0, help="최소 Intelligence Index (기본 제한 없음)")
    ap.add_argument("--filter", help="모델명/제작사 정규식 필터 (예: 'opus|sol')")
    ap.add_argument("--refresh", action="store_true", help="캐시를 무시하고 새로 받기")
    ap.add_argument("--html", help="URL 대신 저장된 HTML 파일 사용")
    ap.add_argument("--print", action="store_true", help="TUI 대신 표만 출력")
    ap.add_argument("--markdown", action="store_true", help="마크다운 표로 출력")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

    if not (args.print or args.markdown) and sys.stdout.isatty():
        import aa_tui

        aa_tui.run(args.maker, args.sort, args.top, args.min, args.html, args.filter or "", args.refresh)
        return 0

    try:
        models, _, _ = d.load(args.html, refresh=args.refresh)
    except (OSError, ValueError) as e:
        print(f"불러오지 못했습니다: {e}", file=sys.stderr)
        return 1
    rows = d.select(models, args.maker, args.top, args.min, args.filter, args.sort)
    scope = f"top {args.top}" if args.top else "all"
    if args.min:
        scope += f" · score ≥ {args.min:g}"
    title = f"{d.MAKERS[args.maker][0]} · {scope} by score · sort: {args.sort} · {len(rows)} models"
    print_table(args, rows, title)
    return 0


if __name__ == "__main__":
    code = main()
    if opened_by_double_click() and ("--print" in sys.argv or "--markdown" in sys.argv):
        input("\nEnter를 누르면 닫힙니다...")
    sys.exit(code)
