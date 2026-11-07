"""Polite HTTP with a disk cache. Be kind to public servers (event rule): cache, sleep, retry once."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RAW.mkdir(parents=True, exist_ok=True)
HEADERS = {"User-Agent": "open-ground-hackathon-prototype"}


def get(url: str, params: dict | None = None, as_json: bool = True, sleep: float = 0.4, timeout: int = 60):
    key = hashlib.sha1((url + json.dumps(params or {}, sort_keys=True)).encode()).hexdigest()[:16]
    cache = RAW / f"{key}.{'json' if as_json else 'bin'}"
    if cache.exists():
        return json.loads(cache.read_text()) if as_json else cache.read_bytes()
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


def write_json(name: str, obj) -> Path:
    p = PROCESSED / name
    p.write_text(json.dumps(obj, indent=1))
    print("wrote", p)
    return p
