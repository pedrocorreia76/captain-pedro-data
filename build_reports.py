#!/usr/bin/env python3
"""Rebuild reports.json (the website's research table) from the project's report data.

Usage: python3 build_reports.py <Valuation_Params.json or compact latest.json> <Report_Links.json>
  The compact form is {"TICKER": {"date": ..., "rating": "<exact rating string>", "bear": x, "base": y, "bull": z}}
  holding only the LAST history entry of each ticker, copied exactly.
  - Valuation_Params.json and Report_Links.json are read from the claude.ai Project "Peter Lynch"
    (project_read) and saved OUTSIDE this repo; they are never committed.
  - For every ticker with a report link: the latest entry of its Valuation_Params history gives the
    rating, conviction, provisional flag, bear/base/bull values and the report date.
  - Tickers with a link but no Valuation_Params entry keep their previous row in reports.json.
  - Holdings = tickers in holdings.json "units"; every other ticker goes to "watch".
Writes reports.json only if every row is complete; prints a summary of what changed.
"""
import json, re, sys

vp = json.load(open(sys.argv[1]))
links = json.load(open(sys.argv[2]))["links"]
holdings = set(json.load(open("holdings.json"))["units"])
old = json.load(open("reports.json"))
old_rows = {r["t"]: r for r in old.get("reports", []) + old.get("watch", [])}

NAMES = {"AMZN": "Amazon", "BKNG": "Booking Holdings", "DUOL": "Duolingo", "GRAB": "Grab Holdings", "MA": "Mastercard",
         "MCD": "McDonald's", "MELI": "MercadoLibre", "MSFT": "Microsoft", "NFLX": "Netflix", "SPGI": "S&P Global",
         "SE": "Sea Limited", "SPOT": "Spotify", "V": "Visa", "DLO": "dLocal"}
CURRENCY = {"ASML": "EUR"}  # report values in euros (Euronext price)


def latest(entry):
    """Full Valuation_Params entry -> last history item; compact entry {date, rating, bear, base, bull} -> itself."""
    if "history" in entry:
        hist = entry.get("history") or []
        return hist[-1] if hist else None
    return entry if "rating" in entry else None


def parse_rating(s):
    s = str(s or "")
    m = re.search(r"\b(BUY|HOLD|SELL)\b", s)
    rating = m.group(1) if m else None
    prov = bool(re.search(r"provisional", s, re.I)) and not re.search(r"no longer provisional|provisional status removed", s, re.I)
    conv = ""
    for c in ["Low-Medium", "Medium-High", "Moderate-High", "Low", "Medium", "Moderate", "High"]:
        if re.search(r"\b" + c + r"\b", s, re.I):
            conv = c
            break
    return rating, conv, prov


rows, problems, changes = {}, [], []
for t, url in links.items():
    e = vp.get(t)
    h = latest(e) if isinstance(e, dict) else None
    row = None
    if h:
        vals = h.get("values") or {k: h.get(k) for k in ("bear", "base", "bull")}
        rating, conv, prov = parse_rating(h.get("rating"))
        try:
            bear, base, bull = (round(float(vals[k]), 2) for k in ("bear", "base", "bull"))
        except (TypeError, KeyError, ValueError):
            bear = base = bull = None
        date = str(h.get("date", ""))[:10]
        if rating and None not in (bear, base, bull) and re.match(r"\d{4}-\d{2}-\d{2}$", date):
            row = {"t": t, "rating": rating, "conviction": conv, "provisional": prov,
                   "bear": bear, "base": base, "bull": bull, "updated": date}
        else:
            problems.append(f"{t}: latest Valuation_Params entry incomplete ({h.get('date')})")
    if row is None and t in old_rows:
        o = old_rows[t]
        row = {k: o[k] for k in ("t", "rating", "conviction", "provisional", "bear", "base", "bull", "updated")}
    if row is None:
        problems.append(f"{t}: no data in Valuation_Params and no previous row")
        continue
    row["n"] = NAMES.get(t) or (old_rows.get(t) or {}).get("n") or t
    row["url"] = url
    row["currency"] = CURRENCY.get(t, (old_rows.get(t) or {}).get("currency", "USD"))
    prev = old_rows.get(t)
    if not prev:
        changes.append(f"{t}: NEW {row['rating']} {row['bear']}/{row['base']}/{row['bull']} ({row['updated']})")
    elif any(prev.get(k) != row.get(k) for k in ("rating", "conviction", "provisional", "bear", "base", "bull", "updated", "url")):
        changes.append(f"{t}: {prev.get('rating')} {prev.get('bear')}/{prev.get('base')}/{prev.get('bull')} ({prev.get('updated')}) -> "
                       f"{row['rating']} {row['bear']}/{row['base']}/{row['bull']} ({row['updated']})")
    rows[t] = row

missing_holdings = sorted(holdings - set(rows))
if missing_holdings:
    problems.append("holdings without a report link: " + ", ".join(missing_holdings))

order = lambda r: r["t"]
out = {"note": old.get("note", ""),
       "asOf": max(r["updated"] for r in rows.values()),
       "reports": sorted([r for t, r in rows.items() if t in holdings], key=order),
       "watch": sorted([r for t, r in rows.items() if t not in holdings], key=order)}
json.dump(out, open("reports.json", "w"), indent=1, ensure_ascii=False)
print(f"OK reports {len(out['reports'])} watch {len(out['watch'])}")
for c in changes:
    print("CHANGED", c)
for p in problems:
    print("PROBLEM", p)
