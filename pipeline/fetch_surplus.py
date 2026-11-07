"""HCD Surplus Land Act notices for Orange County -> data/raw/sla_oc.json   OWNER: Builder A
Run: python pipeline/fetch_surplus.py      (one CSV download, cached)

Source: data.ca.gov "Surplus Land Act Notices of Availability Received" (CSV resource, dataset modified
2026-11-06). Data dictionary (DOCX on the same page), read 2026-11-07:
  Status "Active"  = the agency sent the notice to HCD within the last 60 days.
  Status "Archive" = sent MORE than 60 days ago. It does NOT mean the land is gone: the response window has
                     likely passed, so the land's status is unknown until someone calls the agency.
Cleaning: OC = inside the OC envelope AND an OC city name (fixes the 'WESTMINISTER' typo); parcel size text
like "9,005 SF" -> acres (43,560 sq ft per acre).
PRIVACY: the CSV's contact column names individual staff with email and phone. We DROP it and keep only the
agency name and the notice link.
"""
import csv
import io
import json
import re

from common import OC_BBOX, RAW, get

CSV = ("https://publish.data.ca.gov/dataset/0a52a6d9-4c1f-4905-8d25-6117c60c35c8/resource/"
       "bb81599a-e130-48aa-a6e3-bbcce9392d4f/download/noa_information.csv")
OC_CITIES = {"ALISO VIEJO", "ANAHEIM", "BREA", "BUENA PARK", "COSTA MESA", "CYPRESS", "DANA POINT",
             "FOUNTAIN VALLEY", "FULLERTON", "GARDEN GROVE", "HUNTINGTON BEACH", "IRVINE", "LA HABRA", "LA PALMA",
             "LAGUNA BEACH", "LAGUNA HILLS", "LAGUNA NIGUEL", "LAGUNA WOODS", "LAKE FOREST", "LOS ALAMITOS",
             "MISSION VIEJO", "NEWPORT BEACH", "ORANGE", "PLACENTIA", "RANCHO SANTA MARGARITA", "SAN CLEMENTE",
             "SAN JUAN CAPISTRANO", "SANTA ANA", "SEAL BEACH", "STANTON", "TUSTIN", "VILLA PARK", "WESTMINSTER",
             "YORBA LINDA"}
TYPOS = {"WESTMINISTER": "WESTMINSTER"}
KEEP = ["Parent Case", "Local Agency Type", "Local Agency", "APN", "Date Notice Issued", "NOA Due Date",
        "NOA Status", "Notice Website Link", "Consolidated Sites", "Address", "City", "Zip",
        "Parcel Size (Gross Acres)", "General Plan/Zoning", "Existing Use/Vacancy"]  # NOT the contact column


def acres(text):
    if not text:
        return None
    m = re.search(r"[\d,]*\.?\d+", text)
    if not m:
        return None
    v = float(m.group().replace(",", ""))
    return round(v / 43560, 3) if re.search(r"sf|sq", text, re.I) else v


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


rows = list(csv.DictReader(io.StringIO(get(CSV, as_json=False, timeout=120).decode("utf-8-sig", "ignore"))))
w, s, e, n = OC_BBOX
out = []
for r in rows:
    lon, lat = num(r.get("x")), num(r.get("y"))
    city = re.sub(r"\s+", " ", (r.get("City") or "").strip().upper())
    city = TYPOS.get(city, city)
    if lon is None or lat is None or not (w <= lon <= e and s <= lat <= n) or city not in OC_CITIES:
        continue
    rec = {k: (r.get(k) or "").strip() or None for k in KEEP}
    rec.update({"City": city.title(), "lon": lon, "lat": lat, "acres": acres(r.get("Parcel Size (Gross Acres)"))})
    out.append(rec)
(RAW / "sla_oc.json").write_text(json.dumps(out))
print(f"SLA notices statewide: {len(rows)}  in Orange County: {len(out)}  "
      f"(Active: {sum(1 for o in out if o['NOA Status'] == 'Active')})")
