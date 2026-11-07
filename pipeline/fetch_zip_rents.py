"""Median rent by ZIP-code area for Orange County -> data/processed/zip_rents.json   OWNER: Builder A
Run: python pipeline/fetch_zip_rents.py      NEEDS CENSUS_API_KEY in .env (see fetch_area.py). Two downloads, cached.

Sources (checked 2026-11-07):
  - Census ACS 5-year 2024, table B25031 "Median Gross Rent by Bedrooms", by ZCTA. Variable labels checked against
    the API: _002 No bedroom (studio), _003 1 bedroom, _004 2 bedrooms; *M = margin of error (90%).
  - Census 2020 ZCTA-to-county relationship file: which ZCTAs have land in Orange County (06059), and how much.
Caveats shown to users:
  - A ZCTA approximates a ZIP code; they are not identical, and some ZIPs (PO boxes) have no ZCTA.
  - Census caps some medians (annotation like "3,500+"): stored as that number with "<br>_at_least": true.
  - GROSS rent includes utilities; it is a 2020-2024 average, so it lags today's market; it covers all rentals,
    not ADUs. A missing or negative Census value stays null (unknown), never filled.
"""
import csv
import io
import json
import os
import sys

from common import get, write_json

if not os.environ.get("CENSUS_API_KEY"):
    sys.exit("CENSUS_API_KEY missing: put it in .env (never commit it).")

REL = "https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_county20_natl.txt"
OC = "06059"
YEAR = "2024"
BEDROOMS = {"0": "B25031_002", "1": "B25031_003", "2": "B25031_004"}  # studio, 1BR, 2BR

# 1) ZCTAs with land in Orange County, and the share of each ZCTA's land that is in OC
rel = csv.DictReader(io.StringIO(get(REL, as_json=False, timeout=180).decode("utf-8-sig")), delimiter="|")
oc = {}
for r in rel:
    if r["GEOID_COUNTY_20"] == OC and r["GEOID_ZCTA5_20"]:
        total = float(r["AREALAND_ZCTA5_20"] or 0)
        oc[r["GEOID_ZCTA5_20"]] = round(float(r["AREALAND_PART"] or 0) / total, 3) if total else None
print(f"ZCTAs with land in Orange County: {len(oc)}")

# 2) ACS B25031 for every ZCTA (one request), keep the OC ones
vars_ = [f"{v}{s}" for v in BEDROOMS.values() for s in ("E", "EA", "M")]  # EA = Census annotation, e.g. "3,500+"
rows = get(f"https://api.census.gov/data/{YEAR}/acs/acs5",
           {"get": ",".join(vars_), "for": "zip code tabulation area:*", "key": os.environ["CENSUS_API_KEY"]},
           timeout=180)
head, data = rows[0], rows[1:]


def num(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return None if v < 0 else v  # Census uses negative codes for missing / not computed


out = {}
for r in data:
    z = r[head.index("zip code tabulation area")]
    if z not in oc:
        continue
    out[z] = {"oc_land_share": oc[z]}
    for br, v in BEDROOMS.items():
        note = (r[head.index(f"{v}EA")] or "").strip()
        top = note.endswith("+")  # Census upper limit, e.g. "3,500+": the true median is at least this
        out[z][br] = float(note.rstrip("+").replace(",", "")) if top else num(r[head.index(f"{v}E")])
        out[z][f"{br}_moe"] = None if top else num(r[head.index(f"{v}M")])
        if top:
            out[z][f"{br}_at_least"] = True

known = {br: sum(1 for z in out.values() if z[br] is not None) for br in BEDROOMS}
tops = {br: max((z[br] for z in out.values() if z[br] is not None), default=None) for br in BEDROOMS}
print(f"OC ZCTAs with ACS rows: {len(out)}; with a value: {known}; highest values: {tops}")
write_json("zip_rents.json", {
    "about": "Median GROSS rent (includes utilities) by bedrooms, Census ACS 5-year 2024 (2020-2024 average), table "
             "B25031, by ZIP Code Tabulation Area (ZCTA, approximates a ZIP). All rentals, not ADUs. null = unknown. "
             "Keys: '0' studio, '1' 1BR, '2' 2BR, '*_moe' 90% margin of error, oc_land_share = share of the ZCTA's "
             "land in Orange County (Census 2020 relationship file).",
    "source_ids": ["census_acs_b25031_zcta", "census_zcta_county_rel"], "checked": "2026-11-07", "year": YEAR,
    "zctas": dict(sorted(out.items()))})
