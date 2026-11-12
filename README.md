# captain-pedro-data
Daily closing prices (from Fiscal.ai) for Captain Pedro's portfolio site. Updated automatically every weekday evening.
`prices.json` contains only public market prices — no holdings, amounts or weights.

## Website
`site/index.html` is the Captain Pedro's Portfolio Tower website (https://captain-pedro.netlify.app). Netlify deploys it from this repo (see `netlify.toml`); commits that only touch the JSON data files don't trigger a deploy.
`reports.json` holds the rating and bear/base/bull values per holding shown in the "Pilot's logbook" section.
