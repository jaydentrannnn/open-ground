"""Median rent by ZIP-code area for Homeowner mode.   OWNER: Builder A
Data: data/processed/zip_rents.json, built by pipeline/fetch_zip_rents.py from Census ACS 5-year 2024 table B25031
(median GROSS rent by bedrooms) by ZCTA, which approximates a ZIP. null = unknown, never filled. Census caps some
medians ("3,500+"), so the real median there is at least that number.
"""
from __future__ import annotations

import json
import re

from core import contracts

UNIT = {0: "studio", 1: "1-bedroom", 2: "2-bedroom"}
CAVEAT = ("Census rents include utilities, are a 2020-2024 average (so likely below today's market) and cover all "
          "rentals, not ADUs. A ZIP Code Tabulation Area approximates your ZIP.")


def load() -> dict:
    p = contracts.PROCESSED / "zip_rents.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"zctas": {}}


def lookup(zip_code: str | None, bedrooms: int, data: dict | None = None) -> dict:
    """{'status': empty|invalid|not_found|no_value|ok, 'zip', 'rent', 'moe', 'at_least', 'oc_land_share', 'text'}."""
    z = (zip_code or "").strip()
    out = {"status": "empty", "zip": z, "rent": None, "moe": None, "at_least": False, "oc_land_share": None, "text": ""}
    if not z:
        return out
    if not re.fullmatch(r"\d{5}", z):
        return {**out, "status": "invalid", "text": "Enter a 5-digit ZIP code."}
    zc = (data if data is not None else load()).get("zctas", {}).get(z)
    unit = UNIT.get(bedrooms, f"{bedrooms}-bedroom")
    if not zc:
        return {**out, "status": "not_found",
                "text": f"No Census rent for ZIP {z}: it is outside Orange County or has no ZIP Code Tabulation "
                        "Area. Using the county default; enter your own rent if you know it."}
    v, moe, top = zc.get(str(bedrooms)), zc.get(f"{bedrooms}_moe"), bool(zc.get(f"{bedrooms}_at_least"))
    share = zc.get("oc_land_share")
    out.update({"oc_land_share": share})
    if v is None:
        return {**out, "status": "no_value",
                "text": f"Census has no {unit} median rent for ZIP area {z} (too few units sampled): UNKNOWN. "
                        "Using the county default; enter your own rent if you know it."}
    amount = f"${v:,.0f} or more (Census upper limit)" if top else f"${v:,.0f}" + (f" ± ${moe:,.0f}" if moe else "")
    part = f" Only {share:.0%} of this ZIP area is in Orange County." if share is not None and share < 0.5 else ""
    return {**out, "status": "ok", "rent": v, "moe": moe, "at_least": top,
            "text": f"Census ACS 2024 median gross rent, {unit}, ZIP area {z}: {amount}.{part} {CAVEAT}"}
