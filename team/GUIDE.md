# Team guide: Open Ground (share this)

**What we're building:** one tool, two modes, same map and data.
- 🏗️ **Builder mode** (the hero): a nonprofit acquisitions lead gets ranked sites in Santa Ana, the law that
  opens each one (yes / no / unknown + why), hazards, who lives nearby, and the **gap per home**.
- 🏠 **Homeowner mode** (one screen): can I add a backyard home, and does it pay back?

**Lane:** 1 Find it (we also cover Fund it). **Real user:** an acquisitions lead at a small housing
nonprofit with no GIS team (scenario F02: "Give me ten sites I should call this month, and why").

## Timeline (submissions due 2:30, no exceptions)

| Time | Everyone |
|---|---|
| **11:10–11:25** | Setup: clone the team repo, unzip this folder on top, `pip install -r requirements.txt`, `pytest -q`, `streamlit run app/Home.py`. It must run before anyone writes code |
| 11:25–12:30 | Build block 1 (your task file) |
| **12:30** | Checkpoint 1 (10 min): pull, run the app together, ChatGPT reviews each person's diff |
| 12:40–1:30 | Build block 2. Eat at your desk |
| **1:30** | Checkpoint 2: deploy (C). **Kill switch:** if Homeowner mode isn't working, swap it for a "Coming next" panel |
| **1:45** | **Feature freeze.** Fixes only |
| 1:45–2:10 | README sources table (A) · demo video (B) · submission form draft (C) |
| **2:15** | Submit. Check the repo while signed out. Then rehearse the 3:00 live demo |

## Who owns what (only edit your own files: no merge fights)

| Builder | Role | Owns |
|---|---|---|
| **A** | Data & Rules | `pipeline/*`, `app/core/contracts.py`, `pathways.py`, `area.py`, `data/processed/sites.geojson`, `tracts.json`, `data/sources.json` |
| **B** | Builder mode | `app/pages/1_Builder_Mode.py`, `app/core/ui.py`, demo video |
| **C** | Money + Homeowner + Ship | `app/core/finance.py`, `app/pages/2_Homeowner_Mode.py`, `app/Home.py`, `data/processed/{income_limits_2026,rates,programs,assumptions}.json`, `README.md`, deploy, submission |

Need a change in someone else's file? Ask in chat; they make it. `tests/` is shared: add, don't delete.

## Git rules
1. `git pull --rebase` before every push. Small commits, clear messages.
2. Before pushing: `pytest -q` passes **and** the app opens. Never break `main`.
3. No keys (`.env` is ignored). No personal info, ever. No invented numbers: mark them `ASSUMPTION` in `data/processed/assumptions.json`.

## Our tools
- **Claude Pro (each builder):** run Claude Code in the repo. It reads `CLAUDE.md` (event rules) + `team/CLAUDE-TEAM.md` (our rules).
  **Hit the usage limit? Switch Claude Code to your $100 API credits immediately** (log in with your Console account). Don't wait it out.
- **4th Pro plan:** its owner uses it. Don't share logins.
- **API credits ($100 each):** Claude Code fallback first. The deployed app uses **no** key.
- **ChatGPT = reviewer only.** At checkpoints, paste `git diff` + `team/REVIEW-PROMPT.md`. It never edits the repo.

## Judges score (25% each, ties go to Impact)
Impact (would a nonprofit use it next month?) · Works (live, real data, sources on screen) ·
Scale (path to the next 100 projects) · Innovation. **Rough and working beats polished. Slides alone do not place.**
