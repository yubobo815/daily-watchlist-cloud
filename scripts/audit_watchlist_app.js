const { staticLatestPayload, staticTickerPayload } = require("../api/_static_data");
const { rowDto, runDto } = require("../api/_supabase");
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
  const nonStaticRows = payload.rows.filter((row) => row.payload?.data_provider !== "static_bundle");
  const unblockedStaticRows = payload.rows.filter((row) => row.payload?.freshness_block !== "YES");

  assert(missingGates.length === 0, `static fallback rows missing gate payloads: ${missingGates.length}`);
  assert(unsafeBuys.length === 0, `static fallback exposes ungated BUY-like rows: ${unsafeBuys.length}`);
  assert(overRankedMissingGates.length === 0, `static fallback over-ranks missing-gate rows: ${overRankedMissingGates.length}`);
  assert(nonStaticRows.length === 0, `static fallback rows must identify bundled source: ${nonStaticRows.length}`);
  assert(unblockedStaticRows.length === 0, `static fallback rows must block execution: ${unblockedStaticRows.length}`);
  assert(Number(payload.runInfo.payload?.stale_execution_blocks || 0) === payload.rows.length, "static fallback run health must count all rows as execution-blocked");

  return {
    rows: payload.rows.length,
    missingGates: missingGates.length,
    unsafeBuys: unsafeBuys.length,
    overRankedMissingGates: overRankedMissingGates.length,
    staleExecutionBlocks: payload.runInfo.payload.stale_execution_blocks,
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
      operator_state: "ACCUMULATION",
      operator_state_score: 72,
      operator_state_plan: "Buyers are absorbing supply; prefer controlled pullback or reclaim entries.",
      bull_trap_score: 0,
      bear_trap_score: 32,
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
      learning_sample_count: 12,
      learning_scope: "action/setup family",
      learning_key_used: "BUY CANDIDATE|BREAKOUT BUY|ANY|ANY",
      data_provider: "polygon",
      data_provider_status: "LIVE_OK",
      data_provider_latency_ms: 180,
    },
  });
  assert(gated.action === "BUY CANDIDATE", "execution-gated BUY row must be preserved");
  assert(allGatesAllow(gated), "execution-gated BUY row must carry ALLOW gates");
  assert(gated.payload.next_day_bias === "BULLISH CONFIRM", "execution-gated BUY row must keep next-day bias");
  assert(gated.payload.operator_pressure === "ACCUMULATION / ABSORPTION", "execution-gated BUY row must keep operator-pressure read");
  assert(gated.payload.operator_state === "ACCUMULATION", "execution-gated BUY row must keep operator-state read");
  assert(gated.payload.absorption_score === 72, "execution-gated BUY row must keep absorption score");
  assert(gated.payload.buy_tier === "A+ BUY", "execution-gated BUY row must keep execution tier");
  assert(gated.payload.freshness_block === "NO", "execution-gated BUY row must keep freshness gate state");
  assert(gated.payload.feedback_quality === "WORKING", "execution-gated BUY row must keep feedback state");
  assert(gated.payload.learning_scope === "action/setup family", "execution-gated row must keep learning scope");
  assert(gated.payload.learning_key_used === "BUY CANDIDATE|BREAKOUT BUY|ANY|ANY", "execution-gated row must keep learning key");
  assert(gated.payload.data_provider === "polygon", "execution-gated BUY row must keep data provider");
  assert(gated.payload.data_provider_status === "LIVE_OK", "execution-gated BUY row must keep data provider status");

  const antiBullTrap = rowDto({
    ticker: "TRAP",
    data_date: new Date().toISOString().slice(0, 10),
    action: "BUY CANDIDATE",
    setup: "BREAKOUT BUY",
    score: 112,
    payload: {
      adjusted_score: 118,
      market_permission: "ALLOW",
      risk_permission: "ALLOW",
      next_day_bias: "BULLISH CONFIRM",
      next_day_bias_score: 84,
      operator_pressure: "DISTRIBUTION",
      operator_pressure_score: 70,
      operator_state: "BULL_TRAP",
      operator_state_score: 76,
      bull_trap_score: 76,
      distribution_score: 62,
      absorption_score: 12,
      freshness_status: "LIVE_OR_CURRENT",
      freshness_block: "NO",
      data_age_days: 0,
      buy_tier: "A+ BUY",
      execution_priority: 1,
    },
  });
  assert(antiBullTrap.action === "SETUP FORMING", "anti-signal bull-trap BUY row must be downgraded");
  assert(antiBullTrap.payload.anti_signal_level === "BLOCK", "anti-signal bull-trap row must carry BLOCK level");
  assert(antiBullTrap.payload.buy_tier === "SETUP ONLY", "anti-signal bull-trap row must not keep A+ BUY tier");
  assert(Number(antiBullTrap.payload.execution_priority) >= 4, "anti-signal bull-trap row must drop execution priority");
  assert(adjustedScore(antiBullTrap) <= 49, "anti-signal bull-trap row must be capped below actionable rank");

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
    gatedProvider: gated.payload.data_provider,
    antiBullTrapAction: antiBullTrap.action,
    antiBullTrapLevel: antiBullTrap.payload.anti_signal_level,
    antiBullTrapTier: antiBullTrap.payload.buy_tier,
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

function auditRunHealthProviderPayload() {
  const run = {
    run_date: "2026-06-12",
    status: "ok",
    live_access_ok: true,
    payload: {
      data_provider_counts: { polygon: 185, twelvedata: 3 },
      data_provider_priority: ["polygon", "twelvedata", "stooq", "yahoo"],
      failures: [{ ticker: "FAIL", error: "provider timeout" }],
      stale_execution_blocks: 0,
    },
  };
  const dto = runDto(run);
  assert(dto.payload.data_provider_counts.polygon === 185, "run health must expose provider counts");
  assert(dto.payload.data_provider_priority.includes("stooq"), "run health must expose provider priority");
  assert(dto.payload.failed_symbols[0]?.ticker === "FAIL", "run health must expose Python failures as failed symbols");
  return dto.payload;
}

const result = {
  staticFallback: auditStaticFallback(),
  staticTickerFallback: auditStaticTickerFallback(["AVGO", "CRWV", "ZM", "MU"]),
  supabaseFallback: auditSupabaseFallback(),
  runHealthProviders: auditRunHealthProviderPayload(),
  tickerDetailMerge: auditTickerDetailMerge(),
};

console.log(JSON.stringify(result, null, 2));
