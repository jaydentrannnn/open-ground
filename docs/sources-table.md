<!--
DRAFT for README.md (Builder A, Data & Rules, 2026-11-07). Builder C: paste from "## Sources and assumptions" down.
It can replace the README's current "Sources and assumptions" table. "What is real vs mocked" overlaps the README's
table of the same name; "Known gaps" adds to "Where it gets things wrong". Links that start with / open from the repo
root on GitHub, so they work here and in README.md. Statuses come from data/sources.json; where its text had a
caveat we kept the weaker status and the caveat.
-->

## Sources and assumptions

> Prototype only. Not legal, financial or lending advice. **Unknown** means our data could not answer.

**Status:** **VERIFIED** = we (or the event organizers) read the source and it says what we use it for.
**UNVERIFIED** = not confirmed yet, date of the data unknown, or third-party with no data date.
**OUTDATED** = a known old version; a newer one may differ. **ASSUMPTION** = a number we made up or copied from the
event's synthetic example. Every source is in [`data/sources.json`](/data/sources.json); every made-up number is in
[`data/processed/assumptions.json`](/data/processed/assumptions.json).

#### Sites and parcels

| What | Source | Date checked | Status | Where it's used |
|---|---|---|---|---|
| Housing-element sites: 2,126 in 28 OC jurisdictions. 7 cities are not in the layer (see Known gaps) | [SCAG Housing Element Sites](https://maps.scag.ca.gov/scaggis/rest/services/LDX/HousingElementSite_poly_scag/MapServer) | 2026-11-07 | VERIFIED | `pipeline/fetch_sites.py`. Builder mode map and shortlist; Land & law tab: housing-element test; "Est. homes" |
| Zoning per parcel: SCAG regional code and city code. Layer metadata: updated as of October 2025 | [SCAG Zoning_poly_OR](https://maps.scag.ca.gov/scaggis/rest/services/LDX/Zoning_poly_OR/MapServer) | 2026-11-07 | VERIFIED | Pipeline: zoning, acres, slope and census tract for every site; code legend in `scag_zoning_codes.json`. Land & law tab: SB 9 single-family zone test |
| Existing land use 2024 (vacant, parking, under construction, religious facilities). Layer metadata: updated as of July 2025 | [SCAG Existing Land Use](https://maps.scag.ca.gov/scaggis/rest/services/LDX/Existinglanduse_poly_OR/MapServer) | 2026-11-07 | VERIFIED | Pipeline: land use for 2,215 of 2,235 sites. Land & law tab: shown in the housing-element and surplus tests; "Religious Facilities" is an SB 4 lead |
| Surplus public land: 113 OC notices on 109 parcels, all status "Archive". Staff contact column dropped | [HCD Surplus Land Act notices (data.ca.gov)](https://data.ca.gov/dataset/surplus-land-act-notices-of-availability-received) | 2026-11-07 | VERIFIED | `pipeline/fetch_surplus.py`: 109 parcels added as sites. Land & law tab: surplus public land test |
| SB 4 lead: places of worship mapped on OpenStreetMap (896 in OC). Proxy only, not ownership | [OpenStreetMap amenity=place_of_worship](https://wiki.openstreetmap.org/wiki/Tag:amenity%3Dplace_of_worship) | 2026-11-07 | VERIFIED | Pipeline: owner type "faith_proxy" when one is inside the parcel (30 sites). Land & law tab: SB 4 ownership test, shown as a LEAD |
| OC parcels (703k, no owner field) | [OC Public Works Parcels](https://www.ocgis.com/arcpub/rest/services/Map_Layers/Parcels/FeatureServer/0) | 2026-11-06 | VERIFIED | Not used yet. Verified by the event repo |
| Santa Ana assessor parcels (land and improvement value) | [Santa Ana Assessor Parcels](https://gis.santa-ana.org/server/rest/services/Public/GIS_AssessorParcels/MapServer/0) | 2026-11-06 | VERIFIED | Not used yet. Verified by the event repo |
| SB 4 parcel analysis code | [Terner Center SB4-Analysis](https://github.com/Terner-Center/SB4-Analysis) | 2026-11-07 | VERIFIED | Not used yet |

#### Hazards and transit

| What | Source | Date checked | Status | Where it's used |
|---|---|---|---|---|
| Flood: county copy of FEMA flood zones (special flood hazard area flag, floodways). Fields checked; date of the county copy unknown | [OC Floodplains](https://www.ocgis.com/arcpub/rest/services/Map_Layers/Floodplains/MapServer/0) | 2026-11-07 | UNVERIFIED | Pipeline: flood check for every site (196 overlap a special flood hazard area, 17 a floodway). Land & law tab: SB 4 flood tests |
| Flood: FEMA National Flood Hazard Layer, the authority | [FEMA NFHL](https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer) | 2026-11-06 | VERIFIED | Not used by the pipeline (slow service). Where to confirm a flood result |
| Fire, local areas: CAL FIRE map dated March 24, 2025 (Very High only) | [CAL FIRE FHSZ in LRA, 2025](https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/FHSALRA25_v1_All/FeatureServer/0) | 2026-11-07 | VERIFIED | Pipeline: main fire check (51 sites overlap). Land & law tab: SB 4 fire test |
| Fire, local areas: OC county copy, 21 polygons, all Very High. Date unknown; CAL FIRE has issued newer LRA maps | [OC Fire Hazard Severity Zones (LRA)](https://www.ocgis.com/arcpub/rest/services/Map_Layers/Fire_Hazard_Severity_Zones_LRA/MapServer/0) | 2026-11-07 | UNVERIFIED | Pipeline: fire check, any overlap flags the site (45 sites). Land & law tab: SB 4 fire test |
| Fire, state areas: 2007 map. Newer CAL FIRE maps exist; zones may differ | [CAL FIRE FHSZ, State Responsibility Areas (2007)](https://services.gis.ca.gov/arcgis/rest/services/Environment/Fire_Severity_Zones/MapServer/0) | 2026-11-07 | OUTDATED | Pipeline: fire check (3 sites overlap). Land & law tab: SB 4 fire test |
| Fire, state areas: CAL FIRE 2025 layer. Describes itself as submitted to OAL / under public comment | [CAL FIRE FHSZSRA25_3](https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/FHSZSRA25_3/FeatureServer/0) | 2026-11-07 | UNVERIFIED | Not used. Lead only |
| Transit: Caltrans High-Quality Transit Areas (867 polygons around OC) | [Caltrans HQTA](https://caltrans-gis.dot.ca.gov/arcgis/rest/services/CHrailroad/CA_HQ_Transit_Areas/FeatureServer/0) | 2026-11-07 | VERIFIED | Pipeline: transit check for every site (831 overlap). Land & law tab: "Transit area" |

#### Law

| What | Source | Date checked | Status | Where it's used |
|---|---|---|---|---|
| SB 4 (Gov Code 65913.16), faith and college land: HCD fact sheet, April 2026, read in full | [HCD SB 4 fact sheet](https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/aff-hsg-faith-higher-ed-sb-4.pdf) | 2026-11-07 | VERIFIED | Builder mode, Land & law tab: every SB 4 test and note, with the page |
| SB 9 (Gov Code 65852.21, 66411.7), duplexes and lot splits: HCD fact sheet, April 2026, read in full | [HCD SB 9 fact sheet](https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/lot-splits-and-duplexes-sb-9.pdf) | 2026-11-07 | VERIFIED | Builder mode, Land & law tab: every SB 9 test and note, with the page |
| HCD Housing Law Fact Sheets, combined (April 2026) | [HCD Housing Law Fact Sheets](https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/housing-law-fact-sheets.pdf) | 2026-11-06 | VERIFIED | Not cited by a test; the SB 4 and SB 9 sheets above are. Verified by the event repo |
| Affordable housing cost, ownership: HSC 50052.5(b) and (h), official text. (b)(1)-(4) and (h) checked word for word by Builder C in a browser (leginfo blocks automated fetch) | [leginfo HSC 50052.5](https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=HSC&sectionNum=50052.5) | 2026-11-07 | VERIFIED | `app/core/finance.py` statutory price (built and tested, not yet in live Builder mode) |
| HSC 50052.5, FindLaw copy ("current as of Jan 1, 2026"). (b)(1)-(4) and (h) match the official text per Builder C's browser check | [FindLaw HSC 50052.5](https://codes.findlaw.com/ca/health-and-safety-code/hsc-sect-50052-5/) | 2026-11-07 | VERIFIED | The text `finance.py` was coded from |
| What counts as an owner's housing cost: 25 CCR 6920 (a)-(g) | [25 CCR 6920 (Cornell LII)](https://www.law.cornell.edu/regulations/california/25-CCR-6920) | 2026-11-07 | VERIFIED | `finance.py` statutory price; the list of cost items in `assumptions.json` |

#### Who it helps

| What | Source | Date checked | Status | Where it's used |
|---|---|---|---|---|
| OC income limits by household size: HCD State limits, memo dated June 23, 2026 (replaced May 29), p.11. 4-person median $138,600 | [HCD 2026 State Income Limits](https://www.hcd.ca.gov/sites/default/files/docs/grants-and-funding/income-limits-2026.pdf) | 2026-11-07 | VERIFIED | `income_limits_2026.json`. Builder mode sidebar: low-income limit for the household; Does it pencil tab; statutory price |
| City of Irvine 2026 OC income limits page. Not checked against the June 23 revision | [City of Irvine income limits](https://cityofirvine.gov/node/56276) | 2026-11-07 | UNVERIFIED | Not used. Earlier city-posted tables (Irvine, Newport Beach) showed a 4-person median of $136,600; HCD's June 23 PDF says $138,600. We use HCD |
| Tract data: ACS 2024 5-year, the latest on the API (household income, rent burden, crowding, income bins). Every table id checked against its API variable label | [Census ACS 5-year 2024 API](https://api.census.gov/data/2024/acs/acs5) | 2026-11-07 | VERIFIED | `pipeline/fetch_area.py` builds `tracts.json` (614 OC tracts). Who it helps tab: Area Benefit Score |
| Low-wage jobs by workplace: LODES 8 CE01 + CE02 (jobs paying $3,333/month or less), CA 2024 file, the latest year in the directory | [Census LEHD LODES 8 (CA workplace files)](https://lehd.ces.census.gov/data/lodes/LODES8/ca/wac/) | 2026-11-07 | VERIFIED | `tracts.json` low-wage jobs. Who it helps tab: Area Benefit Score |
| TCAC/HCD 2026 Opportunity Map (adopted Dec 2025), 2020 tracts (methodology p.14). Low 0 / Moderate 1 / High 2 / Highest 3; High-Poverty & Segregated kept as an overlay flag (FAQ p.9). A draft 2027 map is posted and not used | [2026 Statewide Summary Table (TCAC)](https://www.treasurer.ca.gov/sites/default/files/2025-11/summary_file.zip) | 2026-11-07 | VERIFIED | `pipeline/fetch_opportunity.py`: 610 of 614 OC tracts scored (4 null, reason recorded). Who it helps tab: Area Benefit Score |

#### Money

| What | Source | Date checked | Status | Where it's used |
|---|---|---|---|---|
| 30-year mortgage rate: 104 weekly points, latest 7.18% (week of 2026-11-05). A market average, not a quote | [Freddie Mac PMMS history](https://www.freddiemac.com/pmms/docs/PMMS_history.csv) | 2026-11-06 | VERIFIED | `pipeline/fetch_rates.py` builds `rates.json`. Home page; Builder mode rate and rate table; Homeowner mode loan rate |
| Housing costs about 30-35% of income | [Lane 3 brief](/lanes/3-fund-it/README.md) | 2026-11-07 | VERIFIED | Basis for the 30% household-budget ASSUMPTION. Builder mode, Does it pencil tab |
| The event's one-home bill. SYNTHETIC: every number is made up | [synthetic-example-deal.json](/lanes/3-fund-it/data/synthetic-example-deal.json) | 2026-11-07 | ASSUMPTION | Default cost lines, subsidy and rent-while-waiting in Builder mode, Does it pencil tab; Home page |
| CalHome (HCD): CLOSED, next round unknown. Lends to agencies and nonprofits, not individuals | [HCD CalHome](https://www.hcd.ca.gov/grants-and-funding/programs-active/calhome) | 2026-11-06; status re-checked 2026-11-07 | VERIFIED | "Who could close the gap" (Builder) and "Help that might apply" (Homeowner), from `programs.json` |
| CalHFA MyHome Assistance: funds availability not stated | [CalHFA homebuyer programs](https://www.calhfa.ca.gov/homebuyer/programs/) | 2026-11-06; status re-checked 2026-11-07 | VERIFIED | Builder mode, "Who could close the gap" |
| CalHFA Dream For All: CLOSED (portal closed after Mar 16, 2026). Registry: funds not confirmed | [CalHFA Dream For All](https://calhfa.ca.gov/dream/) | 2026-11-06; status re-checked 2026-11-07 | VERIFIED | Builder mode, "Who could close the gap" |
| CalHFA ADU Grant: latest round fully allocated (Dec 28, 2023) | [CalHFA ADU Grant](https://www.calhfa.ca.gov/adu/) | 2026-11-07 | VERIFIED | Homeowner mode, "Help that might apply" |
| HCD ADU funding page (lists the CalHFA ADU Grant). Grant availability not confirmed | [HCD ADU funding](https://hcd.ca.gov/building-standards/adu/funding) | 2026-11-07 | UNVERIFIED | Not used by id. `programs.json` notes the CalHFA and HCD pages agree on the grant's maximum |
| OC average rents. Third-party; date of the data not shown | [Rentometer: Orange County](https://www.rentometer.com/average-rent-in/county/orange-county-ca) | 2026-11-07 | UNVERIFIED | Homeowner mode: 1-bedroom rent default (ASSUMPTION below) |
| ADU build cost per sq ft: statewide owner survey, Apr 22, 2021. Page checked; the costs are statewide and from 2021, likely low for OC today | [Terner Center ADU owner survey](https://ternercenter.berkeley.edu/blog/cci-adu-survey) | 2026-11-07 | OUTDATED | Homeowner mode: cost per sq ft default (ASSUMPTION below) |

#### Assumptions

Every row below is a placeholder. Replace it with a real number and its source. The date is when the basis was
checked. "No source" means there is none.

| What | Source | Date checked | Status | Where it's used |
|---|---|---|---|---|
| Household size: 4. Typical family size for the demo | [assumptions.json](/data/processed/assumptions.json): no source | 2026-11-07 | ASSUMPTION | Builder mode sidebar default; README statutory example |
| Family income: $90,000/yr. For 4 people that is very low income in OC (limit $93,050, HCD p.11) | [HCD 2026 State Income Limits](https://www.hcd.ca.gov/sites/default/files/docs/grants-and-funding/income-limits-2026.pdf) | 2026-11-07 | ASSUMPTION | Builder mode sidebar default; README statutory example |
| Home size: 3 bedrooms. HSC 50052.5(h) sizes the cap by bedrooms (3BR = household of 4) | [assumptions.json](/data/processed/assumptions.json) | 2026-11-07 | ASSUMPTION | README statutory example; not used by live Builder mode |
| Share of income for housing: 30%. A household budget, not the legal cap (that is HSC 50052.5(b)) | [Lane 3 brief](/lanes/3-fund-it/README.md) | 2026-11-07 | ASSUMPTION | Builder mode: "Family can pay" and the live gap |
| Tax + insurance + HOA: $400/month | [assumptions.json](/data/processed/assumptions.json): no source | 2026-11-07 | ASSUMPTION | Builder mode: "Family can pay" |
| Habitat OC mortgage rate: UNKNOWN, ask them. The optional toggle's 3.0% default is set in the page code, no source, not in `assumptions.json` | [assumptions.json](/data/processed/assumptions.json) | 2026-11-07 | ASSUMPTION | Builder mode sidebar (off by default) |
| Loan term: 30-year fixed | [assumptions.json](/data/processed/assumptions.json): standard term | 2026-11-07 | ASSUMPTION | Builder mode: "Family can pay" |
| Property tax: 1.1% of price, 6920(b). Basis in the file: 1% general levy plus local add-ons, which vary by area (not checked) | [25 CCR 6920](https://www.law.cornell.edu/regulations/california/25-CCR-6920) | 2026-11-07 | ASSUMPTION | Statutory price; README example ($153,751). Not read by the live app |
| Fire and casualty insurance: $150/month, 6920(c) | [assumptions.json](/data/processed/assumptions.json): no source | 2026-11-07 | ASSUMPTION | Statutory price; README example |
| Maintenance and repairs: $150/month, 6920(d) | [assumptions.json](/data/processed/assumptions.json): no source | 2026-11-07 | ASSUMPTION | Statutory price; README example |
| Utilities allowance: $250/month, 6920(e). The real figure is the local housing authority's utility allowance schedule (not checked) | [assumptions.json](/data/processed/assumptions.json) | 2026-11-07 | ASSUMPTION | Statutory price; README example |
| HOA fees: $0, 6920(f). Assumes a detached home with no HOA | [assumptions.json](/data/processed/assumptions.json) | 2026-11-07 | ASSUMPTION | Statutory price; README example |
| Loan insurance: $0, 6920(a). Assumes none (for example a nonprofit first loan); unknown per lender | [assumptions.json](/data/processed/assumptions.json) | 2026-11-07 | ASSUMPTION | Statutory price; README example |
| Space rent: $0, 6920(g). Assumes the home is not on rented land; a land trust ground lease would add this | [assumptions.json](/data/processed/assumptions.json) | 2026-11-07 | ASSUMPTION | Statutory price; README example |
| Family down payment: $0 | [assumptions.json](/data/processed/assumptions.json): no source | 2026-11-07 | ASSUMPTION | Statutory price; README example |
| Land and building purchase: $360,000 per home | [synthetic-example-deal.json](/lanes/3-fund-it/data/synthetic-example-deal.json) | 2026-11-07 | ASSUMPTION | Builder mode, Does it pencil tab: default cost line (editable), every site |
| Time costs while waiting: $85,000 per home | [synthetic-example-deal.json](/lanes/3-fund-it/data/synthetic-example-deal.json) | 2026-11-07 | ASSUMPTION | Builder mode, Does it pencil tab: default cost line |
| Construction and repairs: $40,000 per home | [synthetic-example-deal.json](/lanes/3-fund-it/data/synthetic-example-deal.json) | 2026-11-07 | ASSUMPTION | Builder mode, Does it pencil tab: default cost line |
| Fees, design, legal, sales: $50,000 per home | [synthetic-example-deal.json](/lanes/3-fund-it/data/synthetic-example-deal.json) | 2026-11-07 | ASSUMPTION | Builder mode, Does it pencil tab: default cost line |
| Public subsidies: $100,000 per home. Placeholder city and state funds | [synthetic-example-deal.json](/lanes/3-fund-it/data/synthetic-example-deal.json) | 2026-11-07 | ASSUMPTION | Builder mode: "Other sources" in the gap |
| Rent earned while waiting: $55,000 per home | [synthetic-example-deal.json](/lanes/3-fund-it/data/synthetic-example-deal.json) | 2026-11-07 | ASSUMPTION | Builder mode: "Other sources" in the gap |
| ADU build cost: $300,000. Replace with a real quote | [assumptions.json](/data/processed/assumptions.json): no source | 2026-11-07 | ASSUMPTION | Not read by the app (Homeowner mode uses size × cost per sq ft, or the owner's quote) |
| ADU cost per sq ft: $250. Survey median ($150,000 or $250/sq ft); statewide, 2021, not OC, likely low today; leaves out site-specific and some soft costs | [Terner Center ADU owner survey](https://ternercenter.berkeley.edu/blog/cci-adu-survey) | 2026-11-07 | ASSUMPTION | Homeowner mode: cost per sq ft default |
| ADU rent: $2,598/month (Rentometer 1-bedroom average) | [Rentometer: Orange County](https://www.rentometer.com/average-rent-in/county/orange-county-ca) | 2026-11-07 | ASSUMPTION | Not read by the app (the by-unit-type entry below is) |
| ADU rent by unit type: 1BR $2,598 (Rentometer). Studio and 2BR: UNKNOWN, the owner enters them. HUD FY2026 Fair Market Rents are a better source but huduser.gov blocks automated downloads; they are gross rent | [Rentometer: Orange County](https://www.rentometer.com/average-rent-in/county/orange-county-ca) | 2026-11-07 | ASSUMPTION | Homeowner mode: rent default |
| Vacancy and upkeep: 25% of rent | [assumptions.json](/data/processed/assumptions.json): no source | 2026-11-07 | ASSUMPTION | Homeowner mode: net rent and paybacks |
| Owner cash in: $50,000 | [assumptions.json](/data/processed/assumptions.json): no source | 2026-11-07 | ASSUMPTION | Homeowner mode: loan size and payback |
| Max homes per site: 9. Basis in the file: 10+ "may trigger SB 4 prevailing wage (UNVERIFIED)" and SB 684/1123 cap at 10. **Disagrees with the SB 4 fact sheet (p.3):** prevailing wage applies to every SB 4 project, whatever its size. SB 684/1123 is not in our source list | [assumptions.json](/data/processed/assumptions.json) | 2026-11-07 | ASSUMPTION | Builder mode filter default and "too big" warning |
| "Eligible households" = households earning under $150k: the nearest ACS income bin to the OC 4-person low-income limit ($148,850). Mixes household sizes. Labelled in the app, not yet in `assumptions.json` | [Census ACS 5-year API](https://api.census.gov/data.html) | 2026-11-07 | ASSUMPTION | Who it helps tab: Area Benefit Score |
| Area Benefit Score weights (rent burden 0.3, crowding 0.2, eligible households 0.2, low-wage jobs 0.2, opportunity 0.1) and the 0-1 scaling ranges. Our choice; `area.score()` returns an ASSUMPTION note for the app to show; not yet in `assumptions.json` | [`app/core/area.py`](/app/core/area.py): no source | 2026-11-07 | ASSUMPTION | Who it helps tab; Builder mode shortlist order |
| The PMMS first-mortgage average used as an ADU loan rate. ADU, HELOC and construction loans are often priced differently. Labelled in the app, not in `assumptions.json` | [Freddie Mac PMMS history](https://www.freddiemac.com/pmms/docs/PMMS_history.csv) | 2026-11-06 | ASSUMPTION | Homeowner mode: loan rate default |

The Builder mode one-pager lists every source in `data/sources.json`, used or not.

### What is real vs mocked

**Real** (public data, built 2026-11-07)

- **2,235 sites:** 2,126 SCAG housing-element sites in 28 OC jurisdictions (including unincorporated County of
  Orange), plus 109 parcels from 113 HCD Surplus Land Act notices.
- **SCAG zoning** on 2,213 sites and **SCAG 2024 existing land use** on 2,215 (155 vacant, 17 parking, 50 religious
  facilities).
- **Flood, fire and transit checks** on each parcel outline, from layers downloaded once: 196 sites overlap a FEMA
  special flood hazard area, 17 a floodway, 52 a Very High fire zone on at least one map, 831 a High-Quality Transit
  Area. The share of the parcel that overlaps is recorded, so a sliver shows as a sliver.
- **Tract data:** ACS 2024 5-year and LODES 2024 for 614 OC tracts, plus the TCAC/HCD 2026 opportunity category
  for 610; 2,215 sites are linked to a tract.
- **Income limits:** HCD 2026 State limits, June 23 revision, checked against the PDF.
- **Mortgage rate:** Freddie Mac PMMS, 104 weekly points to 2026-11-05.
- **Law tests and program statuses:** HCD fact sheets (April 2026) and each program's own page, checked 2026-11-07.

**Partly real**

- **Law verdicts:** real rules, but most SB 4 tests and several SB 9 tests say "unknown" because our data can't check
  them (see Known gaps).
- **SB 4 owner type:** a proxy. 57 sites are flagged: 30 have an OpenStreetMap place of worship inside the parcel, 27
  only have SCAG "Religious Facilities" land use. Leads to check, not ownership.
- **Area Benefit Score:** real tract numbers (ACS 2024, LODES 2024, TCAC 2026 opportunity); the weights, scaling
  ranges and the under-$150k "eligible" proxy are ours (ASSUMPTION).
- **Est. homes:** the city's housing-element capacity for the parcel, not a design. Unknown for the 109 surplus parcels.
- **Gap per home (Builder mode):** real rate and income limits; the family budget is the 30% ASSUMPTION and every cost
  line is synthetic.
- **Statutory price (HSC 50052.5 + 25 CCR 6920):** real formula; the cost items are placeholders; not yet shown in
  Builder mode.
- **Homeowner mode:** real rate and program statuses; cost per sq ft, rent and cash in are ASSUMPTIONS.

**Mocked**

- **Cost to create each home** ($360,000 land, $85,000 time, $40,000 construction, $50,000 fees), **public subsidy**
  ($100,000) and **rent while waiting** ($55,000): the event's SYNTHETIC example. No site has a sourced land cost, so
  the land line is the same placeholder everywhere.
- **Demo family:** $90,000, 4 people, 3 bedrooms, 30% of income for housing, $400/month tax, insurance and HOA.
- **Housing-cost items:** insurance, upkeep, utilities, HOA, loan insurance, space rent, 1.1% tax rate.
- **ADU:** build cost, vacancy share, cash in. Studio and 2-bedroom rents are unknown.
- **Max 9 homes per site** filter default.

### Known gaps

- **Earthquake fault zones are not checked.** The California Geological Survey service needs a login. The SB 4 fault
  test says "unknown" for every site.
- **Historic districts are not checked.** The SB 9 historic test says "unknown" for every site.
- **Fire maps differ in date.** Local areas use CAL FIRE's map dated 2025-03-24; the OC county copy has no date. State
  areas use CAL FIRE's 2007 map (OUTDATED). CAL FIRE's 2025 state-area layer calls itself a draft, so we don't use it.
  Confirm any result on CAL FIRE's current map.
- **Flood uses the county's copy** of FEMA zones, date unknown. FEMA's National Flood Hazard Layer is the authority:
  check the FIRM before deciding.
- **SB 4 ownership is a proxy only.** OpenStreetMap places of worship and SCAG "Religious Facilities" land use are
  leads, not ownership. Confirm on title or the Assessor roll.
- **SB 4 tests our data can't check:** ownership as of Jan 1, 2024; farmland, wetlands, hazardous waste, conservation
  land, protected habitat and easements; industrial uses nearby; 75% of the perimeter next to urban uses.
- **SB 9 tests our data can't check:** historic district or landmark; the other lands listed in Gov Code
  65913.4(a)(6)(B)-(K); whether rent-restricted or recently tenant-occupied housing would be demolished. The zone test
  uses SCAG's regional code, so confirm the city's zone.
- **Seven cities are not in the SCAG housing-element layer:** Santa Ana, Costa Mesa, Huntington Beach, Orange, Tustin,
  Rancho Santa Margarita and Laguna Woods. Surplus notices partly cover three of them (Santa Ana 29 parcels, Tustin
  27, Orange 6). Costa Mesa, Huntington Beach, Rancho Santa Margarita and Laguna Woods have no sites in our data.
- **20 surplus parcels have only the notice's point:** no parcel outline, so no zoning, land use or census tract.
- **Every OC surplus notice is "Archive":** sent to HCD more than 60 days ago (HCD data dictionary). The response
  window has likely passed; whether the land is still available is unknown until someone calls the agency.
- **Housing-element lists go stale.** A listed site may already be sold or built. No site is flagged "under
  construction" in SCAG's 2024 land use, but that does not prove it is still available.
- **"Est. homes" is the city's capacity number**, not a Habitat design.
- **No street address for most sites** (APN only). Surplus notices that describe an occupied home have the address
  withheld.
- **No sourced land cost for any site.** The cost lines are synthetic until a real deal replaces them.
- **"Transit area" approximates SB 4's parking rule.** The rule is about 0.5-mile walking distance to a high-quality
  transit corridor or major transit stop; we test overlap with Caltrans HQTA polygons, not walking distance.
- **City housing funds:** no source; amount and availability unknown. Ask the city housing division.
- **Rebuilding the tract data needs a free Census API key** (the API now refuses requests without one).

### How to rebuild the data

The app runs on the committed files in `data/processed/` and needs no keys. To rebuild them, from the repo root
(Python 3.11+):

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
  is gitignored; never commit a key.
- `data/raw/` is a gitignored download cache. A second run makes no requests; delete a cached file to fetch it again.
  Keep request volume low: these are public servers.
- `build_sites.py --limit 40` runs a quick test on 40 sites. A layer that fails to download leaves its field empty
  ("unknown"), never guessed.
- `income_limits_2026.json`, `programs.json` and `assumptions.json` are kept by hand: re-check them on the source pages.
