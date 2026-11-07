"""Shared UI bits so every page shows sources and assumptions the same way.

OWNER: Builder B. Others: use these, don't fork them.
"""
from __future__ import annotations

import streamlit as st

from core import contracts

ICON = {"pass": "✅", "fail": "❌", "unknown": "❔", "yes": "✅ Yes", "no": "❌ No", "maybe": "❔ Maybe"}


def disclaimer():
    st.caption(
        "Prototype built at Claude Impact Lab (Nov 7, 2026). Not legal, financial or lending advice. "
        "Numbers marked **ASSUMPTION** are placeholders. **Unknown** means our data could not answer."
    )


def sample_banner():
    if contracts.using_sample_sites():
        st.warning("Showing **SYNTHETIC** sample sites (not real parcels) until the real data file is built.")


def assumption(text: str):
    st.markdown(f":orange-background[ASSUMPTION] {text}")


def source_line(ids: list[str] | str):
    if isinstance(ids, str):
        ids = [ids]
    srcs = contracts.load_sources()
    bits = []
    for i in ids:
        s = srcs.get(i)
        if not s:
            bits.append(f"`{i}` (source missing!)")
            continue
        status = "" if s.get("status", "").startswith("VERIFIED") else f" · {s.get('status', 'UNVERIFIED')}"
        bits.append(f"[{s['title']}]({s['url']}) (checked {s.get('checked', '?')}{status})")
    st.caption("Source: " + " · ".join(bits))


def money(x) -> str:
    return "unknown" if x is None else f"${x:,.0f}"
