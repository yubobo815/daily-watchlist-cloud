const { marketSessionAge } = require("./_market_session");

const SUPABASE_CONFIG = {
  url: process.env.SUPABASE_URL || "",
  apiKey: process.env.SUPABASE_SECRET_KEY
    || process.env.SUPABASE_SERVICE_ROLE_KEY
    || process.env.SUPABASE_PUBLISHABLE_KEY
    || process.env.SUPABASE_ANON_KEY
    || "",
};

const SNAPSHOT_FIELDS = [
  "publication_id",
  "run_date",
  "ticker",
  "name",
  "data_date",
  "action",
  "setup",
  "adaptive_mode",
  "psychology",
  "score",
  "open",
  "high",
  "low",
  "close",
  "day_change_pct",
  "entry_est",
  "stop_est",
  "target_est",
  "notes",
  "payload",
];

const HISTORY_FIELDS = [
  "publication_id",
  "run_date",
  "ticker",
  "history_date",
  "action",
  "setup",
  "adaptive_mode",
  "psychology",
  "score",
  "open",
  "high",
  "low",
  "close",
  "day_change_pct",
  "entry_est",
  "stop_est",
  "target_est",
  "notes",
  "payload",
];

const RUN_FIELDS = [
  "publication_id",
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

const RUN_OPTIONAL_FIELDS = [
  "learning_history_rows",
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
  "contextual_overlay",
  "contextual_plan",
  "contextual_score_adjustment",
  "data_age_days",
  "days_to_report",
  "distance_from_ref_zone_pct",
  "entry_zone_low",
  "entry_zone_high",
  "entry_zone_width_pct",
  "entry_zone_plan",
  "entry_quality_label",
  "entry_quality_score",
  "emotion_score",
  "event_risk",
  "execution_block",
  "execution_style",
  "execution_window_sessions",
  "execution_fill_sample_count",
  "execution_fill_distinct_ticker_count",
  "execution_fill_evaluation_date_count",
  "execution_fill_rate",
  "execution_fill_probability",
  "execution_fill_scope",
  "execution_fill_state",
  "execution_fill_model_version",
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
  "learning_distinct_ticker_count",
  "learning_evaluation_date_count",
  "learning_evaluation_date_min",
  "learning_evaluation_date_max",
  "learning_failed_rate",
  "learning_key_used",
  "learning_model_version",
  "learning_plan",
  "learning_promotion_eligible",
  "learning_promotion_state",
  "learning_reporting_only",
  "learning_sample_count",
  "learning_scope",
  "learning_trap_avoided_rate",
  "learning_window_end",
  "learning_window_start",
  "learning_working_rate",
  "prediction_horizon_sessions",
  "prediction_upside_probability",
  "prediction_downside_probability",
  "prediction_no_edge_probability",
  "prediction_confidence",
  "prediction_model_version",
  "prediction_state",
  "directional_model_version",
  "directional_model_train_samples",
  "directional_model_oos_samples",
  "directional_model_brier_score",
  "directional_model_baseline_brier",
  "directional_model_brier_skill",
  "directional_model_state",
  "data_provider",
  "data_provider_error",
  "data_provider_latency_ms",
  "data_provider_status",
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
  "open",
  "high",
  "low",
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
  "transition_edge_score",
  "personality_weight_label",
  "personality_weight_emotion",
  "personality_weight_transition",
  "personality_weight_setup",
  "personality_weight_trend",
  "personality_setup_allowed",
  "volatility_regime",
  "volatility_permission",
  "volatility_plan",
  "position_size_factor",
  "take_profit_1",
  "take_profit_1_r",
  "take_profit_1_reduce_pct",
  "post_tp1_stop",
  "profit_management_plan",
  "profit_stage",
  "take_profit_1_hit",
  "profit_peak_r",
  "profit_giveback_r",
  "active_protective_stop",
  "profit_protect_pressure",
  "hard_exit_pressure",
  "trend_location_score",
  "setup_context_score",
  "volume_state",
  "walk_forward_permission",
  "wf_test_avg_return",
  "wf_test_trades",
  "wf_test_win_rate",
  "position_value_1k_risk",
];

const AUDIT_GATE_FIELDS = ["market_permission", "ticker_permission", "walk_forward_permission", "risk_permission"];
const AUDIT_GATE_VALUES = {
  market_permission: new Set(["ALLOW", "BLOCK"]),
  ticker_permission: new Set(["ALLOW", "CAUTION", "BLOCK", "INSUFFICIENT"]),
  walk_forward_permission: new Set(["ALLOW", "BLOCK", "INSUFFICIENT", "NONE"]),
  risk_permission: new Set(["ALLOW", "BLOCK"]),
};
const BUY_LIKE_ACTIONS = new Set(["BUY CANDIDATE", "STRONG CONTINUATION"]);
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

function promotePayloadFields(row) {
  const payload = row?.payload && typeof row.payload === "object" ? row.payload : {};
  PAYLOAD_FIELDS.forEach((field) => {
    if (row[field] === undefined && payload[field] !== undefined) row[field] = payload[field];
  });
  return row;
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
  return marketSessionAge(isoDateOnly(dataDate));
}

function appendReasonCode(payload, code) {
  const raw = payload.reason_codes;
  const codes = Array.isArray(raw)
    ? raw
    : (typeof raw === "string" && raw ? raw.split(",").map((item) => item.trim()) : []);
  if (!codes.includes(code)) codes.push(code);
  payload.reason_codes = codes.filter(Boolean);
}

function normalizeAuditGate(value) {
  return String(value ?? "").trim().toUpperCase();
}

function auditGateState(source, field) {
  const topLevel = normalizeAuditGate(source?.[field]);
  const nested = normalizeAuditGate(source?.payload?.[field]);
  const value = topLevel || nested;
  return {
    field,
    value,
    contradictory: Boolean(topLevel && nested && topLevel !== nested),
    valid: AUDIT_GATE_VALUES[field].has(value),
  };
}

function applyPersonalitySetupGate(output, source) {
  if (!BUY_LIKE_ACTIONS.has(output.action)) return output;

  const topLevel = normalizeAuditGate(source?.personality_setup_allowed);
  const nested = normalizeAuditGate(source?.payload?.personality_setup_allowed);
  // A conflicting YES cannot override a NO from either producer row shape.
  if (topLevel !== "NO" && nested !== "NO") return output;

  const payload = output.payload && typeof output.payload === "object" ? { ...output.payload } : {};
  payload.personality_setup_allowed = "NO";
  payload.audit_gate_status = "BLOCKED";
  payload.signal_quality = "PERSONALITY SETUP BLOCKED";
  payload.transition_label = "Personality Setup Blocked";
  payload.transition_score = capScore(payload.transition_score ?? output.transition_score ?? -25, -25);
  payload.adjusted_score = capScore(payload.adjusted_score ?? output.adjusted_score ?? output.score);
  output.adjusted_score = capScore(output.adjusted_score ?? payload.adjusted_score ?? output.score);
  payload.buy_tier = "SETUP ONLY";
  payload.execution_priority = Math.max(Number(payload.execution_priority || 4), 4);
  payload.execution_plan = "Personality setup gate is NO; keep this as a setup and do not promote it to BUY.";
  appendReasonCode(payload, "personality_setup_not_allowed");
  if (topLevel && nested && topLevel !== nested) appendReasonCode(payload, "personality_setup_allowed_contradictory");
  output.action = "SETUP FORMING";
  payload.signal_stage = "SETUP";
  output.notes = [output.notes, "Personality setup gate blocks BUY promotion"].filter(Boolean).join("; ");
  output.payload = payload;
  return output;
}

function applyVolatilityGate(output, source) {
  if (!BUY_LIKE_ACTIONS.has(output.action)) return output;

  const topLevel = normalizeAuditGate(source?.volatility_permission);
  const nested = normalizeAuditGate(source?.payload?.volatility_permission);
  const permission = [topLevel, nested].includes("BLOCK")
    ? "BLOCK"
    : ([topLevel, nested].includes("CAUTION") ? "CAUTION" : "ALLOW");
  if (permission === "ALLOW") return output;

  const payload = output.payload && typeof output.payload === "object" ? { ...output.payload } : {};
  payload.volatility_permission = permission;
  payload.audit_gate_status = "BLOCKED";
  payload.signal_quality = permission === "BLOCK" ? "CHAOTIC VOLATILITY" : "VOLATILITY NEEDS CONFIRMATION";
  payload.transition_label = permission === "BLOCK" ? "Volatility Blocked" : "Volatility Caution";
  payload.transition_score = capScore(payload.transition_score ?? output.transition_score ?? -20, -20);
  payload.adjusted_score = capScore(payload.adjusted_score ?? output.adjusted_score ?? output.score);
  output.adjusted_score = capScore(output.adjusted_score ?? payload.adjusted_score ?? output.score);
  payload.buy_tier = "SETUP ONLY";
  payload.execution_priority = Math.max(Number(payload.execution_priority || 4), 4);
  payload.next_day_bias = permission === "BLOCK" ? "EXECUTION BLOCKED" : "WATCH TREND";
  payload.next_day_plan = payload.volatility_plan || "Wait for directional volatility and buyer confirmation before entering.";
  payload.execution_plan = payload.next_day_plan;
  appendReasonCode(payload, "volatility_execution_gate");
  output.action = "SETUP FORMING";
  payload.signal_stage = "SETUP";
  output.notes = [output.notes, payload.next_day_plan].filter(Boolean).join("; ");
  output.payload = payload;
  return output;
}

function applyAuditGateFallback(output, source) {
  const payload = output.payload && typeof output.payload === "object" ? { ...output.payload } : {};
  const gates = AUDIT_GATE_FIELDS.map((field) => auditGateState(source, field));
  const hasAllGates = gates.every((gate) => !gate.contradictory && gate.valid && gate.value === "ALLOW");
  if (hasAllGates) {
    output.payload = payload;
    return output;
  }

  // A current execution recommendation needs unambiguous ALLOW evidence for
  // every execution gate. Do not expose a permissive value from a conflicting row.
  gates.forEach((gate) => {
    payload[gate.field] = gate.contradictory || !gate.valid ? "UNKNOWN" : gate.value;
  });
  payload.audit_gate_status = "BLOCKED";
  payload.signal_quality = "NEEDS EXECUTION PROOF";
  payload.transition_label = "Needs Execution Proof";
  payload.transition_score = capScore(payload.transition_score ?? output.transition_score ?? -25, -25);
  payload.adjusted_score = capScore(payload.adjusted_score ?? output.adjusted_score ?? output.score);
  output.adjusted_score = capScore(output.adjusted_score ?? payload.adjusted_score ?? output.score);
  appendReasonCode(payload, "missing_execution_proof");
  gates.forEach((gate) => {
    if (gate.contradictory) appendReasonCode(payload, `${gate.field}_contradictory`);
    else if (!gate.valid || gate.value !== "ALLOW") appendReasonCode(payload, `${gate.field}_not_allowed`);
  });
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
  const rawAge = payload.data_age_days;
  const suppliedAge = rawAge === "" || rawAge === null || rawAge === undefined ? null : Number(rawAge);
  const dataDate = output.data_date || output.history_date || output.date;
  const dateAge = dataAgeDays(dataDate);
  const claimedCurrentDateConflict = suppliedAge === 0 && Number.isFinite(dateAge) && dateAge !== 0;
  const age = claimedCurrentDateConflict
    ? dateAge
    : (Number.isFinite(suppliedAge) ? suppliedAge : dateAge);
  const hasAge = Number.isFinite(age);
  // The producer treats only current-session data (age 0) as executable.
  // Future and malformed ages are also fail-closed rather than assumed fresh.
  const stale = !hasAge || age !== 0 || claimedCurrentDateConflict;
  payload.data_age_days = hasAge ? age : "";
  // Producer freshness is fail-closed: an objectively stale age wins over any
  // contradictory freshness flag carried by an older or malformed payload.
  payload.freshness_block = stale ? "YES" : (payload.freshness_block || "NO");
  payload.freshness_status = stale ? "STALE_BLOCK" : (payload.freshness_status || "LIVE_OR_CURRENT");
  payload.freshness_plan = stale
    ? (claimedCurrentDateConflict
      ? `Execution blocked: data_date ${isoDateOnly(dataDate)} contradicts claimed data_age_days=0; refresh live data before acting.`
      : `Execution blocked: market data is ${hasAge ? age : "unknown"} day(s) old; refresh live data before acting.`)
    : (payload.freshness_plan || "Data freshness is acceptable for scanner use.");

  if (stale) {
    appendReasonCode(payload, "data_stale_block");
    if (claimedCurrentDateConflict) appendReasonCode(payload, "data_age_date_contradiction");
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
      payload.next_day_bias = "EXECUTION BLOCKED";
      payload.next_day_plan = payload.freshness_plan;
      output.notes = [output.notes, payload.freshness_plan].filter(Boolean).join("; ");
    }
  }

  output.payload = payload;
  return output;
}

function applyFillabilityFallback(output) {
  if (!['BUY CANDIDATE', 'STRONG CONTINUATION'].includes(output.action)) return output;
  const payload = output.payload && typeof output.payload === 'object' ? { ...output.payload } : {};
  const state = String(payload.execution_fill_state || '').toUpperCase();
  const probability = Number(payload.execution_fill_probability);
  const proven = state === 'VALIDATED' && Number.isFinite(probability) && probability >= 0.45;
  if (!proven) {
    output.action = 'SETUP FORMING';
    payload.signal_stage = 'SETUP';
    payload.buy_tier = 'SETUP ONLY';
    payload.execution_priority = 4;
    payload.execution_fill_state = state || 'INSUFFICIENT';
    payload.adjusted_score = capScore(payload.adjusted_score ?? output.adjusted_score ?? output.score, 79);
    output.adjusted_score = payload.adjusted_score;
    payload.next_day_plan = state === 'LOW'
      ? 'Comparable entry plans were filled too rarely; keep this as a setup.'
      : 'Entry fillability is not yet proven; keep this as a setup.';
    payload.execution_plan = payload.next_day_plan;
    appendReasonCode(payload, state === 'LOW' ? 'fillability_below_threshold' : 'fillability_evidence_insufficient');
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

function rowDto(row, options = {}) {
  const output = {};
  [...new Set([...SNAPSHOT_FIELDS, ...HISTORY_FIELDS])].forEach((field) => {
    if (field !== "payload" && row?.[field] !== undefined) output[field] = row[field];
  });
  output.payload = cleanPayload(row);
  if (options.historical) {
    return promotePayloadFields(
      applyBuyTierFallback(antiSignalFallback(applyVolatilityGate(applyOperatorStateFallback(output), row)))
    );
  }
  return promotePayloadFields(
    applyBuyTierFallback(antiSignalFallback(applyFillabilityFallback(applyFreshnessFallback(applyOperatorStateFallback(applyAuditGateFallback(applyVolatilityGate(applyPersonalitySetupGate(output, row), row), row))))))
  );
}

function runDto(row) {
  if (!row) return null;
  const output = {};
  [...RUN_FIELDS, ...RUN_OPTIONAL_FIELDS].forEach((field) => {
    if (field !== "payload" && row[field] !== undefined) output[field] = row[field];
  });
  const payload = row.payload && typeof row.payload === "object" ? row.payload : {};
  RUN_OPTIONAL_FIELDS.forEach((field) => {
    if (output[field] === undefined && payload[field] !== undefined) output[field] = payload[field];
  });
  const failedSymbols = Array.isArray(payload.failed_symbols)
    ? payload.failed_symbols
    : (Array.isArray(payload.failures) ? payload.failures : []);
  output.payload = {
    data_provider_counts: payload.data_provider_counts && typeof payload.data_provider_counts === "object" ? payload.data_provider_counts : {},
    data_provider_priority: Array.isArray(payload.data_provider_priority) ? payload.data_provider_priority : [],
    failed_symbols: failedSymbols.slice(0, 25),
    stale_cache_fallbacks: Array.isArray(payload.stale_cache_fallbacks) ? payload.stale_cache_fallbacks.slice(0, 25) : [],
    stale_execution_blocks: Number(payload.stale_execution_blocks || 0),
    signal_outcomes: payload.signal_outcomes && typeof payload.signal_outcomes === "object" ? payload.signal_outcomes : {},
    max_execution_data_age_days: Number(payload.max_execution_data_age_days || 0),
    publication_id: String(payload.publication_id || ""),
    sync_state: String(payload.sync_state || ""),
    storage: payload.storage && typeof payload.storage === "object" ? payload.storage : {},
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

function committedPublicationMatches(run, rows) {
  if (!run || !["ok", "degraded"].includes(String(run.status || ""))) return false;
  if (String(run.payload?.sync_state || "") !== "complete") return false;
  const publicationId = String(run.payload?.publication_id || "");
  if (!publicationId || !Array.isArray(rows) || rows.length === 0) return false;
  return rows.every((row) => String(row?.publication_id || row?.payload?.publication_id || "") === publicationId);
}

async function recentRunDates(limit = 2) {
  const dates = [];
  const addDate = (row) => {
    if (row.run_date && !dates.includes(row.run_date)) dates.push(row.run_date);
  };

  try {
    // A run is publishable only after scanner, snapshot, history, and outcome
    // writes have all completed. Rows left in publishing/sync_failed state are
    // intentionally invisible to the production API.
    const runRows = await supabaseSelect(`watchlist_refresh_runs?select=run_date,status&status=in.(ok,degraded)&order=run_date.desc,created_at.desc&limit=${Math.max(limit * 6, 12)}`);
    runRows.forEach(addDate);
    return dates.slice(0, limit);
  } catch {
    // Fail closed. Published Pages data is the only safe fallback when the
    // commit-marker table cannot be read.
    return [];
  }
}

async function runInfo(runDate) {
  if (!runDate) return null;
  try {
    const rows = await supabaseSelect(`watchlist_refresh_runs?select=${selectList([...RUN_FIELDS, ...RUN_OPTIONAL_FIELDS])}&run_date=eq.${encodeFilterValue(runDate)}&status=in.(ok,degraded)&order=created_at.desc&limit=1`);
    return runDto(rows[0]);
  } catch {
    try {
      const rows = await supabaseSelect(`watchlist_refresh_runs?select=${selectList(RUN_FIELDS)}&run_date=eq.${encodeFilterValue(runDate)}&status=in.(ok,degraded)&order=created_at.desc&limit=1`);
      return runDto(rows[0]);
    } catch {
      return null;
    }
  }
}

module.exports = {
  committedPublicationMatches,
  encodeFilterValue,
  HISTORY_FIELDS,
  isValidTicker,
  normalizeTicker,
  recentRunDates,
  rowDto,
  RUN_FIELDS,
  RUN_OPTIONAL_FIELDS,
  runDto,
  runInfo,
  selectList,
  SNAPSHOT_FIELDS,
  sortRows,
  supabaseRequest,
  supabaseSelect,
};
