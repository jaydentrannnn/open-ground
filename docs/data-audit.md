# Data spot-audit (2026-11-07, about 1:25 PM)

> Prototype. Not legal, financial or lending advice. A sample of 8 sites is a spot check, not proof that every
> site is right.

**Question:** does what Builder mode shows match our data, and does our data match the original public sources?

## 1. App vs our data

We ran Builder mode with its defaults and compared the three "call these first" tiles with
`data/processed/sites.geojson` and `tracts.json`.

| Tile | App says | Our data | Match |
|---|---|---|---|
| Garden Grove APN 098-120-39 | 4 lower-income homes, clear of flood and fire, area score 64 | Low-income capacity 4, flood no, fire no, score 64 | Yes |
| Garden Grove APN 099-173-10 | 25 lower-income homes, clear, 64 → 63 | 25, no, no, 63 | Yes |
| Garden Grove APN 096-281-13 | 14 lower-income homes, clear, 60 | 14, no, no, 60 | Yes |
| "Also listed nearby" distances | 19 m, 67 m, 45 m, 36 m | 19, 67, 46, 36 m | Yes (1 m rounding) |

The app shows **2,020** of the 2,235 sites by default. The other 215 are hidden by the sidebar filter "Hide existing
houses where the city plans few homes".

## 2. Our data vs the original sources (live re-query)

`pipeline/audit_sample.py` re-asks each source live, with no cache. Sample: the 3 tiles, 2 random sites (seed 7),
one flood-flagged site, one fire-flagged site and one surplus parcel. Two checks use sources we did **not** build
from, so they are independent: FEMA's National Flood Hazard Layer (the authority; we use the county's copy) and the
Census geocoder (we take the tract from SCAG).

| Check | Upstream source | Values matched |
|---|---|---|
| City capacity (total and lower-income) | SCAG housing-element sites | 7 / 7 (the surplus parcel has none) |
| Zoning (SCAG code and city code) | SCAG zoning | 8 / 8 |
| Existing land use | SCAG existing land use | 8 / 8 |
| In a special flood hazard area | **FEMA NFHL** (independent), at the site's point | 8 / 8 (incl. the Zone A site) |
| In a Very High fire zone | CAL FIRE LRA map dated 2025-03-24, at the site's point | 8 / 8 (incl. the Very High site) |
| Census tract | **Census geocoder** (independent) | 8 / 8 |
| **Total** | | **47 / 47** |

Limits: point checks test one spot in the parcel, while our build tests the whole outline. A parcel partly in a zone
can pass a point check. Everything above agrees.

## 3. What the sample shows about the data (for the user)

- The #1 call (Garden Grove 098-120-39) has a **single-family house** on it today (SCAG 2024 land use). The city
  counts 4 homes there; the owner would have to sell. Whether anyone lives there is unknown.
- Brea APN 320-071-18 is zoned R-1 with 19 homes of city capacity, but its existing use is **"Mineral Extraction -
  Oil and Gas"** and it sits in a Very High fire zone. An oil-field use is a contamination lead (a Phase I
  environmental assessment is required for SB 4 anyway). Our data does not check hazardous-waste sites yet.
- Garden Grove APN 100-074-23 is an SB 4 lead (SCAG: Religious Facilities) but sits in FEMA Zone A, so SB 4 says no.

Re-run: `python pipeline/audit_sample.py` (about 50 polite requests).
