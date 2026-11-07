# Builder B: Builder mode (the demo the judges see)

**Goal:** an acquisitions lead opens Builder mode and in 30 seconds knows the three sites to call, why, and the gap.
The page already runs on SYNTHETIC samples. Make it clear, fast and honest. Real data from A drops in automatically.

## Tasks (in order, with deadlines)
1. **By 11:45:** run it, click through every tab, and list what's confusing. Fix layout first: shortlist on the
   left, map on the right? Big "call these 3 first" box at the top?
2. **By 12:30: Site Card v2.** One screen answering: *Can we build? (law) · Is it safe? (hazards) · Who does it help? (area) · Does it pencil? (gap)*.
   Every number shows its source line or an ASSUMPTION tag (`ui.source_line`, `ui.assumption`).
3. **By 1:15: ranking that means something.** Let the user sort by "homes per $1M of gap" vs "area benefit".
   Show *why* a site ranks high in one sentence.
4. **By 1:30: one-pager export.** A clean one-page markdown to send to a congregation or a funder. Stretch: print-friendly HTML.
5. **1:45–2:05: record the demo video** (script in `team/DEMO-SCRIPT.md`, 30–60 sec, screen recording + voice).

## Claude Code starter prompt
> Read CLAUDE.md, team/CLAUDE-TEAM.md and app/pages/1_Builder_Mode.py. I'm Builder B. Only edit
> app/pages/1_Builder_Mode.py and app/core/ui.py. Make the page answer, for an acquisitions lead: which 3 sites
> to call first and why. Keep every number sourced or labelled ASSUMPTION. Run the app and pytest -q after each change.

## Watch out
- Never show a SYNTHETIC site as real. The red banner stays until A's data lands.
- "Unknown" is a feature: judges reward honesty. Don't hide it, style it.
- The map must still work if `lat` is missing. Test with A's real file at 12:30.
