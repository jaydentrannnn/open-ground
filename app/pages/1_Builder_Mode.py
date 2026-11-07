"""Builder mode: which sites should a small nonprofit call first, why, and what is the gap per home.

OWNER: Builder B (layout redesigned by C, 2026-11-07). Uses core/*. Logic lives in core/builder.py
(tested in tests/test_builder.py); this file is layout only.
Layout: filter row · 3 call-first tiles · map + shortlist · site card in a pop-up (tabs) · how we rank.
"""
import datetime
import time

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from core import area, builder, contracts, finance, parcels, pathways, ui

STAT, BUDGET = "Statutory benchmark", "Assumed household budget"
FIXED_KEYS = ("fire_casualty_insurance", "maintenance_repairs", "utilities_allowance", "hoa_fees", "loan_insurance",
              "space_rent")
TIER_LABEL = {"extremely_low": "Extremely low", "very_low": "Very low", "low": "Low", "moderate": "Moderate",
              "above_moderate": "Above moderate"}
MAP_LIMIT = 50
HAZARD_WORD = {True: "clear of flood and fire maps", None: "hazards not fully checked, or only touching the edge",
               False: "in a flood or fire zone"}


def data_stamp() -> tuple:
    """Modified times of every data file, so a new file from A or C shows on the next rerun (no restart)."""
    files = [contracts.DATA / "sources.json",
             *sorted([*contracts.PROCESSED.glob("*.json"), *contracts.PROCESSED.glob("*.geojson")])]
    return tuple((p.name, p.stat().st_mtime) for p in files if p.exists())


@st.cache_resource(max_entries=1, show_spinner="Loading sites…")
def load(stamp: tuple):  # stamp is part of the cache key (no leading underscore)
    """Static data + per-site law checks and area scores (do not mutate the returned objects)."""
    sites = contracts.load_sites()
    tracts = contracts.load_tracts()
    evals = {s["id"]: pathways.evaluate(s) for s in sites}
    areas = {s["id"]: area.score(tracts.get(s.get("tract_id"))) for s in sites}
    return (sites, tracts, evals, areas, contracts.load_income_limits(), contracts.load_rates(),
            [p for p in contracts.load_programs() if "builder" in p["mode"]], contracts.load_assumptions(),
            contracts.load_sources())


@st.cache_resource
def outline_store() -> dict:
    """Parcel outlines fetched so far, shared across sessions: {site_id: geometry, or None = no parcel row}."""
    return {"_failed_at": 0.0}


def parcel_outlines(site_list: list) -> dict:
    """Real parcel outlines for these sites: one SCAG request for the ones not fetched yet. If SCAG fails, nothing is
    stored and we wait 2 minutes before asking again, so a down server never slows every click."""
    store = outline_store()
    missing = [s for s in site_list if s["id"] not in store]
    if missing and time.time() - store["_failed_at"] > 120:
        got = parcels.outlines(missing)
        if got is None:
            store["_failed_at"] = time.time()
        else:
            store.update({s["id"]: got.get(s["id"]) for s in missing})  # no PID/APN to ask with = None too
    return {s["id"]: store.get(s["id"]) for s in site_list}


def card_map(s: dict):
    """Square, zoomable map of one lot: its real parcel outline (SCAG), or a dashed ring when unavailable."""
    if s.get("lat") is None or s.get("lon") is None:
        ui.unknown("No coordinates for this site, so no map.")
        return
    shape = parcel_outlines([s]).get(s["id"])
    m = folium.Map(location=[s["lat"], s["lon"]], zoom_start=18, max_zoom=19, tiles="OpenStreetMap",
                   control_scale=True)
    if shape:
        folium.GeoJson(shape, style_function=lambda _: {"color": "#0E4449", "weight": 3, "fillColor": ui.ACCENT,
                                                        "fillOpacity": 0.35}).add_to(m)
        m.fit_bounds(parcels.bounds(shape), padding=(40, 40), max_zoom=19)
    else:
        folium.CircleMarker([s["lat"], s["lon"]], radius=18, color="#0E4449", weight=3, fill=False,
                            dash_array="5").add_to(m)
    folium.CircleMarker([s["lat"], s["lon"]], radius=5, color="#ffffff", weight=2, fill=True,
                        fill_color=ui.RANK_RAMP[0], fill_opacity=1).add_to(m)
    st_folium(m, height=470, use_container_width=True, returned_objects=[], key=f"cardmap-{s['id']}")
    st.caption("Parcel outline from SCAG's zoning-parcel layer. Scroll or use + / − to zoom." if shape else
               "Parcel outline unavailable right now: the dot is the site's mapped point, not a boundary.")


sites, tracts, EVALS, AREAS, limits, rates, programs, A, SRC = load(data_stamp())
rate_pt = contracts.latest_rate(rates)
fam = A["family"]
S = A["statutory_housing_cost"]
ss = st.session_state
ss.setdefault("edits", {})  # {site_id: {cost line: value}}: survives the pop-up closing
ss.setdefault("gen", 0)  # bumped when a card closes: fresh map + shortlist widgets, so the same site can reopen

# ---------------------------------------------------------------- header
ui.header("Open Ground · Builder mode", "Which sites should we call first?")
ui.sample_banner()

# ---------------------------------------------------------------- filter row
cities = sorted({s["city"] for s in sites if s.get("city")})
f = st.columns([2.2, 1.5, 2.2, 1.35, 1.15, 1.15], vertical_alignment="bottom")
pick_cities = f[0].multiselect("City", cities, default=[], placeholder="All cities")
sort_by = f[1].selectbox("Rank by", builder.SORTS,
                         help="Ready to call: hazards clear first, then most checks passed, then area benefit, "
                              "then lower-income homes. See 'How we rank' at the bottom.")
want = f[2].multiselect("Law pathway", [v[0] for v in pathways.PATHWAYS.values()], default=[],
                        placeholder="Any pathway", help="Keep sites where this pathway is not ruled out")
hide_hazard = f[3].toggle("Hide flood / fire", value=False,
                          help="Hide sites inside a FEMA flood zone or a very-high fire hazard zone")
with f[4].popover("More filters", width="stretch"):
    max_homes = st.number_input("Max homes per site · ASSUMPTION", 1, 200,
                                A["site_rules"]["max_homes_default"]["value"],
                                help=A["site_rules"]["max_homes_default"]["basis"])
    hide_no = st.checkbox("Hide sites where every pathway says No", value=True)
    hide_houses = st.checkbox(f"Hide existing houses where the city plans {builder.SMALL_HOUSE_MAX_HOMES} or fewer homes",
                              value=True,
                              help="SCAG 2024 land use says a single-family home is there today: likely someone's house "
                                   "with room for an ADU or lot split, not a site to buy. The cutoff is an ASSUMPTION.")
with f[5].popover("Family & loan", width="stretch"):
    basis = st.radio("Family price that drives the gap", [STAT, BUDGET],
                     help="Statutory = the legal affordable housing cost cap, HSC 50052.5(b). "
                          "Budget = a share of this family's income (ASSUMPTION). Both use the same 25 CCR 6920 costs.")
    hh = st.selectbox("Household size", list(range(1, 9)), index=fam["household_size"]["value"] - 1)
    income = st.number_input("Family income ($/yr) · ASSUMPTION", 10000, 300000, fam["annual_income"]["value"], 1000)
    tier = finance.income_tier(income, hh, limits)
    lrow = limits["by_household_size"].get(str(hh), {})
    if tier is None:
        st.caption("Income tier: unknown (no HCD row for this size)")
    elif tier == "above_moderate":
        st.caption(f"Above moderate income for {hh}: over {ui.money(lrow.get('moderate'))}")
    else:
        st.caption(f"**{TIER_LABEL[tier]} income** for {hh} {'person' if hh == 1 else 'people'}: at or under "
                   f"{ui.money(lrow.get(tier))} (HCD State Income Limits 2026, memo {limits.get('memo_date')})")
    beds = st.selectbox("Bedrooms in the home", [0, 1, 2, 3, 4], index=fam["bedrooms"]["value"],
                        help="HSC 50052.5(h) sizes the statutory cap by bedrooms (3BR = household of 4)")
    share = st.slider("Budget: share of income for housing · ASSUMPTION", 0.25, 0.35, fam["housing_share"]["value"], 0.01)
    use_habitat_rate = st.toggle("Use a below-market Habitat rate", value=False,
                                 help="Habitat OC's real rate is UNKNOWN. Ask them.")
    rate = (st.number_input("Habitat rate (%) · ASSUMPTION", 0.0, 10.0,
                            fam["below_market_rate_placeholder"]["value"] * 100, 0.25,
                            help=fam["below_market_rate_placeholder"]["basis"]) / 100) if use_habitat_rate \
        else st.number_input(f"Market rate (%) · PMMS {rate_pt['date']}", 0.0, 12.0, rate_pt["rate_30yr"] * 100, 0.05) / 100

# ---------------------------------------------------------------- money (same for all sites until per-site costs exist)
years = fam["term_years"]["value"]
fixed = sum(S[k]["value"] for k in FIXED_KEYS)
tax_rate = S["property_tax_rate"]["value"]
down = S["down_payment"]["value"]
sp = finance.statutory_price(income, hh, beds, limits, rate, fixed, tax_rate, down_payment=down, years=years)
bp = builder.budget_price_same_costs(income, share, rate, fixed, tax_rate, down, years)
statutory = basis == STAT
price = sp["price"] if statutory else bp["price"]
price_note = sp.get("reason") if statutory and sp["price"] is None else (
    bp.get("reason") if not statutory and bp["price"] is None else None)
if statutory:
    basis_label = (f"Statutory benchmark · {sp['citation']} (FindLaw copy, checked 2026-11-07) · HCD State Income Limits, "
                   f"memo {limits.get('memo_date')}") if sp.get("citation") else "Statutory benchmark · HSC 50052.5(b): not applicable"
    basis_sources = ["findlaw_hsc_50052_5", "hsc_50052_5", "ccr_25_6920", "hcd_income_2026", "pmms"]
else:
    basis_label = f"Assumed household budget · {share:.0%} of {ui.money(income)}/yr (ASSUMPTION)"
    basis_sources = ["lane3_brief", "ccr_25_6920", "pmms"]
basis_short = "statutory price" if statutory else "household budget"
cost_defaults = {k: v["value"] for k, v in A["cost_per_home_defaults"].items() if isinstance(v, dict)}
other_defaults = {k: v["value"] for k, v in A["other_sources_per_home_defaults"].items()}


def site_costs(site: dict) -> dict:
    """Defaults = synthetic worked example. Only a SOURCED per-site land cost overrides the land line.
    Vacant or parking sites: lines that assume an existing building become unknown (builder.adjust_for_site)."""
    c = dict(cost_defaults)
    if site.get("land_cost_per_home") is not None:
        c["land_and_building_purchase"] = site["land_cost_per_home"]
    return builder.adjust_for_site(c, other_defaults, site)[0]


def site_other(site: dict) -> dict:
    """Other sources per home (subsidy, rent while waiting), adjusted for this site like site_costs()."""
    return builder.adjust_for_site(cost_defaults, other_defaults, site)[1]


def effective_other(site: dict) -> dict:
    """site_other() plus the user's edits for this site, stored like effective_costs() under 'other:<line>'."""
    mine = ss["edits"].get(site["id"], {})
    return {k: mine.get(f"other:{k}", v) for k, v in site_other(site).items()}


def known_total(d: dict) -> float:
    return sum(v for v in d.values() if v is not None)


def effective_costs(site: dict) -> dict:
    """site_costs() plus the user's edits for this site. Shortlist, tiles, card, rate table and one-pager all use
    this, so every view shows the same gap. An unknown (None) line stays unknown until the user types a value.
    Edits live in ss["edits"], not in widget keys, so they survive the pop-up closing."""
    mine = ss["edits"].get(site["id"], {})
    return {k: mine.get(k, v) for k, v in site_costs(site).items()}


def save_edit(sid: str, k: str):
    ss["edits"].setdefault(sid, {})[k] = ss[f"w-{sid}-{k}"]


def gap_text(g: dict) -> str:
    if not g["complete"]:
        return "incomplete"
    return ui.money(g["gap"]) if g["gap"] >= 0 else f"{ui.money(-g['gap'])} surplus"


# ---------------------------------------------------------------- rows + ranking
rows = []
for s in sites:
    if pick_cities and s.get("city") not in pick_cities:
        continue
    ev = EVALS[s["id"]]
    best = pathways.best_verdict(ev)
    if hide_no and best == "no":
        continue
    if want and not any(e["label"] in want and e["verdict"] != "no" for e in ev.values()):
        continue
    if hide_houses and builder.small_existing_house(s):
        continue
    ready = builder.readiness(s, max_homes)
    if hide_hazard and ready["hazard_clear"] is False:
        continue
    g = finance.gap(effective_costs(s), {"family_price": price, **effective_other(s)})
    rows.append({"id": s["id"], "site": s, "ev": ev, "best": best, "ready": ready, "gap": g,
                 "area_score": AREAS[s["id"]]["score"], "lower_income": builder.lower_income_homes(s),
                 "homes_per_1m": finance.families_per_million(g["gap"]) if g["complete"] else None})

ranked = builder.rank(rows, sort_by)
rows = ranked["rows"]
scope = ", ".join(pick_cities) if pick_cities else "all of Orange County"
st.caption(f"**{len(rows):,}** sites in {scope} · ranked by **{sort_by}** · gap uses the **{basis_short}**"
           + (f" · {ranked['note']}" if ranked["note"] else ""))
if not rows:
    st.info("No sites match these filters.")
    st.stop()
ids = [r["id"] for r in rows]
by_id = {r["id"]: r for r in rows}
if ss.get("focus") not in by_id:
    ss["focus"] = None


def open_card(sid):
    """Open the pop-up. It stays open across full reruns (the map redraws when it zooms) until the user closes it."""
    ss["focus"] = sid
    ss["card"] = sid


def close_card():
    ss["card"] = None
    ss["gen"] += 1  # new map/shortlist keys clear the old click and row selection
    ss["_last_map"] = ss["_last_row"] = None


# ---------------------------------------------------------------- call these 3 first
picks = builder.call_first(rows)  # nearby listed sites (within NEIGHBOUR_M) fold into one call
call_no = {p["row"]["id"]: i + 1 for i, p in enumerate(picks)}
for i, (col, pick) in enumerate(zip(st.columns(3), picks)):
    r = pick["row"]
    s = r["site"]
    li = r["lower_income"]
    new_build_gap = not r["gap"]["complete"] and builder.new_build_site(s)
    with col.container(border=True, key=f"tile-top-{i}"):
        ui.eyebrow(f"Call first · #{i + 1}")
        st.markdown(f"**{s['name']}**")
        ui.stats([("Homes", s.get("est_homes") if s.get("est_homes") is not None else "unknown"),
                  ("Checks", f"{r['ready']['passed']}/{builder.N_CHECKS}"),
                  ("Gap / home · ASSUMPTION", gap_text(r["gap"]))])
        st.caption(f"{li if li is not None else 'Unknown'} lower-income homes in the city's plan · "
                   f"{HAZARD_WORD[r['ready']['hazard_clear']]}")
        if new_build_gap:
            st.caption("Gap incomplete: vacant or parking today, so the new-build cost is unknown.")
        nb = builder.neighbours_line(pick["neighbours"])
        if nb:
            st.caption(f"📍 {nb}")
        st.button("Open site card", key=f"open-{r['id']}", on_click=open_card, args=(r["id"],), width="stretch")

# ---------------------------------------------------------------- map (left) + shortlist (right)
left, right = st.columns([1.1, 1], gap="medium")
with left:
    on_map = [(n, r) for n, r in enumerate(rows[:MAP_LIMIT]) if r["site"].get("lat") is not None
              and r["site"].get("lon") is not None]
    focus = by_id.get(ss["focus"])
    shown = on_map + ([(ids.index(focus["id"]), focus)] if focus and focus["id"] not in {r["id"] for _, r in on_map}
                      and focus["site"].get("lat") is not None else [])
    shapes = parcel_outlines([r["site"] for _, r in shown])
    total = max(len(rows[:MAP_LIMIT]), 1)
    m = folium.Map(location=[33.70, -117.85], zoom_start=10, max_zoom=19, tiles="OpenStreetMap", control_scale=True)
    feats = [{"type": "Feature", "geometry": shapes[r["id"]],
              "properties": {"fill": ui.rank_color(n, total), "tip": f"#{n + 1} {r['site']['name']}"}}
             for n, r in shown if shapes.get(r["id"])]
    if feats:  # every lot's real outline, shaded by rank: visible once you zoom in
        folium.GeoJson({"type": "FeatureCollection", "features": feats},
                       style_function=lambda ft: {"color": "#0E4449", "weight": 1.5,
                                                  "fillColor": ft["properties"]["fill"], "fillOpacity": 0.6},
                       tooltip=folium.GeoJsonTooltip(fields=["tip"], labels=False)).add_to(m)
    if focus and focus["site"].get("lat") is not None:
        folium.CircleMarker([focus["site"]["lat"], focus["site"]["lon"]], radius=16, color="#0E4449", weight=3,
                            fill=False, dash_array="5", tooltip=f"Last opened: {focus['site']['name']}").add_to(m)
    for n, r in sorted(shown, key=lambda x: (x[1]["id"] in call_no, -x[0])):  # calls last, so they sit on top
        s = r["site"]
        k = call_no.get(r["id"])
        tip = (f"{'Call ' + str(k) + ' · ' if k else ''}#{n + 1} {s['name']} · {r['ready']['passed']}/"
               f"{builder.N_CHECKS} checks · {HAZARD_WORD[r['ready']['hazard_clear']]}")
        if k:
            folium.Marker([s["lat"], s["lon"]], tooltip=tip, popup=s["name"], icon=folium.DivIcon(
                icon_size=(26, 26), icon_anchor=(13, 13),
                html=f"<div style='background:{ui.RANK_RAMP[0]};color:#fff;border:2px solid #fff;border-radius:50%;"
                     f"width:26px;height:26px;line-height:22px;text-align:center;font:600 12px Geist,sans-serif;"
                     f"box-shadow:0 0 0 1px #0E4449'>{k}</div>")).add_to(m)
        else:
            folium.CircleMarker([s["lat"], s["lon"]], radius=6, color="#0E4449", weight=1, fill=True,
                                fill_color=ui.rank_color(n, total), fill_opacity=0.95,
                                tooltip=tip, popup=s["name"]).add_to(m)
    if on_map:
        lats = [r["site"]["lat"] for _, r in on_map]
        lons = [r["site"]["lon"] for _, r in on_map]
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]], padding=(20, 20))
    clicked = st_folium(m, height=520, use_container_width=True, returned_objects=["last_object_clicked_popup"],
                        key=f"map-{ss['gen']}")
    if not on_map:
        st.info("None of these sites has coordinates: use the shortlist.")
    st.caption(f"Top {min(len(rows), MAP_LIMIT)} of {len(rows):,} sites. Darker = ranked higher · numbers = call first "
               "· zoom in to see each lot's real outline (SCAG) · click a dot to open its card.")
    name_to_id = {r["site"]["name"]: r["id"] for _, r in shown}  # popups show the name (unique), not the raw id
    pid = name_to_id.get((clicked or {}).get("last_object_clicked_popup"))
    if pid and pid != ss.get("_last_map"):
        ss["_last_map"] = pid
        open_card(pid)
        st.rerun()

with right:
    df = pd.DataFrame([{
        "#": n + 1, "Site": r["site"]["name"], "Homes": r["site"].get("est_homes"),
        "Checks": r["ready"]["passed"], "Area": r["area_score"],
    } for n, r in enumerate(rows)])
    # a new key when the filters change, so an old row selection can't open the wrong site
    fkey = abs(hash((tuple(ids), ss["gen"])))  # new order (filters, cost edits) or a closed card = no stale row
    event = st.dataframe(
        df, hide_index=True, width="stretch", height=560, on_select="rerun", selection_mode="single-row",
        key=f"shortlist-{fkey}",
        column_config={
            "#": st.column_config.NumberColumn("#", width=40),
            "Site": st.column_config.TextColumn("Site", width=230, help="City and parcel number (APN)"),
            "Homes": st.column_config.NumberColumn("Homes", width=64,
                                                   help="Homes the city's housing plan counted here (SCAG). Blank = unknown"),
            "Checks": st.column_config.ProgressColumn("Checks", min_value=0, max_value=builder.N_CHECKS,
                                                      format=f"%d / {builder.N_CHECKS}", width=96,
                                                      help="Readiness checks passed (hazards, transit, plan, size, "
                                                           "land lead, vacant). Unknown never counts as a pass."),
            "Area": st.column_config.ProgressColumn("Area benefit", min_value=0, max_value=100, format="%d", width=96,
                                                    help="Area Benefit Score 0–100 for the census tract. Weights are "
                                                         "an ASSUMPTION. Blank = no tract data"),
        })
    st.caption("Select a row to open its site card.")
    sel = event.selection.rows if event else []
    sel_id = ids[sel[0]] if sel and sel[0] < len(ids) else None
    if sel_id and sel_id != ss.get("_last_row"):
        ss["_last_row"] = sel_id
        open_card(sel_id)
        st.rerun()


# ---------------------------------------------------------------- site card (pop-up)
def card_body(sid: str):
    r = by_id[sid]
    s, ev, rd = r["site"], r["ev"], r["ready"]
    cost = effective_costs(s)
    other = effective_other(s)
    other_total = known_total(other)
    g = finance.gap(cost, {"family_price": price, **other})
    fpm = finance.families_per_million(g["gap"]) if g["complete"] else None

    info, side = st.columns([1.35, 1], gap="medium")
    with side:
        card_map(s)
    with info:
        ui.eyebrow(f"Ranked #{ids.index(sid) + 1} of {len(rows):,} · {sort_by} · {s.get('city') or 'city unknown'}")
        ui.facts([("APN", s.get("apn") or "unknown"), ("Address", s.get("address") or "unknown"),
                  ("Acres", s.get("acres") if s.get("acres") is not None else "unknown"),
                  ("Zoning", f"{s.get('zoning_local') or 'unknown'} / {s.get('zoning_scag') or 'unknown'}"),
                  ("Homes", s.get("est_homes") if s.get("est_homes") is not None else "unknown"),
                  ("Gap / home", gap_text(g))])
        st.markdown(f"**Why call:** {rd['why']}")
        card_nb = builder.neighbours_line(builder.neighbours(r, rows))
        if card_nb:
            st.caption(f"📍 {card_nb}")
        if s.get("synthetic"):
            st.error("SYNTHETIC site for testing. Not a real parcel.")
        if (s.get("est_homes") or 0) > max_homes:
            st.warning(f"{s.get('est_homes')} homes is above your max of {max_homes}. See the SB 4 notes under "
                       "*Can we build?*")

        t_law, t_haz, t_area, t_money, t_doc = st.tabs(["Can we build?", "Hazards", "Who it helps", "Does it pencil?",
                                                        "One-pager"])
        with t_law:
            st.markdown(f"Can we build? {ui.verdict_badge(builder.law_verdict(ev))}")
            st.caption(f"Best of the by-right laws we check ({builder.LAW_NAMES}). Being on a city's housing-element "
                       "list is the city's plan, not permission to build.")
            for e in ev.values():
                n = {k: sum(t["result"] == k for t in e["tests"]) for k in ("pass", "fail", "unknown")}
                st.markdown(f"{ui.verdict_badge(e['verdict'])} **{e['label']}** · {n['pass']} pass · {n['fail']} fail · "
                            f"{n['unknown']} unknown")
            with st.expander("Every law check, with the reason"):
                for e in ev.values():
                    st.markdown(f"**{e['label']}** {ui.verdict_badge(e['verdict'])}")
                    st.dataframe(pd.DataFrame([{"": ui.ICON[t["result"]], "test": t["test"], "why": t["why"]}
                                               for t in e["tests"]]), hide_index=True, width="stretch")
                    for note in e.get("notes") or []:
                        st.caption(f"Note: {note if isinstance(note, str) else note.get('text', note)}")
                    ui.source_line(sorted({t["source"] for t in e["tests"] if t.get("source")}))

        with t_haz:
            hz = builder.hazards(s)
            worst = "fail" if any(t["result"] == "fail" for t in hz) else (
                "unknown" if any(t["result"] == "unknown" for t in hz) else "pass")
            st.markdown({"fail": ui.chip("fail", "a hazard overlaps"), "unknown": ui.chip("unknown", "partly unchecked"),
                         "pass": ui.chip("pass", "clear on every map we checked")}[worst]
                        + " · hazards checked, not a safety finding")
            for t in hz:
                st.markdown(f"{ui.chip(t['result'])} **{t['test']}**  \n<small>{t['why']}</small>", unsafe_allow_html=True)
            ui.source_line(["oc_floodplains", *builder.FIRE_SOURCES])

        with t_area:
            sc = AREAS[sid]
            tract = tracts.get(s.get("tract_id")) or {}
            a1, a2 = st.columns(2)
            a1.metric("Area Benefit Score", f"{sc['score']} / 100" if sc["score"] is not None else "unknown",
                      help="Weights are the team's choice (ASSUMPTION); see core/area.py")
            a2.metric("Lower-income homes in the city's plan",
                      r["lower_income"] if r["lower_income"] is not None else "unknown")
            if tract.get("synthetic"):
                st.caption("SYNTHETIC tract data")
            if sc["parts"]:
                st.dataframe(pd.DataFrame([{"metric": p["label"], "value": p["value"], "weight": p["weight"]}
                                           for p in sc["parts"]]), hide_index=True, width="stretch",
                             column_config={"value": st.column_config.NumberColumn(format="%.1f", width="small"),
                                            "weight": st.column_config.NumberColumn(format="%.2f", width="small")})
            if sc["score"] is None:
                ui.unknown(f"No tract data for {s.get('tract_id') or 'this site'} yet.")
            elif sc["missing"]:
                ui.unknown("Not scored: " + ", ".join(sc["missing"]))
            st.caption(f"{tract.get('name') or s.get('tract_id') or 'Tract unknown'}")
            ui.source_line(["census_acs", "lodes"])
            cap = builder.he_capacity(s)
            if cap.get("Total") is not None:
                st.markdown(f"The city counted **{int(cap['Total'])} homes** here: {int(cap.get('Low_Income') or 0)} "
                            f"lower-income · {int(cap.get('Moderate_Income') or 0)} moderate · "
                            f"{int(cap.get('Above_Moderate_Income') or 0)} above-moderate")
            eu = builder.existing_use(s)
            sla = builder.surplus_notice(s)
            if s.get("surplus_notice"):
                st.markdown("Surplus Land Act notice: " + " · ".join(f"{k} **{sla[k]}**"
                                                                     for k in ("agency", "issued", "status") if sla.get(k)))
            st.markdown(f"Near frequent transit: {ui.yes_no(s.get('in_hqta'))} · In use today: "
                        + (f"**{eu['label']}**" if eu.get("label") else ui.yes_no(None)))
            ui.source_line(["scag_he_sites", "hcd_sla_notices", "caltrans_hqta", "scag_landuse"])

        with t_money:
            p1, p2 = st.columns(2)
            p1.metric(f"{STAT}{' (used)' if statutory else ''}", ui.money(sp["price"]),
                      help="Highest price whose 25 CCR 6920 housing cost fits the HSC 50052.5(b) cap")
            p2.metric(f"{BUDGET}{' (used)' if not statutory else ''}", ui.money(bp["price"]),
                      help=f"{share:.0%} of {ui.money(income)}/yr = {ui.money(bp['monthly_cap'])}/mo, same costs (ASSUMPTION)")
            if sp.get("citation"):
                st.caption(f"Statutory benchmark · {sp['citation']} (FindLaw copy, checked 2026-11-07) · HCD State Income "
                           f"Limits, memo {limits.get('memo_date')} · tier **{TIER_LABEL.get(sp['tier'], sp['tier'])}** · "
                           f"cap {ui.money(sp['monthly_cap'])}/mo")
            if sp["price"] is None and sp.get("reason"):
                ui.unknown(f"Statutory price: {sp['reason']}")
            for note in sp.get("notes") or []:
                st.caption(f"Note: {note}")
            g1, g2, g3 = st.columns(3)
            g1.metric("Gap per home" if not g["complete"] or g["gap"] >= 0 else "Surplus per home",
                      gap_text(g).replace(" surplus", ""))
            homes = s.get("est_homes")
            g2.metric(f"Gap, all {homes or '?'} homes", ui.money(g["gap"] * homes) if g["complete"] and homes else "unknown",
                      help="Same gap for every home: ASSUMPTION")
            g3.metric("Homes per $1M of gap", f"{fpm:.1f}" if fpm else ("no gap" if g["complete"] else "unknown"))
            if not g["complete"]:
                ui.unknown(f"Missing: {builder.missing_label(g)}. The gap can't be totalled.")
                if builder.new_build_site(s):
                    st.caption(builder.NEW_BUILD_REASON + " Type real numbers under *Edit the cost lines*.")
            st.markdown(f"Cost to create {ui.money(sum(v for v in cost.values() if v is not None))}"
                        f"{' (incomplete)' if any(v is None for v in cost.values()) else ''} − family "
                        f"{ui.money(price)} − other sources {ui.money(other_total)}"
                        f"{' (incomplete)' if any(v is None for v in other.values()) else ''}, per home")
            ui.assumption("Cost lines and other sources are copied from the event's SYNTHETIC worked example: the same for "
                          f"every site until a real per-site cost exists. Housing-cost items per 25 CCR 6920 (Cornell LII "
                          f"copy, read 2026-11-07): {ui.money(fixed)}/mo + {tax_rate:.1%}/yr property tax, all placeholders.")
            ui.source_line([*basis_sources, "synthetic_deal"])

            with st.expander("Edit the cost lines (use a real deal)"):
                cc = st.columns(2)
                for i, k in enumerate(site_costs(s)):
                    cc[i % 2].number_input(k.replace("_", " "), 0, 2_000_000, None if cost[k] is None else int(cost[k]),
                                           5000, key=f"w-{sid}-{k}", placeholder="unknown: type a number",
                                           on_change=save_edit, args=(sid, k))
                st.caption("Other sources, per home (subsidy, rent while waiting)")
                oc = st.columns(2)
                for i, k in enumerate(site_other(s)):
                    oc[i % 2].number_input(k.replace("_", " "), 0, 2_000_000, None if other[k] is None else int(other[k]),
                                           5000, key=f"w-{sid}-other:{k}", placeholder="unknown: type a number",
                                           on_change=save_edit, args=(sid, f"other:{k}"))
            with st.expander(f"If the rate moves ({basis_short})"):
                rlist = [max(rate + d, 0.0) for d in (-0.01, -0.005, 0, 0.005, 0.01)]
                if any(v is None for v in [*cost.values(), *other.values()]):
                    ui.unknown("The rate table needs every cost and other-source line: fill the unknown ones above.")
                else:
                    total_cost = sum(cost.values())
                    sens = (finance.statutory_rate_sensitivity(income, hh, beds, limits, rlist, fixed, tax_rate, total_cost,
                                                               other_total, down, years) if statutory else
                            builder.budget_rate_sensitivity(income, share, rlist, fixed, tax_rate, total_cost, other_total,
                                                            down, years))
                    st.dataframe(pd.DataFrame([{"rate": f"{x['rate']:.2%}", "family price": ui.money(x["family_price"]),
                                                "gap per home": ui.money(x["gap"])} for x in sens]), hide_index=True,
                                 width="stretch")
            with st.expander("Who could close the gap (funds unconfirmed)"):
                st.dataframe(pd.DataFrame([{k: p[k] for k in ("name", "who_applies", "max", "status")} for p in programs]),
                             hide_index=True, width="stretch")
            with st.expander("What a donor's gift covers"):
                gift = st.number_input("A donor gives…", 0, 1_000_000, 25000, 5000, key=f"gift-{sid}")
                for line in finance.gift_coverage(gift, cost):
                    st.write(f"• {ui.money(line['covered'])} covers {line['share_of_line']:.0%} of "
                             f"*{line['line'].replace('_', ' ')}*")

        with t_doc:
            doc = builder.one_pager(s, ev, rd, AREAS[sid], tracts.get(s.get("tract_id")), {
                "basis_label": basis_label, "basis_sources": basis_sources, "price": price, "price_note": price_note,
                "other_sources": other_total, "cost_total": sum(v for v in cost.values() if v is not None), "gap": g,
                "homes_per_1m": fpm}, SRC, datetime.date.today().isoformat())
            md = builder.one_pager_md(doc, SRC)
            st.caption("A draft to send a congregation or a funder. Review it before you send it; open the .html in a "
                       "browser and print to PDF.")
            d1, d2 = st.columns(2)
            d1.download_button("Download one-pager (.md)", md, file_name=f"{sid}.md", mime="text/markdown",
                               width="stretch", on_click="ignore")
            d2.download_button("Download print-ready page (.html)", builder.one_pager_html(doc, SRC),
                               file_name=f"{sid}.html", mime="text/html", width="stretch", on_click="ignore")
            with st.container(border=True, height=420):
                st.markdown(md)


card = ss.get("card")
if card in by_id:
    st.dialog(by_id[card]["site"]["name"], width="large", on_dismiss=close_card)(card_body)(card)
elif card is not None:
    close_card()  # the site left the list (filters changed)

# ---------------------------------------------------------------- how we rank + about the data
with st.expander("How we rank, and what we can't rank on yet"):
    st.markdown(
        "**Ready to call** sorts sites clear of flood and fire maps first (a hazard touching under "
        f"{builder.EDGE_PCT:g}% of the parcel counts as 'check the map', an ASSUMPTION), then by how many of seven checks pass, "
        "then by Area Benefit Score, then by lower-income homes in the city's plan. **Unknown never counts as a pass.**\n\n"
        "1. Clear of FEMA flood zones · 2. Clear of very-high fire zones · 3. Near frequent transit · "
        "4. City planned lower-income homes here · 5. Fits your max homes (ASSUMPTION) · "
        "6. Land lead: place of worship mapped here (SB 4, never proof of ownership) or a Surplus Land Act notice · "
        "7. Vacant land or a parking lot today")
    ui.source_line(["oc_floodplains", *builder.FIRE_SOURCES, "caltrans_hqta", "scag_he_sites", "osm_worship",
                    "hcd_sla_notices", "scag_landuse"])
    st.caption(f"'Call these 3 first' skips a site within {builder.NEIGHBOUR_M:.0f} m of a higher pick and lists it on "
               f"that card instead (ASSUMPTION). Above {builder.DENSITY_WATCH:.0f} homes per acre (ASSUMPTION) the reason says "
               "the city's count may cover several parcels.")
    st.caption("Homes per $1M of gap can't separate sites yet: no site has its own land cost, so all use the same "
               "SYNTHETIC cost lines. It will rank on its own once real per-site costs land.")
if not contracts.using_sample_sites():
    with st.expander("About the data"):
        he = SRC.get("scag_he_sites", {})
        status = he.get("status", "")
        missing_cities = status.split("NOT in layer:")[1].strip() if "NOT in layer:" in status else None
        n_cities = len({s.get("city") for s in sites if s.get("city")})
        n_he = sum(1 for s in sites if s.get("housing_element_site"))
        n_sla = sum(1 for s in sites if s.get("surplus_notice"))
        st.markdown(f"**Real data:** {len(sites):,} Orange County sites in {n_cities} jurisdictions: {n_he:,} on city "
                    f"housing-element inventories (SCAG, checked {he.get('checked', '?')}) and {n_sla:,} with a Surplus "
                    f"Land Act notice (HCD).")
        if missing_cities:
            st.markdown(f"Cities missing from the SCAG inventory layer: **{missing_cities}**.")
        st.markdown("Parcel outlines on the map are fetched live from SCAG's public zoning-parcel layer when you open a "
                    "site (no key). If it fails, the map shows a dashed ring and says the outline is unavailable.")
        ui.source_line([parcels.SOURCE_ID])
