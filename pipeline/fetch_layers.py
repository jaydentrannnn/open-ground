"""Download constraint layers ONCE for all of Orange County -> data/raw/layer_*.geojson   OWNER: Builder A
Run: python pipeline/fetch_layers.py      (cached: a second run makes no requests)

Why bulk: checking 2,126 sites one request at a time would be ~6,000+ calls to public servers.
Downloading each layer once and testing locally is kinder (event rule) and makes the next city free.

Layers (fields checked 2026-11-07 by reading each layer's REST metadata):
  flood     OC Floodplains (county copy of FEMA flood zones). SFHA_TF = FEMA's own "special flood hazard
            area" flag; ZONE_SUBTY marks floodways. Vintage of the county copy: UNKNOWN.
  fire_lra  OC Fire_Hazard_Severity_Zones_LRA: 21 polygons, all HAZ_CLASS 'Very High'. Vintage UNKNOWN.
  fire_lra25 CAL FIRE (org "California Department of Forestry and Fire Protection") FHSALRA25_v1_All:
            "Fire Hazard Severity Zone classes from the map dated March 24, 2025". Very High only.
  fire_sra  CAL FIRE statewide service, layer 0 "State Responsibility Areas (2007)": OLD MAP. CAL FIRE's
            FHSZSRA25_3 layer describes itself as a draft under public comment, so it is a lead, not used.
  hqta      Caltrans CA High-Quality Transit Areas (867 polygons in the OC envelope).
  worship   OpenStreetMap amenity=place_of_worship (SB 4 LEAD only: not ownership).
  zoning legend: SCAG Zoning_poly_OR layer metadata -> data/processed/scag_zoning_codes.json
"""
import html
import json
import re

from common import OC_BBOX, PROCESSED, RAW, fetch_all, get

LAYERS = {
    "flood": ("https://www.ocgis.com/arcpub/rest/services/Map_Layers/Floodplains/MapServer/0", "1=1",
              "FLD_ZONE,ZONE_SUBTY,SFHA_TF", None),
    "fire_lra": ("https://www.ocgis.com/arcpub/rest/services/Map_Layers/Fire_Hazard_Severity_Zones_LRA/MapServer/0",
                 "HAZ_CLASS='Very High'", "HAZ_CLASS,SRA", None),
    "fire_lra25": ("https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/FHSALRA25_v1_All/FeatureServer/0",
                   "FHSZ_Description='Very High'", "FHSZ_Description,SRA", OC_BBOX, 100),
    "fire_sra": ("https://services.gis.ca.gov/arcgis/rest/services/Environment/Fire_Severity_Zones/MapServer/0",
                 "HAZ_CLASS='Very High'", "HAZ_CLASS,SRA", OC_BBOX),
    "hqta": ("https://caltrans-gis.dot.ca.gov/arcgis/rest/services/CHrailroad/CA_HQ_Transit_Areas/FeatureServer/0",
             "1=1", "hqta_type,agency_primary", OC_BBOX, 100),
}

for name, (url, where, fields, bbox, *chunk) in LAYERS.items():
    try:
        feats = fetch_all(url, where, fields, bbox, *chunk)
        (RAW / f"layer_{name}.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    except Exception as e:  # a failed layer stays unknown downstream; never guessed
        print(f"  {name} FAILED (its checks will show 'unknown'; note in README): {e}")

# SB 4 lead layer: places of worship (Overpass bbox order is south, west, north, east)
w, s, e, n = OC_BBOX
q = f'[out:json][timeout:90];nwr["amenity"="place_of_worship"]({s},{w},{n},{e});out center tags;'
try:
    d = get("https://overpass-api.de/api/interpreter", {"data": q}, timeout=120)
    pts = []
    for el in d.get("elements", []):
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lon = el.get("lon") or (el.get("center") or {}).get("lon")
        if lat and lon:
            tags = el.get("tags", {})
            pts.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]},
                        "properties": {"osm_id": f"{el['type']}/{el['id']}", "name": tags.get("name"),
                                       "religion": tags.get("religion")}})
    (RAW / "layer_worship.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": pts}))
    print(f"  places of worship (OSM, proxy only): {len(pts)}")
except Exception as e:
    print("  Overpass FAILED (SB 4 lead layer skipped; note in README):", e)

# SCAG zoning code legend, parsed from the layer's own metadata (no hand-typed codes)
meta = get("https://maps.scag.ca.gov/scaggis/rest/services/LDX/Zoning_poly_OR/MapServer/0/metadata", as_json=False)
t = html.unescape(meta.decode("utf-8", "ignore"))
legend_html = t[t.find("Legend"):]
codes = {}
for code, label in re.findall(r"<SPAN>(\d{4}) ([^<]+)</SPAN>", legend_html):  # one code per HTML element
    codes.setdefault(code, re.sub(r"\s+", " ", html.unescape(label)).strip())
(PROCESSED / "scag_zoning_codes.json").write_text(json.dumps({
    "about": "SCAG 2024 zoning codes (ZN24_SCAG) parsed from the Zoning_poly_OR layer metadata. "
             "Metadata says: 2024 zoning at the parcel level, updated as of October 2025.",
    "source_id": "scag_zoning", "checked": "2026-11-07", "codes": codes}, indent=1))
print(f"  SCAG zoning legend: {len(codes)} codes")
