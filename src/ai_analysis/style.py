"""HTML 리포트와 터미널 표가 함께 쓰는 열 정의와 색 규칙."""
from . import data as d

# (헤더, 값 키) — 왼쪽일수록 중요
METRICS = [("Cost", "cost"), ("Time", "time"), ("Intelligence", "score"), ("Terminal", "tb"), ("Agentic", "agentic")]
METRIC_HELP = {
    "cost": "Artificial Analysis cost per Intelligence Index task (USD). Lower is better.",
    "time": "Median end-to-end response time (seconds). Lower is better.",
    "score": "Artificial Analysis Intelligence Index. Higher is better.",
    "tb": "Terminal-Bench 4.0 score (%). Higher is better.",
    "agentic": "LiveBench Agentic Coding average. Higher is better.",
}
HEAD = ["#", "Model", *(h for h, _ in METRICS)]

# 어두운 배경에서 눈이 덜 피로한 톤
MAKER_COLOR = {"Anthropic": "#e8956f", "OpenAI": "#5fd3a5", "Google": "#82aaff"}
BEST = "bold #7ee787"   # 열 최고 값 (★)
GOOD = "#b5e8b0"        # 상위 30%
POOR = "#8b949e"        # 하위 30% (흐리게)
MISSING = "#6e7681"     # 값 없음


def tiers(rows: list[d.Model]) -> dict[str, tuple[float, float, float]]:
    """열마다 (최고 값, 상위 30% 경계, 하위 30% 경계). 좋은 쪽 기준으로 정렬한 값에서 뽑는다."""
    out = {}
    for _, key in METRICS:
        _, high = d.SORTS[key]
        vals = sorted((m.get(key) for m in rows if m.get(key) is not None), reverse=high)
        if vals:
            n = len(vals)
            out[key] = (vals[0], vals[max(0, n * 3 // 10 - 1)], vals[min(n - 1, n - n * 3 // 10)])
    return out


def cell_style(key: str, value, tier: dict) -> tuple[str, bool]:
    """(스타일, 최고 값 여부)."""
    if value is None:
        return MISSING, False
    if key not in tier:
        return "", False
    best, good, poor = tier[key]
    _, high = d.SORTS[key]
    better = (lambda a, b: a >= b) if high else (lambda a, b: a <= b)
    if value == best:
        return BEST, True
    if better(value, good):
        return GOOD, False
    if not better(value, poor) or value == poor:
        return POOR, False
    return "", False
