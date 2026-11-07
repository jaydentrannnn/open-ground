"""Legal pathways: a yes / no / unknown per test, with the reason and the source.

OWNER: Builder A (Data & Rules).
Rule from CLAUDE.md: never invent a statute detail. Every test and note below comes from the HCD
Housing Law Fact Sheets (April 2026), read in full on 2026-11-07, with the page cited (SB 684 / SB 1123:
the combined PDF, pp. 67-68). Anything our
data cannot check stays "unknown": that is most of SB 4's list, and we show it rather than hide it.

evaluate() returns, per pathway: label, verdict, tests (pass / fail / unknown) and notes
(facts that apply but are not a site test, e.g. labor rules).
"""
from __future__ import annotations

PASS, FAIL, UNKNOWN = "pass", "fail", "unknown"

SB4 = "hcd_sb4_factsheet"
SB9 = "hcd_sb9_factsheet"
FIRE_MAPS = ("CAL FIRE LRA map dated 2025-03-24, an OC LRA copy of unknown date, and CAL FIRE SRA 2007 "
             "(outdated): confirm on CAL FIRE's current map")
SINGLE_FAMILY_CODES = {"1110", "1111", "1112", "1113"}  # SCAG legend group "Single Family Residential"


def _t(test, result, why, source):
    return {"test": test, "result": result, "why": why, "source": source}


def _raw(site: dict) -> dict:
    return site.get("raw") or {}


def _overlaps(items: list[dict], key: str) -> str:
    bits = []
    for x in items or []:
        share = f"{x['pct_of_site']}% of parcel" if x.get("pct_of_site") is not None else "overlap"
        bits.append(f"{x.get(key)}: {share}")
    return "; ".join(bits)


def _fire(site: dict, source: str) -> dict:
    v = site.get("in_fire_zone")
    name = "Not in a very high fire hazard severity zone"
    if v is None:
        return _t(name, UNKNOWN, "Fire maps not checked for this site", source)
    if v:
        detail = _overlaps(_raw(site).get("fire_very_high"), "layer")
        return _t(name, FAIL, f"Overlaps a Very High zone ({detail or 'see map'}). Checked: {FIRE_MAPS}", source)
    return _t(name, PASS, f"No Very High zone on the maps we checked: {FIRE_MAPS}", source)


def _flood(site: dict, source: str) -> list[dict]:
    v = site.get("in_flood_zone")
    sfha_name = "Not in a FEMA special flood hazard area"
    if v is None:
        out = [_t(sfha_name, UNKNOWN, "Flood layer not checked", source)]
    elif v:
        out = [_t(sfha_name, FAIL, f"Overlaps SFHA ({_overlaps(_raw(site).get('flood_sfha'), 'zone') or 'see map'}). "
                                   "A small share may be a mapping sliver: check the FIRM", source)]
    else:
        out = [_t(sfha_name, PASS, "No SFHA overlap (FEMA SFHA_TF flag, OC county copy of unknown date)", source)]
    fw = _raw(site).get("floodway")
    fw_name = "Not in a regulatory floodway"
    if "floodway" not in _raw(site) or v is None:
        out.append(_t(fw_name, UNKNOWN, "Floodway not checked", source))
    elif fw:
        out.append(_t(fw_name, FAIL, f"Overlaps a floodway ({_overlaps(fw, 'zone')})", source))
    else:
        out.append(_t(fw_name, PASS, "No floodway overlap (FEMA ZONE_SUBTY, OC county copy)", source))
    return out


def _fault(site: dict, source: str) -> dict:
    v = site.get("in_fault_zone")
    name = "Not in an earthquake fault zone (p.2)"
    term = ("The fact sheet does not define the term; we use the State's Alquist-Priolo Earthquake Fault Zones "
            "(CGS, PRC 2621-2630)")
    if v is None:
        return _t(name, UNKNOWN, "Fault-zone layer not checked for this site", source)
    if v:
        quads = ", ".join(sorted({x.get("quad") for x in _raw(site).get("fault_ap", []) if x.get("quad")}))
        return _t(name, FAIL, f"Overlaps an Alquist-Priolo zone ({_overlaps(_raw(site).get('fault_ap'), 'quad') or quads}). "
                              + term, source)
    return _t(name, PASS, "No overlap with an Alquist-Priolo Earthquake Fault Zone. " + term, source)


def _flag_absent(site: dict, key: str, label: str, source: str, unchecked: str | None = None) -> dict:
    v = site.get(key)
    if v is None:
        return _t(f"Not in {label}", UNKNOWN, unchecked or f"{label} layer not checked yet", source)
    if v:
        return _t(f"Not in {label}", FAIL, f"Site is in a {label}", source)
    return _t(f"Not in {label}", PASS, f"No {label} overlap found", source)


# ---------------------------------------------------------------------------- SB 4
def sb4(site: dict) -> list[dict]:
    """SB 4, Gov Code 65913.16 (HCD fact sheet, April 2026). By-right, 100% affordable, faith / college land."""
    owner = site.get("owner_type_proxy")
    own = "Owned by a religious institution or independent college as of Jan 1, 2024 (p.1)"
    if owner in ("faith_proxy", "college_proxy"):
        names = [w.get("name") for w in _raw(site).get("worship_osm", []) if w.get("name")]
        leads = []
        if _raw(site).get("worship_osm"):
            leads.append("a place of worship is mapped inside this parcel on OpenStreetMap"
                         + (f" ({', '.join(names)})" if names else ""))
        if (_raw(site).get("existing_use") or {}).get("religious"):
            leads.append("SCAG 2024 existing land use is 'Religious Facilities'")
        tests = [_t(own, UNKNOWN, f"LEAD: {'; '.join(leads) or 'proxy match'}. Not proof of ownership: "
                                  "confirm on title or the Assessor roll", SB4)]
    elif owner is None:
        tests = [_t(own, UNKNOWN, "Owner type is not in free parcel data", SB4)]
    else:
        tests = [_t(own, FAIL, f"Owner type is {owner}", SB4)]
    tests.append(_t("Zone allows SB 4 (p.1)", PASS, "SB 4 projects are permitted in all zones, "
                                                    "including single-family and non-residential", SB4))
    tests.append(_fire(site, SB4))
    tests += _flood(site, SB4)
    tests.append(_fault(site, SB4))
    tests.append(_t("No other listed environmental exclusion (p.2)", UNKNOWN,
                    "Not checked: farmland, agricultural-protection land, wetlands, hazardous waste, NCCP "
                    "conservation land, protected-species habitat, conservation easement", SB4))
    tests.append(_t("No listed industrial use nearby (p.2)", UNKNOWN,
                    "Not checked: adjacent light industrial (>1/3 of floor area), heavy industrial within "
                    "1,200 ft, Title V within 1,600 ft, refinery within 3,200 ft", SB4))
    tests.append(_t("75% of perimeter adjoins urban uses (p.2)", UNKNOWN, "Not checked", SB4))
    return tests


SB4_NOTES = [
    "100% of units for lower-income households, except up to 20% moderate-income and up to 5% for staff of the "
    "land-owning institution. Deed restriction: 45 years for ownership, 55 for rental (p.1).",
    "Prevailing wage applies to every SB 4 project, whatever its size. At 50+ units, health care and "
    "apprenticeship requirements are added (p.3). Volunteer-built homes: ask a labor lawyer how this applies.",
    "Ministerial approval without CEQA, but the applicant must complete a Phase I environmental assessment (p.3).",
    "Parking: up to 1 space per unit; none within 0.5-mile walking distance of a high-quality transit corridor "
    "or major transit stop (p.3).",
    "In effect July 2, 2024 through January 1, 2036 (p.1).",
]


# ---------------------------------------------------------------------------- SB 9
def sb9(site: dict) -> list[dict]:
    """SB 9, Gov Code 65852.21 and 66411.7 (HCD fact sheet, April 2026)."""
    zs = site.get("zoning_scag") or ""
    code = zs.split(" ", 1)[0] if zs else ""
    local = site.get("zoning_local")
    zone_name = "Single-family residential zone (p.1)"
    shown = f"SCAG {zs}" + (f"; city code {local}" if local else "")
    if not code:
        z = _t(zone_name, UNKNOWN, "Zoning not joined yet", SB9)
    elif code in SINGLE_FAMILY_CODES:
        z = _t(zone_name, PASS, f"{shown}. SCAG's regional code is a translation: confirm the city's zone", SB9)
    elif code in ("7777", "9999", "1700"):
        z = _t(zone_name, UNKNOWN, f"{shown}: read the city or specific-plan zoning", SB9)
    else:
        z = _t(zone_name, FAIL, f"{shown}: not a single-family zone", SB9)
    return [
        z,
        _flag_absent(site, "in_historic_district", "historic district", SB9,
                     "Not checked: historic district, State Historic Resource Inventory or local landmark (p.3)"),
        _t("Not on lands listed in Gov Code 65913.4(a)(6)(B)-(K) (p.3)", UNKNOWN,
           "Fact sheet names wetlands and prime farmland 'etc.'; the full list is in the statute and not checked", SB9),
        _t("No rent-restricted or recently tenant-occupied housing demolished or altered (p.2-3)", UNKNOWN,
           "Not in public data: rent restriction, tenant in last 3 years, Ellis Act withdrawal in last 15 years", SB9),
    ]


SB9_NOTES = [
    "Up to two primary units per lot, or split into two lots of roughly equal size with up to two units on each (p.1-2).",
    "Lot-split owner-occupancy affidavit (3 years) is NOT required when the applicant is a community land trust "
    "or nonprofit (p.2).",
    "City must approve or deny a complete application within 60 days (p.2). Units must be rented for more than "
    "30 days if rented (p.2).",
    "Local standards cannot block two units of at least 800 sq ft each, or two lots of 1,200 sq ft (p.1).",
]


# ---------------------------------------------------------------------------- SB 684 / SB 1123
SHRA_SRC = "hcd_law_factsheets"
MULTIFAMILY_CODES = {"1120", "1121", "1122", "1123", "1124", "1125"}  # SCAG legend group "Multi-Family Residential"
NON_RESIDENTIAL_PREFIXES = ("13", "14", "18", "2", "4", "8888")  # SCAG legend: industrial, transport/utilities,
# open space, agriculture, water, undevelopable


def shra(site: dict) -> list[dict]:
    """Starter Home Revitalization Act: SB 684 (2023) + SB 1123 (2024), Gov Code 65852.28, 65913.4.5, 66499.41.
    Source: HCD Housing Law Fact Sheets (April 2026), combined PDF pp. 67-68 ('1 of 2', '2 of 2')."""
    acres = site.get("acres")
    if acres is None:
        size = _t("Lot under 5 acres (p.67)", UNKNOWN, "Lot size unknown", SHRA_SRC)
    elif acres < 5:
        size = _t("Lot under 5 acres (p.67)", PASS, f"{acres} acres", SHRA_SRC)
    else:
        size = _t("Lot under 5 acres (p.67)", FAIL, f"{acres} acres", SHRA_SRC)

    zs = site.get("zoning_scag") or ""
    code = zs.split(" ", 1)[0] if zs else ""
    local = site.get("zoning_local")
    shown = f"SCAG {zs}" + (f"; city code {local}" if local else "")
    zname = "Zoned for multifamily, or a single-family lot under SB 1123 (p.67-68)"
    if not code:
        zone = _t(zname, UNKNOWN, "Zoning not joined yet", SHRA_SRC)
    elif code in MULTIFAMILY_CODES:
        zone = _t(zname, PASS, f"{shown}. SCAG's regional code is a translation: confirm the city's zone", SHRA_SRC)
    elif code in SINGLE_FAMILY_CODES:
        zone = _t(zname, UNKNOWN, f"{shown}. SB 1123 (effective July 1, 2025) extends SHRA to single-family zones, "
                                  "headlined for vacant lots; its conditions are not in the fact sheet: read Gov Code "
                                  "66499.41", SHRA_SRC)
    elif code.startswith(NON_RESIDENTIAL_PREFIXES):
        zone = _t(zname, FAIL, f"{shown}: not a zone that allows multifamily housing", SHRA_SRC)
    else:
        zone = _t(zname, UNKNOWN, f"{shown}: SHRA applies in any zone that allows multifamily, including mixed-use "
                                  "(HCD letter to Hayward, Jan 28 2025, p.67). Confirm the city's zone allows it",
                  SHRA_SRC)

    city = site.get("city")
    if not city:
        inc = _t("In an incorporated city or large urban county (p.67)", UNKNOWN, "City unknown", SHRA_SRC)
    elif city == "County of Orange":
        inc = _t("In an incorporated city or large urban county (p.67)", UNKNOWN,
                 "Unincorporated: the fact sheet does not define 'large urban county'", SHRA_SRC)
    else:
        inc = _t("In an incorporated city or large urban county (p.67)", PASS, f"City of {city}", SHRA_SRC)

    fire = site.get("in_fire_zone")
    fname = "Not in a fire hazard zone (p.67)"
    if fire:
        f = _t(fname, FAIL, f"Overlaps a Very High fire zone ({_overlaps(_raw(site).get('fire_very_high'), 'layer')})",
               SHRA_SRC)
    else:
        f = _t(fname, UNKNOWN, "The fact sheet says 'fire hazard zones' without a severity; we only check Very High "
                               "zones, so lower-severity zones are not ruled out", SHRA_SRC)

    eu = _raw(site).get("existing_use") or {}
    tname = "Does not displace rent-controlled or tenant-occupied housing (p.67)"
    if eu.get("vacant"):
        ten = _t(tname, PASS, f"Existing use is {eu.get('label')} (SCAG 2024): no housing to displace", SHRA_SRC)
    else:
        ten = _t(tname, UNKNOWN, f"Existing use: {eu.get('label') or 'unknown'}. Tenancy and rent control are not in "
                                 "public data", SHRA_SRC)
    other = _t("Not on other environmentally sensitive land (p.67)", UNKNOWN,
               "Not checked: farmland, wetlands and the statute's full list", SHRA_SRC)
    return [size, zone, inc, f, ten, other]


SHRA_NOTES = [
    "Up to 10 lots and 10 total units (p.67); SB 1123: up to 10 units excluding ADUs (p.68). Fits a 4-12 home "
    "ownership project only at 10 or fewer.",
    "Ministerial approval within 60 days, deemed approved if the city does not act; exempt from CEQA (p.67).",
    "Can be fee simple ownership, a common interest development (condo/HOA) or a community land trust (p.67-68).",
    "Must comply with local inclusionary housing requirements (p.67). Cities cannot impose excessive setbacks, "
    "parking mandates or low floor-area ratios that reduce allowed density (p.67).",
]


# ---------------------------------------------------------------------------- other pathways
def _existing_use(site: dict) -> tuple[str, bool]:
    """(' Existing use (SCAG 2024): <label>.' or '', is_under_construction)."""
    eu = _raw(site).get("existing_use") or {}
    if not eu.get("label"):
        return "", False
    return f" Existing use (SCAG 2024 land use, updated July 2025): {eu['label']}.", bool(eu.get("under_construction"))


def housing_element(site: dict) -> list[dict]:
    v = site.get("housing_element_site")
    res = UNKNOWN if v is None else (PASS if v else FAIL)
    cap = _raw(site).get("he_capacity") or {}
    year = _raw(site).get("he_year")
    detail = ""
    if cap.get("Total") is not None:
        detail = (f" The city counted {int(cap['Total'])} homes here ({int(cap.get('Low_Income') or 0)} lower-income)"
                  + (f" in its {year} inventory" if year else "") + ".")
    use, building = _existing_use(site)
    why = {PASS: "On the city's adopted site inventory (check it has not sold or been built: lists go stale)." + detail,
           FAIL: "Not on the adopted site inventory", UNKNOWN: "Inventory not joined yet"}[res] + use
    tests = [_t("Listed in housing-element site inventory", res, why, "scag_he_sites")]
    if building:
        tests.append(_t("Not already in development", FAIL, "SCAG 2024 existing land use says Under Construction: "
                                                          "the listing may be stale", "scag_landuse"))
    return tests


def surplus_land(site: dict) -> list[dict]:
    v = site.get("surplus_notice")
    res = UNKNOWN if v is None else (PASS if v else FAIL)
    n = _raw(site).get("sla") or {}
    detail = ""
    if n:
        detail = (f": {n.get('agency') or 'agency unknown'}, notice {n.get('case')}, issued {n.get('issued') or 'unknown'}"
                  f", status {n.get('status') or 'unknown'}"
                  + (" (Archive = sent to HCD more than 60 days ago. The interest window has likely passed; "
                     "whether the land is still available is unknown until you call the agency)"
                     if n.get("status") == "Archive" else ""))
    why = {PASS: "Public agency posted a Surplus Land Act notice" + detail,
           FAIL: "No notice for this APN in HCD's Surplus Land Act list (checked 2026-11-07)",
           UNKNOWN: "Surplus notices not joined yet"}[res] + (_existing_use(site)[0] if res == PASS else "")
    tests = [_t("Surplus Land Act notice", res, why, "hcd_sla_notices")]
    if res == PASS:
        status = n.get("status")
        if status == "Active":
            tests.append(_t("Notice window open (Active)", PASS, "Sent to HCD within the last 60 days", "hcd_sla_notices"))
        else:
            tests.append(_t("Notice window open (Active)", UNKNOWN,
                            f"Status {status or 'unknown'}: sent to HCD more than 60 days ago, so the 60-day interest "
                            "window has likely passed. Availability is unknown until someone calls the agency",
                            "hcd_sla_notices"))
    return tests


PATHWAYS = {
    "SB4": ("SB 4 faith / college land", sb4),
    "SB9": ("SB 9 lot split / duplex", sb9),
    "SHRA": ("SB 684 / SB 1123 starter homes (10 or fewer)", shra),
    "HE": ("Housing-element site", housing_element),
    "SLA": ("Surplus public land", surplus_land),
}
NOTES = {"SB4": SB4_NOTES, "SB9": SB9_NOTES, "SHRA": SHRA_NOTES}


def verdict(tests: list[dict]) -> str:
    results = {t["result"] for t in tests}
    if FAIL in results:
        return "no"
    if results == {PASS}:
        return "yes"
    return "maybe"


def evaluate(site: dict) -> dict:
    """{pathway_id: {"label", "verdict", "tests", "notes"}} for one site."""
    out = {}
    for pid, (label, fn) in PATHWAYS.items():
        tests = fn(site)
        out[pid] = {"label": label, "verdict": verdict(tests), "tests": tests, "notes": NOTES.get(pid, [])}
    return out


def best_verdict(evals: dict) -> str:
    order = {"yes": 2, "maybe": 1, "no": 0}
    return max((e["verdict"] for e in evals.values()), key=lambda v: order[v], default="no")
