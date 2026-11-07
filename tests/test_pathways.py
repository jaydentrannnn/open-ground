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


def test_religious_land_use_is_a_lead_not_a_pass():
    site = {"owner_type_proxy": "faith_proxy", "raw": {"existing_use": {"label": "Religious Facilities", "religious": True}}}
    own = pathways.sb4(site)[0]
    assert own["result"] == "unknown" and "Religious Facilities" in own["why"]


def test_under_construction_flags_stale_housing_element_site():
    site = {"housing_element_site": True, "raw": {"existing_use": {"label": "Under Construction",
                                                                   "under_construction": True}}}
    assert pathways.evaluate(site)["HE"]["verdict"] == "no"


def test_area_weights_are_tagged_assumption_and_note_matches():
    sc = area.score({"rent_burden_pct": 50})
    assert "not from a source" in sc["assumption"]
    w = area.DEFAULT_WEIGHTS
    for key, pct in [("rent_burden_pct", "30%"), ("overcrowded_pct", "20%"), ("eligible_households", "20%"),
                     ("low_wage_jobs", "20%"), ("opportunity_score", "10%")]:
        assert f"{round(w[key] * 100)}%" == pct and pct in area.ASSUMPTION_NOTE


def test_shra_multifamily_small_lot_can_pass_zone_and_size():
    tests = pathways.shra({"acres": 0.5, "zoning_scag": "1120 Multi-Family Residential", "city": "Anaheim"})
    by = {t["test"].split(" (")[0]: t["result"] for t in tests}
    assert by["Lot under 5 acres"] == "pass" and by["In an incorporated city or large urban county"] == "pass"
    assert tests[1]["result"] == "pass"


def test_shra_fire_never_passes_on_very_high_only_maps():
    # fact sheet says 'fire hazard zones' with no severity; we only map Very High, so absence is unknown
    fire = next(t for t in pathways.shra({"in_fire_zone": False}) if "fire" in t["test"])
    assert fire["result"] == "unknown"


def test_shra_single_family_is_unknown_not_pass():
    zone = pathways.shra({"zoning_scag": "1110 Single Family Residential"})[1]
    assert zone["result"] == "unknown" and "66499.41" in zone["why"]


def test_shra_industrial_and_big_lots_fail():
    ev = pathways.evaluate({"acres": 6, "zoning_scag": "1310 Light Industrial", "city": "Brea"})
    assert ev["SHRA"]["verdict"] == "no"


def test_fault_zone_test_uses_ap_layer():
    hit = next(t for t in pathways.sb4({"in_fault_zone": True, "raw": {"fault_ap": [{"quad": "Seal Beach", "pct_of_site": 12.0}]}})
               if "fault" in t["test"])
    miss = next(t for t in pathways.sb4({"in_fault_zone": False}) if "fault" in t["test"])
    none = next(t for t in pathways.sb4({}) if "fault" in t["test"])
    assert (hit["result"], miss["result"], none["result"]) == ("fail", "pass", "unknown")
    assert "Alquist-Priolo" in miss["why"]


def test_archived_surplus_notice_is_maybe_not_yes():
    site = {"surplus_notice": True, "raw": {"sla": {"status": "Archive"}}}
    assert pathways.evaluate(site)["SLA"]["verdict"] == "maybe"
    site["raw"]["sla"]["status"] = "Active"
    assert pathways.evaluate(site)["SLA"]["verdict"] == "yes"


def test_ab2011_commercial_zone_passes_zone_test_but_never_yes():
    ev = pathways.evaluate({"zoning_scag": "1220 Retail Stores and Commercial Services",
                            "raw": {"existing_use": {"code": "1220", "label": "Retail Stores and Commercial Services"}}})
    assert ev["AB2011"]["tests"][0]["result"] == "pass" and ev["AB2011"]["verdict"] == "maybe"


def test_ab2011_residential_zone_or_industrial_use_fails():
    assert pathways.evaluate({"zoning_scag": "1120 Multi-Family Residential"})["AB2011"]["verdict"] == "no"
    ev = pathways.evaluate({"zoning_scag": "1200 Commercial and Services",
                            "raw": {"existing_use": {"code": "1310", "label": "Light Industrial"}}})
    assert ev["AB2011"]["verdict"] == "no"


def test_ab2011_mixed_use_is_unknown():
    assert pathways.ab2011({"zoning_scag": "1600 Mixed Residential and Commercial"})[0]["result"] == "unknown"


def test_edge_sliver_is_unknown_with_reason_never_pass():
    site = {"in_flood_zone": None, "in_fire_zone": None,
            "raw": {"flood_checked": True, "flood_sfha": [{"zone": "AE", "pct_of_site": 0.2}],
                    "floodway": [{"zone": "AE", "pct_of_site": 0.1}],
                    "fire_very_high": [{"layer": "LRA 2025 (CAL FIRE)", "pct_of_site": 0.5}],
                    "edge_sliver": {"flood_sfha": True, "floodway": True, "fire": True}, "sliver_threshold_pct": 1.0}}
    tests = pathways.sb4(site)
    hz = [t for t in tests if any(k in t["test"].lower() for k in ("flood", "floodway", "fire"))]
    assert len(hz) == 3 and all(t["result"] == "unknown" and "Edge sliver" in t["why"] and "ASSUMPTION" in t["why"]
                                for t in hz)
    assert pathways.evaluate(site)["SB4"]["verdict"] != "yes"


def test_real_overlap_still_fails():
    site = {"in_flood_zone": True, "raw": {"flood_checked": True, "flood_sfha": [{"zone": "AE", "pct_of_site": 12.0}],
                                           "floodway": [], "edge_sliver": {}}}
    assert pathways.sb4(site)[3]["result"] == "fail"
