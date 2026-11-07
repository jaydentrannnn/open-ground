# Demo video, live demo and submission form (drafts)

Updated 2026-11-07 for the top-bar / pop-up design. Numbers below were read from the app with its defaults
(demo family: $90,000, 4 people, 3 bedrooms, 7.18% rate). **Re-check them after the last feature lands.**
Homeowner beats are placeholders until the zip code + goal panel work is merged.

## 1. Demo video (93 s, v3, recorded 2026-11-07 2:14 PM on the live URL)

File: `open-ground-demo-v3.mp4` (1920x1200, H.264 + AAC). Made with Claude: Claude wrote the script, drove the live app
with Playwright (Chrome screencast, fake cursor, captions, feature chips, title cards), voiced it with Microsoft's
"Emma" neural text-to-speech voice (edge-tts, 14% faster) and synthesized the music bed in code (no third-party
music), which plays throughout about 11 dB under the voice. ffmpeg joined picture, voice and music. The submission page asks for "one user, one problem, the tool working,
the result": the real user and their problem open Part 1; the voice also covers the result (a call list with the facts
behind it), sources and ASSUMPTION labels, and the path to the next county (Scale). Up to 2 minutes is
allowed; 30 s is "ideal". The MP4 is not in the repo: upload it with the form.

| # | Screen | Caption / voice |
|---|---|---|
| T1 | Title card "Part 1 · A nonprofit builder" | "Part one: a nonprofit builder." |
| 1 | Builder, top of page (chip: the problem) | "Meet the land lead at a small Orange County housing nonprofit, with no mapping team. Today, they find land by luck, one site at a time, across a dozen websites." |
| 2 | Filter row; type 098-120-39 in the shortlist search | "Open Ground ranks over two thousand real sites from city housing plans and surplus public land. Filter by city, law, or flood and fire risk, or search any parcel." |
| 3 | The three "Call first" tiles; open card #1 | "It names three different sites to call first, and says why." |
| 4 | Card #1 (Garden Grove APN 098-120-39): SCAG parcel outline, law list | "Each site card shows the real parcel, and a yes, no, or unknown for every state housing law. Unknown never counts as a pass." |
| 5 | "Hazards" tab | "Hazards: flood and fire maps, checked for every parcel." |
| 6 | "Who it helps" tab (Area Benefit Score 64 / 100, 4 lower-income homes planned) | "Who it helps: an area benefit score from Census data, and the homes the city planned here." |
| 7 | "Does it pencil?" tab ($153,751 statutory price, $226,249 gap / home on ASSUMPTION costs) | "Does it pencil? From this year's state income limits and this week's mortgage rate, it shows what a family can pay, and the gap per home. Placeholder costs are labeled assumption." |
| 8 | "One-pager" tab | "Then one click drafts a sourced one-pager for a congregation or a funder. Instead of luck, they start the week with a call list and the facts behind it." |
| T2 | Title card "Part 2 · A homeowner" | "Part two: a homeowner." |
| 9 | Homeowner: type ZIP 92840; rent becomes the Census median ($1,611 ± $112, 1BR) | "Can a backyard home pay for itself? Type a ZIP code, and the rent comes from the Census median for that area." |
| 10 | Pick 2 bedrooms: rent becomes the 2BR Census median ($2,099 ± $110); metrics update | "Switch to two bedrooms, and the cost, rent and cash flow all update." |
| 11 | Years to earn back your cash; "Help that might apply" table | "It shows the years to earn your cash back, and the help that might apply, each with its status checked today." |
| End | End card: who it is for, the real data sources, "every number sourced, every guess labeled ASSUMPTION", next county = re-run the pipeline, disclaimer, repo | "Every number shows its source. The laws are statewide and most data is regional, so a new county is mostly a re-run of the pipeline. Built with Claude. A prototype, not legal or financial advice." |

Do not say a number in the voice that the screen doesn't show. The gap uses the event's SYNTHETIC cost lines: the
screen labels it ASSUMPTION, so the voice says "placeholder costs".

## 2. Live demo for finalists (plan 3 minutes; the length is not stated in docs/judging.md, ask an organizer)

Open the live URL before you start and open card #1 once, so the parcel outlines are cached.

| Time | Do | Say (the facts on screen) |
|---|---|---|
| 0:00 | Builder, top | Real user: an acquisitions lead at a small nonprofit with no GIS team (scenario F02: "ten sites I should call this month, and why"). |
| 0:20 | Point at the filter row and the 3 tiles | 2,020 of 2,235 real OC sites (SCAG housing-element lists + HCD surplus land). Three different calls: nearby listed parcels fold into one call (100 m, ASSUMPTION). |
| 0:45 | Open card #1 | Why call: clear of flood and fire maps, near frequent transit, the city planned 4 lower-income homes here. Unknown: owner. The real parcel outline (SCAG) on the right. |
| 1:10 | "Can we build?" tab | SB 4 Maybe (5 pass, 4 unknown), SB 684/1123 Maybe, SB 9 No, AB 2011 No. Unknown is never a pass; every test cites the HCD fact sheet page. |
| 1:35 | "Does it pencil?" tab | Statutory price $153,751 (HSC 50052.5(b), HCD 2026 limits) vs a 30%-of-income budget $221,037. Gap $226,249 per home, on the event's synthetic costs (ASSUMPTION): type a real deal and it updates everywhere. |
| 2:05 | Close the card, open "Family & loan", change the rate | The price and gap move with this week's Freddie Mac rate. |
| 2:20 | Card #1, "One-pager" tab | A sourced one-pager for a congregation or a funder. Draft only, never sent. |
| 2:35 | Homeowner tab, type ZIP 92840 | Same engine for a homeowner's backyard home. The rent default becomes the Census ACS 2024 median for ZIP area 92840 (1BR $1,611 ± $112): cash flow $531 / mo, cash back in 7.8 years at 7.18%, on a $150,000 ASSUMPTION build cost. |
| 2:50 | Close | Honest gaps: 7 cities missing from SCAG's layer, owner unknown, costs synthetic. Spot-audit: 47 of 47 values matched live sources. |

## 3. Submission form (claudesocal.com/uci-impact-lab#submit). Jayden reviews, pastes and submits by 2:15

- **Team name:** Open Ground
- **Your email:** the one on the team registration (Jayden fills).
- **Lane:** 1 Find it (we also cover 3 Fund it).
- **One-liner:** Open Ground shows a small Orange County housing nonprofit which sites to call first, whether the law
  lets them build there, who it would help, and the funding gap per home, with every source on screen.
- **The real user, before and after:** An acquisitions lead at a small housing nonprofit with no GIS team. Before:
  they find land by luck, word of mouth and spreadsheets, checking one site at a time across a dozen county, state and
  federal websites. After: a ranked shortlist of 2,235 real OC sites with the three to call first, the law that opens
  each one (yes / no / unknown and why, with the fact-sheet page), hazards, who lives nearby, and the gap per home at
  this week's mortgage rate, plus a one-pager to send a congregation or a funder.
- **What it does:** One Streamlit app with two modes. Builder mode ranks real housing-element and surplus-land sites by
  readiness (flood, fire, transit, the city's plan, size, land lead, vacant today), opens a site card with the real
  parcel outline, a law check for SB 4, SB 9, SB 684/1123 and AB 2011, hazards, an Area Benefit Score, and the gap per
  home from the HSC 50052.5(b) statutory price. Homeowner mode estimates whether a backyard home (ADU) pays back; an optional ZIP code sets the rent from the Census
  median for that ZIP area.
  Unknown is shown as unknown; every made-up number is labelled ASSUMPTION. Prototype, not legal or financial advice.
- **Sources and assumptions:** see the README's "Sources and assumptions" (every row has a URL, the date checked and
  VERIFIED / UNVERIFIED / ASSUMPTION). Short version:
  - Laws: HSC 50052.5(b) and (h); 25 CCR 6920; SB 4 (Gov Code 65913.16); SB 9; SB 684 / SB 1123; AB 2011 (HCD fact
    sheets, April 2026).
  - Data: SCAG housing-element sites, zoning and 2024 land use; HCD Surplus Land Act notices; FEMA / OC flood zones;
    CAL FIRE fire hazard zones; CGS Alquist-Priolo fault zones; Caltrans High-Quality Transit Areas; ACS 2024 5-year (tracts, and median rent by ZIP area, B25031);
    LODES 2024; TCAC/HCD 2026 Opportunity Map; HCD 2026 State Income Limits (June 23 memo); Freddie Mac PMMS;
    OpenStreetMap places of worship.
  - Programs (status checked today): CalHome, CalHFA MyHome Assistance, CalHFA Dream For All, CalHFA ADU Grant, city
    housing funds.
  - Assumptions: household 4, income $90,000, 3 bedrooms, 30% budget share, 30-year loan, property tax 1.1%,
    insurance $150, maintenance $150, utilities $250, HOA / loan insurance / space rent $0, the event's synthetic cost
    lines and subsidies, max 9 homes per site, 1% edge sliver, 100 m same call, 150 homes/acre density watch,
    existing-house cutoff 2 homes, Area Benefit Score weights, ADU $250/sq ft, 1BR rent $2,598 when no ZIP is given, vacancy and upkeep 25%,
    owner cash $50,000, below-market rate toggle 3.0%.
- **Public repo URL:** https://github.com/jaydentrannnn/open-ground
- **Video:** upload `open-ground-demo-v3.mp4` (93 s; see section 1).
- **Live demo URL:** https://open-ground-sqjmqchnp8w8kc5vegpm8k.streamlit.app/
- **Company website:** leave blank (the form shows this field; we have none).

## 4. Before you submit (from docs/submission.md)

- [ ] Repo public; opens in a private window, signed out.
- [ ] Everything pushed to `main`; `pytest -q` passes; the live app loads signed out.
- [ ] No keys or personal information in the repo or its history (scan with Claude).
- [ ] README: who, what, Try it, real vs mocked, sources, Members, Demo video line.
- [ ] Video uploaded, or its link opens signed out.
