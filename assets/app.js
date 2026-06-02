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
  ["score", "Conviction"],
  ["close", "Close"],
  ["day_change_pct", "Chg%"],
  ["setup", "Pattern"],
  ["adaptive_mode", "Market Behavior"],
  ["psychology", "Tape"],
  ["entry_est", "Entry"],
  ["stop_est", "Stop"],
  ["target_est", "Target"],
  ["notes", "Behavior Note"]
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
  previousRows: [],
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

function firstSentence(text, maxLength = 190) {
  const clean = String(text || "").replace(/\s+/g, " ").trim();
  if (!clean) return "";
  const sentence = clean.match(/^.*?[.!?](?:\s|$)/)?.[0]?.trim() || clean;
  return sentence.length > maxLength ? `${sentence.slice(0, maxLength - 1).trim()}...` : sentence;
}

function safeWebsite(value) {
  const text = String(value || "").trim();
  if (!/^https?:\/\//i.test(text)) return "";
  try {
    return new URL(text).href;
  } catch {
    return "";
  }
}

function renderCompanyBrief(profile) {
  const target = document.querySelector("#ticker-name");
  if (!target) return;
  const summary = firstSentence(profile?.business_summary);
  const highlights = String(profile?.latest_report_highlights || "").trim();
  const nextReport = String(profile?.next_report_date || "").trim();
  const website = safeWebsite(profile?.website);
  const industry = [profile?.sector, profile?.industry].filter(Boolean).join(" · ");
  const source = String(profile?.profile_source || "Company profile").trim();

  if (!summary && !highlights && !nextReport && !website && !industry) {
    target.innerHTML = "";
    return;
  }

  target.innerHTML = `
    <div class="company-brief">
      ${industry ? `<div class="company-kicker">${escapeHtml(industry)}</div>` : ""}
      ${summary ? `<p>${escapeHtml(summary)}</p>` : ""}
      <div class="company-facts">
        ${highlights ? `<div><span>Latest report</span><strong>${escapeHtml(highlights)}</strong></div>` : ""}
        ${nextReport ? `<div><span>Next report</span><strong>${escapeHtml(nextReport)}</strong></div>` : ""}
        ${website ? `<div><span>Website</span><strong><a href="${escapeHtml(website)}" target="_blank" rel="noopener noreferrer">${escapeHtml(new URL(website).hostname.replace(/^www\./, ""))}</a></strong></div>` : ""}
      </div>
      <span class="company-source">Source: ${escapeHtml(source)}</span>
    </div>
  `;
}

function hasCompanyBrief(profile) {
  return Boolean(
    profile?.business_summary ||
    profile?.latest_report_highlights ||
    profile?.next_report_date ||
    profile?.website ||
    profile?.sector ||
    profile?.industry
  );
}

async function fetchCompanyBrief(ticker) {
  const response = await fetch(`./api/company?ticker=${encodeURIComponent(ticker)}`);
  if (!response.ok) return {};
  return response.json();
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

function scoreBand(value) {
  const score = Number(value);
  if (score >= 75) return "strong";
  if (score >= 50) return "constructive";
  if (score >= 25) return "weak";
  return "risk";
}

function convictionScore(rowOrScore) {
  const raw = typeof rowOrScore === "object" ? numericValue(rowOrScore, "score") : Number(rowOrScore);
  if (!Number.isFinite(raw)) return 0;
  return Math.max(0, Math.min(100, (raw / 128) * 100));
}

function fmtConviction(rowOrScore) {
  return fmtNumber(convictionScore(rowOrScore), 0);
}

function behaviorDetail(row) {
  const kind = actionKind(row.action);
  const pattern = setupLabel(row.setup);
  const score = convictionScore(row);
  const move = numericValue(row, "day_change_pct");
  const tape = row.psychology || "Mixed tape";
  const mode = row.adaptive_mode || "Mixed mode";
  const note = String(row.notes || "").trim();

  if (note) return note;
  if (kind === "buy") return `${pattern} behavior with strong conviction and ${tape.toLowerCase()} tape.`;
  if (kind === "setup") return `${pattern} is forming; conviction is constructive but still developing.`;
  if (kind === "watch") return `${mode} behavior; monitor for conviction expansion or cleaner entry.`;
  if (kind === "exit") return `Exit pressure: weak conviction with ${move < 0 ? "negative" : "unstable"} price action.`;
  if (score < 25) return "Weak scanner behavior; avoid until conviction and tape improve.";
  return `${mode} behavior with no clear edge yet.`;
}

function payloadValue(row, key) {
  return row?.payload?.[key] ?? row?.[key];
}

function dataDateSummary(rows) {
  const dates = [...new Set(rows.map((row) => row.data_date || row.date || row.history_date).filter(Boolean))].sort();
  if (!dates.length) return "";
  const latest = dates.at(-1);
  const earliest = dates[0];
  return earliest === latest ? `Market data: ${latest}` : `Market data: ${earliest} to ${latest}`;
}

function isStaleMarketDate(runDate, rows) {
  const dates = rows.map((row) => row.data_date || row.date || row.history_date).filter(Boolean).sort();
  const latestDataDate = dates.at(-1);
  return Boolean(runDate && latestDataDate && latestDataDate < runDate);
}

function historyDateSummary(rows) {
  const dates = [...new Set(rows.map((row) => row.history_date || row.date).filter(Boolean))].sort();
  if (!dates.length) return "";
  return `History range: ${dates[0]} to ${dates.at(-1)}`;
}

function rowByTicker(rows) {
  return new Map(rows.map((row) => [row.ticker, row]));
}

function dailyChangeItems(rows, previousRows) {
  if (!rows.length || !previousRows.length) return [];
  const previousByTicker = rowByTicker(previousRows);
  return rows
    .map((row) => {
      const previous = previousByTicker.get(row.ticker);
      if (!previous) return null;
      const scoreMove = convictionScore(row) - convictionScore(previous);
      const actionChanged = row.action !== previous.action;
      const setupChanged = row.setup !== previous.setup;
      const priceMove = numericValue(row, "close") - numericValue(previous, "close");
      const previousClose = numericValue(previous, "close");
      const pricePct = previousClose ? (priceMove / previousClose) * 100 : 0;
      const priority =
        (actionChanged ? 40 : 0) +
        (setupChanged ? 20 : 0) +
        Math.min(Math.abs(scoreMove), 30) +
        Math.min(Math.abs(pricePct), 10);
      if (!actionChanged && !setupChanged && Math.abs(scoreMove) < 6 && Math.abs(pricePct) < 3) return null;
      return { row, previous, scoreMove, pricePct, actionChanged, setupChanged, priority };
    })
    .filter(Boolean)
    .sort((a, b) => b.priority - a.priority)
    .slice(0, 8);
}

function gaugePoint(score, radius = 58) {
  const clamped = Math.max(0, Math.min(100, score));
  const angle = Math.PI + (clamped / 100) * Math.PI;
  return {
    x: 90 + radius * Math.cos(angle),
    y: 84 + radius * Math.sin(angle)
  };
}

function gaugePointerPath(point) {
  const base = { x: 90, y: 63 };
  const dx = point.x - base.x;
  const dy = point.y - base.y;
  const length = Math.hypot(dx, dy) || 1;
  const ux = dx / length;
  const uy = dy / length;
  const px = -uy;
  const py = ux;
  const tip = {
    x: base.x + ux * Math.max(0, length - 4),
    y: base.y + uy * Math.max(0, length - 4)
  };
  const head = {
    x: tip.x - ux * 9,
    y: tip.y - uy * 9
  };
  const shaftWidth = 2.4;
  const headWidth = 6.2;
  return [
    `M ${(base.x + px * shaftWidth).toFixed(1)} ${(base.y + py * shaftWidth).toFixed(1)}`,
    `L ${(head.x + px * shaftWidth).toFixed(1)} ${(head.y + py * shaftWidth).toFixed(1)}`,
    `L ${(head.x + px * headWidth).toFixed(1)} ${(head.y + py * headWidth).toFixed(1)}`,
    `L ${tip.x.toFixed(1)} ${tip.y.toFixed(1)}`,
    `L ${(head.x - px * headWidth).toFixed(1)} ${(head.y - py * headWidth).toFixed(1)}`,
    `L ${(head.x - px * shaftWidth).toFixed(1)} ${(head.y - py * shaftWidth).toFixed(1)}`,
    `L ${(base.x - px * shaftWidth).toFixed(1)} ${(base.y - py * shaftWidth).toFixed(1)}`,
    "Z"
  ].join(" ");
}

function renderGauge(row) {
  const gauge = convictionScore(row);
  const point = gaugePoint(gauge);
  const band = scoreBand(gauge);
  const pointer = gaugePointerPath(point);
  return `
    <div class="conviction-gauge score-${band}">
      <svg viewBox="0 0 180 104" role="img" aria-label="Conviction score ${fmtConviction(row)} out of 100">
        <path class="gauge-track" pathLength="100" d="M 24 84 A 66 66 0 0 1 156 84" />
        <path class="gauge-zone zone-risk" pathLength="100" d="M 24 84 A 66 66 0 0 1 156 84" />
        <path class="gauge-zone zone-weak" pathLength="100" d="M 24 84 A 66 66 0 0 1 156 84" />
        <path class="gauge-zone zone-constructive" pathLength="100" d="M 24 84 A 66 66 0 0 1 156 84" />
        <path class="gauge-zone zone-strong" pathLength="100" d="M 24 84 A 66 66 0 0 1 156 84" />
        <path class="gauge-pointer" d="${pointer}" />
        <circle class="gauge-hub" cx="90" cy="63" r="4.2" />
      </svg>
      <div class="gauge-readout">
        <strong>${fmtConviction(row)}</strong>
        <small>/100</small>
      </div>
    </div>
  `;
}

function renderScoreBreakdown(row) {
  const atrPct = Number(payloadValue(row, "atr_pct"));
  const buyer = Number(payloadValue(row, "buyer_score"));
  const seller = Number(payloadValue(row, "seller_score"));
  const volume = payloadValue(row, "volume_state") || "NEUTRAL";
  const items = [
    ["Trend", row.adaptive_mode || "Mixed"],
    ["Candle", buyer >= seller ? `Buyer ${fmtNumber(buyer, 0)}` : `Seller ${fmtNumber(seller, 0)}`],
    ["Volume", volume],
    ["Volatility", Number.isFinite(atrPct) ? `ATR ${fmtNumber(atrPct, 1)}%` : "n/a"],
    ["Pattern", setupLabel(row.setup)]
  ];
  return `
    <div class="score-explainer">
      <div class="score-explainer-head">
        <span>Conviction Read</span>
        <strong>${escapeHtml(behaviorDetail(row))}</strong>
      </div>
      <div class="score-factors">
        ${items.map(([label, value]) => `
          <div>
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(value)}</strong>
          </div>
        `).join("")}
      </div>
      ${renderGauge(row)}
    </div>
  `;
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
  const scoreMove = convictionScore(row) - convictionScore(previous);
  if (Math.abs(scoreMove) >= 4) {
    chips.push(`<span class="change-chip ${moveClass(scoreMove)}">Conviction ${fmtSignedNumber(scoreMove, 0)}</span>`);
  }
  return chips.join(" ") || `<span class="change-chip quiet">Steady</span>`;
}

function setStatus(message, ok = true) {
  const status = document.querySelector("#status");
  const runStatus = document.querySelector("#run-status");
  if (status) status.textContent = message;
  if (runStatus) runStatus.classList.toggle("bad", !ok);
}

function setRefreshSummary(latest, marketData, rows) {
  const status = document.querySelector("#status");
  const runStatus = document.querySelector("#run-status");
  if (runStatus) {
    const stalePrefix = isStaleMarketDate(latest, rows) ? "Market data may lag · " : "";
    runStatus.textContent = `${stalePrefix}Updated ${latest} · ${marketData}`;
  }
  if (status) status.textContent = APP_DISCLAIMER;
  if (runStatus) runStatus.classList.remove("bad");
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

async function recentRunDates(limit = 2) {
  const rows = await supabaseFetch("watchlist_snapshots?select=run_date&order=run_date.desc&limit=600");
  const dates = [];
  rows.forEach((row) => {
    if (row.run_date && !dates.includes(row.run_date)) dates.push(row.run_date);
  });
  return dates.slice(0, limit);
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
    return `<span class="badge pattern-pill">${escapeHtml(setupLabel(row.setup))}</span>`;
  }
  if (key === "notes") {
    return `<span class="behavior-detail">${escapeHtml(behaviorDetail(row))}</span>`;
  }
  if (key === "score") return `<span class="badge conviction-pill">${escapeHtml(fmtConviction(row))}</span>`;
  if (key === "day_change_pct") return renderMovePct(row[key]);
  if (["close", "entry_est", "stop_est", "target_est"].includes(key)) return escapeHtml(fmtNumber(row[key], 2));
  return escapeHtml(row[key]);
}

function renderMobileWatchlistSummary(row) {
  const kind = actionKind(row.action);
  return `
    <a class="mobile-watch-row" href="./history.html?ticker=${encodeURIComponent(row.ticker)}">
      <span class="mobile-watch-main">
        <strong>${escapeHtml(row.ticker)}</strong>
        <span>${escapeHtml(displaySecurityName(row.name, row.ticker) || row.name || row.ticker)}</span>
        <span class="mobile-watch-tags">
          <span class="badge ${kind}">${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>
          <span class="badge pattern-pill">${escapeHtml(setupLabel(row.setup))}</span>
          <span class="badge conviction-pill">${escapeHtml(fmtConviction(row))}</span>
          <span class="badge entry-pill">Entry ${escapeHtml(fmtNumber(row.entry_est, 2))}</span>
        </span>
      </span>
      <span class="mobile-watch-price">
        <strong>${escapeHtml(fmtNumber(row.close, 2))}</strong>
        ${renderMovePct(row.day_change_pct)}
      </span>
    </a>
  `;
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
  const score = fmtConviction(row);
  return `
    <a class="focus-item tone-${kind}" href="./history.html?ticker=${encodeURIComponent(row.ticker)}" style="--score-pct: ${score}%">
      <span class="focus-kicker">${escapeHtml(reason)}</span>
      <span class="focus-main">
        <strong>${escapeHtml(row.ticker)}</strong>
        <span>${escapeHtml(displaySecurityName(row.name, row.ticker) || row.name || "")}</span>
      </span>
      <span class="focus-meta">
        <span class="badge ${kind}">${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>
        <span>${score}/100</span>
        <span>Close ${fmtNumber(row.close, 2)} ${renderMovePct(row.day_change_pct)}</span>
      </span>
      <span class="focus-meter" aria-hidden="true"><i></i></span>
    </a>
  `;
}

function renderTodayFocus() {
  const panel = document.querySelector("#today-focus");
  if (!panel) return;
  const runDate = state.rows[0]?.run_date || "";
  const ranked = [...state.rows].sort((a, b) => convictionScore(b) - convictionScore(a));
  const strongest = ranked.find((row) => actionKind(row.action) === "buy");
  const building = ranked.find((row) => actionKind(row.action) === "setup");
  const pressure = [...state.rows]
    .filter((row) => actionKind(row.action) === "exit")
    .sort((a, b) => convictionScore(a) - convictionScore(b))[0];
  const bestDay = [...state.rows]
    .filter((row) => ["buy", "setup", "watch"].includes(actionKind(row.action)))
    .sort((a, b) => Number(b.day_change_pct || 0) - Number(a.day_change_pct || 0))[0];

  const items = [
    focusItem(strongest, "Buy"),
    focusItem(building, "Setup"),
    focusItem(pressure, "Exit"),
    focusItem(bestDay, "Move")
  ].filter(Boolean);

  panel.innerHTML = `
    <div class="section-heading">
      <div>
        <span>Today’s Focus</span>
      </div>
      ${runDate ? `<span class="section-date">${escapeHtml(runDate)}</span>` : ""}
    </div>
    <div class="focus-grid">${items.join("")}</div>
  `;
}

function renderChangedToday() {
  const panel = document.querySelector("#changed-today");
  if (!panel) return;
  const runDate = state.rows[0]?.run_date || "";
  const changes = dailyChangeItems(state.rows, state.previousRows);
  if (!changes.length) {
    panel.innerHTML = `
      <div class="section-heading">
        <div>
          <span>Today’s Movers</span>
        </div>
        ${runDate ? `<span class="section-date">${escapeHtml(runDate)}</span>` : ""}
      </div>
      <div class="empty compact-empty">No major scanner changes versus the previous run.</div>
    `;
    return;
  }

  panel.innerHTML = `
    <div class="section-heading">
      <div>
        <span>Today’s Movers</span>
      </div>
      ${runDate ? `<span class="section-date">${escapeHtml(runDate)}</span>` : ""}
    </div>
    <div class="change-grid">
      ${changes.map(({ row, previous, scoreMove, pricePct, actionChanged, setupChanged }) => `
        <a class="change-card tone-${actionKind(row.action)}" href="./history.html?ticker=${encodeURIComponent(row.ticker)}">
          <div class="change-card-head">
            <strong>${escapeHtml(row.ticker)}</strong>
            <span>${escapeHtml(displaySecurityName(row.name, row.ticker) || row.name || "")}</span>
          </div>
          <div class="change-card-body">
            ${actionChanged ? `<span class="change-chip signal">${escapeHtml(ACTION_LABELS[previous.action] || previous.action)} <b>→</b> ${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>` : ""}
            ${setupChanged ? `<span class="change-chip setup">${escapeHtml(setupLabel(previous.setup))} <b>→</b> ${escapeHtml(setupLabel(row.setup))}</span>` : ""}
            <span class="change-chip ${moveClass(scoreMove)}">Conviction ${fmtSignedNumber(scoreMove, 0)}</span>
            <span class="change-chip ${moveClass(pricePct)}">Price ${fmtSignedNumber(pricePct, 1)}%</span>
          </div>
        </a>
      `).join("")}
    </div>
  `;
}

function renderWatchlist() {
  const counts = { buy: 0, setup: 0, watch: 0, exit: 0, avoid: 0 };
  state.rows.forEach((row) => {
    counts[actionKind(row.action)] += 1;
  });
  renderCards(counts);
  renderTodayFocus();
  renderChangedToday();

  const needle = state.query.trim().toLowerCase();
  const [sortKey, direction] = state.sort.split("-");
  const multiplier = direction === "asc" ? 1 : -1;
  state.visibleRows = state.rows
    .filter((row) => state.filter === "all" || actionKind(row.action) === state.filter)
    .filter((row) => !needle || WATCHLIST_COLUMNS.some(([key]) => String(row[key] || "").toLowerCase().includes(needle)))
    .sort((a, b) => {
      if (sortKey === "ticker") return a.ticker.localeCompare(b.ticker) * multiplier;
      if (sortKey === "score") return (convictionScore(a) - convictionScore(b)) * multiplier;
      return (Number(a[sortKey] || 0) - Number(b[sortKey] || 0)) * multiplier;
    });

  document.querySelector("#watchlist-head").innerHTML = `<tr>${WATCHLIST_COLUMNS.map(([, label]) => `<th>${label}</th>`).join("")}</tr>`;
  document.querySelector("#watchlist-body").innerHTML = state.visibleRows.map((row) => `
    <tr class="row-${actionKind(row.action)}" style="--score-pct: ${fmtConviction(row)}%">
      ${WATCHLIST_COLUMNS.map(([key]) => `<td class="${["score", "close", "day_change_pct", "entry_est", "stop_est", "target_est"].includes(key) ? "num" : ""}">${renderWatchlistCell(row, key)}</td>`).join("")}
      <td class="mobile-summary">${renderMobileWatchlistSummary(row)}</td>
    </tr>
  `).join("");
  document.querySelector("#count").textContent = `${state.visibleRows.length} / ${state.rows.length} shown`;
  document.querySelector("#empty").classList.toggle("hidden", state.visibleRows.length > 0);
}

function initTabNavigation() {
  const tabs = [...document.querySelectorAll(".app-tabbar a")];
  if (!tabs.length) return;
  const setActive = (hash) => {
    tabs.forEach((tab) => tab.classList.toggle("active", tab.getAttribute("href") === hash));
  };
  tabs.forEach((tab) => {
    tab.addEventListener("click", (event) => {
      const hash = tab.getAttribute("href");
      const target = hash ? document.querySelector(hash) : null;
      if (!target) return;
      event.preventDefault();
      setActive(hash);
      const stickyOffset = window.matchMedia("(max-width: 960px)").matches ? 150 : 24;
      const top = Math.max(0, target.getBoundingClientRect().top + window.scrollY - stickyOffset);
      window.history.replaceState(null, "", hash);
      window.scrollTo({ top, behavior: "smooth" });
    });
  });
  if (window.location.hash) setActive(window.location.hash);
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
  initTabNavigation();
  try {
    const [latest, previous] = await recentRunDates(2);
    if (!latest) throw new Error("No Supabase run found yet.");
    state.rows = (await supabaseFetch(`watchlist_snapshots?select=*&run_date=eq.${encodeURIComponent(latest)}&order=score.desc`))
      .map((row) => ({ ...row, name: displaySecurityName(row.name, row.ticker) || row.name || row.ticker }));
    state.previousRows = previous
      ? await supabaseFetch(`watchlist_snapshots?select=*&run_date=eq.${encodeURIComponent(previous)}&order=score.desc`)
      : [];
    const marketData = dataDateSummary(state.rows);
    setRefreshSummary(latest, marketData, state.rows);
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
        <div><span>Conviction</span><strong>${fmtConviction(latest)}/100</strong></div>
        <div><span>Pattern</span><strong>${escapeHtml(setupLabel(latest.setup))}</strong></div>
        <div><span>Entry</span><strong>${fmtNumber(latest.entry_est, 2)}</strong></div>
      </div>
      ${renderScoreBreakdown(latest)}
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

  const width = 960;
  const height = 146;
  const pad = { left: 34, right: 22, top: 16, bottom: 26 };
  const plotWidth = width - pad.left - pad.right;
  const plotHeight = height - pad.top - pad.bottom;
  const scores = chronological.map((row) => convictionScore(row));
  const closes = chronological.map((row) => numericValue(row, "close"));
  const minClose = Math.min(...closes);
  const maxClose = Math.max(...closes);
  const xFor = (index) => pad.left + (chronological.length === 1 ? plotWidth / 2 : (index / (chronological.length - 1)) * plotWidth);
  const scoreY = (score) => pad.top + plotHeight - (Math.max(0, Math.min(100, score)) / 100) * plotHeight;
  const closeY = (close) => scalePoint(close, minClose, maxClose, pad.top + plotHeight, pad.top);
  const pricePointList = chronological.map((row, index) => ({ x: xFor(index), y: closeY(numericValue(row, "close")) }));
  const pricePath = linePath(pricePointList);
  const latest = chronological.at(-1);
  const first = chronological[0];
  const priceMove = numericValue(latest, "close") - numericValue(first, "close");
  const firstClose = numericValue(first, "close");
  const priceMovePct = firstClose ? (priceMove / firstClose) * 100 : 0;
  const signalCounts = chronological.reduce((counts, row) => {
    const kind = actionKind(row.action);
    counts[kind] = (counts[kind] || 0) + 1;
    return counts;
  }, {});
  const dominantSignal = Object.entries(signalCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || "watch";
  const priceRange = maxClose - minClose;
  const gridLines = [75, 50, 25].map((score) => `
    <line x1="${pad.left}" y1="${scoreY(score).toFixed(1)}" x2="${width - pad.right}" y2="${scoreY(score).toFixed(1)}" class="chart-grid" />
    <text x="${pad.left - 10}" y="${scoreY(score).toFixed(1) + 3}" text-anchor="end" class="score-tick">${score}</text>
  `).join("");
  const barSlot = chronological.length > 1 ? plotWidth / chronological.length : plotWidth;
  const barWidth = Math.max(6, Math.min(18, barSlot * 0.58));
  const baselineY = pad.top + plotHeight;
  const scoreBars = chronological.map((row, index) => {
    const score = convictionScore(row);
    const y = scoreY(score);
    const x = xFor(index) - barWidth / 2;
    return `
      <rect class="score-bar score-${scoreBand(score)}" x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${barWidth.toFixed(1)}" height="${Math.max(1, baselineY - y).toFixed(1)}" rx="3">
        <title>${escapeHtml(row.history_date)} · conviction ${fmtConviction(row)}/100 · raw rank ${fmtNumber(row.score, 1)} · close ${fmtNumber(row.close, 2)}</title>
      </rect>
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
        <span class="subtle">30-day price move</span>
        <strong class="${priceMove >= 0 ? "up" : "down"}">
          ${priceMove >= 0 ? "+" : ""}${fmtNumber(priceMove, 2)}
          <span>${fmtSignedNumber(priceMovePct, 1)}%</span>
        </strong>
      </div>
    </div>
    <details class="chart-details">
      <summary>
        <span>Show Conviction Detail</span>
        <strong>Daily bars, compact view</strong>
      </summary>
      <div class="chart-card">
      <div class="chart-heading">
        <div>
          <span>Conviction Detail</span>
          <strong>Daily normalized conviction bars</strong>
          <p class="chart-note">Bars show normalized conviction from 0-100. The thin dotted line shows close-price direction, scaled only for shape comparison.</p>
        </div>
        <div class="chart-latest">
          <span>Latest</span>
          <strong>${fmtConviction(latest)}</strong>
        </div>
      </div>
      <svg class="history-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(state.ticker)} 30-day conviction and price chart">
        <rect x="${pad.left}" y="${pad.top}" width="${plotWidth}" height="${plotHeight}" class="plot-bg" />
        ${gridLines}
        ${scoreBars}
        <path d="${pricePath}" class="price-line" />
        ${dateTicks}
      </svg>
      <div class="chart-legend">
        <span><i class="legend-score"></i> daily conviction bars</span>
        <span><i class="legend-price"></i> price direction</span>
      </div>
      <div class="chart-insights">
        <div><span>Dominant signal</span><strong>${escapeHtml(KIND_LABELS[dominantSignal] || dominantSignal.toUpperCase())}</strong></div>
        <div><span>Current pattern</span><strong>${escapeHtml(setupLabel(latest.setup))}</strong></div>
        <div><span>Close range</span><strong>${fmtNumber(minClose, 2)} - ${fmtNumber(maxClose, 2)}</strong></div>
        <div><span>Range width</span><strong>${fmtNumber(priceRange, 2)}</strong></div>
      </div>
      </div>
    </details>
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
      return row.action !== previous.action || row.setup !== previous.setup || Math.abs(convictionScore(row) - convictionScore(previous)) >= 6;
    })
    .slice(-8)
    .reverse();
  const oldestMomentDate = moments[moments.length - 1]?.row.history_date;
  const lookbackRows = oldestMomentDate
    ? state.historyRows.filter((row) => row.history_date < oldestMomentDate)
    : state.historyRows.slice(1);

  timeline.innerHTML = `
    <h3>Key Behavior Moments</h3>
    ${moments.map(({ row, previous, index }) => `
      <div class="moment-card tone-${actionKind(row.action)}">
        <div class="moment-date">${index === chronological.length - 1 ? "Latest" : escapeHtml(fmtCompactDate(row.history_date))}</div>
        <div class="moment-body">
          <span class="badge ${actionKind(row.action)}">${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>
          <div class="change-chips">${renderHistoryChangeChips(row, previous)}</div>
          <p class="subtle">Close ${fmtNumber(row.close, 2)} ${renderMovePct(row.day_change_pct)} · Conviction ${fmtConviction(row)}/100 · Pattern ${escapeHtml(setupLabel(row.setup))} · ${escapeHtml(row.adaptive_mode || "Mixed")}</p>
          ${row.notes ? `<p class="subtle">${escapeHtml(row.notes)}</p>` : ""}
        </div>
      </div>
    `).join("")}
    <details class="raw-history" open>
      <summary>Show Earlier Days</summary>
      <div class="lookback-grid">
      ${lookbackRows.length ? lookbackRows.map((row) => `
        <article class="lookback-card tone-${actionKind(row.action)}">
          <div class="lookback-date">
            <strong>${escapeHtml(fmtCompactDate(row.history_date))}</strong>
            <span>${escapeHtml(row.history_date)}</span>
          </div>
          <div class="lookback-main">
            <span class="badge ${actionKind(row.action)}">${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>
            <strong>${fmtConviction(row)}</strong>
            <span>Conviction</span>
          </div>
          <div class="lookback-meta">
            <span>${escapeHtml(setupLabel(row.setup))}</span>
            <span>${escapeHtml(row.adaptive_mode || "Mixed")}</span>
          </div>
          <div class="bar"><span class="score-${scoreBand(convictionScore(row))}" style="width: ${Math.max(2, convictionScore(row))}%"></span></div>
          <div class="lookback-price">
            <strong>${fmtNumber(row.close, 2)}</strong>
            ${renderMovePct(row.day_change_pct)}
          </div>
        </article>
      `).join("") : "<div class=\"empty compact-empty\">No earlier look-back days available.</div>"}
      </div>
    </details>
  `;
}

async function loadHistory(ticker) {
  state.ticker = normaliseTicker(ticker);
  state.tickerName = "";
  document.querySelector("#ticker").value = state.ticker;
  document.querySelector("#history-title").textContent = state.ticker;
  document.querySelector("#ticker-name").innerHTML = "";
  document.title = state.ticker;
  window.history.replaceState(null, "", `./history.html?ticker=${encodeURIComponent(state.ticker)}`);
  setStatus("Loading ticker history...");
  document.querySelector("#run-status").textContent = "No history loaded";
  document.querySelector("#run-status").classList.add("bad");
  try {
    const runRows = await supabaseFetch(`watchlist_behavior_history?select=run_date&ticker=eq.${encodeURIComponent(state.ticker)}&order=run_date.desc&limit=1`);
    const latest = runRows[0]?.run_date;
    if (!latest) throw new Error(`No 30-day history found for ${state.ticker}.`);
    const snapshotRows = await supabaseFetch(`watchlist_snapshots?select=name,payload&ticker=eq.${encodeURIComponent(state.ticker)}&run_date=eq.${encodeURIComponent(latest)}&limit=1`);
    state.tickerName = displaySecurityName(snapshotRows[0]?.name, state.ticker);
    document.querySelector("#history-title").textContent = historyDisplayTitle();
    document.title = historyDisplayTitle();
    state.historyRows = await supabaseFetch(`watchlist_behavior_history?select=*&ticker=eq.${encodeURIComponent(state.ticker)}&run_date=eq.${encodeURIComponent(latest)}&order=history_date.desc`);
    const marketData = historyDateSummary(state.historyRows);
    setRefreshSummary(latest, marketData, state.historyRows);
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
  loadHistory(ticker);
}

if (document.body.dataset.page === "history") {
  initHistory();
} else {
  initWatchlist();
}
