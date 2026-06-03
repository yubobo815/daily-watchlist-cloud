const SUPABASE_CONFIG = {
  url: process.env.SUPABASE_URL || "",
  apiKey: process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_ANON_KEY || "",
};

const SNAPSHOT_FIELDS = [
  "run_date",
  "ticker",
  "name",
  "data_date",
  "action",
  "setup",
  "adaptive_mode",
  "psychology",
  "score",
  "close",
  "day_change_pct",
  "entry_est",
  "stop_est",
  "target_est",
  "notes",
  "payload",
];

const HISTORY_FIELDS = ["run_date", "history_date", ...SNAPSHOT_FIELDS.filter((field) => field !== "run_date")];

const RUN_FIELDS = [
  "run_date",
  "status",
  "live_access_ok",
  "live_access_message",
  "earliest_data_date",
  "latest_data_date",
  "symbols_total",
  "symbols_analyzed",
  "symbols_failed",
  "symbols_stale_cache",
  "snapshot_rows",
  "history_rows",
  "scanner_version",
  "notes",
  "payload",
];

const PAYLOAD_FIELDS = [
  "adjusted_score",
  "atr_pct",
  "buyer_score",
  "distance_from_ref_zone_pct",
  "extension_state",
  "freshness_penalty",
  "price_progress_since_signal_pct",
  "reason_codes",
  "seller_score",
  "signal_age_days",
  "signal_stage",
  "transition_label",
  "transition_score",
  "volume_state",
];

function assertSupabaseConfig() {
  if (!SUPABASE_CONFIG.url || !SUPABASE_CONFIG.apiKey) {
    throw new Error("Supabase server config is missing.");
  }
}

function supabaseBaseUrl() {
  return SUPABASE_CONFIG.url.replace(/\/$/, "");
}

async function supabaseSelect(path) {
  assertSupabaseConfig();
  const response = await fetch(`${supabaseBaseUrl()}/rest/v1/${path}`, {
    headers: {
      apikey: SUPABASE_CONFIG.apiKey,
      Authorization: `Bearer ${SUPABASE_CONFIG.apiKey}`,
    },
  });
  const text = await response.text();
  if (!response.ok) {
    console.error(`Supabase query failed (${response.status}): ${text.slice(0, 500)}`);
    throw new Error("Data service unavailable.");
  }
  return text ? JSON.parse(text) : [];
}

function encodeFilterValue(value) {
  return encodeURIComponent(String(value));
}

function normalizeTicker(value) {
  return String(value || "").trim().toUpperCase().replace("BRK.B", "BRK-B");
}

function isValidTicker(value) {
  return /^[A-Z0-9.^-]{1,12}$/.test(value);
}

function selectList(fields) {
  return fields.join(",");
}

function cleanPayload(row) {
  const payload = row?.payload && typeof row.payload === "object" ? row.payload : {};
  return PAYLOAD_FIELDS.reduce((cleaned, field) => {
    const value = row?.[field] ?? payload[field];
    if (value !== undefined && value !== null && value !== "") cleaned[field] = value;
    return cleaned;
  }, {});
}

function rowDto(row) {
  const output = {};
  [...new Set([...SNAPSHOT_FIELDS, ...HISTORY_FIELDS])].forEach((field) => {
    if (field !== "payload" && row?.[field] !== undefined) output[field] = row[field];
  });
  output.payload = cleanPayload(row);
  return output;
}

function runDto(row) {
  if (!row) return null;
  const output = {};
  RUN_FIELDS.forEach((field) => {
    if (field !== "payload" && row[field] !== undefined) output[field] = row[field];
  });
  const payload = row.payload && typeof row.payload === "object" ? row.payload : {};
  output.payload = {
    failed_symbols: Array.isArray(payload.failed_symbols) ? payload.failed_symbols.slice(0, 25) : [],
    stale_cache_fallbacks: Array.isArray(payload.stale_cache_fallbacks) ? payload.stale_cache_fallbacks.slice(0, 25) : [],
  };
  return output;
}

function sortRows(rows) {
  return [...rows].sort((a, b) => {
    const aScore = Number(a.adjusted_score ?? a.payload?.adjusted_score ?? a.score ?? 0);
    const bScore = Number(b.adjusted_score ?? b.payload?.adjusted_score ?? b.score ?? 0);
    if (bScore !== aScore) return bScore - aScore;
    return String(a.ticker || "").localeCompare(String(b.ticker || ""));
  });
}

async function recentRunDates(limit = 2) {
  const dates = [];
  try {
    const runRows = await supabaseSelect(`watchlist_refresh_runs?select=run_date&order=run_date.desc&limit=${limit}`);
    runRows.forEach((row) => {
      if (row.run_date && !dates.includes(row.run_date)) dates.push(row.run_date);
    });
  } catch {
    // Older deployments may not have refresh run rows yet.
  }
  if (dates.length >= limit) return dates.slice(0, limit);

  const snapshotRows = await supabaseSelect("watchlist_snapshots?select=run_date&order=run_date.desc&limit=600");
  snapshotRows.forEach((row) => {
    if (row.run_date && !dates.includes(row.run_date)) dates.push(row.run_date);
  });
  return dates.slice(0, limit);
}

async function runInfo(runDate) {
  if (!runDate) return null;
  try {
    const rows = await supabaseSelect(`watchlist_refresh_runs?select=${selectList(RUN_FIELDS)}&run_date=eq.${encodeFilterValue(runDate)}&limit=1`);
    return runDto(rows[0]);
  } catch {
    return null;
  }
}

module.exports = {
  encodeFilterValue,
  HISTORY_FIELDS,
  isValidTicker,
  normalizeTicker,
  recentRunDates,
  rowDto,
  RUN_FIELDS,
  runInfo,
  selectList,
  SNAPSHOT_FIELDS,
  sortRows,
  supabaseSelect,
};
