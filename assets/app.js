const ACTION_LABELS = {
  "BUY CANDIDATE": "BUY",
  "SETUP FORMING": "SETUP",
  "WATCH TREND": "WATCH",
  "EXIT PRESSURE": "EXIT",
  "WAIT": "WAIT",
  "WAIT / AVOID": "AVOID"
};

const SETUP_LABELS = {
  "BREAKOUT BUY": "Breakout",
  "MOMENTUM BUY": "Momentum",
  "PULLBACK BUY": "Pullback",
  "EARLY PULLBACK BUY": "Early Pullback",
  "REVERSAL BUY": "Reversal",
  "NONE": "None"
};

const WATCHLIST_COLUMNS = [
  ["ticker", "Sym"],
  ["name", "Name"],
  ["action", "Signal"],
  ["score", "Score"],
  ["close", "Close"],
  ["day_change_pct", "Chg%"],
  ["setup", "Pattern"],
  ["adaptive_mode", "Mode"],
  ["psychology", "Tape"],
  ["entry_est", "Entry"],
  ["stop_est", "Stop"],
  ["target_est", "Target"],
  ["notes", "Behavior"]
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
  buy: "#0f8a5f",
  setup: "#b7791f",
  watch: "#2f5fb3",
  exit: "#b42318",
  avoid: "#667085"
};

const KIND_LABELS = {
  buy: "BUY",
  setup: "SETUP",
  watch: "WATCH",
  exit: "EXIT",
  avoid: "AVOID"
};

const APP_DISCLAIMER = "This tool is intended for reference and analysis only. Do not consider this as financial or investment advice.";

const SECURITY_NAME_FALLBACKS = {
  AAPL: "Apple",
  ABBV: "AbbVie",
  ABNB: "Airbnb",
  ABT: "Abbott Laboratories",
  ACN: "Accenture",
  ADBE: "Adobe",
  ADI: "Analog Devices",
  ADP: "Automatic Data Processing",
  ADSK: "Autodesk",
  AEP: "American Electric Power",
  ALNY: "Alnylam Pharmaceuticals",
  AMAT: "Applied Materials",
  AMD: "Advanced Micro Devices",
  AMGN: "Amgen",
  AMT: "American Tower",
  AMZN: "Amazon",
  ANET: "Arista Networks",
  APP: "AppLovin",
  ARM: "Arm Holdings",
  ASML: "ASML",
  ASTS: "AST SpaceMobile",
  AVGO: "Broadcom",
  AXON: "Axon Enterprise",
  AXP: "American Express",
  BA: "Boeing",
  BAC: "Bank of America",
  BKR: "Baker Hughes",
  BKNG: "Booking Holdings",
  BLK: "BlackRock",
  BMY: "Bristol Myers Squibb",
  BNY: "BNY Mellon",
  "BRK.B": "Berkshire Hathaway",
  C: "Citigroup",
  CAT: "Caterpillar",
  CCEP: "Coca-Cola Europacific Partners",
  CDNS: "Cadence Design Systems",
  CEG: "Constellation Energy",
  CHTR: "Charter Communications",
  CL: "Colgate-Palmolive",
  CMCSA: "Comcast",
  COF: "Capital One",
  COHR: "Coherent",
  COP: "ConocoPhillips",
  COST: "Costco",
  CPRT: "Copart",
  CRM: "Salesforce",
  CRWD: "CrowdStrike",
  CSCO: "Cisco Systems",
  CSX: "CSX",
  CTAS: "Cintas",
  CTSH: "Cognizant",
  CVS: "CVS Health",
  CVX: "Chevron",
  DASH: "DoorDash",
  DDOG: "Datadog",
  DE: "Deere",
  DELL: "Dell Technologies",
  DHR: "Danaher",
  DIS: "Disney",
  DRAM: "Global X DRAM ETF",
  DUK: "Duke Energy",
  DXCM: "Dexcom",
  EA: "Electronic Arts",
  EMR: "Emerson Electric",
  "EOS.AX": "Electro Optic Systems",
  EXC: "Exelon",
  FANG: "Diamondback Energy",
  FAST: "Fastenal",
  FDX: "FedEx",
  FER: "Ferrovial",
  FTNT: "Fortinet",
  GD: "General Dynamics",
  GE: "GE Aerospace",
  GEHC: "GE HealthCare",
  GEV: "GE Vernova",
  GILD: "Gilead Sciences",
  GLW: "Corning",
  GM: "General Motors",
  GOOG: "Alphabet",
  GOOGL: "Alphabet",
  GS: "Goldman Sachs",
  HD: "Home Depot",
  HON: "Honeywell",
  IBM: "IBM",
  IDXX: "IDEXX Laboratories",
  INSM: "Insmed",
  INTC: "Intel",
  INTU: "Intuit",
  ISRG: "Intuitive Surgical",
  JNJ: "Johnson & Johnson",
  JPM: "JPMorgan Chase",
  KDP: "Keurig Dr Pepper",
  KHC: "Kraft Heinz",
  KLAC: "KLA",
  KO: "Coca-Cola",
  LIN: "Linde",
  LITE: "Lumentum",
  LLY: "Eli Lilly",
  LMT: "Lockheed Martin",
  LOW: "Lowe's",
  LRCX: "Lam Research",
  MA: "Mastercard",
  MAR: "Marriott International",
  MCD: "McDonald's",
  MCHP: "Microchip Technology",
  MDLZ: "Mondelez International",
  MDT: "Medtronic",
  MELI: "MercadoLibre",
  META: "Meta Platforms",
  MMM: "3M",
  MNST: "Monster Beverage",
  MO: "Altria",
  MPWR: "Monolithic Power Systems",
  MRK: "Merck",
  MRVL: "Marvell Technology",
  MS: "Morgan Stanley",
  MSFT: "Microsoft",
  MSTR: "MicroStrategy",
  MU: "Micron",
  NASA: "Nasa",
  NEE: "NextEra Energy",
  NFLX: "Netflix",
  NKE: "Nike",
  NOW: "ServiceNow",
  NVDA: "Nvidia",
  NXPI: "NXP Semiconductors",
  ODFL: "Old Dominion Freight Line",
  OKTA: "Okta",
  ORCL: "Oracle",
  ORLY: "O'Reilly Automotive",
  PANW: "Palo Alto Networks",
  PAYX: "Paychex",
  PCAR: "PACCAR",
  PDD: "PDD Holdings",
  PEP: "PepsiCo",
  PFE: "Pfizer",
  PG: "Procter & Gamble",
  PLTR: "Palantir",
  PM: "Philip Morris International",
  PYPL: "PayPal",
  QCOM: "Qualcomm",
  REGN: "Regeneron Pharmaceuticals",
  ROK: "Rockwell Automation",
  ROP: "Roper Technologies",
  ROST: "Ross Stores",
  RKLB: "Rocket Lab",
  RTX: "RTX",
  SBUX: "Starbucks",
  SCHW: "Charles Schwab",
  SHOP: "Shopify",
  SMCI: "Super Micro Computer",
  SMH: "VanEck Semiconductor ETF",
  SNAP: "Snap",
  SNDK: "SanDisk",
  SNOW: "Snowflake",
  SNPS: "Synopsys",
  SO: "Southern Company",
  SOHR: "Soho House",
  SPG: "Simon Property Group",
  SRM: "SRM Entertainment",
  STX: "Seagate",
  T: "AT&T",
  TEAM: "Atlassian",
  TMO: "Thermo Fisher Scientific",
  TMUS: "T-Mobile US",
  TRI: "Thomson Reuters",
  TSLA: "Tesla",
  TSM: "Taiwan Semiconductor",
  TTWO: "Take-Two Interactive",
  TXN: "Texas Instruments",
  UBER: "Uber",
  UNH: "UnitedHealth",
  UNP: "Union Pacific",
  UPS: "UPS",
  USB: "U.S. Bancorp",
  V: "Visa",
  VGT: "Vanguard Information Technology ETF",
  VOLT: "Volt Information Sciences",
  VRSK: "Verisk Analytics",
  VRT: "Vertiv",
  VRTX: "Vertex Pharmaceuticals",
  VZ: "Verizon",
  WBD: "Warner Bros. Discovery",
  WDAY: "Workday",
  WDC: "Western Digital",
  WFC: "Wells Fargo",
  WMT: "Walmart",
  XEL: "Xcel Energy",
  XOM: "Exxon Mobil",
  ZM: "Zoom",
  ZS: "Zscaler"
};

const state = {
  rows: [],
  visibleRows: [],
  filter: "all",
  query: "",
  sort: "score-desc",
  historyRows: [],
  ticker: "ORCL",
  tickerName: ""
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

function fmtSignedNumber(value, digits = 1) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "";
  return `${number >= 0 ? "+" : ""}${number.toFixed(digits)}`;
}

function moveClass(value) {
  return Number(value) >= 0 ? "up" : "down";
}

function renderMovePct(value) {
  const text = fmtSignedNumber(value, 1);
  return text ? `<span class="move-pct ${moveClass(value)}">${text}%</span>` : "";
}

function displaySecurityName(name, ticker) {
  const cleanName = String(name || "").trim();
  if (cleanName && cleanName.toUpperCase() !== ticker) return cleanName;
  return SECURITY_NAME_FALLBACKS[ticker] || "";
}

function historyDisplayTitle() {
  return state.tickerName || state.ticker;
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

function linePath(points) {
  if (!points.length) return "";
  return points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(" ");
}

function setupLabel(value) {
  if (!value) return "None";
  return SETUP_LABELS[value] || value;
}

function behaviorDetail(row) {
  const kind = actionKind(row.action);
  const pattern = setupLabel(row.setup);
  const score = numericValue(row, "score");
  const move = numericValue(row, "day_change_pct");
  const tape = row.psychology || "Mixed tape";
  const mode = row.adaptive_mode || "Mixed mode";
  const note = String(row.notes || "").trim();

  if (note) return note;
  if (kind === "buy") return `${pattern} behavior with strong score and ${tape.toLowerCase()} tape.`;
  if (kind === "setup") return `${pattern} is forming; score is constructive but still developing.`;
  if (kind === "watch") return `${mode} behavior; monitor for score expansion or cleaner entry.`;
  if (kind === "exit") return `Exit pressure: weak score with ${move < 0 ? "negative" : "unstable"} price action.`;
  if (score < 25) return "Weak scanner behavior; avoid until score and tape improve.";
  return `${mode} behavior with no clear edge yet.`;
}

function renderHistoryChangeChips(row, previous) {
  if (!previous) return `<span class="change-chip quiet">Latest state</span>`;
  const chips = [];
  if (row.action !== previous.action) {
    chips.push(`<span class="change-chip signal">${escapeHtml(ACTION_LABELS[previous.action] || previous.action)} <b>→</b> ${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>`);
  }
  if (row.setup !== previous.setup) {
    chips.push(`<span class="change-chip setup">${escapeHtml(setupLabel(previous.setup))} <b>→</b> ${escapeHtml(setupLabel(row.setup))}</span>`);
  }
  const scoreMove = numericValue(row, "score") - numericValue(previous, "score");
  if (Math.abs(scoreMove) >= 5) {
    chips.push(`<span class="change-chip ${moveClass(scoreMove)}">Score ${fmtSignedNumber(scoreMove, 1)}</span>`);
  }
  return chips.join(" ") || `<span class="change-chip quiet">Steady</span>`;
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
  if (key === "name") {
    return escapeHtml(displaySecurityName(row.name, row.ticker) || row.name || row.ticker);
  }
  if (key === "action") {
    const kind = actionKind(row.action);
    return `<span class="badge ${kind}">${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>`;
  }
  if (key === "setup") {
    return `<span class="pattern-label">${escapeHtml(setupLabel(row.setup))}</span>`;
  }
  if (key === "notes") {
    return `<span class="behavior-detail">${escapeHtml(behaviorDetail(row))}</span>`;
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

function securityDisplay(row) {
  const name = displaySecurityName(row.name, row.ticker);
  return name ? `${row.ticker} · ${name}` : row.ticker;
}

function focusItem(row, reason) {
  if (!row) return "";
  const kind = actionKind(row.action);
  return `
    <a class="focus-item tone-${kind}" href="./history.html?ticker=${encodeURIComponent(row.ticker)}">
      <span class="focus-kicker">${escapeHtml(reason)}</span>
      <strong>${escapeHtml(securityDisplay(row))}</strong>
      <span class="focus-meta">
        <span class="badge ${kind}">${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>
        <span>Score ${fmtNumber(row.score, 1)}</span>
        <span>Close ${fmtNumber(row.close, 2)} ${renderMovePct(row.day_change_pct)}</span>
        <span>${escapeHtml(setupLabel(row.setup))}</span>
      </span>
    </a>
  `;
}

function renderTodayFocus() {
  const panel = document.querySelector("#today-focus");
  if (!panel) return;
  const ranked = [...state.rows].sort((a, b) => Number(b.score || 0) - Number(a.score || 0));
  const strongest = ranked.find((row) => actionKind(row.action) === "buy");
  const building = ranked.find((row) => actionKind(row.action) === "setup");
  const pressure = [...state.rows]
    .filter((row) => actionKind(row.action) === "exit")
    .sort((a, b) => Number(a.score || 0) - Number(b.score || 0))[0];
  const bestDay = [...state.rows]
    .filter((row) => ["buy", "setup", "watch"].includes(actionKind(row.action)))
    .sort((a, b) => Number(b.day_change_pct || 0) - Number(a.day_change_pct || 0))[0];

  const items = [
    focusItem(strongest, "Strongest buy candidate"),
    focusItem(building, "Best forming behavior"),
    focusItem(pressure, "Most exit pressure"),
    focusItem(bestDay, "Strongest daily move")
  ].filter(Boolean);

  panel.innerHTML = `
    <div class="section-heading">
      <div>
        <span>Today’s Focus</span>
        <strong>Start here, then drill into the table.</strong>
      </div>
    </div>
    <div class="focus-grid">${items.join("")}</div>
  `;
}

function renderWatchlist() {
  const counts = { buy: 0, setup: 0, watch: 0, exit: 0, avoid: 0 };
  state.rows.forEach((row) => {
    counts[actionKind(row.action)] += 1;
  });
  renderCards(counts);
  renderTodayFocus();

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
    state.rows = (await supabaseFetch(`watchlist_snapshots?select=*&run_date=eq.${encodeURIComponent(latest)}&order=score.desc`))
      .map((row) => ({ ...row, name: displaySecurityName(row.name, row.ticker) || row.name || row.ticker }));
    document.querySelector("#run-status").textContent = `Database run: ${latest}`;
    setStatus(`Last refresh date: ${latest}. ${APP_DISCLAIMER}`);
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
    <div class="latest-card tone-${actionKind(latest.action)}">
      <div class="latest-head">
        <span class="latest-label">Latest signal</span>
        <span class="badge ${actionKind(latest.action)}">${escapeHtml(ACTION_LABELS[latest.action] || latest.action)}</span>
      </div>
      <div class="latest-metrics">
        <div><span>Close</span><strong>${fmtNumber(latest.close, 2)} ${renderMovePct(latest.day_change_pct)}</strong></div>
        <div><span>Score</span><strong>${fmtNumber(latest.score, 1)}</strong></div>
        <div><span>Pattern</span><strong>${escapeHtml(setupLabel(latest.setup))}</strong></div>
        <div><span>Entry</span><strong>${fmtNumber(latest.entry_est, 2)}</strong></div>
      </div>
      ${latest.notes ? `<p class="subtle">${escapeHtml(latest.notes)}</p>` : ""}
    </div>
  `;
}

function renderHistoryVisual(rows) {
  const visual = document.querySelector("#history-visual");
  const chronological = [...rows].reverse();
  if (!chronological.length) {
    visual.innerHTML = "<div class=\"empty\">No visual history found.</div>";
    return;
  }

  const width = 1040;
  const height = 260;
  const pad = { left: 66, right: 34, top: 24, bottom: 42 };
  const plotWidth = width - pad.left - pad.right;
  const plotHeight = height - pad.top - pad.bottom;
  const scores = chronological.map((row) => numericValue(row, "score"));
  const closes = chronological.map((row) => numericValue(row, "close"));
  const minClose = Math.min(...closes);
  const maxClose = Math.max(...closes);
  const xFor = (index) => pad.left + (chronological.length === 1 ? plotWidth / 2 : (index / (chronological.length - 1)) * plotWidth);
  const scoreY = (score) => pad.top + plotHeight - (Math.max(0, Math.min(100, score)) / 100) * plotHeight;
  const closeY = (close) => scalePoint(close, minClose, maxClose, pad.top + plotHeight, pad.top);
  const scorePointList = chronological.map((row, index) => ({ x: xFor(index), y: scoreY(numericValue(row, "score")) }));
  const pricePointList = chronological.map((row, index) => ({ x: xFor(index), y: closeY(numericValue(row, "close")) }));
  const scorePath = linePath(scorePointList);
  const pricePath = linePath(pricePointList);
  const scoreArea = `${scorePath} L ${xFor(chronological.length - 1).toFixed(1)} ${(pad.top + plotHeight).toFixed(1)} L ${pad.left.toFixed(1)} ${(pad.top + plotHeight).toFixed(1)} Z`;
  const buyZoneY = scoreY(75);
  const exitZoneY = scoreY(25);
  const scoreBands = `
    <rect x="${pad.left}" y="${pad.top}" width="${plotWidth}" height="${(buyZoneY - pad.top).toFixed(1)}" class="zone-band zone-buy" />
    <rect x="${pad.left}" y="${buyZoneY.toFixed(1)}" width="${plotWidth}" height="${(exitZoneY - buyZoneY).toFixed(1)}" class="zone-band zone-mid" />
    <rect x="${pad.left}" y="${exitZoneY.toFixed(1)}" width="${plotWidth}" height="${(pad.top + plotHeight - exitZoneY).toFixed(1)}" class="zone-band zone-exit" />
  `;
  const latest = chronological.at(-1);
  const first = chronological[0];
  const scoreMove = numericValue(latest, "score") - numericValue(first, "score");
  const priceMove = numericValue(latest, "close") - numericValue(first, "close");
  const signalCounts = chronological.reduce((counts, row) => {
    const kind = actionKind(row.action);
    counts[kind] = (counts[kind] || 0) + 1;
    return counts;
  }, {});
  const dominantSignal = Object.entries(signalCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || "watch";
  const priceRange = maxClose - minClose;
  const segments = chronological.map((row, index) => {
    const x = xFor(index);
    const nextX = index === chronological.length - 1 ? width - pad.right : xFor(index + 1);
    const segmentWidth = Math.max(8, nextX - x);
    return `<rect x="${x.toFixed(1)}" y="${pad.top}" width="${segmentWidth.toFixed(1)}" height="${plotHeight}" fill="${ACTION_TONE[actionKind(row.action)]}" opacity="0.035" />`;
  }).join("");
  const markers = chronological.map((row, index) => {
    const kind = actionKind(row.action);
    return `
      <circle cx="${xFor(index).toFixed(1)}" cy="${scoreY(numericValue(row, "score")).toFixed(1)}" r="${index === chronological.length - 1 ? 6 : 4}" fill="${ACTION_TONE[kind]}" />
      <title>${escapeHtml(row.history_date)} · ${escapeHtml(row.action)} · score ${fmtNumber(row.score, 1)} · close ${fmtNumber(row.close, 2)}</title>
    `;
  }).join("");
  const dateTicks = chronological
    .map((row, index) => ({ row, index }))
    .filter(({ index }) => index === 0 || index === chronological.length - 1 || (index % 7 === 0 && index < chronological.length - 3))
    .map(({ row, index }, tickIndex, ticks) => {
      return `<text x="${xFor(index).toFixed(1)}" y="${height - 18}" text-anchor="${index === 0 ? "start" : tickIndex === ticks.length - 1 ? "end" : "middle"}">${escapeHtml(fmtCompactDate(row.history_date))}</text>`;
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
      <div class="chart-heading">
        <div>
          <span>30-day behavior path</span>
          <strong>Scanner score vs. close direction</strong>
          <p class="chart-note">White line is scanner score. Blue dotted line is close-price direction, scaled only for shape comparison.</p>
        </div>
        <div class="chart-latest">
          <span>Latest</span>
          <strong>${fmtNumber(latest.score, 1)}</strong>
        </div>
      </div>
      <svg class="history-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(state.ticker)} 30-day score and price chart">
        <rect x="${pad.left}" y="${pad.top}" width="${plotWidth}" height="${plotHeight}" class="plot-bg" />
        ${scoreBands}
        <line x1="${pad.left}" y1="${scoreY(75).toFixed(1)}" x2="${width - pad.right}" y2="${scoreY(75).toFixed(1)}" class="guide buy-guide" />
        <line x1="${pad.left}" y1="${scoreY(50).toFixed(1)}" x2="${width - pad.right}" y2="${scoreY(50).toFixed(1)}" class="guide" />
        <line x1="${pad.left}" y1="${scoreY(25).toFixed(1)}" x2="${width - pad.right}" y2="${scoreY(25).toFixed(1)}" class="guide exit-guide" />
        ${segments}
        <path d="${scoreArea}" class="score-area" />
        <path d="${pricePath}" class="price-line" />
        <path d="${scorePath}" class="score-line" />
        ${markers}
        <text x="16" y="${scoreY(87).toFixed(1) + 4}" class="axis-label">STRONGER</text>
        <text x="16" y="${scoreY(50).toFixed(1) + 4}" class="axis-label">NEUTRAL</text>
        <text x="16" y="${scoreY(13).toFixed(1) + 4}" class="axis-label">EXIT RISK</text>
        ${dateTicks}
      </svg>
      <div class="chart-legend">
        <span><i class="legend-score"></i> scanner score</span>
        <span><i class="legend-price"></i> price direction</span>
        <span><i class="legend-band"></i> signal zones</span>
      </div>
      <div class="chart-insights">
        <div><span>Dominant signal</span><strong>${escapeHtml(KIND_LABELS[dominantSignal] || dominantSignal.toUpperCase())}</strong></div>
        <div><span>Current pattern</span><strong>${escapeHtml(setupLabel(latest.setup))}</strong></div>
        <div><span>Close range</span><strong>${fmtNumber(minClose, 2)} - ${fmtNumber(maxClose, 2)}</strong></div>
        <div><span>Range width</span><strong>${fmtNumber(priceRange, 2)}</strong></div>
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
          <div class="change-chips">${renderHistoryChangeChips(row, previous)}</div>
          <p class="subtle">Close ${fmtNumber(row.close, 2)} ${renderMovePct(row.day_change_pct)} · Score ${fmtNumber(row.score, 1)} · Pattern ${escapeHtml(setupLabel(row.setup))} · ${escapeHtml(row.adaptive_mode || "Mixed")}</p>
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
            <span class="subtle"> ${escapeHtml(setupLabel(row.setup))} · ${escapeHtml(row.adaptive_mode || "Mixed")}</span>
            <div class="bar"><span style="width: ${Math.max(2, Math.min(100, Number(row.score) || 0))}%"></span></div>
          </div>
          <span class="num">${fmtNumber(row.close, 2)} ${renderMovePct(row.day_change_pct)}</span>
        </div>
      `).join("")}
    </details>
  `;
}

async function loadHistory(ticker) {
  state.ticker = normaliseTicker(ticker);
  state.tickerName = "";
  document.querySelector("#ticker").value = state.ticker;
  document.querySelector("#history-title").textContent = state.ticker;
  document.querySelector("#ticker-name").textContent = "";
  document.title = state.ticker;
  window.history.replaceState(null, "", `./history.html?ticker=${encodeURIComponent(state.ticker)}`);
  setStatus("Loading ticker history...");
  document.querySelector("#run-status").textContent = "No history loaded";
  document.querySelector("#run-status").classList.add("bad");
  try {
    const runRows = await supabaseFetch(`watchlist_behavior_history?select=run_date&ticker=eq.${encodeURIComponent(state.ticker)}&order=run_date.desc&limit=1`);
    const latest = runRows[0]?.run_date;
    if (!latest) throw new Error(`No 30-day history found for ${state.ticker}.`);
    const snapshotRows = await supabaseFetch(`watchlist_snapshots?select=name&ticker=eq.${encodeURIComponent(state.ticker)}&run_date=eq.${encodeURIComponent(latest)}&limit=1`);
    state.tickerName = displaySecurityName(snapshotRows[0]?.name, state.ticker);
    document.querySelector("#history-title").textContent = historyDisplayTitle();
    document.querySelector("#ticker-name").textContent = "";
    document.title = historyDisplayTitle();
    state.historyRows = await supabaseFetch(`watchlist_behavior_history?select=*&ticker=eq.${encodeURIComponent(state.ticker)}&run_date=eq.${encodeURIComponent(latest)}&order=history_date.desc`);
    document.querySelector("#run-status").textContent = `Database run: ${latest}`;
    setStatus(`Last refresh date: ${latest}. ${APP_DISCLAIMER}`);
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
