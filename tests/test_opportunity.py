"""TCAC/HCD opportunity fields in tracts.json (filled by pipeline/fetch_opportunity.py)."""
import json
import sys
from pathlib import Path

import pytest

from core import area, contracts

ROOT = Path(__file__).resolve().parents[1]
REAL = ROOT / "data" / "processed" / "tracts.json"
FOUR = {"Low Resource": 0, "Moderate Resource": 1, "High Resource": 2, "Highest Resource": 3}


def test_opportunity_score_is_0_to_3_or_unknown():
    for tid, t in contracts.load_tracts().items():
        assert t.get("opportunity_score") in {0, 1, 2, 3, None}, tid
        assert t.get("tcac_high_poverty_segregated") in {True, False, None}, tid


@pytest.mark.skipif(not REAL.exists(), reason="real tracts.json not built")
def test_real_tracts_are_scored_and_match_category():
    tracts = json.loads(REAL.read_text())
    scored = [t for t in tracts.values() if t.get("opportunity_score") is not None]
    assert len(scored) > 600, f"only {len(scored)} tracts have an opportunity score: run pipeline/fetch_opportunity.py"
    for tid, t in tracts.items():
        cat = t.get("opportunity_category")
        assert t["opportunity_score"] == FOUR.get(cat), (tid, cat, t["opportunity_score"])  # unknown text -> None


def test_pipeline_maps_only_the_four_categories():
    sys.path.insert(0, str(ROOT / "pipeline"))
    fo = pytest.importorskip("fetch_opportunity")
    assert {c: fo.category_score(c) for c in FOUR} == FOUR
    for other in [None, "", "Missing/Insufficient Information", "N/A", "High-Poverty & Segregated"]:
        assert fo.category_score(other) is None
    assert (fo.hps_flag("1"), fo.hps_flag("0"), fo.hps_flag(None), fo.hps_flag(float("nan"))) == (True, False, None, None)
    assert [fo.band(s) for s in ("9", "8", "7", "6", "5", "4", "3", "-1")] == [
        "Highest Resource"] * 2 + ["High Resource"] * 2 + ["Moderate Resource"] * 2 + ["Low Resource"] * 2


def test_area_score_uses_opportunity_score():
    hi, lo = area.score({"opportunity_score": 3}), area.score({"opportunity_score": 0})
    assert hi["score"] == 100 and lo["score"] == 0
    assert [p["metric"] for p in hi["parts"]] == ["opportunity_score"]
    assert "opportunity_score" in area.score({"opportunity_score": None})["missing"]
