"""Homeowner mode: can I add a backyard home (ADU), and does it pay back?

OWNER: Builder C. Keep it ONE screen. Kill switch: if it isn't working by 1:30 PM, replace the body
with a 'Coming next' panel and spend the time on Builder mode + the demo.
"""
import pandas as pd
import streamlit as st

from core import contracts, finance, ui

st.set_page_config(page_title="Homeowner mode · Open Ground", page_icon="🏠", layout="wide")
st.title("🏠 Homeowner mode")
st.write("For an Orange County homeowner with space in the backyard: what would a backyard home (ADU) cost, "
         "and does the rent pay for it?")
ui.disclaimer()

A = contracts.load_assumptions()["homeowner_adu"]
RENTS = A["monthly_rent_by_bedrooms"]
rates = contracts.load_rates()
rate_pt = contracts.latest_rate(rates)
programs = [p for p in contracts.load_programs() if "homeowner" in p["mode"]]
UNIT_TYPES = {"Studio": 0, "1 bedroom": 1, "2 bedrooms": 2}

c1, c2 = st.columns([1, 2])
with c1:
    st.subheader("1 · Your ADU")
    unit = st.radio("Type", list(UNIT_TYPES), index=1, horizontal=True)
    bedrooms = UNIT_TYPES[unit]
    size = st.slider("Size (sq ft)", 300, 1200, 600 if bedrooms < 2 else 800, 50)
    cps = st.number_input("Cost per sq ft · ASSUMPTION", 100, 1500, A["cost_per_sqft"]["value"], 10,
                          help=A["cost_per_sqft"]["basis"])
    estimate = finance.adu_build_cost(size, cps)
    override = st.toggle("I have a real quote", value=False)
    build = st.number_input("Your quote ($)", 10_000, 2_000_000, min(max(int(estimate), 10_000), 2_000_000), 5_000) if override else estimate
    st.caption(f"Build cost used: **{ui.money(build)}** "
               f"({'your quote' if override else f'{size} sq ft × ${cps}/sq ft, ASSUMPTION'})")

    st.subheader("2 · Paying for it")
    cash = st.number_input("Your cash in · ASSUMPTION", 0, 1_500_000, A["cash_in"]["value"], 5_000)
    grants = st.number_input("Grants actually awarded to you", 0, 200_000, 0, 5_000,
                             help="Leave at $0 unless a program has said yes. See 'Help that might apply' below.")
    rate = st.number_input(f"Loan rate (%) · Freddie Mac PMMS 30-yr, week of {rate_pt['date']}", 0.0, 15.0,
                           round(rate_pt["rate_30yr"] * 100, 2), 0.05,
                           help="PMMS is a first-mortgage average, not a quote for an ADU, HELOC or "
                                "construction loan. Those are often priced differently: ASSUMPTION.") / 100

    st.subheader("3 · Rent")
    sourced = RENTS.get(str(bedrooms))
    if sourced is None:
        st.warning(f"No sourced market rent for a {unit.lower()} in our data: **UNKNOWN**. Enter your own.")
    rent = st.number_input("Monthly rent · ASSUMPTION" if sourced else "Monthly rent (your number)", 500, 10_000,
                           int(sourced) if sourced else None, 50, help=RENTS["basis"], key=f"rent_{bedrooms}",
                           placeholder="Enter a rent")
    exp = st.slider("Vacancy + upkeep share of rent · ASSUMPTION", 0.0, 0.5,
                    A["vacancy_and_expense_share"]["value"], 0.05, help=A["vacancy_and_expense_share"]["basis"])

def payback_panel():
    res = finance.adu_cashflow(build, rent, rate, cash_in=cash, grants=grants, vacancy_and_expense_share=exp)
    m = st.columns(3)
    m[0].metric("Loan payment / mo", ui.money(res["monthly_loan_payment"]), help=f"{ui.money(res['financed'])} over 30 years")
    m[1].metric("Net rent / mo", ui.money(res["net_rent"]), help=f"Rent minus {exp:.0%} for vacancy and upkeep")
    m[2].metric("Cash flow / mo", ui.money(res["net_monthly"]))
    p = st.columns(2)
    p[0].metric("Years to earn back your cash",
                f"{res['cash_payback_years']:.1f}" if res["cash_payback_years"] else "never at these numbers",
                help="Your cash in ÷ yearly cash flow after the loan payment")
    p[1].metric("Simple payback (ignores the loan)",
                f"{res['simple_payback_years']:.1f} years" if res["simple_payback_years"] else "n/a",
                help="(build cost − grants) ÷ yearly net rent")
    if res["assistance_exceeds_cost"]:
        st.warning("Your cash plus grants are more than the build cost. Check the inputs.")
    elif res["net_monthly"] < 0:
        st.warning("At these numbers the rent does not cover the loan. Try more cash in, a smaller unit, or a real quote.")

    st.markdown("**If the loan rate moves**")
    sens = finance.adu_rate_sensitivity(build, rent, [rate - 0.01, rate, rate + 0.01], cash_in=cash, grants=grants,
                                        vacancy_and_expense_share=exp)
    st.dataframe(pd.DataFrame([{"rate": f"{s['rate']:.2%}", "loan payment / mo": ui.money(s["monthly_loan_payment"]),
                                "cash flow / mo": ui.money(s["net_monthly"])} for s in sens]),
                 hide_index=True, width="stretch")


with c2:
    st.subheader("Does it pay back?")
    if rent is None:
        st.info(f"Enter a monthly rent for the {unit.lower()} to see the cash flow. We have no sourced market rent "
                "for this unit type, so we won't guess one.")
    else:
        payback_panel()

    with st.expander("What is assumed here", expanded=False):
        ui.assumption(f"Cost per sq ft: {A['cost_per_sqft']['basis']}")
        ui.assumption(f"Rent: {RENTS['basis']}")
        ui.assumption(f"Vacancy + upkeep: {A['vacancy_and_expense_share']['basis']}")
        ui.assumption(f"Cash in: {A['cash_in']['basis']}")
        st.caption("Not included: permits and city fees, utility hookups, design, site work, property-tax "
                   "change, insurance change, income tax. Impact fees for small ADUs: state law has rules on this "
                   "that we have NOT verified, so treat them as **UNKNOWN** and ask your city.")
    ui.source_line(["pmms", "rentometer_oc"])
    st.caption("Cost per sq ft: [Terner Center ADU owner survey, Apr 22 2021]"
               "(https://ternercenter.berkeley.edu/blog/cci-adu-survey) (checked 2026-11-07)")

    st.subheader("Help that might apply")
    st.caption("A program page saying 'up to $X' does not mean money is available. Status as checked on each "
               "program's own page.")
    st.dataframe(pd.DataFrame([{k: p[k] for k in ("name", "who_applies", "max", "status")} for p in programs]),
                 hide_index=True, width="stretch")
    known = contracts.load_sources()
    ids = [p["source_id"] for p in programs if p.get("source_id") in known]
    if ids:
        ui.source_line(ids)
    st.caption("CalHFA ADU Grant status: [calhfa.ca.gov/adu](https://www.calhfa.ca.gov/adu/) (checked 2026-11-07)")

    st.subheader("Rent it affordably?")
    st.write("Renting to a household under the income limit adds an affordable home and may open local help. "
             "What rent counts as affordable, and which programs pay for it, depends on the program and city: "
             "**UNKNOWN** until checked. Talk to your city housing office before you sign anything.")
