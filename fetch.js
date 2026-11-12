async () => {
  // Captain Pedro site: daily closes from Fiscal.ai (last ~6 calendar days) for holdings, watch list and SPY.
  const keys = ["NASDAQ_AMZN","NASDAQ_BKNG","NASDAQ_DUOL","NASDAQ_GRAB","NYSE_MA","NYSE_MCD","NASDAQ_MELI","NASDAQ_MSFT","NASDAQ_NFLX","NYSE_SPGI","NYSE_SE","NYSE_SPOT","NYSE_V","NASDAQ_META","NASDAQ_GOOG","NYSE_NVO","NYSE_O","NYSE_VICI","NASDAQ_CEG","NYSE_GEV","NYSE_VST","NYSE_ZTS"];
  const since = new Date(Date.now() - 6 * 864e5).toISOString().slice(0, 10);
  const rows = [];
  for (let i = 0; i < keys.length; i += 6) {
    const res = await Promise.all(keys.slice(i, i + 6).map(k => codemode.company_stock_prices({ companyKey: k, startDate: since }).catch(() => null)));
    res.forEach((r, j) => { if (!r) return; const t = keys[i + j].split("_")[1]; r.prices.filter(p => p.date >= since && p.volume > 1000).forEach(p => rows.push([t, p.date, p.closePrice])); });
  }
  const spy = await codemode.fund_prices({ ticker: "SPY", startDate: since }).catch(() => null);
  if (spy) spy.prices.filter(p => p.date >= since).forEach(p => rows.push(["SPY", p.date, p.closePrice]));
  console.log(JSON.stringify({ fetched: new Date().toISOString(), rows }));
}
