const { conservativeFallbackRow, normalizeTicker, staticLatestPayload, staticTickerPayload } = require("./_static_data");

const PUBLISHED_BASE_URL = "https://yubobo815.github.io/daily-watchlist-cloud/data";
const LEARNING_EVIDENCE_FIELDS = [
  "learning_sample_count",
  "learning_working_rate",
  "learning_failed_rate",
  "learning_trap_avoided_rate",
  "learning_avg_score",
  "learning_adjustment",
  "learning_scope",
  "learning_key_used",
  "learning_plan",
  "learning_model_version",
  "learning_distinct_ticker_count",
  "learning_evaluation_date_count",
  "learning_evaluation_date_min",
  "learning_evaluation_date_max",
  "learning_window_start",
  "learning_window_end",
  "learning_promotion_eligible",
  "learning_reporting_only",
  "learning_promotion_state",
];

async function fetchPublishedJson(name) {
  const response = await fetch(`${PUBLISHED_BASE_URL}/${name}?v=${Date.now()}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Published ${name} returned HTTP ${response.status}.`);
  }
  return response.json();
}

function normalizeFallbackRow(row) {
  const source = row && typeof row === "object" ? row : {};
  const payload = source.payload && typeof source.payload === "object" ? { ...source.payload } : {};
  LEARNING_EVIDENCE_FIELDS.forEach((field) => {
    if (payload[field] === undefined && source[field] !== undefined) payload[field] = source[field];
  });

  const normalized = conservativeFallbackRow({ ...source, payload });
  const normalizedPayload = normalized.payload && typeof normalized.payload === "object" ? normalized.payload : {};
  LEARNING_EVIDENCE_FIELDS.forEach((field) => {
    if (normalizedPayload[field] === undefined && normalized[field] !== undefined) normalizedPayload[field] = normalized[field];
    if (normalized[field] === undefined && normalizedPayload[field] !== undefined) normalized[field] = normalizedPayload[field];
  });
  // A fallback cannot establish promotion eligibility for the current session.
  normalized.learning_promotion_eligible = false;
  normalizedPayload.learning_promotion_eligible = false;
  normalized.learning_reporting_only = true;
  normalizedPayload.learning_reporting_only = true;
  normalized.learning_promotion_state = "REPORTING_ONLY";
  normalizedPayload.learning_promotion_state = "REPORTING_ONLY";
  normalized.payload = normalizedPayload;
  return normalized;
}

function fallbackRunInfo(source, latest, rowCount, sourceName) {
  const run = source && typeof source === "object" ? source : {};
  const sourcePayload = run.payload && typeof run.payload === "object" ? run.payload : {};
  const label = sourceName === "static_bundle" ? "bundled static" : "published GitHub Pages";
  const message = `Using ${label} fallback data because the live database is unavailable; execution is blocked.`;
  return {
    ...run,
    run_date: latest || run.run_date || "",
    status: sourceName === "static_bundle" ? "static_fallback" : "published_fallback",
    live_access_ok: false,
    live_access_message: message,
    symbols_total: rowCount,
    symbols_analyzed: rowCount,
    symbols_failed: 0,
    symbols_stale_cache: 0,
    snapshot_rows: rowCount,
    scanner_version: `${sourceName}-fallback`,
    notes: message,
    payload: {
      ...sourcePayload,
      data_provider_counts: { [sourceName]: rowCount },
      data_provider_priority: ["supabase", "published_pages", "static_bundle"],
      failed_symbols: [],
      stale_cache_fallbacks: [],
      stale_execution_blocks: rowCount,
      max_execution_data_age_days: 0,
    },
  };
}

function fallbackLatestResponse(data, sourceName) {
  const rows = Array.isArray(data?.rows) ? data.rows.map(normalizeFallbackRow) : [];
  const latest = data?.run_date || data?.latest || data?.runInfo?.run_date || rows[0]?.run_date || "";
  return {
    latest,
    previous: "",
    rows,
    previousRows: [],
    runInfo: fallbackRunInfo(data?.runInfo, latest, rows.length, sourceName),
  };
}

async function publishedLatestPayload() {
  try {
    const latestData = await fetchPublishedJson("latest.json");
    return fallbackLatestResponse(latestData, "published_pages");
  } catch {
    return fallbackLatestResponse(staticLatestPayload(), "static_bundle");
  }
}

async function publishedTickerPayload(ticker, profile = {}) {
  try {
    const normalized = normalizeTicker(ticker);
    const [latestData, historyData] = await Promise.all([
      fetchPublishedJson("latest.json"),
      fetchPublishedJson("history.json"),
    ]);
    const rows = Array.isArray(latestData.rows) ? latestData.rows.map(normalizeFallbackRow) : [];
    const snapshot = rows.find((row) => normalizeTicker(row.ticker) === normalized) || null;
    const rawHistoryRows = Array.isArray(historyData.by_ticker?.[normalized])
      ? historyData.by_ticker[normalized]
      : (Array.isArray(historyData.rows) ? historyData.rows.filter((row) => normalizeTicker(row.ticker) === normalized) : []);
    const historyRows = rawHistoryRows
      .map(normalizeFallbackRow)
      .sort((a, b) => String(b.history_date || b.data_date || b.date || "").localeCompare(String(a.history_date || a.data_date || a.date || "")));
    const latest = latestData.run_date || snapshot?.run_date || historyRows[0]?.run_date || "";
    return {
      ticker: normalized,
      latest,
      snapshot,
      historyRows,
      runInfo: fallbackRunInfo(latestData.runInfo, latest, snapshot ? 1 : 0, "published_pages"),
      profile,
    };
  } catch {
    const fallback = staticTickerPayload(ticker, profile);
    return {
      ...fallback,
      snapshot: fallback.snapshot ? normalizeFallbackRow(fallback.snapshot) : null,
      historyRows: (fallback.historyRows || []).map(normalizeFallbackRow),
      runInfo: fallbackRunInfo(fallback.runInfo, fallback.latest, fallback.snapshot ? 1 : 0, "static_bundle"),
    };
  }
}

module.exports = {
  publishedLatestPayload,
  publishedTickerPayload,
};
