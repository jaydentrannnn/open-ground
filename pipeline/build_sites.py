"""Merge raw layers into data/processed/sites.geojson (the shared contract).   OWNER: Builder A
Needs: pip install -r pipeline/requirements.txt   (shapely: pipeline only, the app does not need it)
Run (from repo root, after fetch_sites.py and fetch_layers.py):
    python pipeline/build_sites.py            # every site in data/raw/he_sites.geojson
    python pipeline/build_sites.py --limit 40 # quick test

Per site:
  - zoning, acres check, slope, census tract: SCAG Zoning_poly_OR joined on PID24 (same parcel id as the
    housing-element layer). ~15 cached requests for all of OC. GEOID20 is a 2020 census BLOCK id; its
    first 11 digits are the tract, matching tracts.json keys.
  - hazards / transit: the parcel OUTLINE is tested against each downloaded layer (any overlap counts,
    and the overlap share is recorded so a sliver is visible in the UI). No per-site requests.
  - SB 4 lead: an OpenStreetMap place of worship inside the parcel -> owner_type_proxy "faith_proxy".
A layer that failed to download leaves its field null = "unknown". Nothing is guessed.
Extra detail (not in the contract) goes under properties["raw"].
"""
import argparse
import json

from shapely.geometry import shape
from shapely.strtree import STRtree

from common import PROCESSED, RAW, get, write_json

ZONING = "https://maps.scag.ca.gov/scaggis/rest/services/LDX/Zoning_poly_OR/MapServer/0"
SQM_PER_ACRE = 4046.8564224  # international acre in square meters (unit definition)

ap = argparse.ArgumentParser()
ap.add_argument("--limit", type=int, default=None)
args = ap.parse_args()

he = json.loads((RAW / "he_sites.geojson").read_text())["features"][: args.limit]
legend = json.loads((PROCESSED / "scag_zoning_codes.json").read_text())["codes"]


# ---------- zoning join on PID24 (attribute query, no geometry) ----------
pids = sorted({f["properties"].get("PID24") for f in he if f["properties"].get("PID24")})
zoning = {}
for i in range(0, len(pids), 150):
    chunk = ",".join(f"'{p}'" for p in pids[i:i + 150])
    d = get(f"{ZONING}/query", {"where": f"PID24 IN ({chunk})", "returnGeometry": "false", "f": "json",
                                "outFields": "PID24,ACRES,SLOPE,GEOID20,ZN24_CITY,ZN24_SCAG,YEAR_ZN"})
    for feat in d.get("features", []):
        a = feat["attributes"]
        zoning.setdefault(a["PID24"], a)  # first row wins if a parcel is stacked
print(f"zoning matched for {len(zoning)} of {len(pids)} parcels")


# ---------- local layers ----------
def load_layer(name):
    p = RAW / f"layer_{name}.geojson"
    if not p.exists():
        print(f"  layer {name} missing -> its field stays unknown")
        return None
    feats = [f for f in json.loads(p.read_text())["features"] if f.get("geometry")]
    geoms = [shape(f["geometry"]) for f in feats]
    geoms = [g if g.geom_type == "Point" else g.buffer(0) for g in geoms]  # repair polygons; buffer(0) empties points
    return {"tree": STRtree(geoms), "geoms": geoms, "props": [f.get("properties", {}) for f in feats]}


L = {n: load_layer(n) for n in ("flood", "fire_lra25", "fire_lra", "fire_sra", "hqta", "worship")}


def hits(layer, geom):
    """[(props, share_of_site_overlapped)] for every layer feature touching the site."""
    if layer is None:
        return None
    out = []
    for idx in layer["tree"].query(geom, predicate="intersects"):
        g = layer["geoms"][idx]
        share = geom.intersection(g).area / geom.area if geom.area and g.geom_type != "Point" else None
        out.append((layer["props"][idx], share))
    return out


def any_hit(layer, geom, keep=lambda p: True):
    h = hits(layer, geom)
    if h is None:
        return None, []
    h = [(p, s) for p, s in h if keep(p)]
    return bool(h), h


def pct(s):
    return None if s is None else round(100 * s, 1)


out = []
for f in he:
    p, g = f["properties"], f.get("geometry")
    if not g:
        continue
    site = shape(g).buffer(0)
    pt = site.representative_point()
    z = zoning.get(p.get("PID24"), {})
    code = (z.get("ZN24_SCAG") or "").strip()
    geoid = z.get("GEOID20") or ""

    sfha, sfha_h = any_hit(L["flood"], site, lambda q: q.get("SFHA_TF") == "T")
    _, fway_h = any_hit(L["flood"], site, lambda q: "FLOODWAY" in (q.get("ZONE_SUBTY") or "").upper())
    lra25, lra25_h = any_hit(L["fire_lra25"], site)  # CAL FIRE LRA map dated 2025-03-24 (primary)
    lra, lra_h = any_hit(L["fire_lra"], site)        # OC copy, vintage unknown (kept: any hit flags)
    sra, sra_h = any_hit(L["fire_sra"], site)        # CAL FIRE SRA 2007 (outdated)
    fire = True if (lra25 or lra or sra) else (None if None in (lra25, sra) else False)
    hqta, _ = any_hit(L["hqta"], site)
    worship_h = hits(L["worship"], site)

    juris = (p.get("Jurisdiction") or "").title()
    cap = p.get("Total_HE_Capacity")
    props = {
        "id": f"HE-{p.get('PID24') or p.get('OBJECTID')}",
        "name": f"{juris} · APN {p.get('Assessor_Parcel_Number') or p.get('APN24') or 'unknown'}",
        "city": "County of Orange" if juris == "Orange County" else juris,
        "apn": p.get("Assessor_Parcel_Number") or p.get("APN24"),
        "address": None,
        "acres": round(p["Shape.STArea()"] / SQM_PER_ACRE, 3) if p.get("Shape.STArea()") else None,
        "owner_type_proxy": "faith_proxy" if worship_h else None,
        "housing_element_site": True,
        "surplus_notice": None,
        "zoning_local": z.get("ZN24_CITY") or None,
        "zoning_scag": f"{code} {legend.get(code, 'code not in SCAG legend')}" if code else None,
        "in_fire_zone": fire,
        "in_flood_zone": sfha,
        "in_historic_district": None,
        "in_fault_zone": None,
        "in_hqta": hqta,
        "tract_id": geoid[:11] if len(geoid) == 15 else None,
        "est_homes": int(cap) if cap is not None else None,
        "land_cost_mode": None,
        "land_cost_per_home": None,
        "source_ids": ["scag_he_sites", "scag_zoning", "oc_floodplains", "calfire_fhsz_lra_2025", "oc_fhsz_lra", "calfire_fhsz_sra_2007",
                       "caltrans_hqta"] + (["osm_worship"] if worship_h else []),
        "synthetic": False,
        "raw": {
            "he_capacity": {k: p.get(f"{k}_HE_Capacity") for k in ("Low_Income", "Moderate_Income",
                                                                    "Above_Moderate_Income", "Total")},
            "he_year": p.get("YEAR"),
            "zoning_acres": z.get("ACRES"), "slope": z.get("SLOPE"),
            "flood_sfha": [{"zone": q.get("FLD_ZONE"), "pct_of_site": pct(s)} for q, s in sfha_h],
            "floodway": [{"zone": q.get("FLD_ZONE"), "pct_of_site": pct(s)} for q, s in fway_h],
            "fire_very_high": [{"layer": "LRA 2025 (CAL FIRE)", "pct_of_site": pct(s)} for _, s in lra25_h]
                              + [{"layer": "LRA (OC copy, vintage unknown)", "pct_of_site": pct(s)} for _, s in lra_h]
                              + [{"layer": "SRA 2007 (CAL FIRE)", "pct_of_site": pct(s)} for _, s in sra_h],
            "worship_osm": [{"osm_id": q.get("osm_id"), "name": q.get("name")} for q, _ in (worship_h or [])],
        },
    }
    out.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(pt.x, 6), round(pt.y, 6)]},
                "properties": props})

write_json("sites.geojson", {"type": "FeatureCollection",
                             "about": "REAL housing-element sites (SCAG, Orange County) with zoning and hazard checks. "
                                      "null = unknown. Built by pipeline/build_sites.py.",
                             "built": "2026-11-07", "features": out}, indent=None)
n = len(out)
for k in ("in_flood_zone", "in_fire_zone", "in_hqta", "tract_id", "zoning_scag", "owner_type_proxy"):
    vals = [o["properties"][k] for o in out]
    print(f"  {k:18s} true/set={sum(1 for v in vals if v)}  unknown={sum(1 for v in vals if v is None)}  of {n}")
