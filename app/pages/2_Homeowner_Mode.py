"""Homeowner mode: can I add a backyard home (ADU), and does it pay back?

OWNER: Builder C. Keep it ONE screen. Kill switch: if it isn't working by 1:15 PM, replace the body
with a 'Coming next' panel and spend the time on Builder mode + the demo.
"""
import pandas as pd
import streamlit as st

from core import contracts, finance, ui

st.set_page_config(page_title="Homeowner mode · Open Ground", page_icon="🏠", layout="wide")
st.title("🏠 Homeowner mode")
st.write("For an OC homeowner with space in the backyard: what would a backyard home (ADU) cost, and does it pay back?")
ui.disclaimer()

A = contracts.load_assumptions()["homeowner_adu"]
rate_pt = contracts.latest_rate(contracts.load_rates())
programs = [p for p in contracts.load_programs() if "homeowner" in p["mode"]]

c1, c2 = st.columns([1, 2])
with c1:
    st.subheader("Your project")
    size = st.slider("ADU size (sq ft)", 300, 1200, 750, 50)
    if size <= 750:
        st.caption("Small ADUs may owe no impact fees (UNVERIFIED: confirm in the HCD ADU fact sheet).")
    build = st.number_input("Build cost · ASSUMPTION", 50000, 1000000, A["build_cost"]["value"], 10000,
                            help=A["build_cost"]["basis"])
    cash = st.number_input("Your cash in · ASSUMPTION", 0, 1000000, A["cash_in"]["value"], 5000)
    grants = st.number_input("Grants you expect (unconfirmed)", 0, 200000, 0, 5000)
    rent = st.number_input("Monthly rent · ASSUMPTION", 500, 8000, A["monthly_rent"]["value"], 50, help=A["monthly_rent"]["basis"])
    exp = st.slider("Vacancy + upkeep share · ASSUMPTION", 0.0, 0.5, A["vacancy_and_expense_share"]["value"], 0.05)
    rate = st.number_input(f"Loan rate (%) · PMMS {rate_pt['date']}", 0.0, 15.0, rate_pt["rate_30yr"] * 100, 0.05) / 100

with c2:
    res = finance.adu_cashflow(build, rent, rate, cash_in=cash, grants=grants, vacancy_and_expense_share=exp)
    m = st.columns(3)
    m[0].metric("Loan payment / mo", ui.money(res["monthly_loan_payment"]))
    m[1].metric("Net rent / mo", ui.money(res["net_rent"]))
    m[2].metric("Cash flow / mo", ui.money(res["net_monthly"]))
    if res["simple_payback_years"]:
        st.metric("Simple payback", f"{res['simple_payback_years']:.1f} years", help="(build cost − grants) ÷ yearly net rent")
    if res["net_monthly"] < 0:
        st.warning("At these numbers the rent does not cover the loan. Try more cash in, a grant, or a smaller unit.")
    for k in ("build_cost", "monthly_rent", "vacancy_and_expense_share", "cash_in"):
        ui.assumption(f"{k.replace('_', ' ')}: {A[k]['basis']}")
    ui.source_line(["pmms", "rentometer_oc"])

    st.subheader("Help that might apply (funds unconfirmed)")
    st.dataframe(pd.DataFrame([{k: p[k] for k in ("name", "who_applies", "max", "status")} for p in programs]),
                 hide_index=True, width="stretch")
    ui.source_line([p["source_id"] for p in programs])

    st.subheader("Rent it affordably?")
    st.write("Renting to a household under the income limit could make you eligible for local help and adds an "
             "affordable home. Rules vary by program and city: UNKNOWN until checked.")
