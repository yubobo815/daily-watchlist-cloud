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
    return Math.abs(result) < 0.005 ? "0.00%" : `${result > 0 ? "+" : "−"}${Math.abs(result).toFixed(2)}%`;
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
  function coverage(runInfo, rows) {
    const payload = runInfo?.payload || {};
    const failed = Array.isArray(payload.failed_symbols) ? payload.failed_symbols : [];
    const missing = failed.map(item => ({ ticker: String(item.ticker || "Unknown"), reason: String(item.error || "Unavailable") }));
    const unique = new Map();
    for (const row of rows || []) {
      const blocked = ["YES", "TRUE"].includes(String(value(row, "freshness_block") || "").toUpperCase());
      const dataDate = row.data_date || row.history_date || row.date;
      const oldDate = runInfo?.latest_data_date && dataDate && String(dataDate).slice(0, 10) < String(runInfo.latest_data_date).slice(0, 10);
      if ((blocked || oldDate) && row.ticker) unique.set(row.ticker, {
        ticker: row.ticker,
        date: String(dataDate || "Unavailable").slice(0, 10),
        reason: String(value(row, "freshness_plan") || value(row, "freshness_status") || "Older market data"),
      });
    }
    const declared = number(payload.stale_execution_blocks) || 0;
    return { missing, stale: [...unique.values()], staleCount: Math.max(declared, unique.size), declaredMissing: number(runInfo?.symbols_failed) || 0 };
  }
  return Object.freeze({ value, number, zone, distance, formatDistance, compareDistance, pricePosition, transitions, coverage });
}));
