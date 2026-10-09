"""리더보드 수집·파싱·선별. 화면(HTML/표)과 무관한 데이터 계층."""
import csv
import io
import json
import math
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
        reader = csv.DictReader(io.StringIO(table))
        if not reader.fieldnames or "model" not in reader.fieldnames:
            raise ValueError("LiveBench CSV에 model 열이 없습니다.")
        if not isinstance(categories, dict) or any(
            not isinstance(tasks, list) or any(not isinstance(task, str) for task in tasks)
            for tasks in categories.values()
        ):
            raise ValueError("LiveBench 카테고리 형식이 올바르지 않습니다.")
        for row in reader:
            if not row.get("model"):
                raise ValueError("LiveBench CSV에 모델명이 없는 행이 있습니다.")
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


def numeric(value) -> float | None:
    """Next.js 누락 값($undefined 등)을 제외하고 유한한 수만 반환한다."""
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def to_models(raw: list[dict], livebench: dict[str, dict] | None = None) -> list[Model]:
    livebench = livebench or {}
    out = []
    for m in raw:
        cost = numeric(m.get("intelligenceIndexCostPerTask"))
        score = numeric(m.get("intelligenceIndex"))
        if cost is None or cost <= 0 or score is None:
            continue
        name = m.get("shortName") or m.get("name") or m["slug"]
        base, effort = model_key(name)
        lb = livebench.get(f"{base}|{effort}", {})
        context = numeric(m.get("contextWindowTokens"))
        out.append(Model(
            name=name.replace(" (with fallback)", "").replace(" with fallback", ""),
            creator=m.get("modelCreatorName", ""),
            score=score,
            cost=cost,
            time=numeric(m.get("medianEndToEndResponseTimeSeconds")),
            tb=numeric(m.get("terminalBench40")),
            tps=numeric(m.get("medianOutputTokensPerSecond")),
            ttft=numeric(m.get("medianTimeToFirstTokenSeconds")),
            price_in=numeric(m.get("price1mInputTokens")),
            price_out=numeric(m.get("price1mOutputTokens")),
            context=int(context) if context is not None else None,
            agentic=numeric(lb.get("agentic")),
            lb_coding=numeric(lb.get("coding")),
        ))
    return out


def load(html_path: str | None = None, refresh: bool = False) -> tuple[list[Model], datetime, str | None]:
    """(모델 목록, 수집 시각 UTC, LiveBench 표 날짜). 캐시가 TTL 안이면 쓰고, 아니거나 refresh면 새로 받는다."""
    if not html_path and not refresh and CACHE_FILE.exists():
        try:
            data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            fetched_at = datetime.fromisoformat(data["fetched_at"])
            age = (datetime.now(timezone.utc) - fetched_at).total_seconds()
            if 0 <= age < CACHE_TTL_HOURS * 3600:
                models = to_models(data["models"], data.get("livebench"))
                if models:
                    return models, fetched_at, data.get("livebench_date")
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            pass  # 읽을 수 없거나 손상된 캐시는 새로 수집해 복구한다.
    raw = parse(Path(html_path).read_text(encoding="utf-8") if html_path else fetch())
    if not raw:
        raise ValueError("모델 데이터를 찾지 못했습니다. 페이지 구조가 바뀌었을 수 있습니다.")
    models = to_models(raw)
    if not models:
        raise ValueError("유효한 모델이 없습니다. 점수·비용 데이터 형식을 확인하세요.")
    try:
        livebench, lb_date = fetch_livebench()
    except (OSError, ValueError, KeyError, TypeError, AttributeError, csv.Error):
        livebench, lb_date = {}, None  # LiveBench가 없어도 나머지 열은 보여 준다
    if livebench:
        models = to_models(raw, livebench)
    fetched_at = datetime.now(timezone.utc)
    if not html_path:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps({"fetched_at": fetched_at.isoformat(), "models": raw,
                                          "livebench": livebench, "livebench_date": lb_date}), encoding="utf-8")
    return models, fetched_at, lb_date


def matches_maker(m: Model, maker: str) -> bool:
    if maker == "all":
        return True
    if maker == "other":
        return m.creator not in NAMED_CREATORS
    return m.creator == MAKERS[maker][1]


def select(models: list[Model], maker: str = "all", top: int = 20, min_score: float = 0,
           pattern: str | None = None, sort: str = "cost", reverse: bool = False,
           min_terminal: float = 0) -> list[Model]:
    """제조사·검색어로 거른 뒤 점수 상위 top개를 골라 sort 기준으로 나열한다."""
    rx = re.compile(pattern, re.I) if pattern else None
    rows = [
        m for m in models
        if m.score >= min_score and matches_maker(m, maker)
        and (min_terminal <= 0 or (m.tb is not None and m.tb * 100 >= min_terminal))
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
        "cost": fmt(m.cost, ".1f", prefix="$"),
        "time": fmt(m.time, ".1f", "s"),
        "score": fmt(m.score, ".1f"),
        "tb": fmt(m.tb and m.tb * 100, ".1f", "%"),
        "agentic": fmt(m.agentic, ".1f"),
    }
