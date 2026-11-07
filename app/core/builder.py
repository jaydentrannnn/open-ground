"""Builder mode logic: which sites to call first, why, and a one-pager to send. Pure functions, no Streamlit.

OWNER: Builder B. Reads core/pathways (A) and core/finance (C); never changes them.
Rules: unknown is never counted as a pass, every check names its source id, made-up numbers say ASSUMPTION.
"""
from __future__ import annotations

import html

from core import finance, pathways

PASS, FAIL, UNKNOWN = pathways.PASS, pathways.FAIL, pathways.UNKNOWN
FLOOD_SOURCES = ["oc_floodplains"]
FIRE_SOURCES = ["calfire_fhsz_lra_2025", "oc_fhsz_lra", "calfire_fhsz_sra_2007"]
SORTS = ("Ready to call", "Area benefit", "Homes per $1M of gap")
N_CHECKS = 7
# Laws that can give a right to build. A housing-element listing (HE) is the city's plan and a Surplus Land Act
# notice (SLA) is an offer of land: both are reasons to call, not permission, so they never make the headline "Yes".
LAND_SIGNALS = ("HE", "SLA")
LAW_PATHWAYS = tuple(pid for pid in pathways.PATHWAYS if pid not in LAND_SIGNALS)  # new laws join automatically
LAW_NAMES = "; ".join(pathways.PATHWAYS[pid][0] for pid in LAW_PATHWAYS)
# ASSUMPTION (team choice, no source): a hazard overlap under this share of the parcel is shown as
# "edge: check the map" instead of ruling the site down. A small overlap may be a mapping sliver (see pathways).
EDGE_PCT = 5.0
# ASSUMPTION: an existing single-family home where the city plans this many homes or fewer is someone's house
# with room for an ADU or lot split, not a site a nonprofit would buy. Hidden by a sidebar filter.
SMALL_HOUSE_MAX_HOMES = 2


def law_verdict(ev: dict) -> str:
    """Best verdict among the by-right laws only (yes / maybe / no). See LAW_PATHWAYS."""
    laws = {k: e for k, e in ev.items() if k in LAW_PATHWAYS}
    return pathways.best_verdict(laws) if laws else "maybe"


def small_existing_house(site: dict, max_homes: int = SMALL_HOUSE_MAX_HOMES) -> bool:
    """True when SCAG land use says single-family home today and the city plans max_homes or fewer here."""
    label = existing_use(site).get("label") or ""
    homes = site.get("est_homes")
    return label.startswith("Single Family") and homes is not None and homes <= max_homes


def money(x) -> str:
    return "unknown" if x is None else f"${x:,.0f}"


def missing_label(g: dict) -> str:
    """finance.gap()'s missing keys ("paid:family_price") as plain words ("family price")."""
    return ", ".join(m.split(":", 1)[-1].replace("_", " ") for m in g.get("missing", []))


def _neg(v):
    """A flag where True is bad (hazards)."""
    return UNKNOWN if v is None else (FAIL if v else PASS)


def _pos(v):
    """A flag where True is good."""
    return UNKNOWN if v is None else (PASS if v else FAIL)


def lower_income_homes(site: dict) -> int | None:
    """Lower-income homes the city counted on this parcel in its housing-element inventory (scag_he_sites)."""
    v = ((site.get("raw") or {}).get("he_capacity") or {}).get("Low_Income")
    return None if v is None else int(v)


def he_capacity(site: dict) -> dict:
    return ((site.get("raw") or {}).get("he_capacity") or {})


def existing_use(site: dict) -> dict:
    """SCAG 2024 existing land use joined by A: {label, vacant, parking, under_construction, religious} or {}."""
    return ((site.get("raw") or {}).get("existing_use") or {})


def surplus_notice(site: dict) -> dict:
    """HCD Surplus Land Act notice details joined by A (agency, issued, status, ...) or {}."""
    return ((site.get("raw") or {}).get("sla") or {})


def _land_lead(site: dict, owner) -> dict:
    """SB 4 faith-land proxy or a Surplus Land Act notice: a reason to call, never proof of ownership."""
    sla = surplus_notice(site)
    if owner == "faith_proxy" or existing_use(site).get("religious"):
        return {"key": "land_lead", "kind": "plus", "result": PASS, "sources": ["osm_worship", "scag_landuse"],
                "text": "a place of worship is mapped here (SB 4 lead, not proof of ownership)"}
    if site.get("surplus_notice"):
        when = f", issued {sla['issued']}" if sla.get("issued") else ""
        status = f", status {sla['status']}: may be stale, ask the agency" if sla.get("status") else ""
        return {"key": "land_lead", "kind": "plus", "result": PASS, "sources": ["hcd_sla_notices"],
                "text": f"a public agency posted a Surplus Land Act notice{when}{status}"}
    if owner is None:
        return {"key": "land_lead", "kind": "plus", "result": UNKNOWN, "sources": ["osm_worship"], "text": "owner"}
    return {"key": "land_lead", "kind": "plus", "result": FAIL, "sources": ["osm_worship"],
            "text": f"owner type is {owner}"}


def _current_use(site: dict) -> dict:
    """Vacant land or a parking lot today is easier to build on (SCAG 2024 existing land use)."""
    eu = existing_use(site)
    base = {"key": "use", "kind": "plus", "sources": ["scag_landuse"]}
    if not eu or not eu.get("label"):
        return {**base, "result": UNKNOWN, "text": "current use"}
    if eu.get("under_construction"):
        return {**base, "result": FAIL, "text": "under construction today (the listing may be stale)"}
    if eu.get("vacant"):
        return {**base, "result": PASS, "text": "vacant land today"}
    if eu.get("parking"):
        return {**base, "result": PASS, "text": "a parking lot today"}
    return {**base, "result": FAIL, "text": f"in use today as {eu['label'].lower()}"}


def _hazard(site: dict, key: str, flag: str, raw_key: str, name: str, sources: list[str], text: dict) -> dict:
    """A hazard check. An overlap smaller than EDGE_PCT of the parcel becomes 'edge: check the map' (unknown),
    so a mapping sliver does not sink a site. A point-only site (no share) that hits stays a fail."""
    v = site.get(flag)
    if v:
        shares = [x.get("pct_of_site") for x in ((site.get("raw") or {}).get(raw_key) or [])]
        known = [s for s in shares if s is not None]
        if known and max(known) < EDGE_PCT:
            return {"key": key, "kind": "hazard", "result": UNKNOWN, "edge": True, "sources": sources,
                    "text": f"touches the edge of a {name} ({max(known):g}% of the parcel): check the map"}
    return {"key": key, "kind": "hazard", "result": _neg(v), "text": text, "sources": sources}


# ---------------------------------------------------------------------------- readiness
def readiness(site: dict, max_homes: int) -> dict:
    """Seven checks from sourced site fields. Hazards can rule a site down; the rest are pluses.

    Each check: {key, kind: hazard|plus, result: pass|fail|unknown, text, sources}.
    `text` is the phrase used in the one-sentence why.
    """
    li = lower_income_homes(site)
    homes = site.get("est_homes")
    owner = site.get("owner_type_proxy")
    checks = [
        _hazard(site, "flood", "in_flood_zone", "flood_sfha", "FEMA flood zone", FLOOD_SOURCES,
                {PASS: "clear of FEMA flood zones", FAIL: "in a FEMA flood zone", UNKNOWN: "flood zone"}),
        _hazard(site, "fire", "in_fire_zone", "fire_very_high", "very-high fire zone", FIRE_SOURCES,
                {PASS: "clear of very-high fire zones", FAIL: "in a very-high fire zone", UNKNOWN: "fire zone"}),
        {"key": "transit", "kind": "plus", "result": _pos(site.get("in_hqta")),
         "text": {PASS: "near frequent transit", FAIL: "not in a transit area", UNKNOWN: "transit area"},
         "sources": ["caltrans_hqta"]},
        {"key": "lower_income", "kind": "plus", "result": UNKNOWN if li is None else (PASS if li > 0 else FAIL),
         "text": {PASS: f"the city planned {li} lower-income home{'s' if li != 1 else ''} here",
                  FAIL: "no lower-income homes in the city's plan", UNKNOWN: "lower-income capacity"},
         "sources": ["scag_he_sites"]},
        {"key": "size", "kind": "plus", "result": UNKNOWN if homes is None else (PASS if homes <= max_homes else FAIL),
         "text": {PASS: f"{homes} home{'s' if homes != 1 else ''} fits your cap of {max_homes}",
                  FAIL: f"{homes} homes is over your cap of {max_homes}", UNKNOWN: "number of homes"},
         "sources": ["scag_he_sites"], "assumption": "max homes per site (assumptions.json site_rules)"},
        _land_lead(site, owner),
        _current_use(site),
    ]
    for c in checks:
        if isinstance(c["text"], dict):
            c["text"] = c["text"][c["result"]]
    hazards = [c["result"] for c in checks if c["kind"] == "hazard"]
    hazard_clear = False if FAIL in hazards else (None if UNKNOWN in hazards else True)
    # ranking tier: 0 = no hazard found (an edge-only overlap counts here; it still loses that check's point),
    # 1 = a hazard layer unchecked, 2 = a hazard overlaps the parcel
    open_unknown = any(c["result"] == UNKNOWN and not c.get("edge") for c in checks if c["kind"] == "hazard")
    hazard_tier = 2 if FAIL in hazards else (1 if open_unknown else 0)
    passed = sum(c["result"] == PASS for c in checks)
    unknowns = [c["text"] for c in checks if c["result"] == UNKNOWN]
    return {"checks": checks, "passed": passed, "hazard_clear": hazard_clear, "hazard_tier": hazard_tier,
            "unknowns": unknowns, "why": why_sentence(checks)}


def why_sentence(checks: list[dict]) -> str:
    good = [c["text"] for c in checks if c["result"] == PASS]
    bad = [c["text"] for c in checks if c["kind"] == "hazard" and (c["result"] == FAIL or c.get("edge"))]
    unk = [c["text"] for c in checks if c["result"] == UNKNOWN and not c.get("edge")]
    hazard_pass = [c for c in checks if c["kind"] == "hazard" and c["result"] == PASS]
    if len(hazard_pass) == 2:  # shorter: merge the two hazard passes
        good = ["clear of flood and fire maps"] + [g for g in good if g not in {c["text"] for c in hazard_pass}]
    parts = []
    if good:
        s = "; ".join(good)
        parts.append(s[0].upper() + s[1:] + ".")
    if bad:
        parts.append("Watch: " + "; ".join(bad) + ".")
    if unk:
        parts.append("Unknown: " + ", ".join(unk) + ".")
    return " ".join(parts) or "No checks could be run."


# ---------------------------------------------------------------------------- ranking
_HAZ_ORDER = {True: 0, None: 1, False: 2}


def _ready_key(r: dict):
    rd = r["ready"]
    return (rd.get("hazard_tier", _HAZ_ORDER[rd["hazard_clear"]]), -rd["passed"], -(r.get("area_score") if r.get("area_score") is not None else -1),
            -(r.get("lower_income") or 0), len(rd["unknowns"]), str(r["id"]))


def _spread_note(values: list, what: str, why_same: str, why_unknown: str) -> str | None:
    known = [v for v in values if v is not None]
    if not values:
        return None
    if not known:
        return f"{what} is unknown for all {len(values):,} sites ({why_unknown}). Showing the 'Ready to call' order instead."
    if len({round(v, 6) for v in known}) == 1:
        return f"{what} is the same for every site ({why_same}). Showing the 'Ready to call' order instead."
    return None


def rank(rows: list[dict], sort_by: str = SORTS[0]) -> dict:
    """Sort rows (each has id, ready, area_score, homes_per_1m, lower_income). Returns {rows, note}.

    `note` says plainly when the chosen sort cannot tell the sites apart, so nobody reads meaning into file order.
    """
    note = None
    if sort_by == "Area benefit":
        note = _spread_note([r.get("area_score") for r in rows], "Area Benefit Score",
                            "every site maps to tracts with the same score", "tract data not loaded")
        key = lambda r: (r.get("area_score") is None, -(r.get("area_score") or 0), _ready_key(r))  # noqa: E731
    elif sort_by == "Homes per $1M of gap":
        note = _spread_note([r.get("homes_per_1m") for r in rows], "Homes per $1M of gap",
                            "no site has its own land cost yet, so every site uses the same ASSUMPTION cost lines",
                            "the gap is incomplete, zero or a surplus")
        key = lambda r: (r.get("homes_per_1m") is None, -(r.get("homes_per_1m") or 0), _ready_key(r))  # noqa: E731
    else:
        key = _ready_key
    return {"rows": sorted(rows, key=key), "note": note}


# ---------------------------------------------------------------------------- hazards for the site card
def hazards(site: dict) -> list[dict]:
    """Flood / fire / fault / historic rows: {test, result, why, sources}. Reuses A's wording from pathways."""
    out = [{**t, "sources": FLOOD_SOURCES} for t in pathways._flood(site, FLOOD_SOURCES[0])]
    out.append({**pathways._fire(site, FIRE_SOURCES[0]), "sources": FIRE_SOURCES})
    for key, label in (("in_fault_zone", "an earthquake fault zone"), ("in_historic_district", "a historic district")):
        t = pathways._flag_absent(site, key, label, "", unchecked="No layer joined yet: not checked")
        out.append({**t, "sources": []})
    return out


# ---------------------------------------------------------------------------- money (same costs both ways)
def budget_price_same_costs(annual_income: float, housing_share: float, annual_rate: float,
                            monthly_fixed_costs: float, property_tax_rate: float,
                            down_payment: float = 0.0, years: int = 30) -> dict:
    """ASSUMED HOUSEHOLD BUDGET price using the SAME 25 CCR 6920 cost items as finance.statutory_price.

    Property tax depends on the price, so solve: share x income / 12 = P&I(loan) + fixed + tax_rate x price / 12.
    Equivalent to finance.family_price(income, rate, share, fixed + tax) at the solved price.
    """
    cap = finance.monthly_payment_cap(annual_income, housing_share)
    k = finance.loan_from_payment(1.0, annual_rate, years)
    t = property_tax_rate / 12
    available = cap - monthly_fixed_costs - t * down_payment
    if available <= 0:  # the non-loan costs already use the whole budget: no price works (not $0)
        return {"monthly_cap": cap, "monthly_fixed_costs": monthly_fixed_costs, "monthly_property_tax": None,
                "monthly_for_loan": None, "loan": None, "price": None,
                "reason": "The non-loan housing costs already use the whole budget: no price works"}
    loan = k * available / (1 + k * t)
    price = loan + down_payment
    tax = t * price
    return {"monthly_cap": cap, "monthly_fixed_costs": monthly_fixed_costs, "monthly_property_tax": tax,
            "monthly_for_loan": cap - monthly_fixed_costs - tax, "loan": loan, "price": price, "reason": None}


def budget_rate_sensitivity(annual_income: float, housing_share: float, rates: list[float],
                            monthly_fixed_costs: float, property_tax_rate: float, total_cost: float,
                            other_sources: float, down_payment: float = 0.0, years: int = 30) -> list[dict]:
    rows = []
    for rate in rates:
        p = budget_price_same_costs(annual_income, housing_share, rate, monthly_fixed_costs, property_tax_rate,
                                    down_payment, years)["price"]
        rows.append({"rate": rate, "family_price": p, "gap": None if p is None else total_cost - p - other_sources})
    return rows


# ---------------------------------------------------------------------------- one-pager
ICON = {PASS: "✅", FAIL: "❌", UNKNOWN: "❔", "yes": "✅ Yes", "no": "❌ No", "maybe": "❔ Maybe"}


def one_pager(site: dict, ev: dict, ready: dict, area_sc: dict, tract: dict | None, money_ctx: dict,
              sources: dict, today: str) -> dict:
    """Structured one-pager: {title, intro, sections: [(heading, [lines])], cited: [source ids]}.

    money_ctx: basis, basis_label, basis_sources, price, price_note, other_sources, cost_total, gap (finance.gap dict),
    homes_per_1m.
    """
    cited: list[str] = []

    def cite(*ids):
        for i in ids:
            if i and i in sources and i not in cited:
                cited.append(i)
        tags = [i for i in ids if i in sources]
        return f" [{', '.join(tags)}]" if tags else ""

    s = site
    cap = he_capacity(s)
    li = cap.get("Low_Income")
    site_lines = [
        f"City: {s.get('city') or 'unknown'} · APN: {s.get('apn') or 'unknown'} · Address: {s.get('address') or 'unknown'}",
        f"Acres: {s.get('acres') if s.get('acres') is not None else 'unknown'} · Zoning: "
        f"{s.get('zoning_local') or 'unknown'} / {s.get('zoning_scag') or 'unknown'}" + cite("scag_zoning"),
    ]
    if cap.get("Total") is not None:
        site_lines.append(
            f"The city counted {int(cap['Total'])} homes here: {int(li or 0)} lower-income, "
            f"{int(cap.get('Moderate_Income') or 0)} moderate, {int(cap.get('Above_Moderate_Income') or 0)} above-moderate"
            + (f" ({(s.get('raw') or {}).get('he_year')} inventory)" if (s.get('raw') or {}).get('he_year') else "")
            + cite("scag_he_sites"))
    else:
        site_lines.append(f"Homes: {s.get('est_homes') if s.get('est_homes') is not None else 'unknown'}" + cite("scag_he_sites"))
    eu = existing_use(s)
    if eu.get("label"):
        site_lines.append(f"In use today: {eu['label']} (SCAG {eu.get('year') or ''} existing land use)" + cite("scag_landuse"))
    sla = surplus_notice(s)
    if s.get("surplus_notice"):
        site_lines.append("Surplus Land Act notice: " + " · ".join(
            f"{k} {sla[k]}" for k in ("agency", "issued", "status") if sla.get(k)) + cite("hcd_sla_notices"))
    if s.get("synthetic"):
        site_lines.insert(0, "SYNTHETIC SITE FOR TESTING. NOT A REAL PARCEL.")

    law = [f"Overall: {ICON[law_verdict(ev)]}, the best of the by-right laws we check ({LAW_NAMES}). "
           "Being on a city's housing-element list is the city's plan, not permission to build."]
    for e in ev.values():
        law.append(f"{e['label']}: {ICON[e['verdict']]}")
        law += [f"    {ICON[t['result']]} {t['test']}: {t['why']}" + cite(t["source"]) for t in e["tests"]]
        # pathway notes carry material requirements (e.g. SB 4 prevailing wage, affordability, Phase I): keep them
        law += [f"    Note: {n if isinstance(n, str) else n.get('text', n)}" for n in e.get("notes") or []]

    hz = [f"{ICON[t['result']]} {t['test']}: {t['why']}" + cite(*t["sources"]) for t in hazards(s)]

    who = []
    if area_sc.get("score") is not None:
        name = (tract or {}).get("name") or s.get("tract_id") or "unknown tract"
        who.append(f"Area Benefit Score: {area_sc['score']} / 100 for {name}. Weights are the team's choice (ASSUMPTION)"
                   + cite("census_acs", "lodes"))
        who += [f"    {p['label']}: {p['value']:,}" for p in area_sc.get("parts", [])]
    else:
        who.append("Area Benefit Score: unknown (no tract data for this site)")
    if area_sc.get("missing"):
        who.append("Not scored (unknown): " + ", ".join(area_sc["missing"]))
    who.append({True: "In a high-quality transit area", False: "Not in a high-quality transit area",
                None: "Transit area: unknown"}[s.get("in_hqta")] + cite("caltrans_hqta"))

    g = money_ctx["gap"]
    gap_text = money(g["gap"]) if g["complete"] else f"incomplete (missing: {missing_label(g)})"
    homes = s.get("est_homes")
    pencil = [
        f"Price basis: {money_ctx['basis_label']}" + cite(*money_ctx.get("basis_sources", [])),
        f"Family can pay: {money(money_ctx['price'])}" + (f" ({money_ctx['price_note']})" if money_ctx.get("price_note") else ""),
        f"Cost to create, per home: {money(money_ctx['cost_total'])} (ASSUMPTION: SYNTHETIC example costs)" + cite("synthetic_deal"),
        f"Other sources, per home: {money(money_ctx['other_sources'])} (ASSUMPTION: SYNTHETIC example)" + cite("synthetic_deal"),
        f"Gap per home: {gap_text}",
    ]
    if g["complete"] and homes:
        pencil.append(f"Gap for all {homes} homes: {money(g['gap'] * homes)} (ASSUMPTION: same gap for every home)")
    hp = money_ctx.get("homes_per_1m")
    pencil.append(f"Homes per $1M of gap funding: {hp:.1f}" if hp else "Homes per $1M of gap funding: n/a")

    unknown_lines: list[str] = []
    for item in ([t["test"] for e in ev.values() for t in e["tests"] if t["result"] == UNKNOWN]
                 + [t["test"] for t in hazards(s) if t["result"] == UNKNOWN] + ready["unknowns"]):
        if item not in unknown_lines:
            unknown_lines.append(item)
    if money_ctx.get("price") is None:
        unknown_lines.append("Family price (" + (money_ctx.get("price_note") or "unknown") + ")")
    unknown_lines += ["Who owns it and whether they would sell or lease (not in free parcel data)",
                      "Whether it has sold or been built since the inventory (lists go stale)",
                      "Real land, construction and fee costs (the gap above uses ASSUMPTION lines)"]

    sections = [
        ("Why call this site", [ready["why"]]),
        ("The site", site_lines),
        ("Can we build? (law)", law),
        ("Hazards checked (not a safety finding)", hz),
        ("Who does it help? (area)", who),
        ("Does it pencil? (per home)", pencil),
        ("What we don't know yet (ask before you rely on this)", unknown_lines),
    ]
    intro = (f"Prototype from Open Ground (Claude Impact Lab, {today}). Not legal, financial or lending advice: "
             "talk to a professional before deciding. ASSUMPTION = placeholder number. Unknown = our data could not answer.")
    return {"title": s.get("name") or s.get("id"), "intro": intro, "sections": sections, "cited": cited}


def one_pager_md(doc: dict, sources: dict) -> str:
    out = [f"# {doc['title']}", "", f"_{doc['intro']}_", ""]
    for head, lines in doc["sections"]:
        out += [f"## {head}", ""]
        for ln in lines:
            out.append(("  - " + ln.strip()) if ln.startswith("    ") else f"- {ln}")
        out.append("")
    out += ["## Sources", ""]
    for i in doc["cited"]:
        src = sources[i]
        out.append(f"- `{i}`: {src['title']}, {src['url']} (checked {src.get('checked', '?')}; {src.get('status', 'UNVERIFIED')})")
    return "\n".join(out) + "\n"


_CSS = """body{font:15px/1.45 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#1d2a24;max-width:760px;
margin:24px auto;padding:0 16px;background:#fff}h1{font-size:22px;margin:0 0 4px}h2{font-size:15px;margin:18px 0 6px;
padding-bottom:3px;border-bottom:1px solid #cfd8d3;color:#1f6f4a}ul{margin:0;padding-left:18px}li{margin:2px 0}
li.sub{list-style:none;margin-left:-4px;color:#44514b;font-size:13.5px}.intro{color:#5b6660;font-size:12.5px;margin-bottom:8px}
.src{font-size:12px;color:#44514b;word-break:break-all}@media print{body{margin:0;max-width:none;font-size:12px}
h2{break-after:avoid}a{color:inherit}}"""


def one_pager_html(doc: dict, sources: dict) -> str:
    e = html.escape
    body = [f"<h1>{e(doc['title'])}</h1>", f"<p class='intro'>{e(doc['intro'])}</p>"]
    for head, lines in doc["sections"]:
        items = "".join(f"<li class='sub'>{e(ln.strip())}</li>" if ln.startswith("    ") else f"<li>{e(ln)}</li>"
                        for ln in lines)
        body.append(f"<h2>{e(head)}</h2><ul>{items}</ul>")
    srcs = "".join(
        f"<li><code>{e(i)}</code>: {e(sources[i]['title'])}, <a href='{e(sources[i]['url'])}'>{e(sources[i]['url'])}</a> "
        f"(checked {e(sources[i].get('checked', '?'))}; {e(sources[i].get('status', 'UNVERIFIED'))})</li>"
        for i in doc["cited"])
    body.append(f"<h2>Sources</h2><ul class='src'>{srcs}</ul>")
    return (f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' "
            f"content='width=device-width,initial-scale=1'><title>{e(doc['title'])} · Open Ground</title>"
            f"<style>{_CSS}</style></head><body>{''.join(body)}</body></html>")
