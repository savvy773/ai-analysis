"""명령행 진입점: 옵션을 읽고 TUI · 표 · 마크다운 · HTML 중 하나로 보여 준다."""
import argparse
import sys

from rich import box
from rich.console import Console
from rich.table import Table

from . import data as d
from . import style as st

USAGE = """Artificial Analysis · LiveBench 데이터로 AI 모델의 비용·시간·코딩 성능을 비교한다.

  ai-analysis                        # 터미널 대화형 화면 (TUI)
  ai-analysis --web                  # 프로젝트 루트에 report.html을 만들고 브라우저로 연다
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


def open_report(args) -> int:
    import webbrowser
    from pathlib import Path

    from . import web

    try:
        models, fetched_at, lb_date = d.load(args.html, refresh=args.refresh)
    except (OSError, ValueError) as e:
        print(f"불러오지 못했습니다: {e}", file=sys.stderr)
        return 1
    path = web.write(Path(args.out).resolve() if args.out else web.REPORT_PATH, models, fetched_at, lb_date)
    print(f"HTML 리포트: {path}")
    if not args.out:
        webbrowser.open(path.as_uri())
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--maker", choices=d.MAKERS, default="all", help="제조사 (기본 all)")
    ap.add_argument("--sort", choices=d.SORTS, default="cost", help="정렬 기준 (기본 cost=작업당 비용)")
    ap.add_argument("--top", type=int, default=20, help="점수 상위 N개만 표시 (기본 20, 0=전부)")
    ap.add_argument("--min", type=float, default=0, help="최소 Intelligence Index (기본 제한 없음)")
    ap.add_argument("--filter", help="모델명/제작사 정규식 필터 (예: 'opus|sol')")
    ap.add_argument("--refresh", action="store_true", help="캐시를 무시하고 새로 받기")
    ap.add_argument("--from-html", dest="html", help="URL 대신 저장된 Artificial Analysis 페이지 사용")
    ap.add_argument("--web", action="store_true", help="HTML 리포트를 만들어 브라우저로 열기")
    ap.add_argument("--out", help="HTML 리포트 저장 경로 (기본 프로젝트 루트의 report.html, 지정하면 브라우저를 열지 않음)")
    ap.add_argument("--print", action="store_true", help="TUI 대신 표만 출력")
    ap.add_argument("--markdown", action="store_true", help="마크다운 표로 출력")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

    if args.web or args.out:
        return open_report(args)

    if not (args.print or args.markdown) and sys.stdout.isatty():
        from . import tui

        tui.run(args.maker, args.sort, args.top, args.min, args.html, args.filter or "", args.refresh)
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
