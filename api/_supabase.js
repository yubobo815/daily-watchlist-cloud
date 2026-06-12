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
  "anti_signal_level",
  "anti_signal_plan",
  "anti_signal_score",
  "atr_pct",
  "benchmark_return_20d_pct",
  "buy_quality_minimum",
  "buy_quality_score",
  "buy_tier",
  "buyer_score",
  "data_age_days",
  "days_to_report",
  "distance_from_ref_zone_pct",
  "entry_quality_label",
  "entry_quality_score",
  "emotion_score",
  "event_risk",
  "execution_plan",
  "execution_priority",
  "extension_state",
  "feedback_max_drawdown_pct",
  "feedback_plan",
  "feedback_quality",
  "feedback_return_pct",
  "feedback_stop_hit",
  "feedback_window_days",
  "freshness_penalty",
  "freshness_block",
  "freshness_plan",
  "freshness_status",
  "last_outcome_label",
  "last_outcome_reason",
  "last_outcome_return_pct",
  "last_outcome_score",
  "learning_adjustment",
  "learning_avg_score",
  "learning_failed_rate",
  "learning_plan",
  "learning_sample_count",
  "learning_trap_avoided_rate",
  "learning_working_rate",
  "market_context",
  "market_permission",
  "market_regime_summary",
  "next_day_bias",
  "next_day_bias_score",
  "next_day_plan",
  "operator_pressure",
  "operator_pressure_score",
  "operator_plan",
  "operator_state",
  "operator_state_score",
  "operator_state_plan",
  "demand_control_score",
  "bull_trap_score",
  "bear_trap_score",
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
const MAX_EXECUTION_DATA_AGE_DAYS = Number(process.env.MAX_EXECUTION_DATA_AGE_DAYS || 3);

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

function isoDateOnly(value) {
  const text = String(value || "").slice(0, 10);
  return /^\d{4}-\d{2}-\d{2}$/.test(text) ? text : "";
}

function dataAgeDays(dataDate) {
  const dateText = isoDateOnly(dataDate);
  if (!dateText) return null;
  const today = new Date();
  const todayUtc = Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate());
  const dataUtc = Date.parse(`${dateText}T00:00:00Z`);
  if (!Number.isFinite(dataUtc)) return null;
  return Math.floor((todayUtc - dataUtc) / 86400000);
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

function applyFreshnessFallback(output) {
  const payload = output.payload && typeof output.payload === "object" ? { ...output.payload } : {};
  const age = Number(payload.data_age_days ?? dataAgeDays(output.data_date || output.history_date || output.date));
  const hasAge = Number.isFinite(age);
  const stale = !hasAge || age > MAX_EXECUTION_DATA_AGE_DAYS;
  payload.data_age_days = hasAge ? age : "";
  payload.freshness_block = payload.freshness_block || (stale ? "YES" : "NO");
  payload.freshness_status = payload.freshness_status || (stale ? "STALE_BLOCK" : "LIVE_OR_CURRENT");
  payload.freshness_plan = payload.freshness_plan || (
    stale
      ? `Execution blocked: market data is ${hasAge ? age : "unknown"} day(s) old; refresh live data before acting.`
      : "Data freshness is acceptable for scanner use."
  );

  if (stale) {
    appendReasonCode(payload, "data_stale_block");
    if (output.action === "BUY CANDIDATE" || output.action === "STRONG CONTINUATION") {
      output.action = "SETUP FORMING";
      payload.signal_stage = "SETUP";
    }
    if (["BUY CANDIDATE", "STRONG CONTINUATION", "SETUP FORMING"].includes(output.action)) {
      payload.signal_quality = "STALE DATA";
      payload.transition_label = "Data Stale";
      payload.transition_score = capScore(payload.transition_score ?? output.transition_score ?? -30, -30);
      payload.adjusted_score = capScore(payload.adjusted_score ?? output.adjusted_score ?? output.score);
      output.adjusted_score = capScore(output.adjusted_score ?? payload.adjusted_score ?? output.score);
      output.score = capScore(output.score);
      payload.next_day_bias = "EXECUTION BLOCKED";
      payload.next_day_plan = payload.freshness_plan;
      output.notes = [output.notes, payload.freshness_plan].filter(Boolean).join("; ");
    }
  }

  output.payload = payload;
  return output;
}

function antiSignalFallback(output) {
  const payload = output.payload && typeof output.payload === "object" ? { ...output.payload } : {};
  const operatorState = String(payload.operator_state || "").toUpperCase();
  const operatorPressure = String(payload.operator_pressure || "").toUpperCase();
  const nextDay = String(payload.next_day_bias || "").toUpperCase();
  const extensionState = String(payload.extension_state || "").toUpperCase();
  const quality = String(payload.signal_quality || "").toUpperCase();
  const bullTrapScore = Number(payload.bull_trap_score || 0);
  const distributionScore = Number(payload.distribution_score || 0);
  const triggers = [];
  let computedScore = 0;

  if (payload.freshness_block === "YES" || quality === "STALE DATA") {
    computedScore += 45;
    triggers.push("stale data");
  }
  if (operatorState === "BULL_TRAP" || bullTrapScore >= 58) {
    computedScore += 38;
    triggers.push("bull trap");
  }
  if (operatorState === "DISTRIBUTION" || operatorPressure.includes("DISTRIBUTION") || distributionScore >= 55) {
    computedScore += 34;
    triggers.push("distribution");
  }
  if (extensionState === "EXTENDED" || nextDay === "AVOID CHASE" || quality === "EXTENDED") {
    computedScore += 28;
    triggers.push("extended chase");
  }
  if (nextDay === "EXECUTION BLOCKED") {
    computedScore += 35;
    triggers.push("execution blocked");
  } else if (nextDay === "DEFENSIVE / EXIT RISK") {
    computedScore += 24;
    triggers.push("defensive tape");
  }

  const existingScore = Number(payload.anti_signal_score || 0);
  const score = Math.min(100, Math.max(computedScore, Number.isFinite(existingScore) ? existingScore : 0));
  const uniqueTriggers = [...new Set(triggers)];
  let level = payload.anti_signal_level || "NONE";
  if (score >= 45) level = "BLOCK";
  else if (score >= 25) level = "CAUTION";

  payload.anti_signal_score = Number.isFinite(score) ? score : 0;
  payload.anti_signal_level = level;
  payload.anti_signal_plan = payload.anti_signal_plan || (
    level === "BLOCK"
      ? `Anti-signal block: ${uniqueTriggers.join(", ")}; downgrade execution even if trend score is high.`
      : level === "CAUTION"
        ? `Anti-signal caution: ${uniqueTriggers.join(", ")}; keep on watch, but do not upgrade without a clean reset.`
        : "No major anti-signal penalty."
  );

  if (level === "NONE") {
    output.payload = payload;
    return output;
  }

  appendReasonCode(payload, level === "BLOCK" ? "anti_signal_block" : "anti_signal_caution");
  const reasonByTrigger = {
    "stale data": "anti_stale_data",
    "bull trap": "anti_bull_trap",
    distribution: "anti_distribution",
    "extended chase": "anti_extended_chase",
    "execution blocked": "anti_execution_blocked",
    "defensive tape": "anti_defensive_tape",
  };
  uniqueTriggers.forEach((trigger) => appendReasonCode(payload, reasonByTrigger[trigger]));

  if (["BUY CANDIDATE", "STRONG CONTINUATION", "SETUP FORMING"].includes(output.action)) {
    payload.buy_tier = "SETUP ONLY";
    payload.execution_priority = level === "BLOCK" ? 4 : Math.max(Number(payload.execution_priority || 3), 3);
    payload.execution_plan = payload.anti_signal_plan;
    appendReasonCode(payload, "setup_only_tier");
    if (level === "BLOCK") {
      if (output.action === "BUY CANDIDATE" || output.action === "STRONG CONTINUATION") {
        output.action = "SETUP FORMING";
        payload.signal_stage = "SETUP";
      }
      payload.adjusted_score = capScore(payload.adjusted_score ?? output.adjusted_score ?? output.score);
      output.adjusted_score = capScore(output.adjusted_score ?? payload.adjusted_score ?? output.score);
      output.score = capScore(output.score);
    } else {
      const cap = 76;
      payload.adjusted_score = capScore(payload.adjusted_score ?? output.adjusted_score ?? output.score, cap);
      output.adjusted_score = capScore(output.adjusted_score ?? payload.adjusted_score ?? output.score, cap);
    }
  }

  output.payload = payload;
  return output;
}

function applyBuyTierFallback(output) {
  const payload = output.payload && typeof output.payload === "object" ? { ...output.payload } : {};
  if (!payload.buy_tier) {
    if (["BLOCK", "CAUTION"].includes(payload.anti_signal_level) && ["BUY CANDIDATE", "STRONG CONTINUATION", "SETUP FORMING"].includes(output.action)) {
      payload.buy_tier = "SETUP ONLY";
      payload.execution_priority = payload.anti_signal_level === "BLOCK" ? 4 : 3;
      payload.execution_plan = payload.anti_signal_plan || "Anti-signal penalty active; do not execute directly.";
      appendReasonCode(payload, "setup_only_tier");
    } else if (payload.freshness_block === "YES" && ["BUY CANDIDATE", "STRONG CONTINUATION", "SETUP FORMING"].includes(output.action)) {
      payload.buy_tier = "SETUP ONLY";
      payload.execution_priority = 4;
      payload.execution_plan = "Do not execute directly; treat as a setup until the blocker clears.";
      appendReasonCode(payload, "setup_only_tier");
    } else if (output.action === "BUY CANDIDATE") {
      payload.buy_tier = "BUY WATCH";
      payload.execution_priority = 2;
      payload.execution_plan = "Qualified buy watch; prefer reference-zone entry and Pine confirmation.";
    } else if (output.action === "WATCH TREND") {
      payload.buy_tier = "WATCH";
      payload.execution_priority = 5;
    } else if (output.action === "EXIT PRESSURE") {
      payload.buy_tier = "EXIT RISK";
      payload.execution_priority = 8;
    } else {
      payload.buy_tier = "NO TRADE";
      payload.execution_priority = 9;
    }
  }
  output.payload = payload;
  return output;
}

function applyOperatorStateFallback(output) {
  const payload = output.payload && typeof output.payload === "object" ? { ...output.payload } : {};
  if (!payload.operator_state) {
    const pressure = String(payload.operator_pressure || "NEUTRAL").toUpperCase();
    if (pressure.includes("DISTRIBUTION") || pressure === "SHORT PRESSURE") {
      payload.operator_state = "DISTRIBUTION";
    } else if (pressure.includes("SQUEEZE")) {
      payload.operator_state = "BEAR_TRAP / SQUEEZE WATCH";
    } else if (pressure.includes("ACCUMULATION") || pressure.includes("ABSORPTION")) {
      payload.operator_state = "ACCUMULATION";
    } else {
      payload.operator_state = "NEUTRAL";
    }
    payload.operator_state_score = payload.operator_pressure_score ?? 0;
    payload.operator_state_plan = payload.operator_plan || "No clear trap or accumulation/distribution edge from the current candle sequence.";
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
  return applyBuyTierFallback(antiSignalFallback(applyFreshnessFallback(applyOperatorStateFallback(applyAuditGateFallback(output)))));
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
    stale_execution_blocks: Number(payload.stale_execution_blocks || 0),
    signal_outcomes: payload.signal_outcomes && typeof payload.signal_outcomes === "object" ? payload.signal_outcomes : {},
    max_execution_data_age_days: Number(payload.max_execution_data_age_days || 0),
  };
  return output;
}

function sortRows(rows) {
  return [...rows].sort((a, b) => {
    const aPriority = Number(a.execution_priority ?? a.payload?.execution_priority ?? 99);
    const bPriority = Number(b.execution_priority ?? b.payload?.execution_priority ?? 99);
    if (aPriority !== bPriority) return aPriority - bPriority;
    const aScore = Number(a.adjusted_score ?? a.payload?.adjusted_score ?? a.score ?? 0);
    const bScore = Number(b.adjusted_score ?? b.payload?.adjusted_score ?? b.score ?? 0);
    if (bScore !== aScore) return bScore - aScore;
    return String(a.ticker || "").localeCompare(String(b.ticker || ""));
  });
}

async function recentRunDates(limit = 2) {
  const dates = [];
  const addDate = (row) => {
    if (row.run_date && !dates.includes(row.run_date)) dates.push(row.run_date);
  };

  // Snapshot rows are the source of truth for a usable app state. A degraded
  // refresh may write run health without snapshot rows, and that must not make
  // the app select an empty latest date.
  const snapshotRows = await supabaseSelect("watchlist_snapshots?select=run_date&order=run_date.desc&limit=600");
  snapshotRows.forEach(addDate);
  if (dates.length >= limit) return dates.slice(0, limit);

  try {
    const runRows = await supabaseSelect(`watchlist_refresh_runs?select=run_date&order=run_date.desc&limit=${limit}`);
    runRows.forEach(addDate);
  } catch {
    // Older deployments may not have refresh run rows yet.
  }
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
