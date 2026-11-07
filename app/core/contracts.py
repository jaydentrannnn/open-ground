"""Shared data contract. Every page and the pipeline agree on these shapes.

OWNER: Builder A (Data & Rules). Others may READ; propose changes in team chat first.

Files (all under data/processed/):
  sites.geojson            FeatureCollection of candidate sites (Point or Polygon).
                           Falls back to sites.sample.geojson (SYNTHETIC) until Builder A ships real data.
  tracts.json              {tract_id: {metrics...}}   falls back to tracts.sample.json (SYNTHETIC)
  income_limits_2026.json  HCD 2026 Orange County limits (sourced; verify vs June 23 revision)
  rates.json               Freddie Mac PMMS 30-yr series (sourced)
  programs.json            Gap-closing programs (sourced; funds unconfirmed)
  assumptions.json         Every number we made up, labelled ASSUMPTION
  data/sources.json        Source registry: id -> {title, url, checked, status}

Site properties (null = unknown, never guess):
  id, name, city, apn, address, acres,
  owner_type_proxy: "faith_proxy" | "college_proxy" | "public_surplus" | "private" | null
  housing_element_site: bool | null      (on a city's adopted site inventory)
  surplus_notice: bool | null            (HCD Surplus Land Act notice)
  zoning_local, zoning_scag: str | null
  in_fire_zone, in_flood_zone, in_historic_district, in_fault_zone, in_hqta: bool | null
  tract_id: str | null
  est_homes: int | null
  land_cost_mode: "ground_lease" | "purchase" | "donated" | null
  land_cost_per_home: number | null
  source_ids: [str]
  synthetic: bool                         (True = made up for testing, never shown as real)
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
PROCESSED = DATA / "processed"


def _load(name: str, fallback: str | None = None):
    path = PROCESSED / name
    if not path.exists() and fallback:
        path = PROCESSED / fallback
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_sites() -> list[dict]:
    """Return a flat list of site dicts with lat/lon added from geometry."""
    fc = _load("sites.geojson", fallback="sites.sample.geojson")
    out = []
    for feat in fc.get("features", []):
        props = dict(feat.get("properties", {}))
        lat, lon = _centroid(feat.get("geometry"))
        props["lat"], props["lon"] = lat, lon
        out.append(props)
    return out


def using_sample_sites() -> bool:
    return not (PROCESSED / "sites.geojson").exists()


def load_tracts() -> dict:
    return _load("tracts.json", fallback="tracts.sample.json")


def load_income_limits() -> dict:
    return _load("income_limits_2026.json")


def load_rates() -> dict:
    return _load("rates.json")


def load_programs() -> list[dict]:
    return _load("programs.json")["programs"]


def load_assumptions() -> dict:
    return _load("assumptions.json")


def load_sources() -> dict:
    with open(DATA / "sources.json", encoding="utf-8") as f:
        return json.load(f)


def latest_rate(rates: dict) -> dict:
    """Most recent {date, rate_30yr} point."""
    return sorted(rates["series"], key=lambda p: p["date"])[-1]


def _centroid(geom) -> tuple[float | None, float | None]:
    if not geom:
        return None, None
    t, c = geom.get("type"), geom.get("coordinates")
    if t == "Point":
        return c[1], c[0]
    if t == "Polygon":
        ring = c[0]
    elif t == "MultiPolygon":
        ring = c[0][0]
    else:
        return None, None
    lon = sum(p[0] for p in ring) / len(ring)
    lat = sum(p[1] for p in ring) / len(ring)
    return lat, lon
