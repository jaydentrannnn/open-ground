"""Builder mode: rank sites for a nonprofit builder and show the gap per home.

OWNER: Builder B. Uses core/* (read-only for B except ui.py).
"""
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from core import area, contracts, finance, pathways, ui

st.set_page_config(page_title="Builder mode · Open Ground", page_icon="🏗️", layout="wide")
st.title("🏗️ Builder mode")
ui.disclaimer()
ui.sample_banner()

A = contracts.load_assumptions()
sites = contracts.load_sites()
tracts = contracts.load_tracts()
limits = contracts.load_income_limits()
rate_pt = contracts.latest_rate(contracts.load_rates())
programs = [p for p in contracts.load_programs() if "builder" in p["mode"]]
fam = A["family"]

# ---------------- Sidebar: the family + filters ----------------
with st.sidebar:
    st.header("Family (who it's for)")
    hh = st.selectbox("Household size", list(range(1, 9)), index=fam["household_size"]["value"] - 1)
    low = limits["by_household_size"][str(hh)]["low"]
    st.caption(f"OC 2026 low-income limit for {hh}: {ui.money(low)}")
    income = st.number_input("Family income ($/yr) · ASSUMPTION", 10000, 300000, fam["annual_income"]["value"], 1000)
    share = st.slider("Share of income for housing · ASSUMPTION", 0.25, 0.35, fam["housing_share"]["value"], 0.01)
    other = st.number_input("Tax + insurance + HOA ($/mo) · ASSUMPTION", 0, 2000, fam["monthly_tax_insurance_hoa"]["value"], 50)
    use_habitat_rate = st.toggle("Use a below-market Habitat rate", value=False,
                                 help="Habitat OC's real rate is UNKNOWN. Ask them.")
    rate = (st.number_input("Habitat rate (%) · ASSUMPTION", 0.0, 10.0, 3.0, 0.25) / 100) if use_habitat_rate \
        else st.number_input(f"Market rate (%) · PMMS {rate_pt['date']}", 0.0, 12.0, rate_pt["rate_30yr"] * 100, 0.05) / 100

    st.header("Filters")
    max_homes = st.number_input("Max homes per site", 1, 50, A["site_rules"]["max_homes_default"]["value"],
                                help=A["site_rules"]["max_homes_default"]["basis"])
    want = st.multiselect("Pathway", [v[0] for v in pathways.PATHWAYS.values()], default=[])
    hide_no = st.checkbox("Hide sites where every pathway says No", value=True)

# ---------------- Per-home economics (same for all sites until per-site costs exist) ----------------
cost_defaults = {k: v["value"] for k, v in A["cost_per_home_defaults"].items() if isinstance(v, dict)}
other_defaults = {k: v["value"] for k, v in A["other_sources_per_home_defaults"].items()}
fp = finance.family_price(income, rate, share, other, years=fam["term_years"]["value"])


def site_costs(site: dict) -> dict:
    """Defaults = synthetic worked example. Only a SOURCED per-site land cost overrides the land line."""
    c = dict(cost_defaults)
    if site.get("land_cost_per_home") is not None:
        c["land_and_building_purchase"] = site["land_cost_per_home"]
    return c


rows = []
for s in sites:
    ev = pathways.evaluate(s)
    best = pathways.best_verdict(ev)
    sc = area.score(tracts.get(s.get("tract_id")))
    g = finance.gap(site_costs(s), {"family_price": fp["price"], **other_defaults})
    if hide_no and best == "no":
        continue
    if want and not any(ev[pid]["label"] in want and ev[pid]["verdict"] != "no" for pid in ev):
        continue
    rows.append({
        "id": s["id"], "name": s["name"], "homes": s.get("est_homes"), "acres": s.get("acres"),
        "best_pathway": ui.ICON[best], "area_score": sc["score"], "gap_per_home": g["gap"],
        "homes_per_$1M": finance.families_per_million(g["gap"]),
        "too_big": (s.get("est_homes") or 0) > max_homes, "_site": s, "_ev": ev, "_area": sc, "_gap": g,
    })

rows.sort(key=lambda r: (-(r["area_score"] or 0), r["gap_per_home"]))

left, right = st.columns([3, 2])
with left:
    st.subheader("Map")
    m = folium.Map(location=[33.745, -117.868], zoom_start=13, tiles="OpenStreetMap")
    for r in rows:
        s = r["_site"]
        if s["lat"] is None:
            continue
        color = "green" if "Yes" in r["best_pathway"] else "orange"
        folium.CircleMarker([s["lat"], s["lon"]], radius=10, color=color, fill=True, fill_opacity=0.8,
                            tooltip=f"{r['name']} · score {r['area_score']} · gap {ui.money(r['gap_per_home'])}",
                            popup=r["id"]).add_to(m)
    clicked = st_folium(m, height=420, use_container_width=True, returned_objects=["last_object_clicked_popup"])

with right:
    st.subheader("Ranked shortlist")
    if not rows:
        st.info("No sites match these filters.")
        st.stop()
    df = pd.DataFrame([{k: v for k, v in r.items() if not k.startswith("_")} for r in rows])
    st.dataframe(df, hide_index=True, width="stretch",
                 column_config={"gap_per_home": st.column_config.NumberColumn(format="$%d"),
                                "homes_per_$1M": st.column_config.NumberColumn(format="%.1f")})

ids = [r["id"] for r in rows]
pick = (clicked or {}).get("last_object_clicked_popup")
chosen = st.selectbox("Site card for", ids, index=ids.index(pick) if pick in ids else 0,
                      format_func=lambda i: next(r["name"] for r in rows if r["id"] == i))
r = next(r for r in rows if r["id"] == chosen)
s = r["_site"]

st.divider()
st.header(f"📋 {s['name']}")
if s.get("synthetic"):
    st.error("SYNTHETIC site for testing. Not a real parcel.")
if r["too_big"]:
    st.warning(f"{s.get('est_homes')} homes is above your max of {max_homes}. See the labor-standards note under SB 4.")

t_land, t_who, t_money, t_export = st.tabs(["⚖️ Land & law", "👥 Who it helps", "💵 Does it pencil", "📄 One-pager"])

with t_land:
    c = st.columns(4)
    c[0].metric("Acres", s.get("acres") if s.get("acres") is not None else "unknown")
    c[1].metric("Est. homes", s.get("est_homes") if s.get("est_homes") is not None else "unknown")
    c[2].metric("Owner type", s.get("owner_type_proxy") or "unknown")
    c[3].metric("Transit area", {True: "Yes", False: "No", None: "unknown"}[s.get("in_hqta")])
    for pid, e in r["_ev"].items():
        with st.expander(f"{ui.ICON[e['verdict']]} · {e['label']}", expanded=e["verdict"] != "no"):
            st.dataframe(pd.DataFrame([{"": ui.ICON[t["result"]], "test": t["test"], "why": t["why"]} for t in e["tests"]]),
                         hide_index=True, width="stretch")
            ui.source_line(sorted({t["source"] for t in e["tests"]}))

with t_who:
    sc = r["_area"]
    tract = tracts.get(s.get("tract_id"), {})
    st.metric("Area Benefit Score", f"{sc['score']} / 100" if sc["score"] is not None else "unknown")
    if tract.get("synthetic"):
        st.caption("SYNTHETIC tract data")
    if sc["parts"]:
        st.dataframe(pd.DataFrame([{"metric": p["label"], "value": p["value"], "weight": p["weight"]} for p in sc["parts"]]),
                     hide_index=True, width="stretch")
    if sc["missing"]:
        st.caption("Unknown (not scored): " + ", ".join(sc["missing"]))
    ui.source_line(["census_acs", "lodes", "tcac_opp_2026"])

with t_money:
    cost = site_costs(s)
    st.markdown("**Cost to create, per home**")
    edited = {}
    cc = st.columns(len(cost))
    for i, (k, v) in enumerate(cost.items()):
        edited[k] = cc[i].number_input(k.replace("_", " "), 0, 2_000_000, int(v or 0), 5000, key=f"{s['id']}-{k}")
    ui.assumption("Defaults copied from the event's SYNTHETIC worked example. Replace with a real deal.")
    paid = {"family_price": fp["price"], **other_defaults}
    g = finance.gap(edited, paid)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Family can pay", ui.money(fp["price"]), help=f"{share:.0%} of {ui.money(income)}/yr, minus {ui.money(other)}/mo, at {rate:.2%}")
    m2.metric("Other sources", ui.money(sum(other_defaults.values())))
    m3.metric("Gap per home" if g["gap"] >= 0 else "Surplus per home", ui.money(abs(g["gap"])))
    if s.get("land_cost_mode") == "ground_lease":
        st.info("Ground lease: land may cost ~$0 upfront, but lease payments and a new-build construction cost "
                "are UNKNOWN here. Edit the lines above with real numbers before trusting the gap.")
    fpm = finance.families_per_million(g["gap"])
    m4.metric("Homes per $1M of gap", f"{fpm:.1f}" if fpm else "n/a")
    ui.source_line(["lane3_brief", "pmms", "hcd_income_2026", "synthetic_deal"])

    st.markdown("**If the rate moves** (scenario M02)")
    sens = finance.rate_sensitivity(income, [rate - 0.01, rate - 0.005, rate, rate + 0.005, rate + 0.01], share, other,
                                    g["total_cost"], sum(other_defaults.values()))
    st.dataframe(pd.DataFrame([{"rate": f"{x['rate']:.2%}", "family price": ui.money(x["family_price"]), "gap": ui.money(x["gap"])} for x in sens]),
                 hide_index=True, width="stretch")

    st.markdown("**Who could close the gap** (funds unconfirmed)")
    st.dataframe(pd.DataFrame([{k: p[k] for k in ("name", "who_applies", "max", "status")} for p in programs]),
                 hide_index=True, width="stretch")

    gift = st.number_input("A donor gives… (scenario M03)", 0, 1_000_000, 25000, 5000)
    for line in finance.gift_coverage(gift, edited):
        st.write(f"• {ui.money(line['covered'])} covers {line['share_of_line']:.0%} of *{line['line'].replace('_', ' ')}*")

with t_export:
    md = [f"# {s['name']}", "", "_Prototype. Not legal or financial advice. ASSUMPTION = placeholder._", "",
          f"- Homes: {s.get('est_homes')} · Acres: {s.get('acres')} · Owner type: {s.get('owner_type_proxy') or 'unknown'}",
          f"- Best pathway: {r['best_pathway']} · Area score: {r['area_score']}",
          f"- Family can pay: {ui.money(fp['price'])} (ASSUMPTION inputs) · Gap per home: {ui.money(r['gap_per_home'])}", "",
          "## Law checks"]
    for e in r["_ev"].values():
        md.append(f"### {e['label']}: {e['verdict']}")
        md += [f"- {t['result']}: {t['test']} ({t['why']}) [{t['source']}]" for t in e["tests"]]
    md.append("\n## Sources\n" + "\n".join(f"- {k}: {v['url']} (checked {v['checked']})" for k, v in contracts.load_sources().items()))
    text = "\n".join(md)
    st.download_button("Download one-pager (.md)", text, file_name=f"{s['id']}.md")
    st.code(text[:1500] + ("…" if len(text) > 1500 else ""), language="markdown")
