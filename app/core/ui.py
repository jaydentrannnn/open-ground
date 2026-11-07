"""Shared UI bits so every page shows sources and assumptions the same way.

OWNER: Builder B (restyled by C, 2026-11-07). Others: use these, don't fork them.
Design: github.com/jaydentrannnn/resumetailor docs/design.md with a lagoon-teal accent. No emoji: a status
is a word plus a mark shape (Material icon), never colour alone.
"""
from __future__ import annotations

import html

import streamlit as st

from core import contracts

ACCENT = "#1B6870"
# map rank ramp, best first: darker = ranked higher
RANK_RAMP = ("#0E4449", "#1B6870", "#4E9A9E", "#8FC3C3", "#CFE6E5")

# plain text marks for places that can't render icons (tables, downloads)
ICON = {"pass": "✓", "fail": "✕", "unknown": "?", "yes": "✓ Yes", "no": "✕ No", "maybe": "? Maybe"}
MARK = {"pass": ":material/check:", "fail": ":material/close:", "unknown": ":material/question_mark:"}

CSS = """
<style>
.og-eyebrow{font-family:"Geist Mono",ui-monospace,monospace;font-size:11px;letter-spacing:.08em;
  text-transform:uppercase;color:#6b6b68;margin:0 0 2px 0;line-height:1.4}
.og-title{font-family:"Fraunces",Georgia,serif;font-weight:380;font-size:clamp(1.9rem,2.6vw,2.6rem);
  letter-spacing:-.015em;line-height:1.1;margin:0 0 6px 0;color:#0b0b0b}
.og-stats{display:flex;gap:28px;flex-wrap:wrap;margin:6px 0 4px 0}
.og-stats .og-fig{font-family:"Fraunces",Georgia,serif;font-weight:400;font-size:26px;line-height:1.15;
  font-variant-numeric:tabular-nums;color:#0b0b0b}
.og-facts{display:flex;flex-wrap:wrap;gap:6px 32px;margin:4px 0 10px 0 !important;padding:0 !important}
.og-facts dd{margin:0;font-size:15px;font-weight:500;color:#0b0b0b}
.og-facts dt{margin:0}
[class*="st-key-tile"]{background:#f6f7f5}
[data-testid="stMetricValue"]{font-family:"Fraunces",Georgia,serif;font-weight:400;font-variant-numeric:tabular-nums}
[data-testid="stCaptionContainer"]{color:#6b6b68}
</style>
"""


def style():
    """Inject the few styles the theme config can't set (eyebrows, serif figures, grey tiles)."""
    st.html(CSS)


def eyebrow(text: str):
    st.html(f'<p class="og-eyebrow">{html.escape(text)}</p>')


def header(kicker: str, title: str):
    """Page top: mono eyebrow over a serif title. No intro paragraph under it."""
    st.html(f'<p class="og-eyebrow">{html.escape(kicker)}</p><h1 class="og-title">{html.escape(title)}</h1>')


def stats(items: list[tuple[str, str]]):
    """A row of serif figures, each under a mono label."""
    cells = "".join(f'<div><p class="og-eyebrow">{html.escape(k)}</p><div class="og-fig">{html.escape(str(v))}</div></div>'
                    for k, v in items)
    st.html(f'<div class="og-stats">{cells}</div>')


def facts(items: list[tuple[str, str]]):
    """Label / value pairs separated by space, not boxes."""
    cells = "".join(f'<div><dt class="og-eyebrow">{html.escape(k)}</dt><dd>{html.escape(str(v))}</dd></div>'
                    for k, v in items)
    st.html(f'<dl class="og-facts">{cells}</dl>')


def rank_color(n: int, total: int) -> str:
    """Map colour for the site ranked n (0 = best) of total: five teal steps, darkest = highest rank."""
    if total <= 0:
        return RANK_RAMP[-1]
    return RANK_RAMP[min(len(RANK_RAMP) - 1, n * len(RANK_RAMP) // total)]


def disclaimer():
    st.caption(
        "Prototype built at Claude Impact Lab (Nov 7, 2026). Not legal, financial or lending advice. "
        "Numbers marked **ASSUMPTION** are placeholders. **Unknown** means our data could not answer."
    )


def footer():
    """Bottom of every page: the equation, the latest rate and the disclaimer."""
    st.divider()
    st.caption("**The $0 equation:** what the family can pay + subsidies + fundraising − cost to create the home = $0")
    r = contracts.latest_rate(contracts.load_rates())
    st.caption(f"Latest 30-yr rate in our data: {r['rate_30yr']:.2%} (week of {r['date']})")
    source_line(["pmms", "synthetic_deal"])
    disclaimer()


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


# ---- show unknown as a styled answer, never hide it ----
RESULT_CHIP = {"pass": f":green-background[{MARK['pass']} yes]", "fail": f":red-background[{MARK['fail']} no]",
               "unknown": f":gray-background[{MARK['unknown']} unknown]"}
VERDICT_BADGE = {"yes": f":green-background[{MARK['pass']} Yes]", "maybe": ":orange-background[:material/help: Maybe]",
                 "no": f":red-background[{MARK['fail']} No]"}


def chip(result: str, text: str | None = None) -> str:
    """Markdown chip for a pass / fail / unknown result. Optional text replaces the default word."""
    color = {"pass": "green", "fail": "red", "unknown": "gray"}.get(result, "gray")
    if text is None:
        return RESULT_CHIP.get(result, RESULT_CHIP["unknown"])
    return f":{color}-background[{MARK.get(result, MARK['unknown'])} {text}]"


def verdict_badge(verdict: str) -> str:
    return VERDICT_BADGE.get(verdict, VERDICT_BADGE["maybe"])


def yes_no(v) -> str:
    """True / False / None as Yes / No / a grey 'unknown' chip."""
    return {True: "Yes", False: "No"}.get(v, ":gray-background[unknown]")


def unknown(text: str):
    st.markdown(f":gray-background[UNKNOWN] {text}")
