"""Tract-level "who it helps" data for Orange County -> data/processed/tracts.json   OWNER: Builder A
Run: python pipeline/fetch_area.py      NEEDS CENSUS_API_KEY in .env (free: https://api.census.gov/data/key_signup.html).
     As of 2026-11-07 the API redirects keyless calls to missing_key.html.

Census ACS 5-year 2024 (table ids checked against the API variable labels 2026-11-07):
  B19013_001E  median household income
  B25070       gross rent as % of income: 007-010 = 30%+, 011 = not computed
  B25014       occupants per room: owner 005-007, renter 011-013 = more than 1.0 per room
  B19001       household income bins: 002-015 = under $150k (APPROXIMATION of 'under the 4-person
               low-income limit of $148,850'; mixes household sizes: label it ASSUMPTION)
LODES WAC (jobs by workplace block): CE01 + CE02 = jobs paying <= $3,333/month. Aggregate block -> tract.
"""
import csv
import gzip
import io
import os
import sys

from common import get, write_json

YEAR = os.environ.get("ACS_YEAR", "2024")  # latest 5-year on the API, checked 2026-11-07
VARS = (["B19013_001E", "B25070_001E", "B25070_011E"] + [f"B25070_{i:03d}E" for i in range(7, 11)]
        + ["B25014_001E"] + [f"B25014_{i:03d}E" for i in (5, 6, 7, 11, 12, 13)]
        + ["B19001_001E"] + [f"B19001_{i:03d}E" for i in range(2, 16)])
params = {"get": ",".join(["NAME"] + VARS), "for": "tract:*", "in": "state:06 county:059"}
if not os.environ.get("CENSUS_API_KEY"):
    sys.exit("CENSUS_API_KEY missing. Get a free key at https://api.census.gov/data/key_signup.html, "
             "put CENSUS_API_KEY=... in .env (never commit it), and re-run.")
params["key"] = os.environ["CENSUS_API_KEY"]
rows = get(f"https://api.census.gov/data/{YEAR}/acs/acs5", params)
head, data = rows[0], rows[1:]


def n(r, k):
    v = r[head.index(k)]
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return None if v < 0 else v  # Census uses negative codes for missing


tracts = {}
for r in data:
    tid = "06059" + r[head.index("tract")]
    rent_tot = (n(r, "B25070_001E") or 0) - (n(r, "B25070_011E") or 0)
    burden = sum(n(r, f"B25070_{i:03d}E") or 0 for i in range(7, 11))
    crowd = sum(n(r, f"B25014_{i:03d}E") or 0 for i in (5, 6, 7, 11, 12, 13))
    hh = n(r, "B25014_001E")
    under150 = sum(n(r, f"B19001_{i:03d}E") or 0 for i in range(2, 16))
    tracts[tid] = {
        "name": r[head.index("NAME")], "households": hh, "median_hh_income": n(r, "B19013_001E"),
        "rent_burden_pct": round(100 * burden / rent_tot, 1) if rent_tot else None,
        "overcrowded_pct": round(100 * crowd / hh, 1) if hh else None,
        "eligible_households": under150 or None, "low_wage_jobs": None, "opportunity_score": None,
        "synthetic": False,
    }

# LODES: confirm the latest year at https://lehd.ces.census.gov/data/lodes/LODES8/ca/wac/
LODES = os.environ.get("LODES_URL", "https://lehd.ces.census.gov/data/lodes/LODES8/ca/wac/ca_wac_S000_JT00_2024.csv.gz")  # latest in directory, checked 2026-11-07
try:
    blob = gzip.decompress(get(LODES, as_json=False, timeout=180))
    for row in csv.DictReader(io.StringIO(blob.decode())):
        tid = row["w_geocode"][:11]
        if tid in tracts:
            tracts[tid]["low_wage_jobs"] = (tracts[tid]["low_wage_jobs"] or 0) + int(row["CE01"]) + int(row["CE02"])
except Exception as e:
    print("LODES skipped (say so in README):", e)

write_json("tracts.json", tracts)
