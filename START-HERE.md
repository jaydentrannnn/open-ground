# Start here (one person, 10 minutes)

1. On GitHub, open the starter repo `travcjohnson/claude-impact-lab-uci` → **Use this template** → create a
   **public** repo named `open-ground` under one teammate's account. Settings → Collaborators → add the other two builders.
2. Clone it: `git clone https://github.com/<you>/<repo>` and `cd <repo>`.
3. Unzip this folder **on top of** the repo root (say yes to replacing `README.md` and `CLAUDE.md`).
   Then add the lines from `.gitignore.team` to `.gitignore` and delete `.gitignore.team`.
4. Check it runs:
   ```bash
   python -m pip install -r requirements.txt
   python -m pytest -q          # expect 11 passed
   streamlit run app/Home.py    # opens in the browser
   ```
5. `git add -A && git commit -m "Open Ground scaffold" && git push`
6. The other two builders clone it. Everyone reads `team/GUIDE.md`, then your own task file in `team/`.
