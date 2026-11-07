"""Open Ground: find land, see who it helps, and know if it pencils.

Run:  streamlit run app/Home.py
OWNER: Builder C (ship). Keep this page tiny.
"""
import streamlit as st

from core import contracts, ui

st.set_page_config(page_title="Open Ground", page_icon="🏡", layout="wide")

st.title("🏡 Open Ground")
st.subheader("Where can the next affordable home go, who does it help, and does it pencil?")
ui.disclaimer()
ui.sample_banner()

c1, c2 = st.columns(2)
with c1:
    st.markdown("### 🏗️ Builder mode")
    st.write("For a nonprofit acquisitions lead (e.g. Habitat OC). Ranked sites, the law that opens each one, "
             "hazards, who lives nearby, and the funding gap per home.")
    st.page_link("pages/1_Builder_Mode.py", label="Open Builder mode", icon="🏗️")
with c2:
    st.markdown("### 🏠 Homeowner mode")
    st.write("For an OC homeowner with a backyard. Can I add a home, what does it cost, and does it pay back?")
    st.page_link("pages/2_Homeowner_Mode.py", label="Open Homeowner mode", icon="🏠")

st.divider()
st.markdown("**The $0 equation:** what the family can pay + subsidies + fundraising − cost to create the home = $0")
r = contracts.latest_rate(contracts.load_rates())
st.caption(f"Latest 30-yr rate in our data: {r['rate_30yr']:.2%} ({r['date']})")
ui.source_line(["pmms", "synthetic_deal"])
