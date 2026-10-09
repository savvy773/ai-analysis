"""Textual 기반 대화형 비교표."""
import re
from datetime import datetime

from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import DataTable, Footer, Header, Input, Static, Tab, Tabs

import aa_data as d
import aa_style as st

SORT_LABEL = {key: head for head, key in st.METRICS}


class LeaderboardApp(App):
    TITLE = "AI model comparison"
    CSS = """
    #bar { height: 2; padding: 0 1; }
    #bar Tabs { width: 1fr; }
    #search { width: 32; height: 1; border: none; padding: 0 1; }
    DataTable { height: 1fr; }
    DataTable > .datatable--header { background: $panel; color: $text; text-style: bold; }
    DataTable > .datatable--cursor { background: $primary 35%; }
    #detail { height: auto; min-height: 3; padding: 0 1; background: $boost; }
    #status { height: 1; padding: 0 1; color: $text-muted; }
    """
    BINDINGS = [
        Binding("1", "maker('all')", "All"),
        Binding("2", "maker('claude')", "Claude"),
        Binding("3", "maker('openai')", "OpenAI"),
        Binding("4", "maker('google')", "Google"),
        Binding("5", "maker('other')", "Other"),
        Binding("c", "sort('cost')", "Cost"),
        Binding("t", "sort('time')", "Time"),
        Binding("s", "sort('score')", "Score"),
        Binding("b", "sort('tb')", "Terminal"),
        Binding("g", "sort('agentic')", "Agentic"),
        Binding("plus,equals_sign", "top(5)", "+5", show=False),
        Binding("minus", "top(-5)", "-5", show=False),
        Binding("a", "toggle_all", "Top/All"),
        Binding("slash", "search", "Search"),
        Binding("m", "copy_markdown", "Copy MD"),
        Binding("w", "web", "HTML"),
        Binding("r", "refresh", "Refresh"),
        Binding("escape", "clear_search", "Clear", show=False),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, maker: str, sort: str, top: int, min_score: float, html: str | None,
                 pattern: str = "", refresh: bool = False):
        super().__init__()
        self.maker, self.sort_key, self.top, self.min_score, self.html = maker, sort, top, min_score, html
        self.reverse = False
        self.pattern = pattern
        self.initial_refresh = refresh
        self.models: list[d.Model] = []
        self.rows: list[d.Model] = []
        self.fetched_at: datetime | None = None
        self.lb_date: str | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="bar"):
            yield Tabs(*(Tab(label, id=key) for key, (label, _) in d.MAKERS.items()), active=self.maker)
            yield Input(self.pattern, placeholder="/ search (regex)", id="search")
        yield DataTable(cursor_type="row", zebra_stripes=True)
        yield Static(id="detail")
        yield Static(id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.theme = "tokyo-night"
        table = self.query_one(DataTable)
        for label in st.HEAD:
            table.add_column(label, key=label)
        table.focus()
        self.load(refresh=self.initial_refresh)

    # ---- 데이터 ----
    @work(thread=True, exclusive=True)
    def load(self, refresh: bool) -> None:
        self.call_from_thread(self.set_status, "불러오는 중..." if not refresh else "새로 받는 중...")
        try:
            models, fetched_at, lb_date = d.load(self.html, refresh=refresh)
        except Exception as e:  # 네트워크/파싱 오류는 화면에 표시하고 계속 쓴다
            self.call_from_thread(self.set_status, f"[red]불러오지 못했습니다: {e}[/]")
            return
        self.call_from_thread(self.apply_models, models, fetched_at, lb_date)

    def apply_models(self, models: list[d.Model], fetched_at: datetime, lb_date: str | None) -> None:
        self.models, self.fetched_at, self.lb_date = models, fetched_at, lb_date
        self.refresh_table()

    # ---- 화면 ----
    def refresh_table(self) -> None:
        self.rows = d.select(self.models, self.maker, self.top, self.min_score,
                             self.pattern or None, self.sort_key, self.reverse)
        tier = st.tiers(self.rows)
        table = self.query_one(DataTable)
        table.clear()
        for i, m in enumerate(self.rows, 1):
            vals = d.cells(m)
            row: list[Text] = [Text(str(i), style=st.MISSING, justify="right"),
                               Text(m.name, style=st.MAKER_COLOR.get(m.creator, ""))]
            for _, key in st.METRICS:
                style, is_best = st.cell_style(key, m.get(key), tier)
                if key == "cost" and not is_best:
                    style = f"bold {style}".strip()
                if key == self.sort_key:
                    style = f"underline {style}".strip()
                row.append(Text(("★ " if is_best else "") + vals[key], style=style, justify="right"))
            table.add_row(*row, key=str(i))
        self.update_header()
        self.set_status()
        if self.rows:
            self.show_detail(self.rows[0])
        else:
            self.query_one("#detail", Static).update("조건에 맞는 모델이 없습니다.")

    def update_header(self) -> None:
        arrow = "↑" if self.reverse else ""
        scope = f"top {self.top}" if self.top else "all"
        self.sub_title = f"{d.MAKERS[self.maker][0]} · {scope} by score · sort: {SORT_LABEL[self.sort_key]}{arrow}"

    def set_status(self, message: str | None = None) -> None:
        if message is None:
            when = self.fetched_at.astimezone().strftime("%Y-%m-%d %H:%M") if self.fetched_at else "-"
            lb = f" · LiveBench {self.lb_date}" if self.lb_date else " · LiveBench 없음"
            message = (f"{len(self.rows)} models · data {when}{lb} · "
                       f"[{st.BEST}]★ best[/] [{st.GOOD}]top 25%[/] [{st.POOR}]bottom 25%[/]")
        self.query_one("#status", Static).update(message)

    def show_detail(self, m: d.Model) -> None:
        ctx = f"{m.context // 1000:,}K" if m.context else "-"
        self.query_one("#detail", Static).update(
            f"[b]{m.name}[/]  [dim]{m.creator}[/]\n"
            f"Price in/out per 1M: {d.fmt(m.price_in, '.2f', prefix='$')} / {d.fmt(m.price_out, '.2f', prefix='$')}"
            f"  ·  Output {d.fmt(m.tps, '.0f', ' tok/s')}"
            f"  ·  First token {d.fmt(m.ttft, '.1f', 's')}"
            f"  ·  Context {ctx}"
            f"  ·  LiveBench Coding {d.fmt(m.lb_coding, '.1f')}"
        )

    @on(DataTable.RowHighlighted)
    def row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key.value and self.rows:
            self.show_detail(self.rows[int(event.row_key.value) - 1])

    @on(Tabs.TabActivated)
    def tab_activated(self, event: Tabs.TabActivated) -> None:
        if event.tab.id and event.tab.id != self.maker:
            self.maker = event.tab.id
            self.refresh_table()

    @on(Input.Changed, "#search")
    def search_changed(self, event: Input.Changed) -> None:
        try:
            re.compile(event.value)
        except re.error:
            return  # 입력 중인 미완성 정규식은 무시
        self.pattern = event.value
        if self.models:
            self.refresh_table()

    @on(Input.Submitted, "#search")
    def search_submitted(self) -> None:
        self.query_one(DataTable).focus()

    # ---- 액션 ----
    def action_maker(self, maker: str) -> None:
        self.query_one(Tabs).active = maker

    def action_sort(self, key: str) -> None:
        # 같은 키를 다시 누르면 방향 반전
        self.reverse = not self.reverse if key == self.sort_key else False
        self.sort_key = key
        self.refresh_table()

    def action_top(self, step: int) -> None:
        self.top = max(5, (self.top or 20) + step)
        self.refresh_table()

    def action_toggle_all(self) -> None:
        self.top = 0 if self.top else 20
        self.refresh_table()

    def action_search(self) -> None:
        self.query_one("#search", Input).focus()

    def action_clear_search(self) -> None:
        search = self.query_one("#search", Input)
        search.value = ""
        self.query_one(DataTable).focus()

    def action_web(self) -> None:
        import webbrowser

        import aa_web

        if not self.models or not self.fetched_at:
            return
        path = aa_web.write((d.CACHE_DIR / "report.html").resolve(), self.models, self.fetched_at, self.lb_date)
        webbrowser.open(path.as_uri())
        self.notify(f"브라우저로 열었습니다: {path}")

    def action_refresh(self) -> None:
        self.load(refresh=True)

    def action_copy_markdown(self) -> None:
        lines = ["| " + " | ".join(st.HEAD) + " |", "|" + "---|" * len(st.HEAD)]
        for i, m in enumerate(self.rows, 1):
            v = d.cells(m)
            lines.append("| " + " | ".join([str(i), m.name, *(v[k] for _, k in st.METRICS)]) + " |")
        self.copy_to_clipboard("\n".join(lines))
        self.notify(f"{len(self.rows)}개 행을 마크다운으로 복사했습니다.")


def run(maker: str, sort: str, top: int, min_score: float, html: str | None,
        pattern: str = "", refresh: bool = False) -> None:
    LeaderboardApp(maker, sort, top, min_score, html, pattern, refresh).run()
