"""Builder mode: which sites should a small nonprofit call first, why, and what is the gap per home.

OWNER: Builder B. Uses core/* (read-only for B except ui.py and builder.py).
Logic lives in core/builder.py (tested in tests/test_builder.py); this file is layout only.
"""
import datetime

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from core import area, builder, contracts, finance, pathways, ui

st.set_page_config(page_title="Builder mode · Open Ground", page_icon="🏗️", layout="wide")

STAT, BUDGET = "Statutory benchmark", "Assumed household budget"
FIXED_KEYS = ("fire_casualty_insurance", "maintenance_repairs", "utilities_allowance", "hoa_fees", "loan_insurance",
              "space_rent")
TIER_LABEL = {"extremely_low": "Extremely low", "very_low": "Very low", "low": "Low", "moderate": "Moderate",
              "above_moderate": "Above moderate"}
MAP_LIMIT = 150
HAZ_COLOR = {True: "#1f6f4a", None: "#8a8f8c", False: "#c0392b"}


def data_stamp() -> tuple:
    """Modified times of every data file, so a new file from A or C shows on the next rerun (no restart)."""
    files = [contracts.DATA / "sources.json", *sorted(contracts.PROCESSED.glob("*.json*"))]
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


sites, tracts, EVALS, AREAS, limits, rates, programs, A, SRC = load(data_stamp())
rate_pt = contracts.latest_rate(rates)
fam = A["family"]
S = A["statutory_housing_cost"]
ss = st.session_state

# ---------------------------------------------------------------- header
st.title("🏗️ Builder mode")
st.markdown("**Which sites should a small housing nonprofit call first, why, and what's the gap per home?**")
ui.disclaimer()
ui.sample_banner()
if not contracts.using_sample_sites():
    he = SRC.get("scag_he_sites", {})
    status = he.get("status", "")
    missing_cities = status.split("NOT in layer:")[1].strip() if "NOT in layer:" in status else None
    n_cities = len({s.get("city") for s in sites if s.get("city")})
    n_he = sum(1 for s in sites if s.get("housing_element_site"))
    n_sla = sum(1 for s in sites if s.get("surplus_notice"))
    st.caption(f"**Real data:** {len(sites):,} Orange County sites in {n_cities} jurisdictions: {n_he:,} on city "
               f"housing-element inventories (SCAG, checked {he.get('checked', '?')}) and {n_sla:,} with a Surplus "
               f"Land Act notice (HCD)." + (f" Cities missing from the SCAG inventory layer: {missing_cities}."
                                            if missing_cities else ""))

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Find sites")
    cities = sorted({s["city"] for s in sites if s.get("city")})
    pick_cities = st.multiselect("City", cities, default=[], placeholder="All cities")
    sort_by = st.radio("Rank by", builder.SORTS,
                       help="Ready to call: hazards clear first, then most checks passed, then area benefit, "
                            "then lower-income homes. See 'How we rank'.")
    max_homes = st.number_input("Max homes per site · ASSUMPTION", 1, 200, A["site_rules"]["max_homes_default"]["value"],
                                help=A["site_rules"]["max_homes_default"]["basis"])
    hide_hazard = st.checkbox("Hide sites in a flood or fire zone", value=False)
    want = st.multiselect("Pathway not ruled out", [v[0] for v in pathways.PATHWAYS.values()], default=[])
    hide_no = st.checkbox("Hide sites where every pathway says No", value=True)

    st.header("Money")
    basis = st.radio("Family price that drives the gap", [STAT, BUDGET],
                     help="Statutory = the legal affordable housing cost cap, HSC 50052.5(b). "
                          "Budget = a share of this family's income (ASSUMPTION). Both use the same 25 CCR 6920 costs.")
    with st.expander("Family and loan (ASSUMPTION inputs)", expanded=False):
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
        rate = (st.number_input("Habitat rate (%) · ASSUMPTION", 0.0, 10.0, 3.0, 0.25) / 100) if use_habitat_rate \
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
price_note = (sp.get("reason") if sp["price"] is None else None) if statutory else None
if statutory:
    basis_label = (f"Statutory benchmark · {sp['citation']} (FindLaw copy, checked 2026-11-07) · HCD State Income Limits, "
                   f"memo {limits.get('memo_date')}") if sp.get("citation") else "Statutory benchmark · HSC 50052.5(b): not applicable"
    basis_sources = ["hsc_50052_5", "hcd_income_2026", "pmms"]
else:
    basis_label = f"Assumed household budget · {share:.0%} of {ui.money(income)}/yr (ASSUMPTION)"
    basis_sources = ["lane3_brief", "pmms"]
basis_short = "statutory price" if statutory else "household budget"
cost_defaults = {k: v["value"] for k, v in A["cost_per_home_defaults"].items() if isinstance(v, dict)}
other_defaults = {k: v["value"] for k, v in A["other_sources_per_home_defaults"].items()}
other_total = sum(v for v in other_defaults.values() if v is not None)


def site_costs(site: dict) -> dict:
    """Defaults = synthetic worked example. Only a SOURCED per-site land cost overrides the land line."""
    c = dict(cost_defaults)
    if site.get("land_cost_per_home") is not None:
        c["land_and_building_purchase"] = site["land_cost_per_home"]
    return c


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
    ready = builder.readiness(s, max_homes)
    if hide_hazard and ready["hazard_clear"] is False:
        continue
    g = finance.gap(site_costs(s), {"family_price": price, **other_defaults})
    rows.append({"id": s["id"], "site": s, "ev": ev, "best": best, "ready": ready, "gap": g,
                 "area_score": AREAS[s["id"]]["score"], "lower_income": builder.lower_income_homes(s),
                 "homes_per_1m": finance.families_per_million(g["gap"]) if g["complete"] else None})

ranked = builder.rank(rows, sort_by)
rows = ranked["rows"]
if not rows:
    st.info("No sites match these filters.")
    st.stop()
ids = [r["id"] for r in rows]
if ss.get("site_id") not in ids:
    ss["site_id"] = ids[0]


def _open(sid):
    ss["site_id"] = sid


# ---------------------------------------------------------------- call these 3 first
st.subheader("📞 Call these 3 first")
scope = ", ".join(pick_cities) if pick_cities else "all cities"
st.caption(f"Ranked by **{sort_by}** among {len(rows):,} sites ({scope}). Gap uses the **{basis_short}**.")
if ranked["note"]:
    st.info(ranked["note"])
for i, (col, r) in enumerate(zip(st.columns(3), rows[:3])):
    s = r["site"]
    with col.container(border=True):
        st.markdown(f"**{i + 1}. {s['name']}**")
        st.caption(f"Address {s.get('address') or 'unknown'} · "
                   f"{s.get('acres') if s.get('acres') is not None else 'unknown'} acres · "
                   f"zoning {s.get('zoning_local') or 'unknown'}")
        li = r["lower_income"]
        st.markdown(f"🏠 **{s.get('est_homes') if s.get('est_homes') is not None else 'unknown'}** homes "
                    f"({li if li is not None else 'unknown'} lower-income) · "
                    f"👥 area **{r['area_score'] if r['area_score'] is not None else 'unknown'}**/100 · "
                    f"✔️ **{r['ready']['passed']}/{builder.N_CHECKS}** checks")
        st.write(r["ready"]["why"])
        st.markdown(f"💵 Gap per home: **{gap_text(r['gap'])}** · :orange-background[ASSUMPTION costs]")
        st.button("Open site card", key=f"open-{r['id']}", on_click=_open, args=(r["id"],), width="stretch")

with st.expander("How we rank (and what we can't rank on yet)"):
    st.markdown(
        "**Ready to call** sorts sites clear of flood and fire maps first, then by how many of seven checks pass, "
        "then by Area Benefit Score, then by lower-income homes in the city's plan. **Unknown never counts as a pass.**\n\n"
        "1. Clear of FEMA flood zones · 2. Clear of very-high fire zones · 3. Near frequent transit · "
        "4. City planned lower-income homes here · 5. Fits your max homes (ASSUMPTION) · "
        "6. Land lead: place of worship mapped here (SB 4, never proof of ownership) or a Surplus Land Act notice · "
        "7. Vacant land or a parking lot today")
    ui.source_line(["oc_floodplains", *builder.FIRE_SOURCES, "caltrans_hqta", "scag_he_sites", "osm_worship",
                    "hcd_sla_notices", "scag_landuse"])
    st.caption("Homes per $1M of gap can't separate sites yet: no site has its own land cost, so all use the same "
               "SYNTHETIC cost lines. It will rank on its own once real per-site costs land.")

# ---------------------------------------------------------------- shortlist (left) + map (right)
left, right = st.columns([1.15, 1])
with left:
    st.subheader("Ranked shortlist")
    st.caption("Click a row to open its site card.")
    df = pd.DataFrame([{
        "#": n + 1, "Site": r["site"]["name"], "City": r["site"].get("city"), "Homes": r["site"].get("est_homes"),
        "Lower-inc.": r["lower_income"], "Checks": f"{r['ready']['passed']}/{builder.N_CHECKS}",
        "Area": r["area_score"], "Homes/$1M": r["homes_per_1m"], "Why": r["ready"]["why"],
    } for n, r in enumerate(rows)])
    event = st.dataframe(df, hide_index=True, width="stretch", height=460, on_select="rerun",
                         selection_mode="single-row", key="shortlist",
                         column_config={"Homes/$1M": st.column_config.NumberColumn(format="%.1f"),
                                        "Why": st.column_config.TextColumn(width="large")})
    sel = event.selection.rows if event else []
    sel_id = ids[sel[0]] if sel and sel[0] < len(ids) else None
    if sel_id and sel_id != ss.get("_last_row"):
        ss["_last_row"] = sel_id
        ss["site_id"] = sel_id

with right:
    st.subheader("Map")
    on_map = [(n, r) for n, r in enumerate(rows[:MAP_LIMIT]) if r["site"].get("lat") is not None
              and r["site"].get("lon") is not None]
    m = folium.Map(location=[33.70, -117.85], zoom_start=10, tiles="OpenStreetMap")
    for n, r in reversed(on_map):  # draw the top 3 last so they sit on top
        s = r["site"]
        tip = f"#{n + 1} {s['name']} · {r['ready']['passed']}/{builder.N_CHECKS} checks · area {r['area_score']}"
        color = HAZ_COLOR[r["ready"]["hazard_clear"]]
        if n < 3:
            folium.Marker([s["lat"], s["lon"]], tooltip=tip, popup=s["name"], icon=folium.DivIcon(
                icon_size=(28, 28), icon_anchor=(14, 14),
                html=f"<div style='background:{color};color:#fff;border:2px solid #fff;border-radius:50%;width:28px;"
                     f"height:28px;line-height:24px;text-align:center;font-weight:700;box-shadow:0 1px 4px #0006'>{n + 1}</div>",
            )).add_to(m)
        else:
            folium.CircleMarker([s["lat"], s["lon"]], radius=6, color=color, weight=1, fill=True, fill_opacity=0.75,
                                tooltip=tip, popup=s["name"]).add_to(m)
    if on_map:
        lats = [r["site"]["lat"] for _, r in on_map]
        lons = [r["site"]["lon"] for _, r in on_map]
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]], padding=(20, 20))
    clicked = st_folium(m, height=460, use_container_width=True, returned_objects=["last_object_clicked_popup"],
                        key="map")
    if not on_map:
        st.info("None of these sites has coordinates: use the shortlist.")
    st.caption(f"Top {min(len(rows), MAP_LIMIT)} of {len(rows):,} shown. 🟢 clear of flood and fire maps · "
               "🔴 in a flood or fire zone · ⚪ not checked. Numbers = call first.")
    name_to_id = {r["site"]["name"]: r["id"] for _, r in on_map}  # popups show the name (unique), not the raw id
    pid = name_to_id.get((clicked or {}).get("last_object_clicked_popup"))
    if pid and pid != ss.get("_last_map"):
        ss["_last_map"] = pid
        ss["site_id"] = pid

# ---------------------------------------------------------------- site card
r = next(x for x in rows if x["id"] == ss["site_id"])
s, ev, rd = r["site"], r["ev"], r["ready"]
sid = s["id"]
st.divider()
st.header(f"📋 {s['name']}")
st.caption(f"Ranked **#{ids.index(sid) + 1}** of {len(rows):,} by {sort_by} · {s.get('city') or 'unknown city'} · "
           f"APN {s.get('apn') or 'unknown'} · address {s.get('address') or 'unknown'} · "
           f"{s.get('acres') if s.get('acres') is not None else 'unknown'} acres · zoning "
           f"{s.get('zoning_local') or 'unknown'} / {s.get('zoning_scag') or 'unknown'}")
st.markdown(f"**Why call:** {rd['why']}")
if s.get("synthetic"):
    st.error("SYNTHETIC site for testing. Not a real parcel.")
if (s.get("est_homes") or 0) > max_homes:
    st.warning(f"{s.get('est_homes')} homes is above your max of {max_homes}. See the SB 4 notes under *Can we build?*")

# cost lines the user may edit below (read first so every number on the card agrees)
cost = {k: ss.get(f"{sid}-{k}", int(v or 0)) for k, v in site_costs(s).items()}
g = finance.gap(cost, {"family_price": price, **other_defaults})
fpm = finance.families_per_million(g["gap"]) if g["complete"] else None

q1, q2 = st.columns(2)
q3, q4 = st.columns(2)

with q1.container(border=True):
    st.markdown(f"### ⚖️ Can we build? {ui.verdict_badge(r['best'])}")
    for e in ev.values():
        n = {k: sum(t["result"] == k for t in e["tests"]) for k in ("pass", "fail", "unknown")}
        st.markdown(f"{ui.verdict_badge(e['verdict'])} **{e['label']}** · {n['pass']} pass · {n['fail']} fail · "
                    f"{n['unknown']} unknown")
    with st.expander("Show every law check, with the reason"):
        for e in ev.values():
            st.markdown(f"**{e['label']}** {ui.verdict_badge(e['verdict'])}")
            st.dataframe(pd.DataFrame([{"": ui.ICON[t["result"]], "test": t["test"], "why": t["why"]} for t in e["tests"]]),
                         hide_index=True, width="stretch")
            for note in e.get("notes") or []:
                st.caption(f"Note: {note if isinstance(note, str) else note.get('text', note)}")
            ui.source_line(sorted({t["source"] for t in e["tests"] if t.get("source")}))

with q2.container(border=True):
    hz = builder.hazards(s)
    worst = "fail" if any(t["result"] == "fail" for t in hz) else ("unknown" if any(t["result"] == "unknown" for t in hz) else "pass")
    head = {"fail": ui.chip("fail", "a hazard overlaps"), "unknown": ui.chip("unknown", "partly unchecked"),
            "pass": ui.chip("pass", "clear on every map we checked")}[worst]
    st.markdown(f"### 🛡️ Is it safe? {head}")
    for t in hz:
        st.markdown(f"{ui.chip(t['result'])} **{t['test']}**  \n<small>{t['why']}</small>", unsafe_allow_html=True)
    ui.source_line(["oc_floodplains", *builder.FIRE_SOURCES])

with q3.container(border=True):
    sc = AREAS[sid]
    tract = tracts.get(s.get("tract_id")) or {}
    st.markdown("### 👥 Who does it help?")
    a1, a2 = st.columns(2)
    a1.metric("Area Benefit Score", f"{sc['score']} / 100" if sc["score"] is not None else "unknown",
              help="Weights are the team's choice (ASSUMPTION); see core/area.py")
    cap = builder.he_capacity(s)
    a2.metric("Lower-income homes in the city's plan", r["lower_income"] if r["lower_income"] is not None else "unknown")
    if tract.get("synthetic"):
        st.caption("SYNTHETIC tract data")
    if sc["parts"]:
        st.dataframe(pd.DataFrame([{"value": p["value"], "weight": p["weight"], "metric": p["label"]} for p in sc["parts"]]),
                     hide_index=True, width="stretch",
                     column_config={"value": st.column_config.NumberColumn(format="%.1f", width="small"),
                                    "weight": st.column_config.NumberColumn(format="%.2f", width="small")})
    if sc["score"] is None:
        ui.unknown(f"No tract data for {s.get('tract_id') or 'this site'} yet.")
    elif sc["missing"]:
        ui.unknown("Not scored: " + ", ".join(sc["missing"]))
    st.caption(f"{tract.get('name') or s.get('tract_id') or 'Tract unknown'}")
    ui.source_line(["census_acs", "lodes"])
    if cap.get("Total") is not None:
        st.markdown(f"The city counted **{int(cap['Total'])} homes** here: {int(cap.get('Low_Income') or 0)} lower-income · "
                    f"{int(cap.get('Moderate_Income') or 0)} moderate · {int(cap.get('Above_Moderate_Income') or 0)} above-moderate")
    eu = builder.existing_use(s)
    sla = builder.surplus_notice(s)
    if s.get("surplus_notice"):
        st.markdown("Surplus Land Act notice: " + " · ".join(f"{k} **{sla[k]}**" for k in ("agency", "issued", "status")
                                                             if sla.get(k)))
    st.markdown(f"Near frequent transit: {ui.yes_no(s.get('in_hqta'))} · In use today: "
                + (f"**{eu['label']}**" if eu.get("label") else ui.yes_no(None)))
    ui.source_line(["scag_he_sites", "hcd_sla_notices", "caltrans_hqta", "scag_landuse"])

with q4.container(border=True):
    st.markdown(f"### 💵 Does it pencil? {ui.chip('unknown', 'incomplete') if not g['complete'] else ''}")
    p1, p2 = st.columns(2)
    p1.metric(f"{STAT}{' ◀ used' if statutory else ''}", ui.money(sp["price"]),
              help="Highest price whose 25 CCR 6920 housing cost fits the HSC 50052.5(b) cap")
    p2.metric(f"{BUDGET}{' ◀ used' if not statutory else ''}", ui.money(bp["price"]),
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
    g1.metric("Gap per home" if not g["complete"] or g["gap"] >= 0 else "Surplus per home", gap_text(g).replace(" surplus", ""))
    homes = s.get("est_homes")
    g2.metric(f"Gap, all {homes or '?'} homes", ui.money(g["gap"] * homes) if g["complete"] and homes else "unknown",
              help="Same gap for every home: ASSUMPTION")
    g3.metric("Homes per $1M of gap", f"{fpm:.1f}" if fpm else "n/a")
    if not g["complete"]:
        ui.unknown(f"Missing: {builder.missing_label(g)}. The gap can't be totalled.")
    st.markdown(f"Cost to create {ui.money(sum(v for v in cost.values() if v is not None))} − family "
                f"{ui.money(price)} − other sources {ui.money(other_total)}, per home")
    ui.assumption("Cost lines and other sources are copied from the event's SYNTHETIC worked example: the same for "
                  f"every site until a real per-site cost exists. Housing-cost items per 25 CCR 6920 (Cornell LII copy, "
                  f"read 2026-11-07): {ui.money(fixed)}/mo + {tax_rate:.1%}/yr property tax, all placeholders.")
    ui.source_line([*basis_sources, "synthetic_deal"])

    with st.expander("Edit the numbers · rate table · who could close the gap · a donor's gift"):
        st.markdown("**Cost to create, per home** (edit with a real deal)")
        cc = st.columns(2)
        for i, (k, v) in enumerate(site_costs(s).items()):
            cc[i % 2].number_input(k.replace("_", " "), 0, 2_000_000, int(v or 0), 5000, key=f"{sid}-{k}")
        st.markdown(f"**If the rate moves** (scenario M02, {basis_short})")
        rlist = [max(rate + d, 0.0) for d in (-0.01, -0.005, 0, 0.005, 0.01)]
        total_cost = sum(v for v in cost.values() if v is not None)
        sens = (finance.statutory_rate_sensitivity(income, hh, beds, limits, rlist, fixed, tax_rate, total_cost,
                                                   other_total, down, years) if statutory else
                builder.budget_rate_sensitivity(income, share, rlist, fixed, tax_rate, total_cost, other_total, down, years))
        st.dataframe(pd.DataFrame([{"rate": f"{x['rate']:.2%}", "family price": ui.money(x["family_price"]),
                                    "gap per home": ui.money(x["gap"])} for x in sens]), hide_index=True, width="stretch")
        st.markdown("**Who could close the gap** (funds unconfirmed)")
        st.dataframe(pd.DataFrame([{k: p[k] for k in ("name", "who_applies", "max", "status")} for p in programs]),
                     hide_index=True, width="stretch")
        gift = st.number_input("A donor gives… (scenario M03)", 0, 1_000_000, 25000, 5000)
        for line in finance.gift_coverage(gift, cost):
            st.write(f"• {ui.money(line['covered'])} covers {line['share_of_line']:.0%} of *{line['line'].replace('_', ' ')}*")

# ---------------------------------------------------------------- one-pager
st.subheader("📄 One-pager to send a congregation or a funder")
doc = builder.one_pager(s, ev, rd, AREAS[sid], tracts.get(s.get("tract_id")), {
    "basis_label": basis_label, "basis_sources": basis_sources, "price": price, "price_note": price_note,
    "other_sources": other_total, "cost_total": sum(v for v in cost.values() if v is not None), "gap": g,
    "homes_per_1m": fpm}, SRC, datetime.date.today().isoformat())
md = builder.one_pager_md(doc, SRC)
d1, d2, _ = st.columns([1, 1, 2])
d1.download_button("Download one-pager (.md)", md, file_name=f"{sid}.md", mime="text/markdown", width="stretch")
d2.download_button("Download print-ready page (.html)", builder.one_pager_html(doc, SRC), file_name=f"{sid}.html",
                   mime="text/html", width="stretch")
st.caption("Draft only: review it before you send it. Open the .html in a browser and print to PDF.")
with st.expander("Preview the one-pager"):
    st.markdown(md)
