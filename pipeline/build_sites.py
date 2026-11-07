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
  - Surplus Land Act notices (fetch_surplus.py): housing-element sites get surplus_notice by APN match, and
    OC surplus parcels NOT on a housing-element list are added as their own sites (outline from SCAG zoning
    by APN; the notice's point if no match). Includes Santa Ana, which the housing-element layer lacks.
A layer that failed to download leaves its field null = "unknown". Nothing is guessed.
Extra detail (not in the contract) goes under properties["raw"].
"""
import argparse
import json
import re
from datetime import datetime

from shapely.geometry import Point, shape
from shapely.strtree import STRtree

from common import PROCESSED, RAW, get, write_json

ZONING = "https://maps.scag.ca.gov/scaggis/rest/services/LDX/Zoning_poly_OR/MapServer/0"
SQM_PER_ACRE = 4046.8564224  # international acre in square meters (unit definition)

ap = argparse.ArgumentParser()
ap.add_argument("--limit", type=int, default=None)
args = ap.parse_args()

he = json.loads((RAW / "he_sites.geojson").read_text())["features"][: args.limit]
legend = json.loads((PROCESSED / "scag_zoning_codes.json").read_text())["codes"]
sla_path = RAW / "sla_oc.json"
sla_rows = json.loads(sla_path.read_text()) if sla_path.exists() else None  # None = not checked
if sla_rows is None:
    print("  sla_oc.json missing -> surplus_notice stays unknown (run fetch_surplus.py)")


def apn_digits(apn):
    """'089-010-34' -> '08901034' (SCAG APN24 format). First APN if a field lists several."""
    m = re.search(r"\d{3}-?\d{3}-?\d{2}", apn or "")
    return m.group().replace("-", "") if m else None


def notice_date(r):
    try:
        return datetime.strptime(r.get("Date Notice Issued") or "", "%m-%d-%Y")
    except ValueError:
        return datetime.min


sla_by_apn = {}
for r in sorted(sla_rows or [], key=notice_date):  # latest notice per parcel wins
    if apn_digits(r.get("APN")):
        sla_by_apn[apn_digits(r["APN"])] = r


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
print(f"zoning matched for {len(zoning)} of {len(pids)} housing-element parcels")

# surplus parcels not on a housing-element list: zoning row + parcel outline by APN24
he_apns = {apn_digits(f["properties"].get("Assessor_Parcel_Number")) or f["properties"].get("APN24") for f in he}
sla_only = {a: r for a, r in sla_by_apn.items() if a not in he_apns}
sla_zoning = {}
apns = sorted(sla_only)
for i in range(0, len(apns), 100):
    chunk = ",".join(f"'{a}'" for a in apns[i:i + 100])
    d = get(f"{ZONING}/query", {"where": f"APN24 IN ({chunk})", "outSR": 4326, "geometryPrecision": 6, "f": "geojson",
                                "outFields": "APN24,PID24,ACRES,SLOPE,GEOID20,ZN24_CITY,ZN24_SCAG,YEAR_ZN"})
    for feat in d.get("features", []):
        sla_zoning.setdefault(feat["properties"]["APN24"], feat)
print(f"surplus notices in OC: {len(sla_rows or [])}; parcels {len(sla_by_apn)}; not on a housing-element list "
      f"{len(sla_only)}; parcel outline found {len(sla_zoning)}")


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


FIRE_SRC = ["oc_floodplains", "calfire_fhsz_lra_2025", "oc_fhsz_lra", "calfire_fhsz_sra_2007", "caltrans_hqta"]


def checks(site, use_worship=True):
    """Hazard / transit / worship checks on one parcel outline (or point)."""
    sfha, sfha_h = any_hit(L["flood"], site, lambda q: q.get("SFHA_TF") == "T")
    _, fway_h = any_hit(L["flood"], site, lambda q: "FLOODWAY" in (q.get("ZONE_SUBTY") or "").upper())
    lra25, lra25_h = any_hit(L["fire_lra25"], site)  # CAL FIRE LRA map dated 2025-03-24 (primary)
    lra, lra_h = any_hit(L["fire_lra"], site)        # OC copy, vintage unknown (kept: any hit flags)
    sra, sra_h = any_hit(L["fire_sra"], site)        # CAL FIRE SRA 2007 (outdated)
    hqta, _ = any_hit(L["hqta"], site)
    worship_h = hits(L["worship"], site) if use_worship else []
    return {
        "in_fire_zone": True if (lra25 or lra or sra) else (None if None in (lra25, sra) else False),
        "in_flood_zone": sfha, "in_hqta": hqta, "_worship": worship_h or [],
        "raw": {
            "flood_sfha": [{"zone": q.get("FLD_ZONE"), "pct_of_site": pct(s)} for q, s in sfha_h],
            "floodway": [{"zone": q.get("FLD_ZONE"), "pct_of_site": pct(s)} for q, s in fway_h],
            "fire_very_high": [{"layer": "LRA 2025 (CAL FIRE)", "pct_of_site": pct(s)} for _, s in lra25_h]
                              + [{"layer": "LRA (OC copy, vintage unknown)", "pct_of_site": pct(s)} for _, s in lra_h]
                              + [{"layer": "SRA 2007 (CAL FIRE)", "pct_of_site": pct(s)} for _, s in sra_h],
            "worship_osm": [{"osm_id": q.get("osm_id"), "name": q.get("name")} for q, _ in (worship_h or [])],
        },
    }


def zoning_fields(z):
    code = (z.get("ZN24_SCAG") or "").strip()
    geoid = z.get("GEOID20") or ""
    return {"zoning_local": z.get("ZN24_CITY") or None,
            "zoning_scag": f"{code} {legend.get(code, 'code not in SCAG legend')}" if code else None,
            "tract_id": geoid[:11] if len(geoid) == 15 else None}


def sla_raw(r):
    return {"case": r.get("Parent Case"), "agency": r.get("Local Agency"), "agency_type": r.get("Local Agency Type"),
            "issued": r.get("Date Notice Issued"), "interest_due": r.get("NOA Due Date"), "status": r.get("NOA Status"),
            "link": r.get("Notice Website Link"), "existing_use": r.get("Existing Use/Vacancy"),
            "plan_zoning_text": r.get("General Plan/Zoning"), "size_text": r.get("Parcel Size (Gross Acres)")}


def feature(geom, props):
    pt = geom.representative_point()
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(pt.x, 6), round(pt.y, 6)]},
            "properties": props}


out = []
# ---------- housing-element sites ----------
for f in he:
    p, g = f["properties"], f.get("geometry")
    if not g:
        continue
    site = shape(g).buffer(0)
    z = zoning.get(p.get("PID24"), {})
    c = checks(site)
    apn = p.get("Assessor_Parcel_Number") or p.get("APN24")
    notice = sla_by_apn.get(apn_digits(apn) or p.get("APN24"))
    juris = (p.get("Jurisdiction") or "").title()
    cap = p.get("Total_HE_Capacity")
    props = {
        "id": f"HE-{p.get('PID24') or p.get('OBJECTID')}",
        "name": f"{juris} · APN {apn or 'unknown'}",
        "city": "County of Orange" if juris == "Orange County" else juris,
        "apn": apn, "address": None,
        "acres": round(p["Shape.STArea()"] / SQM_PER_ACRE, 3) if p.get("Shape.STArea()") else None,
        "owner_type_proxy": "public_surplus" if notice else ("faith_proxy" if c["_worship"] else None),
        "housing_element_site": True,
        "surplus_notice": None if sla_rows is None else bool(notice),
        **zoning_fields(z),
        "in_fire_zone": c["in_fire_zone"], "in_flood_zone": c["in_flood_zone"],
        "in_historic_district": None, "in_fault_zone": None, "in_hqta": c["in_hqta"],
        "est_homes": int(cap) if cap is not None else None,
        "land_cost_mode": None, "land_cost_per_home": None,
        "source_ids": ["scag_he_sites", "scag_zoning", *FIRE_SRC] + (["hcd_sla_notices"] if sla_rows is not None else [])
                      + (["osm_worship"] if c["_worship"] else []),
        "synthetic": False,
        "raw": {"site_source": "housing_element",
                "he_capacity": {k: p.get(f"{k}_HE_Capacity") for k in ("Low_Income", "Moderate_Income",
                                                                        "Above_Moderate_Income", "Total")},
                "he_year": p.get("YEAR"), "zoning_acres": z.get("ACRES"), "slope": z.get("SLOPE"),
                **c["raw"], **({"sla": sla_raw(notice)} if notice else {})},
    }
    out.append(feature(site, props))

# ---------- surplus parcels that are not housing-element sites ----------
for a, r in sorted(sla_only.items()):
    zf = sla_zoning.get(a)
    site = shape(zf["geometry"]).buffer(0) if zf and zf.get("geometry") else Point(r["lon"], r["lat"])
    z = zf["properties"] if zf else {}
    c = checks(site, use_worship=False)  # owner is a public agency: worship proxy does not apply
    occupied_home = "occupied" in (r.get("Existing Use/Vacancy") or "").lower()
    props = {
        "id": f"SLA-{r.get('Parent Case')}-{a}",
        "name": f"{r['City']} · surplus land · APN {r.get('APN')}",
        "city": r["City"], "apn": r.get("APN"),
        "address": None if occupied_home else r.get("Address"),  # don't point the map at an occupied home
        "acres": r.get("acres") if r.get("acres") is not None else z.get("ACRES"),
        "owner_type_proxy": "public_surplus",
        "housing_element_site": False, "surplus_notice": True,
        **zoning_fields(z),
        "in_fire_zone": c["in_fire_zone"], "in_flood_zone": c["in_flood_zone"],
        "in_historic_district": None, "in_fault_zone": None, "in_hqta": c["in_hqta"],
        "est_homes": None, "land_cost_mode": None, "land_cost_per_home": None,
        "source_ids": ["hcd_sla_notices", "scag_zoning", *FIRE_SRC],
        "synthetic": False,
        "raw": {"site_source": "surplus_notice", "outline": "parcel" if zf else "notice point only",
                "zoning_acres": z.get("ACRES"), "slope": z.get("SLOPE"), **c["raw"], "sla": sla_raw(r)},
    }
    out.append(feature(site, props))

write_json("sites.geojson", {"type": "FeatureCollection",
                             "about": "REAL Orange County candidate sites: SCAG housing-element sites plus HCD Surplus "
                                      "Land Act notices, with zoning and hazard checks. null = unknown. "
                                      "Built by pipeline/build_sites.py.",
                             "built": "2026-11-07", "features": out}, indent=None)
n = len(out)
print(f"sites: {n} ({sum(1 for o in out if o['properties']['id'].startswith('SLA'))} surplus-only)")
for k in ("in_flood_zone", "in_fire_zone", "in_hqta", "tract_id", "zoning_scag", "surplus_notice", "owner_type_proxy"):
    vals = [o["properties"][k] for o in out]
    print(f"  {k:18s} true/set={sum(1 for v in vals if v)}  unknown={sum(1 for v in vals if v is None)}  of {n}")
