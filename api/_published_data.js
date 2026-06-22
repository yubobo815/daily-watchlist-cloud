const { conservativeFallbackRow, normalizeTicker, staticLatestPayload, staticTickerPayload } = require("./_static_data");

const PUBLISHED_BASE_URL = "https://yubobo815.github.io/daily-watchlist-cloud/data";

async function fetchPublishedJson(name) {
  const response = await fetch(`${PUBLISHED_BASE_URL}/${name}?v=${Date.now()}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Published ${name} returned HTTP ${response.status}.`);
  }
  return response.json();
}

async function publishedLatestPayload() {
  try {
    const latestData = await fetchPublishedJson("latest.json");
    const rows = Array.isArray(latestData.rows) ? latestData.rows.map(conservativeFallbackRow) : [];
    const runInfo = latestData.runInfo && typeof latestData.runInfo === "object"
      ? latestData.runInfo
      : {
          run_date: latestData.run_date || rows[0]?.run_date || "",
          status: "published_fallback",
          live_access_ok: false,
          live_access_message: "Using published GitHub Pages data because the live database is unavailable.",
          symbols_total: rows.length,
          symbols_analyzed: rows.length,
          symbols_failed: 0,
          symbols_stale_cache: 0,
          snapshot_rows: rows.length,
          history_rows: 0,
          scanner_version: "published-fallback",
          notes: "Published fallback served by Vercel API.",
          payload: {
            data_provider_counts: { published_pages: rows.length },
            data_provider_priority: ["supabase", "published_pages", "static_bundle"],
            failed_symbols: [],
            stale_cache_fallbacks: [],
            stale_execution_blocks: rows.length,
            max_execution_data_age_days: 0,
          },
        };
    return {
      latest: latestData.run_date || runInfo.run_date || rows[0]?.run_date || "",
      previous: "",
      rows,
      previousRows: [],
      runInfo,
    };
  } catch {
    return staticLatestPayload();
  }
}

async function publishedTickerPayload(ticker, profile = {}) {
  try {
    const normalized = normalizeTicker(ticker);
    const [latestData, historyData] = await Promise.all([
      fetchPublishedJson("latest.json"),
      fetchPublishedJson("history.json"),
    ]);
    const rows = Array.isArray(latestData.rows) ? latestData.rows.map(conservativeFallbackRow) : [];
    const snapshot = rows.find((row) => normalizeTicker(row.ticker) === normalized) || null;
    const rawHistoryRows = Array.isArray(historyData.by_ticker?.[normalized])
      ? historyData.by_ticker[normalized]
      : (Array.isArray(historyData.rows) ? historyData.rows.filter((row) => normalizeTicker(row.ticker) === normalized) : []);
    const historyRows = rawHistoryRows
      .map(conservativeFallbackRow)
      .sort((a, b) => String(b.history_date || b.data_date || b.date || "").localeCompare(String(a.history_date || a.data_date || a.date || "")));
    const latest = latestData.run_date || snapshot?.run_date || historyRows[0]?.run_date || "";
    const runInfo = latestData.runInfo && typeof latestData.runInfo === "object"
      ? latestData.runInfo
      : {
          run_date: latest,
          status: "published_fallback",
          live_access_ok: false,
          live_access_message: "Using published GitHub Pages data because the live database is unavailable.",
          scanner_version: "published-fallback",
          payload: {
            data_provider_counts: { published_pages: snapshot ? 1 : 0 },
            data_provider_priority: ["supabase", "published_pages", "static_bundle"],
            failed_symbols: [],
            stale_cache_fallbacks: [],
            stale_execution_blocks: snapshot ? 1 : 0,
            max_execution_data_age_days: 0,
          },
        };
    return {
      ticker: normalized,
      latest,
      snapshot,
      historyRows,
      runInfo,
      profile,
    };
  } catch {
    return staticTickerPayload(ticker, profile);
  }
}

module.exports = {
  publishedLatestPayload,
  publishedTickerPayload,
};
