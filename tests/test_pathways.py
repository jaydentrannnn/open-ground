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


# --- Builder A: checks tied to the April 2026 HCD fact sheets ---

def test_zone_x_is_not_a_flood_fail():
    # in_flood_zone means FEMA SFHA only (SFHA_TF); Zone X sites come through as False
    tests = pathways.sb4({"in_flood_zone": False, "raw": {"flood_sfha": [], "floodway": []}})
    flood = [t for t in tests if "flood" in t["test"].lower()]
    assert flood and all(t["result"] == "pass" for t in flood)


def test_floodway_unknown_without_data():
    tests = pathways.sb4({"in_flood_zone": False})
    fw = next(t for t in tests if "floodway" in t["test"])
    assert fw["result"] == "unknown"


def test_sb9_zone_from_scag_code():
    sf = pathways.sb9({"zoning_scag": "1110 Single Family Residential"})[0]
    mf = pathways.sb9({"zoning_scag": "1120 Multi-Family Residential"})[0]
    sp = pathways.sb9({"zoning_scag": "7777 Specific Plan"})[0]
    assert (sf["result"], mf["result"], sp["result"]) == ("pass", "fail", "unknown")


def test_sb9_never_yes_from_public_data():
    # tenant history and the 65913.4 land list are not in public data, so SB 9 stays 'maybe' at best
    ev = pathways.evaluate({"zoning_scag": "1110 Single Family Residential", "in_historic_district": False})
    assert ev["SB9"]["verdict"] == "maybe"


def test_sb4_labor_note_has_no_10_home_threshold():
    notes = " ".join(pathways.evaluate({})["SB4"]["notes"])
    assert "every SB 4 project" in notes and "50+" in notes and "10+" not in notes


def test_real_sites_follow_contract():
    sites = contracts.load_sites()
    if contracts.using_sample_sites():
        return
    assert len(sites) > 1000
    for s in sites:
        assert s["synthetic"] is False and s["lat"] and s["lon"]
        assert s["tract_id"] is None or (len(s["tract_id"]) == 11 and s["tract_id"].startswith("06059"))
        assert s["in_flood_zone"] in (True, False, None)


def test_surplus_archive_is_explained_not_hidden():
    site = {"surplus_notice": True, "raw": {"sla": {"agency": "X", "case": "SLA1", "issued": "01-01-2026",
                                                    "status": "Archive"}}}
    t = pathways.surplus_land(site)[0]
    assert t["result"] == "pass" and "more than 60 days" in t["why"]


def test_surplus_sites_carry_no_contact_column():
    for s in contracts.load_sites():
        sla = (s.get("raw") or {}).get("sla") or {}
        assert not any("contact" in k.lower() for k in sla), s["id"]
