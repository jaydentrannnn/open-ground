"""Polite HTTP with a disk cache. Be kind to public servers (event rule): cache, sleep, retry once."""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RAW.mkdir(parents=True, exist_ok=True)
HEADERS = {"User-Agent": "open-ground-hackathon-prototype"}

# Load ROOT/.env (gitignored) into the environment, without a new dependency. Never print values.
_env = ROOT / ".env"
if _env.exists():
    for _line in _env.read_text().splitlines():
        if "=" in _line and not _line.lstrip().startswith("#"):
            _k, _v = _line.split("=", 1)
            if _v.strip():
                os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))


def get(url: str, params: dict | None = None, as_json: bool = True, sleep: float = 0.4, timeout: int = 60):
    key = hashlib.sha1((url + json.dumps(params or {}, sort_keys=True)).encode()).hexdigest()[:16]
    cache = RAW / f"{key}.{'json' if as_json else 'bin'}"
    if cache.exists():
        if not as_json:
            return cache.read_bytes()
        data = json.loads(cache.read_text())
        if isinstance(data, dict) and "error" in data:  # an error cached by an older run: drop it and refetch
            cache.unlink()
        else:
            return data
    for attempt in (1, 2):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            break
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(3)
    time.sleep(sleep)
    if as_json:
        data = r.json()
        # ArcGIS reports errors as HTTP 200 + {"error": {...}}. Never cache or return that as data: a silent empty
        # result would read as "no hazard" downstream. Raising leaves the field unknown (callers catch it).
        if isinstance(data, dict) and "error" in data:
            raise RuntimeError(f"service error from {url}: {data['error']}")
        cache.write_text(json.dumps(data))
        return data
    cache.write_bytes(r.content)
    return r.content


def arcgis_point_hits(layer_url: str, lon: float, lat: float) -> bool | None:
    """Does a point fall inside any feature of an ArcGIS layer? None if the service fails."""
    try:
        d = get(f"{layer_url}/query", {
            "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects", "returnCountOnly": "true", "f": "json"})
        return d.get("count", 0) > 0
    except Exception:
        return None


OC_BBOX = (-118.13, 33.38, -117.41, 33.95)  # lon/lat envelope around Orange County, for layer downloads

# ASSUMPTION (team choice, no source): parcel lines (SCAG/county) and hazard lines (FEMA, CAL FIRE) are drawn by
# different agencies, so boundaries that should only touch often overlap by a few feet. When EVERY overlap with a
# hazard layer covers less than this share of the parcel, we call the result unknown ("edge sliver: check the
# map"), never a pass and never a fail. Overlaps at or above it still count as in the zone.
SLIVER_PCT = 1.0


def edge_sliver_only(overlaps: list[dict], threshold: float = SLIVER_PCT) -> bool:
    """True when there is at least one overlap and every overlap is a measured share under `threshold` percent.
    An overlap with no measured share (e.g. a point-only site) is never treated as a sliver."""
    shares = [o.get("pct_of_site") for o in overlaps or []]
    return bool(shares) and all(s is not None and s < threshold for s in shares)


def fetch_all(layer_url: str, where: str = "1=1", out_fields: str = "*", bbox: tuple | None = None,
              chunk: int = 500) -> list[dict]:
    """Every feature of an ArcGIS layer as GeoJSON (lon/lat). Ids first, then features in chunks:
    works on servers without pagination, and each chunk is cached so a re-run makes no requests."""
    q = {"where": where, "returnIdsOnly": "true", "f": "json"}
    if bbox:
        q.update({"geometry": ",".join(map(str, bbox)), "geometryType": "esriGeometryEnvelope", "inSR": 4326,
                  "spatialRel": "esriSpatialRelIntersects"})
    first = get(f"{layer_url}/query", q)
    if "objectIds" not in first:
        raise RuntimeError(f"no objectIds in response from {layer_url}: layer stays unknown")
    ids = sorted(first["objectIds"] or [])
    feats = []
    for i in range(0, len(ids), chunk):
        d = get(f"{layer_url}/query", {"objectIds": ",".join(map(str, ids[i:i + chunk])), "outFields": out_fields,
                                       "outSR": 4326, "geometryPrecision": 6, "f": "geojson"}, timeout=120)
        if "features" not in d:
            raise RuntimeError(f"no features in response from {layer_url}: layer stays unknown")
        feats += d["features"]
    if len(feats) != len(ids):  # a partial layer would clear sites it never covered
        raise RuntimeError(f"incomplete download from {layer_url}: {len(feats)} of {len(ids)} features")
    print(f"  {layer_url.split('/services/')[-1]}: {len(feats)} features")
    return feats


def scag_legend(layer_url: str) -> dict:
    """{code: label} parsed from a SCAG LDX layer's own metadata page: each legend paragraph reads 'NNNN label'
    once its tags are stripped (some rows split the code and label into separate tags)."""
    import html
    import re
    t = html.unescape(get(f"{layer_url}/metadata", as_json=False).decode("utf-8", "ignore"))
    codes = {}
    for para in re.split(r"</P>", t[t.find("Legend"):], flags=re.I):
        text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", para))).strip()
        m = re.fullmatch(r"(\d{4}) (.+)", text)
        if m:
            codes.setdefault(m.group(1), m.group(2).strip())
    return codes


def attr_join(layer_url: str, field: str, keys, out_fields: str, chunk: int = 150) -> dict:
    """{key: attributes} from an ArcGIS layer by an attribute IN-list (no geometry). First row per key wins."""
    keys, out = sorted({k for k in keys if k}), {}
    for i in range(0, len(keys), chunk):
        where = f"{field} IN ({','.join(repr(str(k)) for k in keys[i:i + chunk])})"
        d = get(f"{layer_url}/query", {"where": where, "returnGeometry": "false", "outFields": out_fields, "f": "json"})
        for feat in d.get("features", []):
            out.setdefault(feat["attributes"][field], feat["attributes"])
    return out


def write_json(name: str, obj, indent: int | None = 1) -> Path:
    p = PROCESSED / name
    p.write_text(json.dumps(obj, indent=indent))
    print("wrote", p)
    return p
