const { conservativeFallbackRow, staticLatestPayload, staticTickerPayload } = require("../api/_static_data");
const { publishedLatestPayload, publishedTickerPayload } = require("../api/_published_data");
const { committedPublicationMatches, rowDto, runDto } = require("../api/_supabase");
const { mergeSnapshotIntoLatestHistory } = require("../api/ticker/[ticker]");
const { latestCompletedMarketSession, marketSessionAge, previousMarketSession } = require("../api/_market_session");
const { historyMetrics, pressureComparison, signalTransition, interpretationState } = require("../assets/history_summary");
const { qualityConstraintLabel, runHealthStatus, runHealthSummary } = require("../assets/presentation");
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

function companySearchTerms(row) {
  return [row.ticker, row.name].filter(Boolean).map((value) => String(value).toLowerCase());
}

function exactTickerSearchNeedle(query, rows) {
  const ticker = normaliseSearchTicker(query);
  if (!ticker || !/^[A-Z0-9.-]{1,8}$/.test(ticker)) return "";
  return rows.some((row) => tickerSearchAliases(row).includes(ticker)) ? ticker : "";
}

function resolveTickerDirectoryQuery(query, rows) {
  const cleanQuery = String(query || "").trim();
  if (!cleanQuery) return "";
  const exactTicker = exactTickerSearchNeedle(cleanQuery, rows);
  if (exactTicker) return rows.find((row) => tickerSearchAliases(row).includes(exactTicker))?.ticker || "";
  const needle = cleanQuery.toLowerCase();
  const exactCompanyMatches = rows.filter((row) => companySearchTerms(row).some((term) => term.toLowerCase() === needle));
  if (exactCompanyMatches.length === 1) return exactCompanyMatches[0].ticker;
  if (exactCompanyMatches.length > 1) return "";
  const matches = rows.filter((row) => companySearchTerms(row).some((term) => term.toLowerCase().includes(needle)));
  return matches.length === 1 ? matches[0].ticker : "";
}

function auditSearchBehavior() {
  const source = fs.readFileSync("assets/app.js", "utf8");
  assert(source.includes("function exactTickerSearchNeedle"), "watchlist search must include exact ticker matching");
  assert(source.includes("function companySearchTerms"), "watchlist search must index company names alongside ticker aliases");
  assert(source.includes("...companySearchTerms(row),"), "company names must be included in the searchable watchlist text");
  assert(source.includes("rowMatchesSearch(row, state.query, exactTickerNeedle)"), "watchlist render must use ticker-aware search matching");
  assert(source.includes("if (searchActive && state.visibleRows.length === 1)"), "a unique search result must become the selected ticker");

  const rows = staticLatestPayload().rows || [];
  const muNeedle = exactTickerSearchNeedle("MU", rows);
  const muMatches = rows.filter((row) => tickerSearchAliases(row).includes(muNeedle)).map((row) => row.ticker);
  const micronMatches = rows.filter((row) => companySearchTerms(row).some((term) => term.includes("micron"))).map((row) => row.ticker);

  assert(muNeedle === "MU", "MU query must resolve to exact ticker search");
  assert(muMatches.length === 1 && muMatches[0] === "MU", `MU exact search must only match MU, got ${muMatches.join(",")}`);
  assert(micronMatches.includes("MU"), "company-name search for Micron must still find MU");
  assert(resolveTickerDirectoryQuery("MU", rows) === "MU", "ticker detail search must resolve exact ticker symbols");
  assert(resolveTickerDirectoryQuery("Micron", rows) === "MU", "ticker detail search must resolve full displayed company names");
  assert(resolveTickerDirectoryQuery("icron", rows) === "MU", "ticker detail search must resolve unique company-name fragments");
  assert(resolveTickerDirectoryQuery("Alphabet", rows) === "", "ticker detail search must not choose arbitrarily between duplicate company names");
  const tickerSource = fs.readFileSync("ticker.html", "utf8");
  assert(!tickerSource.includes("company-context"), "ticker detail must not render company context");
  assert(!source.includes("renderCompanyBrief"), "ticker detail must not fetch or render company context");

  return {
    muNeedle,
    muMatches,
    micronMatches,
  };
}

function auditConditionalBuyPresentation() {
  const source = fs.readFileSync("assets/app.js", "utf8");
  const styles = fs.readFileSync("assets/styles.css", "utf8");
  assert(source.includes('return actionKind(row?.action) === "buy" ? "Qualified setup" : "Latest signal"'), "BUY qualification must not be labelled as an immediately executable signal");
  assert(source.includes('"STARTER BUY SETUP"'), "Starter BUY must be presented as a setup qualification");
  assert(source.includes('"Wait for pullback · then use 50% size"'), "an above-zone Starter BUY must make the pullback condition explicit");
  assert(source.includes('"The setup qualifies, but price is above the entry zone. Do not enter until a controlled pullback reaches the zone and holds."'), "readiness copy must not imply immediate entry above the zone");
  assert(source.includes('"The setup is qualified, but execution is waiting for price to return to the planned entry zone."'), "recent-behavior summary must respect an above-zone wait state");
  assert(!source.includes('"Starter position · 50% of normal size"'), "detail UI must not present a conditional setup as an open position");
  assert(!source.includes("latest Buy has passed the current execution checks"), "detail UI must not equate risk checks with an executable entry");
  assert(source.includes('"BUY CANDIDATE": "BUY SETUP"'), "all user-facing action labels must call a qualified candidate a BUY SETUP");
  assert(!source.includes('"BUY CANDIDATE": "BUY"'), "the UI must not shorten a conditional setup to BUY");
  assert(source.includes('["If the stop is reached", risk ? `Estimated loss: about ${fmtNumber(Math.abs(risk), 1)}% from the planned entry`'), "stop risk must be explained as a potential loss in natural language");
  assert(!source.includes('"Planned downside"'), "the unexplained downside label must not return");
  assert(!source.includes("before it becomes a buy"), "developing setups must use the BUY SETUP product term");
  assert(!source.includes("upgrade the stock to a buy."), "learning copy must use the BUY SETUP product term");
  assert(styles.includes('grid-template-columns: minmax(0, 1fr) clamp(340px, 31vw, 420px)'), "desktop detail width must leave enough room for the watchlist");
  assert(styles.includes('body[data-page="watchlist"] .watchlist-workspace table { min-width: 980px; }'), "desktop watchlist must preserve readable column widths");
  assert(styles.includes('body[data-page="watchlist"] .watchlist-workspace th:nth-child(6)'), "loss-to-stop column must have an explicit desktop width");
  assert(styles.includes('white-space: normal;'), "desktop table headings must be allowed to wrap naturally");
  assert(styles.includes('font-size: clamp(38px, 3.4vw, 52px)'), "watchlist masthead must not overpower the decision workspace");
  assert(styles.includes('body[data-page="watchlist"] .editorial-hero .brand-name { font-size: 34px; }'), "mobile masthead must preserve first-screen workspace");
  return true;
}

function auditHistorySummary() {
  const completeRows = Array.from({ length: 30 }, (_, index) => ({
    history_date: `2026-06-${String(index + 1).padStart(2, "0")}`,
    close: 100 + index,
    high: 101 + index,
  }));
  const completeMetrics = historyMetrics(completeRows);
  assert(completeMetrics.rows.length === 30 && completeMetrics.priceAvailable, "history summary must retain the fixed 30-session window when prices are complete");
  assert(Number.isFinite(completeMetrics.distanceFromHighPct), "complete daily highs must produce a distance from the period high");

  const missingHighRows = completeRows.map((row, index) => index === 12 ? { ...row, high: null } : row);
  assert(historyMetrics(missingHighRows).distanceFromHighPct === null, "a missing daily high must make distance from the period high unavailable");
  const invalidHighRows = completeRows.map((row, index) => index === 12 ? { ...row, high: row.close - 1 } : row);
  assert(historyMetrics(invalidHighRows).distanceFromHighPct === null, "a daily high below its close must make distance from the period high unavailable");
  const invalidPriceMetrics = historyMetrics([
    { history_date: "2026-06-01", close: 0, high: 1 },
    { history_date: "2026-06-02", close: -2, high: 1 },
  ]);
  assert(invalidPriceMetrics.available && !invalidPriceMetrics.priceAvailable && invalidPriceMetrics.rows.length === 2, "invalid closes must fail price metrics without silently removing sessions");
  const gappedWindow = historyMetrics([...completeRows, { history_date: "2026-07-01", close: null, high: null }]);
  assert(gappedWindow.rows.length === 30 && !gappedWindow.priceAvailable, "the latest 30 sessions must be selected before completeness checks");

  const pressureRows = Array.from({ length: 30 }, (_, index) => ({
    history_date: `2026-06-${String(index + 1).padStart(2, "0")}`,
    buyer_score: index < 25 ? 20 : 40,
    seller_score: index < 25 ? 80 : 55,
  }));
  const recoveringPressure = pressureComparison(pressureRows);
  assert(recoveringPressure.shift === "buying" && recoveringPressure.control === "selling", "a shift toward buying must not imply buyer control while sellers still dominate");
  const reversedPressure = pressureComparison([...pressureRows].reverse());
  assert(reversedPressure.shift === recoveringPressure.shift && reversedPressure.control === recoveringPressure.control, "pressure comparison must be independent of API row order when dates are present");
  assert(pressureComparison(pressureRows.slice(1)).reason === "window", "pressure comparison must require the full 5-versus-25 window");
  assert(pressureComparison([...pressureRows.slice(0, 29), { history_date: "2026-06-30", buyer_score: null, seller_score: 50 }]).reason === "scores", "missing pressure scores must fail closed");
  const partialDates = completeRows.map((row, index) => index === 12 ? { close: row.close, high: row.high } : row);
  assert(historyMetrics(partialDates).reason === "dates", "partially dated history must fail closed instead of trusting input order");
  assert(pressureComparison(partialDates).reason === "dates", "partially dated pressure history must fail closed instead of trusting input order");
  const undatedRows = completeRows.map(({ history_date, ...row }) => row);
  assert(historyMetrics(undatedRows).reason === "dates" && historyMetrics([...undatedRows].reverse()).reason === "dates", "fully undated history must fail closed in either caller order");
  assert(pressureComparison(undatedRows).reason === "dates", "fully undated pressure history must fail closed");
  const changedToday = signalTransition([
    { history_date: "2026-06-01", action: "WAIT" },
    { history_date: "2026-06-02", action: "BUY CANDIDATE" },
  ]);
  const changedPriorSession = signalTransition([
    { history_date: "2026-06-01", action: "WAIT" },
    { history_date: "2026-06-02", action: "BUY CANDIDATE" },
    { history_date: "2026-06-03", action: "BUY CANDIDATE" },
  ]);
  assert(changedToday.sessionsAgo === 0, "a signal change on the latest session must be reported as current, not one session old");
  assert(changedPriorSession.sessionsAgo === 1, "a signal change on the prior session must be one trading session old");
  assert(signalTransition([{ history_date: "2026-06-01", action: "WAIT" }, { history_date: "2026-06-02", action: "" }]).reason === "actions", "missing session actions must fail closed instead of shifting the apparent latest signal");
  assert(signalTransition([
    { history_date: "2026-06-01", action: "WAIT" },
    { history_date: "2026-06-02" },
    { history_date: "2026-06-03", action: "BUY CANDIDATE" },
  ]).reason === "actions", "missing middle-session actions must fail closed instead of shortening signal history");
  assert(interpretationState("exit", { stale: true, checksClear: true }) === "stale-exit", "stale status must remain visible while preserving defensive Exit priority");
  assert(interpretationState("avoid", { stale: true, checksClear: true }) === "stale-avoid", "stale status must remain visible while preserving Avoid priority");
  return { metricCases: 6, pressureCases: 6, transitionCases: 4, priorityCases: 2 };
}

function auditPresentationSemantics() {
  const currentSession = latestCompletedMarketSession().toISOString().slice(0, 10);
  const blocked = { action: "SETUP FORMING", market_permission: "BLOCK" };
  const avoid = { action: "WAIT / AVOID", market_permission: "BLOCK" };
  const exit = { action: "EXIT PRESSURE", market_permission: "BLOCK" };
  assert(qualityConstraintLabel(blocked) === "MARKET BLOCKED", "entry setups must expose their hard market block");
  assert(qualityConstraintLabel(avoid) === "NO ENTRY", "avoid rows must lead with the action rather than an irrelevant entry gate");
  assert(qualityConstraintLabel(exit) === "PROTECT CAPITAL", "exit rows must lead with capital protection");
  const balancedStarter = {
    action: "BUY CANDIDATE",
    data_date: currentSession,
    payload: {
      policy_version: "balanced-v1",
      market_permission: "MIXED",
      risk_permission: "ALLOW",
      ticker_permission: "BLOCK",
      walk_forward_permission: "INSUFFICIENT",
      anti_signal_level: "NONE",
      freshness_block: "NO",
    },
  };
  assert(qualityConstraintLabel(balancedStarter) === "", "balanced Starter BUY must present soft uncertainty without a blocked-quality label");
  assert(qualityConstraintLabel({ ...balancedStarter, payload: { ...balancedStarter.payload, market_permission: "BLOCK" } }) === "MARKET BLOCKED", "balanced policy must still expose a true market block");
  const partial = runHealthStatus({
    symbols_analyzed: 186,
    symbols_total: 192,
    symbols_failed: 6,
    symbols_stale_cache: 1,
    latest_data_date: currentSession,
    payload: { stale_execution_blocks: 1 },
  }, Array.from({ length: 186 }, (_, index) => ({ ticker: `T${index}`, date: currentSession })));
  assert(partial.tone === "warn" && partial.label === "Partial coverage", "one stale ticker must not mark a 97% complete publication globally unsafe");
  assert(partial.detail.includes("1 stale-data block") && !partial.detail.includes("1 stale-data blocks"), "health copy must use natural singular grammar");
  assert(runHealthSummary({ symbols_stale_cache: 1 }).includes("1 stock using"), "cached-data copy must use natural singular grammar");
  const unsafe = runHealthStatus({ symbols_analyzed: 20, symbols_total: 100 }, []);
  assert(unsafe.tone === "bad", "materially incomplete publications must still fail closed");
  const expired = runHealthStatus({ symbols_analyzed: 1, symbols_total: 1, latest_data_date: "2026-01-02" }, [{ ticker: "OLD", date: "2026-01-02" }]);
  assert(expired.tone === "bad", "an expired static publication must fail closed even if stored stale flags say fresh");
  assert(qualityConstraintLabel({ action: "BUY CANDIDATE", data_date: "2026-01-02" }) === "DATA NEEDS REFRESH", "expired rows must block entry in the browser");
  return { readinessCases: 6, healthCases: 4 };
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
  const presentationSource = fs.readFileSync("assets/presentation.js", "utf8");
  assert(stylesSource.includes("#market-activity[open] > summary"), "open market activity must have a scoped surface treatment");
  assert(pageSource.includes('id="market-highlights"'), "market activity must use one concise highlight surface");
  assert(appSource.includes("function previousSessionHighlights(limit = 8)"), "market activity must cap and deduplicate latest-session highlights");
  assert(appSource.includes("if (item.row?.ticker && !unique.has(item.row.ticker))"), "a stock must not be repeated across activity categories");
  assert(appSource.includes("function activityHighlightReason(item)"), "activity cards must explain why each stock matters in natural language");
  assert(appSource.includes('state.rows[0]?.data_date || state.rows[0]?.date || state.rows[0]?.run_date'), "activity highlights must identify the latest market date across publication formats");
  assert(!pageSource.includes('id="signal-changes"') && !pageSource.includes('id="price-movers"') && !pageSource.includes('id="focus-list"'), "market activity must not retain the repetitive multi-section layout");
  assert(appSource.includes("function renderTickerDetailPanel"), "desktop watchlist must expose an in-place ticker scanner review panel");
  assert(!appSource.includes("Confirm any BUY on the TradingView Pine chart before acting."), "ticker panel must not repeat the removed Pine confirmation copy");
  assert(appSource.includes("function decisionHeadline(row)"), "ticker context must lead with a clear user decision");
  assert(appSource.includes("function decisionNarrative(row)"), "ticker context must explain the decision in natural language");
  assert(appSource.includes("function predictionNarrative(row)"), "ticker context must explain prediction evidence in natural language");
  assert(appSource.includes("function recentBehaviorSummary(row, previous)"), "recent behavior must be summarized in natural language");
  assert(appSource.includes("function renderQualityScore(row)"), "watchlist quality must distinguish unavailable evidence from a numeric score");
  assert(appSource.includes("function qualityConstraintLabel(row)"), "all quality surfaces must share the same constraint semantics");
  assert(appSource.includes("function renderReferenceLevels(row"), "reference levels must be separated from active trade plans");
  assert(appSource.includes('return active ? "Breakout entry range" : "Reference breakout range"'), "breakout plans must explain the trigger in reader-facing language");
  assert(appSource.includes("This is a conditional breakout plan, not a market order."), "BUY guidance must explain that a breakout signal is conditional");
  assert(appSource.includes("skip the trade if price opens or runs above the maximum entry"), "BUY guidance must state the no-chase rule");
  assert(appSource.includes("function fillabilityReadout(row)"), "entry fillability must be explained in natural language");
  assert(appSource.includes("Price plan"), "active levels must use a concise reader-facing label");
  assert(presentationSource.includes('return "NEEDS VERIFICATION"'), "missing execution evidence must use a reader-facing readiness status");
  assert(presentationSource.includes('return "MARKET BLOCKED"'), "market blocks must be presented as a concrete decision reason");
  assert(presentationSource.includes('return "SETUP UNPROVEN"'), "insufficient walk-forward evidence must be distinguished from a market block");
  assert(presentationSource.includes('if (antiSignal === "BLOCK") return "DO NOT ENTER"'), "anti-signal blocks must suppress the numeric readiness display with an actionable label");
  assert(!appSource.includes('"GATE BLOCK"'), "reader-facing UI must not expose the internal gate-block label");
  assert(!appSource.includes("Trend quality ${fmtConviction(latest)} / 100"), "ticker diagnostics must not present adjusted rank as synthetic trend quality");
  assert(appSource.includes("Why we see it this way"), "ticker panel must use a reader-facing evidence label");
  assert(!appSource.includes('<details class="detail-diagnostics">'), "decision evidence must not be collapsed on either app surface");
  assert(appSource.includes('<section class="detail-diagnostics"><h3>Why we see it this way</h3>'), "decision evidence must be visible by default");
  assert(!appSource.includes("<summary>Diagnostics</summary>"), "ticker panel must not expose an internal diagnostics label");
  assert(!appSource.includes("Weight Model"), "ticker detail must not expose internal model-weight shorthand");
  assert(!appSource.includes("Transition Edge"), "ticker detail must not expose unexplained transition scores");
  assert(pageSource.includes('id="ticker-detail-panel"'), "watchlist page must provide the selected ticker panel mount");
  assert(pageSource.includes('id="profit-alerts"'), "watchlist must provide an in-app notification center mount");
  assert(appSource.includes("function notificationForRow(row)"), "notification center must derive alerts from current scanner rows");
  assert(appSource.includes('stage === "TP1 REACHED"'), "notification center must detect first-profit events");
  assert(appSource.includes('stage === "PROTECT REMAINDER"'), "notification center must detect profit-protection events");
  assert(appSource.includes('row.action === "EXIT PRESSURE" && state.focusTickers.includes(ticker)'), "exit alerts must be limited to saved Focus List names");
  assert(appSource.includes("function markNotificationsRead(ids)"), "notification center must persist read state");
  assert(appSource.includes("const NOTIFICATION_RETENTION_MARKET_SESSIONS = 5"), "notification history must expire after five completed market sessions");
  assert(appSource.includes("notificationIsWithinRetention(item)"), "stored notification history must enforce market-session retention");
  assert(appSource.includes("pruneNotificationReadState(items)"), "expired notification read markers must be reclaimed");
  assert(appSource.includes(".slice(0, 50)"), "notification history must remain storage-bounded");
  assert(!appSource.includes("Notification.requestPermission"), "in-app notifications must not request browser notification permission");
  assert(pageSource.includes("Scanner rank first"), "watchlist sorting must use scanner-review terminology");
  assert(!pageSource.includes("Execution tier first"), "watchlist must not retain execution-tier sorting copy");
  assert(!tickerSource.includes("Execution plan"), "ticker detail must not retain execution-plan copy");
  assert(tickerSource.includes('placeholder="Ticker or company name"'), "ticker detail search must advertise ticker and company matching");
  assert(appSource.includes("function resolveTickerDirectoryQuery(query, rows)"), "ticker detail must resolve company-name searches through the published directory");
  assert(appSource.includes("loadHistory(ticker).finally(() => loadTickerDirectory())"), "ticker detail must refresh its search directory without delaying the current stock");
  assert(!tickerSource.includes('id="ticker-name"'), "ticker detail must not retain an unused company-name node");
  assert(!tickerSource.includes('class="ticker-switcher"'), "change-stock search must not remain inside the decision card");
  assert(tickerSource.includes('class="ticker-hero-tools"'), "ticker search and scanner context must share one header tool region");
  assert(stylesSource.includes("v3.3 concept workspace"), "both app surfaces must use the approved concept workspace design layer");
  assert(pageSource.indexOf('class="secondary-tools"') < pageSource.indexOf('class="hero editorial-hero"'), "supporting tools must be reachable from the top utility rail");
  assert(stylesSource.includes(".secondary-tools .utility-drawer-body"), "market activity must open as a non-disruptive top drawer");
  assert(stylesSource.includes(".activity-highlight-grid"), "market activity must use a compact card grid");
  assert(stylesSource.includes("body[data-page=\"watchlist\"] .execution-queue::after { display: none; }"), "watchlist summary strip must not retain decorative card ornaments");
  assert(stylesSource.includes("body.ticker-page .moment-card::before"), "ticker history must use timeline markers instead of nested cards");
  assert(stylesSource.includes("body.ticker-page .history-visual { gap: 0; border: 0; background: transparent; }"), "ticker summary must remain a flat editorial section");
  assert(!pageSource.includes("Buy = scanner candidate; chart confirmation required; not trade execution."), "watchlist must not repeat a generic BUY disclaimer");
  assert(!tickerSource.includes("Buy = scanner candidate; chart confirmation required; not trade execution."), "ticker detail must not repeat a generic BUY disclaimer");
  assert(pageSource.includes('id="mobile-search-count">Loading...</strong>'), "mobile loading state must not report a false zero-result count");
  assert(tickerSource.includes("Loading current data..."), "ticker loading state must not report a false missing-history error");
  const pageBundleVersion = pageSource.match(/assets\/app\.js\?v=([^"']+)/)?.[1];
  const tickerBundleVersion = tickerSource.match(/assets\/app\.js\?v=([^"']+)/)?.[1];
  assert(pageBundleVersion && pageBundleVersion === tickerBundleVersion, "both app surfaces must load the current shared application bundle");
  assert(stylesSource.includes("@media (prefers-color-scheme: dark)") && stylesSource.includes("html { color-scheme: dark; }"), "shared app surfaces must follow the device dark-mode preference");
  assert(pageSource.includes('media="(prefers-color-scheme: light)"') && pageSource.includes('media="(prefers-color-scheme: dark)"'), "watchlist browser chrome must follow the device theme");
  assert(tickerSource.includes('media="(prefers-color-scheme: light)"') && tickerSource.includes('media="(prefers-color-scheme: dark)"'), "ticker browser chrome must follow the device theme");
  assert(!appSource.includes("Optional chart"), "ticker detail must remove the optional scanner chart");
  assert(!appSource.includes("Daily scanner bars"), "ticker detail must remove scanner-chart jargon");
  assert(!stylesSource.includes(".chart-details") && !stylesSource.includes(".history-chart"), "removed chart styles must not remain as dead UI code");
  assert(appSource.includes("Why we see it this way"), "ticker detail must explain the decision in natural language");
  assert(tickerSource.includes("assets/history_summary.js"), "ticker detail must load the executable history-summary module");
  assert(!pageSource.includes("assets/history_summary.js"), "the main watchlist must not load ticker-only summary code");
  assert(appSource.includes("Recent behavior summary is temporarily unavailable."), "ticker detail must fail clearly when its summary dependency is unavailable");
  assert(appSource.includes("session dates are incomplete"), "ticker detail must explain mixed-date history failures");
  assert(appSource.includes("maximum closing-price drawdown"), "behavior summary must disclose its drawdown basis");
  assert(appSource.includes("highest daily high"), "behavior summary must compare the latest close with the period's intraday high");
  assert(appSource.includes("function historySignalSentence(rows, summaryApi)"), "behavior summary must report the latest actual signal transition");
  assert(appSource.includes("function pressureSummary(rows, summaryApi)"), "behavior summary must provide a bounded price-and-volume pressure inference");
  assert(appSource.includes("comparison.shift") && appSource.includes("comparison.control"), "pressure copy must distinguish directional shift from current control");
  assert(appSource.includes("Directionally supportive volume"), "volume confirmation must agree with pressure direction");
  assert(appSource.includes("This price-and-volume proxy does not override the latest"), "pressure inference must not soften a defensive signal");
  assert(appSource.includes("The latest data is stale, so this historical pressure is descriptive only."), "stale pressure must be explicitly qualified");
  assert(appSource.includes("A 5-versus-25 session comparison needs 30 valid observations"), "partial history must not be presented as a full pressure window");
  assert(!appSource.includes("The most common view was"), "behavior summary must not substitute a dominant historical label for the actual transition");
  assert(appSource.includes("The current Exit signal takes priority"), "positive history must never soften today's Exit signal");
  assert(appSource.includes("The latest data is stale, so the recent record cannot support an entry."), "stale history must be explained without execution jargon");
  assert(appSource.includes("The technical picture is developing, but it has not reached an entry signal."), "Building must remain explicitly non-executable");
  assert(appSource.includes("function similarCasesNarrative(row)"), "plain-language evidence must retain comparable historical context");
  assert(appSource.includes("No entry is recommended from the latest session."), "inactive signals must not expose misleading planning levels");
  assert(appSource.includes("Frozen execution plan"), "ticker surfaces must separate a frozen plan from today's signal");
  assert(appSource.includes("This confirms a market touch, not that you bought the stock."), "daily OHLC must not claim that the user entered a trade");
  assert(appSource.includes("daily data cannot show which happened first"), "ambiguous daily paths need plain-language disclosure");
  assert(tickerSource.includes("Latest decision") && tickerSource.includes("Recent behavior"), "ticker detail must follow the user decision order without implying stale data is current");
  assert(stylesSource.includes("body.ticker-page :is(a, button, input, summary):focus-visible"), "ticker controls must expose keyboard focus");
  assert(appSource.includes('if (!hash?.startsWith("#")) return;'), "ordinary navigation links must not be parsed as CSS hash targets");
  assert(pageSource.includes('data-mobile-filter="building"'), "mobile Building filter must use the aggregate queue");
  assert(pageSource.includes('data-mobile-filter="risk"'), "mobile Risk filter must use the aggregate queue");
  assert(appSource.includes("if (searchActive) return true;"), "search must cover the full watchlist instead of being hidden by a selected queue");
  assert(appSource.includes('card.classList.toggle("active", !searchActive'), "global search must clear the visual category selection");
  return { executionQueues: 3, activityTarget: "market-activity", naturalDecisionCopy: true };
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
  const fifthSessionAfterAlert = new Date("2026-07-17T21:00:00Z");
  const sixthSessionAfterAlert = new Date("2026-07-20T21:00:00Z");
  assert(marketSessionAge("2026-07-10", fifthSessionAfterAlert) === 5, "notification retention boundary must count completed sessions, not calendar days");
  assert(marketSessionAge("2026-07-10", sixthSessionAfterAlert) === 6, "notifications must expire on the sixth completed session");

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
      personality_setup_allowed: "YES",
      market_permission: "ALLOW",
      ticker_permission: "ALLOW",
      walk_forward_permission: "ALLOW",
      risk_permission: "ALLOW",
      execution_fill_state: "VALIDATED",
      execution_fill_probability: 0.68,
      execution_plan_id: "dto-plan",
      execution_plan_status: "ARMED",
      execution_plan_zone_low: 100,
      execution_plan_zone_high: 105,
      execution_plan_stop: 96,
      execution_plan_risk_pct: 8.57,
    },
  });
  assert(dto.payload.data_age_days === 0, "API DTO must agree with the scanner for the latest completed session");
  assert(dto.payload.freshness_block === "NO", "API DTO must not stale-block the latest completed session");
  assert(dto.score === 96 && adjustedScore(dto) === 96, "fresh API DTO must preserve raw and adjusted scores");
  assert(dto.payload.execution_plan_id === "dto-plan" && dto.payload.execution_plan_status === "ARMED", "API DTO must preserve frozen plan identity and state");
  assert(dto.payload.execution_plan_zone_low === 100 && dto.payload.execution_plan_stop === 96, "API DTO must preserve frozen plan prices");

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
  assert(source.includes("learning_evaluation_date_count"), "learning readout must surface evaluation breadth when present");
  assert(source.includes("entry_model_version"), "learning readout must require a versioned model before claiming an adjustment");
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
  assert(rich.includes("8 comparable settled signals") && rich.includes("4 stocks") && rich.includes("4 market dates"), "learning readout must explain evidence coverage in reader-facing language");
  assert(rich.includes("adjusted confidence by +2.4 points"), "eligible learning must explain its practical score effect");
  assert(explicitFalse.includes("Validation is incomplete") && !explicitFalse.includes("adjusted confidence"), "explicit false learning eligibility must prevent a claimed promotion");
  assert(missingProducerEligibility.includes("Validation is incomplete") && !missingProducerEligibility.includes("adjusted confidence"), "learning readout must not infer eligibility from counts or model state");
  assert(missingModelVersion.includes("Validation is incomplete") && !missingModelVersion.includes("adjusted confidence"), "learning readout must keep promotion pending without a model version");
  assert(basic.includes("3 comparable settled signals") && basic.includes("Validation is incomplete"), "incomplete learning evidence must be explained without internal model terminology");
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
  assert(guard.includes("readonly LEARNING_SESSIONS=100"), "outcome retention must cover the learning baseline");
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
  const pageVerifier = fs.readFileSync("scripts/verify_pages_publication.py", "utf8");
  const rollbackBuilder = fs.readFileSync("scripts/build_pages_rollback.py", "utf8");
  assert(scanner.includes('final_metadata["status"] = "pending_audit"'), "scanner must keep a synced run hidden until database audit passes");
  assert(workflow.indexOf("Audit Supabase learning health") < workflow.indexOf("Enforce staged database ceiling"), "database health audit must precede staged capacity enforcement");
  assert(workflow.indexOf("Enforce staged database ceiling") < workflow.indexOf("Deploy immutable Pages artifact"), "an oversized staged publication must roll back before deployment");
  assert(workflow.indexOf("Activate Supabase publication") < workflow.indexOf("Reclaim Supabase replay storage"), "retention must never run before pointer activation");
  assert(workflow.indexOf("Upload Pages artifact") < workflow.indexOf("Mark Supabase publication validated"), "the immutable Pages artifact must be staged before database validation");
  assert(workflow.indexOf("Verify deployed Pages publication") < workflow.indexOf("Activate Supabase publication"), "the active database pointer must move only after deployed manifest verification");
  assert(workflow.includes("supabase_learning_health.py --finalize") && workflow.includes("supabase_learning_health.py --activate"), "workflow must separate validation from activation");
  assert(supabaseApi.includes("watchlist_publication_control"), "API must resolve the explicit active publication pointer");
  assert(supabaseApi.includes("committedPublicationMatches"), "API must verify immutable publication ids after fetching rows");
  assert(supabaseApi.includes("return [];"), "status-query failures must fail closed instead of selecting raw snapshots");
  assert(tickerApi.includes("recentRunDates(1)"), "ticker detail must share the validated run selector with the main list");
  assert(tickerApi.includes("committedPublicationMatches") && latestApi.includes("committedPublicationMatches"), "list and detail APIs must reject mixed same-day reruns");
  assert(healthAudit.includes('payload->>publication_id=eq.') && healthAudit.includes('status=eq.pending_audit'), "audit promotion must compare-and-set the exact pending publication");
  assert(scanner.includes('outcomes["publication_id"] = publication_id'), "outcomes must be attributable to one immutable publication");
  assert(scanner.includes("fetch_active_publication_run()"), "learning must resolve outcomes through the active publication pointer");
  assert(scanner.includes('["publication_id", "signal_run_date", "evaluation_run_date", "ticker"]'), "outcome upserts must preserve publication versions");
  assert(schema.includes("('watchlist_snapshots', array['publication_id', 'ticker'])") && schema.includes("('watchlist_behavior_history', array['publication_id', 'ticker', 'history_date'])"), "snapshot and history staging rows must be versioned by publication");
  assert(workflow.includes("github-pages-rollback") && workflow.includes("Restore previous Pages publication"), "a failed Pages/database commit must redeploy the prior publication");
  assert(workflow.includes("verify_pages_publication.py") && pageVerifier.includes("hashlib.sha256") && pageVerifier.includes("ticker_count") && pageVerifier.includes("site_files"), "Pages verification must validate payload, UI integrity, and ticker mappings");
  assert(pageVerifier.includes("set(tickers) != set(ticker_paths)"), "Pages verification must reject a latest payload missing any manifest ticker");
  assert(rollbackBuilder.includes("site_files.items()") && rollbackBuilder.includes("Published site file failed integrity validation") && !rollbackBuilder.includes("--template"), "Pages rollback must preserve the manifest's complete verified site inventory");
  assert(workflow.includes("Retry previous Pages publication restore") && workflow.includes("Verify restored Pages publication"), "Pages rollback must retry and verify compensation");
  assert(workflow.includes("build-publication:") && workflow.includes("deploy-pages:") && workflow.includes("verify-and-activate:"), "build, deployment, and activation must use separate jobs");
  assert(workflow.indexOf("deploy-pages:") < workflow.indexOf("verify-and-activate:"), "online verification must run only after the Pages deployment job completes");
  assert(workflow.includes("restore-pages-after-failed-activation:") && workflow.includes("--assert-inactive"), "deployment and activation failures must reconcile the active pointer before compensation");
  assert(workflow.indexOf("Verify restored Pages publication") < workflow.indexOf("Roll back inactive Supabase publication"), "staged data must remain recoverable until the previous Pages publication is verified");
  assert(workflow.includes('psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -1'), "schema migration must run in one database transaction");
  assert(schema.includes("watchlist_publication_control") && schema.includes("('watchlist_snapshots', 'publication_id', 'watchlist_snapshots_publication_fk', 'c', 'cascade')"), "database staging must have an active pointer and cascading publication ownership");
  assert(schema.includes("select control.generation") && !schema.includes("select generation\n    from public.watchlist_publication_control"), "activation generation lookup must not collide with the table-return output parameter");
  assert(latestApi.includes("publication_id=eq.") && tickerApi.includes("publication_id=eq."), "list and detail APIs must select the active validated publication only");
  assert(scanner.includes('"learning_model_version": LEARNING_MODEL_VERSION'), "publication metadata must declare the active learning model");
  assert(scanner.includes('"learning_horizon_sessions": LEARNING_HORIZON_SESSIONS'), "publication metadata must declare the active learning horizon");
  assert(!healthAudit.includes('entry_model_version") or "") == "zone-v2"'), "health audit must not hard-code a stale learning model");
  assert(healthAudit.includes('synced_outcome_rows') && healthAudit.includes('len(outcome_rows)'), "health audit must reconcile the current publication outcome count");
  assert(healthAudit.includes("if finalize and") && healthAudit.includes("--activate"), "health validation and production activation must be separate operations");
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
  assert(source.includes("validatePublishedPayload"), "browser published data must be bound to a validated manifest version");
  assert(source.includes("payload?.publication_id !== manifest.publication_id"), "browser published data must reject publication mismatches");
  assert(source.includes("payload?.run_date !== manifest.run_date"), "browser published data must reject run-date mismatches");
  assert(!source.includes("PUBLISHED_HISTORY_JSON_URL") && !source.includes("PUBLISHED_HISTORY_CSV_URL"), "browser ticker loading must not download a global history archive");
  assert(source.includes("loadStaticTickerHistory") && source.includes("manifest.ticker_base_path"), "browser ticker history must use the manifest's per-ticker path");

  const validationStart = source.indexOf("function validatePublishedPayload");
  const validationEnd = source.indexOf("async function loadStaticLatestRows");
  assert(validationStart >= 0 && validationEnd > validationStart, "published payload validation must remain independently testable");
  const validatePublishedPayload = new Function(
    `${source.slice(validationStart, validationEnd)}; return validatePublishedPayload;`
  )();
  const publication = { publication_id: "publication-a", run_date: "2026-07-23" };
  assert(validatePublishedPayload({ ...publication, rows: [] }, publication).rows.length === 0, "matching published payload must be accepted");
  let mismatchRejected = false;
  try {
    validatePublishedPayload({ ...publication, publication_id: "publication-b" }, publication);
  } catch {
    mismatchRejected = true;
  }
  assert(mismatchRejected, "mismatched published payload must fail closed");

  return {
    publicationValidation: "pass",
    perTickerHistory: true,
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
    publication_id: "publication-20260716",
    run_date: "2026-07-16",
    runInfo: liveLookingRunInfo,
    rows: [
      { ticker: "PUBLISHED", run_date: "2026-07-16", action: "BUY CANDIDATE", score: 98, payload: learningEvidence },
      { ticker: "SECOND", run_date: "2026-07-16", action: "WATCH TREND", score: 62, payload: {} },
    ],
  };
  const manifestData = {
    publication_id: "publication-20260716",
    run_date: "2026-07-16",
    latest_path: "runs/publication-20260716/latest.json",
    ticker_base_path: "runs/publication-20260716/tickers",
    ticker_paths: { PUBLISHED: "runs/publication-20260716/tickers/PUBLISHED.json" },
  };
  const tickerData = {
    publication_id: "publication-20260716",
    run_date: "2026-07-16",
    ticker: "PUBLISHED",
    snapshot: latestData.rows[0],
    historyRows: [{ ticker: "PUBLISHED", history_date: "2026-07-15", action: "BUY CANDIDATE", score: 96, payload: learningEvidence }],
  };

  const published = await withMockFetch(async (url) => {
    const path = String(url);
    const body = path.endsWith("manifest.json") ? manifestData
      : path.endsWith("/latest.json") ? latestData
        : tickerData;
    return { ok: true, json: async () => body };
  }, async () => {
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
      market_permission: "ALLOW",
      ticker_permission: "ALLOW",
      walk_forward_permission: "ALLOW",
      risk_permission: "ALLOW",
      personality_setup_allowed: "YES",
      absorption_score: 72,
      short_pressure_proxy: 0,
      squeeze_watch: "NO",
      buy_tier: "A+ BUY",
      execution_priority: 1,
      execution_style: "BREAKOUT TRIGGER",
      execution_fill_state: "VALIDATED",
      execution_fill_probability: 0.68,
      execution_fill_sample_count: 37,
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

  const balancedStarter = rowDto({
    ticker: "SOFT",
    data_date: new Date().toISOString().slice(0, 10),
    action: "BUY CANDIDATE",
    setup: "REVERSAL BUY",
    score: 82,
    payload: {
      policy_version: "balanced-v1",
      buy_type: "STARTER",
      shadow_action: "BUY CANDIDATE",
      shadow_buy_type: "STARTER",
      shadow_policy_allowed: "YES",
      shadow_hard_blockers: [],
      shadow_cautions: ["The broader market is mixed", "Historical validation is still limited"],
      market_permission: "MIXED",
      ticker_permission: "BLOCK",
      walk_forward_permission: "INSUFFICIENT",
      risk_permission: "ALLOW",
      personality_setup_allowed: "NO",
      volatility_permission: "CAUTION",
      anti_signal_level: "CAUTION",
      execution_fill_state: "INSUFFICIENT",
      freshness_status: "LIVE_OR_CURRENT",
      freshness_block: "NO",
      data_age_days: 0,
      buy_tier: "STARTER BUY",
      execution_priority: 2,
    },
  });
  assert(balancedStarter.action === "BUY CANDIDATE", "balanced Starter BUY must survive soft confidence gates");
  assert(balancedStarter.payload.buy_tier === "STARTER BUY", "balanced Starter BUY must retain its half-size tier");

  const contradictoryBalanced = rowDto({
    ticker: "CONFLICT",
    data_date: new Date().toISOString().slice(0, 10),
    action: "BUY CANDIDATE",
    market_permission: "ALLOW",
    payload: {
      policy_version: "balanced-v1",
      buy_type: "STARTER",
      shadow_policy_allowed: "YES",
      shadow_hard_blockers: [],
      market_permission: "MIXED",
      ticker_permission: "INSUFFICIENT",
      walk_forward_permission: "INSUFFICIENT",
      risk_permission: "ALLOW",
      freshness_block: "NO",
      data_age_days: 0,
    },
  });
  assert(contradictoryBalanced.action === "SETUP FORMING", "contradictory balanced hard-gate evidence must fail closed");

  const unprovenFill = rowDto({
    ticker: "UNPROVEN",
    data_date: new Date().toISOString().slice(0, 10),
    action: "BUY CANDIDATE",
    setup: "MOMENTUM BUY",
    score: 96,
    payload: {
      market_permission: "ALLOW", ticker_permission: "ALLOW", walk_forward_permission: "ALLOW", risk_permission: "ALLOW",
      personality_setup_allowed: "YES", data_age_days: 0, freshness_block: "NO",
      execution_style: "BREAKOUT TRIGGER", execution_fill_state: "INSUFFICIENT",
    },
  });
  assert(unprovenFill.action === "SETUP FORMING", "BUY without proven fillability must be downgraded");
  assert(unprovenFill.payload.reason_codes.includes("fillability_evidence_insufficient"), "unproven fillability must retain its downgrade reason");

  const lowFill = rowDto({
    ticker: "LOWFILL",
    data_date: new Date().toISOString().slice(0, 10),
    action: "BUY CANDIDATE",
    setup: "BREAKOUT BUY",
    score: 96,
    payload: {
      market_permission: "ALLOW", ticker_permission: "ALLOW", walk_forward_permission: "ALLOW", risk_permission: "ALLOW",
      personality_setup_allowed: "YES", data_age_days: 0, freshness_block: "NO",
      execution_style: "BREAKOUT TRIGGER", execution_fill_state: "LOW", execution_fill_probability: 0.31,
    },
  });
  assert(lowFill.action === "SETUP FORMING", "BUY with low fillability must be downgraded");
  assert(lowFill.payload.reason_codes.includes("fillability_below_threshold"), "low fillability must retain its downgrade reason");

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

  const volatilityBlocked = rowDto({
    ticker: "VOLATILITY_BLOCKED",
    data_date: new Date().toISOString().slice(0, 10),
    action: "BUY CANDIDATE",
    score: 96,
    payload: {
      market_permission: "ALLOW",
      ticker_permission: "ALLOW",
      risk_permission: "ALLOW",
      personality_setup_allowed: "YES",
      volatility_regime: "CHAOTIC VOLATILITY",
      volatility_permission: "BLOCK",
      volatility_plan: "Volatility is not directional; do not open a new position.",
      data_age_days: 0,
    },
  });
  assert(!isBuyLike(volatilityBlocked), "chaotic-volatility payload must not preserve a BUY-like action");
  assert(volatilityBlocked.payload.next_day_bias === "EXECUTION BLOCKED", "volatility block must be visible in next-day guidance");
  assert(volatilityBlocked.payload.reason_codes.includes("volatility_execution_gate"), "volatility block must be auditable");
  assert(adjustedScore(volatilityBlocked) <= 49, "volatility-blocked BUY row must be capped below actionable rank");

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
    balancedStarterAction: balancedStarter.action,
    balancedStarterTier: balancedStarter.payload.buy_tier,
    contradictoryBalancedAction: contradictoryBalanced.action,
    unprovenFillAction: unprovenFill.action,
    lowFillAction: lowFill.action,
    unsafeGateActions: unsafeGates.map(({ dto }) => dto.action),
    personalityBlockedAction: personalityBlocked.action,
    personalityBlockedScore: adjustedScore(personalityBlocked),
    volatilityBlockedAction: volatilityBlocked.action,
    volatilityBlockedScore: adjustedScore(volatilityBlocked),
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
      market_permission: "ALLOW",
      ticker_permission: "ALLOW",
      walk_forward_permission: "ALLOW",
      risk_permission: "ALLOW",
      personality_setup_allowed: "YES",
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
  assert(!current.payload.reason_codes.includes("missing_execution_proof"), "complete frozen gates must not be mislabeled as missing execution proof");

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
    conditionalBuyPresentation: auditConditionalBuyPresentation(),
    historySummary: auditHistorySummary(),
    presentationSemantics: auditPresentationSemantics(),
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
