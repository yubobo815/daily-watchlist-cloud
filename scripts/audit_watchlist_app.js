const { staticLatestPayload, staticTickerPayload } = require("../api/_static_data");
const { rowDto, runDto } = require("../api/_supabase");
const { mergeSnapshotIntoLatestHistory } = require("../api/ticker/[ticker]");
const fs = require("fs");

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

function normaliseSearchTicker(value) {
  return String(value || "").trim().toUpperCase().replace("BRK.B", "BRK-B");
}

function tickerSearchAliases(row) {
  const ticker = normaliseSearchTicker(row?.ticker);
  if (!ticker) return [];
  return [...new Set([ticker, ticker.replace("-", ".")].filter(Boolean))];
}

function exactTickerSearchNeedle(query, rows) {
  const ticker = normaliseSearchTicker(query);
  if (!ticker || !/^[A-Z0-9.-]{1,8}$/.test(ticker)) return "";
  return rows.some((row) => tickerSearchAliases(row).includes(ticker)) ? ticker : "";
}

function auditSearchBehavior() {
  const source = fs.readFileSync("assets/app.js", "utf8");
  assert(source.includes("function exactTickerSearchNeedle"), "watchlist search must include exact ticker matching");
  assert(source.includes("rowMatchesSearch(row, state.query, exactTickerNeedle)"), "watchlist render must use ticker-aware search matching");

  const rows = staticLatestPayload().rows || [];
  const muNeedle = exactTickerSearchNeedle("MU", rows);
  const muMatches = rows.filter((row) => tickerSearchAliases(row).includes(muNeedle)).map((row) => row.ticker);
  const micronMatches = rows.filter((row) => String(row.name || "").toLowerCase().includes("micron")).map((row) => row.ticker);

  assert(muNeedle === "MU", "MU query must resolve to exact ticker search");
  assert(muMatches.length === 1 && muMatches[0] === "MU", `MU exact search must only match MU, got ${muMatches.join(",")}`);
  assert(micronMatches.includes("MU"), "company-name search for Micron must still find MU");

  return {
    muNeedle,
    muMatches,
    micronMatches,
  };
}

function auditDecisionFunnelUi() {
  const appSource = fs.readFileSync("assets/app.js", "utf8");
  const pageSource = fs.readFileSync("index.html", "utf8");
  const tickerSource = fs.readFileSync("ticker.html", "utf8");
  assert(appSource.includes("function executionQueues(counts)"), "watchlist must render execution queues");
  assert(appSource.includes('state.filter === "building"'), "BUILDING queue must retain Trending, Building, and Watch rows");
  assert(appSource.includes('state.filter === "risk"'), "RISK queue must retain Exit and Avoid rows");
  assert(pageSource.includes('id="market-activity"'), "secondary market activity must have a navigable target");
  assert(appSource.includes("target.open = true"), "Activity navigation must open the details drawer before scrolling");
  assert(appSource.includes("function renderTickerDetailPanel"), "desktop watchlist must expose an in-place ticker execution panel");
  assert(appSource.includes("Confirm any BUY on the TradingView Pine chart before acting."), "ticker panel must retain the Pine confirmation boundary");
  assert(pageSource.includes('id="ticker-detail-panel"'), "watchlist page must provide the selected ticker panel mount");
  assert(tickerSource.includes("dark-ledger-20260716"), "ticker detail must load the current shared application bundle");
  assert(pageSource.includes('data-mobile-filter="building"'), "mobile Building filter must use the aggregate queue");
  assert(pageSource.includes('data-mobile-filter="risk"'), "mobile Risk filter must use the aggregate queue");
  assert(!appSource.includes('if (state.query.trim()) state.filter = "all"'), "search must preserve the selected decision queue");
  return { executionQueues: 3, activityTarget: "market-activity" };
}

function auditStorageGuard() {
  const workflow = fs.readFileSync(".github/workflows/daily-watchlist-pages.yml", "utf8");
  assert(workflow.includes("cancel-in-progress: false"), "refresh must not cancel a run before retention cleanup");
  assert(workflow.includes("storage_hard_limit_bytes=250000000"), "database hard cap must be 250,000,000 bytes");
  assert(workflow.includes("delete from public.watchlist_snapshots"), "SQL fallback must retain snapshots");
  assert(workflow.includes("delete from public.watchlist_refresh_runs"), "SQL fallback must retain refresh runs");
  assert(workflow.includes("where run_date <> date '$current_run_date'"), "replay retention must target the verified current run");
  return { hardCapBytes: 250000000 };
}

function auditPartialRunStatus() {
  const scanner = fs.readFileSync("daily_watchlist_overview.py", "utf8");
  assert(scanner.includes("not live_access_ok or stale_cache_fallbacks or failures"), "partial ticker failures must mark a daily refresh degraded");
  return { partialFailures: "degraded" };
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
  assert(gated.learning_sample_count === 12, "execution-gated row must promote learning sample count to top level");
  assert(gated.learning_scope === "action/setup family", "execution-gated row must promote learning scope to top level");
  assert(gated.learning_key_used === "BUY CANDIDATE|BREAKOUT BUY|ANY|ANY", "execution-gated row must promote learning key to top level");
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

function auditHistoricalReplayDto() {
  const oldSetup = {
    ticker: "ORCL",
    run_date: "2026-06-13",
    history_date: "2026-05-28",
    action: "BUY CANDIDATE",
    setup: "BREAKOUT BUY",
    score: 96,
    open: 194.2,
    high: 205.4,
    low: 193.8,
    close: 203.7,
    payload: {
      adjusted_score: 96,
      signal_quality: "FRESH",
      transition_label: "Fresh Setup To Buy",
      next_day_bias: "BULLISH CONFIRM",
      next_day_plan: "Confirm on Pine chart before acting.",
      reason_codes: ["next_day_bullish_confirm"],
      buyer_score: 90,
      seller_score: 5,
      operator_state: "ACCUMULATION",
      operator_pressure: "ACCUMULATION / ABSORPTION",
      bull_trap_score: 0,
      distribution_score: 6,
    },
  };

  const historical = rowDto(oldSetup, { historical: true });
  assert(historical.action === "BUY CANDIDATE", "historical replay BUY row must preserve its original action");
  assert(historical.payload.signal_quality === "FRESH", "historical replay row must preserve original quality");
  assert(historical.payload.transition_label === "Fresh Setup To Buy", "historical replay row must preserve transition label");
  assert(historical.payload.next_day_bias === "BULLISH CONFIRM", "historical replay row must not be current-date execution-blocked");
  assert(historical.open === 194.2 && historical.high === 205.4 && historical.low === 193.8, "historical replay row must expose OHLC for entry/stop audit");
  assert(!historical.payload.reason_codes.includes("data_stale_block"), "historical replay row must not add stale-data reason");
  assert(!historical.payload.reason_codes.includes("missing_execution_proof"), "historical replay row must not add execution-proof reason");

  const current = rowDto(oldSetup);
  assert(current.action === "SETUP FORMING", "current DTO must still downgrade stale/missing-proof BUY rows");
  assert(current.payload.signal_quality === "STALE DATA", "current DTO must still mark old current rows stale");
  assert(current.payload.next_day_bias === "EXECUTION BLOCKED", "current DTO must still block stale execution");
  assert(current.payload.reason_codes.includes("data_stale_block"), "current DTO must still add stale-data reason");
  assert(current.payload.reason_codes.includes("missing_execution_proof"), "current DTO must still add execution-proof reason");

  return {
    historicalAction: historical.action,
    historicalQuality: historical.payload.signal_quality,
    historicalBias: historical.payload.next_day_bias,
    currentAction: current.action,
    currentQuality: current.payload.signal_quality,
    currentBias: current.payload.next_day_bias,
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
    learning_history_rows: 5640,
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
  assert(dto.learning_history_rows === 5640, "run health must expose learning history row count");

  const payloadOnlyDto = runDto({
    run_date: "2026-06-12",
    status: "ok",
    payload: {
      learning_history_rows: 5640,
    },
  });
  assert(payloadOnlyDto.learning_history_rows === 5640, "run health must recover optional learning rows from payload");
  return dto.payload;
}

const result = {
  staticFallback: auditStaticFallback(),
  staticTickerFallback: auditStaticTickerFallback(["AVGO", "CRWV", "ZM", "MU"]),
  supabaseFallback: auditSupabaseFallback(),
  historicalReplayDto: auditHistoricalReplayDto(),
  searchBehavior: auditSearchBehavior(),
  decisionFunnelUi: auditDecisionFunnelUi(),
  storageGuard: auditStorageGuard(),
  partialRunStatus: auditPartialRunStatus(),
  runHealthProviders: auditRunHealthProviderPayload(),
  tickerDetailMerge: auditTickerDetailMerge(),
};

console.log(JSON.stringify(result, null, 2));
