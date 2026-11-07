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


# ---- Builder B additions: show unknown as a styled answer, never hide it ----
RESULT_CHIP = {"pass": ":green-background[✅ yes]", "fail": ":red-background[❌ no]",
               "unknown": ":gray-background[❔ unknown]"}
VERDICT_BADGE = {"yes": ":green-background[✅ Yes]", "maybe": ":orange-background[❔ Maybe]",
                 "no": ":red-background[❌ No]"}


def chip(result: str, text: str | None = None) -> str:
    """Markdown chip for a pass / fail / unknown result. Optional text replaces the default word."""
    color = {"pass": "green", "fail": "red", "unknown": "gray"}.get(result, "gray")
    if text is None:
        return RESULT_CHIP.get(result, RESULT_CHIP["unknown"])
    return f":{color}-background[{ICON.get(result, '❔')} {text}]"


def verdict_badge(verdict: str) -> str:
    return VERDICT_BADGE.get(verdict, VERDICT_BADGE["maybe"])


def yes_no(v) -> str:
    """True / False / None as Yes / No / a grey 'unknown' chip."""
    return {True: "Yes", False: "No"}.get(v, ":gray-background[unknown]")


def unknown(text: str):
    st.markdown(f":gray-background[UNKNOWN] {text}")
