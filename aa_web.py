"""모든 모델 데이터를 담은 단일 HTML 리포트. 필터·정렬·검색은 브라우저에서 처리한다."""
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import aa_data as d
import aa_style as st


def build(models: list[d.Model], fetched_at: datetime, lb_date: str | None) -> str:
    payload = {
        "models": [asdict(m) for m in models],
        "makers": {k: list(v) for k, v in d.MAKERS.items()},
        "named": sorted(d.NAMED_CREATORS),
        "colors": st.MAKER_COLOR,
        "metrics": [{"head": h, "key": k, "high": d.SORTS[k][1]} for h, k in st.METRICS],
        "fetched": fetched_at.astimezone().strftime("%Y-%m-%d %H:%M"),
        "lbDate": lb_date,
        "sources": {"aa": d.URL, "lb": d.LB_URL},
    }
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return TEMPLATE.replace("/*DATA*/null", data)


def write(path: Path, models: list[d.Model], fetched_at: datetime, lb_date: str | None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build(models, fetched_at, lb_date), encoding="utf-8")
    return path


TEMPLATE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Model Comparison</title>
<style>
:root {
  --bg: #f6f7fb; --panel: #ffffff; --text: #1f2330; --muted: #6b7280; --line: #e5e7ef;
  --accent: #4f6bed; --best: #15803d; --best-bg: #dcfce7; --good: #3f8f4f; --poor: #9ca3af;
  --row-hover: #f1f4ff; --chip: #eef1fb;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #1a1b26; --panel: #1f2335; --text: #c0caf5; --muted: #7a82a6; --line: #2f3549;
    --accent: #7aa2f7; --best: #9ece6a; --best-bg: #2a3a2a; --good: #b5e8b0; --poor: #6e7681;
    --row-hover: #262b40; --chip: #292e42;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text);
  font: 14px/1.5 system-ui, -apple-system, "Segoe UI", "Noto Sans KR", sans-serif; }
main { max-width: 1100px; margin: 0 auto; padding: 24px 16px 48px; }
h1 { font-size: 20px; margin: 0 0 4px; }
.sub { color: var(--muted); font-size: 13px; margin-bottom: 18px; }
.controls { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 14px; }
.tabs { display: flex; gap: 4px; background: var(--chip); padding: 4px; border-radius: 10px; flex-wrap: wrap; }
.tabs button { border: 0; background: transparent; color: var(--muted); padding: 6px 12px;
  border-radius: 7px; font: inherit; cursor: pointer; }
.tabs button.on { background: var(--panel); color: var(--text); font-weight: 600;
  box-shadow: 0 1px 2px rgba(0,0,0,.12); }
.tabs .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
input, select { font: inherit; color: var(--text); background: var(--panel); border: 1px solid var(--line);
  border-radius: 8px; padding: 6px 10px; }
input { flex: 1; min-width: 160px; }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
th, td { padding: 9px 12px; text-align: right; white-space: nowrap; }
th:nth-child(2), td:nth-child(2) { text-align: left; }
thead th { position: sticky; top: 0; background: var(--panel); border-bottom: 1px solid var(--line);
  font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); cursor: pointer;
  user-select: none; }
thead th.sorted { color: var(--accent); }
tbody tr { border-top: 1px solid var(--line); cursor: pointer; }
tbody tr:hover { background: var(--row-hover); }
tbody tr.sel { background: var(--row-hover); }
td.rank { color: var(--muted); width: 36px; }
td.model { font-weight: 500; }
td.cost { font-weight: 600; }
td.best { color: var(--best); font-weight: 700; }
td.best span { background: var(--best-bg); padding: 2px 6px; border-radius: 6px; }
td.good { color: var(--good); }
td.poor, td.none { color: var(--poor); }
.legend { display: flex; flex-wrap: wrap; gap: 14px; color: var(--muted); font-size: 12px; margin-top: 10px; }
.legend b.best { color: var(--best); } .legend b.good { color: var(--good); } .legend b.poor { color: var(--poor); }
.detail { margin-top: 14px; background: var(--panel); border: 1px solid var(--line); border-radius: 12px;
  padding: 14px 16px; display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
.detail .name { grid-column: 1 / -1; font-weight: 600; }
.detail .k { color: var(--muted); font-size: 12px; } .detail .v { font-size: 15px; font-weight: 600; }
.empty { padding: 24px; text-align: center; color: var(--muted); }
a { color: var(--accent); }
</style>
</head>
<body>
<main>
  <h1>AI Model Comparison</h1>
  <div class="sub" id="sub"></div>
  <div class="controls">
    <div class="tabs" id="tabs"></div>
    <select id="top" aria-label="표시 개수">
      <option value="10">Top 10</option><option value="20" selected>Top 20</option>
      <option value="40">Top 40</option><option value="0">All</option>
    </select>
    <input id="q" type="search" placeholder="모델 검색 (예: opus|sol)">
  </div>
  <div class="card"><table><thead><tr id="head"></tr></thead><tbody id="body"></tbody></table></div>
  <div class="legend">
    <span><b class="best">★</b> 열 최고 값</span><span><b class="good">●</b> 상위 25%</span>
    <span><b class="poor">●</b> 하위 25%</span><span>열 제목을 누르면 정렬 · 행을 누르면 상세</span>
  </div>
  <div class="detail" id="detail"></div>
</main>
<script>
const D = /*DATA*/null;
const state = { maker: "all", top: 20, q: "", sort: "cost", desc: false, sel: null };
const $ = (id) => document.getElementById(id);
const metric = (k) => D.metrics.find((m) => m.key === k);
const fmt = {
  cost: (v) => "$" + v.toFixed(2), time: (v) => Math.round(v) + "s", score: (v) => v.toFixed(1),
  tb: (v) => (v * 100).toFixed(1) + "%", agentic: (v) => v.toFixed(1),
};

function matchesMaker(m) {
  if (state.maker === "all") return true;
  if (state.maker === "other") return !D.named.includes(m.creator);
  return m.creator === D.makers[state.maker][1];
}

function rows() {
  let rx = null;
  try { rx = state.q ? new RegExp(state.q, "i") : null; } catch { rx = null; }
  let list = D.models.filter((m) => matchesMaker(m) && (!rx || rx.test(m.name + " " + m.creator)));
  list.sort((a, b) => b.score - a.score);
  if (state.top) list = list.slice(0, state.top);
  const { high } = metric(state.sort);
  const dir = (high ? -1 : 1) * (state.desc ? -1 : 1);
  const has = list.filter((m) => m[state.sort] != null).sort((a, b) => (a[state.sort] - b[state.sort]) * dir);
  return has.concat(list.filter((m) => m[state.sort] == null));
}

function tiers(list) {
  const out = {};
  for (const { key, high } of D.metrics) {
    const vals = list.map((m) => m[key]).filter((v) => v != null).sort((a, b) => high ? b - a : a - b);
    if (!vals.length) continue;
    const n = vals.length, q = Math.floor(n / 4);
    out[key] = { best: vals[0], good: vals[Math.max(0, q - 1)], poor: vals[Math.min(n - 1, n - q)], high };
  }
  return out;
}

function cls(key, v, t) {
  if (v == null) return "none";
  const x = t[key]; if (!x) return "";
  const better = (a, b) => x.high ? a >= b : a <= b;
  if (v === x.best) return "best";
  if (better(v, x.good)) return "good";
  if (!better(v, x.poor) || v === x.poor) return "poor";
  return "";
}

function renderTabs() {
  $("tabs").innerHTML = Object.entries(D.makers).map(([k, [label, creator]]) => {
    const dot = creator && D.colors[creator] ? `<span class="dot" style="background:${D.colors[creator]}"></span>` : "";
    return `<button data-k="${k}" class="${k === state.maker ? "on" : ""}">${dot}${label}</button>`;
  }).join("");
}

function render() {
  const list = rows(), t = tiers(list);
  $("head").innerHTML = `<th>#</th><th>Model</th>` + D.metrics.map(({ head, key }) =>
    `<th data-k="${key}" class="${key === state.sort ? "sorted" : ""}">${head}${key === state.sort ? (state.desc ? " ↑" : " ↓") : ""}</th>`).join("");
  $("body").innerHTML = list.length ? list.map((m, i) => {
    const color = D.colors[m.creator] || "inherit";
    const cells = D.metrics.map(({ key }) => {
      const v = m[key], c = cls(key, v, t);
      const txt = v == null ? "–" : fmt[key](v);
      return `<td class="${key} ${c}">${c === "best" ? `<span>★ ${txt}</span>` : txt}</td>`;
    }).join("");
    return `<tr data-i="${D.models.indexOf(m)}" class="${state.sel === D.models.indexOf(m) ? "sel" : ""}">` +
      `<td class="rank">${i + 1}</td><td class="model" style="color:${color}">${m.name}</td>${cells}</tr>`;
  }).join("") : `<tr><td colspan="7" class="empty">조건에 맞는 모델이 없습니다.</td></tr>`;
  renderDetail(state.sel != null ? D.models[state.sel] : list[0]);
}

function renderDetail(m) {
  if (!m) { $("detail").innerHTML = ""; return; }
  const f = (v, s) => v == null ? "–" : s(v);
  const items = [
    ["Input / 1M", f(m.price_in, (v) => "$" + v.toFixed(2))], ["Output / 1M", f(m.price_out, (v) => "$" + v.toFixed(2))],
    ["Output speed", f(m.tps, (v) => Math.round(v) + " tok/s")], ["First token", f(m.ttft, (v) => v.toFixed(1) + "s")],
    ["Context", f(m.context, (v) => (v / 1000).toLocaleString() + "K")], ["LiveBench Coding", f(m.lb_coding, (v) => v.toFixed(1))],
  ];
  $("detail").innerHTML = `<div class="name" style="color:${D.colors[m.creator] || "inherit"}">${m.name}
    <span style="color:var(--muted);font-weight:400"> · ${m.creator}</span></div>` +
    items.map(([k, v]) => `<div><div class="k">${k}</div><div class="v">${v}</div></div>`).join("");
}

$("tabs").addEventListener("click", (e) => {
  const b = e.target.closest("button"); if (!b) return;
  state.maker = b.dataset.k; state.sel = null; renderTabs(); render();
});
$("head").addEventListener("click", (e) => {
  const th = e.target.closest("th[data-k]"); if (!th) return;
  const k = th.dataset.k;
  state.desc = state.sort === k ? !state.desc : false; state.sort = k; render();
});
$("body").addEventListener("click", (e) => {
  const tr = e.target.closest("tr[data-i]"); if (!tr) return;
  state.sel = +tr.dataset.i; render();
});
$("top").addEventListener("change", (e) => { state.top = +e.target.value; render(); });
$("q").addEventListener("input", (e) => { state.q = e.target.value; render(); });

$("sub").innerHTML = `데이터 ${D.fetched} · <a href="${D.sources.aa}">Artificial Analysis</a>` +
  (D.lbDate ? ` · <a href="${D.sources.lb}">LiveBench</a> ${D.lbDate} (Agentic = Agentic Coding)` : " · LiveBench 없음");
renderTabs(); render();
</script>
</body>
</html>
"""
