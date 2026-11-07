# Team rules for Claude Code (imported by CLAUDE.md)

We are team Open Ground: 3 builders working in parallel for about 3 hours. The event rules in CLAUDE.md
always win. On top of them:

- **Stay in your lane's files.** Ownership table: `team/GUIDE.md`. Before editing a file you don't own,
  stop and tell the user to ask its owner.
- **The data contract is `app/core/contracts.py`.** Don't add, rename or retype a site field without
  the user confirming the team agreed. Unknown = `null`, never a guess.
- **Every number has a home.** Sourced numbers cite an id from `data/sources.json`. Made-up numbers live
  in `data/processed/assumptions.json` labelled ASSUMPTION, and the UI shows the tag.
- **SYNTHETIC stays SYNTHETIC.** Sample files are fake. Never present them as real, and never add a real
  person's name, phone, email or address.
- **Keep `main` runnable.** After each change run `pytest -q` and `streamlit run app/Home.py`. Add a test when you
  add a function in `app/core/`.
- **Small, boring code.** Pure functions in `app/core/`, UI in `app/pages/`. No new dependencies without
  pinning them in `requirements.txt`, and tell the team.
- **No runtime API keys in the deployed app.** If you use Claude API credits, run it offline and commit
  the output as JSON with its source and date.
- Stack: Python 3.11+, Streamlit 1.67, folium + streamlit-folium, pandas. Run from the repo root.
