#!/usr/bin/env python3
# 의존성(rich)이 없으면 이 프로젝트의 uv 환경으로 다시 실행한다 (아래 try/except ImportError)
USAGE = """Artificial Analysis 리더보드에서 기준 점수 이상 모델의 가성비 표를 출력한다.

사용 예 (Windows는 더블클릭도 가능):
  ./aa_value.py                    # Intelligence Index 50점 이상, 작업당 비용 순
  ./aa_value.py --min 45 --sort time
  ./aa_value.py --filter "opus|sonnet|sol"
  ./aa_value.py --html saved.html  # 저장해 둔 페이지로 오프라인 실행
"""
import argparse
import json
import os
import re
import sys
import urllib.request


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

URL = os.environ.get("AA_URL", "https://artificialanalysis.ai/leaderboards/models")

SORTS = {
    "score": lambda r: -r["score"],
    "time": lambda r: r["time"] if r["time"] is not None else float("inf"),
    "cost": lambda r: r["cost"],
    "tb": lambda r: -(r["tb"] or 0),
}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse(html: str) -> list[dict]:
    # 페이지에 내장된 Next.js 데이터: {\"slug\":...} 형태의 평평한 객체들
    models: dict[str, dict] = {}
    for raw in re.findall(r'\{\\"slug\\":[^{}]*\}', html):
        try:
            obj = json.loads(raw.replace('\\"', '"'))
        except json.JSONDecodeError:
            continue
        models.setdefault(obj["slug"], {}).update(obj)
    return [m for m in models.values() if m.get("intelligenceIndex") is not None]


def build_rows(models: list[dict], min_score: float, pattern: str | None) -> list[dict]:
    rx = re.compile(pattern, re.I) if pattern else None
    rows = []
    for m in models:
        score, cost = m["intelligenceIndex"], m.get("intelligenceIndexCostPerTask")
        name = m.get("shortName") or m.get("name") or m["slug"]
        if score < min_score or not cost:
            continue
        if rx and not rx.search(f'{name} {m.get("modelCreatorName", "")}'):
            continue
        rows.append({
            "name": name,
            "creator": m.get("modelCreatorName", ""),
            "score": score,
            "cost": cost,
            "tps": m.get("medianOutputTokensPerSecond"),
            "time": m.get("medianEndToEndResponseTimeSeconds"),
            "tb": m.get("terminalBench40"),
        })
    return rows


def fmt(v, spec: str, suffix: str = "") -> str:
    return "-" if v is None else f"{v:{spec}}{suffix}"


HEAD = ["#", "Model", "Cost", "Time", "Score", "Terminal"]
# 모델명 접두어 → 색 (그 외 모델은 기본색)
MODEL_STYLE = {"gpt": "#10a37f", "claude": "#d97757"}
# 열 인덱스 → (값 키, 높을수록 좋은가): 열마다 최고 값을 강조
BEST = {2: ("cost", False), 3: ("time", False), 4: ("score", True), 5: ("tb", True)}


def cells(i: int, r: dict) -> list[str]:
    return [
        str(i), r["name"].replace(" with fallback", ""), f'${r["cost"]:.2f}',
        fmt(r["time"], ".0f", "s"), f'{r["score"]:.1f}',
        fmt(r["tb"] and r["tb"] * 100, ".1f", "%"),
    ]


def model_style(name: str) -> str | None:
    return next((s for k, s in MODEL_STYLE.items() if name.lower().startswith(k)), None)


def render_markdown(rows: list[dict]) -> str:
    lines = ["| " + " | ".join(HEAD) + " |", "|" + "---|" * len(HEAD)]
    return "\n".join(lines + ["| " + " | ".join(cells(i, r)) + " |" for i, r in enumerate(rows, 1)])


def render_table(rows: list[dict], title: str) -> Table:
    best = {}
    for col, (key, high) in BEST.items():
        vals = [r[key] for r in rows if r[key] is not None]
        if vals:
            best[col] = max(vals) if high else min(vals)

    table = Table(title=title, box=box.ROUNDED, header_style="bold cyan", row_styles=["", "on grey11"])
    for c, h in enumerate(HEAD):
        table.add_column(h, justify="left" if c == 1 else "right", no_wrap=True,
                         style="bold" if c == 2 else None)  # 작업당 비용 강조
    for i, r in enumerate(rows, 1):
        row = cells(i, r)
        if style := model_style(row[1]):
            row[1] = f"[{style}]{row[1]}[/]"
        for col, (key, _) in BEST.items():
            if col in best and r[key] == best[col]:
                row[col] = f"[bold green]★ {row[col]}[/]"
        table.add_row(*row)
    table.caption = "★ best per column"
    return table


def main() -> int:
    ap = argparse.ArgumentParser(description=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min", type=float, default=50, help="최소 Intelligence Index (기본 50)")
    ap.add_argument("--sort", choices=SORTS, default="cost", help="정렬 기준 (기본 cost=작업당 비용)")
    ap.add_argument("--filter", help="모델명/제작사 정규식 필터 (예: 'opus|sol')")
    ap.add_argument("--top", type=int, default=0, help="상위 N개만 출력")
    ap.add_argument("--html", help="URL 대신 저장된 HTML 파일 사용")
    ap.add_argument("--markdown", action="store_true", help="컬러 표 대신 마크다운 표로 출력")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

    try:
        html = open(args.html, encoding="utf-8").read() if args.html else fetch(URL)
    except OSError as e:
        print(f"페이지를 가져오지 못했습니다: {e}", file=sys.stderr)
        return 1

    models = parse(html)
    if not models:
        print("모델 데이터를 찾지 못했습니다. 페이지 구조가 바뀌었을 수 있습니다.", file=sys.stderr)
        return 1

    rows = sorted(build_rows(models, args.min, args.filter), key=SORTS[args.sort])
    if args.top:
        rows = rows[: args.top]
    title = f"Intelligence Index ≥ {args.min:g} · sort: {args.sort} · {len(rows)} models"
    if args.markdown:
        print(f"{title} (source: {URL})\n\n{render_markdown(rows)}")
    else:
        table = render_table(rows, title)
        console = Console()
        # 좁은 창이나 파이프 출력에서도 열이 잘리지 않도록 표 본래 폭을 보장
        need = Console(width=1000).measure(table).maximum
        if console.width < need:
            console = Console(width=need)
        console.print(table)
        console.print(f"[dim]source: {URL}[/]")
    return 0


if __name__ == "__main__":
    code = main()
    if opened_by_double_click():
        input("\nEnter를 누르면 닫힙니다...")
    sys.exit(code)
