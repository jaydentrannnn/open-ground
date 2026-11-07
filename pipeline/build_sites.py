"""Merge raw layers into data/processed/sites.geojson (the shared contract).   OWNER: Builder A
Run after fetch_sites.py:  python pipeline/build_sites.py --limit 40

For each site: point-in-polygon checks against hazard / transit layers (server-side, cached,
one request per site per layer). Anything not checked stays null = "unknown" in the UI.
TODO (ranked): 1) SCAG zoning join  2) surplus notices CSV join  3) worship proxy match by distance
4) est_homes from capacity fields  5) tract_id via Census geocoder or tract polygons.
"""
import argparse
import json

from common import RAW, arcgis_point_hits, write_json

LAYERS = {
    "in_flood_zone": "https://www.ocgis.com/arcpub/rest/services/Map_Layers/Floodplains/MapServer/0",
    "in_fire_zone": "https://www.ocgis.com/arcpub/rest/services/Map_Layers/Fire_Hazard_Severity_Zones_LRA/MapServer/0",
    "in_hqta": "https://caltrans-gis.dot.ca.gov/arcgis/rest/services/CHrailroad/CA_HQ_Transit_Areas/FeatureServer/0",
}

ap = argparse.ArgumentParser()
ap.add_argument("--limit", type=int, default=40, help="keep it small: be kind to public servers")
args = ap.parse_args()

he = json.loads((RAW / "he_sites.geojson").read_text())["features"][: args.limit]
out = []
for i, f in enumerate(he):
    p = f.get("properties", {})
    g = f.get("geometry")
    ring = g["coordinates"][0] if g and g["type"] == "Polygon" else (g["coordinates"][0][0] if g else None)
    if not ring:
        continue
    lon = sum(x[0] for x in ring) / len(ring)
    lat = sum(x[1] for x in ring) / len(ring)
    props = {
        "id": f"HE-{i:03d}", "name": f"Housing-element site {p.get('Assessor_Parcel_Number') or i}",
        "city": p.get("Jurisdiction"), "apn": p.get("Assessor_Parcel_Number"), "address": None,
        "acres": p.get("ACRES") or p.get("Acres"), "owner_type_proxy": None,
        "housing_element_site": True, "surplus_notice": None, "zoning_local": None, "zoning_scag": None,
        "in_historic_district": None, "in_fault_zone": None, "tract_id": None, "est_homes": None,
        "land_cost_mode": None, "land_cost_per_home": None,
        "source_ids": ["scag_he_sites", "oc_fhsz_lra", "caltrans_hqta"], "synthetic": False,
        "raw": {k: v for k, v in p.items() if v is not None},
    }
    for key, url in LAYERS.items():
        props[key] = arcgis_point_hits(url, lon, lat)
    out.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]}, "properties": props})
    print(i, props["apn"], {k: props[k] for k in LAYERS})

write_json("sites.geojson", {"type": "FeatureCollection", "features": out})
