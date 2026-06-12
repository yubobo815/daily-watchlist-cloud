const SUPABASE_CONFIG = {
  url: process.env.SUPABASE_URL || "",
  apiKey: process.env.SUPABASE_SECRET_KEY
    || process.env.SUPABASE_SERVICE_ROLE_KEY
    || process.env.SUPABASE_PUBLISHABLE_KEY
    || process.env.SUPABASE_ANON_KEY
    || "",
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

const HISTORY_FIELDS = [
  "run_date",
  "ticker",
  "history_date",
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
  "benchmark_return_20d_pct",
  "buy_quality_minimum",
  "buy_quality_score",
  "buyer_score",
  "days_to_report",
  "distance_from_ref_zone_pct",
  "entry_quality_label",
  "entry_quality_score",
  "emotion_score",
  "event_risk",
  "extension_state",
  "freshness_penalty",
  "market_context",
  "market_permission",
  "market_regime_summary",
  "next_day_bias",
  "next_day_bias_score",
  "next_day_plan",
  "operator_pressure",
  "operator_pressure_score",
  "operator_plan",
  "distribution_score",
  "absorption_score",
  "short_pressure_proxy",
  "squeeze_watch",
  "price_progress_since_signal_pct",
  "profile_zone_limit_pct",
  "personality_abs_move_pct",
  "personality_atr_pct",
  "personality_type",
  "qqq_return_20d_pct",
  "reason_codes",
  "relative_return_20d_pct",
  "risk_pct_to_stop",
  "risk_permission",
  "seller_score",
  "signal_age_days",
  "signal_quality",
  "signal_stage",
  "spy_return_20d_pct",
  "ticker_return_20d_pct",
  "ticker_avg_return",
  "ticker_permission",
  "ticker_trades",
  "ticker_win_rate",
  "ticker_worst_return",
  "transition_label",
  "transition_score",
  "trend_location_score",
  "setup_context_score",
  "volume_state",
  "walk_forward_permission",
  "wf_test_avg_return",
  "wf_test_trades",
  "wf_test_win_rate",
  "position_value_1k_risk",
];

const AUDIT_GATE_FIELDS = ["market_permission", "risk_permission"];
const UNGATED_SCORE_CAP = 49;

function assertSupabaseConfig() {
  if (!SUPABASE_CONFIG.url || !SUPABASE_CONFIG.apiKey) {
    throw new Error("Supabase server config is missing.");
  }
}

function supabaseBaseUrl() {
  return SUPABASE_CONFIG.url.replace(/\/$/, "");
}

function isJwtKey(key) {
  return String(key || "").split(".").length === 3 && !String(key || "").startsWith("sb_");
}

function supabaseHeaders() {
  const headers = {
    apikey: SUPABASE_CONFIG.apiKey,
  };
  if (isJwtKey(SUPABASE_CONFIG.apiKey)) {
    headers.Authorization = `Bearer ${SUPABASE_CONFIG.apiKey}`;
  }
  return headers;
}

async function supabaseSelect(path) {
  assertSupabaseConfig();
  const response = await supabaseRequest(path);
  const text = await response.text();
  if (!response.ok) {
    console.error(`Supabase query failed (${response.status}): ${text.slice(0, 500)}`);
    throw new Error("Data service unavailable.");
  }
  return text ? JSON.parse(text) : [];
}

async function supabaseRequest(path, options = {}) {
  assertSupabaseConfig();
  const headers = {
    ...supabaseHeaders(),
    ...(options.headers || {}),
  };
  if (options.body !== undefined && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  return fetch(`${supabaseBaseUrl()}/rest/v1/${path}`, {
    ...options,
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
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

function numericOrNull(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function capScore(value, cap = UNGATED_SCORE_CAP) {
  const number = numericOrNull(value);
  return number === null ? value : Math.min(number, cap);
}

function appendReasonCode(payload, code) {
  const raw = payload.reason_codes;
  const codes = Array.isArray(raw)
    ? raw
    : (typeof raw === "string" && raw ? raw.split(",").map((item) => item.trim()) : []);
  if (!codes.includes(code)) codes.push(code);
  payload.reason_codes = codes.filter(Boolean);
}

function hasKnownAuditGate(value) {
  const text = String(value || "").toUpperCase();
  return Boolean(text) && text !== "UNKNOWN";
}

function applyAuditGateFallback(output) {
  const payload = output.payload && typeof output.payload === "object" ? { ...output.payload } : {};
  const hasAllGates = AUDIT_GATE_FIELDS.every((field) => hasKnownAuditGate(output[field] || payload[field]));
  if (hasAllGates) {
    output.payload = payload;
    return output;
  }

  payload.market_permission = payload.market_permission || output.market_permission || "UNKNOWN";
  payload.risk_permission = payload.risk_permission || output.risk_permission || "UNKNOWN";
  payload.audit_gate_status = "MISSING";
  payload.signal_quality = "NEEDS EXECUTION PROOF";
  payload.transition_label = "Needs Execution Proof";
  payload.transition_score = capScore(payload.transition_score ?? output.transition_score ?? -25, -25);
  payload.adjusted_score = capScore(payload.adjusted_score ?? output.adjusted_score ?? output.score);
  output.adjusted_score = capScore(output.adjusted_score ?? payload.adjusted_score ?? output.score);
  output.score = capScore(output.score);
  appendReasonCode(payload, "missing_execution_proof");
  output.notes = [output.notes, "Live row lacks current market/risk execution proof"].filter(Boolean).join("; ");
  if (output.action === "BUY CANDIDATE" || output.action === "STRONG CONTINUATION") {
    output.action = "SETUP FORMING";
    payload.signal_stage = "SETUP";
  }
  output.payload = payload;
  return output;
}

function rowDto(row) {
  const output = {};
  [...new Set([...SNAPSHOT_FIELDS, ...HISTORY_FIELDS])].forEach((field) => {
    if (field !== "payload" && row?.[field] !== undefined) output[field] = row[field];
  });
  output.payload = cleanPayload(row);
  return applyAuditGateFallback(output);
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
  supabaseRequest,
  supabaseSelect,
};
