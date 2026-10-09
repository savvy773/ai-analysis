"""리더보드 수집·파싱·선별. 화면(TUI/표)과 무관한 데이터 계층."""
import json
import os
import re
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

URL = os.environ.get("AA_URL", "https://artificialanalysis.ai/leaderboards/models")
CACHE_DIR = Path(os.environ.get("AA_CACHE_DIR", Path(__file__).resolve().parent / ".cache"))
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
MAKER_COLOR = {"Anthropic": "#d97757", "OpenAI": "#10a37f", "Google": "#4c8bf5"}
NAMED_CREATORS = {c for _, c in MAKERS.values() if c}

# 정렬 키: 이름 → (값 키, 높을수록 좋은가)
SORTS = {
    "cost": ("cost", False),
    "time": ("time", False),
    "score": ("score", True),
    "tb": ("tb", True),
}


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

    def get(self, key: str):
        return getattr(self, key)


def fetch(url: str = URL) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


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


def to_models(raw: list[dict]) -> list[Model]:
    out = []
    for m in raw:
        cost = m.get("intelligenceIndexCostPerTask")
        if not cost:
            continue
        name = m.get("shortName") or m.get("name") or m["slug"]
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
        ))
    return out


def load(html_path: str | None = None, refresh: bool = False) -> tuple[list[Model], datetime]:
    """모델 목록과 수집 시각(UTC). 캐시가 TTL 안이면 쓰고, 아니거나 refresh면 새로 받는다."""
    if html_path:
        raw = parse(Path(html_path).read_text(encoding="utf-8"))
        return to_models(raw), datetime.now(timezone.utc)
    if not refresh and CACHE_FILE.exists():
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        fetched_at = datetime.fromisoformat(data["fetched_at"])
        if (datetime.now(timezone.utc) - fetched_at).total_seconds() < CACHE_TTL_HOURS * 3600:
            return to_models(data["models"]), fetched_at
    raw = parse(fetch())
    if not raw:
        raise ValueError("모델 데이터를 찾지 못했습니다. 페이지 구조가 바뀌었을 수 있습니다.")
    fetched_at = datetime.now(timezone.utc)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps({"fetched_at": fetched_at.isoformat(), "models": raw}), encoding="utf-8")
    return to_models(raw), fetched_at


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


def best_values(rows: list[Model]) -> dict[str, float]:
    best = {}
    for key, high in SORTS.values():
        vals = [m.get(key) for m in rows if m.get(key) is not None]
        if vals:
            best[key] = max(vals) if high else min(vals)
    return best


def fmt(v, spec: str, suffix: str = "", prefix: str = "") -> str:
    return "-" if v is None else f"{prefix}{v:{spec}}{suffix}"


def cells(m: Model) -> dict[str, str]:
    return {
        "cost": fmt(m.cost, ".2f", prefix="$"),
        "time": fmt(m.time, ".0f", "s"),
        "score": fmt(m.score, ".1f"),
        "tb": fmt(m.tb and m.tb * 100, ".1f", "%"),
    }
