/* v5 presentation adapter. Existing scanner decisions and validation functions are reused. */
(function initialiseResearchWorkspace() {
  "use strict";
  const ui = window.ResearchUI;
  const pageIsTicker = document.body.classList.contains("ticker-page");
  const historyCache = new Map();
  let pageNumber = 1;
  let pageSignature = "";
  let coverageRows = [];
  let coverageRun = null;
  let initialNavigationDone = false;
  let mobileExpandedTicker = "";
  let nearOnly = false;
  const requestedTicker = new URLSearchParams(location.search).get("ticker");
  const originalSelectTicker = window.selectTicker;
  const originalLoadDirectory = window.loadTickerDirectory;
  const fmt = n => Number(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const label = action => ACTION_LABELS[action] || action;
  const escaped = escapeHtml;
  const badge = row => `<span class="badge ${actionKind(row.action)}">${escaped(label(row.action))}</span>`;
  // Presentation bands only: colours never grant entry permission.
  const readinessTone = score => score === null ? "unavailable" : score >= 75 ? "high" : score >= 50 ? "mid" : "low";
  function readiness(row) {
    const score = ui.readinessScore(row);
    const status = qualityConstraintLabel(row);
    const dated = freshnessBlocked(row);
    const date = String(row.data_date || row.history_date || row.date || "Unavailable").slice(0, 10);
    const context = [status, dated ? "As of " + date : "", "Setup evidence, not a win probability"].filter(Boolean).join(" · ");
    return `<span class="readiness-label readiness-compact ${dated ? "is-dated" : ""}" data-readiness-tone="${readinessTone(score)}" title="${escaped(context)}">${score === null
      ? '<span class="readiness-value">Not scored</span>'
      : `<span class="readiness-value">${Math.round(score)}</span><meter min="0" max="100" value="${score}" aria-label="Signal readiness for ${escaped(row.ticker)}">${score}/100</meter>`}
      </span>`;
  }
  window.renderQualityScore = readiness;

  function coverageMarkup(runInfo, rows) {
    const result = ui.coverage(runInfo, rows);
    return `<div class="coverage-content"><h3>Coverage details</h3>
      <section><h4>Unavailable stocks (${result.declaredMissing || result.missing.length})</h4>
      ${result.missing.length ? `<ul>${result.missing.map(item => `<li><strong>${escaped(item.ticker)}</strong><span>${escaped(item.reason)}</span></li>`).join("")}</ul>` : `<p>${result.declaredMissing ? "The publication reports missing stocks but did not provide their names." : "No unavailable stocks reported."}</p>`}</section>
      <section><h4>Stale or older inputs (${result.staleCount})</h4>
      ${result.stale.length ? `<ul>${result.stale.map(item => `<li><strong>${escaped(item.ticker)}</strong><span>${escaped(item.date)} · ${escaped(item.reason)}</span></li>`).join("")}</ul>` : `<p>${result.staleCount ? "The run reports stale inputs; their identities are not available in this view yet." : "No stale inputs reported."}</p>`}
      ${result.staleCount > result.stale.length && result.stale.length ? '<p>Additional stale inputs were counted by the publication but not identified in this view.</p>' : ""}</section></div>`;
  }

  window.renderMarketRail = function renderResearchRail(runInfo, rows = []) {
    coverageRun = runInfo || coverageRun;
    if (!pageIsTicker || rows.length > coverageRows.length) coverageRows = rows;
    const rail = document.querySelector("#market-rail");
    if (!rail) return;
    const health = runHealthStatus(runInfo, rows);
    const wasOpen = Boolean(rail.querySelector("details[open]"));
    const analyzed = Number(runInfo?.symbols_analyzed ?? rows.length);
    const total = Number(runInfo?.symbols_total ?? rows.length);
    const date = ui.latestUSDataDate(rows) || "Unavailable";
    const partial = health.label.toLowerCase().includes("partial") || analyzed < total || ui.coverage(runInfo, rows).staleCount > 0;
    rail.innerHTML = `<a class="rail-home" href="./">Daily Trade Copilot</a>
      <span>US close <strong>${escaped(date)}</strong></span><span>Coverage <strong>${analyzed}/${total}</strong></span>
      <details class="coverage-disclosure" ${wasOpen ? "open" : ""}><summary class="${partial ? "coverage-partial" : ""}">${escaped(partial ? "Partial coverage" : health.label)}</summary>${coverageMarkup(runInfo, coverageRows.length ? coverageRows : rows)}</details>`;
    const hero = document.querySelector("#hero-brief");
    if (hero) { hero.innerHTML = ""; hero.hidden = true; }
  };

  function zoneMarkup(row) {
    const zone = ui.zone(row);
    return zone ? `${fmt(zone.low)}–${fmt(zone.high)}` : "Unavailable";
  }

  function distanceMarkup(row) {
    const distance = ui.distance(row);
    const near = distance !== null && Math.abs(distance) <= 1 && !["exit", "avoid"].includes(actionKind(row.action)) && !freshnessBlocked(row);
    return `<span class="zone-distance ${near ? "near-zone" : ""}" title="Inside means the close is within the planned zone. Outside values show signed distance to the nearest boundary. Proximity is not entry permission.">${escaped(ui.formatDistance(row))}</span>`;
  }

  function freshnessBlocked(row) {
    const flagged = ["YES", "TRUE"].includes(String(payloadValue(row, "freshness_block") || "").toUpperCase());
    const date = row.data_date || row.date;
    return flagged || window.WatchlistMarketSession.marketSessionAge(date) > 0;
  }

  function protection(row) {
    if (activeExecutionPlan(row)) return ui.number(payloadValue(row, "execution_plan_stop"));
    return executionChecksClear(row) && ["buy", "continue"].includes(actionKind(row.action)) ? ui.number(row.stop_est) : null;
  }
  function loss(row) {
    if (activeExecutionPlan(row)) return ui.number(payloadValue(row, "execution_plan_risk_pct"));
    return executionChecksClear(row) && ["buy", "continue"].includes(actionKind(row.action)) ? ui.number(payloadValue(row, "risk_pct_to_stop")) : null;
  }

  function columns() {
    return [
      ["ticker", "Ticker / company"], ["action", "Signal"], ["readiness", "Signal readiness"], ["zone", "Planned entry zone"], ["distance", "Distance to zone"],
    ];
  }

  function favourite(row) {
    return `<button class="focus-toggle ${isFocusTicker(row.ticker) ? "active" : ""}" type="button" data-focus-ticker="${escaped(row.ticker)}" aria-label="${isFocusTicker(row.ticker) ? "Remove" : "Add"} ${escaped(row.ticker)} from Focus List">${isFocusTicker(row.ticker) ? "★" : "☆"}</button>`;
  }

  function cell(row, key) {
    if (key === "ticker") return `<span class="v5-ticker-cell">${favourite(row)}<span><button class="ticker-link" data-select-ticker="${escaped(row.ticker)}" type="button">${escaped(row.ticker)}</button><small class="ticker-name">${escaped(displaySecurityName(row.name, row.ticker) || row.ticker)}</small></span></span>`;
    if (key === "action") return badge(row);
    if (key === "readiness") return readiness(row);
    if (key === "zone") return `<span class="zone-values">${escaped(zoneMarkup(row))}</span>`;
    if (key === "distance") return distanceMarkup(row);
    return "";
  }

  function mobileCard(row) {
    return `<div class="v5-stock-card"><button type="button" data-mobile-ticker="${escaped(row.ticker)}" aria-expanded="${mobileExpandedTicker === row.ticker}" aria-controls="mobile-detail-${escaped(row.ticker)}" class="v5-stock-link">
      <span class="v5-card-identity"><strong>${escaped(row.ticker)}</strong><span>${escaped(displaySecurityName(row.name, row.ticker) || row.ticker)}</span></span>
      <span class="v5-card-badges">${badge(row)}${readiness(row)}</span>
      <span class="v5-card-distance"><small>Distance to planned zone</small>${distanceMarkup(row)}</span></button></div>${mobileExpandedTicker === row.ticker ? `<section id="mobile-detail-${escaped(row.ticker)}" class="mobile-inline-detail" aria-label="${escaped(row.ticker)} supporting evidence"></section>` : ""}`;
  }

  function resetPaginationIfNeeded() {
    const next = [state.query, state.filter, state.sort, state.rows[0]?.publication_id || state.rows[0]?.run_date, state.focusTickers.join(",")].join("|");
    if (next !== pageSignature) pageNumber = 1;
    pageSignature = next;
  }

  window.renderWatchlist = function renderResearchWatchlist({ refreshOverview = true } = {}) {
    const counts = { buy: 0, continue: 0, setup: 0, watch: 0, exit: 0, avoid: 0 };
    state.rows.forEach(row => { counts[actionKind(row.action)] += 1; });
    if (refreshOverview) { renderCards(counts); renderMarketActivity(); renderNotificationCenter(); }
    const exact = exactTickerSearchNeedle(state.query, state.rows);
    const searchActive = Boolean(state.query.trim());
    document.body.classList.toggle("search-active", searchActive);
    const filtered = state.rows.filter(row => {
      const kind = actionKind(row.action);
      const filter = state.filter === "building" ? ["continue", "setup", "watch"].includes(kind)
        : state.filter === "risk" ? ["exit", "avoid"].includes(kind)
        : state.filter === "favourites" ? isFocusTicker(row.ticker)
        : state.filter === "all" || kind === state.filter;
      const distance = ui.distance(row);
      return (searchActive || filter) && rowMatchesSearch(row, state.query, exact) && (!nearOnly || (distance !== null && Math.abs(distance) <= 1));
    });
    const [sortKey, direction] = state.sort.split("-");
    filtered.sort((a, b) => sortKey === "distance" ? ui.compareDistance(a, b)
      : sortKey === "ticker" ? a.ticker.localeCompare(b.ticker)
      : sortKey === "score" ? (ui.readinessScore(b) ?? -1) - (ui.readinessScore(a) ?? -1) || a.ticker.localeCompare(b.ticker)
      : (Number(a[sortKey] || 0) - Number(b[sortKey] || 0)) * (direction === "asc" ? 1 : -1) || a.ticker.localeCompare(b.ticker));
    state.visibleRows = filtered;
    document.querySelector("#sort").value = state.sort;
    const mobileSort = document.querySelector("#mobile-sort");
    if (mobileSort) mobileSort.value = state.sort;
    resetPaginationIfNeeded();
    if (!initialNavigationDone && filtered.length) {
      const requestedIndex = requestedTicker ? filtered.findIndex(row => row.ticker === requestedTicker) : -1;
      if (requestedIndex >= 0) pageNumber = Math.floor(requestedIndex / INITIAL_WATCHLIST_ROWS) + 1;
      if (!requestedTicker) state.selectedTicker = filtered[0].ticker;
      initialNavigationDone = true;
    }
    const totalPages = Math.max(1, Math.ceil(filtered.length / INITIAL_WATCHLIST_ROWS));
    pageNumber = Math.min(pageNumber, totalPages);
    const shown = filtered.slice((pageNumber - 1) * INITIAL_WATCHLIST_ROWS, pageNumber * INITIAL_WATCHLIST_ROWS);
    if (!shown.some(row => row.ticker === state.selectedTicker)) state.selectedTicker = shown[0]?.ticker || "";
    const visibleColumns = columns(filtered);
    document.querySelector("#watchlist-head").innerHTML = `<tr>${visibleColumns.map(([key, text]) => `<th scope="col" class="col-${key}">${escaped(text)}</th>`).join("")}</tr>`;
    document.querySelector("#watchlist-body").innerHTML = shown.map(row => {
      const previous = state.previousByTicker.get(row.ticker);
      const changed = previous && previous.action !== row.action;
      return `<tr class="row-${actionKind(row.action)} ${row.ticker === state.selectedTicker ? "selected" : ""} ${changed ? "recent-change" : ""}" data-select-ticker="${escaped(row.ticker)}" aria-selected="${row.ticker === state.selectedTicker}">
      ${visibleColumns.map(([key]) => `<td class="col-${key}">${cell(row, key)}</td>`).join("")}<td class="mobile-summary">${mobileCard(row)}</td></tr>`;
    }).join("");
    const start = filtered.length ? (pageNumber - 1) * INITIAL_WATCHLIST_ROWS + 1 : 0;
    document.querySelector("#count").textContent = `${start}–${Math.min(pageNumber * INITIAL_WATCHLIST_ROWS, filtered.length)} of ${filtered.length} · ${state.rows.length} total`;
    const mobileCount = document.querySelector("#mobile-search-count");
    if (mobileCount) mobileCount.textContent = `${filtered.length} shown`;
    document.querySelector("#empty").classList.toggle("hidden", filtered.length > 0);
    document.querySelectorAll("[data-mobile-filter], #cards [data-filter], [data-workspace-filter]").forEach(button => {
      const active = !searchActive && (button.dataset.mobileFilter || button.dataset.filter || button.dataset.workspaceFilter) === state.filter;
      button.classList.toggle("active", active); button.setAttribute("aria-pressed", String(active));
    });
    const pagination = document.querySelector("#research-pagination");
    if (pagination) {
      pagination.innerHTML = `<button type="button" data-page-step="-1" ${pageNumber <= 1 ? "disabled" : ""}>Previous</button><span>Page ${pageNumber} of ${totalPages}</span><button type="button" data-page-step="1" ${pageNumber >= totalPages ? "disabled" : ""}>Next</button><a href="#watchlist-table" class="back-to-list-top">Back to list top ↑</a>`;
    }
    const legacyShowMore = document.querySelector("#show-more");
    if (legacyShowMore) legacyShowMore.hidden = true;
    try { if (state.selectedTicker) sessionStorage.setItem("research-watchlist-order-v5", JSON.stringify(filtered.map(row => row.ticker))); } catch { /* Storage may be disabled; directory navigation still works. */ }
    renderTickerDetailPanel();
  };

  function transitionsMarkup(rows, loading = false, failed = false, compact = false) {
    if (loading) return '<p class="subtle">Loading recorded state changes…</p>';
    if (failed) return '<p class="subtle">Recorded state changes are temporarily unavailable.</p>';
    const result = ui.transitions(rows);
    if (!result.changes.length) return `<p class="subtle">${result.sessions ? `No signal changes in ${result.sessions} available sessions.` : "No recorded state changes available."}</p>`;
    const item = change => `<li><time>${escaped(change.date)}</time><span>${escaped(label(change.from))} <span aria-hidden="true">→</span> <strong>${escaped(label(change.to))}</strong></span></li>`;
    return `<ol class="state-timeline">${(compact ? result.changes.slice(0, 2) : result.changes).map(item).join("")}</ol>${compact && result.changes.length > 2 ? `<details class="earlier-changes"><summary>Earlier changes</summary><ol class="state-timeline">${result.changes.slice(2).map(item).join("")}</ol></details>` : ""}<p class="timeline-window">${result.total} recorded changes across ${result.sessions} available sessions.</p>`;
  }

  async function loadPanelHistory(ticker) {
    if (historyCache.has(ticker)) return;
    if (historyCache.size >= 20) historyCache.delete(historyCache.keys().next().value);
    historyCache.set(ticker, { loading: true, rows: [] });
    try {
      const result = isGithubPagesHost() ? await loadStaticTickerHistory(ticker) : await appApiFetch(`/api/ticker/${encodeURIComponent(ticker)}`, { ttl: SUPABASE_CACHE_TTL_MS });
      historyCache.set(ticker, { rows: result.historyRows || result.rows || [] });
    } catch { historyCache.set(ticker, { failed: true, rows: [] }); }
    if (state.selectedTicker === ticker) renderTickerDetailPanel();
  }

  window.renderTickerDetailPanel = function renderResearchDetailPanel() {
    const panel = document.querySelector("#ticker-detail-panel");
    if (!panel) return;
    const row = state.visibleRows.find(item => item.ticker === state.selectedTicker);
    if (!row) { panel.innerHTML = '<p class="subtle">Choose a stock to read its supporting evidence.</p>'; return; }
    const history = historyCache.get(row.ticker) || { loading: true, rows: [] };
    const index = state.visibleRows.findIndex(item => item.ticker === row.ticker);
    const plan = protection(row) > 0 || loss(row) > 0 ? `<section class="recorded-plan"><h3>${activeExecutionPlan(row) ? "Existing frozen plan" : "Qualified plan"}</h3><dl class="plan-facts">${protection(row) > 0 ? `<div><dt>Protection</dt><dd>${fmt(protection(row))}</dd></div>` : ""}${loss(row) > 0 ? `<div><dt>Loss if stopped</dt><dd>−${Math.abs(loss(row)).toFixed(1)}%</dd></div>` : ""}</dl></section>` : "";
    const evidence = `${readinessDetails(row)}<section class="detail-diagnostics"><h3>Why we see it this way</h3>${renderScoreBreakdown(row)}${readinessFactorsMarkup(row)}</section>
      <section class="state-changes"><h3>State changes</h3>${transitionsMarkup(history.rows, history.loading, history.failed, true)}</section>${plan}`;
    const fullLink = `<a class="full-detail-link" href="./ticker.html?ticker=${encodeURIComponent(row.ticker)}">Open full detail →</a>`;
    panel.innerHTML = `<div class="detail-panel-head"><div><h2>${escaped(row.ticker)}</h2><p>${escaped(displaySecurityName(row.name, row.ticker) || row.ticker)}</p></div>${favourite(row)}</div>${evidence}<nav class="detail-neighbours" aria-label="Selected stock navigation"><button type="button" data-research-step="-1" ${index <= 0 ? "disabled" : ""}>Previous stock</button><button type="button" data-research-step="1" ${index >= state.visibleRows.length - 1 ? "disabled" : ""}>Next stock</button></nav>${fullLink}`;
    const inline = document.querySelector(".mobile-inline-detail");
    if (inline) inline.innerHTML = `<div class="mobile-detail-tools">${favourite(row)}</div>${evidence}${fullLink}`;
    loadPanelHistory(row.ticker);
  };

  window.selectTicker = function selectResearchTicker(ticker) {
    const index = state.visibleRows.findIndex(row => row.ticker === ticker);
    if (index >= 0) pageNumber = Math.floor(index / INITIAL_WATCHLIST_ROWS) + 1;
    originalSelectTicker(ticker);
    renderWatchlist({ refreshOverview: false });
  };

  function rulerMarkup(row) {
    const model = ui.pricePosition(row);
    const zone = ui.zone(row);
    return `<section class="price-position"><div class="position-price"><span>Latest close</span><strong>${ui.number(row.close) === null ? "Unavailable" : fmt(row.close)}</strong>${renderMovePct(row.day_change_pct)}</div>
      ${model ? `<div class="price-ruler" role="img" aria-label="Close ${fmt(model.close)}; planned zone ${fmt(model.low)} to ${fmt(model.high)}; ${model.relation}">
        <span class="ruler-caption">${escaped(model.relation)}</span><div class="ruler-axis"><span class="ruler-zone" style="left:${model.lowPosition}%;width:${Math.max(0.5, model.highPosition - model.lowPosition)}%"></span><span class="ruler-close" style="left:${model.closePosition}%"><span>Close ${fmt(model.close)}</span></span></div>
        <span class="ruler-bounds"><span style="left:${model.lowPosition}%">${fmt(model.low)}</span><span style="left:${model.highPosition}%">${fmt(model.high)}</span></span></div>` : '<p class="ruler-unavailable">Price position unavailable: a valid close and planned zone are required.</p>'}
      <div class="position-zone"><span>Planned entry zone</span><strong>${escaped(zone ? `${fmt(zone.low)}–${fmt(zone.high)}` : "Unavailable")}</strong><small>${zone?.frozen ? "Frozen plan" : "Reference zone"}</small></div></section>`;
  }

  function readinessDetails(row) {
    const score = ui.readinessScore(row);
    const dated = freshnessBlocked(row);
    const status = qualityConstraintLabel(row);
    const date = String(row.data_date || row.history_date || row.date || "Unavailable").slice(0, 10);
    const context = [status, dated ? "As of " + date : "", "Setup evidence, not a win probability"].filter(Boolean).join(" · ");
    return `<section class="readiness-meter ${dated ? "is-dated" : ""}" data-readiness-tone="${readinessTone(score)}" aria-label="Signal readiness" title="${escaped(context)}">
      <span>Signal readiness</span><strong>${score === null ? "—" : Math.round(score)}</strong>
      ${score === null ? '<span class="readiness-unavailable">Not scored</span>' : `<meter min="0" max="100" value="${score}" aria-label="Signal readiness">${score}/100</meter>`}
      </section>`;
  }
  function readinessFactorsMarkup(row) {
    return `<details class="readiness-factors"><summary>Score components</summary><dl>${ui.readinessFactors(row).map(f => `<div><dt>${f.label}<small>${f.weight}% weight</small></dt><dd>${f.score === null ? "Unavailable" : Math.round(f.score)}</dd></div>`).join("")}</dl>
      <p>Published model components, not a win probability. Missing values are not zero. Entry triggers and risk checks remain separate.</p></details>`;
  }
  window.renderShadowPolicyPreview = readinessDetails;

  window.renderLatestHistoryPanel = function renderResearchStock(latest) {
    const panel = document.querySelector("#latest-panel");
    if (!latest) { panel.innerHTML = `<p role="alert">${escaped(document.querySelector("#status")?.textContent || "Current stock data is unavailable.")}</p>`; return; }
    const kind = actionKind(latest.action);
    const active = executionChecksClear(latest) && ["buy", "continue"].includes(kind);
    panel.innerHTML = `<div class="latest-card tone-${kind}"><div class="latest-head">${badge(latest)}</div>
      ${rulerMarkup(latest)}${renderShadowPolicyPreview(latest)}
      <section class="decision-callout tone-${kind}"><span class="eyebrow">What to do</span><strong>${escaped(decisionHeadline(latest))}</strong><p>${escaped(decisionNarrative(latest))}</p></section>
      ${renderFrozenExecutionPlan(latest) || (active ? `<section class="active-plan"><h3>Price plan</h3>${renderReferenceLevels(latest, { active: true })}</section>` : '<div class="inactive-plan">No entry is recommended from the latest session.</div>')}
      <section class="detail-diagnostics"><h3>Why we see it this way</h3>${renderScoreBreakdown(latest)}${readinessFactorsMarkup(latest)}</section></div>`;
    updateTickerNavigation();
  };

  function updateTickerNavigation() {
    const nav = document.querySelector("#ticker-navigation");
    if (!nav) return;
    let stored = [];
    try { stored = JSON.parse(sessionStorage.getItem("research-watchlist-order-v5") || "[]"); } catch { /* use the current directory */ }
    const symbols = Array.isArray(stored) && stored.includes(state.ticker) ? stored : state.tickerDirectory.map(row => row.ticker).sort();
    const index = symbols.indexOf(state.ticker);
    const link = (offset, title) => index >= 0 && symbols[index + offset] ? `<a href="./ticker.html?ticker=${encodeURIComponent(symbols[index + offset])}">${title} <span>${escaped(symbols[index + offset])}</span></a>` : `<span aria-disabled="true">${title}</span>`;
    nav.innerHTML = `<a href="./?ticker=${encodeURIComponent(state.ticker)}#watchlist-table">← Back to watchlist</a><div>${link(-1, "Previous stock")}${link(1, "Next stock")}</div>`;
  }

  if (pageIsTicker) {
    const originalHistoryRows = window.renderHistoryRows;
    window.renderHistoryRows = function renderResearchHistoryRows() {
      originalHistoryRows();
      const timeline = document.querySelector("#timeline");
      const details = timeline.querySelector(".raw-history")?.outerHTML || "";
      timeline.innerHTML = `<h3>State changes</h3>${transitionsMarkup(state.historyRows)}${details}`;
    };
    window.loadTickerDirectory = async function loadResearchDirectory() {
      await originalLoadDirectory();
      // The existing directory fetch retains the complete rows. Reuse it, rather than
      // adding another latest-watchlist request just for coverage and navigation.
      coverageRows = state.tickerDirectory.filter(row => !coverageRun?.publication_id || row.publication_id === coverageRun.publication_id);
      renderMarketRail(coverageRun, coverageRows);
      updateTickerNavigation();
    };
    updateTickerNavigation();
    if (state.historyRows.length) renderHistoryRows();
  } else {
    state.sort = "distance-asc";
    document.querySelector("#sort").value = state.sort;
    const mobileSearch = document.querySelector(".mobile-search-panel");
    if (mobileSearch) document.querySelector("#watchlist-table").insertBefore(mobileSearch, document.querySelector(".controls"));
    document.querySelectorAll(".controls, .mobile-search-panel").forEach((controls, index) => {
      const toggle = document.createElement("label");
      toggle.className = "near-zone-control";
      toggle.innerHTML = `<input type="checkbox" id="near-zone-${index}"> Near the zone`;
      toggle.querySelector("input").addEventListener("change", event => {
        nearOnly = event.target.checked; pageSignature = "";
        document.querySelectorAll(".near-zone-control input").forEach(input => { input.checked = nearOnly; });
        renderWatchlist({ refreshOverview: false });
      });
      controls.append(toggle);
    });
    document.querySelector('[data-mobile-filter="favourites"]')?.addEventListener("click", event => {
      event.stopImmediatePropagation();
      state.filter = state.filter === "favourites" ? "all" : "favourites";
      renderWatchlist();
    }, true);
    document.querySelector("#watchlist-body").addEventListener("click", event => {
      const button = event.target.closest("[data-mobile-ticker]");
      if (button) {
        event.preventDefault(); event.stopImmediatePropagation();
        const ticker = button.dataset.mobileTicker;
        mobileExpandedTicker = mobileExpandedTicker === ticker ? "" : ticker;
        selectTicker(ticker);
      } else if (event.target.closest(".mobile-inline-detail")) {
        event.stopImmediatePropagation();
        const star = event.target.closest("[data-focus-ticker]");
        if (star) { event.preventDefault(); toggleFocusTicker(star.dataset.focusTicker); }
      }
    }, true);
    document.querySelector("#ticker-detail-panel")?.addEventListener("click", event => {
      const star = event.target.closest("[data-focus-ticker]");
      if (star) toggleFocusTicker(star.dataset.focusTicker);
      const step = event.target.closest("[data-research-step]");
      if (step && !step.disabled) {
        const index = state.visibleRows.findIndex(row => row.ticker === state.selectedTicker);
        const next = state.visibleRows[index + Number(step.dataset.researchStep)];
        if (next) selectTicker(next.ticker);
      }
    });
    document.querySelector("#mobile-sort")?.addEventListener("change", event => {
      state.sort = event.target.value; document.querySelector("#sort").value = state.sort; renderWatchlist({ refreshOverview: false });
    });
    document.querySelector("#research-pagination")?.addEventListener("click", event => {
      const step = event.target.closest("[data-page-step]");
      if (!step || step.disabled) return;
      pageNumber += Number(step.dataset.pageStep);
      renderWatchlist({ refreshOverview: false });
      document.querySelector("#watchlist-table").scrollIntoView({ block: "start", behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    });
    document.querySelectorAll("[data-workspace-filter]").forEach(button => button.addEventListener("click", () => {
      state.filter = button.dataset.workspaceFilter; renderWatchlist();
    }));
    if (state.rows.length) { renderWatchlist(); renderMarketRail(state.runInfo, state.rows); }
  }
  const originalStatus = window.setStatus;
  window.setStatus = function researchStatus(message, ok = true) {
    originalStatus(message, ok);
    let error = document.querySelector("#research-data-error");
    if (!error) { error = document.createElement("p"); error.id = "research-data-error"; error.setAttribute("role", "alert"); document.querySelector(".hero")?.after(error); }
    const show = !ok && (pageIsTicker ? !state.historyRows.length : !state.rows.length);
    error.hidden = !show; error.textContent = show ? String(message) : "";
  };
  document.addEventListener("keydown", event => {
    if (event.key === "Escape") document.querySelector(".coverage-disclosure")?.removeAttribute("open");
  });
  document.addEventListener("click", event => {
    if (!event.target.closest(".coverage-disclosure")) document.querySelector(".coverage-disclosure")?.removeAttribute("open");
  });
}());
