# Open Ground

> Open Ground shows a small housing nonprofit which Orange County sites it can legally build on, who they
> would help, and the funding gap per home, with every source on screen.

**Team:** Open Ground
**Members:** TODO: add names
**Lane:** 1 Find it (we also cover 3 Fund it)
**Built at:** Claude Impact Lab: UCI × SoCal Affordable Housing, November 7, 2026

**Live demo:** <https://open-ground-sqjmqchnp8w8kc5vegpm8k.streamlit.app/>
(If it is down, the fallback is a live demo from a laptop: see *Try it*.)
**Demo video:** TODO: uploaded on the hub

> **Prototype only.** Not legal, financial or lending advice. Numbers marked **ASSUMPTION** are placeholders;
> **UNKNOWN** means our data could not answer. Talk to a housing attorney, lender or the city before deciding anything.

## The real user

An acquisitions lead at a small housing nonprofit, with no GIS team (event scenario F02: "Give me ten sites I
should call this month, and why"). Today they find land by luck, word of mouth and spreadsheets, and they
can't tell quickly whether a site is legal, safe, or how big the funding gap will be.

**Before:** one site at a time, by hand, across a dozen county, state and federal websites.
**After:** a ranked shortlist of real housing-element sites, each with the law that opens it (yes / no / unknown
and why), hazards, who lives nearby, and the gap per home at today's mortgage rate, plus a one-pager to send.

## What we built

One Streamlit app, two modes, same data:

- **🏗️ Builder mode:** map and shortlist of Orange County's 2,126 housing-element sites (SCAG), checked
  against zoning, flood, fire, fault, historic-district and transit layers. Each site card shows the law checks,
  hazards and a **gap-per-home** calculator with rate sensitivity and "what a gift closes".
  *Status:* the live gap currently uses the **assumed household budget** (a share of the family's income, labelled
  ASSUMPTION). Switching it to the statutory benchmark below is in progress.
- **🏠 Homeowner mode:** can a backyard home (ADU) pay for itself? Size × cost per sq ft (or a real quote) →
  loan at this week's rate → rent → cash flow → two paybacks → the help that might apply, with each program's
  status checked today.

### The money engine (`app/core/finance.py`)

What a family can pay is set by law, not guessed. We coded **Health & Safety Code 50052.5(b)**: the most an
assisted owner-occupied home may cost each month is a share of the **area median income adjusted for the family
size appropriate for the unit** (studio = 1 person, 1BR = 2 ... 4BR = 5, per 50052.5(h)):

| Income tier | Monthly housing-cost cap | Section |
|---|---|---|
| Extremely low | 30% × 30% of size-adjusted median ÷ 12 | 50052.5(b)(1) |
| Very low | 30% × 50% | (b)(2) |
| Lower | 30% × 70% | (b)(3) |
| Moderate | 35% × 110% (and not less than 28% of the household's income) | (b)(4) |

"Housing cost" includes everything **25 CCR 6920** lists: principal and interest, property tax, insurance,
maintenance, a utilities allowance, HOA fees and space rent. The price is solved so all of it fits under the cap
(property tax depends on the price, so the two are solved together).

**Why it matters:** for the demo family ($90,000, 4 people, a 3-bedroom home, 7.18% rate) the statutory
benchmark price is **$153,751**. The common shortcut (30% of the family's own income, same costs) gives
**$221,037**. Using the shortcut understates the gap by about **$67,000 per home**.

*Status:* the statutory engine is built and tested (`finance.statutory_price`, `statutory_rate_sensitivity`,
32 tests passing), but the live Builder mode does not call it yet: it still shows the shortcut.

The tool also says when it can't answer: no price is shown when the income is above moderate, when the unit is
over 4 bedrooms, or when the moderate-income floor is above the cap (a funder policy choice). Where the statute
lets a funding agency choose an income-based limit instead, the tool says so and doesn't pick.

## How Claude is used

- **Built with Claude Code.** Three builders each ran Claude Code in their own files. Claude read the event rules
  (`CLAUDE.md`) and our team rules (`team/CLAUDE-TEAM.md`), pulled the public data, coded the statute from text
  a person confirmed in a browser, and wrote the tests.
- **Cross-checked by a second model.** Big decisions (the plan, the statute reading, which price drives the gap)
  were reviewed read-only by OpenAI's GPT-6.1-sol through Orca. It caught real bugs: a floor-over-cap case shown
  as feasible, unknown lines silently counted as $0, and an unfair before/after comparison.
- **At runtime the app calls no AI and needs no keys.** Every number comes from a committed data file with its
  source and date, so a person can check it.

## Try it

Needs Python 3.11 or newer.

```bash
git clone https://github.com/jaydentrannnn/open-ground
cd open-ground
pip install -r requirements.txt
pytest -q
streamlit run app/Home.py
```

No keys needed to run the app. `.env.example` lists optional keys for the data pipeline only
(`CENSUS_API_KEY`: the Census API now refuses requests without one).

Refresh the data (optional, low volume): `python pipeline/fetch_rates.py` (mortgage rates), and the other
scripts in `pipeline/`.

## Sources and assumptions

Every source the app shows is in [`data/sources.json`](data/sources.json) with its URL, date checked and status.
Every made-up number is in [`data/processed/assumptions.json`](data/processed/assumptions.json), labelled
ASSUMPTION with what it is based on, and tagged in the UI.

| Item | Source or assumption | Date checked |
|---|---|---|
| Affordable housing cost, ownership | [HSC 50052.5(b), (h)](https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=HSC&sectionNum=50052.5): checked word for word in a browser (leginfo blocks bots); [FindLaw copy](https://codes.findlaw.com/ca/health-and-safety-code/hsc-sect-50052-5/) | 2026-11-07 |
| What counts as housing cost | [25 CCR 6920](https://www.law.cornell.edu/regulations/california/25-CCR-6920) (Cornell LII copy) | 2026-11-07 |
| OC income limits by household size | [HCD 2026 State Income Limits](https://www.hcd.ca.gov/sites/default/files/docs/grants-and-funding/income-limits-2026.pdf), memo dated June 23, 2026 (replaced May 29), p.11. 4-person median $138,600 | 2026-11-07 |
| Mortgage rate | [Freddie Mac PMMS 30-yr](https://www.freddiemac.com/pmms/docs/PMMS_history.csv), 104 weekly points, latest 7.18% (week of 2026-11-05) | 2026-11-07 |
| Sites | [SCAG Housing Element Sites](https://maps.scag.ca.gov/scaggis/rest/services/LDX/HousingElementSite_poly_scag/MapServer): 2,126 OC sites, joined to SCAG zoning | 2026-11-07 |
| Hazards and transit | FEMA / OC floodplains, CAL FIRE fire hazard zones (LRA 2025 map; SRA layers flagged outdated or draft), Caltrans High-Quality Transit Areas: see `data/sources.json` for each layer's status | 2026-11-07 |
| Law checks | HCD Housing Law Fact Sheets (April 2026): SB 4, SB 9 and others | 2026-11-07 |
| Gap-closing programs | CalHome (closed), CalHFA MyHome, Dream For All (closed), CalHFA ADU Grant (fully allocated since Dec 28, 2023): each program's own page | 2026-11-07 |
| ADU cost per sq ft | ASSUMPTION $250/sq ft: [Terner Center statewide ADU owner survey](https://ternercenter.berkeley.edu/blog/cci-adu-survey) (Apr 2021). Statewide, historical, likely low for OC today | 2026-11-07 |
| ADU 1-bedroom rent | ASSUMPTION $2,598: [Rentometer OC average](https://www.rentometer.com/average-rent-in/county/orange-county-ca), third-party, data date not shown. Studio and 2BR: UNKNOWN (user enters) | 2026-11-07 |
| Demo family | ASSUMPTION: $90,000, 4 people (very low income in OC), 3-bedroom home | n/a |
| Insurance, upkeep, utilities, HOA, property tax rate | ASSUMPTION placeholders, one per 25 CCR 6920 item | n/a |
| Cost to create a home | ASSUMPTION: copied from the event's SYNTHETIC example deal. Not a benchmark | n/a |
| Public subsidy per home | ASSUMPTION: synthetic example | n/a |

**Sources that disagree:** a city-posted 2026 table showed the OC 4-person median as $136,600; the HCD June 23 PDF
says $138,600. We use HCD's.

## What is real and what is mocked

| Part | Status |
|---|---|
| 2,126 housing-element sites, zoning, hazards, transit | working, real public data |
| Law checks per site | working: yes / no / unknown with the reason and source |
| Statutory price (HSC 50052.5 + 25 CCR 6920) | partly working: engine built and tested against hand-computed values; not yet shown in Builder mode |
| Gap per home in Builder mode | working, but uses the assumed household budget (share of income, ASSUMPTION) |
| Builder mode base map | **broken on the live app**: CARTO tiles now need an API key; switching to keyless OpenStreetMap tiles |
| Income limits, mortgage rates | working, real (HCD, Freddie Mac) |
| Cost to build each home | **mocked**: synthetic example numbers, labelled ASSUMPTION |
| Housing-cost items (insurance, utilities, tax rate...) | **mocked**: placeholders, labelled ASSUMPTION |
| Homeowner mode ADU calculator | working; cost/sq ft and rent are ASSUMPTIONS |
| Program availability | real status as of today; funds never shown as confirmed |

## Where it gets things wrong

- **The cost side is not real.** Every per-home cost line comes from the event's synthetic deal. The gap is only as
  good as those numbers. A nonprofit should type in its own.
- **Which income table applies depends on the funder.** We use HCD State limits. HUD or State HOME limits can differ,
  and federal funds can override the unit-size rule in 50052.5(h).
- **One reading of the statute is ours.** 50052.5(b)(3) gives the 30% × 70% formula for lower-income households
  up to 70% of the median; for households above that it only gives an optional income-based limit. We still
  apply 30% × 70% and flag it as an interpretation in the tool.
- **The mortgage rate is a market average**, not a quote, and not what a nonprofit lender charges (UNKNOWN).
- **ADU numbers are rough.** City fees, hookups and site work are not included. Small-ADU impact-fee rules are UNKNOWN
  here: ask the city.
- Hazard layers have different vintages; some are flagged OUTDATED or draft in `data/sources.json`.

## Next steps

- One real deal from a local nonprofit, to replace the synthetic cost lines.
- HUD Fair Market Rents by bedroom for the Santa Ana-Anaheim-Irvine area (huduser.gov blocks automated downloads;
  enter them by hand).
- A choice of income table per program (State / HUD / State HOME), each with its own date.
- **Scale:** the engine is county-agnostic. Swap the income-limit row and the site layer to run the next 100 projects
  in any California county; the statute and the cost rules are statewide.

## Data and privacy

This project uses only public or provided data. It contains no personal information about real tenants, buyers or
residents. It does not file applications or contact any city or person.

## License

MIT, see [LICENSE](LICENSE). The event's brief, lane pages and docs in `docs/` and `lanes/` keep their own terms
(see the event's original README in git history).
