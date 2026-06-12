const { staticLatestPayload, staticTickerPayload } = require("../api/_static_data");
const { rowDto } = require("../api/_supabase");
const { mergeSnapshotIntoLatestHistory } = require("../api/ticker/[ticker]");

const REQUIRED_GATES = [
  "market_permission",
  "risk_permission",
];

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function gateValues(row) {
  const payload = row.payload || {};
  return REQUIRED_GATES.map((field) => row[field] || payload[field] || "");
}

function isBuyLike(row) {
  return row.action === "BUY CANDIDATE" || row.action === "STRONG CONTINUATION";
}

function allGatesAllow(row) {
  return gateValues(row).every((value) => value === "ALLOW");
}

function hasMissingGate(row) {
  return gateValues(row).some((value) => !value || value === "UNKNOWN");
}

function adjustedScore(row) {
  return Number(row.adjusted_score ?? row.payload?.adjusted_score ?? row.score ?? 0);
}

function auditStaticFallback() {
  const payload = staticLatestPayload();
  assert(Array.isArray(payload.rows), "static fallback rows must be an array");
  assert(payload.rows.length > 0, "static fallback must include rows");

  const missingGates = payload.rows.filter((row) => gateValues(row).some((value) => !value));
  const unsafeBuys = payload.rows.filter((row) => isBuyLike(row) && !allGatesAllow(row));
  const overRankedMissingGates = payload.rows.filter((row) => hasMissingGate(row) && adjustedScore(row) > 49);

  assert(missingGates.length === 0, `static fallback rows missing gate payloads: ${missingGates.length}`);
  assert(unsafeBuys.length === 0, `static fallback exposes ungated BUY-like rows: ${unsafeBuys.length}`);
  assert(overRankedMissingGates.length === 0, `static fallback over-ranks missing-gate rows: ${overRankedMissingGates.length}`);

  return {
    rows: payload.rows.length,
    missingGates: missingGates.length,
    unsafeBuys: unsafeBuys.length,
    overRankedMissingGates: overRankedMissingGates.length,
  };
}

function auditStaticTickerFallback(tickers) {
  let historyRows = 0;
  let unsafeBuys = 0;
  let overRankedMissingGates = 0;

  tickers.forEach((ticker) => {
    const payload = staticTickerPayload(ticker);
    assert(payload.snapshot, `static ticker fallback must include a snapshot for ${ticker}`);
    const rows = payload.historyRows || [];
    historyRows += rows.length;
    unsafeBuys += rows.filter((row) => isBuyLike(row) && !allGatesAllow(row)).length;
    overRankedMissingGates += rows.filter((row) => hasMissingGate(row) && adjustedScore(row) > 49).length;
  });

  assert(unsafeBuys === 0, `static ticker fallback exposes ungated BUY-like history rows: ${unsafeBuys}`);
  assert(overRankedMissingGates === 0, `static ticker fallback over-ranks missing-gate history rows: ${overRankedMissingGates}`);

  return {
    tickers: tickers.length,
    historyRows,
    unsafeBuys,
    overRankedMissingGates,
  };
}

function auditSupabaseFallback() {
  const legacy = rowDto({
    ticker: "TEST",
    action: "BUY CANDIDATE",
    setup: "BREAKOUT BUY",
    score: 99,
    payload: {
      adjusted_score: 128,
      signal_quality: "FRESH",
      transition_label: "Fresh Setup To Buy",
      transition_score: 35,
    },
  });
  assert(legacy.action === "SETUP FORMING", "legacy missing-execution BUY row must be downgraded");
  assert(gateValues(legacy).every((value) => value === "UNKNOWN"), "legacy row must carry UNKNOWN execution gates");
  assert(adjustedScore(legacy) <= 49, "legacy missing-execution row must be capped below actionable rank");
  assert(legacy.payload.signal_quality === "NEEDS EXECUTION PROOF", "legacy missing-execution row must not keep FRESH quality");
  assert(legacy.payload.transition_label === "Needs Execution Proof", "legacy missing-execution row must not keep promotion transition");

  const unknownGated = rowDto({
    ticker: "TEST",
    action: "SETUP FORMING",
    setup: "MOMENTUM BUY",
    score: 91,
    payload: {
      adjusted_score: 128,
      signal_quality: "FRESH",
      transition_label: "Fresh Setup To Buy",
      market_permission: "UNKNOWN",
      risk_permission: "UNKNOWN",
    },
  });
  assert(adjustedScore(unknownGated) <= 49, "UNKNOWN execution-gate row must be capped below actionable rank");
  assert(unknownGated.payload.signal_quality === "NEEDS EXECUTION PROOF", "UNKNOWN execution-gate row must not keep FRESH quality");
  assert(unknownGated.payload.transition_label === "Needs Execution Proof", "UNKNOWN execution-gate row must not keep promotion transition");

  const gated = rowDto({
    ticker: "TEST",
    data_date: new Date().toISOString().slice(0, 10),
    action: "BUY CANDIDATE",
    setup: "BREAKOUT BUY",
    score: 99,
    payload: {
      market_permission: "ALLOW",
      risk_permission: "ALLOW",
      next_day_bias: "BULLISH CONFIRM",
      next_day_bias_score: 82,
      next_day_plan: "Confirm on Pine chart; prefer entry near the reference zone with the listed stop.",
      operator_pressure: "ACCUMULATION / ABSORPTION",
      operator_pressure_score: 18,
      operator_plan: "Buyers are absorbing supply; watch pullback or reclaim entries near the reference zone.",
      distribution_score: 6,
      absorption_score: 72,
      short_pressure_proxy: 0,
      squeeze_watch: "NO",
      buy_tier: "A+ BUY",
      execution_priority: 1,
      freshness_status: "LIVE_OR_CURRENT",
      freshness_block: "NO",
      data_age_days: 1,
      feedback_quality: "WORKING",
      feedback_return_pct: 4.2,
      feedback_max_drawdown_pct: -1.1,
      feedback_stop_hit: "NO",
    },
  });
  assert(gated.action === "BUY CANDIDATE", "execution-gated BUY row must be preserved");
  assert(allGatesAllow(gated), "execution-gated BUY row must carry ALLOW gates");
  assert(gated.payload.next_day_bias === "BULLISH CONFIRM", "execution-gated BUY row must keep next-day bias");
  assert(gated.payload.operator_pressure === "ACCUMULATION / ABSORPTION", "execution-gated BUY row must keep operator-pressure read");
  assert(gated.payload.absorption_score === 72, "execution-gated BUY row must keep absorption score");
  assert(gated.payload.buy_tier === "A+ BUY", "execution-gated BUY row must keep execution tier");
  assert(gated.payload.freshness_block === "NO", "execution-gated BUY row must keep freshness gate state");
  assert(gated.payload.feedback_quality === "WORKING", "execution-gated BUY row must keep feedback state");

  return {
    legacyAction: legacy.action,
    legacyGates: gateValues(legacy),
    legacyAdjustedScore: adjustedScore(legacy),
    legacyQuality: legacy.payload.signal_quality,
    legacyTransition: legacy.payload.transition_label,
    unknownGatedAdjustedScore: adjustedScore(unknownGated),
    unknownGatedQuality: unknownGated.payload.signal_quality,
    gatedAction: gated.action,
    gatedGates: gateValues(gated),
  };
}

function auditTickerDetailMerge() {
  const merged = mergeSnapshotIntoLatestHistory(
    {
      ticker: "TEST",
      action: "EXIT PRESSURE",
      adjusted_score: undefined,
      payload: {
        adjusted_score: 12.7,
        signal_quality: "EXIT RISK",
        market_permission: "ALLOW",
        ticker_permission: "CAUTION",
        walk_forward_permission: "NONE",
        risk_permission: "ALLOW",
      },
    },
    {
      ticker: "TEST",
      action: "WAIT",
      adjusted_score: 0,
      history_date: "2026-06-10",
      payload: {
        adjusted_score: 0,
        signal_quality: "NEEDS EXECUTION PROOF",
        market_permission: "UNKNOWN",
        ticker_permission: "UNKNOWN",
        walk_forward_permission: "UNKNOWN",
        risk_permission: "UNKNOWN",
      },
    }
  );

  assert(merged.action === "EXIT PRESSURE", "ticker detail latest row must use snapshot action");
  assert(merged.adjusted_score === 12.7, "ticker detail latest row top-level score must match snapshot adjusted score");
  assert(merged.payload.signal_quality === "EXIT RISK", "ticker detail latest row must use snapshot quality");
  assert(gateValues(merged).join(",") === "ALLOW,ALLOW", "ticker detail latest row must use snapshot execution gates");

  return {
    action: merged.action,
    adjustedScore: merged.adjusted_score,
    quality: merged.payload.signal_quality,
    gates: gateValues(merged),
  };
}

const result = {
  staticFallback: auditStaticFallback(),
  staticTickerFallback: auditStaticTickerFallback(["AVGO", "CRWV", "ZM", "MU"]),
  supabaseFallback: auditSupabaseFallback(),
  tickerDetailMerge: auditTickerDetailMerge(),
};

console.log(JSON.stringify(result, null, 2));
