"""ZIP-level rent lookup (Builder A). Unknown stays unknown; caps and caveats are always shown."""
from core import contracts, zip_rent

DATA = {"zctas": {
    "92701": {"oc_land_share": 1.0, "0": 1500.0, "0_moe": 120.0, "1": 1900.0, "1_moe": 80.0, "2": None, "2_moe": None},
    "92625": {"oc_land_share": 1.0, "0": 3500.0, "0_moe": None, "0_at_least": True},
    "90638": {"oc_land_share": 0.2, "1": 1800.0, "1_moe": 90.0},
}}


def test_empty_and_invalid_zip():
    assert zip_rent.lookup("", 1, DATA)["status"] == "empty"
    assert zip_rent.lookup(None, 1, DATA)["status"] == "empty"
    assert zip_rent.lookup("9270", 1, DATA)["status"] == "invalid"
    assert zip_rent.lookup("92a01", 1, DATA)["status"] == "invalid"


def test_outside_oc_and_missing_value_are_unknown_not_guessed():
    out = zip_rent.lookup("10001", 1, DATA)
    assert out["status"] == "not_found" and out["rent"] is None
    miss = zip_rent.lookup("92701", 2, DATA)
    assert miss["status"] == "no_value" and miss["rent"] is None and "UNKNOWN" in miss["text"]


def test_found_rent_carries_moe_and_caveats():
    out = zip_rent.lookup(" 92701 ", 1, DATA)
    assert out["status"] == "ok" and out["rent"] == 1900.0 and out["moe"] == 80.0
    assert "± $80" in out["text"] and "include utilities" in out["text"] and "2020-2024" in out["text"]


def test_census_cap_is_shown_as_at_least():
    out = zip_rent.lookup("92625", 0, DATA)
    assert out["at_least"] and "or more" in out["text"]


def test_partly_outside_oc_is_flagged():
    assert "Only 20% of this ZIP area is in Orange County" in zip_rent.lookup("90638", 1, DATA)["text"]


def test_real_file_covers_most_oc_zips():
    real = zip_rent.load()
    if not real.get("zctas"):
        return
    z = real["zctas"]
    assert len(z) > 80
    assert sum(1 for v in z.values() if v.get("1") is not None) > 80
    for v in z.values():
        for br in ("0", "1", "2"):
            assert v.get(br) is None or 500 <= v[br] <= 3500
    assert "census_acs_b25031_zcta" in contracts.load_sources()
