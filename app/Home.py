"""Open Ground: find land, see who it helps, and know if it pencils.

Run:  streamlit run app/Home.py
OWNER: Builder C (ship). Entry point only: two modes in a top bar, Builder opens first.
"""
from pathlib import Path

import streamlit as st

from core import ui

APP = Path(__file__).parent
st.set_page_config(page_title="Open Ground", page_icon=":material/roofing:", layout="wide")
st.logo(str(APP / "assets" / "logo.svg"), size="large")
ui.style()

page = st.navigation([
    st.Page(APP / "pages" / "1_Builder_Mode.py", title="Builder", url_path="Builder_Mode", default=True),
    st.Page(APP / "pages" / "2_Homeowner_Mode.py", title="Homeowner", url_path="Homeowner_Mode"),
], position="top")
page.run()
ui.footer()
