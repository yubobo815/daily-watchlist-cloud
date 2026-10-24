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
          // Re-evaluate time-sensitive labels without collapsing an open source disclosure.
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
  function render(input, now = new Date()) {
    const data = validate(input); const f = data.forecast; const state = status(data, now);
    const stamp = (value) => escape(new Intl.DateTimeFormat("en-AU", { timeZone: "Australia/Melbourne", dateStyle: "medium", timeStyle: "short" }).format(new Date(value)));
    const probabilities = [
      ["bull", "Bull", `Final close > ${f.upper_bound.toLocaleString("en-AU")}`],
      ["base", "Base", `${f.lower_bound.toLocaleString("en-AU")}–${f.upper_bound.toLocaleString("en-AU")} inclusive`],
      ["bear", "Bear", `Final close < ${f.lower_bound.toLocaleString("en-AU")}`],
    ];
    return `<div class="brief-heading"><div><p class="brief-eyebrow">INDEPENDENT RESEARCH · DAILY BRIEF</p><h2>Market overview</h2></div><span class="brief-state">${state.dated ? "Dated report — awaiting a newer session" : "Latest completed US session"}</span></div>
      <p class="brief-date">US session ${escape(data.session_date)} · Published ${stamp(data.issued_at)} Melbourne</p>
      <h3 class="brief-headline">${escape(data.headline)}</h3><p>${escape(data.summary)}</p>
      <div class="brief-metrics">${data.metrics.map((m) => `<div><span>${escape(m.label)}</span><strong>${escape(m.value)}</strong><small>${escape(m.detail)}</small></div>`).join("")}</div>
      <div class="brief-columns"><div class="brief-developments">${data.highlights.map((h) => `<article><h4>${escape(h.title)}</h4><p>${escape(h.text)}</p></article>`).join("")}</div>
      <div class="brief-outlook"><p class="brief-eyebrow">${state.expired ? "FORECAST WINDOW ENDED · ARCHIVED OUTLOOK" : "RESEARCH OUTLOOK · NOT A TRADE SIGNAL"}</p><h3>${escape(f.outlook)}</h3><p>${escape(f.horizon)}</p>
      <div class="brief-scenarios">${probabilities.map(([key, label, boundary]) => `<div class="brief-scenario"><span>${label}</span><strong>${f.probabilities[key]}%</strong><small>${escape(boundary)}</small><progress max="100" value="${f.probabilities[key]}" aria-label="${label} probability">${f.probabilities[key]}%</progress></div>`).join("")}</div>
      <p class="brief-note">${escape(f.method)} Completed forecast sample: ${f.completed_sample}.</p></div></div>
      <details class="brief-details"><summary>Forecast conditions &amp; sources</summary><p>${escape(f.watch_next)}</p><p>Reference S&amp;P 500: ${f.reference_close.toLocaleString("en-AU")}. Evaluate at ${stamp(f.evaluates_at)} Melbourne. Forecast ID: ${escape(f.id)}. Original forecasts are not revised retrospectively.</p><p>${escape(data.limitations)}</p><ul>${data.sources.map((s) => `<li><a href="${escape(s.url)}" target="_blank" rel="noopener noreferrer">${escape(s.label)}</a></li>`).join("")}</ul></details>`;
  }
  return Object.freeze({ validate, status, render });
}));
