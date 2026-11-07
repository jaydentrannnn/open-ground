# Builder A: Data & Rules (the "Find it" engine)

**Goal:** replace every SYNTHETIC sample with real, sourced Santa Ana data, and make the law checks honest.
Builder B is building on `sites.sample.geojson` right now. Your output drops in with **the same fields**
(see the docstring in `app/core/contracts.py`). Don't rename fields without telling B.

## Tasks (in order, with deadlines)
1. **By 11:50: first real sites on the map.**
   `cd pipeline && python fetch_sites.py "Santa Ana" && python build_sites.py --limit 40`
   → writes `data/processed/sites.geojson`. The app switches to it automatically. Push it.
   If the SCAG layer id isn't 0, open the MapServer URL in a browser and fix `fetch_sites.py`.
2. **By 12:30: who lives there.** `python fetch_area.py` → `tracts.json`. Then give each site a `tract_id`
   (Census geocoder by lat/lon, or point-in-polygon on tract shapes). Without `tract_id` the area score shows "unknown".
3. **By 1:00: law checks you can defend.** Read the HCD SB 4 and SB 9 fact sheets (links in `data/sources.json`).
   Tighten `app/core/pathways.py`: add tests the fact sheets name, keep anything you can't check as `unknown`.
   Confirm or delete the "10+ homes, prevailing wage" note. Add `SB684` (small-lot subdivisions, up to 10 homes) if time allows.
4. **By 1:30: the real test case.** Pick one **public** OC listing of a small lot or building (4–12 homes).
   Add it as a site with its listing URL in `source_ids` (add it to `sources.json`). Only property facts: no agent or owner names.
5. **Optional:** SB 4 lead layer (worship sites near parcels → `owner_type_proxy: "faith_proxy"`), surplus-notice join, zoning join.
6. **1:45–2:10:** fill the README **Sources and assumptions** table from `data/sources.json` + `assumptions.json`.

## Claude Code starter prompt
> Read CLAUDE.md, team/CLAUDE-TEAM.md and app/core/contracts.py. I'm Builder A. Run pipeline/fetch_sites.py for
> Santa Ana and fix it until it writes data/raw/he_sites.geojson. Then run build_sites.py --limit 40. Keep requests
> polite (cached, one per site per layer). Every field must match the contract; unknown = null. Run pytest -q after.

## Watch out
- Ownership isn't in free parcel data. A worship-site match is a **lead**, so it stays `unknown`.
- Housing-element lists go stale: the site may have sold or already been built.
- Keep `--limit` small. Don't hammer city servers (event rule).
