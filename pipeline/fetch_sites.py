"""Candidate sites for ONE city -> data/raw/he_sites.geojson   OWNER: Builder A
Run: python pipeline/fetch_sites.py "Santa Ana"

Sources (event repo, VERIFIED 2026-11-06):
- SCAG HousingElementSite_poly_scag: fields COUNTY, Jurisdiction, Assessor_Parcel_Number, capacity
  by income. Layer id assumed 0: open the MapServer URL in a browser to confirm.
- SB 4 proxy: OpenStreetMap places of worship (a LEAD, not ownership). Overpass can be at capacity:
  if it 502s, skip and say so in the README.
"""
import json
import sys

from common import RAW, get

CITY = sys.argv[1] if len(sys.argv) > 1 else "Santa Ana"
HE = "https://maps.scag.ca.gov/scaggis/rest/services/LDX/HousingElementSite_poly_scag/MapServer/0/query"

feats, offset = [], 0
while True:
    d = get(HE, {"where": f"COUNTY='Orange' AND Jurisdiction='{CITY}'", "outFields": "*", "outSR": 4326,
                 "f": "geojson", "resultOffset": offset, "resultRecordCount": 1000})
    batch = d.get("features", [])
    feats += batch
    if len(batch) < 1000:
        break
    offset += 1000
print(f"housing-element sites in {CITY}: {len(feats)}")
(RAW / "he_sites.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))

# SB 4 lead layer: places of worship in a bounding box around the city (edit bbox for other cities)
BBOX = {"Santa Ana": (33.68, -117.95, 33.79, -117.82)}.get(CITY)
if BBOX:
    q = f'[out:json][timeout:60];nwr["amenity"="place_of_worship"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});out center tags;'
    try:
        w = get("https://overpass-api.de/api/interpreter", {"data": q}, timeout=90)
        (RAW / "worship.json").write_text(json.dumps(w))
        print("places of worship (proxy):", len(w.get("elements", [])))
    except Exception as e:
        print("Overpass failed (note this in README):", e)
