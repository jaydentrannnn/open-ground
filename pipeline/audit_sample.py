"""Spot-audit: re-query the ORIGINAL public sources live for 8 sites and compare with data/processed/sites.geojson.
OWNER: Builder A. Run: python pipeline/audit_sample.py   (~50 requests over 5 servers, 0.6 s apart, no cache)
Sample: the 3 "call first" Garden Grove sites, 2 random sites (seed 7), one flood-flagged, one fire-flagged, one
surplus parcel. Independent checks we did NOT use to build the data: FEMA NFHL (authority) and the Census geocoder.
Prints one JSON line per site: (ours, upstream) pairs."""
import sys, json, random, time, requests
from pathlib import Path
R = str(Path(__file__).resolve().parents[1]); sys.path.insert(0, R + '/app')
from core import contracts
H={"User-Agent": "open-ground-hackathon-prototype"}
def q(url, params, timeout=40):
    for a in (1, 2):
        try:
            r = requests.get(url, params={**params, "f": params.get("f", "json")}, headers=H, timeout=timeout); r.raise_for_status()
            time.sleep(0.6); return r.json()
        except Exception as e:
            if a == 2: return {"_err": str(e)[:80]}
            time.sleep(3)
S = contracts.load_sites(); byapn = {s['apn']: s for s in S}
random.seed(7)
he = [s for s in S if s['id'].startswith('HE')]
sample = [byapn[a] for a in ('098-120-39', '099-173-10', '096-281-13')] + random.sample(he, 2)
sample.append(next(s for s in he if s['in_flood_zone'] and max(x['pct_of_site'] or 0 for x in s['raw']['flood_sfha']) > 50))
sample.append(next(s for s in he if s['in_fire_zone'] and any('2025' in x['layer'] and (x['pct_of_site'] or 0) > 50 for x in s['raw']['fire_very_high'])))
sample.append(next(s for s in S if s['id'].startswith('SLA') and s['raw'].get('outline') == 'parcel' and s['apn'] == '390-382-09'))
SC = "https://maps.scag.ca.gov/scaggis/rest/services/LDX"
pt = lambda s: {"geometry": f"{s['lon']},{s['lat']}", "geometryType": "esriGeometryPoint", "inSR": 4326,
                "spatialRel": "esriSpatialRelIntersects", "returnGeometry": "false"}
rows = []
for s in sample:
    pid = s['id'].split('-', 1)[1] if s['id'].startswith('HE') else None
    apn24 = s['apn'].replace('-', '')
    out = {"site": s['name'], "id": s['id']}
    if pid:
        d = q(f"{SC}/HousingElementSite_poly_scag/MapServer/0/query", {"where": f"PID24='{pid}'", "outFields": "Total_HE_Capacity,Low_Income_HE_Capacity", "returnGeometry": "false"})
        a = (d.get('features') or [{}])[0].get('attributes', {})
        out["capacity"] = (s['est_homes'], a.get('Total_HE_Capacity'), s['raw']['he_capacity']['Low_Income'], a.get('Low_Income_HE_Capacity'))
    w = f"PID24='{pid}'" if pid else f"APN24='{apn24}'"
    d = q(f"{SC}/Zoning_poly_OR/MapServer/0/query", {"where": w, "outFields": "ZN24_SCAG,ZN24_CITY", "returnGeometry": "false"})
    a = (d.get('features') or [{}])[0].get('attributes', {})
    out["zoning"] = ((s['zoning_scag'] or '').split(' ')[0], a.get('ZN24_SCAG'), s['zoning_local'], a.get('ZN24_CITY'))
    d = q(f"{SC}/Existinglanduse_poly_OR/MapServer/0/query", {"where": w, "outFields": "LU24", "returnGeometry": "false"})
    a = (d.get('features') or [{}])[0].get('attributes', {})
    out["land_use"] = ((s['raw'].get('existing_use') or {}).get('code'), a.get('LU24'))
    d = q("https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query", {**pt(s), "outFields": "FLD_ZONE,SFHA_TF"}, timeout=60)
    f = [x['attributes'] for x in d.get('features', [])] if '_err' not in d else d['_err']
    out["flood_ours_vs_FEMA_point"] = (s['in_flood_zone'], f)
    d = q("https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/FHSALRA25_v1_All/FeatureServer/0/query", {**pt(s), "outFields": "FHSZ_Description"})
    out["fire_ours_vs_CALFIRE_point"] = (s['in_fire_zone'], [x['attributes']['FHSZ_Description'] for x in d.get('features', [])] if '_err' not in d else d['_err'])
    d = q("https://geocoding.geo.census.gov/geocoder/geographies/coordinates", {"x": s['lon'], "y": s['lat'], "benchmark": "Public_AR_Current", "vintage": "Census2020_Current", "layers": "Census Tracts", "format": "json", "f": "json"})
    try: g = d['result']['geographies']['Census Tracts'][0]['GEOID']
    except Exception: g = d.get('_err', 'no result')
    out["tract_ours_vs_Census"] = (s['tract_id'], g)
    rows.append(out); print(json.dumps(out))
