# ChatGPT review prompt (paste with your `git diff`)

Get the diff: `git diff origin/main -- <your files>` (or `git show HEAD~3..HEAD`).

---
You are reviewing a hackathon pull request for a Streamlit app that helps a housing nonprofit find
land and size the funding gap per home. Be brief and concrete. Do NOT rewrite the code. Report only:

1. **Bugs:** anything that would crash or give a wrong number (show the line and a failing input).
2. **Invented facts:** any statute section, dollar amount, fee, rate, address or parcel fact that is
   not read from a data file or labelled ASSUMPTION.
3. **Math:** check the formulas (mortgage payment, loan from payment, gap = cost − sources).
4. **Honesty:** places where "unknown" or SYNTHETIC data could be shown as real.
5. **Secrets / personal info:** any key, token, email, phone number or person's name.

Rank by severity. Max 8 items. If it looks fine, say "ship it".
---

Then paste your diff below. Fix only what matters before 1:45.
