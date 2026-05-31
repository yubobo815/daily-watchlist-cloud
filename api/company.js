const YAHOO_MODULES = [
  "assetProfile",
  "calendarEvents",
  "financialData",
  "incomeStatementHistoryQuarterly",
].join(",");

function yahooValue(value, key = "fmt") {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value[key] ?? value.raw ?? "";
  }
  return value ?? "";
}

function compactText(value) {
  const clean = yahooValue(value);
  return clean === null || clean === undefined ? "" : String(clean);
}

function yahooHeaders() {
  return {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://finance.yahoo.com/",
  };
}

async function fetchYahooSummary(ticker) {
  const base = `https://query2.finance.yahoo.com/v10/finance/quoteSummary/${encodeURIComponent(ticker)}`;
  const query = `modules=${encodeURIComponent(YAHOO_MODULES)}`;
  const direct = await fetch(`${base}?${query}`, { headers: yahooHeaders() });
  if (direct.ok) return direct.json();

  const crumbResponse = await fetch("https://query2.finance.yahoo.com/v1/test/getcrumb", {
    headers: yahooHeaders(),
  });
  if (!crumbResponse.ok) throw new Error("Yahoo crumb unavailable");
  const crumb = (await crumbResponse.text()).trim();
  const crumbQuery = `${query}&formatted=true&lang=en-US&region=US&corsDomain=finance.yahoo.com&crumb=${encodeURIComponent(crumb)}`;
  const retry = await fetch(`${base}?${crumbQuery}`, { headers: yahooHeaders() });
  if (!retry.ok) throw new Error(`Yahoo profile returned HTTP ${retry.status}`);
  return retry.json();
}

function toProfile(ticker, payload) {
  const result = payload?.quoteSummary?.result?.[0] || {};
  const asset = result.assetProfile || {};
  const calendar = result.calendarEvents || {};
  const financial = result.financialData || {};
  const latestQuarter = result.incomeStatementHistoryQuarterly?.incomeStatementHistory?.[0] || {};
  const nextReport = compactText(calendar.earnings?.earningsDate?.[0]);
  const highlights = [
    compactText(latestQuarter.totalRevenue) && `latest quarterly revenue ${compactText(latestQuarter.totalRevenue)}`,
    compactText(latestQuarter.netIncome) && `net income ${compactText(latestQuarter.netIncome)}`,
    compactText(financial.revenueGrowth) && `revenue growth ${compactText(financial.revenueGrowth)}`,
    compactText(financial.earningsGrowth) && `earnings growth ${compactText(financial.earningsGrowth)}`,
  ].filter(Boolean);

  return {
    ticker,
    business_summary: asset.longBusinessSummary || "",
    website: asset.website || "",
    sector: asset.sector || "",
    industry: asset.industry || "",
    latest_report_highlights: highlights.join("; "),
    next_report_date: nextReport,
    profile_source: "Yahoo Finance",
  };
}

module.exports = async function handler(req, res) {
  const rawTicker = String(req.query?.ticker || "").trim().toUpperCase();
  const ticker = rawTicker.replace("BRK.B", "BRK-B");
  if (!/^[A-Z0-9.^-]{1,12}$/.test(ticker)) {
    res.status(400).json({ error: "Invalid ticker" });
    return;
  }

  try {
    const payload = await fetchYahooSummary(ticker);
    res.setHeader("Cache-Control", "s-maxage=21600, stale-while-revalidate=86400");
    res.status(200).json(toProfile(rawTicker, payload));
  } catch (error) {
    res.status(502).json({ error: error.message || "Yahoo profile unavailable" });
  }
};
