"""명령행 진입점: 기본은 HTML 리포트를 갱신해 브라우저로 열고, --print/--markdown이면 터미널에 표를 출력한다."""
import argparse
import re
import sys

from rich import box
from rich.console import Console
from rich.table import Table

from . import data as d
from . import style as st

USAGE = """Artificial Analysis · LiveBench 데이터로 AI 모델의 비용·시간·코딩 성능을 비교한다.

  ai-analysis                        # 루트의 report.html을 갱신하고 브라우저로 연다
  ai-analysis --maker claude --sort tb   # 브라우저에서 처음 보일 탭과 정렬
  ai-analysis --print --maker google --top 10
  ai-analysis --markdown --sort tb
"""


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
            text = v[k]
            row.append(f"[{style}]{text}[/]" if style else text)
        table.add_row(*row)
    table.caption = f"[{st.BEST}]best[/]  [{st.GOOD}]top 25%[/]  [{st.POOR}]bottom 25%[/]  · Agentic = LiveBench Agentic Coding"
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


def open_report(args) -> int:
    import webbrowser
    from pathlib import Path

    from . import web

    try:
        models, fetched_at, lb_date = d.load(args.html, refresh=args.refresh)
    except (OSError, ValueError) as e:
        print(f"불러오지 못했습니다: {e}", file=sys.stderr)
        return 1
    view = {"maker": args.maker, "sort": args.sort, "top": args.top, "q": args.filter or "",
            "min": args.min, "terminalMin": args.min_terminal}
    view["explicit"] = [key for flag, key in (("--maker", "maker"), ("--sort", "sort"),
                        ("--top", "top"), ("--filter", "q"), ("--min", "min"),
                        ("--min-terminal", "terminalMin"))
                        if any(arg == flag or arg.startswith(flag + "=") for arg in sys.argv[1:])]
    path = web.write(Path(args.out).resolve() if args.out else web.REPORT_PATH, models, fetched_at, lb_date, view)
    print(f"HTML 리포트: {path}")
    if not args.out:
        webbrowser.open(path.as_uri())
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--maker", choices=d.MAKERS, default="all", help="처음 보일 제조사 탭 (기본 all)")
    ap.add_argument("--sort", choices=d.SORTS, default="cost", help="정렬 기준 (기본 cost=작업당 비용)")
    ap.add_argument("--top", type=int, default=20, help="점수 상위 N개만 표시 (기본 20, 0=전부)")
    ap.add_argument("--min", type=float, choices=[0, 40, 50, 60], default=40.0, help="Minimum Intelligence (default 40; 0=Any)")
    ap.add_argument("--min-terminal", type=float, choices=[0, 40, 50, 60], default=0.0, help="Minimum Terminal percentage, AND with --min (default 0)")
    ap.add_argument("--filter", help="모델명/제작사 정규식 필터 (예: 'opus|sol')")
    ap.add_argument("--refresh", action="store_true", default=True, help="Fetch current source data (default)")
    ap.add_argument("--cached", dest="refresh", action="store_false", help="Use cached data while valid")
    ap.add_argument("--from-html", dest="html", help="URL 대신 저장된 Artificial Analysis 페이지 사용")
    ap.add_argument("--out", help="HTML 리포트 저장 경로 (기본 프로젝트 루트의 report.html, 지정하면 브라우저를 열지 않음)")
    ap.add_argument("--print", action="store_true", help="브라우저 대신 터미널에 표 출력")
    ap.add_argument("--markdown", action="store_true", help="마크다운 표로 출력")
    args = ap.parse_args()
    if args.top < 0:
        ap.error("Top must be non-negative; use 0 for all models.")
    if args.filter:
        try:
            re.compile(args.filter, re.I)
        except re.error as e:
            ap.error(f"검색 정규식이 올바르지 않습니다: {e}")
    if not (0 <= args.min < float("inf")) or not (0 <= args.min_terminal <= 100):
        ap.error("Minimum Intelligence must be non-negative and finite; Terminal must be between 0 and 100.")
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

    if not (args.print or args.markdown):
        return open_report(args)

    try:
        models, _, _ = d.load(args.html, refresh=args.refresh)
    except (OSError, ValueError) as e:
        print(f"불러오지 못했습니다: {e}", file=sys.stderr)
        return 1
    rows = d.select(models, args.maker, args.top, args.min, args.filter, args.sort,
                    min_terminal=args.min_terminal)
    scope = f"top {args.top}" if args.top else "all"
    if args.min:
        scope += f" · score ≥ {args.min:.1f}"
    if args.min_terminal:
        scope += f" · Terminal ≥ {args.min_terminal:.1f}%"
    title = f"{d.MAKERS[args.maker][0]} · {scope} by score · sort: {args.sort} · {len(rows)} models"
    print_table(args, rows, title)
    return 0
