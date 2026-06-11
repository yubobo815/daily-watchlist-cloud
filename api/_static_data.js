const latestData = require("../data/latest.json");
const historyData = require("../data/history.json");

const AUDIT_GATE_FIELDS = ["market_permission", "ticker_permission", "walk_forward_permission", "risk_permission"];
const UNGATED_SCORE_CAP = 49;

function normalizeTicker(value) {
  return String(value || "").trim().toUpperCase().replace("BRK.B", "BRK-B");
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

function conservativeFallbackRow(row) {
  const next = { ...(row || {}) };
  const payload = next.payload && typeof next.payload === "object" ? { ...next.payload } : {};
  const hasAllGates = AUDIT_GATE_FIELDS.every((field) => hasKnownAuditGate(next[field] || payload[field]));
  if (!hasAllGates) {
    payload.market_permission = payload.market_permission || next.market_permission || "UNKNOWN";
    payload.ticker_permission = payload.ticker_permission || next.ticker_permission || "UNKNOWN";
    payload.walk_forward_permission = payload.walk_forward_permission || next.walk_forward_permission || "UNKNOWN";
    payload.risk_permission = payload.risk_permission || next.risk_permission || "UNKNOWN";
    payload.audit_gate_status = "MISSING";
    payload.signal_quality = "STATIC FALLBACK - NEEDS GATE PROOF";
    payload.transition_label = "Needs Gate Proof";
    payload.transition_score = capScore(payload.transition_score ?? next.transition_score ?? -25, -25);
    payload.adjusted_score = capScore(payload.adjusted_score ?? next.adjusted_score ?? next.score);
    next.adjusted_score = capScore(next.adjusted_score ?? payload.adjusted_score ?? next.score);
    next.score = capScore(next.score);
    appendReasonCode(payload, "missing_audit_gates");
    next.notes = [next.notes, "Static fallback lacks current audit-gate proof"].filter(Boolean).join("; ");
    if (next.action === "BUY CANDIDATE" || next.action === "STRONG CONTINUATION") {
      next.action = "SETUP FORMING";
      payload.signal_stage = "SETUP";
    }
  }
  next.payload = payload;
  return next;
}

function staticLatestPayload() {
  const rows = Array.isArray(latestData.rows) ? latestData.rows.map(conservativeFallbackRow) : [];
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
  const rows = Array.isArray(latestData.rows) ? latestData.rows.map(conservativeFallbackRow) : [];
  const snapshot = rows.find((row) => normalizeTicker(row.ticker) === normalized) || null;
  const rawHistoryRows = Array.isArray(historyData.by_ticker?.[normalized])
    ? historyData.by_ticker[normalized]
    : (Array.isArray(historyData.rows) ? historyData.rows.filter((row) => normalizeTicker(row.ticker) === normalized) : []);
  const historyRows = rawHistoryRows.map(conservativeFallbackRow);
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
