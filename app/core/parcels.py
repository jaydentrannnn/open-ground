"""Real parcel outlines for the map highlight, from SCAG's public zoning-parcel layer (no API key).

OWNER: Builder C (frontend). One small request per site the user opens; the page caches the answer.
If the layer fails or has no row, outline() returns None and the map shows a ring at the point with
"outline unavailable". We never draw a made-up boundary (event rule: never invent a parcel fact).
Source id: scag_zoning (data/sources.json). Query by PID24 or APN24 checked against the layer 2026-11-07.
"""
from __future__ import annotations

import requests

LAYER = "https://maps.scag.ca.gov/scaggis/rest/services/LDX/Zoning_poly_OR/MapServer/0/query"
SOURCE_ID = "scag_zoning"


def where_clause(site: dict) -> str | None:
    """ArcGIS where clause for this site's parcel, built from digits only (no injection), or None."""
    sid = site.get("id") or ""
    pid = sid[3:] if sid.startswith("HE-") else ""
    if pid.isdigit() and len(pid) == 13 and pid.startswith("059"):  # PID24 = OC county code 059 + parcel digits
        return f"PID24='{pid}'"
    digits = "".join(ch for ch in (site.get("apn") or "") if ch.isdigit())
    return f"APN24='{digits}'" if len(digits) == 8 else None


def outline(site: dict, get=requests.get, timeout: float = 6) -> dict | None:
    """GeoJSON Polygon / MultiPolygon of the parcel, or None when unknown. Never raises."""
    where = where_clause(site)
    if where is None or site.get("synthetic"):
        return None
    try:
        r = get(LAYER, params={"where": where, "outSR": 4326, "geometryPrecision": 6, "f": "geojson",
                               "outFields": "PID24,APN24"}, timeout=timeout)
        r.raise_for_status()
        d = r.json()
    except Exception:  # network, HTTP or JSON error: the outline is unknown, the app keeps working
        return None
    if not isinstance(d, dict) or "error" in d:
        return None
    for f in d.get("features") or []:
        g = f.get("geometry") or {}
        if g.get("type") in ("Polygon", "MultiPolygon") and g.get("coordinates"):
            return g
    return None


def outlines(sites: list[dict], get=requests.get, timeout: float = 10) -> dict | None:
    """Outlines for many sites in ONE request (polite). Returns {site_id: geometry or None (no parcel row)}, or None
    when the request itself failed (then nothing is known and the caller may retry later)."""
    keys = {}  # where-value -> site id
    for s in sites:
        w = where_clause(s)
        if w and not s.get("synthetic"):
            keys[w] = s["id"]
    if not keys:
        return {}
    try:
        r = get(LAYER, params={"where": " OR ".join(keys), "outSR": 4326, "geometryPrecision": 6, "f": "geojson",
                               "outFields": "PID24,APN24"}, timeout=timeout)
        r.raise_for_status()
        d = r.json()
    except Exception:
        return None
    if not isinstance(d, dict) or "error" in d:
        return None
    found = {sid: None for sid in keys.values()}
    for f in d.get("features") or []:
        g, p = f.get("geometry") or {}, f.get("properties") or {}
        if g.get("type") not in ("Polygon", "MultiPolygon") or not g.get("coordinates"):
            continue
        for w in (f"PID24='{p.get('PID24')}'", f"APN24='{p.get('APN24')}'"):
            if w in keys and found[keys[w]] is None:
                found[keys[w]] = g
    return found


def bounds(geom: dict) -> list[list[float]]:
    """[[south, west], [north, east]] of a GeoJSON Polygon / MultiPolygon, for folium fit_bounds."""
    rings = geom["coordinates"] if geom["type"] == "Polygon" else [r for poly in geom["coordinates"] for r in poly]
    pts = [p for ring in rings for p in ring]
    lons, lats = [p[0] for p in pts], [p[1] for p in pts]
    return [[min(lats), min(lons)], [max(lats), max(lons)]]
