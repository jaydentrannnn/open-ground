> **PROTOTYPE. Not legal, financial or lending advice.** Every fact below comes from public data that can be
> wrong or out of date. Confirm it with the agency, the city and a qualified professional before acting on it.

# Real test case: three surplus public parcels in Orange County

> **Update after review (2026-11-07, later the same day).** Two fixes in `pipeline/build_sites.py` change a few
> fields below: (1) surplus parcels in the 7 cities missing from the SCAG housing-element layer (including Orange,
> pick 2) now show the housing-element test as **unknown**, not "no"; (2) surplus `acres` now uses the SCAG parcel
> outline, with the notice's figure kept as `raw.notice_acres`. Also new since this was written: an SB 684/1123
> (starter homes) pathway, Alquist-Priolo fault-zone checks (none of the three picks overlap one) and an
> "Archive" notice now gives the surplus pathway a "maybe", not a "yes". **AB 2011 (housing on commercial sites)**
> was added after that: all three picks (and Orange 390-382-11) pass its commercial-zone test, so AB 2011 is the
> likeliest route; its corridor rules and any city exemption are still unknown. Re-run the scripts at the end to refresh.

Goal: pick the 3 best Surplus Land Act parcels in Orange County for a Habitat-style ownership project of about
4 to 12 homes, to use as the team's real test case. Prepared 2026-11-07 by Builder A (Data & Rules) with
Claude Code. Data used: `data/processed/sites.geojson` (commit 42803a1) and `data/processed/tracts.json`
(commit 2fb63e5).

**How many homes fit on each parcel: unknown.** We did not estimate it. The size screen below is a filter,
not a home count.

## The short answer

| # | Parcel | Size (parcel outline / notice) | What is there (notice / SCAG 2024) | Notice issued | Near transit (HQTA) | Area Benefit Score | Points (of 9) |
|---|---|---|---|---|---|---|---|
| 1 | **Buena Park, APN 276-282-43** | 0.266 ac / 0.26 ac | "Adjoining parking lot" / Vacant Undifferentiated | 2026-05-07 | No | 69 | 7 |
| 2 | **Orange, APN 390-382-09** | 0.180 ac / 0.18 ac | "Surface Parking Lot" / Public Parking Facilities | 2026-07-02 | Yes | 44 | 6 |
| 3 | **Laguna Niguel, APN 740-014-01** (owner: OCTA) | 0.764 ac / 0.56 ac | "vacant" / Retail Strip Development | 2025-09-26 | Yes | 67 | 5 |

- **Buena Park 276-282-43** ranks first. The notice is recent. Both sources say nothing is built on it, the two
  size figures agree, and its need score is the highest of the finalists. Watch out: it adjoins a parcel the
  same notice calls "Historic Resource No. 7".
- **Orange 390-382-09** is in the newest notice of the three and sits in a transit area. It is small (0.18 ac),
  but it touches two more parcels in the same notice (390-382-08 and 390-382-11). Together they are about 1.14 ac.
- **Laguna Niguel 740-014-01** is in a transit area and in a "High Resource" tract with high rent burden. Watch
  out: the notice and SCAG disagree on its size and on whether it is vacant.

All three are zoned commercial. None of the 16 parcels that passed our screens has residential zoning. Whether
homes are allowed, and by which route, is **unknown** until the city answers. See "What to check next" under
each parcel.

## What "Archive" means (read this before calling anyone)

All 109 surplus parcels in our data, including all three picks, have notice status **"Archive"**. The HCD data
dictionary (DOCX on https://data.ca.gov/dataset/surplus-land-act-notices-of-availability-received, checked
2026-11-07; quoted in `pipeline/fetch_surplus.py`) defines the statuses:

- **Active**: the agency sent the notice to HCD within the last 60 days.
- **Archive**: the agency sent the notice to HCD **more than 60 days ago**.

Archive does **not** mean the land is sold or gone. The window to respond to the notice has likely passed, so
**whether the land is still available is unknown until someone calls the agency.** Our tool can draft that call
or email. It never contacts anyone.

## How we chose

Start: the 109 parcels in `sites.geojson` whose id starts with `SLA-`. The code is in "How this was produced"
at the end.

**Step 1. Hard screens.** A parcel is set aside if any of these is true. Promising ones are listed under
near-misses.

| Screen | Rule |
|---|---|
| A home on site | The notice's existing-use text mentions "occupied" or "home", **or** SCAG 2024 land use is a residential label. Nobody should be displaced. When SCAG says residential, we cannot tell whether anyone lives there, so we skip those parcels too. |
| No parcel outline | The notice could not be matched to a SCAG parcel outline ("notice point only"). Hazard checks on a single point are weak. |
| Hazard | Any overlap with a FEMA special flood hazard area, a floodway, or a Very High fire hazard zone. |
| Red flag | The notice text, notice plan/zoning, SCAG land use or SCAG zoning contains: open space, park(s), recreation, trail, golf, equestrian, historic, protected, civic. |
| Active use | The notice describes a use (a store, storage, a building, an occupied home) and does not say vacant. |
| Not vacant or parking | Neither the notice nor SCAG 2024 says vacant or parking. |
| Size | **ASSUMPTION: 0.15 to 1.0 acre.** The notice size and the outline size must both fall in this range. |
| Thin strip | Shape index below 0.30, which is thinner than about 8 to 1. Shape index = 4π × area ÷ perimeter². A square scores 0.785 and a 4:1 rectangle 0.50. |

**Basis for the size screen (ASSUMPTION).** In our data, cities counted 4 to 12 homes on 873 Orange County
housing-element sites (source `scag_he_sites`). Those parcels run from about 0.16 ac (10th percentile) to
0.63 ac (90th percentile), with a median of 0.24 ac. We set the floor at 0.15 ac. We raised the ceiling to
1.0 ac so that parcels with room for parking or open space stay in. A city's counted capacity is a planning
number. It is not what a nonprofit would actually build.

**Step 2. Ranking points (our judgement, 9 maximum).**

| Factor | Points | Why |
|---|---|---|
| Notice issued in 2026 / 2025 / earlier | 2 / 1 / 0 | A newer notice is more likely to still be live. Availability is unknown for all of them |
| Inside a Caltrans High-Quality Transit Area | 1 | Transit access for families |
| Area Benefit Score 60+ / 50-59 / under 50 | 2 / 1 / 0 | Need nearby |
| Notice and SCAG both say vacant or parking | 1 | Less risk of a building or use still on site |
| Notice size and outline size within 25% of each other | 1 | The data agrees |
| Compact shape (shape index 0.50 or more) | 1 | Easier to lay out homes |
| Residential or mixed-use zoning or plan text | 1 | Fewer approvals. No finalist earned this point |

**Step 3. One pick per agency,** so the three picks are three different phone calls. A tie goes to the larger
parcel outline.

**Result.** 16 parcels passed the hard screens and 93 were set aside. Reasons (a parcel can have several): size 71,
not vacant or parking 40, red flag 34, no outline 20, active use 13, thin strip 10, home on site 5, hazard 4.

**Area Benefit Score note.** When this task was briefed, `opportunity_score` was null in `tracts.json`. Commit
2fb63e5 (12:08 today) filled it from the TCAC/HCD 2026 Opportunity Map for 610 of 614 tracts. The scores here
include it and are missing no metric. For comparison, each pick also shows its score without that metric.

---

## Pick 1: Buena Park, APN 276-282-43

| Field | Value | Source |
|---|---|---|
| City | Buena Park | `hcd_sla_notices` |
| APN | 276-282-43 | `hcd_sla_notices` |
| Acres | 0.266 (parcel outline); 0.26 (notice). They agree | `scag_zoning`, `hcd_sla_notices` |
| Notice address | 6591 Beach Boulevard (the notice gives the same address for the adjoining parcel 276-282-19) | `hcd_sla_notices` |
| Zoning | SCAG 1220 "Retail Stores and Commercial Services"; city code CG; the notice says "General Commercial (GC)" | `scag_zoning`, `hcd_sla_notices` |
| Existing use | Notice: "Adjoining parking lot". SCAG 2024 land use: 3100 "Vacant Undifferentiated" | `hcd_sla_notices`, `scag_landuse` |
| Agency | City of Buena Park (agency type "City or County") | `hcd_sla_notices` |
| Notice | SLA0002669, consolidated site "B" (276-282-19 is site "A") | `hcd_sla_notices` |
| Issued / NOA due date | 2026-05-07 / 2026-07-05 (HCD column "NOA Due Date", stored as `interest_due`) | `hcd_sla_notices` |
| Status | Archive (see above) | `hcd_sla_notices` |
| Notice link | None in the notice | `hcd_sla_notices` |
| Flood (FEMA SFHA) | No overlap. OC county copy of the FEMA layer, date unknown; FEMA NFHL is the authority | `oc_floodplains` (`fema_nfhl`) |
| Floodway | No overlap | `oc_floodplains` |
| Fire, Very High zone | No overlap on the CAL FIRE LRA map dated 2025-03-24, the OC LRA copy (date unknown) or CAL FIRE SRA 2007 (outdated) | `calfire_fhsz_lra_2025`, `oc_fhsz_lra`, `calfire_fhsz_sra_2007` |
| Transit (HQTA) | **No** | `caltrans_hqta` |
| Earthquake fault zone, historic district | Not checked: **unknown** | (none) |
| Context, not a legal test | 100% inside a CGS liquefaction zone (Anaheim quad, released 1998-04-15). No landslide zone | `oc_liquefaction`, `cgs_landslide` |
| Shape index | 0.64 (compact) | SCAG outline |

**Area Benefit Score: 69** (76 without the opportunity metric). Missing metrics: none. Census tract 06059110500
(Tract 1105).

| Metric | Value | Scaled 0-1 | Weight |
|---|---|---|---|
| Renters paying 30%+ of income on rent | 57.2% | 0.74 | 0.3 |
| Overcrowded households | 20.4% | 0.68 | 0.2 |
| Households earning under $150k (ASSUMPTION: nearest ACS bin to the OC 4-person low-income limit) | 1,911 | 0.64 | 0.2 |
| Low-wage jobs located in the tract (LODES CE01+CE02) | 3,409 | 1.00 | 0.2 |
| TCAC/HCD 2026 opportunity | 0 (Low Resource) | 0.00 | 0.1 |

Sources: `census_acs` (ACS 2024 5-year), `lodes` (2024 workplace file), `tcac_opp_2026`.

**Pathway verdicts** (`app/core/pathways.py`):

- **SB 4: no.** The owner is a public agency. SB 4 needs land owned by a religious institution or an independent
  college as of Jan 1, 2024 (`hcd_sb4_factsheet` p.1). The fire and flood tests pass. Fault zone, other
  environmental exclusions, nearby industrial uses and the 75% urban-perimeter test are unknown.
- **SB 9: no.** CG is not a single-family zone (`hcd_sb9_factsheet` p.1).
- **Housing element: no.** This APN is not in the SCAG housing-element site layer, which does cover Buena Park
  (`scag_he_sites`).
- **Surplus land: yes.** A Surplus Land Act notice exists (`hcd_sla_notices`). Availability is unknown (Archive).

**Red flags.** The adjoining parcel in the same notice (276-282-19) is described as "1,200 square foot building
(Historic Resource No. 7)". SCAG 2024 labels it "Single Family Residential". The two parcel outlines touch.

**What to check next**

1. Call the City of Buena Park (the notice has no link). Ask whether the lot is still available, whether it is
   offered alone or only together with 276-282-19, and whether anyone who answered the notice is negotiating.
2. Historic: ask what protections apply to Historic Resource No. 7 next door and whether they limit a project on
   the parking lot. Ask whether anyone lives in that building (SCAG says single-family residential). If someone
   does, nothing we propose should displace them.
3. Zoning: ask whether CG allows homes, at what density, and whether an overlay or specific plan applies. Two
   leads our tool does not test yet are listed in `lanes/1-find-it/data/pathways.json` (source
   `hcd_law_factsheets`): AB 2011 (housing on commercial corridors) and SB 684 / SB 1123 (small-lot subdivisions of up to
   10 homes). Whether they apply here is unknown.
4. Liquefaction zone: ask a geotechnical engineer what study is needed.
5. Still unknown: earthquake fault zone (the CGS service needs a login), contamination history, and parking
   rules (the parcel is not in an HQTA).
6. Confirm the parcel lines and size with the County Assessor.

---

## Pick 2: Orange, APN 390-382-09

| Field | Value | Source |
|---|---|---|
| City | Orange | `hcd_sla_notices` |
| APN | 390-382-09 | `hcd_sla_notices` |
| Acres | 0.180 (parcel outline); 0.18 (notice). They agree | `scag_zoning`, `hcd_sla_notices` |
| Notice address | 154 S Grand St | `hcd_sla_notices` |
| Zoning | SCAG 1200 "Commercial and Services"; city code C-2; the notice says "(C2) General Business" | `scag_zoning`, `hcd_sla_notices` |
| Existing use | Notice: "Surface Parking Lot". SCAG 2024 land use: 1247 "Public Parking Facilities" | `hcd_sla_notices`, `scag_landuse` |
| Agency | City of Orange (agency type "City or County") | `hcd_sla_notices` |
| Notice | SLA0002834 (six parcels on S Grand St / E Chapman Ave) | `hcd_sla_notices` |
| Issued / NOA due date | 2026-07-02 / 2026-08-30 | `hcd_sla_notices` |
| Status | Archive | `hcd_sla_notices` |
| Notice link | https://www.cityoforange.org/business/economic-development (as given in the notice; not opened by us) | `hcd_sla_notices` |
| Flood (FEMA SFHA) / floodway | No overlap / no overlap | `oc_floodplains` |
| Fire, Very High zone | No overlap (same three maps as pick 1) | `calfire_fhsz_lra_2025`, `oc_fhsz_lra`, `calfire_fhsz_sra_2007` |
| Transit (HQTA) | **Yes** | `caltrans_hqta` |
| Earthquake fault zone, historic district | Not checked: **unknown** | (none) |
| Context, not a legal test | No liquefaction or landslide zone | `oc_liquefaction`, `cgs_landslide` |
| Shape index | 0.62 (compact) | SCAG outline |

**Area Benefit Score: 44** (49 without the opportunity metric). Missing metrics: none. Census tract 06059075902
(Tract 759.02).

| Metric | Value | Scaled 0-1 | Weight |
|---|---|---|---|
| Renters paying 30%+ of income on rent | 49.4% | 0.59 | 0.3 |
| Overcrowded households | 6.5% | 0.22 | 0.2 |
| Households earning under $150k (ASSUMPTION, as above) | 2,246 | 0.75 | 0.2 |
| Low-wage jobs located in the tract | 1,058 | 0.35 | 0.2 |
| TCAC/HCD 2026 opportunity | 0 (Low Resource; the high-poverty and segregated overlay is blank, so unknown) | 0.00 | 0.1 |

**Pathway verdicts**

- **SB 4: no.** The owner is a public agency (`hcd_sb4_factsheet` p.1). Other tests as in pick 1.
- **SB 9: no.** C-2 is not a single-family zone (`hcd_sb9_factsheet` p.1).
- **Housing element: the tool says "no", but the real answer is unknown.** The City of Orange is not in the
  SCAG housing-element layer (`scag_he_sites` status note), so we cannot tell whether the parcel is on Orange's
  adopted site inventory. See "Data problems" below.
- **Surplus land: yes** (`hcd_sla_notices`). Availability is unknown (Archive).

**The rest of the notice.** We computed from SCAG outlines which parcels touch:

- 390-382-09 touches **390-382-08**, an identical parking lot of 0.18 ac at 148 S Grand St in the same notice.
- 390-382-09 touches **390-382-11**, a 0.78 ac parcel the notice calls "Former governmental-use facility -
  vacant". This is the earlier eyeball pick; see the next section.
- Together, -08, -09 and -11 are about 1.14 ac of parcel outline.
- The same notice also lists **390-382-07** as "Residential - occupied". It touches -08 but not -09. We
  excluded it, and any project must not displace the people living there.

**Why it ranks here.** It is the most recent notice of the three, sits in a transit area, both sources say it
is a parking lot, the size figures agree, and the shape is compact. Weaknesses: it is small, near the bottom of
the size screen. That is inside the range where cities counted 4 to 12 homes, but whether 4 homes fit here is
unknown. Its need score (44) is the lowest of the three.

**What to check next**

1. Contact the City of Orange through the notice's Economic Development link. Ask whether -09 is still
   available, whether it is offered alone or with -08 and -11, and whether anyone answered the July 2026 notice.
2. Zoning: ask whether C-2 allows homes, at what density, and under which overlays or specific plans. The
   AB 2011 and SB 684 / SB 1123 leads above apply here too (untested).
3. Historic: our tool does not check historic districts. Ask the city's planning staff, or check the city's
   maps, whether this block is in a local or National Register historic district and what design review
   applies.
4. Public parking: ask whether the city has to replace these spaces. Unknown.
5. Housing element: read Orange's adopted site inventory directly.
6. Still unknown: earthquake fault zone and contamination history.

---

## Pick 3: Laguna Niguel, APN 740-014-01 (owner: OCTA)

| Field | Value | Source |
|---|---|---|
| City | Laguna Niguel | `hcd_sla_notices` |
| APN | 740-014-01 | `hcd_sla_notices` |
| Acres | **0.764 (parcel outline) vs 0.56 (notice): they disagree.** The notice also gives 0.56 ac for the adjoining 740-014-05, whose outline is 0.303 ac | `scag_zoning`, `hcd_sla_notices` |
| Notice address | None in the notice | `hcd_sla_notices` |
| Zoning | SCAG 1200 "Commercial and Services"; city code CH (our data does not say what CH stands for); the notice says "Commercial" | `scag_zoning`, `hcd_sla_notices` |
| Existing use | **Notice: "vacant". SCAG 2024 land use: 1223 "Retail Strip Development". They disagree** | `hcd_sla_notices`, `scag_landuse` |
| Agency | Orange County Transportation Authority (agency type "DISTRICT") | `hcd_sla_notices` |
| Notice | SLA0002082 | `hcd_sla_notices` |
| Issued / NOA due date | 2025-09-26 / 2025-11-26 | `hcd_sla_notices` |
| Status | Archive | `hcd_sla_notices` |
| Notice link | None in the notice | `hcd_sla_notices` |
| Flood (FEMA SFHA) / floodway | No overlap / no overlap | `oc_floodplains` |
| Fire, Very High zone | No overlap (same three maps as pick 1) | `calfire_fhsz_lra_2025`, `oc_fhsz_lra`, `calfire_fhsz_sra_2007` |
| Transit (HQTA) | **Yes** | `caltrans_hqta` |
| Earthquake fault zone, historic district | Not checked: **unknown** | (none) |
| Context, not a legal test | No liquefaction or landslide zone | `oc_liquefaction`, `cgs_landslide` |
| Shape index | 0.77 (compact) | SCAG outline |

**Area Benefit Score: 67** (also 67 without the opportunity metric). Missing metrics: none. Census tract
06059032022 (Tract 320.22).

| Metric | Value | Scaled 0-1 | Weight |
|---|---|---|---|
| Renters paying 30%+ of income on rent | 59.4% | 0.79 | 0.3 |
| Overcrowded households | 10.1% | 0.34 | 0.2 |
| Households earning under $150k (ASSUMPTION, as above) | 1,543 | 0.51 | 0.2 |
| Low-wage jobs located in the tract | 6,145 | 1.00 | 0.2 |
| TCAC/HCD 2026 opportunity | 2 (High Resource) | 0.67 | 0.1 |

**Pathway verdicts**

- **SB 4: no.** The owner is a public agency (`hcd_sb4_factsheet` p.1).
- **SB 9: no.** CH is not a single-family zone (`hcd_sb9_factsheet` p.1).
- **Housing element: no.** This APN is not in the SCAG layer, which does cover Laguna Niguel (`scag_he_sites`).
- **Surplus land: yes** (`hcd_sla_notices`). Availability is unknown (Archive).

**Why it ranks here.** It sits in a transit area and a High Resource tract with high rent burden and many
low-wage jobs: the second-highest need score of the finalists. The shape is compact and the notice is from
2025. Weaknesses: the two sources disagree on its size and on whether anything is built there, and the owner
is a transportation agency.

**What to check next**

1. Call OCTA (the notice has no link). Ask whether the parcel is still available. Ask whether it is offered
   alone or with 740-014-05, which is in the same notice and touches it; together they are about 1.07 ac of
   outline. Ask about any transit-related restrictions or easements (unknown).
2. Resolve the conflicts: check a current aerial photo or visit to confirm it is vacant, and confirm the size
   with the County Assessor.
3. Zoning: ask what CH allows in Laguna Niguel and whether homes are possible. The AB 2011 and SB 684 / SB 1123
   leads apply (untested).
4. Still unknown: earthquake fault zone, contamination history, and parking rules.

---

## The earlier eyeball pick: Orange, APN 390-382-11 (checked on its own)

| Check | Result |
|---|---|
| Size | 0.779 ac outline / 0.77 ac notice: they agree |
| Zoning | SCAG 1200 "Commercial and Services"; city C-2; the notice says "(C2) General Business" |
| Existing use | Notice: "Former governmental-use facility - vacant". **SCAG 2024 land use: 1243 "Fire Stations"** |
| Notice | SLA0002834, issued 2026-07-02, NOA due 2026-08-30, Archive, with the Economic Development link |
| Hazards | No SFHA, no floodway, no Very High fire. In an HQTA. No liquefaction or landslide zone |
| Shape index | 0.72 |
| Area Benefit Score | 44 (49 without the opportunity metric), the same tract as pick 2 |
| Pathways | SB 4 no, SB 9 no, housing element "no" (really unknown, as for pick 2), surplus land yes |

The facts in the brief check out. It scored **5 of 9**, one point behind the two parking lots in the same
notice. The only reason is that SCAG 2024 still records a fire-station use, so the two sources do not both say
vacant or parking. A building may still stand there. The cost of demolishing or reusing it is unknown, and so is
whether it is a historic resource. It touches pick 2. **Treat 390-382-08, -09 and -11 as one conversation with
the City of Orange.** If the city would rather sell -11, it is the roomier parcel, but a building may have to come down.

## Near-misses (set aside, with the reason)

| Parcel | Why it is not in the top 3 |
|---|---|
| Orange 390-382-08 (6 pts) | Twin of pick 2, and only one pick per agency. It touches the occupied-home parcel 390-382-07 |
| Orange 390-382-11 (5 pts) | See the section above |
| Orange 390-382-14 (5 pts) | Parking lot, 0.34 ac, C-1, narrower shape (0.40). Same agency as pick 2 |
| Laguna Niguel 740-014-05 (5 pts) | Same OCTA notice as pick 3 and touches it. The outline is 0.303 ac but the notice says 0.56 |
| Anaheim 255-022-54 (4 pts) | The best parcel from a fourth agency: vacant per both sources, 0.675 ac outline / 0.79 ac notice, need score 53. But the notice dates from 2022-05-02 and it is not in an HQTA. Its consolidated partner 255-022-57 has no outline |
| Laguna Niguel 637-231-01 (4 pts) | A separate OCTA notice (SLA0002081). The notice says 0.23 ac but the outline is 0.497 ac, and the notice's plan/zoning field says "vacant", which is not a zone |
| Santa Ana notice SLA0002451 (14 parcels, e.g. 405-274-10) | Issued 2026-02-20, all "Vacant", in an HQTA, need score 48 (tract 06059075100). Set aside because the plan text is **"Open Space with Commercial Option"**. About 2.86 ac of outline across 13 parcels (one has no outline). If the City of Santa Ana confirms homes are possible, this becomes a strong lead. Santa Ana is not in the SCAG housing-element layer |
| Cypress 244-472-09 | Vacant per the notice but 1.1 ac, just over the size screen. SCAG 2024 says "Agriculture" (a conflict). Notice from 2023 |
| Fullerton 293-154-37 | The only parcel that the notice calls vacant and that matched a residential zone (R-1, "Low-Density Residential"). Mission Viejo's notice also says "Residential", but no zone was matched there. But SCAG 2024 calls it "Local Parks and Recreation", and at 2.5 ac it is over the size screen. Notice from 2023 |
| Tustin 430-371-29 and 430-371-33 | Tustin Legacy, plan "Mixed Use", SCAG says vacant, need score 63, notice from 2025. But they are long thin strips (shape index 0.24 and 0.06), and the notice's existing-use field is blank |
| Buena Park 136-211-40 and 136-211-71 (3 pts) | Entertainment Corridor Specific Plan, in an HQTA. The notice says vacant but SCAG 2024 says "Religious Facilities". Notices from 2023 |
| Mission Viejo (one notice listing 5 APNs, plan "Residential", "Vacant", 2025-01-08) | No parcel outline matched, so the size is unknown |
| Lake Forest 613-621-18 | The newest notice in Orange County (2026-07-22) and vacant, but 6.48 ac, too big for 4-12 homes unless the city would split it |
| Laguna Beach 658-101-40 (parking) and 658-101-39 (vacant restaurant) | 0.10 and 0.11 ac, under the size screen |
| Anaheim 037-072-43 | In an HQTA, but the notice says "indoor storage and parking", which is an active use |

## Data problems found (for Builder A to review)

1. **The housing-element verdict is wrong for 7 cities.** `pipeline/build_sites.py` sets
   `housing_element_site: false` for every surplus-only parcel. Orange, Santa Ana, Tustin, Costa Mesa,
   Huntington Beach, Rancho Santa Margarita and Laguna Woods are not in the SCAG layer (`scag_he_sites` status),
   so for parcels in those cities the field should be `null` and the HE verdict "maybe", not "no".
2. **The contract `acres` field holds the notice size, which is sometimes the whole site repeated on every
   parcel.** For example: 101.5 ac on each of 8 golf-course parcels (outlines 0.02 to 94.4 ac), 35.0 ac on 14
   Tustin parcels, 4.56 ac on both San Clemente parcels, and 0.56 ac on both OCTA Laguna Niguel parcels
   (outlines 0.764 and 0.303). `raw.zoning_acres` holds the per-parcel figure. Sorting or filtering by `acres`
   will mislead.
3. **The notice and SCAG 2024 disagree on the existing use** for: OCTA Laguna Niguel (vacant vs retail), Buena
   Park Entertainment Corridor parcels (vacant vs Religious Facilities ×2, Hotels and Motels,
   Transportation/Utilities, Retail), Cypress (vacant vs Agriculture), Orange 390-382-11 (vacant vs Fire
   Stations) and Santa Ana 404-102-06 (the notice describes a former YMCA building on the National Register;
   SCAG says Fire Stations).
4. **Likely typos in the notices:** Buena Park 276-291-24 says 0.014 ac but its outline is 0.148 ac.
   Laguna Niguel 637-231-01 has "vacant" in its plan/zoning field.
5. **Zoning disagrees:** for Orange 390-382-05 the notice says "(C2) General Business" while the SCAG local code
   is C-1.
6. **Blank notices:** Tustin cases 82 and 83 (430-251-23, 430-251-37) have no agency, size or use.
7. **`city` is the notice's city, not the agency's.** Tustin-owned homes (104-611-30/-33, County E-4 zoning) and
   Garden Grove-owned golf-course parcels are listed under Santa Ana. This may be correct, because agencies can
   own land outside their city, but it is worth showing both fields in the UI.
8. **Notices that list several APNs are joined on the first APN only.** Examples: "430-481-07 - 011", the
   6-APN Buena Park row, Westminster "096-522-02; 096-522-04", and the 5-APN Mission Viejo row.
9. **Thin strips:** 10 of the 109 parcels have a shape index under 0.30. The app shows them as sites without
   any warning. `sites.geojson` keeps only a point per site, so shape checks have to read the hashed raw cache.
10. **Formatting in the source data:** the existing-use text for 404-102-06 has underscores where commas belong
    ("44_468 square foot").

## Sources (all checked 2026-11-07 unless noted; full entries in `data/sources.json`)

| Id | What | URL | Status |
|---|---|---|---|
| `hcd_sla_notices` | HCD Surplus Land Act notices (CSV and data dictionary) | https://data.ca.gov/dataset/surplus-land-act-notices-of-availability-received | VERIFIED: 113 OC notices, 109 parcels, all Archive. Contact column dropped |
| `scag_zoning` | SCAG Zoning_poly_OR (zoning, parcel outline, tract) | https://maps.scag.ca.gov/scaggis/rest/services/LDX/Zoning_poly_OR/MapServer | VERIFIED; metadata says updated as of Oct 2025 |
| `scag_landuse` | SCAG Existing Land Use 2024 | https://maps.scag.ca.gov/scaggis/rest/services/LDX/Existinglanduse_poly_OR/MapServer | VERIFIED; metadata says updated as of July 2025 |
| `scag_he_sites` | SCAG Housing Element Sites | https://maps.scag.ca.gov/scaggis/rest/services/LDX/HousingElementSite_poly_scag/MapServer | VERIFIED; does not cover 7 cities including Orange |
| `oc_floodplains` | OC copy of FEMA flood zones | https://www.ocgis.com/arcpub/rest/services/Map_Layers/Floodplains/MapServer/0 | Fields VERIFIED; vintage UNKNOWN |
| `fema_nfhl` | FEMA National Flood Hazard Layer (the authority) | https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer | VERIFIED (checked 2026-11-06) |
| `calfire_fhsz_lra_2025` | CAL FIRE fire hazard zones, LRA, map dated 2025-03-24 | https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/FHSALRA25_v1_All/FeatureServer/0 | VERIFIED |
| `oc_fhsz_lra` | OC copy of fire hazard zones, LRA | https://www.ocgis.com/arcpub/rest/services/Map_Layers/Fire_Hazard_Severity_Zones_LRA/MapServer/0 | UNVERIFIED vintage |
| `calfire_fhsz_sra_2007` | CAL FIRE fire hazard zones, SRA 2007 | https://services.gis.ca.gov/arcgis/rest/services/Environment/Fire_Severity_Zones/MapServer/0 | OUTDATED |
| `caltrans_hqta` | Caltrans High-Quality Transit Areas | https://caltrans-gis.dot.ca.gov/arcgis/rest/services/CHrailroad/CA_HQ_Transit_Areas/FeatureServer/0 | VERIFIED |
| `oc_liquefaction` | OC copy of CGS liquefaction zones (context only) | https://www.ocgis.com/arcpub/rest/services/Map_Layers/Liquefaction/MapServer/0 | VERIFIED fields; zones released 1998-2005 |
| `cgs_landslide` | CGS landslide zones (context only) | https://services2.arcgis.com/zr3KAIbsRSUyARHG/arcgis/rest/services/CGS_Landslide_Zones/FeatureServer/0 | VERIFIED |
| `census_acs` | Census ACS 5-year 2024 (rent burden, crowding, income bins) | https://api.census.gov/data.html | See `data/sources.json`; `pipeline/fetch_area.py` says ACS 2024 was checked on 2026-11-07 |
| `lodes` | Census LEHD LODES 8, CA workplace file 2024 | https://lehd.ces.census.gov/data/ | See `data/sources.json`; `pipeline/fetch_area.py` names `ca_wac_S000_JT00_2024` |
| `tcac_opp_2026` | TCAC/HCD 2026 Opportunity Map (adopted December 2025) | https://www.treasurer.ca.gov/sites/default/files/2025-11/summary_file.zip (listed on https://www.treasurer.ca.gov/ctcac/opportunity) | VERIFIED: 610 of 614 tracts scored |
| `hcd_sb4_factsheet` | HCD SB 4 fact sheet, April 2026 | https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/aff-hsg-faith-higher-ed-sb-4.pdf | VERIFIED: read in full |
| `hcd_sb9_factsheet` | HCD SB 9 fact sheet, April 2026 | https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/lot-splits-and-duplexes-sb-9.pdf | VERIFIED: read in full |
| `hcd_law_factsheets` | HCD Housing Law Fact Sheets (AB 2011 and SB 684 / SB 1123 leads) | https://www.hcd.ca.gov/sites/default/files/docs/planning-and-community/housing-law-fact-sheets.pdf | VERIFIED (event repo, checked 2026-11-06). Not read for these parcels: leads only |

## How this was produced

Everything is read-only and needs no network access. Run from the repo root with the team's virtualenv. The
`shapely` package comes from `pipeline/requirements.txt`. Copy each script below into a scratch file outside the
repo, then:

```bash
cd open-ground
.venv/bin/python /path/to/screen.py     # screens + ranks the 109 surplus parcels, prints the 3 picks
.venv/bin/python /path/to/extras.py     # size-screen basis, score parts, pathway verdicts, adjacency, context layers
```

Expected output of `screen.py` (first lines):

```
SLA parcels 109: kept 16, dropped 93; drop reasons (a parcel can have several): {'size': 71, 'no_outline': 20,
'not_vacant_or_parking': 40, 'thin_strip': 10, 'active_use': 13, 'home': 5, 'red_flag': 34, 'hazard': 4}
7 | Buena Park | 276-282-43 | ...
...
PICKS: [('Buena Park', '276-282-43', 7), ('Orange', '390-382-09', 6), ('Laguna Niguel', '740-014-01', 5)]
```

`screen.py`:

```python
"""Screen the 109 OC Surplus Land Act parcels for a 4-12 home ownership test case. READ-ONLY.
Run from the repo root:  .venv/bin/python screen.py
"""
import glob
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime

sys.path.insert(0, "app")
from shapely.geometry import shape  # pipeline dependency, already in .venv

from core import area, contracts

LO, HI = 0.15, 1.0  # ASSUMPTION: size screen in acres (basis in the doc). A screen, not a unit count.
HOME_LABELS = {"Single Family Residential", "Low-Rise Apartments, Condominiums, and Townhouses",
               "Multi-Family Residential", "Mobile Homes and Trailer Parks",
               "Duplexes, Triplexes and 2- or 3-Unit Condominiums and Townhouses"}
RED = re.compile(r"open space|\bparks?\b|recreation|trail|golf|equestrian|historic|protected|civic", re.I)
ACTIVE = re.compile(r"occupied|home|restaurant|liquidator|storage|dealership|service station|ymca|"
                    r"commercial$|^governmental-use facility$|building|structure|civic", re.I)
VAC_PARK = re.compile(r"vacant|parking|paved lot", re.I)

# Parcel outlines cached by pipeline/build_sites.py (SCAG Zoning_poly_OR features, keyed by APN24).
# sites.geojson keeps only a point per site, so the shape check reads the cache.
outline = {}
for fn in glob.glob("data/raw/*.json"):
    try:
        feats = json.load(open(fn)).get("features") or []
    except (ValueError, AttributeError):
        continue
    for f in feats:
        p = f.get("properties") or {}
        if p.get("APN24") and f.get("geometry") and "ZN24_SCAG" in p:
            outline.setdefault(p["APN24"], shape(f["geometry"]))


def shape_index(apn):
    """Polsby-Popper 4*pi*area/perimeter^2: square 0.785, 4:1 rectangle 0.50, 8:1 rectangle 0.31."""
    m = re.search(r"\d{3}-?\d{3}-?\d{2}", apn or "")
    g = outline.get(m.group().replace("-", "")) if m else None
    return round(4 * math.pi * g.area / g.length ** 2, 2) if g is not None and g.length else None


def issued(s):
    try:
        return datetime.strptime(s["raw"]["sla"]["issued"], "%m-%d-%Y").date()
    except (TypeError, ValueError, KeyError):
        return None


tracts = contracts.load_tracts()
sites = [s for s in contracts.load_sites() if s["id"].startswith("SLA-")]
by_case = {}
for s in sites:
    by_case.setdefault(s["raw"]["sla"]["case"], []).append(s)

kept, dropped, reasons = [], [], Counter()
for s in sites:
    r, n = s["raw"], s["raw"]["sla"]
    eu = r.get("existing_use") or {}
    eu_text, eu_label = (n.get("existing_use") or "").strip(), eu.get("label") or ""
    scag_a, notice_a = r.get("zoning_acres"), s.get("acres")
    texts = " | ".join(filter(None, [eu_text, eu_label, n.get("plan_zoning_text"), s.get("zoning_scag")]))
    pp = shape_index(s["apn"])
    why = {}
    if re.search(r"occupied|home", eu_text, re.I) or eu_label in HOME_LABELS:
        why["home"] = f"a home on site (notice '{eu_text or 'blank'}', SCAG '{eu_label or 'none'}')"
    if r.get("outline") != "parcel":
        why["no_outline"] = "notice point only, no parcel outline"
    if s.get("in_flood_zone") or r.get("floodway") or s.get("in_fire_zone"):
        why["hazard"] = "flood SFHA, floodway or very high fire hit"
    if RED.search(texts):
        why["red_flag"] = f"'{RED.search(texts).group()}' in: {texts}"
    if eu_text and ACTIVE.search(eu_text) and "vacant" not in eu_text.lower():
        why["active_use"] = f"notice existing use '{eu_text[:60]}'"
    if not (VAC_PARK.search(eu_text) or eu.get("vacant") or eu.get("parking")):
        why["not_vacant_or_parking"] = "neither source says vacant or parking"
    sizes = [a for a in (scag_a, notice_a) if a is not None]
    if not sizes or any(not (LO <= a <= HI) for a in sizes):
        why["size"] = f"outside {LO}-{HI} ac (notice {notice_a}, outline {scag_a and round(scag_a, 3)})"
    if pp is not None and pp < 0.3:
        why["thin_strip"] = f"long thin strip (shape index {pp})"
    if why:
        reasons.update(why.keys())
        dropped.append((s, why))
        continue
    d, sc = issued(s), area.score(tracts.get(s.get("tract_id")))
    pts = {  # ranking points: judgement calls, stated in the doc
        "recent_notice": 2 if d and d.year == 2026 else 1 if d and d.year == 2025 else 0,
        "hqta": 1 if s.get("in_hqta") else 0,
        "area_score": 2 if (sc["score"] or 0) >= 60 else 1 if (sc["score"] or 0) >= 50 else 0,
        "both_sources_vacant_or_parking": 1 if VAC_PARK.search(eu_text) and (eu.get("vacant") or eu.get("parking")) else 0,
        "acres_agree_25pct": 1 if scag_a and notice_a and abs(scag_a - notice_a) / max(scag_a, notice_a) <= 0.25 else 0,
        "compact_shape": 1 if pp is not None and pp >= 0.5 else 0,
        "residential_or_mixed_zoning": 1 if re.search(r"residential|mixed", texts, re.I) else 0,
    }
    flags = [f"same notice as {o['apn']}: '{o['raw']['sla']['existing_use']}'" for o in by_case[n["case"]]
             if o is not s and re.search(r"historic|occupied", o["raw"]["sla"].get("existing_use") or "", re.I)]
    kept.append((sum(pts.values()), scag_a or 0, s, pts, pp, sc["score"], flags))

kept.sort(key=lambda k: (-k[0], -k[1]))  # points, then larger parcel outline
print(f"SLA parcels {len(sites)}: kept {len(kept)}, dropped {len(dropped)}; drop reasons (a parcel can have several): "
      f"{dict(reasons)}")
for tot, a, s, pts, pp, abs_, flags in kept:
    n = s["raw"]["sla"]
    print(f"{tot} | {s['city']} | {s['apn']} | {n['agency']} | notice {n['case']} {issued(s)} | outline {round(a, 3)} ac,"
          f" notice {s['acres']} ac | shape {pp} | ABS {abs_} | HQTA {s['in_hqta']} | {s['zoning_local']} | "
          f"{n['existing_use']} / SCAG {(s['raw'].get('existing_use') or {}).get('label')} | "
          f"{[k for k, v in pts.items() if v]} | {flags}")
picks, seen = [], set()  # best-ranked parcel per agency: three picks = three different calls
for k in kept:
    agency = re.sub(r"\s*\(.*\)", "", k[2]["raw"]["sla"].get("agency") or "unknown").strip().lower()
    if agency not in seen:
        seen.add(agency)
        picks.append(k)
print("PICKS:", [(k[2]["city"], k[2]["apn"], k[0]) for k in picks[:3]])
print("DROPPED:")
for s, why in sorted(dropped, key=lambda x: (x[0]["city"], x[0]["apn"])):
    print(f"  {s['city']} | {s['apn']} | {'; '.join(why.values())}")
```

`extras.py`:

```python
"""Size-screen basis, per-pick detail, adjacency and context layers. READ-ONLY. Run from the repo root."""
import glob
import json
import sys

sys.path.insert(0, "app")
from shapely.geometry import shape

from core import area, contracts, pathways

sites = contracts.load_sites()
tracts = contracts.load_tracts()

# 1. size-screen basis: acreage of housing-element sites where the city counted 4-12 homes
acres = sorted(s["acres"] for s in sites if s["id"].startswith("HE-") and s.get("acres")
               and 4 <= ((s["raw"].get("he_capacity") or {}).get("Total") or 0) <= 12)
q = lambda p: acres[int(p * (len(acres) - 1))]
print(f"HE sites with 4-12 homes: {len(acres)}; acres p10 {q(.1):.3f} p25 {q(.25):.3f} median {q(.5):.3f} "
      f"p75 {q(.75):.3f} p90 {q(.9):.3f}")

# 2. detail per parcel: score parts and pathway verdicts
sla = {s["apn"]: s for s in sites if s["id"].startswith("SLA-")}
for apn in sys.argv[1:] or ["276-282-43", "390-382-09", "740-014-01", "390-382-11"]:
    s, t = sla[apn], tracts.get(sla[apn]["tract_id"])
    sc = area.score(t)
    no_opp = area.score({k: v for k, v in t.items() if k != "opportunity_score"})["score"]
    print(f"\n{apn} tract {s['tract_id']} score {sc['score']} (without opportunity {no_opp}) missing {sc['missing']}")
    for p in sc["parts"]:
        print(f"   {p['metric']}: {p['value']} -> {p['scaled']:.2f} x {p['weight']}")
    for pid, e in pathways.evaluate(s).items():
        print(f"   {pid}: {e['verdict']} | " + " | ".join(f"{x['result']}: {x['why'][:90]}" for x in e["tests"]
                                                     if x["result"] != "pass"))

# 3. which parcel outlines touch, and context layers (liquefaction / landslide)
outline = {}
for fn in glob.glob("data/raw/*.json"):
    try:
        for f in json.load(open(fn)).get("features") or []:
            p = f.get("properties") or {}
            if p.get("APN24") and f.get("geometry") and "ZN24_SCAG" in p:
                outline.setdefault(p["APN24"], shape(f["geometry"]).buffer(0))
    except (ValueError, AttributeError):
        pass
for a, b in [("27628243", "27628219"), ("39038209", "39038208"), ("39038209", "39038211"),
             ("39038208", "39038207"), ("39038209", "39038207"), ("74001401", "74001405")]:
    print(f"{a} touches {b}: {outline[a].distance(outline[b]) == 0}")
for name in ("liquefaction", "landslide"):
    layer = [(f["properties"], shape(f["geometry"]).buffer(0))
             for f in json.load(open(f"data/raw/layer_{name}.geojson"))["features"]]
    for apn in ("27628243", "39038209", "39038211", "74001401"):
        site = outline[apn]
        hits = [(p.get("QUAD_NAME"), p.get("RELEASED"), round(100 * g.intersection(site).area / site.area))
                for p, g in layer if g.intersects(site)]
        print(f"{name} {apn}: {hits or 'no overlap'}")
```

Note: `data/raw/layer_liquefaction.geojson` and `layer_landslide.geojson` were downloaded by
`pipeline/fetch_layers.py` today. The pipeline change that adds them to `sites.geojson` was uncommitted when
this was written, so the liquefaction and landslide lines come from `extras.py`, not from the site records.
