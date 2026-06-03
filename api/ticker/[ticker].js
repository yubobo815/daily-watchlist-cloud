const {
  encodeFilterValue,
  isValidTicker,
  normalizeTicker,
  runInfo,
  supabaseSelect,
} = require("../_supabase");
const { fetchCompanyProfile } = require("../company");

module.exports = async function handler(request, response) {
  const ticker = normalizeTicker(request.query?.ticker);
  if (!isValidTicker(ticker)) {
    response.status(400).json({ error: "Invalid ticker." });
    return;
  }

  try {
    const runRows = await supabaseSelect(`watchlist_behavior_history?select=run_date&ticker=eq.${encodeFilterValue(ticker)}&order=run_date.desc&limit=1`);
    const latest = runRows[0]?.run_date;
    if (!latest) {
      response.status(404).json({ error: `No 30-day history found for ${ticker}.` });
      return;
    }

    const [snapshotRows, historyRows, latestRunInfo, profile] = await Promise.all([
      supabaseSelect(`watchlist_snapshots?select=*&ticker=eq.${encodeFilterValue(ticker)}&run_date=eq.${encodeFilterValue(latest)}&limit=1`),
      supabaseSelect(`watchlist_behavior_history?select=*&ticker=eq.${encodeFilterValue(ticker)}&run_date=eq.${encodeFilterValue(latest)}&order=history_date.desc`),
      runInfo(latest),
      fetchCompanyProfile(ticker).catch(() => ({})),
    ]);

    response.setHeader("Cache-Control", "public, s-maxage=90, stale-while-revalidate=300");
    response.status(200).json({
      ticker,
      latest,
      snapshot: snapshotRows[0] || null,
      historyRows,
      runInfo: latestRunInfo,
      profile,
    });
  } catch (error) {
    response.status(502).json({ error: error.message || "Ticker detail unavailable." });
  }
};
