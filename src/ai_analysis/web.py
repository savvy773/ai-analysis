"""모든 모델 데이터를 담은 단일 HTML 리포트. 필터·정렬·검색은 브라우저에서 처리한다."""
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from . import data as d
from . import style as st


# 기본 저장 위치: 프로젝트 루트
REPORT_PATH = d.PROJECT_ROOT / "report.html"


def build(models: list[d.Model], fetched_at: datetime, lb_date: str | None, view: dict | None = None) -> str:
    payload = {
        "view": view or {},
        "models": [asdict(m) for m in models],
        "makers": {k: list(v) for k, v in d.MAKERS.items()},
        "named": sorted(d.NAMED_CREATORS),
        "colors": st.MAKER_COLOR,
        "metrics": [{"head": h, "key": k, "high": d.SORTS[k][1], "help": st.METRIC_HELP[k]} for h, k in st.METRICS],
        "fetched": fetched_at.astimezone().strftime("%y%m%d %H:%M"),
        "lbDate": lb_date,
        "sources": {"aa": d.URL, "lb": d.LB_URL},
    }
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return TEMPLATE.replace("/*DATA*/null", data)


def write(path: Path, models: list[d.Model], fetched_at: datetime, lb_date: str | None,
          view: dict | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build(models, fetched_at, lb_date, view), encoding="utf-8")
    return path


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Model Comparison</title>
<style>
:root {
  color-scheme: light dark;
  --bg: #f6f7fb; --panel: #ffffff; --text: #1f2330; --muted: #6b7280; --line: #e5e7ef;
  --accent: #4f6bed; --best: #15803d; --best-bg: #dcfce7; --good: #3f8f4f; --poor: #9ca3af;
  --row-hover: #f1f4ff; --chip: #eef1fb;
  --favorite-bg: #fff8e4; --favorite-hover: #fff0c2; --favorite-accent: #b87b12;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #1a1b26; --panel: #1f2335; --text: #c0caf5; --muted: #7a82a6; --line: #2f3549;
    --accent: #7aa2f7; --best: #9ece6a; --best-bg: #2a3a2a; --good: #b5e8b0; --poor: #6e7681;
    --row-hover: #262b40; --chip: #292e42;
    --favorite-bg: #353024; --favorite-hover: #453b26; --favorite-accent: #e5b85a;
  }
}
* { box-sizing: border-box; scrollbar-width: thin; scrollbar-color: var(--line) transparent; }
html { scrollbar-gutter: stable; }
main { overflow-anchor: none; }
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--line); border: 2px solid var(--panel); border-radius: 8px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }
button, input, select { accent-color: var(--accent); }
button:focus-visible, input:focus-visible, select:focus-visible, tr:focus-visible {
  outline: 2px solid var(--accent); outline-offset: 2px; }
body { margin: 0; background: var(--bg); color: var(--text);
  font: 13px/1.45 system-ui, -apple-system, "Segoe UI", "Noto Sans KR", sans-serif; }
main { max-width: 1440px; margin: 0 auto; padding: 16px 20px 24px; }
h1 { font-size: 12px; font-weight: 600; line-height: 1.2; margin: 0; white-space: nowrap; }
.report-header { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 6px; }
.header-actions { display: flex; align-items: center; gap: 6px; margin-left: auto; font-size: 12px; }
.header-actions #q { flex: 0 1 200px; width: 200px; max-width: 200px; min-width: 120px; }
.header-actions #q, .header-actions .quiet-button { height: 24px; padding: 1px 8px; border-radius: 6px; }
.report-footer { margin-top: 6px; padding-top: 3px; border-top: 1px solid var(--line); }
.report-footer .sub { margin: 0; text-align: center; font-size: 11px; line-height: 1.3; }
.sub { color: var(--muted); font-size: 12px; margin: 0 0 12px; }
.toolbar-top { display: flex; flex-wrap: wrap; gap: 6px; align-items: flex-end; margin-bottom: 6px; font-size: 12px; }
.report-header .tabs { font-size: 12px; padding: 1px; gap: 1px; border-radius: 6px; }
.report-header .tabs button { padding: 2px 7px; border-radius: 4px; }
.report-header .tabs .dot { width: 6px; height: 6px; margin-right: 4px; }
.toolbar-top select { height: 24px; box-sizing: border-box; padding: 1px 6px; border-radius: 6px; }
.toolbar-top .sort-settings { margin-left: 12px; padding-left: 12px; border-left: 1px solid var(--line); min-width: 0; flex-wrap: nowrap; height: 26px; }
.controls { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin-bottom: 10px; }
.tabs { display: flex; gap: 2px; background: var(--chip); padding: 3px; border-radius: 8px; flex-wrap: wrap; }
.tabs button { border: 0; background: transparent; color: var(--muted); padding: 5px 8px;
  border-radius: 7px; font: inherit; font-weight: 600; cursor: pointer; }
.tabs button.on { background: var(--panel); color: var(--text); font-weight: 600;
  box-shadow: 0 1px 2px rgba(0,0,0,.12); }
.tabs .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
input, select { font: inherit; color: var(--text); background: var(--panel); border: 1px solid var(--line);
  border-radius: 8px; padding: 6px 10px; }
input { flex: 1; min-width: 160px; }
#q { flex: 0 1 180px; width: 180px; min-width: 140px; }
.filter-controls { display: flex; flex-wrap: wrap; align-items: flex-end; gap: 10px; }
.score-filter { display: flex; flex-direction: column; align-items: stretch; gap: 4px; width: 80px; }
.score-filter > label { color: var(--muted); font-size: 11px; line-height: 14px; text-align: center; white-space: nowrap; }
.toolbar-top .score-filter select { width: 80px; min-width: 80px; height: 26px; text-align: center; padding: 2px 6px; }
.toolbar-top #reset-scores { width: 24px; height: 24px; padding: 0; border-radius: 5px; font-size: 16px; line-height: 1; }
.quiet-button { border: 1px solid var(--line); border-radius: 8px; padding: 6px 10px;
  font: inherit; color: var(--text); background: var(--panel); cursor: pointer; }
.quiet-button:hover { background: var(--row-hover); border-color: var(--accent); }
.quiet-button:disabled { opacity: .45; cursor: default; }
.reset-button { color: #986000; background: #fff3dc; border-color: #d8ae68; }
.reset-button:hover { background: #ffe9bf; border-color: #b17a26; }
.settings-toast { position: fixed; bottom: 16px; right: 16px; z-index: 5; padding: 9px 14px;
  border: 1px solid var(--line); border-radius: 8px; color: var(--text); background: var(--panel); }
.settings-toast:empty { display: none; }
.quiet-button.feedback-success { color: var(--best); background: var(--best-bg);
  border-color: var(--best); box-shadow: 0 0 0 3px color-mix(in srgb, var(--best) 18%, transparent);
  animation: settings-feedback .22s ease-out; }
.quiet-button.feedback-error, .settings-toast.feedback-error { border-color: #e57373; color: #c44343; }
@keyframes settings-feedback { from { transform: scale(.94); } to { transform: scale(1); } }
@media (prefers-reduced-motion: reduce) { .quiet-button.feedback-success { animation: none; } }
@media (prefers-color-scheme: dark) {
  .reset-button { color: #efc17b; background: #3b3025; border-color: #705537; }
  .reset-button:hover { background: #4a3928; border-color: #b48a54; }
}
.sort-settings { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.toggle { display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; cursor: pointer; }
.toggle input { appearance: none; flex: none; min-width: 0; width: 28px; height: 17px; margin: 0;
  padding: 2px; border-radius: 12px; background: var(--line); cursor: pointer; }
.toggle input::before { content: ""; display: block; width: 11px; height: 11px; border-radius: 50%;
  background: var(--muted); transition: transform .15s; }
.toggle input:checked { background: var(--accent); }
.toggle input:checked::before { transform: translateX(10px); background: var(--panel); }
#sort-order { color: var(--accent); flex: 0 1 auto; max-width: 240px; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.compare-heading { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.result-summary { display: flex; align-items: center; gap: 8px; min-width: 170px; flex: 0 1 auto; margin-left: auto; height: 26px; color: var(--muted); font-size: 11px; white-space: nowrap; }
#result-count { flex-shrink: 0; }
.compare-shortcuts { display: flex; align-items: center; gap: 6px; flex-shrink: 0; height: 26px; }
.clear-separator { color: var(--muted); }
.compare-shortcuts .quiet-button { padding: 2px 8px; font-size: 11px; }
#jump-compare { width: 84px; color: var(--accent); font-variant-numeric: tabular-nums; }
.comparison .sub { margin: 4px 0 8px; }
.compare-check, .favorite-check { min-width: 0; width: 16px; height: 16px; margin: 0; vertical-align: middle; cursor: pointer; }
.favorite-check { accent-color: #c99223; }
.leaderboard th.favorite-heading { text-transform: none; }
.compare-check:disabled { opacity: .3; cursor: default; }
.leaderboard { height: 562px; overflow: auto; scrollbar-gutter: stable; overflow-anchor: none; }
.leaderboard table { table-layout: fixed; min-width: 828px; }
.leaderboard th { height: 30px; padding: 4px 10px; line-height: 18px; }
.leaderboard td { height: 26px; padding: 3px 10px; line-height: 18px; }
.leaderboard thead th { z-index: 1; }
.leaderboard th:first-child { width: 38px; }
.leaderboard th:nth-child(2) { width: 30%; }
.leaderboard th:nth-last-child(2) { width: 32px; }
.leaderboard th:last-child { width: 44px; }
.leaderboard th:nth-last-child(-n+2), .leaderboard td:nth-last-child(-n+2) { text-align: center; padding-left: 4px; padding-right: 4px; }
.leaderboard td.model { overflow: hidden; text-overflow: ellipsis; }
.sort-indicator { display: inline-block; min-width: 28px; text-align: left; font-size: 10px; }
.sort-button { border: 0; padding: 0; background: none; color: inherit; font: inherit; cursor: pointer; }
#q[aria-invalid="true"] { border-color: #e57373; }
.rank-middle-good { color: #245b9c; background: #eaf2ff; }
.rank-middle-poor { color: #80651d; background: #fff9e8; }
.rank-last { color: #a14e12; background: #fff0df; }
@media (prefers-color-scheme: dark) {
  .rank-middle-good { color: #a6c8ff; background: #253955; }
  .rank-middle-poor { color: #dcc787; background: #383322; }
  .rank-last { color: #efb176; background: #3e3025; }
}
.winner { color: var(--best); background: var(--best-bg); font-weight: 600; }
.badge { display: inline-block; font-size: 10px; margin-left: 6px; padding: 1px 5px;
  border: 1px solid currentColor; border-radius: 4px; }
#vs-result th { text-transform: none; letter-spacing: 0; white-space: normal; min-width: 120px; cursor: default; }
#vs-result tbody tr { cursor: default; }
#vs-result { height: 244px; overflow: auto; scrollbar-gutter: stable; overflow-anchor: none; }
#vs-result table { table-layout: fixed; min-width: 600px; }
#vs-result th { height: 58px; overflow: hidden; text-overflow: ellipsis; }
#vs-result th:first-child { width: 90px; }
#vs-result .empty { height: 100%; display: grid; place-items: center; }
#vs-result td:not(:first-child), #vs-result th:not(:first-child) { text-align: right; }
@media (max-width: 600px) {
  main { padding: 12px 10px 20px; }
  .tabs { width: 100%; }
  .tabs button { flex: 1; padding: 6px 8px; }
  .header-actions { width: 100%; }
  .header-actions #q { flex: 1; width: auto; }
  .toolbar-top .sort-settings { margin-left: 0; padding-left: 0; border-left: 0; }
  th, td { padding: 6px 8px; }
}
.comparison { margin-top: 16px; }
.recommendations { margin-top: 16px; }
.recommendations h2 { font-size: 15px; margin: 0; }
.recommendation-heading { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 6px; }
.weight-control { display: inline-flex; align-items: center; gap: 8px; }
.weight-control input { flex: none; width: 120px; min-width: 0; padding: 0; }
#weight-label { min-width: 132px; font-size: 12px; color: var(--muted); font-variant-numeric: tabular-nums; }
#recommendations-result { height: 218px; overflow: auto; scrollbar-gutter: stable; }
#recommendations-result table { table-layout: fixed; min-width: 590px; }
#recommendations-result th:first-child { width: 40px; }
#recommendations-result th:nth-child(2) { width: 44%; }
#recommendations-result td.model { overflow: hidden; text-overflow: ellipsis; }
#recommendations-result th, #recommendations-result tr { cursor: default; }
.comparison h2 { font-size: 15px; margin: 0 0 8px; }
.comparison select { min-width: 0; max-width: 100%; }
.comparison label { display: flex; align-items: center; gap: 8px; }
.comparison th:first-child, .comparison td:first-child { text-align: left; }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
th, td { padding: 6px 10px; text-align: right; white-space: nowrap; }
th + th, td + td { border-left: 1px solid var(--line); }
th:nth-child(2), td:nth-child(2) { text-align: left; }
thead th { position: sticky; top: 0; background: var(--panel); border-bottom: 1px solid var(--line);
  font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); cursor: pointer;
  user-select: none; }
thead th.sorted { color: var(--accent); }
tbody tr { border-top: 1px solid var(--line); cursor: pointer; }
tbody tr:hover { background: var(--row-hover); }
tbody tr.sel { background: var(--row-hover); }
.leaderboard tr.favorite { background: var(--favorite-bg); }
.leaderboard tr.favorite:hover, .leaderboard tr.favorite.sel { background: var(--favorite-hover); }
.leaderboard tr.favorite td:first-child { box-shadow: inset 3px 0 var(--favorite-accent); }
.leaderboard tr.favorite td.model { font-weight: 700; }
td.rank { color: var(--muted); width: 36px; }
td.model { font-weight: 500; }
td.cost { font-weight: 600; }
td.best { color: var(--best); font-weight: 700; }
td.best span { padding: 0; }
td.good { color: var(--good); }
td.poor, td.none { color: var(--poor); }
.legend { display: flex; flex-wrap: wrap; gap: 10px; color: var(--muted); font-size: 11px; margin-top: 7px; }
.legend b.best { color: var(--best); } .legend b.good { color: var(--good); } .legend b.poor { color: var(--poor); }
.detail { margin-top: 10px; background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
  padding: 10px 12px; display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 6px 12px; }
.detail .name { grid-column: 1 / -1; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.detail .k, .detail .v { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
@media (max-width: 800px) { .detail { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 480px) { .detail { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.detail .k { color: var(--muted); font-size: 11px; } .detail .v { font-size: 13px; font-weight: 600; }
.empty { padding: 24px; text-align: center; color: var(--muted); }
a { color: var(--accent); }
</style>
</head>
<body>
<main>
  <header class="report-header">
    <h1>AI Comparison</h1>
    <div class="tabs" id="tabs"></div>
    <div class="header-actions">
    <input id="q" type="search" aria-label="Search models" placeholder="Search models" title="Search model or maker; regex allowed.">
    <button class="quiet-button" id="save-defaults" type="button" aria-label="Save current settings and favorites as defaults" title="Save settings and favorites.">Save</button>
    <button class="quiet-button reset-button" id="reset-filters" type="button" aria-label="Restore defaults" title="Restore saved defaults; clear VS.">Reset</button>
    </div>
  </header>
  <div class="toolbar-top">
    <div class="filter-controls">
    <div class="score-filter">
      <label for="top" title="Top models by Intelligence.">Top</label>
      <select id="top" aria-label="Top models by Intelligence" title="Top models by Intelligence.">
        <option value="20" selected>20</option><option value="30">30</option>
        <option value="40">40</option><option value="50">50</option>
      </select>
    </div>
    <div class="score-filter">
      <label for="min-score" title="Minimum Intelligence; Any = no limit.">Intelligence</label>
      <select id="min-score" title="Minimum Intelligence; Any = no limit."></select>
    </div>
    <div class="score-filter">
      <label for="min-terminal" title="Minimum Terminal (%); Any = no limit.">Terminal</label>
      <select id="min-terminal" title="Minimum Terminal (%); Any = no limit."></select>
    </div>
    <button class="quiet-button reset-button" id="reset-scores" type="button" aria-label="Reset Intelligence and Terminal to Any" title="Set Intelligence and Terminal to Any.">↺</button>
    </div>
    <div class="sort-settings">
      <label class="toggle" title="Sort by multiple columns; ties use displayed values."><input id="multi-sort" type="checkbox" role="switch">Multi-sort</label>
    </div>
    <div class="result-summary"><span id="result-count" role="status"></span><span id="sort-order"></span></div>
    <div class="compare-shortcuts"><button class="quiet-button" id="jump-compare" type="button" title="Jump to comparison.">VS 0/4 ↓</button>
      <button class="quiet-button" id="clear-favorites" type="button" title="Clear favorites.">Clear fav</button>
      <span class="clear-separator" aria-hidden="true">|</span>
      <button class="quiet-button" id="clear-compare-top" type="button" title="Clear VS selections.">Clear</button></div></div>
  <div class="card leaderboard" tabindex="0" role="region" aria-label="Model leaderboard"><table><thead><tr id="head"></tr></thead><tbody id="body"></tbody></table></div>
  <div class="legend">
    <span><b class="best">Best in view</b></span><span><b class="good">●</b> Top 30%</span>
    <span><b class="poor">●</b> Bottom 30%</span><span>Click headers to sort · Check up to 4 models to compare</span>
  </div>
  <div class="detail" id="detail"></div>
  <section class="comparison" aria-labelledby="vs-title" tabindex="-1">
    <div class="compare-heading"><h2 id="vs-title">Compare <span id="compare-count">0 / 4</span></h2>
      <button id="clear-compare" class="quiet-button" type="button">Clear</button></div>
    <p class="sub">Compare 2–4 models. Green: first · Blue / yellow: middle · Amber: last. Ties share a color.</p>
    <div class="card" id="vs-result" aria-live="polite"></div>
  </section>
  <section class="recommendations" aria-labelledby="recommendations-title">
    <div class="recommendation-heading">
      <h2 id="recommendations-title">Recommended</h2>
      <label class="weight-control" for="cost-weight"><span id="weight-label"></span>
        <input id="cost-weight" type="range" min="0" max="100" step="10" value="60" aria-label="Cost weight as a percentage">
      </label>
    </div>
    <p class="sub" id="recommendation-summary"></p>
    <div class="card" id="recommendations-result" aria-live="polite"></div>
  </section>
  <footer class="report-footer"><div class="sub" id="sub"></div></footer>
</main>
<div id="settings-status" class="settings-toast" role="status"></div>
<script>
const D = /*DATA*/null;
const state = { maker: "all", top: 20, q: "", min: 40, terminalMin: 0, sort: "cost", desc: false, sel: null, ...D.view, compare: [], multi: false, sortKeys: [], costWeight: 60 };
const $ = (id) => document.getElementById(id);
const metric = (k) => D.metrics.find((m) => m.key === k);
const modelIndexes = new Map(D.models.map((model, index) => [model, index]));
const STORAGE_KEY = "ai-analysis.ui.v1";
const DEFAULT_KEY = "ai-analysis.defaults.v1";
const FAVORITES_KEY = "ai-analysis.favorites.v1";
const modelId = (model) => JSON.stringify([model.creator, model.name]);
const favorites = new Set();
try {
  const saved = JSON.parse(localStorage.getItem(FAVORITES_KEY));
  if (Array.isArray(saved)) for (const id of saved) if (typeof id === "string") favorites.add(id);
} catch { /* Favorites still work when storage is unavailable or invalid. */ }
function saveFavorites() {
  try { localStorage.setItem(FAVORITES_KEY, JSON.stringify([...favorites])); }
  catch { /* Keep the current selection when storage is unavailable. */ }
}
function updateFavoriteRows() {
  for (const input of document.querySelectorAll("#body [data-favorite]")) {
    const model = D.models[+input.dataset.favorite];
    input.checked = favorites.has(modelId(model));
    input.closest("tr").classList.toggle("favorite", input.checked);
  }
  $("clear-favorites").disabled = favorites.size === 0;
}
function toggleFavorite(index, checked) {
  const model = D.models[index];
  if (!model) return;
  const id = modelId(model);
  if (checked) favorites.add(id); else favorites.delete(id);
  saveFavorites();
}
const MINIMUM_VALUES = [0, 40, 45, 50, 55, 60];
const normalizeMinimum = (value) => MINIMUM_VALUES.filter((v) => v <= value).at(-1) ?? 0;
function restoreSettings(source, useExplicit = true) {
  try {
    const saved = JSON.parse(source === undefined ? localStorage.getItem(STORAGE_KEY) || localStorage.getItem(DEFAULT_KEY) : source);
    if (saved && typeof saved === "object") {
      if (Object.hasOwn(D.makers, saved.maker)) state.maker = saved.maker;
      if (Number.isInteger(saved.top) && saved.top >= 0) state.top = saved.top;
      if (typeof saved.q === "string") state.q = saved.q;
      if (Number.isFinite(saved.costWeight) && saved.costWeight >= 0 && saved.costWeight <= 100) state.costWeight = saved.costWeight;
      for (const [key, max] of [["min", Infinity], ["terminalMin", 100]]) {
        if (Number.isFinite(saved[key]) && saved[key] >= 0 && saved[key] <= max) state[key] = saved[key];
      }
      if (metric(saved.sort)) state.sort = saved.sort;
      state.desc = saved.desc === true; state.multi = saved.multi === true;
      if (Array.isArray(saved.sortKeys)) {
        state.sortKeys = saved.sortKeys.filter((s, i, all) => s && metric(s.key) && all.findIndex((x) => x?.key === s.key) === i)
          .map((s) => ({ key: s.key, desc: s.desc === true }));
      }
      if (Array.isArray(saved.compare)) {
        state.compare = [...new Set(saved.compare.map((id) => D.models.findIndex((m) => JSON.stringify([m.creator, m.name]) === id)))]
          .filter((i) => i >= 0).slice(0, 4);
      }
    }
  } catch { /* Storage may be unavailable or contain invalid JSON. */ }
  const explicit = useExplicit ? D.view.explicit || [] : [];
  for (const key of explicit) if (["maker", "sort", "top", "q", "min", "terminalMin"].includes(key)) state[key] = D.view[key];
  state.min = normalizeMinimum(state.min); state.terminalMin = normalizeMinimum(state.terminalMin);
  if (explicit.includes("sort")) state.desc = false;
  if (!state.sortKeys.length || explicit.includes("sort")) state.sortKeys = [{ key: state.sort, desc: state.desc }];
  if (state.multi) { state.sort = state.sortKeys[0].key; state.desc = state.sortKeys[0].desc; }
}
function settingsSnapshot() {
  return { maker: state.maker, top: state.top, q: state.q,
      min: state.min, terminalMin: state.terminalMin, sort: state.sort, desc: state.desc,
      multi: state.multi, sortKeys: state.sortKeys, costWeight: state.costWeight,
      compare: state.compare.map((i) => JSON.stringify([D.models[i].creator, D.models[i].name])) };
}
let lastSettingsJSON;
function saveSettings() {
  try {
    const serialized = JSON.stringify(settingsSnapshot());
    if (serialized === lastSettingsJSON) return;
    localStorage.setItem(STORAGE_KEY, serialized);
    lastSettingsJSON = serialized;
  } catch { /* Keep the controls working without persistent storage. */ }
}
restoreSettings();
function activeSorts() { return state.multi ? state.sortKeys : [{ key: state.sort, desc: state.desc }]; }
const fmt = {
  cost: (v) => "$" + v.toFixed(1), time: (v) => v.toFixed(1) + "s", score: (v) => v.toFixed(1),
  tb: (v) => (v * 100).toFixed(1) + "%", agentic: (v) => v.toFixed(1),
};

function matchesMaker(m) {
  if (state.maker === "all") return true;
  if (state.maker === "other") return !D.named.includes(m.creator);
  return m.creator === D.makers[state.maker][1];
}

function matchingModels() {
  let rx = null;
  $("q").setAttribute("aria-invalid", "false");
  try { rx = state.q ? new RegExp(state.q, "i") : null; } catch { $("q").setAttribute("aria-invalid", "true"); return []; }
  return D.models.filter((m) => m.score >= state.min &&
    (state.terminalMin <= 0 || (m.tb != null && m.tb * 100 >= state.terminalMin)) &&
    matchesMaker(m) && (!rx || rx.test(m.name + " " + m.creator)));
}
function rows(list = matchingModels()) {
  list.sort((a, b) => b.score - a.score);
  if (state.top) list = list.slice(0, state.top);
  return list.sort((a, b) => {
    for (const { key, desc } of activeSorts()) {
      const sortValue = (value) => value == null || !state.multi ? value : Number((key === "tb" ? value * 100 : value).toFixed(1));
      const av = sortValue(a[key]), bv = sortValue(b[key]);
      if (av == null && bv == null) continue;
      if (av == null) return 1;
      if (bv == null) return -1;
      const delta = (av - bv) * (metric(key).high ? -1 : 1) * (desc ? -1 : 1);
      if (delta) return delta;
    }
    return 0;
  });
}

function tiers(list) {
  const out = {};
  for (const { key, high } of D.metrics) {
    const vals = list.map((m) => m[key]).filter((v) => v != null).sort((a, b) => high ? b - a : a - b);
    if (!vals.length) continue;
    const n = vals.length, q = Math.floor(n * 3 / 10);
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
  const leaderboard = document.querySelector(".leaderboard"), comparison = $("vs-result");
  const scroll = { x: window.scrollX, y: window.scrollY, tableX: leaderboard.scrollLeft, tableY: leaderboard.scrollTop,
    compareX: comparison.scrollLeft, compareY: comparison.scrollTop };
  const focused = document.activeElement;
  const focusHeader = focused?.closest("#head th[data-k]")?.dataset.k;
  const candidates = matchingModels();
  const list = rows([...candidates]), t = tiers(list);
  const sorts = activeSorts();
  $("sort-order").textContent = sorts.map(({ key, desc }) => `${metric(key).head} ${metric(key).high !== desc ? "↓" : "↑"}`).join(" › ");
  $("multi-sort").checked = state.multi;
  $("result-count").textContent = $("q").getAttribute("aria-invalid") === "true" ? "Invalid search pattern" : `${list.length} shown / ${D.models.length} models`;
  $("head").innerHTML = `<th>#</th><th>Model</th>` + D.metrics.map(({ head, key, high }) => {
    const priority = sorts.findIndex((s) => s.key === key), active = priority >= 0, descending = active && high !== sorts[priority].desc;
    return `<th data-k="${key}" class="${active ? "sorted" : ""}" aria-sort="${active ? (descending ? "descending" : "ascending") : "none"}"><button class="sort-button" title="${escapeHTML(metric(key).help)}">${head}<span class="sort-indicator">${active ? (descending ? " ↓" : " ↑") + (state.multi ? ` ${priority + 1}` : "") : ""}</span></button></th>`;
  }).join("") + `<th class="favorite-heading" title="Mark favorites.">Fav</th><th>VS</th>`;
  $("body").innerHTML = list.length ? list.map((m, i) => {
    const color = D.colors[m.creator] || "inherit";
    const cells = D.metrics.map(({ key }) => {
      const v = m[key], c = cls(key, v, t);
      const txt = v == null ? "–" : fmt[key](v);
      return `<td class="${key} ${c}">${txt}</td>`;
    }).join("");
    const index = modelIndexes.get(m), checked = state.compare.includes(index), favorited = favorites.has(modelId(m));
    return `<tr data-i="${index}" tabindex="0" class="${state.sel === index ? "sel" : ""} ${favorited ? "favorite" : ""}">` +
      `<td class="rank">${i + 1}</td><td class="model" style="color:${color}" title="${escapeHTML(m.name)}">${escapeHTML(m.name)}</td>${cells}` +
      `<td><input class="favorite-check" type="checkbox" data-favorite="${index}" aria-label="Favorite ${escapeHTML(m.name)}" ${favorited ? "checked" : ""}></td>` +
      `<td><input class="compare-check" type="checkbox" data-compare="${index}" aria-label="Compare ${escapeHTML(m.name)}" ${checked ? "checked" : ""} ${!checked && state.compare.length === 4 ? "disabled" : ""}></td></tr>`;
  }).join("") : `<tr><td colspan="9" class="empty">No matching models. Lower the minimums or reset filters.</td></tr>`;
  const selected = state.sel != null ? D.models[state.sel] : null;
  renderDetail(list.includes(selected) ? selected : list[0]);
  renderComparison();
  renderRecommendations(candidates);
  saveSettings();
  leaderboard.scrollLeft = scroll.tableX; leaderboard.scrollTop = scroll.tableY;
  comparison.scrollLeft = scroll.compareX; comparison.scrollTop = scroll.compareY;
  if (focusHeader) document.querySelector(`#head th[data-k="${focusHeader}"] button`)?.focus({ preventScroll: true });
  window.scrollTo({ left: scroll.x, top: scroll.y, behavior: "instant" });
}

const HTML_ESCAPE = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => HTML_ESCAPE[character]);
}
function selectModel(index) {
  const model = D.models[index];
  if (!model) return;
  state.sel = index;
  for (const row of document.querySelectorAll("#body tr[data-i]")) {
    row.classList.toggle("sel", +row.dataset.i === index);
  }
  renderDetail(model);
}
function updateComparisonRows() {
  for (const input of document.querySelectorAll("#body [data-compare]")) {
    input.checked = state.compare.includes(+input.dataset.compare);
    input.disabled = !input.checked && state.compare.length >= 4;
  }
  const container = $("vs-result"), x = container.scrollLeft, y = container.scrollTop;
  renderComparison();
  container.scrollLeft = x; container.scrollTop = y;
  saveSettings();
}
let pendingRender = 0;
function scheduleRender() {
  if (pendingRender) return;
  pendingRender = requestAnimationFrame(() => { pendingRender = 0; render(); });
}

function renderDetail(m) {
  m = m || { name: "No model selected", creator: "" };
  const f = (v, s) => v == null ? "–" : s(v);
  const items = [
    ["Input / 1M", f(m.price_in, (v) => "$" + v.toFixed(1))], ["Output / 1M", f(m.price_out, (v) => "$" + v.toFixed(1))],
    ["Output speed", f(m.tps, (v) => v.toFixed(1) + " tok/s")], ["First token", f(m.ttft, (v) => v.toFixed(1) + "s")],
    ["Context", f(m.context, (v) => (v / 1000).toLocaleString() + "K")], ["LiveBench Coding", f(m.lb_coding, (v) => v.toFixed(1))],
  ];
  $("detail").innerHTML = `<div class="name" style="color:${D.colors[m.creator] || "inherit"}">${escapeHTML(m.name)}
    <span style="color:var(--muted);font-weight:400"> · ${escapeHTML(m.creator)}</span></div>` +
    items.map(([k, v]) => `<div><div class="k">${k}</div><div class="v">${v}</div></div>`).join("");
}

function renderComparison() {
  const models = state.compare.map((i) => D.models[i]);
  const container = $("vs-result");
  container.replaceChildren();
  $("compare-count").textContent = `${models.length} / 4`;
  $("jump-compare").textContent = `VS ${models.length}/4 ↓`;
  $("jump-compare").disabled = models.length < 2;
  $("clear-favorites").disabled = favorites.size === 0;
  $("clear-compare-top").disabled = models.length === 0;
  $("clear-compare").disabled = models.length === 0;
  if (models.length < 2) {
    const message = document.createElement("div"); message.className = "empty";
    message.textContent = models.length ? `${models[0].name} selected. Check another model.` : "Check 2 to 4 models in the VS column to compare.";
    container.append(message); return;
  }
  const table = document.createElement("table");
  const header = table.createTHead().insertRow();
  const label = document.createElement("th"); label.textContent = "Metric"; header.append(label);
  for (const model of models) {
    const th = document.createElement("th"); th.textContent = model.name;
    th.style.color = D.colors[model.creator] || "inherit"; header.append(th);
  }
  const body = table.createTBody();
  for (const { head, key, high } of D.metrics) {
    const row = body.insertRow(); const label = row.insertCell(); label.textContent = head; label.title = metric(key).help;
    const values = models.map((m) => m[key]).filter((v) => v != null);
    const ranked = [...new Set(values)].sort((a, b) => high ? b - a : a - b);
    const fastest = key === "time" ? Math.min(...values) : null;
    for (const model of models) {
      const value = model[key], cell = row.insertCell();
      cell.textContent = value == null ? "–" : fmt[key](value);
      if (value == null) cell.title = "No data";
      else if (ranked.length === 1) cell.title = values.length > 1 ? "Tie among available values" : "Only available value";
      else {
        const rank = ranked.indexOf(value), last = ranked.length - 1;
        cell.className = rank === 0 ? "winner" : rank === last ? "rank-last" :
          rank / last <= .5 ? "rank-middle-good" : "rank-middle-poor";
        cell.title = `Rank ${rank + 1} of ${ranked.length}`;
        if (values.filter((v) => v === value).length > 1) cell.title += " · Tie";
      }
      if (key === "time" && value != null && fastest > 0 && value > fastest) {
        cell.title += ` · ${((value / fastest - 1) * 100).toFixed(1)}% slower than fastest`;
      }
      if (value != null) cell.setAttribute("aria-label", `${cell.textContent}, ${cell.title}`);

    }
  }
  container.append(table);
}

function recommended(models) {
  const eligible = models.filter((m) => Number.isFinite(m.cost) && m.cost > 0 && Number.isFinite(m.time) && m.time > 0);
  if (!eligible.length) return [];
  const minCost = Math.min(...eligible.map((m) => m.cost));
  const minTime = Math.min(...eligible.map((m) => m.time));
  const weight = state.costWeight / 100;
  return eligible.map((model) => ({ model, value: 100 / (weight * model.cost / minCost + (1 - weight) * (model.time / minTime) ** 1.5) }))
    .sort((a, b) => b.value - a.value || a.model.cost - b.model.cost || a.model.time - b.model.time);
}

let recommendationCache;
function renderRecommendations(models = matchingModels()) {
  if (recommendationCache && recommendationCache.weight === state.costWeight &&
      models.length === recommendationCache.models.length &&
      models.every((model, i) => model === recommendationCache.models[i])) return;
  recommendationCache = { weight: state.costWeight, models: [...models] };
  const ranked = recommended(models);
  $("cost-weight").value = String(state.costWeight);
  $("weight-label").textContent = `Cost ${state.costWeight}% · Time ${100 - state.costWeight}%`;
  $("recommendation-summary").textContent = `Top 5 of ${ranked.length} matching models · No time limit · ${models.length - ranked.length} missing valid cost/time`;
  const container = $("recommendations-result");
  container.replaceChildren();
  if (!ranked.length) {
    const empty = document.createElement("div"); empty.className = "empty";
    empty.textContent = "No matching models with valid cost and time. Adjust the filters.";
    container.append(empty); return;
  }
  const table = document.createElement("table"), header = table.createTHead().insertRow();
  for (const name of ["#", "Model", "Cost", "Time", "Value"]) {
    const th = document.createElement("th"); th.textContent = name;
    if (name === "Value") th.title = "Cost/time efficiency; higher is better. Slow responses are penalized.";
    header.append(th);
  }
  const body = table.createTBody();
  ranked.slice(0, 5).forEach(({ model, value }, index) => {
    const row = body.insertRow();
    for (const [column, text] of [String(index + 1), model.name, fmt.cost(model.cost), fmt.time(model.time), value.toFixed(1)].entries()) {
      const cell = row.insertCell(); cell.textContent = text;
      if (column === 1) { cell.className = "model"; cell.style.color = D.colors[model.creator] || "inherit"; cell.title = model.name; }
      if (column === 4 && value === ranked[0].value) cell.className = "winner";
    }
  });
  container.append(table);
}

$("cost-weight").addEventListener("input", (e) => {
  state.costWeight = Number(e.target.value); renderRecommendations(); saveSettings();
});

$("clear-compare").addEventListener("click", () => { state.compare = []; updateComparisonRows(); });
$("clear-compare-top").addEventListener("click", () => { state.compare = []; updateComparisonRows(); });
$("clear-favorites").addEventListener("click", () => {
  favorites.clear(); saveFavorites(); updateFavoriteRows();
});
$("jump-compare").addEventListener("click", () => {
  const section = document.querySelector(".comparison");
  section.scrollIntoView({ behavior: "instant", block: "start" });
  section.focus({ preventScroll: true });
});
$("body").addEventListener("change", (e) => {
  const favorite = e.target.closest("[data-favorite]");
  if (favorite) {
    const index = +favorite.dataset.favorite;
    toggleFavorite(index, favorite.checked);
    updateFavoriteRows();
    return;
  }
  const input = e.target.closest("[data-compare]"); if (!input) return;
  const index = +input.dataset.compare;
  if (input.checked && state.compare.length < 4) state.compare.push(index);
  else state.compare = state.compare.filter((i) => i !== index);
  updateComparisonRows();
});

$("tabs").addEventListener("click", (e) => {
  const b = e.target.closest("button"); if (!b) return;
  state.maker = b.dataset.k; state.sel = null; renderTabs(); render();
});
$("head").addEventListener("click", (e) => {
  const th = e.target.closest("th[data-k]"); if (!th) return;
  const k = th.dataset.k;
  if (state.multi) {
    const existing = state.sortKeys.find((s) => s.key === k);
    if (existing) existing.desc = !existing.desc;
    else state.sortKeys.push({ key: k, desc: false });
    state.sort = state.sortKeys[0].key; state.desc = state.sortKeys[0].desc;
  } else { state.desc = state.sort === k ? !state.desc : false; state.sort = k; }
  render();
});
$("multi-sort").addEventListener("change", (e) => {
  state.multi = e.target.checked;
  state.sortKeys = [{ key: state.sort, desc: state.desc }]; render();
});
$("body").addEventListener("click", (e) => {
  if (e.target.closest("[data-compare], [data-favorite]")) return;
  const tr = e.target.closest("tr[data-i]"); if (!tr) return;
  selectModel(+tr.dataset.i);
});
$("body").addEventListener("keydown", (e) => {
  if (e.target.matches("tr[data-i]") && ["Enter", " "].includes(e.key)) { e.preventDefault(); selectModel(+e.target.dataset.i); }
});
$("top").addEventListener("change", (e) => { state.top = +e.target.value; render(); });
$("q").addEventListener("input", (e) => { state.q = e.target.value; scheduleRender(); });
for (const [name, key] of [["score", "min"], ["terminal", "terminalMin"]]) {
  const select = $("min-" + name);
  const values = MINIMUM_VALUES;
  for (const value of values) select.add(new Option(value === 0 ? "Any" : String(value), String(value)));
  select.value = String(state[key]);
  select.addEventListener("change", () => {
    state[key] = Number(select.value); state.sel = null; render();
  });
}
$("reset-scores").addEventListener("click", () => {
  state.min = 0; state.terminalMin = 0; state.sel = null;
  $("min-score").value = "0"; $("min-terminal").value = "0";
  render();
  settingsFeedback("reset-scores", "Intelligence and Terminal set to Any");
});
$("reset-filters").addEventListener("click", () => {
  Object.assign(state, { maker: "all", top: 20, q: "", min: 40, terminalMin: 0, sort: "cost", desc: false, sel: null, compare: [], multi: false, sortKeys: [{ key: "cost", desc: false }], costWeight: 60 });
  let defaults = null;
  try { defaults = localStorage.getItem(DEFAULT_KEY); } catch { /* Built-in defaults remain available. */ }
  restoreSettings(defaults, false);
  favorites.clear();
  try {
    const saved = JSON.parse(defaults);
    if (Array.isArray(saved?.favorites)) {
      for (const id of saved.favorites) if (typeof id === "string") favorites.add(id);
    }
  } catch { /* Older or missing defaults restore an empty favorites list. */ }
  saveFavorites();
  state.compare = []; state.sel = null;
  for (const [id, value] of [["min-score", state.min], ["min-terminal", state.terminalMin], ["top", state.top]]) {
    const select = $(id);
    if (![...select.options].some((o) => o.value === String(value))) select.add(new Option(value.toFixed(1), String(value)));
    select.value = String(value);
  }
  $("q").value = state.q;
  renderTabs(); render();
  settingsFeedback("reset-filters", "Defaults restored · VS cleared");
});
let settingsNotice;
const feedbackTimers = new Map();
function settingsFeedback(buttonId, message, failed = false) {
  const button = $(buttonId), status = $("settings-status");
  clearTimeout(feedbackTimers.get(buttonId));
  button.classList.remove("feedback-success", "feedback-error");
  void button.offsetWidth;
  button.classList.add(failed ? "feedback-error" : "feedback-success");
  feedbackTimers.set(buttonId, setTimeout(() => {
    button.classList.remove("feedback-success", "feedback-error");
    feedbackTimers.delete(buttonId);
  }, 1300));
  status.classList.toggle("feedback-error", failed);
  status.textContent = message;
  clearTimeout(settingsNotice);
  settingsNotice = setTimeout(() => { status.textContent = ""; }, 3000);
}
$("save-defaults").addEventListener("click", () => {
  try {
    localStorage.setItem(DEFAULT_KEY, JSON.stringify({ ...settingsSnapshot(), favorites: [...favorites], compare: [] }));
    settingsFeedback("save-defaults", "Defaults saved");
  } catch { settingsFeedback("save-defaults", "Could not save defaults in this browser.", true); }
});

$("sub").innerHTML = `Collected ${D.fetched} · <a href="${D.sources.aa}" target="_blank" rel="noopener noreferrer">Artificial Analysis</a>` +
  (D.lbDate ? ` · <a href="${D.sources.lb}" target="_blank" rel="noopener noreferrer">LiveBench</a>` : " · LiveBench unavailable");
$("q").value = state.q;
$("min-score").value = String(state.min);
if (![...$("top").options].some((o) => +o.value === state.top)) $("top").add(new Option(state.top === 0 ? "All" : String(state.top), state.top));
$("top").value = String(state.top);
renderTabs(); render();
</script>
</body>
</html>
"""
