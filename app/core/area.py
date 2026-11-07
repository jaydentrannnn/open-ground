"""Area Benefit Score: how much a home here helps. 0-100, built from tract-level data only.

OWNER: Builder A (Data & Rules). Neighborhood totals only, never individual households.
A missing metric is skipped and reported, never filled with a guess.

ASSUMPTION: the weights (DEFAULT_WEIGHTS) and the (low, high) scaling ranges in METRICS are the team's own
choice, not from any source. They decide the ranking. score() returns this as "assumption" so the UI can tag it.
"""
from __future__ import annotations

# (metric key, label, higher_is_better, (low, high) range used to scale to 0-1)
METRICS = [
    ("rent_burden_pct", "Renters paying 30%+ of income on rent", True, (20, 70)),
    ("overcrowded_pct", "Overcrowded households", True, (0, 30)),
    ("eligible_households", "Households earning under $150k (ASSUMPTION: nearest ACS income bin to the OC "
                            "4-person low-income limit of $148,850; mixes household sizes)", True, (0, 3000)),
    ("low_wage_jobs", "Low-wage jobs located in this tract (LODES CE01+CE02)", True, (0, 3000)),
    ("opportunity_score", "TCAC/HCD opportunity (0 low - 3 highest)", True, (0, 3)),
]

DEFAULT_WEIGHTS = {"rent_burden_pct": 0.3, "overcrowded_pct": 0.2, "eligible_households": 0.2,
                   "low_wage_jobs": 0.2, "opportunity_score": 0.1}


ASSUMPTION_NOTE = ("Weights (rent burden 30%, crowding 20%, households under $150k 20%, low-wage jobs 20%, "
                   "opportunity 10%) and the 0-100 scaling ranges are our choice, not from a source.")


def _scale(v, lo, hi, higher_better=True):
    x = (v - lo) / (hi - lo) if hi != lo else 0
    x = min(max(x, 0.0), 1.0)
    return x if higher_better else 1 - x


def score(tract: dict | None, weights: dict | None = None) -> dict:
    weights = weights or DEFAULT_WEIGHTS
    if not tract:
        return {"score": None, "parts": [], "missing": [m[0] for m in METRICS], "assumption": ASSUMPTION_NOTE}
    parts, missing, total_w, acc = [], [], 0.0, 0.0
    for key, label, hib, (lo, hi) in METRICS:
        v = tract.get(key)
        w = weights.get(key, 0)
        if v is None:
            missing.append(key)
            continue
        s = _scale(v, lo, hi, hib)
        parts.append({"metric": key, "label": label, "value": v, "scaled": s, "weight": w})
        acc += s * w
        total_w += w
    sc = round(100 * acc / total_w) if total_w else None
    return {"score": sc, "parts": parts, "missing": missing, "assumption": ASSUMPTION_NOTE}
