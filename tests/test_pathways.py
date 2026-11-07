from core import area, contracts, pathways


def test_unknown_stays_unknown():
    ev = pathways.evaluate({"owner_type_proxy": None})
    assert ev["SB4"]["verdict"] == "maybe"  # never 'yes' without data


def test_proxy_is_never_a_pass():
    tests = pathways.sb4({"owner_type_proxy": "faith_proxy", "in_fire_zone": False, "in_flood_zone": False, "in_fault_zone": False})
    assert tests[0]["result"] == "unknown"


def test_fire_zone_fails_sb4():
    ev = pathways.evaluate({"owner_type_proxy": "faith_proxy", "in_fire_zone": True})
    assert ev["SB4"]["verdict"] == "no"


def test_every_test_cites_a_known_source():
    srcs = contracts.load_sources()
    for s in contracts.load_sites():
        for e in pathways.evaluate(s).values():
            for t in e["tests"]:
                assert t["source"] in srcs, t


def test_area_score_skips_missing():
    sc = area.score({"rent_burden_pct": 50, "eligible_households": None})
    assert "eligible_households" in sc["missing"]
    assert sc["score"] is not None
