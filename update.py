#!/usr/bin/env python3
"""Merge Fiscal.ai closes (output of fetch.js saved as JSON) into prices.json.
Usage: python3 update.py fetched.json   -> writes prices.json, or exits 1 without writing if data is incomplete."""
import json, sys, datetime, collections
HOLD = ["AMZN","BKNG","DUOL","GRAB","MA","MCD","MELI","MSFT","NFLX","SPGI","SE","SPOT","V"]
WATCH = ["META","GOOG","NVO","O","VICI","CEG","GEV","VST","ZTS","HIMS"]  # watch list + sold positions (ex-passengers)
BASE = "2026-04-30"  # history kept from 1 May 2026
inp = json.load(open(sys.argv[1]))
try: out = json.load(open("prices.json"))
except FileNotFoundError: out = {"source": "Fiscal.ai", "hist": {}}
from zoneinfo import ZoneInfo
fetched = datetime.datetime.fromisoformat((inp.get("fetched") or datetime.datetime.utcnow().isoformat() + "Z").replace("Z", "+00:00"))
ny = fetched.astimezone(ZoneInfo("America/New_York"))
ny_day, ny_min = ny.date().isoformat(), ny.hour * 60 + ny.minute
series = collections.defaultdict(dict)
for t, d, c in inp["rows"]:
    if c is None: continue
    if d == ny_day and ny_min < 9 * 60 + 35: continue  # pre-market rows are not prices of the session
    series[t][d] = float(c)
missing = [t for t in HOLD + ["SPY"] if len(series[t]) < 2]
if missing:
    print("INCOMPLETE, not written. Missing:", missing); sys.exit(1)
px = {}
for t in HOLD + WATCH:
    s = sorted(series[t].items())
    if len(s) >= 2: px[t] = [s[-1][1], s[-2][1], s[-1][0]]
last_dates = collections.Counter(px[t][2] for t in HOLD)
as_of = last_dates.most_common(1)[0][0]
stale = [t for t in HOLD if px[t][2] != as_of]
hist = out.get("hist", {})
# keep only complete days (every holding + SPY), up to the latest holdings close, so partial/pre-market rows never enter the chart
days = set.intersection(*[set(series[t]) for t in HOLD + ["SPY"]])
for d in sorted(days):
    if BASE < d <= as_of: hist[d] = {t: series[t][d] for t in HOLD + ["SPY"]}
intraday = as_of == ny_day and ny_min < 16 * 60 + 20
out.update({"source": "Fiscal.ai", "asOf": as_of, "intraday": intraday, "updated": inp.get("fetched") or datetime.datetime.utcnow().isoformat() + "Z", "px": px, "stale": stale, "hist": dict(sorted(hist.items()))})
json.dump(out, open("prices.json", "w"), separators=(",", ":"))
print("OK asOf", as_of, "intraday", intraday, "tickers", len(px), "stale", stale, "hist days", len(hist))
