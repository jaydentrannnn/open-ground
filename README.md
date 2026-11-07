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
should call this month, and why"). Today they find land by luck, word of mouth and spreadsheets, and can't tell
quickly whether a site is legal, safe, or how big the funding gap will be.

**Before:** one site at a time, by hand, across a dozen county, state and federal websites.
**After:** a ranked shortlist of real sites with the three to call first, the law that opens each one (yes / no /
unknown and why), hazards, who lives nearby, and the gap per home at today's mortgage rate, plus a one-pager to send.

## What we built

One Streamlit app, two modes, same data:

- **🏗️ Builder mode:** **2,235 real Orange County sites**: 2,126 on city housing-element inventories (SCAG) and 109
  parcels with a Surplus Land Act notice (HCD). Each is checked against zoning, existing land use, flood, fire,
  earthquake-fault-zone and transit layers, and its census tract. You get:
  - **"Call these 3 first"**, then a ranked shortlist and a map (rank by readiness, area benefit, or homes per $1M of gap)
  - a **site card**: can we build (SB 4, SB 9, SB 684 / SB 1123 starter homes and surplus land, each test yes / no /
    unknown with the reason and the fact-sheet page cited),
    hazards, who it helps (tract data and an Area Benefit Score), and does it pencil
  - the **gap per home**, with a rate table and "what a gift closes"
  - a **one-pager** (Markdown or print-ready HTML) to send a congregation or a funder, with its sources
- **🏠 Homeowner mode:** can a backyard home (ADU) pay for itself? Size × cost per sq ft (or a real quote) → loan at
  this week's rate → rent → cash flow → two paybacks → the help that might apply, with each program's status
  checked today.

Historic districts are **not** checked: that test says "unknown" for every site (see *Known gaps*).

### The money engine (`app/core/finance.py`)

What a family can pay is set by law, not guessed. We coded **Health & Safety Code 50052.5(b)**: the most an
assisted owner-occupied home may cost each month is a share of the **area median income adjusted for the family
size appropriate for the unit** (studio = 1 person, 1BR = 2 ... 4BR = 5, per 50052.5(h)):

| Income tier | Monthly housing-cost cap | Section |
|---|---|---|
| Extremely low | 30% × 30% of size-adjusted median ÷ 12 | 50052.5(b)(1) |
| Very low | 30% × 50% | (b)(2) |
| Lower (income up to 70% of the median) | 30% × 70% | (b)(3) |
| Moderate | 35% × 110% (and not less than 28% of the household's income) | (b)(4) |

"Housing cost" includes everything **25 CCR 6920** lists: principal and interest, property tax, insurance,
maintenance, a utilities allowance, HOA fees and space rent. The price is solved so all of it fits under the cap
(property tax depends on the price, so the two are solved together).

**Why it matters:** for the demo family ($90,000, 4 people, a 3-bedroom home, 7.18% rate) the statutory
benchmark price is **$153,751**. The common shortcut (30% of the family's own income, same costs) gives
**$221,037**. The shortcut understates the gap by about **$67,000 per home**.

Builder mode uses the **statutory benchmark by default**. A switch shows the household-budget version, and both use
the same costs. The tool says when it can't answer: no price is shown when income is above moderate, the unit is over
4 bedrooms, a lower-income household earns more than 70% of the median (the statute leaves that to the funder), the
moderate-income floor is above the cap (a funder policy choice), or the non-loan costs alone reach the cap. Where the statute lets a funding
agency choose an income-based limit instead, the tool says so and doesn't pick.

## How Claude is used

- **Built with Claude Code.** Three builders each ran Claude Code in their own files. Claude read the event rules
  (`CLAUDE.md`) and our team rules (`team/CLAUDE-TEAM.md`), pulled the public data, coded the statute from text a
  person confirmed in a browser, and wrote the tests.
- **Cross-checked by a second model.** Big decisions (the plan, the statute reading, which price drives the gap) and
  the checkpoint diffs were reviewed read-only by OpenAI models (GPT-6.1-sol, GPT-6-astra) through Orca. They
  caught real bugs: a floor-over-cap case shown as feasible, unknown lines silently counted as $0, and an unfair
  before/after comparison.
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

The app runs on the committed files in `data/processed/` and needs no keys. See *How to rebuild the data* to refresh
them.

## Sources and assumptions

> Prototype only. Not legal, financial or lending advice. **Unknown** means our data could not answer.

**Status:** **VERIFIED** = we (or the event organizers) read the source and it says what we use it for.
**UNVERIFIED** = not confirmed yet, date of the data unknown, or third-party with no data date.
**OUTDATED** = a known old version; a newer one may differ. **ASSUMPTION** = a number we made up or copied from the
event's synthetic example. Every source is in [`data/sources.json`](data/sources.json); every made-up number is in
[`data/processed/assumptions.json`](data/processed/assumptions.json).

#### Sites and parcels

| What | Source | Date checked | Status | Where it's used |
|---|---|---|---|---|
| Housing-element sites: 2,126 in 28 OC jurisdictions. 7 cities are not in the layer (see Known gaps) | [SCAG Housing Element Sites](https://maps.scag.ca.gov/scaggis/rest/services/LDX/HousingElementSite_poly_scag/MapServer) | 2026-11-07 | VERIFIED | `pipeline/fetch_sites.py`. Builder mode map and shortlist; housing-element test; "Est. homes" |
| Zoning per parcel: SCAG regional code and city code. Layer metadata: updated as of October 2025 | [SCAG Zoning_poly_OR](https://maps.scag.ca.gov/scaggis/rest/services/LDX/Zoning_poly_OR/MapServer) | 2026-11-07 | VERIFIED | Pipeline: zoning, acres, slope and census tract per site; legend in `scag_zoning_codes.json`. SB 9 single-family zone test |
| Existing land use 2024 (vacant, parking, under construction, religious facilities). Layer metadata: updated as of July 2025 | [SCAG Existing Land Use](https://maps.scag.ca.gov/scaggis/rest/services/LDX/Existinglanduse_poly_OR/MapServer) | 2026-11-07 | VERIFIED | Land use for 2,215 of 2,235 sites. "Religious Facilities" is an SB 4 lead |
| Surplus public land: 113 OC notices on 109 parcels, all status "Archive". Staff contact column dropped | [HCD Surplus Land Act notices (data.ca.gov)](https://data.ca.gov/dataset/surplus-land-act-notices-of-availability-received) | 2026-11-07 | VERIFIED | `pipeline/fetch_surplus.py`: 109 parcels added as sites. Surplus public land test |
| SB 4 lead: places of worship mapped on OpenStreetMap (896 in OC). Proxy only, not ownership | [OpenStreetMap amenity=place_of_worship](https://wiki.openstreetmap.org/wiki/Tag:amenity%3Dplace_of_worship) | 2026-11-07 | VERIFIED | Owner type "faith_proxy" when one is inside the parcel (30 sites). SB 4 ownership test, shown as a LEAD |
| OC parcels (703k, no owner field) | [OC Public Works Parcels](https://www.ocgis.com/arcpub/rest/services/Map_Layers/Parcels/FeatureServer/0) | 2026-11-06 | VERIFIED | Not used yet |
| Santa Ana assessor parcels (land and improvement value) | [Santa Ana Assessor Parcels](https://gis.santa-ana.org/server/rest/services/Public/GIS_AssessorParcels/MapServer/0) | 2026-11-06 | VERIFIED | Not used yet |
| SB 4 parcel analysis code | [Terner Center SB4-Analysis](https://github.com/Terner-Center/SB4-Analysis) | 2026-11-07 | VERIFIED | Not used yet |

#### Hazards and transit

| What | Source | Date checked | Status | Where it's used |
|---|---|---|---|---|
| Flood: county copy of FEMA flood zones (special flood hazard area flag, floodways). Fields checked; date of the county copy unknown | [OC Floodplains](https://www.ocgis.com/arcpub/rest/services/Map_Layers/Floodplains/MapServer/0) | 2026-11-07 | UNVERIFIED | Flood check for every site (196 overlap a special flood hazard area, 17 a floodway). SB 4 flood tests |
| Flood: FEMA National Flood Hazard Layer, the authority | [FEMA NFHL](https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer) | 2026-11-06 | VERIFIED | Not used by the pipeline (slow service). Where to confirm a flood result |
| Fire, local areas: CAL FIRE map dated March 24, 2025 (Very High only) | [CAL FIRE FHSZ in LRA, 2025](https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/FHSALRA25_v1_All/FeatureServer/0) | 2026-11-07 | VERIFIED | Main fire check (51 sites overlap). SB 4 fire test |
| Fire, local areas: OC county copy, 21 polygons, all Very High. Date unknown; CAL FIRE has issued newer LRA maps | [OC Fire Hazard Severity Zones (LRA)](https://www.ocgis.com/arcpub/rest/services/Map_Layers/Fire_Hazard_Severity_Zones_LRA/MapServer/0) | 2026-11-07 | UNVERIFIED | Fire check; any overlap flags the site (45 sites). SB 4 fire test |
| Fire, state areas: 2007 map. Newer CAL FIRE maps exist; zones may differ | [CAL FIRE FHSZ, State Responsibility Areas (2007)](https://services.gis.ca.gov/arcgis/rest/services/Environment/Fire_Severity_Zones/MapServer/0) | 2026-11-07 | OUTDATED | Fire check (3 sites overlap). SB 4 fire test |
| Fire, state areas: CAL FIRE 2025 layer. Describes itself as submitted to OAL / under public comment | [CAL FIRE FHSZSRA25_3](https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/FHSZSRA25_3/FeatureServer/0) | 2026-11-07 | UNVERIFIED | Not used. Lead only |
| Earthquake fault zones: CGS Alquist-Priolo Earthquake Fault Zones (PRC 2621-2630), data last edited 2025-11-19. The SB 4 fact sheet does not define "earthquake fault zone"; we use these State zones | [CGS Alquist-Priolo Fault Zones](https://services2.arcgis.com/zr3KAIbsRSUyARHG/arcgis/rest/services/CGS_Alquist_Priolo_Fault_Zones/FeatureServer/0) | 2026-11-07 | VERIFIED | Fault check for every site (0 overlap; nearest site about 590 m away). SB 4 fault test |
| Liquefaction zones (CONTEXT, not a legal test): OC copy of CGS zones, maps released 1998-2005 | [OC Liquefaction](https://www.ocgis.com/arcpub/rest/services/Map_Layers/Liquefaction/MapServer/0) | 2026-11-07 | VERIFIED | Context per site (1,732 sites overlap: most of OC's flat coastal plain) |
| Landslide zones (CONTEXT, not a legal test): CGS, released 1998-2002 | [CGS Landslide Zones](https://services2.arcgis.com/zr3KAIbsRSUyARHG/arcgis/rest/services/CGS_Landslide_Zones/FeatureServer/0) | 2026-11-07 | VERIFIED | Context per site (79 sites overlap) |
| Pollution burden (CONTEXT, not scored): CalEnviroScreen 5.0 percentiles by tract (OEHHA) | [CalEnviroScreen 5.0 (OEHHA)](https://services1.arcgis.com/PCHfdHz4GlDNAhBb/arcgis/rest/services/calenviroscreen50results_F_070126_gdb/FeatureServer/2) | 2026-11-07 | VERIFIED | Context for 2,215 sites. Not part of the Area Benefit Score |
| Transit: Caltrans High-Quality Transit Areas (867 polygons around OC) | [Caltrans HQTA](https://caltrans-gis.dot.ca.gov/arcgis/rest/services/CHrailroad/CA_HQ_Transit_Areas/FeatureServer/0) | 2026-11-07 | VERIFIED | Transit check for every site (831 overlap). "Transit area" |

#### Law

| What | Source | Date checked | Status | Where it's used |
|---|---|---|---|---|
| SB 4 (Gov Code 65913.16), faith and college land: HCD fact sheet, April 2026, read in full | [HCD SB 4 fact sheet](https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/aff-hsg-faith-higher-ed-sb-4.pdf) | 2026-11-07 | VERIFIED | Builder mode site card: every SB 4 test and note, with the page |
| SB 9 (Gov Code 65852.21, 66411.7), duplexes and lot splits: HCD fact sheet, April 2026, read in full | [HCD SB 9 fact sheet](https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/lot-splits-and-duplexes-sb-9.pdf) | 2026-11-07 | VERIFIED | Builder mode site card: every SB 9 test and note, with the page |
| SB 684 / SB 1123, Starter Home Revitalization Act (Gov Code 65852.28, 65913.4.5, 66499.41): HCD combined fact sheets, April 2026, PDF pp.67-68. Up to 10 units | [HCD Housing Law Fact Sheets](https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/housing-law-fact-sheets.pdf) | 2026-11-07 | VERIFIED | Builder mode site card: SB 684/1123 tests (lot under 5 acres, multifamily zone, incorporated city, fire, displacement) |
| Affordable housing cost, ownership: HSC 50052.5(b) and (h), official text. (b)(1)-(4) and (h) checked word for word by Builder C in a browser (leginfo blocks automated fetch) | [leginfo HSC 50052.5](https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=HSC&sectionNum=50052.5) | 2026-11-07 | VERIFIED | `finance.statutory_price`: Builder mode's default family price |
| HSC 50052.5, FindLaw copy ("current as of Jan 1, 2026"). Matches the official text per the browser check | [FindLaw HSC 50052.5](https://codes.findlaw.com/ca/health-and-safety-code/hsc-sect-50052-5/) | 2026-11-07 | VERIFIED | The text `finance.py` was coded from |
| What counts as an owner's housing cost: 25 CCR 6920 (a)-(g) | [25 CCR 6920 (Cornell LII)](https://www.law.cornell.edu/regulations/california/25-CCR-6920) | 2026-11-07 | VERIFIED | Both family prices; the cost items in `assumptions.json` |

#### Who it helps

| What | Source | Date checked | Status | Where it's used |
|---|---|---|---|---|
| OC income limits by household size: HCD State limits, memo dated June 23, 2026 (replaced May 29), p.11. 4-person median $138,600 | [HCD 2026 State Income Limits](https://www.hcd.ca.gov/sites/default/files/docs/grants-and-funding/income-limits-2026.pdf) | 2026-11-07 | VERIFIED | `income_limits_2026.json`. Income tier; statutory price |
| City of Irvine 2026 OC income limits page. Not checked against the June 23 revision | [City of Irvine income limits](https://cityofirvine.gov/node/56276) | 2026-11-07 | UNVERIFIED | Not used. **Sources disagree:** earlier city-posted tables (Irvine, Newport Beach) showed a 4-person median of $136,600; HCD's June 23 PDF says $138,600. We use HCD |
| Tract data: ACS 2024 5-year, the latest on the API (household income, rent burden, crowding, income bins). Every table id checked against its API variable label | [Census ACS 5-year 2024 API](https://api.census.gov/data/2024/acs/acs5) | 2026-11-07 | VERIFIED | `pipeline/fetch_area.py` builds `tracts.json` (614 OC tracts). Area Benefit Score |
| Low-wage jobs by workplace: LODES 8 CE01 + CE02 (jobs paying $3,333/month or less), CA 2024 file, the latest year in the directory | [Census LEHD LODES 8 (CA workplace files)](https://lehd.ces.census.gov/data/lodes/LODES8/ca/wac/) | 2026-11-07 | VERIFIED | `tracts.json` low-wage jobs. Area Benefit Score |
| TCAC/HCD 2026 Opportunity Map (adopted Dec 2025), 2020 tracts (methodology p.14). Low 0 / Moderate 1 / High 2 / Highest 3; High-Poverty & Segregated kept as an overlay flag (FAQ p.9). A draft 2027 map is posted and not used | [2026 Statewide Summary Table (TCAC)](https://www.treasurer.ca.gov/sites/default/files/2025-11/summary_file.zip) | 2026-11-07 | VERIFIED | `pipeline/fetch_opportunity.py`: 610 of 614 OC tracts scored (4 null, reason recorded). Area Benefit Score |

#### Money

| What | Source | Date checked | Status | Where it's used |
|---|---|---|---|---|
| 30-year mortgage rate: 104 weekly points, latest 7.18% (week of 2026-11-05). A market average, not a quote | [Freddie Mac PMMS history](https://www.freddiemac.com/pmms/docs/PMMS_history.csv) | 2026-11-07 | VERIFIED | `pipeline/fetch_rates.py` builds `rates.json`. Home page; Builder mode rate and rate table; Homeowner mode loan rate |
| Housing costs about 30-35% of income | [Lane 3 brief](lanes/3-fund-it/README.md) | 2026-11-07 | VERIFIED | Basis for the 30% household-budget ASSUMPTION |
| The event's one-home bill. SYNTHETIC: every number is made up | [synthetic-example-deal.json](lanes/3-fund-it/data/synthetic-example-deal.json) | 2026-11-07 | ASSUMPTION | Default cost lines, subsidy and rent-while-waiting in Builder mode; Home page |
| CalHome (HCD): CLOSED, next round unknown. Lends to agencies and nonprofits, not individuals | [HCD CalHome](https://www.hcd.ca.gov/grants-and-funding/programs-active/calhome) | 2026-11-07 | VERIFIED | "Who could close the gap" (Builder) and "Help that might apply" (Homeowner), from `programs.json` |
| CalHFA MyHome Assistance: funds availability not stated | [CalHFA homebuyer programs](https://www.calhfa.ca.gov/homebuyer/programs/) | 2026-11-07 | VERIFIED | Builder mode, "Who could close the gap" |
| CalHFA Dream For All: CLOSED (portal closed after Mar 16, 2026). Next round unknown | [CalHFA Dream For All](https://calhfa.ca.gov/dream/) | 2026-11-07 | VERIFIED | Builder mode, "Who could close the gap" |
| CalHFA ADU Grant: latest round fully allocated (Dec 28, 2023) | [CalHFA ADU Grant](https://www.calhfa.ca.gov/adu/) | 2026-11-07 | VERIFIED | Homeowner mode, "Help that might apply" |
| HCD ADU funding page (lists the CalHFA ADU Grant). Grant availability not confirmed | [HCD ADU funding](https://hcd.ca.gov/building-standards/adu/funding) | 2026-11-07 | UNVERIFIED | Not used by id. The CalHFA and HCD pages agree on the grant's maximum |
| OC average rents. Third-party; date of the data not shown | [Rentometer: Orange County](https://www.rentometer.com/average-rent-in/county/orange-county-ca) | 2026-11-07 | UNVERIFIED | Homeowner mode: 1-bedroom rent default (ASSUMPTION below) |
| ADU build cost per sq ft: statewide owner survey, Apr 22, 2021. Statewide and from 2021, likely low for OC today | [Terner Center ADU owner survey](https://ternercenter.berkeley.edu/blog/cci-adu-survey) | 2026-11-07 | OUTDATED | Homeowner mode: cost per sq ft default (ASSUMPTION below) |

#### Assumptions

Every row below is a placeholder. Replace it with a real number and its source. "No source" means there is none.

| What | Source | Date checked | Status | Where it's used |
|---|---|---|---|---|
| Household size: 4. Typical family size for the demo | [assumptions.json](data/processed/assumptions.json): no source | 2026-11-07 | ASSUMPTION | Builder mode default; README example |
| Family income: $90,000/yr. For 4 people that is very low income in OC (limit $93,050, HCD p.11) | [HCD 2026 State Income Limits](https://www.hcd.ca.gov/sites/default/files/docs/grants-and-funding/income-limits-2026.pdf) | 2026-11-07 | ASSUMPTION | Builder mode default; README example |
| Home size: 3 bedrooms. HSC 50052.5(h) sizes the cap by bedrooms (3BR = household of 4) | [assumptions.json](data/processed/assumptions.json) | 2026-11-07 | ASSUMPTION | Builder mode default; statutory price |
| Share of income for housing: 30%. A household budget, not the legal cap | [Lane 3 brief](lanes/3-fund-it/README.md) | 2026-11-07 | ASSUMPTION | Builder mode: the household-budget price (when switched on) |
| Below-market rate toggle: starts at 3.0%. Habitat OC's real rate is UNKNOWN | [assumptions.json](data/processed/assumptions.json): no source | 2026-11-07 | ASSUMPTION | Builder mode sidebar (off by default) |
| Loan term: 30-year fixed | [assumptions.json](data/processed/assumptions.json): standard term | 2026-11-07 | ASSUMPTION | Both family prices |
| Property tax: 1.1% of price, 6920(b). 1% general levy plus local add-ons, which vary by area (not checked) | [25 CCR 6920](https://www.law.cornell.edu/regulations/california/25-CCR-6920) | 2026-11-07 | ASSUMPTION | Both family prices |
| Fire and casualty insurance $150/month (6920(c)), maintenance and repairs $150/month (6920(d)) | [assumptions.json](data/processed/assumptions.json): no source | 2026-11-07 | ASSUMPTION | Both family prices |
| Utilities allowance: $250/month, 6920(e). The real figure is the local housing authority's utility allowance schedule (not checked) | [assumptions.json](data/processed/assumptions.json) | 2026-11-07 | ASSUMPTION | Both family prices |
| HOA $0 (detached home), loan insurance $0 (e.g. a nonprofit first loan; unknown per lender), space rent $0 (not on rented land; a land trust ground lease would add this), down payment $0 | [assumptions.json](data/processed/assumptions.json) | 2026-11-07 | ASSUMPTION | Both family prices |
| Cost to create a home: land and building $360,000, time while waiting $85,000, construction $40,000, fees, design, legal and sales $50,000 | [synthetic-example-deal.json](lanes/3-fund-it/data/synthetic-example-deal.json) | 2026-11-07 | ASSUMPTION | Builder mode, "Does it pencil": default cost lines (editable), the same for every site |
| Public subsidies $100,000 and rent earned while waiting $55,000 per home | [synthetic-example-deal.json](lanes/3-fund-it/data/synthetic-example-deal.json) | 2026-11-07 | ASSUMPTION | Builder mode: "Other sources" in the gap |
| Max homes per site: 9. The team's demo default, under the 10-unit ceiling of the SB 684 / SB 1123 starter-home pathway (fact sheets pp.67-68). **Not a limit for SB 4**: prevailing wage applies at any size (SB 4 fact sheet p.3) | [assumptions.json](data/processed/assumptions.json) | 2026-11-07 | ASSUMPTION | Builder mode filter default and "too big" warning |
| Area Benefit Score weights (rent burden 0.3, crowding 0.2, eligible households 0.2, low-wage jobs 0.2, opportunity 0.1) and the 0-1 scaling ranges. Our choice | [assumptions.json](data/processed/assumptions.json), [`app/core/area.py`](app/core/area.py): no source | 2026-11-07 | ASSUMPTION | Who it helps; shortlist order |
| "Eligible households" = households earning under $150k: the nearest ACS income bin to the OC 4-person low-income limit ($148,850). Mixes household sizes | [Census ACS 5-year API](https://api.census.gov/data.html) | 2026-11-07 | ASSUMPTION | Area Benefit Score |
| ADU cost per sq ft: $250 (survey median; statewide, 2021, not OC; leaves out site-specific and some soft costs) | [Terner Center ADU owner survey](https://ternercenter.berkeley.edu/blog/cci-adu-survey) | 2026-11-07 | ASSUMPTION | Homeowner mode |
| ADU rent by unit type: 1BR $2,598 (Rentometer). Studio and 2BR: UNKNOWN, the owner enters them. HUD FY2026 Fair Market Rents are a better source but huduser.gov blocks automated downloads; they are gross rent | [Rentometer: Orange County](https://www.rentometer.com/average-rent-in/county/orange-county-ca) | 2026-11-07 | ASSUMPTION | Homeowner mode |
| Vacancy and upkeep 25% of rent; owner cash in $50,000 | [assumptions.json](data/processed/assumptions.json): no source | 2026-11-07 | ASSUMPTION | Homeowner mode |
| The PMMS first-mortgage average used as an ADU loan rate. ADU, HELOC and construction loans are often priced differently | [Freddie Mac PMMS history](https://www.freddiemac.com/pmms/docs/PMMS_history.csv) | 2026-11-07 | ASSUMPTION | Homeowner mode: loan rate default (labelled in the app) |

## What is real and what is mocked

**Real** (public data, built 2026-11-07)

- **2,235 sites:** 2,126 SCAG housing-element sites in 28 OC jurisdictions (including unincorporated County of
  Orange), plus 109 parcels from 113 HCD Surplus Land Act notices.
- **SCAG zoning** on 2,213 sites and **SCAG 2024 existing land use** on 2,215 (155 vacant, 17 parking, 50 religious
  facilities).
- **Flood, fire, fault-zone and transit checks** on each parcel outline: 196 sites overlap a FEMA special flood
  hazard area, 17 a floodway, 52 a Very High fire zone on at least one map, 0 an Alquist-Priolo fault zone, 831 a
  High-Quality Transit Area. The share of the parcel that overlaps is recorded, so a sliver shows as a sliver.
  Liquefaction, landslide and CalEnviroScreen 5.0 are shown as context, not legal tests.
- **Tract data:** ACS 2024 5-year and LODES 2024 for 614 OC tracts, plus the TCAC/HCD 2026 opportunity category for
  610; 2,215 sites are linked to a tract.
- **Income limits** (HCD 2026, June 23 revision, checked against the PDF) and the **mortgage rate** (Freddie Mac PMMS).
- **Statutory price:** the HSC 50052.5(b) formula, checked against the official text and tested against
  hand-computed values. Builder mode's default.
- **Law tests and program statuses:** HCD fact sheets (April 2026) and each program's own page, checked 2026-11-07.

**Partly real**

- **Law verdicts:** real rules, but most SB 4 tests and several SB 9 tests say "unknown" because our data can't check
  them (see Known gaps).
- **SB 4 owner type:** a proxy. 57 sites are flagged: 30 have an OpenStreetMap place of worship inside the parcel, 27
  only have SCAG "Religious Facilities" land use. Leads to check, not ownership.
- **Area Benefit Score:** real tract numbers; the weights, scaling ranges and the under-$150k proxy are ours.
- **Est. homes:** the city's housing-element capacity for the parcel, not a design. Unknown for the 109 surplus parcels.
- **Gap per home:** real rate, income limits and statutory formula; every cost line and the housing-cost items are
  placeholders.
- **Homeowner mode:** real rate and program statuses; cost per sq ft, rent and cash in are ASSUMPTIONS.

**Mocked**

- **Cost to create each home**, **public subsidy** and **rent while waiting**: the event's SYNTHETIC example. No site
  has a sourced land cost, so the land line is the same placeholder everywhere.
- **Demo family:** $90,000, 4 people, 3 bedrooms.
- **Housing-cost items:** insurance, upkeep, utilities, HOA, loan insurance, space rent, 1.1% tax rate.
- **ADU:** cost per sq ft, vacancy share, cash in. Studio and 2-bedroom rents are unknown.
- **Max 9 homes per site** filter default.

## Where it gets things wrong (known gaps)

- **Fault zones are the State's Alquist-Priolo zones.** The SB 4 fact sheet says "earthquake fault zone" without
  defining it. No site overlaps one (nearest about 590 m). Liquefaction and landslide zones are context only.
- **Surplus notices and SCAG sometimes disagree** on parcel size or existing use (shown side by side, not settled).
  Notices that list several APNs are joined on the first APN only.
- **SB 684 / SB 1123:** the fact sheet says "fire hazard zones" with no severity, and we only map Very High, so the
  fire test is never a pass. SB 1123's conditions for single-family lots are not in the fact sheet: read Gov Code
  66499.41.
- **Historic districts are not checked.** The SB 9 historic test says "unknown" for every site.
- **The cost side is not real.** Every per-home cost line comes from the event's synthetic deal. The gap is only as
  good as those numbers. A nonprofit should type in its own.
- **Which income table applies depends on the funder.** We use HCD State limits. HUD or State HOME limits can differ,
  and federal funds can override the unit-size rule in 50052.5(h).
- **Lower-income households above 70% of the median get no statutory price.** 50052.5(b)(3) gives the 30% × 70%
  formula only up to 70% of the median; above that it gives an optional income-based limit a funder may choose. The
  tool shows "unknown" with that reason rather than picking (State Controller guidance treats the range separately).
- **The mortgage rate is a market average**, not a quote, and not what a nonprofit lender charges (UNKNOWN).
- **Fire maps differ in date.** Local areas use CAL FIRE's map dated 2025-03-24; the OC county copy has no date. State
  areas use CAL FIRE's 2007 map (OUTDATED); CAL FIRE's 2025 state-area layer calls itself a draft, so we don't use it.
  Confirm any result on CAL FIRE's current map.
- **Flood uses the county's copy** of FEMA zones, date unknown. FEMA's National Flood Hazard Layer is the authority:
  check the FIRM before deciding.
- **SB 4 ownership is a proxy only.** Confirm on title or the Assessor roll.
- **SB 4 tests our data can't check:** ownership as of Jan 1, 2024; farmland, wetlands, hazardous waste, conservation
  land, protected habitat and easements; industrial uses nearby; 75% of the perimeter next to urban uses.
- **SB 9 tests our data can't check:** historic district or landmark; the other lands listed in Gov Code
  65913.4(a)(6)(B)-(K); whether rent-restricted or recently tenant-occupied housing would be demolished. The zone test
  uses SCAG's regional code, so confirm the city's zone.
- **Seven cities are not in the SCAG housing-element layer:** Santa Ana, Costa Mesa, Huntington Beach, Orange, Tustin,
  Rancho Santa Margarita and Laguna Woods. Surplus notices partly cover three of them (Santa Ana 29 parcels, Tustin
  27, Orange 6). Costa Mesa, Huntington Beach, Rancho Santa Margarita and Laguna Woods have no sites in our data.
- **20 surplus parcels have only the notice's point:** no parcel outline, so no zoning, land use or census tract.
- **Every OC surplus notice is "Archive":** sent to HCD more than 60 days ago (HCD data dictionary). Whether the land is
  still available is unknown until someone calls the agency.
- **Housing-element lists go stale.** A listed site may already be sold or built.
- **No street address for most sites** (APN only). Surplus notices that describe an occupied home have the address
  withheld.
- **"Transit area" approximates SB 4's parking rule.** The rule is about 0.5-mile walking distance to a high-quality
  transit corridor or major transit stop; we test overlap with Caltrans HQTA polygons, not walking distance.
- **ADU numbers are rough.** City fees, hookups and site work are not included. Small-ADU impact-fee rules are UNKNOWN
  here: ask the city.
- **City housing funds:** no source; amount and availability unknown. Ask the city housing division.

## How to rebuild the data

From the repo root (Python 3.11+):

```bash
pip install -r requirements.txt
pip install -r pipeline/requirements.txt   # shapely + openpyxl, for the pipeline only
python pipeline/fetch_sites.py             # SCAG housing-element sites -> data/raw/he_sites.geojson
python pipeline/fetch_layers.py            # flood, fire, transit, OSM places of worship, SCAG zoning legend
python pipeline/fetch_surplus.py           # HCD Surplus Land Act notices for OC -> data/raw/sla_oc.json
python pipeline/build_sites.py             # joins zoning, land use, hazards, surplus -> data/processed/sites.geojson
python pipeline/fetch_area.py              # ACS + LODES -> data/processed/tracts.json (needs CENSUS_API_KEY in .env)
python pipeline/fetch_opportunity.py       # TCAC/HCD 2026 opportunity -> tracts.json (run after fetch_area.py)
python pipeline/fetch_rates.py             # Freddie Mac PMMS -> data/processed/rates.json
```

- `fetch_area.py` needs `CENSUS_API_KEY=...` in `.env` (free at <https://api.census.gov/data/key_signup.html>). `.env`
  is gitignored; never commit a key. `.env.example` lists the names only.
- `data/raw/` is a gitignored download cache. A second run makes no requests. Keep request volume low: these are
  public servers.
- `build_sites.py --limit 40` runs a quick test on 40 sites. A layer that fails to download leaves its field empty
  ("unknown"), never guessed.
- `income_limits_2026.json`, `programs.json` and `assumptions.json` are kept by hand: re-check them on the source pages.

## Next steps

- One real deal from a local nonprofit, to replace the synthetic cost lines.
- HUD Fair Market Rents by bedroom for the Santa Ana-Anaheim-Irvine area (huduser.gov blocks automated downloads;
  enter them by hand).
- A choice of income table per program (State / HUD / State HOME), each with its own date.
- Fault zones (California Geological Survey) and local historic districts.
- **Scale:** the statute, the 6920 cost rules, SB 4 and SB 9 are statewide, and the pipeline reads regional or statewide
  services (SCAG, CAL FIRE, Caltrans, FEMA, Census, HCD). Running the next 100 projects in another county means swapping
  the income-limit row and re-running the pipeline with that county's boundary and layers (the county-specific ones,
  such as OC's floodplain and fire copies, need a local equivalent).

## Data and privacy

This project uses only public or provided data. It contains no personal information about real tenants, buyers or
residents (the surplus-notice staff contact column is dropped). It does not file applications or contact any city or
person.

## License

MIT, see [LICENSE](LICENSE). The event's brief, lane pages and docs in `docs/` and `lanes/` keep their own terms.
