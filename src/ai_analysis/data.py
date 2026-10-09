"""리더보드 수집·파싱·선별. 화면(HTML/표)과 무관한 데이터 계층."""
import csv
import io
import json
import os
import re
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

URL = os.environ.get("AA_URL", "https://artificialanalysis.ai/leaderboards/models")
LB_URL = os.environ.get("LB_URL", "https://livebench.ai")
# src/ai_analysis/data.py → 프로젝트 루트
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = Path(os.environ.get("AA_CACHE_DIR", PROJECT_ROOT / ".cache"))
CACHE_FILE = CACHE_DIR / "models.json"
CACHE_TTL_HOURS = float(os.environ.get("AA_CACHE_TTL_HOURS", "6"))

# 제조사 탭: 키 → (표시 이름, 사이트의 modelCreatorName). other는 나머지 전부
MAKERS = {
    "all": ("All", None),
    "claude": ("Claude", "Anthropic"),
    "openai": ("OpenAI", "OpenAI"),
    "google": ("Google", "Google"),
    "other": ("Other", None),
}
NAMED_CREATORS = {c for _, c in MAKERS.values() if c}

# 정렬 키: 이름 → (값 키, 높을수록 좋은가)
SORTS = {
    "cost": ("cost", False),
    "time": ("time", False),
    "score": ("score", True),
    "tb": ("tb", True),
    "agentic": ("agentic", True),
}

EFFORTS = {"minimal", "low", "medium", "high", "xhigh", "max"}
# 이름 정규화 때 버리는 토큰 (사이트마다 붙이는 수식어)
NOISE = {"effort", "thinking", "auto", "with", "fallback", "default", "reasoning", "preview"}


@dataclass
class Model:
    name: str
    creator: str
    score: float
    cost: float
    time: float | None
    tb: float | None
    tps: float | None
    ttft: float | None
    price_in: float | None
    price_out: float | None
    context: int | None
    agentic: float | None = None  # LiveBench Agentic Coding
    lb_coding: float | None = None  # LiveBench Coding

    def get(self, key: str):
        return getattr(self, key)


def fetch(url: str = URL) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def model_key(name: str) -> tuple[str, str | None]:
    """사이트마다 다른 모델 이름을 (기본 이름, effort)로 맞춘다.

    "Claude Opus 5.5 (xhigh with fallback)" / "claude-opus-5-5-xhigh-effort" → ("claude-opus-5-5", "xhigh")
    """
    tokens = re.split(r"[^a-z0-9]+", name.lower())
    tokens = [t for t in tokens if t and t not in NOISE and not re.fullmatch(r"\d+k|\d{8}", t)]
    effort = next((t for t in reversed(tokens) if t in EFFORTS), None)
    return "-".join(t for t in tokens if t not in EFFORTS), effort


def fetch_livebench() -> tuple[dict[str, dict], str]:
    """LiveBench 최신 표 → {"base|effort": {"agentic": .., "coding": ..}}, 표 날짜."""
    index = fetch(f"{LB_URL}/")
    bundle = fetch(f"{LB_URL}/" + re.search(r"static/js/main\.[0-9a-f]+\.js", index).group(0))
    for date in sorted(set(re.findall(r"20\d\d-\d\d-\d\d", bundle)), reverse=True)[:40]:
        tag = date.replace("-", "_")
        try:
            table = fetch(f"{LB_URL}/table_{tag}.csv")
            categories = json.loads(fetch(f"{LB_URL}/categories_{tag}.json"))
        except OSError:
            continue  # 표가 없는 날짜(모델 출시일 등)
        scores = {}
        for row in csv.DictReader(io.StringIO(table)):
            def avg(cat: str) -> float | None:
                vals = [float(row[t]) for t in categories.get(cat, []) if row.get(t)]
                return sum(vals) / len(vals) if vals else None
            base, effort = model_key(row["model"])
            scores[f"{base}|{effort}"] = {"agentic": avg("Agentic Coding"), "coding": avg("Coding")}
        return scores, date
    raise ValueError("LiveBench 표를 찾지 못했습니다.")


def parse(html: str) -> list[dict]:
    # 페이지에 내장된 Next.js 데이터: {\"slug\":...} 형태의 평평한 객체들
    raw_models: dict[str, dict] = {}
    for raw in re.findall(r'\{\\"slug\\":[^{}]*\}', html):
        try:
            obj = json.loads(raw.replace('\\"', '"'))
        except json.JSONDecodeError:
            continue
        raw_models.setdefault(obj["slug"], {}).update(obj)
    return [m for m in raw_models.values() if m.get("intelligenceIndex") is not None]


def to_models(raw: list[dict], livebench: dict[str, dict] | None = None) -> list[Model]:
    livebench = livebench or {}
    out = []
    for m in raw:
        cost = m.get("intelligenceIndexCostPerTask")
        if not cost:
            continue
        name = m.get("shortName") or m.get("name") or m["slug"]
        base, effort = model_key(name)
        lb = livebench.get(f"{base}|{effort}", {})
        out.append(Model(
            name=name.replace(" (with fallback)", "").replace(" with fallback", ""),
            creator=m.get("modelCreatorName", ""),
            score=m["intelligenceIndex"],
            cost=cost,
            time=m.get("medianEndToEndResponseTimeSeconds"),
            tb=m.get("terminalBench40"),
            tps=m.get("medianOutputTokensPerSecond"),
            ttft=m.get("medianTimeToFirstTokenSeconds"),
            price_in=m.get("price1mInputTokens"),
            price_out=m.get("price1mOutputTokens"),
            context=m.get("contextWindowTokens"),
            agentic=lb.get("agentic"),
            lb_coding=lb.get("coding"),
        ))
    return out


def load(html_path: str | None = None, refresh: bool = False) -> tuple[list[Model], datetime, str | None]:
    """(모델 목록, 수집 시각 UTC, LiveBench 표 날짜). 캐시가 TTL 안이면 쓰고, 아니거나 refresh면 새로 받는다."""
    if not html_path and not refresh and CACHE_FILE.exists():
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        fetched_at = datetime.fromisoformat(data["fetched_at"])
        if (datetime.now(timezone.utc) - fetched_at).total_seconds() < CACHE_TTL_HOURS * 3600:
            return to_models(data["models"], data.get("livebench")), fetched_at, data.get("livebench_date")
    raw = parse(Path(html_path).read_text(encoding="utf-8") if html_path else fetch())
    if not raw:
        raise ValueError("모델 데이터를 찾지 못했습니다. 페이지 구조가 바뀌었을 수 있습니다.")
    try:
        livebench, lb_date = fetch_livebench()
    except (OSError, ValueError, AttributeError):
        livebench, lb_date = {}, None  # LiveBench가 없어도 나머지 열은 보여 준다
    fetched_at = datetime.now(timezone.utc)
    if not html_path:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps({"fetched_at": fetched_at.isoformat(), "models": raw,
                                          "livebench": livebench, "livebench_date": lb_date}), encoding="utf-8")
    return to_models(raw, livebench), fetched_at, lb_date


def matches_maker(m: Model, maker: str) -> bool:
    if maker == "all":
        return True
    if maker == "other":
        return m.creator not in NAMED_CREATORS
    return m.creator == MAKERS[maker][1]


def select(models: list[Model], maker: str = "all", top: int = 20, min_score: float = 0,
           pattern: str | None = None, sort: str = "cost", reverse: bool = False) -> list[Model]:
    """제조사·검색어로 거른 뒤 점수 상위 top개를 골라 sort 기준으로 나열한다."""
    rx = re.compile(pattern, re.I) if pattern else None
    rows = [
        m for m in models
        if m.score >= min_score and matches_maker(m, maker)
        and (not rx or rx.search(f"{m.name} {m.creator}"))
    ]
    rows.sort(key=lambda m: -m.score)
    if top:
        rows = rows[:top]
    key, high = SORTS[sort]
    present = [m for m in rows if m.get(key) is not None]
    missing = [m for m in rows if m.get(key) is None]
    present.sort(key=lambda m: m.get(key), reverse=high != reverse)
    return present + missing  # 값이 없는 모델은 항상 맨 뒤


def fmt(v, spec: str, suffix: str = "", prefix: str = "") -> str:
    return "-" if v is None else f"{prefix}{v:{spec}}{suffix}"


def cells(m: Model) -> dict[str, str]:
    return {
        "cost": fmt(m.cost, ".2f", prefix="$"),
        "time": fmt(m.time, ".0f", "s"),
        "score": fmt(m.score, ".1f"),
        "tb": fmt(m.tb and m.tb * 100, ".1f", "%"),
        "agentic": fmt(m.agentic, ".1f"),
    }
