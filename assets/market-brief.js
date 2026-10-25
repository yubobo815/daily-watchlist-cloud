(function exposeMarketBrief(root, factory) {
  const sessions = typeof module === "object" && module.exports ? require("./market-session.js") : root.WatchlistMarketSession;
  const api = factory(sessions);
  if (typeof module === "object" && module.exports) module.exports = api;
  else {
    root.MarketBrief = api;
    const target = document.getElementById("market-brief");
    if (target) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 10000);
      fetch("./data/market-brief.json", { cache: "no-cache", signal: controller.signal })
        .then((response) => { if (!response.ok) throw new Error("Brief unavailable"); return response.json(); })
        .then((data) => {
          target.innerHTML = api.render(data);
          // Re-evaluate time-sensitive labels without fetching the report again.
          setInterval(() => {
            const next = api.status(data);
            target.querySelector(".brief-state").textContent = next.dated ? "Dated report — awaiting a newer session" : "Latest completed US session";
            target.querySelector(".brief-outlook .brief-eyebrow").textContent = next.expired ? "FORECAST WINDOW ENDED · ARCHIVED OUTLOOK" : "RESEARCH OUTLOOK · NOT A TRADE SIGNAL";
          }, 60000);
        })
        .catch(() => { target.innerHTML = '<h2>Market overview</h2><p class="subtle">Daily research is unavailable. The watchlist remains independent; please check again later.</p>'; })
        .finally(() => clearTimeout(timer));
    }
  }
}(typeof globalThis !== "undefined" ? globalThis : this, function buildMarketBrief(sessions) {
  const escape = (value) => String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
  function validate(data) {
    const fail = () => { throw new Error("Invalid market brief"); };
    const text = (value, max = 1200) => { if (typeof value !== "string" || !value.trim() || value.length > max) fail(); };
    const date = (value) => { text(value, 40); if (!Number.isFinite(Date.parse(value))) fail(); };
    if (!data || data.schema_version !== 1) fail();
    if (!/^\d{4}-\d{2}-\d{2}$/.test(data.session_date) || new Date(data.session_date).toISOString().slice(0, 10) !== data.session_date) fail();
    date(data.issued_at);
    if (Date.parse(data.issued_at) < Date.parse(data.session_date)) fail();
    [data.headline, data.summary, data.limitations].forEach((value) => text(value));
    for (const [items, fields, max] of [[data.metrics, ["label", "value", "detail"], 6], [data.highlights, ["title", "text"], 5]]) {
      if (!Array.isArray(items) || !items.length || items.length > max) fail();
      items.forEach((item) => fields.forEach((field) => text(item[field])));
    }
    const f = data.forecast;
    if (!f) fail();
    [f.id, f.outlook, f.horizon, f.method, f.watch_next].forEach((value) => text(value));
    date(f.evaluates_at);
    if (Date.parse(f.evaluates_at) <= Date.parse(data.issued_at)) fail();
    if (![f.lower_bound, f.upper_bound, f.reference_close].every((value) => Number.isFinite(value) && value > 0) || f.lower_bound >= f.upper_bound) fail();
    const p = ["bull", "base", "bear"].map((key) => f.probabilities?.[key]);
    if (p.some((value) => !Number.isFinite(value) || value < 0 || value > 100) || Math.abs(p.reduce((sum, value) => sum + value, 0) - 100) > 0.001) fail();
    if (!Number.isInteger(f.completed_sample) || f.completed_sample < 0) fail();
    if (!Array.isArray(data.sources) || data.sources.length < 2 || data.sources.length > 12) fail();
    data.sources.forEach((source) => {
      text(source.label); text(source.url, 2000);
      const url = new URL(source.url);
      if (url.protocol !== "https:" || url.username || url.password) fail();
      if (source.modified_at) date(source.modified_at);
    });
    return data;
  }
  function status(data, now = new Date()) {
    const age = sessions.marketSessionAge(data.session_date, now);
    return { dated: age === null || age > 0 || Date.parse(data.issued_at) > now.getTime(), expired: now.getTime() >= Date.parse(data.forecast.evaluates_at) };
  }
  function renderChange(detail) {
    // Colour the reported signed move only, not its neutral source/context label.
    // Both the ASCII hyphen and the typographic minus occur in daily reports.
    const match = /^([+\-−])\s*(\d[\d,]*(?:\.\d+)?)(\s*(?:%|bps?\b|pp\b|points?\b))?/i.exec(detail);
    if (!match || Number(match[2].replace(/,/g, "")) === 0) return escape(detail);
    const direction = match[1] === "+" ? "up" : "down";
    return `<span class="brief-change-${direction}">${escape(match[0])}</span>${escape(detail.slice(match[0].length))}`;
  }
  function render(input, now = new Date()) {
    const data = validate(input); const f = data.forecast; const state = status(data, now);
    const stamp = (value) => escape(new Intl.DateTimeFormat("en-AU", { timeZone: "Australia/Melbourne", dateStyle: "medium", timeStyle: "short" }).format(new Date(value)));
    const probabilities = [
      ["bull", "Bull", `Final close > ${f.upper_bound.toLocaleString("en-AU")}`],
      ["base", "Base", `${f.lower_bound.toLocaleString("en-AU")}–${f.upper_bound.toLocaleString("en-AU")} inclusive`],
      ["bear", "Bear", `Final close < ${f.lower_bound.toLocaleString("en-AU")}`],
    ];
    const shortSummary = data.summary.match(/^.*?[.!?](?:\s|$)/)?.[0]?.trim() || data.summary;
    const metricLabel = label => ({"Nasdaq Composite":"Nasdaq", "US 10-year yield":"US 10-year", "Brent futures":"Brent"}[label] || label);
    return `<details class="research-brief" open><summary class="brief-toggle"><span class="brief-heading"><h2>Daily Brief</h2><span class="brief-toggle-label"><span class="when-open">Collapse</span><span class="when-closed">Expand</span></span></span>
      <h3 class="brief-headline">${escape(data.headline)}</h3><span class="brief-summary when-open">${escape(shortSummary)}</span><span class="brief-summary when-closed">${escape(shortSummary)}</span>
      <div class="brief-outlook"><p class="brief-eyebrow">${state.expired ? "FORECAST WINDOW ENDED · ARCHIVED OUTLOOK" : "RESEARCH OUTLOOK · NOT A TRADE SIGNAL"}</p><h3>${escape(f.outlook)}</h3><p>${escape(f.horizon)}</p>
      <div class="probability-strip" role="img" aria-label="${probabilities.map(([key, label]) => `${label} ${f.probabilities[key]}%`).join(", ")}">${probabilities.map(([key, label]) => `<span class="probability-segment segment-${key}" style="flex-basis:${f.probabilities[key]}%" ${f.probabilities[key] === 0 ? 'hidden' : ""}><span>${label}</span><strong>${f.probabilities[key]}%</strong></span>`).join("")}</div></div></summary>
      <div class="brief-body"><div class="brief-meta"><span class="brief-date">US session ${escape(data.session_date)} · Published ${stamp(data.issued_at)} Melbourne</span><span class="brief-state">${state.dated ? "Dated report — awaiting a newer session" : "Latest completed US session"}</span></div>
      <div class="brief-metrics">${data.metrics.map((m) => `<div><span>${escape(metricLabel(m.label))}</span><strong>${escape(m.value)}</strong><small title="${escape(m.detail)}">${renderChange(m.detail.split(/\s·\s/)[0])}</small></div>`).join("")}</div>
      <details class="full-brief"><summary>Read full brief</summary><p class="brief-full-summary">${escape(data.summary)}</p><div class="brief-developments">${data.highlights.map((h) => `<article><h4>${escape(h.title)}</h4><p>${escape(h.text)}</p></article>`).join("")}</div>
      <div class="scenario-ranges">${probabilities.map(([, label, boundary]) => `<small><b>${label}</b> ${escape(boundary)}</small>`).join("")}</div></details></div></details>`;
  }
  return Object.freeze({ validate, status, render, renderChange });
}));
