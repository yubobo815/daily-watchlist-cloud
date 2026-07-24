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

function publishedUrl(path) {
  const normalizedPath = String(path || "").trim().replace(/^\/+/, "");
  if (!normalizedPath || normalizedPath.includes("..") || /[?#]/.test(normalizedPath)) {
    throw new Error("Published data path is invalid.");
  }
  return `${PUBLISHED_BASE_URL}/${normalizedPath.replace(/^data\//, "")}`;
}

async function fetchPublishedJson(path, { mutable = false } = {}) {
  const response = await fetch(publishedUrl(path), {
    // The manifest is the mutable pointer. Publication-scoped artifacts never
    // change, so runtimes and upstream caches can safely retain them.
    cache: mutable ? "no-cache" : "force-cache",
  });
  if (!response.ok) {
    throw new Error(`Published ${path} returned HTTP ${response.status}.`);
  }
  return response.json();
}

async function publishedManifest() {
  const manifest = await fetchPublishedJson("manifest.json", { mutable: true });
  const publicationId = String(manifest?.publication_id || "").trim();
  const runDate = String(manifest?.run_date || "").trim();
  const latestPath = String(manifest?.latest_path || "").trim();
  const tickerBasePath = String(manifest?.ticker_base_path || "").trim().replace(/\/+$/, "");
  const tickerPaths = manifest?.ticker_paths && typeof manifest.ticker_paths === "object" ? manifest.ticker_paths : null;
  if (!publicationId || !runDate || !latestPath || !tickerBasePath || !tickerPaths) {
    throw new Error("Published manifest is incomplete.");
  }
  const latestVersion = latestPath.match(/(?:^|\/)runs\/([^/]+)\//)?.[1];
  const tickerVersion = tickerBasePath.match(/(?:^|\/)runs\/([^/]+)(?:\/|$)/)?.[1];
  if (!latestVersion || latestVersion !== tickerVersion) {
    throw new Error("Published manifest paths are not scoped to its publication.");
  }
  // Validate both paths before returning the manifest.
  publishedUrl(latestPath);
  publishedUrl(tickerBasePath);
  return { ...manifest, publication_id: publicationId, run_date: runDate, latest_path: latestPath, ticker_base_path: tickerBasePath, ticker_paths: tickerPaths };
}

function assertPublication(payload, manifest, label) {
  const payloadPublicationId = String(
    payload?.publication_id || payload?.runInfo?.publication_id || payload?.runInfo?.payload?.publication_id || "",
  ).trim();
  const payloadRunDate = String(payload?.run_date || payload?.latest || "").trim();
  if (payloadPublicationId !== manifest.publication_id || payloadRunDate !== String(manifest.run_date || "").trim()) {
    throw new Error(`Published ${label} does not match the active manifest.`);
  }
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
    const manifest = await publishedManifest();
    const latestData = await fetchPublishedJson(manifest.latest_path);
    assertPublication(latestData, manifest, "latest payload");
    return fallbackLatestResponse(latestData, "published_pages");
  } catch {
    return fallbackLatestResponse(staticLatestPayload(), "static_bundle");
  }
}

async function publishedTickerPayload(ticker, profile = {}) {
  try {
    const normalized = normalizeTicker(ticker);
    const manifest = await publishedManifest();
    const tickerPath = String(manifest.ticker_paths[normalized] || "");
    if (!tickerPath.startsWith(`${manifest.ticker_base_path}/`)) throw new Error(`${normalized} is not included in the active publication.`);
    const tickerData = await fetchPublishedJson(tickerPath);
    assertPublication(tickerData, manifest, `${normalized} payload`);
    if (normalizeTicker(tickerData?.ticker) !== normalized) throw new Error(`Published ${normalized} payload has the wrong ticker.`);
    const rawSnapshot = tickerData?.snapshot && typeof tickerData.snapshot === "object"
      ? tickerData.snapshot
      : null;
    const snapshot = rawSnapshot ? normalizeFallbackRow(rawSnapshot) : null;
    const rawHistoryRows = Array.isArray(tickerData?.historyRows)
      ? tickerData.historyRows
      : (Array.isArray(tickerData?.history_rows) ? tickerData.history_rows : []);
    const historyRows = rawHistoryRows
      .map(normalizeFallbackRow)
      .sort((a, b) => String(b.history_date || b.data_date || b.date || "").localeCompare(String(a.history_date || a.data_date || a.date || "")));
    const latest = tickerData.latest || tickerData.run_date || snapshot?.run_date || historyRows[0]?.run_date || manifest.run_date || "";
    return {
      ticker: normalized,
      latest,
      snapshot,
      historyRows,
      runInfo: fallbackRunInfo(tickerData.runInfo, latest, snapshot ? 1 : 0, "published_pages"),
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
