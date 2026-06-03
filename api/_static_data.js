const latestData = require("../data/latest.json");
const historyData = require("../data/history.json");

function normalizeTicker(value) {
  return String(value || "").trim().toUpperCase().replace("BRK.B", "BRK-B");
}

function staticLatestPayload() {
  const rows = Array.isArray(latestData.rows) ? latestData.rows : [];
  return {
    latest: latestData.run_date || rows[0]?.run_date || "",
    previous: "",
    rows,
    previousRows: [],
    runInfo: {
      run_date: latestData.run_date || rows[0]?.run_date || "",
      status: "static_fallback",
      live_access_ok: false,
      live_access_message: "Using bundled published data because the live database is unavailable.",
      symbols_total: rows.length,
      symbols_analyzed: rows.length,
      symbols_failed: 0,
      symbols_stale_cache: 0,
      snapshot_rows: rows.length,
      history_rows: Array.isArray(historyData.rows) ? historyData.rows.length : 0,
      scanner_version: "static-fallback",
      notes: "Static fallback served by Vercel API.",
      payload: {
        failed_symbols: [],
        stale_cache_fallbacks: [],
      },
    },
  };
}

function staticTickerPayload(ticker, profile = {}) {
  const normalized = normalizeTicker(ticker);
  const rows = Array.isArray(latestData.rows) ? latestData.rows : [];
  const snapshot = rows.find((row) => normalizeTicker(row.ticker) === normalized) || null;
  const historyRows = Array.isArray(historyData.by_ticker?.[normalized])
    ? historyData.by_ticker[normalized]
    : (Array.isArray(historyData.rows) ? historyData.rows.filter((row) => normalizeTicker(row.ticker) === normalized) : []);
  const latest = snapshot?.run_date || historyRows[0]?.run_date || latestData.run_date || "";

  return {
    ticker: normalized,
    latest,
    snapshot,
    historyRows: [...historyRows].sort((a, b) => String(b.history_date || b.data_date || b.date || "").localeCompare(String(a.history_date || a.data_date || a.date || ""))),
    runInfo: {
      run_date: latest,
      status: "static_fallback",
      live_access_ok: false,
      live_access_message: "Using bundled published data because the live database is unavailable.",
      scanner_version: "static-fallback",
      payload: {
        failed_symbols: [],
        stale_cache_fallbacks: [],
      },
    },
    profile,
  };
}

module.exports = {
  staticLatestPayload,
  staticTickerPayload,
};
