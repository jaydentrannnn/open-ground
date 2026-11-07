"""pipeline/common.py: a service error or a partial download must never look like "no hazard"."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
import common  # noqa: E402


class _Resp:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


@pytest.fixture
def no_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(common, "RAW", tmp_path)
    monkeypatch.setattr(common.time, "sleep", lambda s: None)
    return tmp_path


def test_get_raises_on_arcgis_error_and_does_not_cache(no_cache, monkeypatch):
    monkeypatch.setattr(common.requests, "get", lambda *a, **k: _Resp({"error": {"code": 400}}))
    with pytest.raises(RuntimeError):
        common.get("https://example.invalid/layer/query", {"f": "json"})
    assert list(no_cache.iterdir()) == []


def test_get_drops_a_cached_error_and_refetches(no_cache, monkeypatch):
    url, params = "https://example.invalid/x", {"a": 1}
    # an error file left in the cache by an older version of get(), at the exact path get() would read
    key = common.hashlib.sha1((url + common.json.dumps(params, sort_keys=True)).encode()).hexdigest()[:16]
    stale = no_cache / f"{key}.json"
    stale.write_text(common.json.dumps({"error": {"code": 500}}))
    monkeypatch.setattr(common.requests, "get", lambda *a, **k: _Resp({"objectIds": [1]}))
    assert common.get(url, params) == {"objectIds": [1]}  # refetched, not the cached error
    assert common.json.loads(stale.read_text()) == {"objectIds": [1]}  # and the good answer replaced it


def test_get_returns_a_good_cached_answer_without_a_request(no_cache, monkeypatch):
    url, params = "https://example.invalid/y", {"b": 2}
    key = common.hashlib.sha1((url + common.json.dumps(params, sort_keys=True)).encode()).hexdigest()[:16]
    (no_cache / f"{key}.json").write_text(common.json.dumps({"count": 3}))

    def no_network(*a, **k):
        raise AssertionError("should have used the cache")
    monkeypatch.setattr(common.requests, "get", no_network)
    assert common.get(url, params) == {"count": 3}


def test_fetch_all_rejects_partial_downloads(monkeypatch):
    def fake_get(url, params, **kw):
        if params.get("returnIdsOnly"):
            return {"objectIds": [1, 2, 3]}
        return {"features": [{"id": 1}]}  # 1 of 3
    monkeypatch.setattr(common, "get", fake_get)
    with pytest.raises(RuntimeError, match="incomplete"):
        common.fetch_all("https://example.invalid/layer")


def test_fetch_all_rejects_missing_ids(monkeypatch):
    monkeypatch.setattr(common, "get", lambda url, params, **kw: {"something": "else"})
    with pytest.raises(RuntimeError):
        common.fetch_all("https://example.invalid/layer")


def test_fetch_all_empty_layer_is_fine(monkeypatch):
    monkeypatch.setattr(common, "get", lambda url, params, **kw: {"objectIds": None})
    assert common.fetch_all("https://example.invalid/layer") == []
