(function exposePresentation(root, factory) {
  const api = factory(root);
  if (typeof module === "object" && module.exports) module.exports = api;
  else if (root) root.WatchlistPresentation = api;
}(typeof globalThis !== "undefined" ? globalThis : this, function buildPresentation(root) {
  const marketSession = root?.WatchlistMarketSession
    || (typeof require === "function" ? require("./market-session") : null);
  function value(row, key) {
    return row?.payload?.[key] ?? row?.[key];
  }

  function actionKind(action) {
    const normalized = String(action || "").toUpperCase();
    if (normalized === "EXIT PRESSURE") return "exit";
    if (normalized === "WAIT / AVOID") return "avoid";
    if (normalized === "WAIT") return "wait";
    if (normalized === "BUY CANDIDATE") return "buy";
    if (normalized === "STRONG CONTINUATION") return "continue";
    if (normalized === "SETUP FORMING") return "building";
    return "watch";
  }

  function qualityConstraintLabel(row) {
    if (!row || typeof row !== "object") return "";
    const kind = actionKind(row.action);
    if (kind === "exit") return "PROTECT CAPITAL";
    if (kind === "avoid") return "NO ENTRY";
    if (kind === "wait") return "NO CLEAR EDGE";
    const sessionAge = marketSession?.marketSessionAge(row.data_date || row.date || row.history_date);
    const freshnessBlocked = String(value(row, "freshness_block") || "").toUpperCase() === "YES" || sessionAge > 0;
    const quality = String(value(row, "signal_quality") || "").toUpperCase();
    const antiSignal = String(value(row, "anti_signal_level") || "").toUpperCase();
    const marketPermission = String(value(row, "market_permission") || "").toUpperCase();
    const riskPermission = String(value(row, "risk_permission") || "").toUpperCase();
    const tickerPermission = String(value(row, "ticker_permission") || "").toUpperCase();
    const walkForwardPermission = String(value(row, "walk_forward_permission") || "").toUpperCase();
    if (freshnessBlocked) return "DATA NEEDS REFRESH";
    if (antiSignal === "BLOCK") return "DO NOT ENTER";
    if (marketPermission === "BLOCK") return "MARKET BLOCKED";
    if (riskPermission === "BLOCK") return "RISK BLOCKED";
    if (tickerPermission === "BLOCK") return "TICKER BLOCKED";
    if (walkForwardPermission === "BLOCK") return "SETUP FAILED";
    if (walkForwardPermission === "INSUFFICIENT") return "SETUP UNPROVEN";
    if (quality.includes("NEEDS EXECUTION PROOF") || quality.includes("STATIC FALLBACK")) return "NEEDS VERIFICATION";
    if (antiSignal === "CAUTION") return "USE CAUTION";
    return "";
  }

  function countPhrase(count, singular, plural = `${singular}s`) {
    return `${count} ${count === 1 ? singular : plural}`;
  }

  function runHealthSummary(runInfo) {
    if (!runInfo) return "";
    const parts = [];
    const failed = Number(runInfo.symbols_failed || 0);
    const stale = Number(runInfo.symbols_stale_cache || 0);
    if (runInfo.live_access_ok === false) parts.push("live source unavailable");
    if (stale) parts.push(`${countPhrase(stale, "stock")} using recent cached data`);
    if (failed) parts.push(`${countPhrase(failed, "stock")} unavailable`);
    return parts.length ? ` · ${parts.join(" · ")}` : "";
  }

  function runHealthStatus(runInfo, rows = []) {
    const failed = Number(runInfo?.symbols_failed || 0);
    const stale = Number(runInfo?.symbols_stale_cache || 0);
    const latestRows = new Map();
    rows.forEach((row) => {
      const ticker = String(row.ticker || "_");
      const date = String(row.history_date || row.data_date || row.date || "");
      const previous = latestRows.get(ticker);
      if (!previous || date > previous.date) latestRows.set(ticker, { date, row });
    });
    const rowStaleBlocks = [...latestRows.values()]
      .filter(({ row }) => String(value(row, "freshness_block") || "").toUpperCase() === "YES").length;
    const latestData = runInfo?.latest_data_date || "unknown";
    const publicationAge = marketSession?.marketSessionAge(latestData);
    const expiredRows = publicationAge > 0 ? (latestRows.size || rows.length) : 0;
    const staleBlocks = Math.max(Number(runInfo?.payload?.stale_execution_blocks ?? rowStaleBlocks), expiredRows);
    const analyzed = Number(runInfo?.symbols_analyzed || rows.length || 0);
    const total = Number(runInfo?.symbols_total || rows.length || 0);
    const liveOk = runInfo?.live_access_ok;
    const hasRows = rows.length > 0 || analyzed > 0;
    const coverage = total > 0 ? analyzed / total : (hasRows ? 1 : 0);
    const staleRatio = analyzed > 0 ? staleBlocks / analyzed : (staleBlocks ? 1 : 0);
    const globallyUnsafe = !hasRows || coverage < 0.5 || staleRatio >= 0.5;
    const hasIssue = liveOk === false || failed > 0 || stale > 0 || staleBlocks > 0 || coverage < 1;
    const tone = globallyUnsafe ? "bad" : hasIssue ? "warn" : "ok";
    const label = tone === "bad" ? "Data not safe to use" : hasIssue ? "Partial coverage" : "Data current";
    const caveats = [
      staleBlocks ? countPhrase(staleBlocks, "stale-data block") : "",
      stale ? `${countPhrase(stale, "stock")} using recent cached data` : "",
      failed ? `${countPhrase(failed, "stock")} unavailable` : "",
      liveOk === false ? "live data source unavailable" : "",
    ].filter(Boolean);
    const detail = [
      `${analyzed || total || rows.length} analysed`,
      latestData && latestData !== "unknown" ? `market data ${latestData}` : "",
      caveats.length ? caveats.join(", ") : "",
    ].filter(Boolean).join(" · ");
    return { tone, label, detail };
  }

  return Object.freeze({ qualityConstraintLabel, runHealthStatus, runHealthSummary });
}));
