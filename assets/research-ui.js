(function exposeResearchUI(root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.ResearchUI = api;
}(typeof globalThis !== "undefined" ? globalThis : this, function buildResearchUI() {
  // Presentation calculations only. Never infer or change a scanner signal.
  const value = (row, key) => row?.[key] ?? row?.payload?.[key];
  function number(input) {
    if (input === null || input === undefined || String(input).trim() === "") return null;
    const result = Number(input);
    return Number.isFinite(result) ? result : null;
  }
  function readinessScore(row) {
    const raw = value(row, "shadow_readiness_score");
    const score = typeof raw === "number" || typeof raw === "string" ? number(raw) : null;
    return score !== null && score >= 0 && score <= 100 ? score : null;
  }
  function readinessFactors(row) {
    return [
      ["trend", "Trend", 25], ["entry", "Entry quality", 20],
      ["momentum", "Momentum", 15], ["volume_demand", "Volume / demand", 15],
      ["relative_strength", "Relative strength", 10], ["market", "Market environment", 10],
      ["history", "Historical evidence", 5],
    ].map(([key, label, weight]) => {
      const score = number(value(row, "shadow_readiness_" + key));
      return { key, label, weight, score: score !== null && score >= 0 && score <= 100 ? score : null };
    });
  }
  function zone(row) {
    const frozen = ["ARMED", "MODEL_FILLED", "TP1_HIT"].includes(String(value(row, "execution_plan_status") || "").toUpperCase());
    const high = number(frozen ? value(row, "execution_plan_zone_high") : value(row, "entry_zone_high") ?? value(row, "entry_est"));
    const low = number(frozen ? value(row, "execution_plan_zone_low") : value(row, "entry_zone_low") ?? high);
    return low !== null && high !== null && low > 0 && high >= low ? { low, high, frozen } : null;
  }
  function distance(row) {
    const bounds = zone(row); const close = number(value(row, "close"));
    if (!bounds || close === null || close <= 0) return null;
    if (close < bounds.low) return (close - bounds.low) / bounds.low * 100;
    if (close > bounds.high) return (close - bounds.high) / bounds.high * 100;
    return 0;
  }
  function formatDistance(row) {
    const result = distance(row);
    if (result === null) return "Unavailable";
    // Avoid displaying a signed zero caused by rounding a tiny move.
    if (result === 0) return "Inside";
    return Math.abs(result) < 0.005 ? `${result > 0 ? "+" : "−"}<0.01%` : `${result > 0 ? "+" : "−"}${Math.abs(result).toFixed(2)}%`;
  }
  function compareDistance(a, b) {
    const left = distance(a); const right = distance(b);
    if (left === null && right !== null) return 1;
    if (right === null && left !== null) return -1;
    const delta = left === null ? 0 : Math.abs(left) - Math.abs(right);
    return delta || String(a.ticker || "").localeCompare(String(b.ticker || ""));
  }
  function pricePosition(row) {
    const bounds = zone(row); const close = number(value(row, "close"));
    if (!bounds || close === null || close <= 0) return null;
    const spread = Math.max(bounds.high - bounds.low, close * 0.012);
    const min = Math.min(close, bounds.low) - spread * 0.65;
    const max = Math.max(close, bounds.high) + spread * 0.65;
    const position = n => (n - min) / (max - min) * 100;
    return { ...bounds, close, lowPosition: position(bounds.low), highPosition: position(bounds.high), closePosition: position(close), relation: close < bounds.low ? "Below planned zone" : close > bounds.high ? "Above planned zone" : "Inside planned zone" };
  }
  function transitions(rows, limit = 5) {
    const byDate = new Map();
    for (const row of rows || []) {
      const date = String(row.history_date || row.data_date || row.date || "").slice(0, 10);
      if (/^\d{4}-\d{2}-\d{2}$/.test(date) && row.action) byDate.set(date, { ...row, date });
    }
    const ordered = [...byDate.values()].sort((a, b) => a.date.localeCompare(b.date));
    const changes = [];
    for (let i = 1; i < ordered.length; i += 1) {
      if (ordered[i].action !== ordered[i - 1].action) changes.push({ date: ordered[i].date, from: ordered[i - 1].action, to: ordered[i].action });
    }
    return { changes: changes.slice(-limit).reverse(), total: changes.length, sessions: ordered.length, first: ordered[0] || null };
  }
  const marketKey = row => /\.AX$/i.test(String(row?.ticker || "")) ? "ASX" : "US";
  function rowDate(row) {
    const date = String(row?.data_date || row?.history_date || row?.date || "").slice(0, 10);
    return /^\d{4}-\d{2}-\d{2}$/.test(date) && Number.isFinite(Date.parse(date)) && new Date(date).toISOString().slice(0, 10) === date ? date : null;
  }
  function latestUSDataDate(rows) {
    return (rows || []).filter(row => row.ticker && marketKey(row) === "US").map(rowDate).filter(Boolean).sort().at(-1) || null;
  }
  function coverage(runInfo, rows) {
    const payload = runInfo?.payload || {};
    const failed = Array.isArray(payload.failed_symbols) ? payload.failed_symbols : [];
    const missing = failed.map(item => ({ ticker: String(item.ticker || "Unknown"), reason: String(item.error || "Unavailable") }));
    const unique = new Map();
    // Ticker pages initially pass a history series. Coverage describes current
    // inputs, not old sessions: retain only the latest dated row per ticker.
    const current = new Map();
    for (const row of rows || []) {
      const previous = current.get(row.ticker);
      if (!previous || (rowDate(row) || "") > (rowDate(previous) || "")) current.set(row.ticker, row);
    }
    const latestByMarket = new Map();
    for (const row of current.values()) {
      const date = rowDate(row); const key = marketKey(row);
      if (date && (!latestByMarket.has(key) || date > latestByMarket.get(key))) latestByMarket.set(key, date);
    }
    for (const row of current.values()) {
      const blocked = ["YES", "TRUE"].includes(String(value(row, "freshness_block") || "").toUpperCase());
      const dataDate = rowDate(row);
      // US and ASX have different session dates. A newer ASX date must not
      // mark every current US row stale; explicit scanner blocks remain intact.
      const oldDate = dataDate && dataDate < latestByMarket.get(marketKey(row));
      if ((blocked || oldDate) && row.ticker) unique.set(row.ticker, {
        ticker: row.ticker,
        date: String(dataDate || "Unavailable").slice(0, 10),
        reason: String(value(row, "freshness_plan") || value(row, "freshness_status") || "Older market data"),
      });
    }
    // Publication metadata can identify old cache inputs before a ticker page's
    // full directory finishes loading. Do not invent their unavailable dates.
    for (const item of Array.isArray(payload.stale_cache_fallbacks) ? payload.stale_cache_fallbacks : []) {
      if (item.ticker && !unique.has(item.ticker)) unique.set(item.ticker, {
        ticker: item.ticker, date: "Unavailable",
        reason: String(item.error || "Old cache input; source date unavailable in this view"),
      });
    }
    const declared = number(payload.stale_execution_blocks) || 0;
    return { missing, stale: [...unique.values()], staleCount: Math.max(declared, unique.size), declaredMissing: number(runInfo?.symbols_failed) || 0 };
  }
  return Object.freeze({ value, number, readinessScore, readinessFactors, zone, distance, formatDistance, compareDistance, pricePosition, transitions, latestUSDataDate, coverage });
}));
