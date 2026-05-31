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
  document.querySelector("#download-csv").addEventListener("click", () => {
    downloadCsv("daily_watchlist_vercel.csv", state.visibleRows, WATCHLIST_COLUMNS.map(([key]) => key));
  });

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

function renderHistoryRows() {
  const timeline = document.querySelector("#timeline");
  if (!state.historyRows.length) {
    timeline.innerHTML = "<div class=\"empty\">No history found for this ticker.</div>";
    renderLatestHistoryPanel(null);
    return;
  }
  renderLatestHistoryPanel(state.historyRows[0]);
  timeline.innerHTML = [...state.historyRows].reverse().map((row) => `
    <div class="timeline-row">
      <strong>${escapeHtml(row.history_date)}</strong>
      <div>
        <span class="badge ${actionKind(row.action)}">${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>
        <span class="subtle"> ${escapeHtml(row.setup || "NONE")} · ${escapeHtml(row.adaptive_mode || "Mixed")}</span>
        <div class="bar"><span style="width: ${Math.max(2, Math.min(100, Number(row.score) || 0))}%"></span></div>
      </div>
      <span class="num">${fmtNumber(row.close, 2)}</span>
    </div>
  `).join("");
}

async function loadHistory(ticker) {
  state.ticker = normaliseTicker(ticker);
  document.querySelector("#ticker").value = state.ticker;
  document.querySelector("#history-title").textContent = `${state.ticker} 30-Day History`;
  document.title = `${state.ticker} History`;
  window.history.replaceState(null, "", `./history.html?ticker=${encodeURIComponent(state.ticker)}`);
  setStatus("Loading ticker behavior...");
  document.querySelector("#run-status").textContent = "No history loaded";
  document.querySelector("#run-status").classList.add("bad");
  try {
    const runRows = await supabaseFetch(`watchlist_behavior_history?select=run_date&ticker=eq.${encodeURIComponent(state.ticker)}&order=run_date.desc&limit=1`);
    const latest = runRows[0]?.run_date;
    if (!latest) throw new Error(`No 30-day history found for ${state.ticker}.`);
    state.historyRows = await supabaseFetch(`watchlist_behavior_history?select=*&ticker=eq.${encodeURIComponent(state.ticker)}&run_date=eq.${encodeURIComponent(latest)}&order=history_date.desc`);
    document.querySelector("#run-status").textContent = `Database run: ${latest}`;
    setStatus(`${state.ticker} behavior history from Supabase run ${latest}. This is scanner behavior history, not TradingView confirmation.`);
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
  document.querySelector("#download-csv").addEventListener("click", () => {
    downloadCsv(`${state.ticker}_history.csv`, state.historyRows, HISTORY_COLUMNS);
  });
  loadHistory(ticker);
}

if (document.body.dataset.page === "history") {
  initHistory();
} else {
  initWatchlist();
}
