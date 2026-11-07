# Builder C: Money, Homeowner mode, and Shipping

**Goal:** the gap number is defensible, Homeowner mode works on one screen, and we submit on time.

## Tasks (in order, with deadlines)
1. **By 11:45: verify the money inputs.**
   - Open the HCD 2026 income limits PDF (June 23 revision). Check every OC value in
     `data/processed/income_limits_2026.json` and fill the nulls. Note any difference in the `about` field.
   - `cd pipeline && python fetch_rates.py` → full PMMS series in `rates.json`.
   - Open CalHome, MyHome, Dream For All and the ADU grant pages. Update `programs.json` status lines with today's date.
2. **By 12:30: the affordable-price formula.** Open Health & Safety Code 50052.5 in a browser (bots get blocked).
   If you can code its ownership affordable-cost cap correctly, add it to `finance.py` as `statutory_price()` and
   show it beside the share-of-income version. If not, leave the ASSUMPTION label. **Never guess the statute.**
3. **By 1:15: Homeowner mode.** One screen: ADU size → cost → loan → rent → cash flow → payback → programs.
   Source the rent (HUD Fair Market Rent or Census median rent) or keep the ASSUMPTION tag.
4. **1:30: deploy.** share.streamlit.io → New app → our repo, branch `main`, file `app/Home.py`. Put the URL in the README.
   If deployment fails, the fallback is a live demo from a laptop. Say so in the README.
   **Kill switch:** Homeowner mode not working by 1:30 → replace its body with a "Coming next" panel.
5. **1:45–2:15: ship.** README (template sections), `.env.example`, "What is real and what is mocked" table,
   submission form draft (fields in `team/DEMO-SCRIPT.md`). **Submit by 2:15.** Open the repo in a private window first.

## Claude Code starter prompt
> Read CLAUDE.md, team/CLAUDE-TEAM.md, app/core/finance.py and data/processed/assumptions.json. I'm Builder C.
> Only edit finance.py, pages/2_Homeowner_Mode.py, Home.py, README.md and the money JSON files. Add a test in
> tests/test_finance.py for every function you change. Never invent a program term or statute; say unknown.

## Watch out
- Income limits differ by program (State vs State HOME vs HUD). Show which table and its date.
- Programs go stale. Every program row shows "funds unconfirmed" until checked today.
