"""Legal pathways: a yes / no / unknown per test, with the reason and the source.

OWNER: Builder A (Data & Rules).
Rule from CLAUDE.md: never invent a statute detail. Each test below names the source it comes
from. Thresholds you have not read in the source stay "unknown". Read the HCD fact sheet, then
tighten the test and update `checked`.
"""
from __future__ import annotations

PASS, FAIL, UNKNOWN = "pass", "fail", "unknown"


def _flag_absent(site: dict, key: str, label: str, source: str) -> dict:
    v = site.get(key)
    if v is None:
        return {"test": f"Not in {label}", "result": UNKNOWN, "why": f"{label} layer not checked yet", "source": source}
    if v:
        return {"test": f"Not in {label}", "result": FAIL, "why": f"Site is in a {label}", "source": source}
    return {"test": f"Not in {label}", "result": PASS, "why": f"No {label} overlap found", "source": source}


def sb4(site: dict) -> list[dict]:
    """SB 4: affordable housing on faith / nonprofit-college land (Gov Code 65913.16 per HCD)."""
    owner = site.get("owner_type_proxy")
    if owner in ("faith_proxy", "college_proxy"):
        own = {"test": "Owned by a religious institution or nonprofit college", "result": UNKNOWN,
               "why": "Proxy match only (worship-site map / IRS list). A LEAD, not a fact: confirm owner on title or Assessor roll",
               "source": "hcd_sb4_factsheet"}
    elif owner is None:
        own = {"test": "Owned by a religious institution or nonprofit college", "result": UNKNOWN,
               "why": "Owner type not in free parcel data", "source": "hcd_sb4_factsheet"}
    else:
        own = {"test": "Owned by a religious institution or nonprofit college", "result": FAIL,
               "why": f"Owner type is {owner}", "source": "hcd_sb4_factsheet"}
    tests = [own]
    for key, label in [("in_fire_zone", "fire hazard zone"), ("in_flood_zone", "flood zone"),
                       ("in_fault_zone", "fault zone")]:
        tests.append(_flag_absent(site, key, label, "hcd_sb4_factsheet"))
    homes = site.get("est_homes")
    if homes is not None and homes >= 10:
        tests.append({"test": "Labor standards", "result": UNKNOWN,
                      "why": "10+ homes may trigger prevailing-wage rules (UNVERIFIED: confirm in HCD SB 4 fact sheet); conflicts with volunteer builds",
                      "source": "hcd_sb4_factsheet"})
    return tests


def sb9(site: dict) -> list[dict]:
    """SB 9: lot splits and duplexes on single-family lots (Gov Code 65852.21, 66411.7 per HCD)."""
    zoning = (site.get("zoning_scag") or "").lower()
    if not zoning:
        z = {"test": "Single-family zone", "result": UNKNOWN, "why": "Zoning not joined yet", "source": "hcd_sb9_factsheet"}
    elif "single" in zoning:
        z = {"test": "Single-family zone", "result": PASS, "why": f"Zoning: {site.get('zoning_scag')}", "source": "hcd_sb9_factsheet"}
    else:
        z = {"test": "Single-family zone", "result": FAIL, "why": f"Zoning: {site.get('zoning_scag')}", "source": "hcd_sb9_factsheet"}
    return [z, _flag_absent(site, "in_historic_district", "historic district", "hcd_sb9_factsheet")]


def housing_element(site: dict) -> list[dict]:
    v = site.get("housing_element_site")
    res = UNKNOWN if v is None else (PASS if v else FAIL)
    why = {PASS: "On the city's adopted site inventory (check it has not sold or been built: lists go stale)",
           FAIL: "Not on the adopted site inventory", UNKNOWN: "Inventory not joined yet"}[res]
    return [{"test": "Listed in housing-element site inventory", "result": res, "why": why, "source": "scag_he_sites"}]


def surplus_land(site: dict) -> list[dict]:
    v = site.get("surplus_notice")
    res = UNKNOWN if v is None else (PASS if v else FAIL)
    why = {PASS: "Public agency posted a Surplus Land Act notice", FAIL: "No surplus notice found",
           UNKNOWN: "Surplus notices not joined yet"}[res]
    return [{"test": "Surplus Land Act notice", "result": res, "why": why, "source": "hcd_sla_notices"}]


PATHWAYS = {
    "SB4": ("SB 4 faith / college land", sb4),
    "SB9": ("SB 9 lot split / duplex", sb9),
    "HE": ("Housing-element site", housing_element),
    "SLA": ("Surplus public land", surplus_land),
}


def verdict(tests: list[dict]) -> str:
    results = {t["result"] for t in tests}
    if FAIL in results:
        return "no"
    if results == {PASS}:
        return "yes"
    return "maybe"


def evaluate(site: dict) -> dict:
    """{pathway_id: {"label", "verdict", "tests"}} for one site."""
    out = {}
    for pid, (label, fn) in PATHWAYS.items():
        tests = fn(site)
        out[pid] = {"label": label, "verdict": verdict(tests), "tests": tests}
    return out


def best_verdict(evals: dict) -> str:
    order = {"yes": 2, "maybe": 1, "no": 0}
    return max((e["verdict"] for e in evals.values()), key=lambda v: order[v], default="no")
