"""core/parcels.py: the map highlight is the real parcel outline or nothing, never a made-up shape. No network."""
from core import parcels, ui

SQUARE = {"type": "Polygon", "coordinates": [[[-117.9, 33.7], [-117.8, 33.7], [-117.8, 33.8], [-117.9, 33.7]]]}


class _Resp:
    def __init__(self, data, status_ok=True):
        self._data, self._ok = data, status_ok

    def raise_for_status(self):
        if not self._ok:
            raise RuntimeError("HTTP 500")

    def json(self):
        return self._data


def test_where_clause_uses_pid24_then_apn_digits_only():
    assert parcels.where_clause({"id": "HE-0590001704423"}) == "PID24='0590001704423'"
    assert parcels.where_clause({"id": "SLA-X-1", "apn": "017-044-23"}) == "APN24='01704423'"
    assert parcels.where_clause({"id": "HE-123", "apn": "1' OR '1'='1"}) is None  # no digits-only APN: no query
    assert parcels.where_clause({"id": "c"}) is None


def test_outline_returns_the_polygon():
    got = parcels.outline({"id": "HE-0590001704423"}, get=lambda *a, **k: _Resp({"features": [{"geometry": SQUARE}]}))
    assert got == SQUARE


def test_outline_is_none_on_error_empty_or_synthetic():
    def boom(*a, **k):
        raise TimeoutError
    site = {"id": "HE-0590001704423"}
    assert parcels.outline(site, get=boom) is None
    assert parcels.outline(site, get=lambda *a, **k: _Resp({"error": {"code": 400}})) is None
    assert parcels.outline(site, get=lambda *a, **k: _Resp({"features": []})) is None
    assert parcels.outline(site, get=lambda *a, **k: _Resp({}, status_ok=False)) is None
    assert parcels.outline({**site, "synthetic": True}, get=lambda *a, **k: _Resp({"features": [{"geometry": SQUARE}]})) is None


def test_outlines_one_request_maps_back_to_site_ids():
    calls = []
    sites = [{"id": "HE-0590001704423"}, {"id": "SLA-1-2", "apn": "123-456-78"}, {"id": "HE-0590009999999"},
             {"id": "c"}]

    def fake(url, params, timeout):
        calls.append(params["where"])
        return _Resp({"features": [{"geometry": SQUARE, "properties": {"PID24": "0590001704423", "APN24": "01704423"}},
                                   {"geometry": SQUARE, "properties": {"PID24": "0590012345678", "APN24": "12345678"}}]})
    got = parcels.outlines(sites, get=fake)
    assert len(calls) == 1 and " OR " in calls[0]
    assert got == {"HE-0590001704423": SQUARE, "SLA-1-2": SQUARE, "HE-0590009999999": None}  # no row = None, "c" skipped
    assert parcels.outlines(sites, get=lambda *a, **k: _Resp({"error": {}})) is None  # failed request: nothing known
    assert parcels.outlines([{"id": "c"}]) == {}


def test_bounds_for_polygon_and_multipolygon():
    assert parcels.bounds(SQUARE) == [[33.7, -117.9], [33.8, -117.8]]
    multi = {"type": "MultiPolygon", "coordinates": [SQUARE["coordinates"], [[[-118.0, 33.6], [-117.95, 33.6],
                                                                              [-118.0, 33.65], [-118.0, 33.6]]]]}
    assert parcels.bounds(multi) == [[33.6, -118.0], [33.8, -117.8]]


def test_rank_color_is_darker_for_higher_rank():
    shades = [ui.rank_color(n, 50) for n in (0, 12, 25, 37, 49)]
    assert shades == list(ui.RANK_RAMP)
    assert ui.rank_color(0, 1) == ui.RANK_RAMP[0] and ui.rank_color(3, 0) == ui.RANK_RAMP[-1]
