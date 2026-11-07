"""Builder mode logic (core/builder.py). OWNER: Builder B."""
import pytest

from core import area, builder, contracts, finance, pathways

CLEAR = {"id": "a", "in_flood_zone": False, "in_fire_zone": False, "in_hqta": True, "est_homes": 8,
         "owner_type_proxy": None, "raw": {"he_capacity": {"Low_Income": 4, "Total": 8}}}
FLOOD = {**CLEAR, "id": "b", "in_flood_zone": True, "owner_type_proxy": "faith_proxy"}
BLANK = {"id": "c"}  # every field unknown, no lat/lon


def _row(site, area_score=None, hp=None):
    return {"id": site["id"], "ready": builder.readiness(site, 9), "area_score": area_score, "homes_per_1m": hp,
            "lower_income": builder.lower_income_homes(site)}


def test_unknown_is_never_a_pass():
    rd = builder.readiness(BLANK, 9)
    assert rd["passed"] == 0
    assert rd["hazard_clear"] is None
    assert all(c["result"] == "unknown" for c in rd["checks"])
    assert "Unknown:" in rd["why"]


def test_hazard_fail_ranks_below_clear_even_with_more_pluses():
    rows = builder.rank([_row(FLOOD), _row(CLEAR), _row(BLANK)])["rows"]
    assert [r["id"] for r in rows] == ["a", "c", "b"]
    assert "Watch: in a FEMA flood zone" in builder.readiness(FLOOD, 9)["why"]


def test_faith_proxy_is_a_lead_not_ownership():
    c = next(c for c in builder.readiness(FLOOD, 9)["checks"] if c["key"] == "land_lead")
    assert c["result"] == "pass" and "not proof of ownership" in c["text"]


def test_sorts_say_when_they_cannot_tell_sites_apart():
    rows = [_row(CLEAR, 50, 4.0), _row(FLOOD, 70, 4.0), _row(BLANK, None, 4.0)]
    assert "same for every site" in builder.rank(rows, "Homes per $1M of gap")["note"]
    area_sorted = builder.rank(rows, "Area benefit")
    assert area_sorted["note"] is None
    assert [r["id"] for r in area_sorted["rows"]] == ["b", "a", "c"]  # unknown last
    assert "unknown for all" in builder.rank([_row(CLEAR), _row(BLANK)], "Area benefit")["note"]


def test_real_sites_rank_and_give_reasons():
    sites = contracts.load_sites()
    tracts = contracts.load_tracts()
    rows = [{"id": s["id"], "ready": builder.readiness(s, 9), "lower_income": builder.lower_income_homes(s),
             "area_score": area.score(tracts.get(s.get("tract_id")))["score"], "homes_per_1m": None} for s in sites]
    top = builder.rank(rows)["rows"][:3]
    assert all(r["ready"]["why"] for r in top)
    assert all(r["ready"]["hazard_clear"] is not False for r in top)


def test_budget_uses_same_costs_as_statutory():
    A = contracts.load_assumptions()
    S = A["statutory_housing_cost"]
    fixed = sum(S[k]["value"] for k in ("fire_casualty_insurance", "maintenance_repairs", "utilities_allowance",
                                        "hoa_fees", "loan_insurance", "space_rent"))
    tax = S["property_tax_rate"]["value"]
    bp = builder.budget_price_same_costs(90_000, 0.30, 0.0718, fixed, tax)
    assert bp["price"] == pytest.approx(221_037, abs=1)
    # same answer as family_price when its "other costs" include the solved property tax
    fp = finance.family_price(90_000, 0.0718, 0.30, fixed + bp["monthly_property_tax"])
    assert fp["price"] == pytest.approx(bp["price"], rel=1e-9)
    sp = finance.statutory_price(90_000, 4, 3, contracts.load_income_limits(), 0.0718, fixed, tax)
    assert sp["price"] == pytest.approx(153_751, abs=1)


def test_budget_price_is_none_not_zero_when_costs_use_the_whole_budget():
    bp = builder.budget_price_same_costs(20_000, 0.30, 0.0718, 600.0, 0.011)  # cap $500/mo < $600 fixed costs
    assert bp["price"] is None and bp["reason"]
    sens = builder.budget_rate_sensitivity(20_000, 0.30, [0.06, 0.07], 600.0, 0.011, 500_000, 0)
    assert all(r["family_price"] is None and r["gap"] is None for r in sens)


def test_one_pager_keeps_pathway_notes():
    srcs = contracts.load_sources()
    s = contracts.load_sites()[0]
    ev = pathways.evaluate(s)
    g = finance.gap({"land": 100.0}, {"family_price": 50.0})
    doc = builder.one_pager(s, ev, builder.readiness(s, 9), area.score(None), None,
                            {"basis_label": "x", "price": 50.0, "other_sources": 0, "cost_total": 100, "gap": g,
                             "homes_per_1m": None}, srcs, "2026-11-07")
    md = builder.one_pager_md(doc, srcs)
    assert "Prevailing wage" in md  # an SB 4 note: a real requirement a nonprofit must see
    assert "Hazards checked" in md and "Is it safe" not in md


def test_hazard_rows_keep_unknown_visible():
    rows = builder.hazards(BLANK)
    assert {r["result"] for r in rows} == {"unknown"}
    assert any("fault" in r["test"] for r in rows)


def test_one_pager_is_sourced_and_honest():
    srcs = contracts.load_sources()
    s = contracts.load_sites()[0]
    ev = pathways.evaluate(s)
    g = finance.gap({"land": 100.0}, {"family_price": None})
    doc = builder.one_pager(s, ev, builder.readiness(s, 9), area.score(None), None,
                            {"basis_label": "Statutory benchmark", "basis_sources": ["hcd_income_2026"], "price": None,
                             "price_note": "above moderate", "other_sources": 0, "cost_total": 100, "gap": g,
                             "homes_per_1m": None}, srcs, "2026-11-07")
    md = builder.one_pager_md(doc, srcs)
    assert "ASSUMPTION" in md and "None" not in md and "incomplete" in md
    assert all(i in srcs for i in doc["cited"])
    assert "scag_he_sites" in doc["cited"]
    assert "<h1>" in builder.one_pager_html(doc, srcs)


def test_synthetic_sample_still_works_and_says_synthetic():
    srcs = contracts.load_sources()
    fc = contracts._load("sites.sample.geojson")
    sample = [{**f["properties"], "lat": None, "lon": None} for f in fc["features"]]  # no coordinates at all
    rows = builder.rank([_row(s) for s in sample])["rows"]
    assert len(rows) == len(sample)
    s = next(x for x in sample if x.get("synthetic"))
    g = finance.gap({"land": 1.0}, {"family_price": 0.0})
    doc = builder.one_pager(s, pathways.evaluate(s), builder.readiness(s, 9), area.score(None), None,
                            {"basis_label": "x", "price": 0.0, "other_sources": 0, "cost_total": 1, "gap": g,
                             "homes_per_1m": None}, srcs, "2026-11-07")
    assert "SYNTHETIC" in builder.one_pager_md(doc, srcs)


def test_missing_label_is_plain_words():
    assert builder.missing_label(finance.gap({"land": None}, {"family_price": None})) == "land, family price"


def test_surplus_notice_and_vacant_land_are_leads():
    site = {**CLEAR, "id": "s", "owner_type_proxy": "public_surplus", "surplus_notice": True,
            "raw": {"sla": {"issued": "04-27-2020", "status": "Archive"}, "existing_use": {"label": "Urban Vacant", "vacant": True}}}
    checks = {c["key"]: c for c in builder.readiness(site, 9)["checks"]}
    assert checks["land_lead"]["result"] == "pass" and "may be stale" in checks["land_lead"]["text"]
    assert checks["use"]["result"] == "pass" and checks["use"]["text"] == "vacant land today"
    assert builder.readiness(BLANK, 9)["checks"][-1]["result"] == "unknown"


def test_housing_element_listing_alone_is_not_a_yes():
    for s in contracts.load_sites()[:200]:
        ev = pathways.evaluate(s)
        assert builder.law_verdict(ev) != "yes" or any(ev[k]["verdict"] == "yes" for k in builder.LAW_PATHWAYS)
    assert builder.law_verdict({"HE": {"verdict": "yes"}, "SB4": {"verdict": "no"}}) == "no"


def test_small_hazard_overlap_is_check_the_map_not_a_fail():
    sliver = {**CLEAR, "id": "e", "in_flood_zone": None,   # the pipeline nulls an edge sliver and says why
              "raw": {**CLEAR["raw"], "flood_sfha": [{"pct_of_site": 0.4}], "edge_sliver": {"flood_sfha": True}}}
    small = {**CLEAR, "id": "s", "in_flood_zone": True, "raw": {**CLEAR["raw"], "flood_sfha": [{"pct_of_site": 3.0}]}}
    assert builder.readiness(small, 9)["hazard_clear"] is False  # 1% or more is a real overlap (pipeline rule)
    whole = {**CLEAR, "id": "w", "in_flood_zone": True, "raw": {**CLEAR["raw"], "flood_sfha": [{"pct_of_site": 100.0}]}}
    point = {**CLEAR, "id": "p", "in_flood_zone": True, "raw": {**CLEAR["raw"], "flood_sfha": [{"pct_of_site": None}]}}
    rd = builder.readiness(sliver, 9)
    assert rd["hazard_clear"] is None and "check the map" in rd["why"] and "Watch:" in rd["why"]
    assert builder.readiness(whole, 9)["hazard_clear"] is False
    assert builder.readiness(point, 9)["hazard_clear"] is False  # no share known: a hit stays a fail
    # an edge overlap ranks with clear sites (one point fewer), above unchecked and overlapping ones
    assert [r["id"] for r in builder.rank([_row(whole), _row(BLANK), _row(sliver), _row(CLEAR)])["rows"]] == ["a", "e", "c", "w"]


def test_app_edge_cutoff_matches_the_pipeline_sliver_cutoff():
    """One cutoff for ranking, Hazards tab and law checks (2f1896a disagreed: app 5%, pipeline 1%)."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
    import common
    assert builder.EDGE_PCT == common.SLIVER_PCT
    mid = {**CLEAR, "id": "m", "in_flood_zone": True, "raw": {**CLEAR["raw"], "flood_sfha": [{"pct_of_site": 2.8}]}}
    assert builder.readiness(mid, 9)["hazard_clear"] is False  # 2.8% is a real overlap, same as the law checks say


def test_small_existing_house_filter():
    house = {"est_homes": 2, "raw": {"existing_use": {"label": "Single Family Residential"}}}
    assert builder.small_existing_house(house)
    assert not builder.small_existing_house({**house, "est_homes": 12})
    assert not builder.small_existing_house({**house, "est_homes": None})  # unknown is never hidden
    assert not builder.small_existing_house({"est_homes": 1, "raw": {"existing_use": {"label": "Urban Vacant"}}})


def _site(i, lat, lon, **kw):
    return {"id": i, "apn": f"000-000-{i}", "est_homes": 4, "lat": lat, "lon": lon, **kw}


def test_call_first_folds_neighbours_into_one_call():
    a, b = _site("a", 33.7500, -117.9000), _site("b", 33.75017, -117.9000)   # ~19 m apart
    c, d = _site("c", 33.8000, -117.9000), _site("d", None, None)           # far away; no coordinates
    rows = [{"id": s["id"], "site": s} for s in (a, b, c, d)]
    picks = builder.call_first(rows)
    assert [p["row"]["id"] for p in picks] == ["a", "c", "d"]               # b folds into a; d never folds
    assert [o["id"] for o, _ in picks[0]["neighbours"]] == ["b"]
    assert 15 < picks[0]["neighbours"][0][1] < 25
    assert "19 m" in builder.neighbours_line(picks[0]["neighbours"]) or "18 m" in builder.neighbours_line(picks[0]["neighbours"])
    assert builder.neighbours_line([]) is None


def test_real_top_three_calls_are_distinct_places():
    sites = [s for s in contracts.load_sites() if not builder.small_existing_house(s)]
    tracts = contracts.load_tracts()
    rows = builder.rank([{"id": s["id"], "site": s, "ready": builder.readiness(s, 9),
                          "lower_income": builder.lower_income_homes(s), "homes_per_1m": None,
                          "area_score": area.score(tracts.get(s.get("tract_id")))["score"]} for s in sites])["rows"]
    picks = [p["row"]["site"] for p in builder.call_first(rows)]
    for i in range(3):
        for j in range(i + 1, 3):
            assert builder.distance_m(picks[i], picks[j]) >= builder.NEIGHBOUR_M


def test_vacant_lot_costs_that_assume_a_building_become_unknown():
    costs = {"land_and_building_purchase": 360000, "construction_and_repairs": 40000}
    other = {"public_subsidies": 100000, "rent_earned_while_waiting": 55000}
    vacant = {"raw": {"existing_use": {"label": "Urban Vacant", "vacant": True}}}
    c, o = builder.adjust_for_site(costs, other, vacant)
    assert c["construction_and_repairs"] is None and o["rent_earned_while_waiting"] is None
    assert costs["construction_and_repairs"] == 40000                         # inputs not mutated
    assert finance.gap(c, {"family_price": 150000, **o})["complete"] is False
    filled = finance.gap({**c, "construction_and_repairs": 300000}, {"family_price": 150000, **o, "rent_earned_while_waiting": 0})
    assert filled["complete"] is True
    shop = {"raw": {"existing_use": {"label": "Retail Stores and Commercial Services"}}}
    assert builder.adjust_for_site(costs, other, shop) == (costs, other)


def test_density_watch():
    tiny = {**CLEAR, "est_homes": 56, "acres": 0.013}
    assert "may cover several parcels" in builder.readiness(tiny, 9)["why"]
    assert builder.density_note({"est_homes": 22, "acres": 1.0}) is None


def test_site_matches_city_apn_with_or_without_dashes_and_all_words():
    s = {"name": "Garden Grove · APN 098-120-39", "city": "Garden Grove", "apn": "098-120-39",
         "address": None, "zoning_local": "R-3"}
    assert builder.site_matches(s, "") and builder.site_matches(s, None)
    assert builder.site_matches(s, "garden")
    assert builder.site_matches(s, "098-120-39") and builder.site_matches(s, "09812039")
    assert builder.site_matches(s, "grove r-3")  # every word must match
    assert not builder.site_matches(s, "grove fullerton")
    assert not builder.site_matches(s, "99999")
