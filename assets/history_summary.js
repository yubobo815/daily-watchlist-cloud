(function exposeHistorySummary(root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else if (root) root.HistorySummary = api;
}(typeof globalThis !== "undefined" ? globalThis : this, function buildHistorySummary() {
  const DEFAULT_PRESSURE_THRESHOLD = 8;

  function numericValue(row, key) {
    const raw = row?.payload?.[key] ?? row?.[key];
    if (raw == null || raw === "") return null;
    const number = Number(raw);
    return Number.isFinite(number) ? number : null;
  }

  function median(values) {
    const sorted = values.filter(Number.isFinite).sort((a, b) => a - b);
    if (!sorted.length) return null;
    const middle = Math.floor(sorted.length / 2);
    return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
  }

  function sessionDate(row) {
    const raw = String(row?.history_date || row?.date || "");
    if (!/^\d{4}-\d{2}-\d{2}$/.test(raw)) return "";
    const parsed = new Date(`${raw}T00:00:00Z`);
    return Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== raw ? "" : raw;
  }

  function chronologicalWindow(rows, limit = 30) {
    const sourceRows = Array.isArray(rows) ? [...rows] : [];
    const dates = sourceRows.map(sessionDate);
    if (dates.some((date) => !date)) return { rows: [], available: false };
    sourceRows.sort((left, right) => sessionDate(left).localeCompare(sessionDate(right)));
    return { rows: sourceRows.slice(-limit), available: true };
  }

  function historyMetrics(rows) {
    const window = chronologicalWindow(rows);
    if (!window.available) return { rows: [], available: false, priceAvailable: false, reason: "dates" };
    const windowRows = window.rows;
    if (!windowRows.length) return { rows: [], available: false, priceAvailable: false };
    const closes = windowRows.map((row) => numericValue(row, "close"));
    if (!closes.every((close) => close > 0)) {
      return { rows: windowRows, available: true, priceAvailable: false, reason: "prices" };
    }
    const firstClose = closes[0];
    const latestClose = closes.at(-1);
    const priceMovePct = ((latestClose / firstClose) - 1) * 100;
    let peakClose = -Infinity;
    let maxDrawdownPct = 0;
    closes.forEach((close) => {
      peakClose = Math.max(peakClose, close);
      if (peakClose > 0) maxDrawdownPct = Math.min(maxDrawdownPct, ((close / peakClose) - 1) * 100);
    });
    const highs = windowRows.map((row) => numericValue(row, "high"));
    const completeHighs = highs.every((high, index) => high != null && high >= closes[index]);
    const highestHigh = completeHighs ? Math.max(...highs) : null;
    const distanceFromHighPct = highestHigh > 0 ? ((latestClose / highestHigh) - 1) * 100 : null;
    return {
      rows: windowRows,
      available: true,
      priceAvailable: true,
      priceMovePct,
      maxDrawdownPct,
      distanceFromHighPct,
    };
  }

  function pressureComparison(rows, neutralThreshold = 8) {
    const window = chronologicalWindow(rows);
    if (!window.available) return { available: false, reason: "dates" };
    const sourceRows = window.rows;
    if (sourceRows.length < 30) return { available: false, reason: "window" };
    const threshold = Number.isFinite(neutralThreshold) && neutralThreshold > 0
      ? neutralThreshold
      : DEFAULT_PRESSURE_THRESHOLD;
    const pressure = (row) => {
      const buyer = numericValue(row, "buyer_score");
      const seller = numericValue(row, "seller_score");
      return buyer == null || seller == null ? null : buyer - seller;
    };
    const recentValues = sourceRows.slice(-5).map(pressure).filter(Number.isFinite);
    const priorValues = sourceRows.slice(-30, -5).map(pressure).filter(Number.isFinite);
    if (recentValues.length < 5 || priorValues.length < 25) return { available: false, reason: "scores" };
    const recentMedian = median(recentValues);
    const priorMedian = median(priorValues);
    const change = recentMedian - priorMedian;
    const shift = change >= threshold ? "buying" : change <= -threshold ? "selling" : "balanced";
    const control = recentMedian >= threshold ? "buying" : recentMedian <= -threshold ? "selling" : "balanced";
    return { available: true, recentMedian, priorMedian, change, shift, control };
  }

  function signalTransition(rows) {
    const window = chronologicalWindow(rows);
    if (!window.available) return { available: false, reason: "dates" };
    if (window.rows.some((row) => !row?.action)) return { available: false, reason: "actions" };
    const sourceRows = window.rows;
    if (!sourceRows.length) return { available: false };
    const latestIndex = sourceRows.length - 1;
    const currentAction = sourceRows[latestIndex].action;
    for (let index = latestIndex; index > 0; index -= 1) {
      if (sourceRows[index - 1].action !== currentAction) {
        return {
          available: true,
          changed: true,
          currentAction,
          previousAction: sourceRows[index - 1].action,
          sessionsAgo: latestIndex - index,
        };
      }
    }
    return { available: true, changed: false, currentAction, windowSessions: sourceRows.length };
  }

  function interpretationState(kind, { stale = false, checksClear = false } = {}) {
    if (stale) return kind === "exit" || kind === "avoid" ? `stale-${kind}` : "stale";
    if (kind === "exit" || kind === "avoid") return kind;
    if (!checksClear) return "blocked";
    return kind || "wait";
  }

  return Object.freeze({ historyMetrics, pressureComparison, signalTransition, interpretationState });
}));
