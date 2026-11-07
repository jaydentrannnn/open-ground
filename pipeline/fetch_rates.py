"""Freddie Mac PMMS history -> data/processed/rates.json.   OWNER: Builder C
Run: python pipeline/fetch_rates.py
Columns per event repo: date, pmms30, pmms15 ... (percent). Check the header if it fails.
"""
import csv
import io

from common import get, write_json

URL = "https://www.freddiemac.com/pmms/docs/PMMS_history.csv"
raw = get(URL, as_json=False).decode("utf-8-sig")
rows = list(csv.DictReader(io.StringIO(raw)))
print("columns:", list(rows[0].keys()))
series = []
for r in rows[-104:]:  # ~2 years of weekly points
    v = r.get("pmms30")
    if v:
        m, d, y = r["date"].split("/") if "/" in r["date"] else (None, None, None)
        date = f"{y}-{int(m):02d}-{int(d):02d}" if y else r["date"]
        series.append({"date": date, "rate_30yr": round(float(v) / 100, 5)})
write_json("rates.json", {"about": "Freddie Mac PMMS 30-yr, last ~2 years", "source_ids": ["pmms"], "series": series})
