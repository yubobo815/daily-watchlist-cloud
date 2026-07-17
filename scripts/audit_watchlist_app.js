const { conservativeFallbackRow, staticLatestPayload, staticTickerPayload } = require("../api/_static_data");
const { publishedLatestPayload, publishedTickerPayload } = require("../api/_published_data");
const { committedPublicationMatches, rowDto, runDto } = require("../api/_supabase");
const { mergeSnapshotIntoLatestHistory } = require("../api/ticker/[ticker]");
const { latestCompletedMarketSession, marketSessionAge, previousMarketSession } = require("../api/_market_session");
const fs = require("fs");

const REQUIRED_GATES = [
  "market_permission",
  "ticker_permission",
  "walk_forward_permission",
  "risk_permission",
];

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
  const activityTag = pageSource.match(/<details\s+[^>]*id=["']market-activity["'][^>]*>/i)?.[0] || "";
  assert(activityTag, "market activity must remain a details element");
  assert(!/\sopen(?:\s|=|>)/i.test(activityTag), "market activity must be collapsed by default");
  assert(appSource.includes("target.open = true"), "Activity navigation must open the details drawer before scrolling");
  const stylesSource = fs.readFileSync("assets/styles.css", "utf8");
  assert(stylesSource.includes("#market-activity[open] > summary"), "open market activity must have a scoped surface treatment");
  assert(stylesSource.includes("#market-activity .focus-item"), "market activity cards must use scoped palette overrides");
  assert(stylesSource.includes("#market-activity .focus-unlock input"), "saved-name controls must use the shared light palette");
  assert(appSource.includes("function renderTickerDetailPanel"), "desktop watchlist must expose an in-place ticker scanner review panel");
  assert(!appSource.includes("Confirm any BUY on the TradingView Pine chart before acting."), "ticker panel must not repeat the removed Pine confirmation copy");
  assert(appSource.includes("function contextSummary(row)"), "ticker context must be summarized in natural language");
  assert(appSource.includes("function predictionNarrative(row)"), "ticker context must explain prediction evidence in natural language");
  assert(appSource.includes("function recentBehaviorSummary(row, previous)"), "recent behavior must be summarized in natural language");
  assert(appSource.includes("function renderQualityScore(row)"), "watchlist quality must distinguish unavailable evidence from a numeric score");
  assert(appSource.includes("function qualityConstraintLabel(row)"), "all quality surfaces must share the same constraint semantics");
  assert(appSource.includes("function qualityDiagnostic(row)"), "ticker diagnostics must separate technical score from adjusted rank");
  assert(appSource.includes('"GATE BLOCK"'), "missing execution evidence must render as a gate block instead of a synthetic number");
  assert(appSource.includes('if (antiSignal === "BLOCK") return "BLOCKED"'), "anti-signal blocks must suppress the numeric quality display");
  assert(!appSource.includes("Trend quality ${fmtConviction(latest)} / 100"), "ticker diagnostics must not present adjusted rank as synthetic trend quality");
  assert(appSource.includes("Context &amp; evidence"), "ticker panel must use the reader-facing context label");
  assert(!appSource.includes("<summary>More context</summary>"), "ticker panel must not expose the old machine-context label");
  assert(pageSource.includes('id="ticker-detail-panel"'), "watchlist page must provide the selected ticker panel mount");
  assert(pageSource.includes("Scanner rank first"), "watchlist sorting must use scanner-review terminology");
  assert(!pageSource.includes("Execution tier first"), "watchlist must not retain execution-tier sorting copy");
  assert(!tickerSource.includes("Execution plan"), "ticker detail must not retain execution-plan copy");
  assert(pageSource.includes("Buy = scanner candidate; chart confirmation required; not trade execution."), "watchlist must show the permanent scanner boundary legend");
  assert(tickerSource.includes("Buy = scanner candidate; chart confirmation required; not trade execution."), "ticker detail must show the permanent scanner boundary legend");
  assert(tickerSource.includes("calm-paper-20260716"), "ticker detail must load the current shared application bundle");
  assert(pageSource.includes('data-mobile-filter="building"'), "mobile Building filter must use the aggregate queue");
  assert(pageSource.includes('data-mobile-filter="risk"'), "mobile Risk filter must use the aggregate queue");
  assert(!appSource.includes('if (state.query.trim()) state.filter = "all"'), "search must preserve the selected decision queue");
  return { executionQueues: 3, activityTarget: "market-activity", scannerLegend: true };
}

function auditMarketSessionFreshness() {
  const thursdayAfterClose = new Date("2026-07-17T02:00:00Z"); // 22:00 Thursday in New York.
  const fridayBeforeClose = new Date("2026-07-17T19:00:00Z");
  const fridayAfterClose = new Date("2026-07-17T20:01:00Z");
  const mondayBeforeClose = new Date("2026-07-20T15:00:00Z");
  const independenceHoliday = new Date("2026-07-03T21:00:00Z");
  const blackFridayAfterEarlyClose = new Date("2026-11-27T18:01:00Z");

  assert(latestCompletedMarketSession(thursdayAfterClose).toISOString().slice(0, 10) === "2026-07-16", "UTC rollover must not advance the completed New York session");
  assert(marketSessionAge("2026-07-16", thursdayAfterClose) === 0, "Thursday close must remain current during Thursday evening in New York");
  assert(marketSessionAge("2026-07-16", fridayBeforeClose) === 0, "prior close must remain current before Friday market close");
  assert(marketSessionAge("2026-07-16", fridayAfterClose) === 1, "prior close must become one session old after Friday market close");
  assert(marketSessionAge("2026-07-17", mondayBeforeClose) === 0, "Friday close must remain current before Monday market close");
  assert(marketSessionAge("2026-07-02", independenceHoliday) === 0, "exchange holiday must not create a phantom completed session");
  assert(marketSessionAge("2026-11-27", blackFridayAfterEarlyClose) === 0, "early-close session must become current after its actual close");
  assert(marketSessionAge("2099-01-01", thursdayAfterClose) === null, "future market dates must fail closed");

  const currentSession = latestCompletedMarketSession().toISOString().slice(0, 10);
  const dto = rowDto({
    ticker: "CURRENT_SESSION",
    data_date: currentSession,
    action: "BUY CANDIDATE",
    score: 96,
    payload: {
      adjusted_score: 96,
      data_age_days: 0,
      freshness_block: "NO",
      market_permission: "ALLOW",
      ticker_permission: "ALLOW",
      walk_forward_permission: "ALLOW",
      risk_permission: "ALLOW",
    },
  });
  assert(dto.payload.data_age_days === 0, "API DTO must agree with the scanner for the latest completed session");
  assert(dto.payload.freshness_block === "NO", "API DTO must not stale-block the latest completed session");
  assert(dto.score === 96 && adjustedScore(dto) === 96, "fresh API DTO must preserve raw and adjusted scores");

  return {
    utcRolloverAge: marketSessionAge("2026-07-16", thursdayAfterClose),
    afterNextCloseAge: marketSessionAge("2026-07-16", fridayAfterClose),
    holidayAge: marketSessionAge("2026-07-02", independenceHoliday),
    currentDtoFreshness: dto.payload.freshness_block,
  };
}

function auditLearningReadoutUi() {
  const source = fs.readFileSync("assets/app.js", "utf8");
  const start = source.indexOf("function payloadValue");
  const end = source.indexOf("function cacheKeyFor");
  assert(start >= 0 && end > start, "learning readout must remain independently testable");
  assert(source.includes("learning_distinct_ticker_count"), "learning readout must surface diversity when present");
  assert(source.includes("learning_evaluation_date_min"), "learning readout must surface date range when present");
  assert(source.includes("entry_model_version"), "learning readout must surface model version when present");
  const learningReadout = new Function("fmtNumber", "fmtSignedNumber", `${source.slice(start, end)}; return learningReadout;`)(
    (value) => String(value),
    (value) => `${Number(value) >= 0 ? "+" : ""}${value}`
  );
  const rich = learningReadout({ action: "BUY CANDIDATE", payload: {
    learning_sample_count: 8, learning_adjustment: 2.4, learning_scope: "exact signal personality",
    learning_distinct_ticker_count: 4, learning_evaluation_date_count: 4,
    learning_evaluation_date_min: "2026-06-01", learning_evaluation_date_max: "2026-07-15",
    learning_window_start: "2026-05-15", learning_window_end: "2026-07-15", entry_model_version: "zone-v2",
    learning_promotion_eligible: true, learning_promotion_state: "PROMOTION_ELIGIBLE",
  } });
  const explicitFalse = learningReadout({ action: "BUY CANDIDATE", payload: {
    learning_sample_count: 8, learning_scope: "exact signal personality", learning_distinct_ticker_count: 4,
    learning_evaluation_date_count: 4, learning_promotion_eligible: false, learning_promotion_state: "PROMOTION_ELIGIBLE",
  } });
  const missingProducerEligibility = learningReadout({ action: "BUY CANDIDATE", payload: {
    learning_sample_count: 12, learning_scope: "exact signal personality", learning_distinct_ticker_count: 8,
    learning_evaluation_date_count: 6, learning_model_version: "zone-v2", learning_promotion_state: "PROMOTION_ELIGIBLE",
  } });
  const missingModelVersion = learningReadout({ action: "BUY CANDIDATE", payload: {
    learning_sample_count: 12, learning_scope: "exact signal personality", learning_distinct_ticker_count: 8,
    learning_evaluation_date_count: 6, learning_promotion_eligible: true,
  } });
  const basic = learningReadout({ action: "BUY CANDIDATE", payload: { learning_sample_count: 3 } });
  assert(rich.includes("4 tickers") && rich.includes("range 2026-06-01 to 2026-07-15"), "learning readout must show diversity and date range");
  assert(rich.includes("window 2026-05-15 to 2026-07-15"), "learning readout must show the learning window when it differs from evaluation bounds");
  assert(rich.includes("model zone-v2") && rich.includes("promotion evidence eligible"), "learning readout must show model and promotion eligibility");
  assert(explicitFalse.includes("reporting-only") && !explicitFalse.includes("promotion evidence eligible"), "explicit false learning promotion eligibility must override inferred eligibility");
  assert(missingProducerEligibility.includes("reporting-only") && !missingProducerEligibility.includes("promotion evidence eligible"), "learning readout must not infer eligibility from counts or promotion state without producer approval");
  assert(missingModelVersion.includes("model version pending") && !missingModelVersion.includes("promotion evidence eligible"), "learning readout must keep promotion pending without a model version");
  assert(!basic.includes("tickers") && !basic.includes("range") && basic.includes("model version pending") && basic.includes("reporting-only"), "learning readout must mark incomplete learning evidence as pending reporting-only");
  return { rich, explicitFalse, missingProducerEligibility, missingModelVersion, basic };
}

function auditStorageGuard() {
  const workflow = fs.readFileSync(".github/workflows/daily-watchlist-pages.yml", "utf8");
  const guard = fs.readFileSync("scripts/database_capacity_guard.sh", "utf8");
  assert(workflow.includes("cancel-in-progress: false"), "refresh must not cancel a run before retention cleanup");
  assert(guard.includes("readonly WARNING_BYTES=175000000"), "preflight must reserve publishing headroom");
  assert(guard.includes("readonly STAGING_LIMIT_BYTES=220000000"), "staged publication must stay below the operational ceiling");
  assert(guard.includes("readonly HARD_LIMIT_BYTES=250000000"), "database hard cap must be 250,000,000 bytes");
  assert(guard.includes("readonly OHLCV_BARS_PER_TICKER=400"), "OHLCV retention must preserve the full model window");
  assert(guard.includes("readonly LEARNING_SESSIONS=60"), "outcome retention must follow the learning window");
  assert(guard.includes("record_storage_metrics"), "each publication must persist database capacity telemetry");
  assert(guard.includes("rollback_publication"), "failed staging must remove its hidden publication");
  assert(!guard.toLowerCase().includes("vacuum full"), "routine capacity correctness must not depend on VACUUM FULL");
  assert(workflow.includes("if: always() && steps.time_gate.outputs.run == 'true'"), "workflow must attempt rollback on every exit path");
  return { warningBytes: 175000000, stagingLimitBytes: 220000000, hardCapBytes: 250000000 };
}

function auditPartialRunStatus() {
  const scanner = fs.readFileSync("daily_watchlist_overview.py", "utf8");
  assert(scanner.includes("not live_access_ok or stale_cache_fallbacks or failures"), "partial ticker failures must mark a daily refresh degraded");
  return { partialFailures: "degraded" };
}

function auditAtomicPublicationContract() {
  const scanner = fs.readFileSync("daily_watchlist_overview.py", "utf8");
  const workflow = fs.readFileSync(".github/workflows/daily-watchlist-pages.yml", "utf8");
  const supabaseApi = fs.readFileSync("api/_supabase.js", "utf8");
  const tickerApi = fs.readFileSync("api/ticker/[ticker].js", "utf8");
  const latestApi = fs.readFileSync("api/watchlist/latest.js", "utf8");
  const healthAudit = fs.readFileSync("scripts/supabase_learning_health.py", "utf8");
  const schema = fs.readFileSync("supabase_schema.sql", "utf8");
  assert(scanner.includes('final_metadata["status"] = "pending_audit"'), "scanner must keep a synced run hidden until database audit passes");
  assert(workflow.indexOf("Audit Supabase learning health") < workflow.indexOf("Enforce staged database ceiling"), "database health audit must precede staged capacity enforcement");
  assert(workflow.indexOf("Enforce staged database ceiling") < workflow.indexOf("Deploy to GitHub Pages"), "an oversized staged publication must roll back before deployment");
  assert(workflow.indexOf("Finalize Supabase publication") < workflow.indexOf("Reclaim Supabase replay storage"), "retention must never mutate a pending publication");
  assert(workflow.indexOf("Deploy to GitHub Pages") < workflow.indexOf("Finalize Supabase publication"), "Supabase publication must not become visible before Pages deployment succeeds");
  assert(workflow.includes("supabase_learning_health.py --finalize"), "workflow must explicitly finalize the audited publication");
  assert(supabaseApi.includes("status=in.(ok,degraded)"), "API must select only validated run states");
  assert(supabaseApi.includes("committedPublicationMatches"), "API must verify immutable publication ids after fetching rows");
  assert(supabaseApi.includes("return [];"), "status-query failures must fail closed instead of selecting raw snapshots");
  assert(tickerApi.includes("recentRunDates(1)"), "ticker detail must share the validated run selector with the main list");
  assert(tickerApi.includes("committedPublicationMatches") && latestApi.includes("committedPublicationMatches"), "list and detail APIs must reject mixed same-day reruns");
  assert(healthAudit.includes('payload->>publication_id=eq.') && healthAudit.includes('status=eq.pending_audit'), "audit promotion must compare-and-set the exact pending publication");
  assert(scanner.includes('outcomes["publication_id"] = publication_id'), "outcomes must be attributable to one immutable publication");
  assert(scanner.includes('publication_id=in.({publication_filter})'), "learning must exclude outcomes from unvalidated publications");
  assert(scanner.includes('["publication_id", "signal_run_date", "evaluation_run_date", "ticker"]'), "outcome upserts must preserve publication versions");
  assert(schema.includes("add primary key (publication_id, ticker)") && schema.includes("add primary key (publication_id, ticker, history_date)"), "snapshot and history staging rows must be versioned by publication");
  assert(latestApi.includes("publication_id=eq.") && tickerApi.includes("publication_id=eq."), "list and detail APIs must select the active validated publication only");
  assert(scanner.includes('"learning_model_version": LEARNING_MODEL_VERSION'), "publication metadata must declare the active learning model");
  assert(scanner.includes('"learning_horizon_sessions": LEARNING_HORIZON_SESSIONS'), "publication metadata must declare the active learning horizon");
  assert(!healthAudit.includes('entry_model_version") or "") == "zone-v2"'), "health audit must not hard-code a stale learning model");
  assert(healthAudit.includes('synced_outcome_rows') && healthAudit.includes('len(outcome_rows)'), "health audit must reconcile the current publication outcome count");
  assert(healthAudit.includes("if finalize and") && healthAudit.includes("--finalize"), "health validation must not expose a publication before explicit finalization");
  assert(healthAudit.includes("invalid_promotions") && healthAudit.includes("directional_validation_safe"), "health audit must reject under-evidenced model activation");
  const committedRun = { status: "ok", payload: { publication_id: "pub-1", sync_state: "complete" } };
  assert(committedPublicationMatches(committedRun, [{ payload: { publication_id: "pub-1" } }]), "matching publication ids must be readable");
  assert(committedPublicationMatches(committedRun, [{ publication_id: "pub-1", payload: {} }]), "compact rows must use the typed publication id");
  assert(!committedPublicationMatches(committedRun, [{ payload: { publication_id: "pub-2" } }]), "mixed same-day publication ids must fail closed");
  assert(!committedPublicationMatches(committedRun, [{ publication_id: "pub-2", payload: {} }]), "mixed compact publication ids must fail closed");
  assert(!committedPublicationMatches({ status: "pending_audit", payload: { publication_id: "pub-1", sync_state: "complete" } }, [{ payload: { publication_id: "pub-1" } }]), "pending audit runs must remain hidden");
  return { pendingStatus: "pending_audit", validatedStatuses: ["ok", "degraded"] };
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

function auditStaticFallbackNormalization() {
  const row = conservativeFallbackRow({
    ticker: "STATIC",
    action: "BUY CANDIDATE",
    score: 98,
    market_permission: "ALLOW",
    ticker_permission: "ALLOW",
    risk_permission: "ALLOW",
    payload: {
      market_permission: "BLOCK",
      ticker_permission: "ALLOW",
      risk_permission: "ALLOW",
      freshness_block: "NO",
      freshness_status: "LIVE_OR_CURRENT",
      data_age_days: 0,
    },
  });

  assert(row.action === "SETUP FORMING", "static fallback must downgrade a contradictory blocked-gate BUY row");
  assert(gateValues(row).every((value) => value === "UNKNOWN"), "static fallback must erase stale gate evidence from both row shapes");
  assert(row.payload.freshness_block === "YES", "static fallback must override freshness_block=NO");
  assert(row.payload.freshness_status === "STATIC_FALLBACK_BLOCK", "static fallback must expose its conservative freshness status");
  assert(row.personality_setup_allowed === "NO" && row.payload.personality_setup_allowed === "NO", "static fallback must explicitly block personality setup promotion");
  assert(adjustedScore(row) <= 49, "static fallback must cap a contradictory blocked-gate BUY row");

  return {
    action: row.action,
    gates: gateValues(row),
    freshnessBlock: row.payload.freshness_block,
    adjustedScore: adjustedScore(row),
  };
}

async function auditBrowserFallbackNormalization() {
  const source = fs.readFileSync("assets/app.js", "utf8");
  const start = source.indexOf("function staticFallbackNumber");
  const end = source.indexOf("async function fetchJsonNoStore");
  assert(start >= 0 && end > start, "browser fallback must define a conservative normalizer");
  const normalizeStaticFallbackRow = new Function(
    "displaySecurityName",
    "STATIC_FALLBACK_SCORE_CAP",
    "STATIC_FALLBACK_GATE_FIELDS",
    `${source.slice(start, end)}; return normalizeStaticFallbackRow;`
  )(
    (name) => name || "",
    49,
    ["market_permission", "ticker_permission", "walk_forward_permission", "risk_permission"]
  );
  const row = normalizeStaticFallbackRow({
    ticker: "BROWSER",
    action: "BUY CANDIDATE",
    score: 98,
    market_permission: "ALLOW",
    ticker_permission: "ALLOW",
    risk_permission: "ALLOW",
    payload: { freshness_block: "NO", market_permission: "BLOCK" },
  }, "2026-07-16");

  assert(row.action === "SETUP FORMING", "browser fallback must downgrade BUY-like actions");
  assert(gateValues(row).every((value) => value === "UNKNOWN"), "browser fallback must remove stale gate evidence");
  assert(row.payload.freshness_block === "YES", "browser fallback must block execution");
  assert(row.personality_setup_allowed === "NO" && row.payload.personality_setup_allowed === "NO", "browser fallback must explicitly block personality setup promotion");
  assert(row.learning_promotion_eligible === false && row.payload.learning_promotion_eligible === false, "browser fallback must fail closed on learning promotion eligibility");
  assert(row.learning_reporting_only === true && row.payload.learning_promotion_state === "REPORTING_ONLY", "browser fallback must explicitly mark learning as reporting-only");
  assert(adjustedScore(row) <= 49, "browser fallback must cap actionable rank");
  assert(source.includes("loadStaticLatestRows") && source.includes("normalizeStaticFallbackRow(row, fallbackRunDate)"), "browser latest fallback must use the normalizer");
  assert(source.includes("loadStaticTickerHistory") && source.includes("normalizeStaticFallbackRow({"), "browser ticker history fallback must use the normalizer");

  const loaderStart = source.indexOf("function staticFallbackRunDate");
  const loaderEnd = source.indexOf("function uniqueHistoryDateCount");
  assert(loaderStart >= 0 && loaderEnd > loaderStart, "browser fallback loader must remain independently testable");
  const loadStaticLatestRows = new Function(
    "fetch",
    "displaySecurityName",
    "STATIC_FALLBACK_SCORE_CAP",
    "STATIC_FALLBACK_GATE_FIELDS",
    "PUBLISHED_LATEST_JSON_URL",
    `${source.slice(loaderStart, loaderEnd)}; return loadStaticLatestRows;`
  )(
    async () => ({
      ok: true,
      json: async () => ({ run_date: "2000-01-01", rows: [{ ticker: "STALE_BROWSER", action: "BUY CANDIDATE", score: 98 }] }),
    }),
    (name) => name || "",
    49,
    ["market_permission", "ticker_permission", "walk_forward_permission", "risk_permission"],
    ""
  );
  const stalePayload = await loadStaticLatestRows();
  assert(stalePayload.rows.length === 1, "stale browser fallback must still render bundled rows");
  assert(stalePayload.rows[0].payload.freshness_status === "STATIC_FALLBACK_BLOCK", "stale browser fallback rows must remain explicitly blocked");

  return {
    action: row.action,
    gates: gateValues(row),
    freshnessBlock: row.payload.freshness_block,
    adjustedScore: adjustedScore(row),
    staleRows: stalePayload.rows.length,
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

function auditStaticLearningEvidenceFallback() {
  const row = conservativeFallbackRow({
    ticker: "STATIC",
    payload: {
      learning_distinct_ticker_count: 8,
      learning_evaluation_date_count: 6,
      learning_evaluation_date_min: "2026-05-01",
      learning_evaluation_date_max: "2026-06-15",
      learning_model_version: "learning-v3",
      learning_promotion_eligible: true,
    },
  });

  assert(row.learning_distinct_ticker_count === 8, "static fallback must expose distinct-ticker learning evidence");
  assert(row.learning_evaluation_date_count === 6, "static fallback must expose evaluation-date learning evidence");
  assert(row.learning_evaluation_date_min === "2026-05-01", "static fallback must expose learning evaluation minimum date");
  assert(row.learning_evaluation_date_max === "2026-06-15", "static fallback must expose learning evaluation maximum date");
  assert(row.learning_model_version === "learning-v3", "static fallback must expose learning model version");
  assert(row.learning_promotion_eligible === false, "static fallback must fail closed on learning promotion eligibility");
  assert(row.payload.learning_promotion_eligible === false, "static fallback payload must fail closed on learning promotion eligibility");
  assert(row.learning_reporting_only === true && row.payload.learning_reporting_only === true, "static fallback must explicitly mark learning as reporting-only");
  assert(row.learning_promotion_state === "REPORTING_ONLY" && row.payload.learning_promotion_state === "REPORTING_ONLY", "static fallback must expose reporting-only promotion state");

  return {
    distinctTickers: row.learning_distinct_ticker_count,
    evaluationDates: row.learning_evaluation_date_count,
    modelVersion: row.learning_model_version,
    promotionEligible: row.learning_promotion_eligible,
  };
}

async function withMockFetch(fetchImpl, callback) {
  const originalFetch = global.fetch;
  global.fetch = fetchImpl;
  try {
    return await callback();
  } finally {
    global.fetch = originalFetch;
  }
}

async function auditPublishedFallbackContract() {
  const learningEvidence = {
    learning_sample_count: 12,
    learning_working_rate: 0.67,
    learning_failed_rate: 0.17,
    learning_trap_avoided_rate: 0.83,
    learning_avg_score: 4.2,
    learning_adjustment: 1.5,
    learning_scope: "exact signal personality",
    learning_key_used: "BUY CANDIDATE|BREAKOUT BUY|BALANCED|ACCUMULATION|NONE",
    learning_plan: "Use the evidence as a reporting input.",
    learning_model_version: "learning-v3",
    learning_distinct_ticker_count: 8,
    learning_evaluation_date_count: 6,
    learning_evaluation_date_min: "2026-06-01",
    learning_evaluation_date_max: "2026-07-15",
    learning_window_start: "2026-06-01",
    learning_window_end: "2026-07-15",
    learning_promotion_eligible: true,
    learning_reporting_only: false,
    learning_promotion_state: "PROMOTION_ELIGIBLE",
  };
  const liveLookingRunInfo = {
    run_date: "2026-07-16",
    status: "ok",
    live_access_ok: true,
    payload: {
      data_provider_counts: { polygon: 2 },
      stale_execution_blocks: 0,
    },
  };
  const latestData = {
    run_date: "2026-07-16",
    runInfo: liveLookingRunInfo,
    rows: [
      { ticker: "PUBLISHED", run_date: "2026-07-16", action: "BUY CANDIDATE", score: 98, payload: learningEvidence },
      { ticker: "SECOND", run_date: "2026-07-16", action: "WATCH TREND", score: 62, payload: {} },
    ],
  };
  const historyData = {
    by_ticker: {
      PUBLISHED: [{ ticker: "PUBLISHED", history_date: "2026-07-15", action: "BUY CANDIDATE", score: 96, payload: learningEvidence }],
    },
  };

  const published = await withMockFetch(async (url) => ({
    ok: true,
    json: async () => String(url).includes("history.json") ? historyData : latestData,
  }), async () => {
    const latest = await publishedLatestPayload();
    const ticker = await publishedTickerPayload("PUBLISHED");
    return { latest, ticker };
  });

  assert(published.latest.runInfo.status === "published_fallback", "published latest endpoint must replace source run status with fallback status");
  assert(published.latest.runInfo.live_access_ok === false, "published latest endpoint must not claim live access");
  assert(published.latest.runInfo.payload.stale_execution_blocks === 2, "published latest endpoint must block every fallback row");
  assert(published.latest.runInfo.payload.data_provider_counts.published_pages === 2, "published latest endpoint must report the fallback provider");
  assert(published.ticker.runInfo.status === "published_fallback", "published ticker endpoint must replace source run status with fallback status");
  assert(published.ticker.runInfo.payload.stale_execution_blocks === 1, "published ticker endpoint must block the fallback snapshot");
  LEARNING_EVIDENCE_FIELDS.forEach((field) => {
    const expected = field === "learning_promotion_eligible" ? false
      : field === "learning_reporting_only" ? true
        : field === "learning_promotion_state" ? "REPORTING_ONLY"
          : learningEvidence[field];
    assert(published.latest.rows[0][field] === expected, `published fallback must retain ${field} at row level`);
    assert(published.latest.rows[0].payload[field] === expected, `published fallback must retain ${field} in payload`);
  });

  const staticLatest = await withMockFetch(async () => {
    throw new Error("published unavailable");
  }, () => publishedLatestPayload());
  assert(staticLatest.runInfo.status === "static_fallback", "static latest endpoint must replace bundled run status with static fallback status");
  assert(staticLatest.runInfo.live_access_ok === false, "static latest endpoint must not claim live access");
  assert(staticLatest.runInfo.payload.stale_execution_blocks === staticLatest.rows.length, "static latest endpoint must block every bundled row");

  return {
    latestBlocks: published.latest.runInfo.payload.stale_execution_blocks,
    tickerBlocks: published.ticker.runInfo.payload.stale_execution_blocks,
    staticBlocks: staticLatest.runInfo.payload.stale_execution_blocks,
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
      data_age_days: 0,
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
      data_age_days: 0,
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
      ticker_permission: "ALLOW",
      walk_forward_permission: "ALLOW",
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
      data_age_days: 0,
      feedback_quality: "WORKING",
      feedback_return_pct: 4.2,
      feedback_max_drawdown_pct: -1.1,
      feedback_stop_hit: "NO",
      learning_sample_count: 12,
      learning_working_rate: 0.67,
      learning_failed_rate: 0.17,
      learning_trap_avoided_rate: 0.83,
      learning_avg_score: 4.2,
      learning_adjustment: 1.5,
      learning_distinct_ticker_count: 8,
      learning_evaluation_date_count: 6,
      learning_evaluation_date_min: "2026-05-01",
      learning_evaluation_date_max: "2026-06-15",
      learning_window_start: "2026-05-01",
      learning_window_end: "2026-06-15",
      learning_model_version: "learning-v3",
      learning_promotion_eligible: true,
      learning_reporting_only: false,
      learning_promotion_state: "PROMOTION_ELIGIBLE",
      learning_scope: "action/setup family",
      learning_key_used: "BUY CANDIDATE|BREAKOUT BUY|ANY|ANY",
      learning_plan: "Promotion evidence passed the producer checks.",
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
  LEARNING_EVIDENCE_FIELDS.forEach((field) => {
    assert(gated.payload[field] !== undefined, `execution-gated row must retain ${field} in payload`);
    assert(gated[field] !== undefined, `execution-gated row must promote ${field} to top level`);
    assert(gated[field] === gated.payload[field], `execution-gated row must keep ${field} consistent across DTO shapes`);
  });
  assert(gated.payload.data_provider === "polygon", "execution-gated BUY row must keep data provider");
  assert(gated.payload.data_provider_status === "LIVE_OK", "execution-gated BUY row must keep data provider status");

  const unsafeGates = [
    {
      name: "blocked ticker gate",
      row: {
        ticker: "BLOCKED",
        action: "BUY CANDIDATE",
        score: 98,
        payload: { market_permission: "ALLOW", ticker_permission: "BLOCK", risk_permission: "ALLOW", data_age_days: 0 },
      },
    },
    {
      name: "blocked walk-forward gate",
      row: {
        ticker: "WALK_BLOCKED",
        action: "BUY CANDIDATE",
        score: 98,
        payload: { market_permission: "ALLOW", ticker_permission: "ALLOW", walk_forward_permission: "BLOCK", risk_permission: "ALLOW", data_age_days: 0 },
      },
    },
    {
      name: "malformed market gate",
      row: {
        ticker: "MALFORMED",
        action: "BUY CANDIDATE",
        score: 98,
        payload: { market_permission: "GREEN", ticker_permission: "ALLOW", risk_permission: "ALLOW", data_age_days: 0 },
      },
    },
    {
      name: "contradictory market gate",
      row: {
        ticker: "CONTRADICTORY",
        action: "BUY CANDIDATE",
        score: 98,
        market_permission: "ALLOW",
        payload: { market_permission: "BLOCK", ticker_permission: "ALLOW", risk_permission: "ALLOW", data_age_days: 0 },
      },
    },
  ].map(({ name, row }) => ({ name, dto: rowDto(row) }));
  unsafeGates.forEach(({ name, dto }) => {
    assert(!isBuyLike(dto), `${name} must not preserve a BUY-like action`);
    assert(adjustedScore(dto) <= 49, `${name} must be capped below actionable rank`);
  });

  const personalityBlocked = rowDto({
    ticker: "PERSONALITY_BLOCKED",
    data_date: new Date().toISOString().slice(0, 10),
    action: "BUY CANDIDATE",
    score: 98,
    personality_setup_allowed: "YES",
    payload: {
      market_permission: "ALLOW",
      ticker_permission: "ALLOW",
      risk_permission: "ALLOW",
      personality_setup_allowed: "NO",
      data_age_days: 0,
    },
  });
  assert(!isBuyLike(personalityBlocked), "personality_setup_allowed=NO must block a BUY-like action even when the row is contradictory");
  assert(personalityBlocked.payload.personality_setup_allowed === "NO", "personality NO must win over a contradictory top-level YES");
  assert(personalityBlocked.payload.reason_codes.includes("personality_setup_not_allowed"), "personality block must be auditable");
  assert(adjustedScore(personalityBlocked) <= 49, "personality-blocked BUY row must be capped below actionable rank");

  const staleContradiction = rowDto({
    ticker: "STALE",
    action: "BUY CANDIDATE",
    score: 98,
    payload: {
      market_permission: "ALLOW",
      ticker_permission: "ALLOW",
      risk_permission: "ALLOW",
      data_age_days: 1,
      freshness_block: "NO",
      freshness_status: "LIVE_OR_CURRENT",
    },
  });
  assert(staleContradiction.action === "SETUP FORMING", "stale age must downgrade a contradictory fresh BUY row");
  assert(staleContradiction.payload.freshness_block === "YES", "stale age must override freshness_block=NO");
  assert(staleContradiction.payload.freshness_status === "STALE_BLOCK", "stale age must override a contradictory fresh status");
  assert(adjustedScore(staleContradiction) <= 49, "stale age must cap the contradictory fresh row");
  assert(staleContradiction.score === 98, "freshness policy must preserve the raw technical score");

  const dateAgeContradiction = rowDto({
    ticker: "DATE_CONTRADICTION",
    data_date: previousMarketSession(latestCompletedMarketSession()).toISOString().slice(0, 10),
    action: "BUY CANDIDATE",
    score: 98,
    payload: {
      market_permission: "ALLOW",
      ticker_permission: "ALLOW",
      risk_permission: "ALLOW",
      data_age_days: 0,
      freshness_block: "NO",
      freshness_status: "LIVE_OR_CURRENT",
    },
  });
  assert(dateAgeContradiction.action === "SETUP FORMING", "data_date contradicting data_age_days=0 must downgrade a BUY row");
  assert(dateAgeContradiction.payload.freshness_block === "YES", "data_date contradiction must block execution");
  assert(dateAgeContradiction.payload.freshness_status === "STALE_BLOCK", "data_date contradiction must replace fresh status");
  assert(dateAgeContradiction.payload.reason_codes.includes("data_age_date_contradiction"), "data_date contradiction must be auditable");
  assert(adjustedScore(dateAgeContradiction) <= 49, "data_date contradiction must cap actionable rank");
  assert(dateAgeContradiction.score === 98, "date freshness policy must not overwrite raw technical evidence");

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
  assert(antiBullTrap.score === 112, "anti-signal policy must preserve the raw technical score");
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
    unsafeGateActions: unsafeGates.map(({ dto }) => dto.action),
    personalityBlockedAction: personalityBlocked.action,
    personalityBlockedScore: adjustedScore(personalityBlocked),
    staleContradictionAction: staleContradiction.action,
    staleContradictionBlock: staleContradiction.payload.freshness_block,
    dateAgeContradictionAction: dateAgeContradiction.action,
    dateAgeContradictionBlock: dateAgeContradiction.payload.freshness_block,
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
  assert(gateValues(merged).join(",") === "ALLOW,CAUTION,NONE,ALLOW", "ticker detail latest row must use snapshot execution gates");

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

async function main() {
  const result = {
    staticFallback: auditStaticFallback(),
    staticFallbackNormalization: auditStaticFallbackNormalization(),
    browserFallbackNormalization: await auditBrowserFallbackNormalization(),
    staticLearningEvidenceFallback: auditStaticLearningEvidenceFallback(),
    staticTickerFallback: auditStaticTickerFallback(["AVGO", "CRWV", "ZM", "MU"]),
    publishedFallbackContract: await auditPublishedFallbackContract(),
    supabaseFallback: auditSupabaseFallback(),
    historicalReplayDto: auditHistoricalReplayDto(),
    searchBehavior: auditSearchBehavior(),
    decisionFunnelUi: auditDecisionFunnelUi(),
    marketSessionFreshness: auditMarketSessionFreshness(),
    learningReadoutUi: auditLearningReadoutUi(),
    storageGuard: auditStorageGuard(),
    partialRunStatus: auditPartialRunStatus(),
    atomicPublication: auditAtomicPublicationContract(),
    runHealthProviders: auditRunHealthProviderPayload(),
    tickerDetailMerge: auditTickerDetailMerge(),
  };

  console.log(JSON.stringify(result, null, 2));
}

main().catch((error) => {
  console.error(error.stack || error.message || error);
  process.exitCode = 1;
});
