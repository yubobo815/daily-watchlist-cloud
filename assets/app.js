const ACTION_LABELS = {
  "BUY CANDIDATE": "BUY",
  "SETUP FORMING": "SETUP",
  "WATCH TREND": "WATCH",
  "EXIT PRESSURE": "EXIT",
  "WAIT": "WAIT",
  "WAIT / AVOID": "AVOID"
};

const SETUP_LABELS = {
  "BREAKOUT BUY": "BO",
  "MOMENTUM BUY": "MOM",
  "PULLBACK BUY": "PB",
  "EARLY PULLBACK BUY": "EPB",
  "REVERSAL BUY": "REV",
  "NONE": "-"
};

const WATCHLIST_COLUMNS = [
  ["ticker", "Sym"],
  ["name", "Name"],
  ["action", "Signal"],
  ["score", "Score"],
  ["close", "Last"],
  ["day_change_pct", "Chg%"],
  ["setup", "Setup"],
  ["adaptive_mode", "Mode"],
  ["psychology", "Tape"],
  ["entry_est", "Entry"],
  ["stop_est", "Stop"],
  ["target_est", "Target"],
  ["notes", "Read"]
];

const HISTORY_COLUMNS = [
  "history_date",
  "action",
  "setup",
  "adaptive_mode",
  "psychology",
  "score",
  "close",
  "day_change_pct",
  "entry_est",
  "stop_est",
  "target_est",
  "notes"
];

const SUMMARY_CARDS = [
  ["buy", "BUY"],
  ["setup", "SETUP"],
  ["watch", "WATCH"],
  ["exit", "EXIT"],
  ["avoid", "AVOID"]
];

const ACTION_TONE = {
  buy: "#14914d",
  setup: "#d69b00",
  watch: "#3f6fd5",
  exit: "#c93b32",
  avoid: "#777777"
};

const state = {
  rows: [],
  visibleRows: [],
  filter: "all",
  query: "",
  sort: "score-desc",
  historyRows: [],
  ticker: "ORCL"
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function normaliseTicker(value) {
  return (value || "ORCL").trim().toUpperCase().replace("BRK.B", "BRK-B");
}

function actionKind(action) {
  return {
    "BUY CANDIDATE": "buy",
    "SETUP FORMING": "setup",
    "WATCH TREND": "watch",
    "EXIT PRESSURE": "exit",
    "WAIT": "avoid",
    "WAIT / AVOID": "avoid"
  }[action] || "avoid";
}

function fmtNumber(value, digits = 1) {
  if (value === null || value === undefined || value === "") return "";
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(digits) : String(value);
}

function fmtCompactDate(value) {
  if (!value) return "";
  const [, month, day] = String(value).split("-");
  return month && day ? `${month}/${day}` : String(value);
}

function numericValue(row, key) {
  const number = Number(row?.[key]);
  return Number.isFinite(number) ? number : 0;
}

function scalePoint(value, min, max, start, end) {
  if (max === min) return (start + end) / 2;
  return start + ((value - min) / (max - min)) * (end - start);
}

function describeHistoryChange(row, previous) {
  if (!previous) return "Latest scanner state";
  const changes = [];
  if (row.action !== previous.action) {
    changes.push(`Signal changed from ${ACTION_LABELS[previous.action] || previous.action} to ${ACTION_LABELS[row.action] || row.action}`);
  }
  if (row.setup !== previous.setup) {
    changes.push(`Setup shifted from ${previous.setup || "NONE"} to ${row.setup || "NONE"}`);
  }
  const scoreMove = numericValue(row, "score") - numericValue(previous, "score");
  if (Math.abs(scoreMove) >= 5) {
    changes.push(`Score ${scoreMove > 0 ? "improved" : "faded"} ${Math.abs(scoreMove).toFixed(1)} pts`);
  }
  return changes.join(". ") || "Behavior held steady";
}

function csvEscape(value) {
  const text = value === null || value === undefined ? "" : String(value);
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function downloadCsv(filename, rows, columns) {
  const csv = [
    columns.join(","),
    ...rows.map((row) => columns.map((column) => csvEscape(row[column])).join(","))
  ].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function setStatus(message, ok = true) {
  const status = document.querySelector("#status");
  const runStatus = document.querySelector("#run-status");
  if (status) status.textContent = message;
  if (runStatus) runStatus.classList.toggle("bad", !ok);
}

async function getSupabaseConfig() {
  if (window.WATCHLIST_SUPABASE?.url && window.WATCHLIST_SUPABASE?.anonKey) {
    return window.WATCHLIST_SUPABASE;
  }

  await new Promise((resolve) => {
    const existing = document.querySelector("script[data-watchlist-supabase]");
    if (existing) {
      existing.addEventListener("load", resolve, { once: true });
      existing.addEventListener("error", resolve, { once: true });
      return;
    }
    const script = document.createElement("script");
    script.src = "https://yubobo815.github.io/daily-watchlist-cloud/supabase-config.js";
    script.async = true;
    script.dataset.watchlistSupabase = "true";
    script.onload = resolve;
    script.onerror = resolve;
    document.head.appendChild(script);
  });

  return window.WATCHLIST_SUPABASE?.url && window.WATCHLIST_SUPABASE?.anonKey
    ? window.WATCHLIST_SUPABASE
    : null;
}

async function supabaseFetch(path) {
  const config = await getSupabaseConfig();
  if (!config) {
    throw new Error("Supabase browser config is missing.");
  }
  const baseUrl = config.url.replace(/\/$/, "");
  const response = await fetch(`${baseUrl}/rest/v1/${path}`, {
    headers: {
      apikey: config.anonKey,
      Authorization: `Bearer ${config.anonKey}`
    }
  });
  if (!response.ok) {
    throw new Error(`Supabase returned HTTP ${response.status}.`);
  }
  return response.json();
}

async function latestRunDate() {
  const rows = await supabaseFetch("watchlist_snapshots?select=run_date&order=run_date.desc&limit=1");
  return rows[0]?.run_date || null;
}

function renderWatchlistCell(row, key) {
  if (key === "ticker") {
    return `<a class="ticker-link" href="./history.html?ticker=${encodeURIComponent(row.ticker)}">${escapeHtml(row.ticker)}</a>`;
  }
  if (key === "action") {
    const kind = actionKind(row.action);
    return `<span class="badge ${kind}">${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>`;
  }
  if (key === "setup") {
    return SETUP_LABELS[row.setup] ? `<span class="badge">${escapeHtml(SETUP_LABELS[row.setup])}</span>` : escapeHtml(row.setup);
  }
  if (["score", "day_change_pct"].includes(key)) return escapeHtml(fmtNumber(row[key], 1));
  if (["close", "entry_est", "stop_est", "target_est"].includes(key)) return escapeHtml(fmtNumber(row[key], 2));
  return escapeHtml(row[key]);
}

function renderCards(counts) {
  const cards = document.querySelector("#cards");
  cards.innerHTML = SUMMARY_CARDS.map(([kind, label]) => `
    <button class="card tone-${kind} ${state.filter === kind ? "active" : ""}" type="button" data-filter="${kind}">
      <span>${label}</span>
      <strong>${counts[kind] || 0}</strong>
    </button>
  `).join("");
  cards.querySelectorAll("[data-filter]").forEach((card) => {
    card.addEventListener("click", () => {
      const next = card.dataset.filter;
      state.filter = state.filter === next ? "all" : next;
      document.querySelector("#all-filter").classList.toggle("active", state.filter === "all");
      renderWatchlist();
    });
  });
}

function renderWatchlist() {
  const counts = { buy: 0, setup: 0, watch: 0, exit: 0, avoid: 0 };
  state.rows.forEach((row) => {
    counts[actionKind(row.action)] += 1;
  });
  renderCards(counts);

  const needle = state.query.trim().toLowerCase();
  const [sortKey, direction] = state.sort.split("-");
  const multiplier = direction === "asc" ? 1 : -1;
  state.visibleRows = state.rows
    .filter((row) => state.filter === "all" || actionKind(row.action) === state.filter)
    .filter((row) => !needle || WATCHLIST_COLUMNS.some(([key]) => String(row[key] || "").toLowerCase().includes(needle)))
    .sort((a, b) => {
      if (sortKey === "ticker") return a.ticker.localeCompare(b.ticker) * multiplier;
      return (Number(a[sortKey] || 0) - Number(b[sortKey] || 0)) * multiplier;
    });

  document.querySelector("#watchlist-head").innerHTML = `<tr>${WATCHLIST_COLUMNS.map(([, label]) => `<th>${label}</th>`).join("")}</tr>`;
  document.querySelector("#watchlist-body").innerHTML = state.visibleRows.map((row) => `
    <tr class="row-${actionKind(row.action)}">
      ${WATCHLIST_COLUMNS.map(([key]) => `<td class="${["score", "close", "day_change_pct", "entry_est", "stop_est", "target_est"].includes(key) ? "num" : ""}">${renderWatchlistCell(row, key)}</td>`).join("")}
    </tr>
  `).join("");
  document.querySelector("#count").textContent = `${state.visibleRows.length} / ${state.rows.length} shown`;
  document.querySelector("#empty").classList.toggle("hidden", state.visibleRows.length > 0);
}

async function initWatchlist() {
  document.querySelector("#search").addEventListener("input", (event) => {
    state.query = event.target.value;
    renderWatchlist();
  });
  document.querySelector("#sort").addEventListener("change", (event) => {
    state.sort = event.target.value;
    renderWatchlist();
  });
  document.querySelector("#all-filter").addEventListener("click", () => {
    state.filter = "all";
    document.querySelector("#all-filter").classList.add("active");
    renderWatchlist();
  });
  const downloadButton = document.querySelector("#download-csv");
  if (downloadButton) {
    downloadButton.addEventListener("click", () => {
      downloadCsv("daily_watchlist_vercel.csv", state.visibleRows, WATCHLIST_COLUMNS.map(([key]) => key));
    });
  }

  try {
    const latest = await latestRunDate();
    if (!latest) throw new Error("No Supabase run found yet.");
    state.rows = await supabaseFetch(`watchlist_snapshots?select=*&run_date=eq.${encodeURIComponent(latest)}&order=score.desc`);
    document.querySelector("#run-status").textContent = `Database run: ${latest}`;
    setStatus(`Live from Supabase run ${latest}. Confirm BUY CANDIDATE entries on the TradingView Pine chart before acting. Daily refresh still comes from GitHub Actions at 8:00am Australia/Melbourne; this Vercel app reads the database instantly.`);
    renderWatchlist();
  } catch (error) {
    setStatus(error.message, false);
  }
}

function renderLatestHistoryPanel(latest) {
  const panel = document.querySelector("#latest-panel");
  if (!latest) {
    panel.innerHTML = "";
    return;
  }
  panel.innerHTML = `
    <div><strong>Latest signal</strong></div>
    <span class="badge ${actionKind(latest.action)}">${escapeHtml(ACTION_LABELS[latest.action] || latest.action)}</span>
    <p class="subtle">Close ${fmtNumber(latest.close, 2)}, score ${fmtNumber(latest.score, 1)}, entry ${fmtNumber(latest.entry_est, 2)}.</p>
    ${latest.notes ? `<p class="subtle">${escapeHtml(latest.notes)}</p>` : ""}
  `;
}

function renderHistoryVisual(rows) {
  const visual = document.querySelector("#history-visual");
  const chronological = [...rows].reverse();
  if (!chronological.length) {
    visual.innerHTML = "<div class=\"empty\">No visual history found.</div>";
    return;
  }

  const width = 920;
  const height = 310;
  const pad = { left: 46, right: 26, top: 24, bottom: 44 };
  const plotWidth = width - pad.left - pad.right;
  const plotHeight = height - pad.top - pad.bottom;
  const scores = chronological.map((row) => numericValue(row, "score"));
  const closes = chronological.map((row) => numericValue(row, "close"));
  const minClose = Math.min(...closes);
  const maxClose = Math.max(...closes);
  const xFor = (index) => pad.left + (chronological.length === 1 ? plotWidth / 2 : (index / (chronological.length - 1)) * plotWidth);
  const scoreY = (score) => pad.top + plotHeight - (Math.max(0, Math.min(100, score)) / 100) * plotHeight;
  const closeY = (close) => scalePoint(close, minClose, maxClose, pad.top + plotHeight, pad.top);
  const scorePoints = chronological.map((row, index) => `${xFor(index).toFixed(1)},${scoreY(numericValue(row, "score")).toFixed(1)}`).join(" ");
  const pricePoints = chronological.map((row, index) => `${xFor(index).toFixed(1)},${closeY(numericValue(row, "close")).toFixed(1)}`).join(" ");
  const latest = chronological.at(-1);
  const first = chronological[0];
  const scoreMove = numericValue(latest, "score") - numericValue(first, "score");
  const priceMove = numericValue(latest, "close") - numericValue(first, "close");
  const segments = chronological.map((row, index) => {
    const x = xFor(index);
    const nextX = index === chronological.length - 1 ? width - pad.right : xFor(index + 1);
    const segmentWidth = Math.max(8, nextX - x);
    return `<rect x="${x.toFixed(1)}" y="${pad.top}" width="${segmentWidth.toFixed(1)}" height="${plotHeight}" fill="${ACTION_TONE[actionKind(row.action)]}" opacity="0.1" />`;
  }).join("");
  const markers = chronological.map((row, index) => {
    const kind = actionKind(row.action);
    return `
      <circle cx="${xFor(index).toFixed(1)}" cy="${scoreY(numericValue(row, "score")).toFixed(1)}" r="${index === chronological.length - 1 ? 6 : 4}" fill="${ACTION_TONE[kind]}" />
      <title>${escapeHtml(row.history_date)} · ${escapeHtml(row.action)} · score ${fmtNumber(row.score, 1)} · close ${fmtNumber(row.close, 2)}</title>
    `;
  }).join("");
  const dateTicks = chronological
    .filter((_, index) => index === 0 || index === chronological.length - 1 || index % 7 === 0)
    .map((row, index, ticks) => {
      const realIndex = chronological.indexOf(row);
      return `<text x="${xFor(realIndex).toFixed(1)}" y="${height - 14}" text-anchor="${index === 0 ? "start" : index === ticks.length - 1 ? "end" : "middle"}">${escapeHtml(fmtCompactDate(row.history_date))}</text>`;
    }).join("");

  visual.innerHTML = `
    <div class="visual-summary">
      <div>
        <span class="subtle">Latest signal</span>
        <strong><span class="badge ${actionKind(latest.action)}">${escapeHtml(ACTION_LABELS[latest.action] || latest.action)}</span></strong>
      </div>
      <div>
        <span class="subtle">Score move</span>
        <strong class="${scoreMove >= 0 ? "up" : "down"}">${scoreMove >= 0 ? "+" : ""}${fmtNumber(scoreMove, 1)}</strong>
      </div>
      <div>
        <span class="subtle">Price move</span>
        <strong class="${priceMove >= 0 ? "up" : "down"}">${priceMove >= 0 ? "+" : ""}${fmtNumber(priceMove, 2)}</strong>
      </div>
    </div>
    <div class="chart-card">
      <svg class="history-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(state.ticker)} 30-day score and price chart">
        <line x1="${pad.left}" y1="${scoreY(75).toFixed(1)}" x2="${width - pad.right}" y2="${scoreY(75).toFixed(1)}" class="guide buy-guide" />
        <line x1="${pad.left}" y1="${scoreY(50).toFixed(1)}" x2="${width - pad.right}" y2="${scoreY(50).toFixed(1)}" class="guide" />
        <line x1="${pad.left}" y1="${scoreY(25).toFixed(1)}" x2="${width - pad.right}" y2="${scoreY(25).toFixed(1)}" class="guide exit-guide" />
        ${segments}
        <polyline points="${pricePoints}" class="price-line" />
        <polyline points="${scorePoints}" class="score-line" />
        ${markers}
        <text x="12" y="${scoreY(75).toFixed(1) + 4}" class="axis-label">buy</text>
        <text x="12" y="${scoreY(50).toFixed(1) + 4}" class="axis-label">mid</text>
        <text x="12" y="${scoreY(25).toFixed(1) + 4}" class="axis-label">exit</text>
        ${dateTicks}
      </svg>
      <div class="chart-legend">
        <span><i class="legend-score"></i> scanner score</span>
        <span><i class="legend-price"></i> close price shape</span>
        <span><i class="legend-band"></i> signal zones</span>
      </div>
    </div>
  `;
}

function renderHistoryRows() {
  const timeline = document.querySelector("#timeline");
  if (!state.historyRows.length) {
    timeline.innerHTML = "<div class=\"empty\">No history found for this ticker.</div>";
    document.querySelector("#history-visual").innerHTML = "<div class=\"empty\">No visual history found.</div>";
    renderLatestHistoryPanel(null);
    return;
  }
  renderLatestHistoryPanel(state.historyRows[0]);
  renderHistoryVisual(state.historyRows);
  const chronological = [...state.historyRows].reverse();
  const moments = chronological
    .map((row, index) => ({ row, previous: chronological[index - 1], index }))
    .filter(({ row, previous, index }) => {
      if (index === chronological.length - 1) return true;
      if (!previous) return actionKind(row.action) !== "avoid";
      return row.action !== previous.action || row.setup !== previous.setup || Math.abs(numericValue(row, "score") - numericValue(previous, "score")) >= 8;
    })
    .slice(-8)
    .reverse();

  timeline.innerHTML = `
    <h3>Key Behavior Moments</h3>
    ${moments.map(({ row, previous, index }) => `
      <div class="moment-card tone-${actionKind(row.action)}">
        <div class="moment-date">${index === chronological.length - 1 ? "Latest" : escapeHtml(fmtCompactDate(row.history_date))}</div>
        <div class="moment-body">
          <span class="badge ${actionKind(row.action)}">${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>
          <strong>${escapeHtml(describeHistoryChange(row, previous))}</strong>
          <p class="subtle">Close ${fmtNumber(row.close, 2)} · Score ${fmtNumber(row.score, 1)} · ${escapeHtml(row.setup || "NONE")} · ${escapeHtml(row.adaptive_mode || "Mixed")}</p>
          ${row.notes ? `<p class="subtle">${escapeHtml(row.notes)}</p>` : ""}
        </div>
      </div>
    `).join("")}
    <details class="raw-history">
      <summary>Show daily rows</summary>
      ${chronological.map((row) => `
        <div class="timeline-row">
          <strong>${escapeHtml(row.history_date)}</strong>
          <div>
            <span class="badge ${actionKind(row.action)}">${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>
            <span class="subtle"> ${escapeHtml(row.setup || "NONE")} · ${escapeHtml(row.adaptive_mode || "Mixed")}</span>
            <div class="bar"><span style="width: ${Math.max(2, Math.min(100, Number(row.score) || 0))}%"></span></div>
          </div>
          <span class="num">${fmtNumber(row.close, 2)}</span>
        </div>
      `).join("")}
    </details>
  `;
}

async function loadHistory(ticker) {
  state.ticker = normaliseTicker(ticker);
  document.querySelector("#ticker").value = state.ticker;
  document.querySelector("#history-title").textContent = `${state.ticker} 30-Day History`;
  document.title = `${state.ticker} History`;
  window.history.replaceState(null, "", `./history.html?ticker=${encodeURIComponent(state.ticker)}`);
  setStatus("Loading ticker history...");
  document.querySelector("#run-status").textContent = "No history loaded";
  document.querySelector("#run-status").classList.add("bad");
  try {
    const runRows = await supabaseFetch(`watchlist_behavior_history?select=run_date&ticker=eq.${encodeURIComponent(state.ticker)}&order=run_date.desc&limit=1`);
    const latest = runRows[0]?.run_date;
    if (!latest) throw new Error(`No 30-day history found for ${state.ticker}.`);
    state.historyRows = await supabaseFetch(`watchlist_behavior_history?select=*&ticker=eq.${encodeURIComponent(state.ticker)}&run_date=eq.${encodeURIComponent(latest)}&order=history_date.desc`);
    document.querySelector("#run-status").textContent = `Database run: ${latest}`;
    setStatus(`Last refresh date: ${latest}. Reference only; not for trade confirmation.`);
    renderHistoryRows();
  } catch (error) {
    state.historyRows = [];
    setStatus(error.message, false);
    renderHistoryRows();
  }
}

function initHistory() {
  const params = new URLSearchParams(window.location.search);
  const ticker = normaliseTicker(params.get("ticker"));
  document.querySelector("#ticker-form").addEventListener("submit", (event) => {
    event.preventDefault();
    loadHistory(document.querySelector("#ticker").value);
  });
  const downloadButton = document.querySelector("#download-csv");
  if (downloadButton) {
    downloadButton.addEventListener("click", () => {
      downloadCsv(`${state.ticker}_history.csv`, state.historyRows, HISTORY_COLUMNS);
    });
  }
  loadHistory(ticker);
}

if (document.body.dataset.page === "history") {
  initHistory();
} else {
  initWatchlist();
}
