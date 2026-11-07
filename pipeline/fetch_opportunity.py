"""TCAC/HCD 2026 Opportunity Map -> opportunity fields in data/processed/tracts.json   OWNER: Builder A
Run AFTER pipeline/fetch_area.py, which rewrites tracts.json and resets opportunity_score to null:
    python pipeline/fetch_area.py && python pipeline/fetch_opportunity.py
Needs pandas (root requirements.txt) and openpyxl (pipeline/requirements.txt). One ~4 MB zip download, cached
under data/raw/ by common.get, so a re-run makes no request.

Source, checked 2026-11-07: https://www.treasurer.ca.gov/ctcac/opportunity, section "2026 Opportunity and
Neighborhood Change Maps - Adopted December 2025", link "2026 Statewide Summary Table" = summary_file.zip, which
holds final_opp_2026_public.xlsx. We read its "Orange County" sheet: one row per census tract, no block groups.
  - Geography: "this map update uses 2020 census tract boundaries" (2026 methodology PDF, p.14), the same
    geography as ACS 2024 5-year in tracts.json. Rural areas are scored by block group instead (p.7); in OC that
    is one tract, which sits on the "Rural" sheet, not the "Orange County" sheet, so it stays null here.
  - Categories (p.5-6): indicator count 8-9 Highest, 6-7 High, 4-5 Moderate, 3 or lower Low. Excluded areas are
    "Missing/Insufficient Information" (p.6); in this file their category cell is blank.
  - High-Poverty & Segregated is an OVERLAY, not a category: flagged tracts keep their category (FAQ p.9).
  - Final memo of Nov 20, 2025 (CTCAC-HCD.pdf on the same page): no comments, no changes from the Oct 20 draft.

Sets per tract, and changes no other field:
  opportunity_score             Low Resource 0, Moderate 1, High 2, Highest 3 (scale of app/core/area.py).
                                Anything else, blank included -> null. NOT the sheet's own "Opportunity Score"
                                column: that is a different 0-9 indicator count.
  opportunity_category          the sheet's category text, or null
  tcac_high_poverty_segregated  sheet flag 1 -> true, 0 -> false, blank -> null (unknown, never a guess)
"""
from __future__ import annotations

import io
import json
import zipfile

import pandas as pd

from common import PROCESSED, get, write_json

URL = "https://www.treasurer.ca.gov/sites/default/files/2025-11/summary_file.zip"
XLSX = "final_opp_2026_public.xlsx"
SHEET = "Orange County"
OC = "06059"
SCORE = {"Low Resource": 0, "Moderate Resource": 1, "High Resource": 2, "Highest Resource": 3}
# 0-9 indicator count -> category, from the 2026 methodology p.5-6. Used only to sanity-check the file.
BANDS = [(8, "Highest Resource"), (6, "High Resource"), (4, "Moderate Resource"), (-99, "Low Resource")]


def text(v) -> str | None:
    """A cell as stripped text; blank or NaN -> None."""
    if v is None or (isinstance(v, float) and pd.isna(v)) or v is pd.NA:
        return None
    s = str(v).strip()
    return s or None


def category_score(category: str | None) -> int | None:
    """Only the four named categories get a number. Anything else stays unknown."""
    return SCORE.get(category) if category else None


def hps_flag(v) -> bool | None:
    s = text(v)
    return {"1": True, "1.0": True, "0": False, "0.0": False}.get(s) if s else None


def band(score) -> str | None:
    s = text(score)
    if s is None:
        return None
    n = float(s)
    return next(cat for lo, cat in BANDS if n >= lo)


def main():
    path = PROCESSED / "tracts.json"
    tracts = json.loads(path.read_text())
    book = zipfile.ZipFile(io.BytesIO(get(URL, as_json=False, timeout=180))).read(XLSX)
    df = pd.read_excel(io.BytesIO(book), sheet_name=SHEET, dtype=str)
    assert df["Census Tract"].is_unique, "duplicate tracts in the Orange County sheet"
    assert df["Census Block Group"].isna().all(), "Orange County sheet has block-group rows: check the method"
    rows = {text(r["Census Tract"]): r for _, r in df.iterrows()}

    bad_band = [t for t, r in rows.items() if text(r["Opportunity Category"]) and
                band(r["Opportunity Score"]) != text(r["Opportunity Category"])]
    print(f"{SHEET} sheet: {len(rows)} tracts; category vs 0-9 score band mismatches: {len(bad_band)} {bad_band[:5]}")

    counts, blank, other, missing = {}, [], [], []
    for tid, t in tracts.items():
        r = rows.get(tid)
        cat = text(r["Opportunity Category"]) if r is not None else None
        t["opportunity_score"] = category_score(cat)
        t["opportunity_category"] = cat
        t["tcac_high_poverty_segregated"] = hps_flag(r["High-Poverty & Segregated Flag"]) if r is not None else None
        if r is None:
            missing.append(tid)
        elif cat is None:
            blank.append(tid)
        elif cat not in SCORE:
            other.append((tid, cat))
        counts[cat] = counts.get(cat, 0) + 1

    scored = sum(t["opportunity_score"] is not None for t in tracts.values())
    hps = [t["tcac_high_poverty_segregated"] for t in tracts.values()]
    print(f"tracts.json: {len(tracts)} tracts, {scored} scored. By category: {counts}")
    print(f"  High-Poverty & Segregated: true {hps.count(True)}, false {hps.count(False)}, null {hps.count(None)}")
    print(f"  null, blank category in source (excluded = Missing/Insufficient Information): {blank}")
    print(f"  null, category outside the four: {other}")
    if missing:  # explain each: is it on the Rural sheet (block-group level)?
        rural = pd.read_excel(io.BytesIO(book), sheet_name="Rural", dtype=str)
        rural = rural[rural["Census Tract"].str.startswith(OC, na=False)]
        for tid in missing:
            bgs = rural[rural["Census Tract"] == tid]
            parts = [f"{b} {c}" for b, c in zip(bgs["Census Block Group"], bgs["Opportunity Category"])]
            why = "Rural Areas, scored by block group: " + ", ".join(parts) if parts else "not in the 2026 file"
            print(f"  null, not on the {SHEET} sheet: {tid} ({tracts[tid].get('name')}): {why}")
    extra = sorted(set(rows) - set(tracts))
    print(f"  {SHEET} sheet tracts not in tracts.json (not added): {extra}")
    write_json("tracts.json", tracts)


if __name__ == "__main__":
    main()
