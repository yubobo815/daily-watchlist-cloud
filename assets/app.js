const UI_LABELS = {
  actions: {
    "BUY CANDIDATE": "BUY",
    "STRONG CONTINUATION": "TRENDING",
    "SETUP FORMING": "BUILDING",
    "WATCH TREND": "WATCH",
    "EXIT PRESSURE": "EXIT",
    "WAIT": "AVOID",
    "WAIT / AVOID": "AVOID"
  },
  setup: {
    "BREAKOUT BUY": "Breakout",
    "MOMENTUM BUY": "Momentum",
    "PULLBACK BUY": "Pullback",
    "EARLY PULLBACK BUY": "Early Pullback",
    "REVERSAL BUY": "Reversal",
    "NONE": "None"
  },
  kinds: {
    buy: "BUY",
    continue: "TRENDING",
    setup: "BUILDING",
    watch: "WATCH",
    exit: "EXIT",
    avoid: "AVOID"
  },
  columns: {
    ticker: "Ticker",
    action: "Signal",
    score: "Quality",
    entry_est: "Entry plan",
    stop_est: "Protection",
    risk_pct_to_stop: "Downside",
    trade_context: "What it means",
  },
  text: {
    watchlist: "Watchlist",
    searchResults: "Search Results",
    shown: "shown",
    result: "result",
    results: "results",
    dailyBrief: "Daily Brief",
    actionableNames: "{total} actionable names: {buy} BUY, {building} BUILDING",
    fresh: "Fresh",
    upgraded: "Upgraded",
    movers: "Movers",
    risk: "Risk",
    reviewTicker: "Review {ticker}",
    showBuy: "Show BUY",
    todayFocus: "Today’s Focus",
    buyFocus: "Buy",
    buildingFocus: "Building",
    exitFocus: "Exit",
    moveFocus: "Move",
    signalChanges: "Signal Changes",
    priceMovers: "Price Movers",
    focusList: "Focus List",
    noScannerChanges: "No major scanner changes versus the previous run.",
    noPriceMoves: "No large current-day price moves."
  }
};

const WATCHLIST_COLUMN_KEYS = ["ticker", "action", "score", "entry_est", "stop_est", "risk_pct_to_stop", "trade_context"];
const ACTION_LABELS = UI_LABELS.actions;
const SETUP_LABELS = UI_LABELS.setup;
const KIND_LABELS = UI_LABELS.kinds;

const ACTION_TONE = {
  buy: "#0f8a5f",
  continue: "#0891b2",
  setup: "#b7791f",
  watch: "#2f5fb3",
  exit: "#b42318",
  avoid: "#667085"
};

const REASON_LABELS = {
  volume_expansion: "Volume expansion",
  trend_reclaim: "Trend reclaim",
  momentum_reclaim: "Momentum reclaim",
  support_retest: "Support retest",
  fear_rejection: "Fear rejection",
  quiet_absorption: "Quiet absorption",
  buyer_tape: "Buyer tape",
  seller_pressure: "Seller pressure",
  exit_pressure: "Exit pressure",
  extended_from_zone: "Extended from zone",
  reference_zone_adjusted: "Reference zone adjusted",
  stale_buy_no_progress: "Stale buy: no progress",
  fresh_buy_signal: "Fresh buy signal",
  market_leader: "Market leader",
  market_lagging: "Market lagging",
  event_risk: "Event risk",
  personality_extended: "Extended for this stock type",
  weak_reward_risk: "Weak reward/risk",
  buyer_quality_low: "Buyer quality below threshold",
  high_beta_entry_quality: "High-beta entry quality",
  fast_breakout_entry: "Fast breakout entry",
  pullback_reclaim_entry: "Pullback/reclaim entry",
  market_regime_block: "Market regime block",
  next_day_bullish_confirm: "Next-day bullish confirm",
  next_day_constructive_pullback: "Constructive pullback",
  next_day_watch_trend: "Watch trend personality",
  avoid_chase: "Avoid chase",
  execution_risk: "Execution risk",
  operator_accumulation: "Operator accumulation",
  operator_distribution: "Operator distribution",
  operator_short_pressure: "Short-pressure proxy",
  operator_squeeze_watch: "Squeeze watch",
  operator_bull_trap: "Bull trap",
  operator_bear_trap: "Bear trap / squeeze watch",
  operator_markup_demand: "Markup demand control",
  anti_signal_block: "Anti-signal block",
  anti_signal_caution: "Anti-signal caution",
  anti_stale_data: "Anti-signal: stale data",
  anti_bull_trap: "Anti-signal: bull trap",
  anti_distribution: "Anti-signal: distribution",
  anti_extended_chase: "Anti-signal: extended chase",
  anti_execution_blocked: "Anti-signal: execution blocked",
  anti_defensive_tape: "Anti-signal: defensive tape",
  data_stale_block: "Stale data blocked execution",
  cached_data_ok: "Cached data recent enough",
  post_exit_risk_persistence: "Post-exit risk persists",
  top_buy_tier: "A+ buy tier",
  buy_watch_tier: "Buy watch tier",
  learning_confirmed_setup: "Learning-confirmed building",
  setup_only_tier: "Setup only",
  feedback_failed: "Prior signal failed",
  feedback_stale: "Prior signal stale",
  feedback_working: "Prior signal working",
  historical_edge_caution: "Historical edge caution",
  ticker_edge_weak: "Ticker edge weak",
  ticker_caution: "Ticker caution",
  ticker_insufficient: "Ticker history insufficient",
  failed_walk_forward: "Failed walk-forward",
  walk_forward_insufficient: "Walk-forward insufficient",
  risk_governor_block: "Risk governor block",
  missing_audit_gates: "Audit gates pending",
  missing_execution_proof: "Historical confirmation is incomplete"
};

const APP_DISCLAIMER = "This tool is intended for reference and analysis only. Do not consider this as financial or investment advice.";
const SUPABASE_CACHE_TTL_MS = 2 * 60 * 1000;
const JSON_CACHE_PREFIX = "daily-trade-copilot:json:v1:";
const API_CACHE_PREFIX = "daily-trade-copilot:api:v1:";
const FOCUS_LIST_KEY = "daily-trade-copilot:focus-tickers:v1";
const FOCUS_PIN_KEY = "daily-trade-copilot:focus-pin:v1";
const PUBLISHED_DATA_BASE_URL = "https://yubobo815.github.io/daily-watchlist-cloud/data/";
const INITIAL_WATCHLIST_ROWS = 40;
const LOCAL_STATIC_DATA_MODE = ["localhost", "127.0.0.1"].includes(window.location.hostname)
  && new URLSearchParams(window.location.search).get("dataMode") === "static";

function copyText(key, replacements = {}) {
  const text = UI_LABELS.text[key] || key;
  return Object.entries(replacements).reduce(
    (result, [name, value]) => result.replaceAll(`{${name}}`, String(value)),
    text
  );
}

function watchlistColumns() {
  return WATCHLIST_COLUMN_KEYS.map((key) => [key, UI_LABELS.columns[key] || key]);
}

function executionQueues(counts) {
  return [
    { key: "buy", filter: "buy", label: "BUY", count: counts.buy || 0, detail: "Entry-ready candidates" },
    {
      key: "building",
      filter: "building",
      label: "BUILDING",
      count: (counts.continue || 0) + (counts.setup || 0) + (counts.watch || 0),
      detail: `${counts.continue || 0} trending · ${counts.setup || 0} setup · ${counts.watch || 0} watch`,
    },
    {
      key: "risk",
      filter: "risk",
      label: "RISK",
      count: (counts.exit || 0) + (counts.avoid || 0),
      detail: `${counts.exit || 0} exit · ${counts.avoid || 0} avoid`,
    },
  ];
}

const COMPANY_PROFILE_FALLBACKS = {
  AAPL: ["Consumer Technology", "Apple designs iPhone, Mac, iPad, wearables, services, and related software ecosystems.", "apple.com"],
  AMD: ["Semiconductors", "Advanced Micro Devices designs CPUs, GPUs, adaptive chips, and data-center accelerators.", "amd.com"],
  AMZN: ["Internet Retail & Cloud", "Amazon operates e-commerce marketplaces, logistics, advertising, subscriptions, and AWS cloud services.", "amazon.com"],
  AVGO: ["Semiconductors & Infrastructure Software", "Broadcom supplies semiconductor connectivity products and infrastructure software for enterprise and cloud customers.", "broadcom.com"],
  CSCO: ["Networking & Security", "Cisco provides networking hardware, software, cybersecurity, observability, and collaboration products for enterprises and service providers.", "cisco.com"],
  CSX: ["Rail Transportation", "CSX operates a major freight railroad network across the eastern United States.", "csx.com"],
  DELL: ["Technology Hardware", "Dell provides PCs, servers, storage, networking, and infrastructure solutions for consumers and enterprises.", "dell.com"],
  GOOGL: ["Internet Services", "Alphabet operates Google Search, YouTube, Android, cloud services, advertising platforms, and AI products.", "abc.xyz"],
  GOOG: ["Internet Services", "Alphabet operates Google Search, YouTube, Android, cloud services, advertising platforms, and AI products.", "abc.xyz"],
  META: ["Social Platforms", "Meta operates Facebook, Instagram, WhatsApp, Messenger, ads infrastructure, AI products, and Reality Labs.", "meta.com"],
  MRVL: ["Semiconductors", "Marvell designs data-infrastructure semiconductors for cloud, networking, storage, wireless, and automotive markets.", "marvell.com"],
  MSFT: ["Software & Cloud", "Microsoft provides productivity software, Windows, Azure cloud, gaming, security, and AI infrastructure.", "microsoft.com"],
  MU: ["Memory Semiconductors", "Micron manufactures DRAM, NAND, and memory/storage products used in data centers, PCs, mobile, and automotive markets.", "micron.com"],
  NVDA: ["AI Semiconductors", "NVIDIA designs GPUs, networking, systems, and software platforms for AI, gaming, professional visualization, and data centers.", "nvidia.com"],
  ORCL: ["Enterprise Software & Cloud", "Oracle provides enterprise databases, cloud infrastructure, business applications, and industry software.", "oracle.com"],
  PANW: ["Cybersecurity", "Palo Alto Networks provides network security, cloud security, security operations, and threat-intelligence platforms.", "paloaltonetworks.com"],
  PLTR: ["Data Analytics Software", "Palantir provides data integration, analytics, ontology, and AI operating platforms for commercial and government customers.", "palantir.com"],
  TSLA: ["Electric Vehicles & Energy", "Tesla designs electric vehicles, energy storage systems, solar products, charging infrastructure, and autonomous-driving software.", "tesla.com"],
  WDC: ["Data Storage Hardware", "Western Digital designs and manufactures hard disk drives, flash storage, SSDs, and data-center storage products for cloud, enterprise, client, and consumer markets.", "westerndigital.com"],
};

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
  previousByTicker: new Map(),
  visibleRows: [],
  filter: "all",
  query: "",
  sort: "execution_priority-asc",
  historyRows: [],
  ticker: "ORCL",
  tickerName: "",
  focusTickers: [],
  focusPin: "",
  focusMessage: "",
  focusSyncing: false,
  runInfo: null,
  selectedTicker: "",
  rowLimit: INITIAL_WATCHLIST_ROWS,
  staticManifest: null,
};

const APP_NOTIFICATION_HISTORY = "daily-watchlist-notification-history";
const APP_NOTIFICATION_READ = "daily-watchlist-notification-read";

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

function normaliseSearchTicker(value) {
  return String(value || "").trim().toUpperCase().replace("BRK.B", "BRK-B");
}

function tickerSearchAliases(row) {
  const ticker = normaliseSearchTicker(row?.ticker);
  if (!ticker) return [];
  return [...new Set([ticker, ticker.replace("-", ".")].filter(Boolean))];
}

function exactTickerSearchNeedle(query, rows) {
  const ticker = normaliseSearchTicker(query);
  if (!ticker || !/^[A-Z0-9.-]{1,8}$/.test(ticker)) return "";
  return rows.some((row) => tickerSearchAliases(row).includes(ticker)) ? ticker : "";
}

function actionKind(action) {
  return {
    "BUY CANDIDATE": "buy",
    "STRONG CONTINUATION": "continue",
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
  return state.tickerName ? `${state.ticker} · ${state.tickerName}` : state.ticker;
}

function cleanSummaryText(text) {
  const clean = String(text || "").replace(/\s+/g, " ").trim();
  return clean;
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
  const target = document.querySelector("#company-context");
  if (!target) return;
  const summary = cleanSummaryText(profile?.business_summary);
  const highlights = String(profile?.latest_report_highlights || "").trim();
  const nextReport = String(profile?.next_report_date || "").trim();
  const website = safeWebsite(profile?.website);
  const industry = [profile?.sector, profile?.industry].filter(Boolean).join(" · ");
  const source = String(profile?.profile_source || "Company profile").trim();
  const summaryPreview = summary.length > 260 ? `${summary.slice(0, 257).replace(/\s+\S*$/, "")}...` : summary;

  if (!summary && !highlights && !nextReport && !website && !industry) {
    setCompanyContextAvailable(false);
    target.innerHTML = `
      <h2>About the company</h2>
      <div class="company-context-empty subtle">Company information is not available.</div>
    `;
    return;
  }

  setCompanyContextAvailable(true);
  target.innerHTML = `
    <h2>About the company</h2>
    <details class="company-brief">
      <summary>
        ${industry ? `<div class="company-kicker">${escapeHtml(industry)}</div>` : ""}
        ${summaryPreview ? `<p>${escapeHtml(summaryPreview)}</p>` : ""}
        ${summary && summary.length > summaryPreview.length ? `<span class="company-toggle" data-open="Show less" data-closed="Show company details"></span>` : ""}
      </summary>
      <div class="company-facts">
        ${summary && summary.length > summaryPreview.length ? `<div><span>Business overview</span><strong>${escapeHtml(summary)}</strong></div>` : ""}
        ${highlights ? `<div><span>Latest report</span><strong>${escapeHtml(highlights)}</strong></div>` : ""}
        ${nextReport ? `<div><span>Next report</span><strong>${escapeHtml(nextReport)}</strong></div>` : ""}
        ${website ? `<div><span>Website</span><strong><a href="${escapeHtml(website)}" target="_blank" rel="noopener noreferrer">${escapeHtml(new URL(website).hostname.replace(/^www\./, ""))}</a></strong></div>` : ""}
      </div>
      <span class="company-source">Source: ${escapeHtml(source)}</span>
    </details>
  `;
}

function setCompanyContextAvailable(available) {
  const section = document.querySelector("#company-context");
  const tab = document.querySelector('.app-tabbar a[href="#company-context"]');
  if (section) section.hidden = !available;
  if (tab) tab.hidden = !available;
}

function hasCompanyProfile(profile) {
  return Boolean(
    cleanSummaryText(profile?.business_summary)
    || String(profile?.latest_report_highlights || "").trim()
    || String(profile?.next_report_date || "").trim()
    || safeWebsite(profile?.website)
    || [profile?.sector, profile?.industry].filter(Boolean).join(" · ")
  );
}

function fallbackCompanyProfile(ticker) {
  const [industry, summary, domain] = COMPANY_PROFILE_FALLBACKS[normaliseTicker(ticker)] || [];
  if (!summary) return {};
  return {
    business_summary: summary,
    website: `https://${domain}`,
    industry,
    latest_report_highlights: "Live report highlights unavailable in fallback profile.",
    next_report_date: "Check investor relations",
    profile_source: "Built-in fallback profile",
  };
}

function isIncompleteCompanySummary(profile) {
  const summary = cleanSummaryText(profile?.business_summary);
  return !summary || summary.length < 100 || summary.split(/\s+/).filter(Boolean).length < 14;
}

function enrichCompanyProfile(ticker, profile = {}) {
  const fallback = fallbackCompanyProfile(ticker);
  if (!hasCompanyProfile(fallback)) return profile || {};
  if (!hasCompanyProfile(profile)) return fallback;
  if (!isIncompleteCompanySummary(profile)) return profile;

  return {
    ...fallback,
    ...profile,
    business_summary: fallback.business_summary,
    website: safeWebsite(profile.website) || fallback.website,
    industry: profile.industry || fallback.industry,
    profile_source: profile.profile_source
      ? `${profile.profile_source}; summary fallback`
      : fallback.profile_source,
  };
}

async function renderCompanyBriefWithFallback(ticker, profile) {
  const enrichedProfile = enrichCompanyProfile(ticker, profile || {});
  if (hasCompanyProfile(enrichedProfile)) {
    renderCompanyBrief(enrichedProfile);
    return;
  }

  renderCompanyBrief(fallbackCompanyProfile(ticker) || profile || {});
  try {
    const fallbackProfile = await appApiFetch(`/api/company?ticker=${encodeURIComponent(ticker)}`, 6 * 60 * 60 * 1000);
    if (hasCompanyProfile(fallbackProfile)) renderCompanyBrief(fallbackProfile);
  } catch {
    // Company context is useful, but ticker behavior should remain usable without it.
  }
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

function payloadNumeric(row, key) {
  const number = Number(payloadValue(row, key));
  return Number.isFinite(number) ? number : 0;
}

function reasonCodes(row) {
  const raw = payloadValue(row, "reason_codes");
  if (!raw) return [];
  const normalize = (values) => values
    .flatMap((value) => String(value ?? "").split(","))
    .map((item) => item.trim().replace(/^\[+|\]+$/g, "").replace(/^['\"]|['\"]$/g, "").trim())
    .filter(Boolean);
  if (Array.isArray(raw)) return normalize(raw);
  if (typeof raw === "string") {
    let source = raw.trim();
    try {
      const parsed = JSON.parse(source);
      if (Array.isArray(parsed)) return parsed.filter(Boolean);
      if (typeof parsed !== "string") return [];
      source = parsed.trim();
    } catch {
      // CSV serialization can preserve a Python-list string inside JSON quotes.
      source = source.replace(/^['\"]|['\"]$/g, "");
    }
    return normalize([source]);
  }
  return [];
}

function scannerScoreValue(row) {
  const adjusted = payloadValue(row, "adjusted_score");
  const raw = adjusted === "" || adjusted == null ? payloadValue(row, "score") : adjusted;
  const number = Number(raw);
  return Number.isFinite(number) ? number : 0;
}

function setupLabel(value) {
  if (!value) return SETUP_LABELS.NONE;
  return SETUP_LABELS[value] || value;
}

function entryQualityLabel(row) {
  const label = payloadValue(row, "entry_quality_label");
  if (label) return String(label);
  if (payloadValue(row, "extension_state") === "EXTENDED") return "Extended";
  if (row.setup && row.setup !== "NONE") return "Developing";
  return "";
}

function entryQualityTone(row) {
  const label = entryQualityLabel(row).toLowerCase();
  if (label.includes("breakout")) return "strong";
  if (label.includes("pullback") || label.includes("reclaim")) return "constructive";
  if (label.includes("extended") || label.includes("low")) return "risk";
  if (label.includes("developing")) return "watch";
  return "neutral";
}

function renderEntryQualityPill(row) {
  const label = entryQualityLabel(row);
  if (!label) return "";
  return `<span class="badge entry-pill entry-${entryQualityTone(row)}">${escapeHtml(label)}</span>`;
}

function nextDayBiasTone(value) {
  const text = String(value || "").toUpperCase();
  if (text.includes("BULLISH")) return "strong";
  if (text.includes("CONSTRUCTIVE") || text.includes("WATCH")) return "constructive";
  if (text.includes("AVOID") || text.includes("DEFENSIVE") || text.includes("BLOCK")) return "risk";
  return "watch";
}

function renderNextDayBias(row) {
  const bias = payloadValue(row, "next_day_bias") || "NEUTRAL";
  const score = Number(payloadValue(row, "next_day_bias_score"));
  const suffix = Number.isFinite(score) ? ` ${fmtNumber(score, 0)}` : "";
  return `<span class="badge entry-pill entry-${nextDayBiasTone(bias)}">${escapeHtml(`${bias}${suffix}`)}</span>`;
}

function operatorPressureTone(value) {
  const text = String(value || "").toUpperCase();
  if (text.includes("BULL_TRAP") || text.includes("DISTRIBUTION") || text === "SHORT PRESSURE") return "risk";
  if (text.includes("BEAR_TRAP") || text.includes("SQUEEZE") || text.includes("ACCUMULATION") || text.includes("ABSORPTION") || text.includes("MARKUP") || text.includes("DEMAND CONTROL")) return "constructive";
  return "watch";
}

function shortOperatorPressure(value) {
  const text = String(value || "NEUTRAL").toUpperCase();
  if (text === "ACCUMULATION") return "ACCUM";
  if (text === "MARKUP / DEMAND CONTROL") return "MARKUP";
  if (text === "BULL_TRAP") return "BULL TRAP";
  if (text === "DISTRIBUTION") return "DIST";
  if (text === "BEAR_TRAP / SQUEEZE WATCH") return "BEAR TRAP";
  if (text === "SHORT / DISTRIBUTION PRESSURE") return "SHORT/DIST";
  if (text === "ACCUMULATION / ABSORPTION") return "ABSORB";
  if (text === "SQUEEZE WATCH") return "SQUEEZE";
  if (text === "SHORT PRESSURE") return "SHORT";
  if (text === "DISTRIBUTION") return "DIST";
  return "NEUTRAL";
}

function renderOperatorPressure(row) {
  const pressure = payloadValue(row, "operator_state") || payloadValue(row, "operator_pressure") || "NEUTRAL";
  const score = Number(payloadValue(row, "operator_state_score") ?? payloadValue(row, "operator_pressure_score"));
  const suffix = Number.isFinite(score) ? ` ${fmtNumber(score, 0)}` : "";
  return `<span class="badge entry-pill entry-${operatorPressureTone(pressure)}" title="${escapeHtml(String(pressure))}">${escapeHtml(`${shortOperatorPressure(pressure)}${suffix}`)}</span>`;
}

function buyTierTone(value) {
  const text = String(value || "").toUpperCase();
  if (text === "A+ BUY") return "strong";
  if (text === "BUY WATCH" || text === "SETUP ONLY" || text === "WATCH") return "constructive";
  if (text.includes("EXIT") || text.includes("NO TRADE")) return "risk";
  return "watch";
}

function renderBuyTier(row) {
  const tier = payloadValue(row, "buy_tier") || (row.action === "BUY CANDIDATE" ? "BUY WATCH" : "");
  if (!tier) return "";
  return `<span class="badge entry-pill entry-${buyTierTone(tier)}">${escapeHtml(String(tier))}</span>`;
}

function renderDataProvider(row) {
  const provider = String(payloadValue(row, "data_provider") || "unknown").toUpperCase();
  const status = String(payloadValue(row, "data_provider_status") || "");
  const error = String(payloadValue(row, "data_provider_error") || "");
  const tone = provider === "CACHE" || status.includes("FALLBACK") ? "risk" : "constructive";
  const title = [status, error].filter(Boolean).join(" · ") || provider;
  return `<span class="badge entry-pill entry-${tone}" title="${escapeHtml(title)}">${escapeHtml(provider)}</span>`;
}

function permissionShort(value) {
  const text = String(value || "").toUpperCase();
  if (text === "ALLOW") return "A";
  if (text === "CAUTION") return "C";
  if (text === "BLOCK") return "B";
  if (text === "INSUFFICIENT") return "I";
  if (text === "NONE") return "-";
  if (!text || text === "UNKNOWN") return "?";
  return "?";
}

function permissionTone(value) {
  const text = String(value || "").toUpperCase();
  if (text === "ALLOW") return "strong";
  if (text === "CAUTION" || text === "INSUFFICIENT") return "watch";
  if (text === "BLOCK") return "risk";
  return "risk";
}

function renderPermissionGates(row) {
  const gates = [
    ["M", payloadValue(row, "market_permission")],
    ["T", payloadValue(row, "ticker_permission")],
    ["W", payloadValue(row, "walk_forward_permission")],
    ["R", payloadValue(row, "risk_permission")]
  ];
  return `<span class="gate-stack">${gates.map(([label, value]) => `
    <span class="badge gate-pill gate-${permissionTone(value)}" title="${label}: ${escapeHtml(String(value || "UNKNOWN"))}">${label}${permissionShort(value)}</span>
  `).join("")}</span>`;
}

function auditGateValues(row) {
  return [
    payloadValue(row, "market_permission"),
    payloadValue(row, "ticker_permission"),
    payloadValue(row, "walk_forward_permission"),
    payloadValue(row, "risk_permission")
  ].map((value) => String(value || "UNKNOWN").toUpperCase());
}

function isAuditGatePending(row) {
  const values = auditGateValues(row);
  return values.some((value) => !value || value === "UNKNOWN");
}

function auditGatePendingCount(rows = []) {
  return rows.filter(isAuditGatePending).length;
}

function scoreBand(value) {
  const score = Number(value);
  if (score >= 75) return "strong";
  if (score >= 50) return "constructive";
  if (score >= 25) return "weak";
  return "risk";
}

function qualityConstraintLabel(row) {
  if (!row || typeof row !== "object") return "";
  const freshnessBlocked = String(payloadValue(row, "freshness_block") || "").toUpperCase() === "YES";
  const quality = String(payloadValue(row, "signal_quality") || "").toUpperCase();
  const antiSignal = String(payloadValue(row, "anti_signal_level") || "").toUpperCase();
  if (freshnessBlocked) return "DATA OLD";
  if (quality.includes("NEEDS EXECUTION PROOF") || quality.includes("STATIC FALLBACK")) return "PENDING";
  if (antiSignal === "BLOCK") return "AVOID";
  if (antiSignal === "CAUTION") return "USE CAUTION";
  return "";
}

function strengthLabel(rowOrScore) {
  const constraint = qualityConstraintLabel(rowOrScore);
  if (constraint) return constraint;
  if (typeof rowOrScore === "object" && actionKind(rowOrScore.action) === "exit") return "Exit Risk";
  const band = scoreBand(convictionScore(rowOrScore));
  if (band === "strong") return "High";
  if (band === "constructive") return "Building";
  if (band === "weak") return "Neutral";
  return "Weak";
}

function strengthTone(rowOrScore) {
  if (qualityConstraintLabel(rowOrScore)) return "risk";
  if (typeof rowOrScore === "object" && actionKind(rowOrScore.action) === "exit") return "risk";
  return scoreBand(convictionScore(rowOrScore));
}

function setupTone(value) {
  const label = setupLabel(value).toUpperCase();
  if (!label || label === "NONE") return "neutral";
  if (label.includes("BUY") && label.includes("PULLBACK")) return "constructive";
  if (label.includes("BUY")) return "strong";
  if (label.includes("AVOID") || label.includes("WEAK") || label.includes("EXIT")) return "risk";
  return "watch";
}

function convictionScore(rowOrScore) {
  const raw = typeof rowOrScore === "object" ? scannerScoreValue(rowOrScore) : Number(rowOrScore);
  if (!Number.isFinite(raw)) return 0;
  return Math.max(0, Math.min(100, (raw / 128) * 100));
}

function fmtConviction(rowOrScore) {
  return fmtNumber(convictionScore(rowOrScore), 0);
}

function renderQualityScore(row) {
  const blockedLabel = qualityConstraintLabel(row);
  if (blockedLabel) {
    return `<span class="table-score score-blocked" title="A numeric score would be misleading until the required checks are clear">${blockedLabel}</span>`;
  }
  return `<span class="table-score score-${strengthTone(row)}">${escapeHtml(fmtConviction(row))}</span>`;
}

function naturalActionSentence(row) {
  const kind = actionKind(row.action);
  const pattern = setupLabel(row.setup);
  const style = String(payloadValue(row, "execution_style") || "").toUpperCase();
  if (kind === "buy" && style === "BREAKOUT TRIGGER") return `${pattern} conditions are in place; enter only if price reaches the breakout entry range without running above the maximum entry.`;
  if (kind === "buy") return `${pattern} conditions are in place; use a limit entry only inside the pullback zone and require it to hold.`;
  if (kind === "continue") return "The existing trend remains constructive, but a new entry should avoid chasing strength.";
  if (kind === "setup") return `${pattern} is taking shape, but it still needs confirmation before it becomes a buy.`;
  if (kind === "watch") return "There is no clean entry yet; wait for either a stronger breakout or a controlled pullback.";
  if (kind === "exit") return "The trend is under pressure; protect capital rather than looking for a new entry.";
  return "There is no favourable setup at the moment.";
}

function executionChecksClear(row) {
  const permissions = ["market_permission", "risk_permission", "ticker_permission", "walk_forward_permission"]
    .map((key) => String(payloadValue(row, key) || "").toUpperCase())
    .filter(Boolean);
  const personalityAllowed = String(payloadValue(row, "personality_setup_allowed") || "").toUpperCase();
  const kind = actionKind(row?.action);
  const fillState = String(payloadValue(row, "execution_fill_state") || "").toUpperCase();
  const fillProbability = Number(payloadValue(row, "execution_fill_probability"));
  const fillabilityClear = !["buy", "continue"].includes(kind)
    || (fillState === "VALIDATED" && Number.isFinite(fillProbability) && fillProbability >= 0.45);
  return !qualityConstraintLabel(row)
    && permissions.every((value) => value === "ALLOW")
    && personalityAllowed !== "NO"
    && fillabilityClear;
}

function entryPlanLabel(row, { active = false } = {}) {
  const style = String(payloadValue(row, "execution_style") || "").toUpperCase();
  if (style === "BREAKOUT TRIGGER") return active ? "Breakout entry range" : "Reference breakout range";
  if (style === "PULLBACK LIMIT") return active ? "Pullback zone" : "Reference pullback zone";
  return active ? "Entry zone" : "Reference zone";
}

function referenceZonePosition(row) {
  const close = numericValue(row, "close");
  const low = payloadNumeric(row, "entry_zone_low");
  const high = payloadNumeric(row, "entry_zone_high") || numericValue(row, "entry_est");
  if (!close || !high) return "";
  const label = entryPlanLabel(row).replace(/^Reference /, "").toLowerCase();
  if (close > high) return `${fmtNumber(((close / high) - 1) * 100, 1)}% above the ${label}`;
  if (low && close < low) return `${fmtNumber((1 - (close / low)) * 100, 1)}% below the ${label}`;
  return `inside the ${label}`;
}

function decisionHeadline(row) {
  const kind = actionKind(row.action);
  const clear = executionChecksClear(row);
  const position = referenceZonePosition(row);
  if (kind === "exit") return "Protect capital";
  if (kind === "avoid") return "Avoid new entries";
  if (!clear) return "Wait for stronger confirmation";
  if (kind === "setup" || kind === "watch") return "Wait for the setup to mature";
  if (kind === "continue") return position.includes("above") ? "Hold, but do not chase" : "Trend remains constructive";
  if (kind === "buy" && String(payloadValue(row, "execution_style") || "").toUpperCase() === "BREAKOUT TRIGGER") return "Wait for the breakout trigger";
  if (kind === "buy" && position.includes("above")) return "Do not chase above the entry zone";
  if (kind === "buy" && position.includes("inside")) return "Entry candidate is in range";
  return kind === "buy" ? "Watch for entry confirmation" : "Wait";
}

function decisionNarrative(row) {
  const kind = actionKind(row.action);
  const close = numericValue(row, "close");
  const move = numericValue(row, "day_change_pct");
  const position = referenceZonePosition(row);
  const priceLead = close
    ? `Closed at ${fmtNumber(close, 2)}${Number.isFinite(move) ? ` after ${move >= 0 ? "rising" : "falling"} ${fmtNumber(Math.abs(move), 1)}%` : ""}`
    : "Latest price is unavailable";
  if (kind === "exit") return `${priceLead}. The trend is under pressure; reduce exposure or follow the existing stop rather than opening a new position.`;
  if (kind === "avoid") return `${priceLead}. There is no favourable setup, so keep this name off the entry list.`;
  if (!executionChecksClear(row)) {
    const location = position ? ` Price is ${position}.` : "";
    return `${priceLead}.${location} ${validationSummary(row)}`;
  }
  if (kind === "setup" || kind === "watch") return `${priceLead}. ${naturalActionSentence(row)}${position ? ` Price is ${position}.` : ""}`;
  if (kind === "buy" && String(payloadValue(row, "execution_style") || "").toUpperCase() === "BREAKOUT TRIGGER") {
    return `${priceLead}. This is a conditional breakout plan, not a market order. Enter only inside the breakout entry range and skip the trade if price opens or runs above the maximum entry.`;
  }
  if (kind === "buy" && position.includes("above")) return `${priceLead}. Price is ${position}; wait for a controlled pullback or a new base instead of chasing.`;
  return `${priceLead}. ${naturalActionSentence(row)}${position ? ` Price is ${position}.` : ""}`;
}

function predictionNarrative(row) {
  const upside = Number(payloadValue(row, "prediction_upside_probability"));
  const downside = Number(payloadValue(row, "prediction_downside_probability"));
  const noEdge = Number(payloadValue(row, "prediction_no_edge_probability"));
  const confidence = Number(payloadValue(row, "prediction_confidence"));
  const horizon = Number(payloadValue(row, "prediction_horizon_sessions")) || 5;
  const state = String(payloadValue(row, "prediction_state") || "").toUpperCase();
  const modelVersion = String(payloadValue(row, "prediction_model_version") || "").toLowerCase();
  if (![upside, downside, noEdge].every(Number.isFinite)) {
    return `The ${horizon}-session model is still collecting comparable, settled outcomes; it is not changing the recommendation.`;
  }
  const certainty = confidence >= 0.65 ? "moderate" : confidence >= 0.40 ? "limited" : "low";
  if (modelVersion.startsWith("ohlcv-ridge")) {
    return `Using price-and-volume history, the next ${horizon} sessions are estimated at ${fmtNumber(upside * 100, 0)}% for a meaningful rise, ${fmtNumber(downside * 100, 0)}% for a meaningful decline, and ${fmtNumber(noEdge * 100, 0)}% for no decisive move. Confidence is ${certainty}.`;
  }
  const message = `Among comparable filled ${horizon}-session trade plans, the model estimates ${fmtNumber(upside * 100, 0)}% target reached, ${fmtNumber(downside * 100, 0)}% stop reached, and ${fmtNumber(noEdge * 100, 0)}% unresolved. Confidence is ${certainty}.`;
  return state === "CALIBRATED" ? message : `${message} Validation is incomplete, so this estimate does not change today's decision.`;
}

function recentBehaviorSummary(row, previous) {
  const close = numericValue(row, "close");
  const move = numericValue(row, "day_change_pct");
  const moveText = Number.isFinite(move) ? `${move >= 0 ? "up" : "down"} ${fmtNumber(Math.abs(move), 1)}%` : "little changed";
  return `Closed at ${fmtNumber(close, 2)}, ${moveText} on the day. ${naturalActionSentence(row)}`;
}

function behaviorDetail(row) {
  const kind = actionKind(row.action);
  const pattern = setupLabel(row.setup);
  const score = convictionScore(row);
  const move = numericValue(row, "day_change_pct");
  const tape = row.psychology || "Mixed tape";
  const mode = row.adaptive_mode || "Mixed mode";
  const note = String(row.notes || "").trim();
  const antiPlan = String(payloadValue(row, "anti_signal_plan") || "").trim();
  const antiLevel = String(payloadValue(row, "anti_signal_level") || "NONE").toUpperCase();
  const contextualPlan = String(payloadValue(row, "contextual_plan") || "").trim();
  const nextDayPlan = String(payloadValue(row, "next_day_plan") || "").trim();
  const operatorStatePlan = String(payloadValue(row, "operator_state_plan") || "").trim();
  const operatorPlan = String(payloadValue(row, "operator_plan") || "").trim();
  const freshnessPlan = String(payloadValue(row, "freshness_plan") || "").trim();
  const feedbackPlan = String(payloadValue(row, "feedback_plan") || "").trim();
  const operatorPressure = String(payloadValue(row, "operator_state") || payloadValue(row, "operator_pressure") || "").toUpperCase();
  const transition = transitionLabel(row);
  const distanceFromZone = payloadNumeric(row, "distance_from_ref_zone_pct");
  const marketContext = payloadValue(row, "market_context");
  const daysToReport = payloadValue(row, "days_to_report");

  if (contextualPlan) return contextualPlan;
  if (antiLevel === "BLOCK" || antiLevel === "CAUTION") return antiPlan || "Anti-signal penalty active; downgrade execution.";
  if (payloadValue(row, "extension_state") === "EXTENDED") {
    const distance = distanceFromZone ? `${fmtNumber(distanceFromZone, 1)}% above ` : "above ";
    return `Extended: price is ${distance}the reference zone; wait for a cleaner base or pullback.`;
  }
  if (["YES", "true", true].includes(payloadValue(row, "event_risk"))) {
    return `Event risk: next report is ${daysToReport || "soon"} day(s) away; use extra caution.`;
  }
  if (payloadValue(row, "freshness_block") === "YES") return freshnessPlan || "Execution blocked: data is stale.";
  if (marketContext === "LAGGING" && ["buy", "setup", "continue"].includes(kind)) {
    return `${pattern} behavior is forming, but it is lagging SPY/QQQ over the last 20 sessions.`;
  }
  if (transition === "Stale Buy") return "Stale BUY: signal has not made enough price progress yet.";
  if (payloadValue(row, "feedback_quality") === "FAILED") return feedbackPlan;
  if (payloadValue(row, "feedback_quality") === "STALE") return feedbackPlan;
  if (nextDayPlan) return nextDayPlan;
  if (operatorStatePlan && operatorPressure !== "NEUTRAL") return operatorStatePlan;
  if (operatorPlan && operatorPressure !== "NEUTRAL") return operatorPlan;
  if (note) return note;
  if (kind === "buy") return `${pattern} behavior with strong trend quality and ${tape.toLowerCase()} tape.`;
  if (kind === "continue") return `Trending: leadership behavior remains constructive, but fresh entry quality may be extended.`;
  if (kind === "setup") return `${pattern} is forming; trend quality is constructive but still developing.`;
  if (kind === "watch") return `${mode} behavior; monitor for quality expansion or a cleaner reference zone.`;
  if (kind === "exit") return `Exit pressure: weak trend quality with ${move < 0 ? "negative" : "unstable"} price action.`;
  if (score < 25) return "Weak scanner behavior; avoid until trend quality and tape improve.";
  return `${mode} behavior with no clear edge yet.`;
}

function payloadValue(row, key) {
  return row?.payload?.[key] ?? row?.[key];
}

function learningReadout(row) {
  const samples = Number(payloadValue(row, "learning_sample_count"));
  const adjustment = Number(payloadValue(row, "learning_adjustment"));
  const action = String(row?.action || "").toUpperCase();
  const defensiveAction = action === "WAIT" || action === "WAIT / AVOID" || action === "EXIT PRESSURE";
  const distinctTickers = Number(payloadValue(row, "learning_distinct_ticker_count"));
  const evaluationDates = Number(payloadValue(row, "learning_evaluation_date_count"));
  const promotionEligible = learningBoolean(payloadValue(row, "learning_promotion_eligible"));
  const reportingOnly = learningBoolean(payloadValue(row, "learning_reporting_only"));
  const promotionState = String(payloadValue(row, "learning_promotion_state") || "").trim().toUpperCase();
  const modelVersion = payloadValue(row, "learning_model_version") || payloadValue(row, "entry_model_version") || payloadValue(row, "model_version");

  if (!Number.isFinite(samples) || samples <= 0) {
    return "Not enough settled comparable signals yet. Learning is not changing today's decision.";
  }

  const coverage = `${fmtNumber(samples, 0)} comparable settled signals${Number.isFinite(distinctTickers) ? ` from ${fmtNumber(distinctTickers, 0)} stocks` : ""}${Number.isFinite(evaluationDates) ? ` over ${fmtNumber(evaluationDates, 0)} market dates` : ""}`;
  if (defensiveAction) {
    return `Reviewed ${coverage}. This evidence supports risk control only; it cannot upgrade the stock to a buy.`;
  }

  const eligible = Boolean(modelVersion)
    && promotionEligible === true
    && reportingOnly !== true
    && promotionState !== "REPORTING_ONLY";
  if (!eligible) return `Reviewed ${coverage}. Validation is incomplete, so learning did not improve today's recommendation.`;
  const adjustmentText = Number.isFinite(adjustment) && Math.abs(adjustment) >= 0.05
    ? ` It adjusted confidence by ${fmtSignedNumber(adjustment, 1)} points.`
    : " It did not materially change confidence.";
  return `Reviewed ${coverage}.${adjustmentText}`;
}

function fillabilityReadout(row) {
  const samples = Number(payloadValue(row, "execution_fill_sample_count"));
  const probability = Number(payloadValue(row, "execution_fill_probability"));
  const state = String(payloadValue(row, "execution_fill_state") || "INSUFFICIENT").toUpperCase();
  const style = String(payloadValue(row, "execution_style") || "entry plan").toLowerCase();
  if (!Number.isFinite(samples) || samples <= 0 || !Number.isFinite(probability)) {
    return "Comparable entry plans have not produced enough fill evidence, so this cannot be presented as an executable buy.";
  }
  const summary = `${fmtNumber(probability * 100, 0)}% estimated chance that the ${style} trades within five sessions, based on ${fmtNumber(samples, 0)} comparable plans.`;
  return state === "VALIDATED" ? summary : `${summary} Evidence is still insufficient for a BUY.`;
}

function learningBoolean(value) {
  if (value === true || String(value).toLowerCase() === "true") return true;
  if (value === false || String(value).toLowerCase() === "false") return false;
  return null;
}

function cacheKeyFor(path, prefix = JSON_CACHE_PREFIX) {
  return `${prefix}${path}`;
}

function readJsonCache(path, prefix = JSON_CACHE_PREFIX, ttl = SUPABASE_CACHE_TTL_MS) {
  if (ttl <= 0) return null;
  try {
    const cached = sessionStorage.getItem(cacheKeyFor(path, prefix));
    if (!cached) return null;
    const payload = JSON.parse(cached);
    if (!payload?.createdAt || Date.now() - payload.createdAt > ttl) return null;
    return payload.value;
  } catch {
    return null;
  }
}

function writeJsonCache(path, value, prefix = JSON_CACHE_PREFIX) {
  try {
    sessionStorage.setItem(cacheKeyFor(path, prefix), JSON.stringify({ createdAt: Date.now(), value }));
  } catch {
    // Private browsing or storage pressure should not block the app.
  }
}

function cacheBustedPath(path) {
  const separator = path.includes("?") ? "&" : "?";
  return `${path}${separator}fresh=${Date.now()}`;
}

async function appApiFetch(path, options = {}) {
  const settings = typeof options === "number" ? { ttl: options } : options;
  const ttl = settings.ttl ?? SUPABASE_CACHE_TTL_MS;
  const fresh = Boolean(settings.fresh);
  const cached = fresh ? null : readJsonCache(path, API_CACHE_PREFIX, ttl);
  if (cached) return cached;
  const response = await fetch(fresh ? cacheBustedPath(path) : path, {
    cache: fresh ? "no-store" : "default",
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.error || `API returned HTTP ${response.status}.`);
  }
  const value = await response.json();
  if (ttl > 0 && !fresh) writeJsonCache(path, value, API_CACHE_PREFIX);
  return value;
}

function loadFocusTickers() {
  try {
    const parsed = JSON.parse(localStorage.getItem(FOCUS_LIST_KEY) || "[]");
    return Array.isArray(parsed) ? parsed.map(normaliseTicker).filter(Boolean) : [];
  } catch {
    return [];
  }
}

function saveFocusTickers() {
  try {
    localStorage.setItem(FOCUS_LIST_KEY, JSON.stringify(state.focusTickers));
  } catch {
    // Focus List is a convenience feature; the app remains usable without storage.
  }
}

function loadFocusPin() {
  try {
    return localStorage.getItem(FOCUS_PIN_KEY) || "";
  } catch {
    return "";
  }
}

function saveFocusPin(pin) {
  state.focusPin = String(pin || "").trim();
  try {
    if (state.focusPin) localStorage.setItem(FOCUS_PIN_KEY, state.focusPin);
    else localStorage.removeItem(FOCUS_PIN_KEY);
  } catch {
    // PIN storage is optional; the user can re-enter it when needed.
  }
}

function isFocusTicker(ticker) {
  return state.focusTickers.includes(normaliseTicker(ticker));
}

async function focusApiFetch(method = "GET", tickers = null) {
  const options = {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-Focus-Pin": state.focusPin,
    },
  };
  if (tickers) options.body = JSON.stringify({ tickers });
  const response = await fetch("/api/focus-list", options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error || "Focus List unavailable.");
  return Array.isArray(payload.tickers) ? payload.tickers.map(normaliseTicker).filter(Boolean) : [];
}

async function loadCloudFocusTickers() {
  if (!state.focusPin || isGithubPagesHost()) return false;
  try {
    state.focusSyncing = true;
    state.focusTickers = await focusApiFetch("GET");
    saveFocusTickers();
    state.focusMessage = "Focus List synced.";
    return true;
  } catch (error) {
    state.focusMessage = error.message || "Focus List unavailable.";
    return false;
  } finally {
    state.focusSyncing = false;
  }
}

async function saveCloudFocusTickers() {
  if (!state.focusPin || isGithubPagesHost()) return false;
  try {
    state.focusSyncing = true;
    state.focusTickers = await focusApiFetch("PUT", state.focusTickers);
    saveFocusTickers();
    state.focusMessage = "Focus List saved.";
    return true;
  } catch (error) {
    state.focusMessage = error.message || "Focus List unavailable.";
    return false;
  } finally {
    state.focusSyncing = false;
  }
}

async function ensureFocusPin() {
  if (isGithubPagesHost()) return true;
  if (state.focusPin) return true;
  const pin = window.prompt("Enter your Focus List PIN");
  if (!pin) {
    state.focusMessage = "Enter the PIN to sync your Focus List.";
    renderFocusList();
    attachFocusControls();
    return false;
  }
  saveFocusPin(pin);
  const unlocked = await loadCloudFocusTickers();
  if (!unlocked) saveFocusPin("");
  renderWatchlist();
  return unlocked;
}

async function toggleFocusTicker(ticker) {
  if (!await ensureFocusPin()) return;
  const normalised = normaliseTicker(ticker);
  state.focusTickers = isFocusTicker(normalised)
    ? state.focusTickers.filter((value) => value !== normalised)
    : [...state.focusTickers, normalised].sort();
  saveFocusTickers();
  renderWatchlist();
  if (!isGithubPagesHost()) await saveCloudFocusTickers();
  renderWatchlist();
}

function dataDateSummary(rows) {
  const dates = [...new Set(rows.map((row) => row.data_date || row.date || row.history_date).filter(Boolean))].sort();
  if (!dates.length) return "";
  const latest = dates.at(-1);
  const earliest = dates[0];
  return earliest === latest ? `Market data: ${latest}` : `Market data: ${earliest} to ${latest}`;
}

function historyDateSummary(rows) {
  const dates = [...new Set(rows.map((row) => row.history_date || row.date).filter(Boolean))].sort();
  if (!dates.length) return "";
  return `History: ${dates[0]} to ${dates.at(-1)}`;
}

function rowByTicker(rows) {
  return new Map(rows.map((row) => [row.ticker, row]));
}

function previousRowFor(row) {
  return state.previousByTicker.get(row.ticker) || null;
}

function transitionRank(row) {
  const rank = { avoid: 0, exit: 1, watch: 2, setup: 3, continue: 4, buy: 5 };
  return rank[actionKind(row.action)] ?? 0;
}

function transitionLabel(row, previous = previousRowFor(row)) {
  const structured = payloadValue(row, "transition_label");
  if (structured) return structured;
  if (!previous) return "New Today";
  if (row.action === previous.action && row.setup === previous.setup) return "Repeated";
  if (transitionRank(row) > transitionRank(previous) || convictionScore(row) - convictionScore(previous) >= 8) return "Upgraded";
  if (transitionRank(row) < transitionRank(previous) || convictionScore(row) - convictionScore(previous) <= -8) return "Downgraded";
  return "Changed";
}

function displayTransitionLabel(label) {
  if (label === "Fresh Setup To Buy") return "Fresh Building To Buy";
  return label;
}

function transitionTone(label) {
  if (label === "Upgraded" || label === "New Today" || label === "Fresh Setup To Buy") return "up";
  if (label === "Downgraded" || label === "Stale Buy" || label === "Needs Gate Proof" || label === "Needs Execution Proof") return "down";
  if (label === "Extended" || label === "Changed") return "setup";
  return "quiet";
}

function referenceZoneMove(row, previous) {
  const currentZone = numericValue(row, "entry_est");
  const previousZone = numericValue(previous, "entry_est");
  if (!currentZone || !previousZone) return "";
  const delta = currentZone - previousZone;
  if (Math.abs(delta) < 0.01) return "";
  return delta > 0 ? "Reference zone moved higher" : "Reference zone moved closer";
}

function whyThisMatters(row, previous = previousRowFor(row)) {
  const structuredReasons = reasonCodes(row).map((code) => REASON_LABELS[code] || code.replaceAll("_", " "));
  const distanceFromZone = payloadNumeric(row, "distance_from_ref_zone_pct");
  if (payloadValue(row, "extension_state") === "EXTENDED" && distanceFromZone) {
    structuredReasons.unshift(`${fmtNumber(distanceFromZone, 1)}% above zone`);
  }
  if (structuredReasons.length) return [...new Set(structuredReasons)].slice(0, 3);

  const reasons = [];
  const kind = actionKind(row.action);
  const buyer = Number(payloadValue(row, "buyer_score"));
  const seller = Number(payloadValue(row, "seller_score"));
  const scoreMove = previous ? convictionScore(row) - convictionScore(previous) : 0;
  if (!previous) reasons.push("New scan entry");
  if (previous && row.action !== previous.action) reasons.push(`Signal ${ACTION_LABELS[previous.action] || previous.action} to ${ACTION_LABELS[row.action] || row.action}`);
  if (previous && row.setup !== previous.setup) reasons.push(`Pattern changed to ${setupLabel(row.setup)}`);
  if (previous && Math.abs(scoreMove) >= 6) reasons.push(`Trend quality ${scoreMove > 0 ? "improved" : "weakened"}`);
  if (Number.isFinite(buyer) && Number.isFinite(seller) && buyer >= seller + 12) reasons.push("Buyer tape confirmed");
  if (Number.isFinite(buyer) && Number.isFinite(seller) && seller >= buyer + 12) reasons.push("Seller pressure increased");
  const zoneMove = previous ? referenceZoneMove(row, previous) : "";
  if (zoneMove) reasons.push(zoneMove);
  if (kind === "buy" && numericValue(row, "day_change_pct") > 0) reasons.push("Price acting with signal");
  if (kind === "exit") reasons.push("Risk pressure elevated");
  return reasons.slice(0, 3);
}

function transitionBadge(row, previous = previousRowFor(row)) {
  const label = transitionLabel(row, previous);
  return `<span class="change-chip ${transitionTone(label)}">${escapeHtml(displayTransitionLabel(label))}</span>`;
}

function dailyChangeItems(rows, previousRows, limit = 8) {
  if (!rows.length || !previousRows.length) return [];
  const previousByTicker = rowByTicker(previousRows);
  return rows
    .map((row) => {
      const previous = previousByTicker.get(row.ticker);
      if (!previous) return null;
      const scoreMove = convictionScore(row) - convictionScore(previous);
      const actionChanged = row.action !== previous.action;
      const setupChanged = row.setup !== previous.setup;
      const transition = transitionLabel(row, previous);
      const transitionScore = payloadNumeric(row, "transition_score");
      const priceMove = numericValue(row, "close") - numericValue(previous, "close");
      const previousClose = numericValue(previous, "close");
      const pricePct = previousClose ? (priceMove / previousClose) * 100 : 0;
      const priority =
        (actionChanged ? 40 : 0) +
        (setupChanged ? 20 : 0) +
        Math.min(Math.abs(transitionScore), 35) +
        Math.min(Math.abs(scoreMove), 30) +
        Math.min(Math.abs(pricePct), 10);
      if (transition === "Repeated Signal" && !actionChanged && !setupChanged && Math.abs(scoreMove) < 6 && Math.abs(pricePct) < 3) return null;
      return { row, previous, scoreMove, pricePct, actionChanged, setupChanged, priority, transition };
    })
    .filter(Boolean)
    .sort((a, b) => b.priority - a.priority)
    .slice(0, limit);
}

function currentDayMoverItems(rows) {
  return rows
    .map((row) => ({
      row,
      previous: null,
      scoreMove: convictionScore(row),
      pricePct: numericValue(row, "day_change_pct"),
      actionChanged: false,
      setupChanged: false,
      currentDayOnly: true,
      priority: Math.abs(numericValue(row, "day_change_pct")) + convictionScore(row) / 20
    }))
    .filter((item) => Number.isFinite(item.pricePct) && Math.abs(item.pricePct) >= 3)
    .sort((a, b) => b.priority - a.priority)
    .slice(0, 8);
}

function renderScoreBreakdown(row) {
  const buyer = Number(payloadValue(row, "buyer_score"));
  const seller = Number(payloadValue(row, "seller_score"));
  const volume = String(payloadValue(row, "volume_state") || "NEUTRAL").toUpperCase();
  const market = String(payloadValue(row, "market_context") || "UNKNOWN").toUpperCase();
  const nextDayBias = String(payloadValue(row, "next_day_bias") || "NEUTRAL").toUpperCase();
  const tape = Number.isFinite(buyer) && Number.isFinite(seller)
    ? buyer >= seller + 12
      ? `Buyers controlled the latest candle${volume === "DEMAND" ? " with supportive volume" : ""}.`
      : seller >= buyer + 12
        ? `Sellers controlled the latest candle${volume === "SUPPLY" ? " with elevated supply" : ""}.`
        : "The latest candle shows balanced buying and selling pressure."
    : "The latest candle does not show a decisive buyer or seller advantage.";
  const relativeTrend = market === "LEADING"
    ? "The stock is outperforming its market benchmarks over the recent comparison window."
    : market === "LAGGING"
      ? "The stock is lagging SPY/QQQ over the recent comparison window."
      : "Relative performance versus the market is mixed.";
  const items = [
    ["Price and trend", `${tape} ${relativeTrend}`],
    ["Similar past setups", similarCasesNarrative(row)],
    ["Main risk", mainRiskNarrative(row, { nextDayBias, seller, buyer })]
  ];
  return `
    <div class="score-explainer">
      <div class="score-factors">
        ${items.map(([label, value]) => `
          <div>
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(value)}</strong>
          </div>
        `).join("")}
      </div>
    </div>
  `;
}

function similarCasesNarrative(row) {
  const sentences = [];
  const volatility = String(payloadValue(row, "volatility_regime") || "NORMAL").toUpperCase();
  const fillSamples = Number(payloadValue(row, "execution_fill_sample_count"));
  const fillProbability = Number(payloadValue(row, "execution_fill_probability"));
  const upside = Number(payloadValue(row, "prediction_upside_probability"));
  const downside = Number(payloadValue(row, "prediction_downside_probability"));
  const noEdge = Number(payloadValue(row, "prediction_no_edge_probability"));
  const predictionState = String(payloadValue(row, "prediction_state") || "").toUpperCase();
  const adjustment = Number(payloadValue(row, "learning_adjustment"));
  const learningEligible = learningBoolean(payloadValue(row, "learning_promotion_eligible")) === true
    && learningBoolean(payloadValue(row, "learning_reporting_only")) !== true;

  if (volatility.includes("HIGH") || volatility.includes("EXPANSION")) {
    sentences.push("This stock has recently made larger-than-usual moves, so position size matters more.");
  } else if (volatility.includes("LOW") || volatility.includes("COMPRESSED")) {
    sentences.push("This stock has recently moved in a tighter range than usual.");
  }
  if (Number.isFinite(fillSamples) && fillSamples > 0 && Number.isFinite(fillProbability)) {
    sentences.push(`In ${fmtNumber(fillSamples, 0)} similar plans, price reached the planned entry about ${fmtNumber(fillProbability * 100, 0)}% of the time.`);
  } else {
    sentences.push("There are not enough completed similar entries to rely on a historical fill rate.");
  }
  if (predictionState === "CALIBRATED" && [upside, downside, noEdge].every(Number.isFinite)) {
    const likely = upside >= downside && upside >= noEdge
      ? "an upward move"
      : downside >= noEdge
        ? "a downward move"
        : "no decisive move";
    sentences.push(`Comparable five-session paths most often pointed to ${likely}.`);
  }
  if (learningEligible && Number.isFinite(adjustment) && Math.abs(adjustment) >= 0.5) {
    sentences.push(`Past outcomes ${adjustment > 0 ? "raised" : "lowered"} confidence in today's view.`);
  }
  return sentences.slice(0, 3).join(" ");
}

function mainRiskNarrative(row, context = {}) {
  const kind = actionKind(row.action);
  const seller = Number.isFinite(context.seller) ? context.seller : Number(payloadValue(row, "seller_score"));
  const buyer = Number.isFinite(context.buyer) ? context.buyer : Number(payloadValue(row, "buyer_score"));
  const nextDayBias = String(context.nextDayBias || payloadValue(row, "next_day_bias") || "").toUpperCase();
  if (payloadValue(row, "freshness_block") === "YES") return "Price data is not current, so no action is suggested.";
  if (["YES", "true", true].includes(payloadValue(row, "event_risk"))) return "A company report is close, so a gap could invalidate the price plan.";
  if (payloadValue(row, "extension_state") === "EXTENDED") return "Price is above the preferred entry area; chasing it would increase downside risk.";
  if (kind === "exit") return "Selling pressure is damaging the trend; capital protection matters more than a new entry.";
  if (Number.isFinite(seller) && Number.isFinite(buyer) && seller >= buyer + 12) return "Sellers currently have the advantage, so wait for demand to return.";
  if (!executionChecksClear(row)) return validationSummary(row);
  if (nextDayBias.includes("BEARISH")) return "The latest price pattern points to near-term downside risk.";
  const stop = numericValue(row, "stop_est");
  if (stop && ["buy", "continue"].includes(kind)) return `The constructive view is invalid if price closes below ${fmtNumber(stop, 2)}.`;
  return "No single risk dominates, but the setup still depends on price and volume holding together.";
}

function renderHistoryChangeChips(row, previous) {
  if (!previous) return `<span class="change-chip quiet">First recorded day</span>`;
  const chips = [];
  if (row.action !== previous.action) {
    chips.push(`<span class="change-chip signal">Signal changed from ${escapeHtml(ACTION_LABELS[previous.action] || previous.action)} to ${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>`);
  }
  if (row.setup !== previous.setup) {
    const previousSetup = setupLabel(previous.setup);
    const currentSetup = setupLabel(row.setup);
    chips.push(`<span class="change-chip setup">Pattern changed from ${escapeHtml(previousSetup === "None" ? "no clear setup" : previousSetup)} to ${escapeHtml(currentSetup === "None" ? "no clear setup" : currentSetup)}</span>`);
  }
  const scoreMove = convictionScore(row) - convictionScore(previous);
  if (Math.abs(scoreMove) >= 8) {
    chips.push(`<span class="change-chip ${moveClass(scoreMove)}">Confidence ${scoreMove > 0 ? "improved" : "weakened"} ${Math.abs(scoreMove) >= 20 ? "sharply" : "modestly"}</span>`);
  }
  return chips.join(" ") || `<span class="change-chip quiet">No meaningful change</span>`;
}

function setStatus(message, ok = true) {
  const status = document.querySelector("#status");
  const runStatus = document.querySelector("#run-status");
  if (status) status.textContent = message;
  if (runStatus) {
    runStatus.classList.toggle("bad", !ok);
    runStatus.classList.toggle("loading", ok && String(message).toLowerCase().includes("loading"));
  }
}

function runHealthSummary(runInfo) {
  if (!runInfo) return "";
  const parts = [];
  const failed = Number(runInfo.symbols_failed || 0);
  const stale = Number(runInfo.symbols_stale_cache || 0);
  if (runInfo.live_access_ok === false) parts.push("live source unavailable");
  if (stale) parts.push(`${stale} stocks use recent cached data`);
  if (failed) parts.push(`${failed} stocks unavailable`);
  return parts.length ? ` · ${parts.join(" · ")}` : "";
}

function renderRunHealthPanel(runInfo, rows = []) {
  const panel = document.querySelector("#run-health-panel");
  if (!panel) return;
  panel.innerHTML = "";
  panel.hidden = true;
}

function renderMarketRail(runInfo, rows = []) {
  const rail = document.querySelector("#market-rail");
  const heroBrief = document.querySelector("#hero-brief");
  if (!rail && !heroBrief) return;
  const health = runHealthStatus(runInfo, rows);
  const analyzed = Number(runInfo?.symbols_analyzed || rows.length || 0);
  const total = Number(runInfo?.symbols_total || rows.length || 0);
  const coverage = total ? `${analyzed}/${total} analysed` : `${analyzed} analysed`;
  const dataDate = runInfo?.latest_data_date || dataDateSummary(rows).replace(/^Market data:\s*/, "") || "Unavailable";
  if (rail) rail.innerHTML = `
    <span class="rail-brand">Daily Trade <b>Copilot</b></span>
    <span>US close <strong>${escapeHtml(dataDate)}</strong></span>
    <span>Coverage <strong>${escapeHtml(coverage)}</strong></span>
    <span class="rail-health tone-${health.tone}">${escapeHtml(health.label)}</span>
  `;
  if (heroBrief) heroBrief.innerHTML = `
    <div><span class="eyebrow">Scanner status</span><p>${escapeHtml(health.detail || "No current data summary available.")}</p></div>
    <dl>
      <div><dt>Coverage</dt><dd>${escapeHtml(coverage)}</dd></div>
      <div><dt>US close</dt><dd>${escapeHtml(dataDate)}</dd></div>
      <div><dt>Status</dt><dd class="tone-${health.tone}">${escapeHtml(health.label)}</dd></div>
    </dl>
  `;
}

function runHealthStatus(runInfo, rows = []) {
  const failed = Number(runInfo?.symbols_failed || 0);
  const stale = Number(runInfo?.symbols_stale_cache || 0);
  const latestRows = new Map();
  rows.forEach((row) => {
    const ticker = String(row.ticker || "_");
    const date = String(row.history_date || row.data_date || row.date || "");
    const previous = latestRows.get(ticker);
    if (!previous || date > previous.date) latestRows.set(ticker, { date, row });
  });
  const rowStaleBlocks = [...latestRows.values()]
    .filter(({ row }) => payloadValue(row, "freshness_block") === "YES").length;
  const staleBlocks = Number(runInfo?.payload?.stale_execution_blocks ?? rowStaleBlocks);
  const analyzed = Number(runInfo?.symbols_analyzed || rows.length || 0);
  const total = Number(runInfo?.symbols_total || rows.length || 0);
  const liveOk = runInfo?.live_access_ok;
  const latestData = runInfo?.latest_data_date || dataDateSummary(rows).replace(/^Market data:\s*/, "") || "unknown";
  const hasRows = rows.length > 0 || analyzed > 0;
  const hasIssue = liveOk === false || failed > 0 || stale > 0 || staleBlocks > 0;
  const tone = !hasRows || staleBlocks > 0 ? "bad" : hasIssue ? "warn" : "ok";
  const label = tone === "bad"
    ? "Data not safe to use"
    : failed > 0
      ? "Partial coverage"
      : stale > 0 || liveOk === false
        ? "Some data may lag"
        : "Data current";
  const caveats = [
    staleBlocks ? `${staleBlocks} stale-data blocks` : "",
    stale ? `${stale} stocks use recent cached data` : "",
    failed ? `${failed} stocks unavailable` : "",
    liveOk === false ? "live data source unavailable" : "",
  ].filter(Boolean);
  const detail = [
    `${analyzed || total || rows.length} analyzed`,
    latestData && latestData !== "unknown" ? `market data ${latestData}` : "",
    caveats.length ? caveats.join(", ") : "",
  ].filter(Boolean).join(" · ");
  return { tone, label, detail };
}

function renderTrafficHealth(runInfo, rows = []) {
  const health = runHealthStatus(runInfo, rows);
  return `
    <div class="traffic-health tone-${health.tone}">
      <span class="traffic-lights" aria-label="${escapeHtml(health.label)}">
        <i class="traffic-red ${health.tone === "bad" ? "active" : ""}" aria-hidden="true"></i>
        <i class="traffic-yellow ${health.tone === "warn" ? "active" : ""}" aria-hidden="true"></i>
        <i class="traffic-green ${health.tone === "ok" ? "active" : ""}" aria-hidden="true"></i>
      </span>
      <span><b>${escapeHtml(health.label)}</b>${health.detail ? ` · ${escapeHtml(health.detail)}` : ""}</span>
    </div>
  `;
}

function setRefreshSummary(latest, marketData, rows, runInfo = null) {
  const status = document.querySelector("#status");
  const disclaimer = document.querySelector("#app-disclaimer");
  const runStatus = document.querySelector("#run-status");
  if (runStatus) {
    const stalePrefix = runHealthStatus(runInfo, rows).tone === "ok" ? "" : "Some data may lag · ";
    runStatus.textContent = `${stalePrefix}Updated ${latest} · ${marketData}${runHealthSummary(runInfo)}`;
    runStatus.classList.toggle("warn", Boolean(
      runInfo && (
        runInfo.live_access_ok === false
        || Number(runInfo.symbols_failed || 0)
        || Number(runInfo.symbols_stale_cache || 0)
        || Number(runInfo.payload?.stale_execution_blocks || 0)
      )
    ));
    runStatus.classList.toggle("bad", Boolean(runInfo && Number(runInfo.payload?.stale_execution_blocks || 0)));
    runStatus.classList.remove("loading");
  }
  if (status) status.textContent = "";
  if (disclaimer) disclaimer.textContent = APP_DISCLAIMER;
  if (runStatus && !(runInfo && Number(runInfo.payload?.stale_execution_blocks || 0))) runStatus.classList.remove("bad");
  renderRunHealthPanel(runInfo, rows);
  renderMarketRail(runInfo, rows);
}

async function fetchStaticJson(path, { mutable = false, errorPrefix = "Published data" } = {}) {
  const response = await fetch(path, { cache: mutable ? "no-cache" : "force-cache" });
  if (!response.ok) throw new Error(`${errorPrefix} returned HTTP ${response.status}.`);
  return response.json();
}

function isGithubPagesHost() {
  return window.location.hostname.endsWith(".github.io") || LOCAL_STATIC_DATA_MODE;
}

function publishedManifestUrl() {
  return isGithubPagesHost() ? new URL("./data/manifest.json", window.location.href).href : `${PUBLISHED_DATA_BASE_URL}manifest.json`;
}

function resolvePublishedPath(path, manifestUrl) {
  if (!path || path.startsWith("/") || path.includes("..") || path.includes("//") || !/^[A-Za-z0-9_./-]+\.json$/.test(path)) {
    throw new Error("Published manifest contains an invalid data path.");
  }
  const resolved = new URL(path, manifestUrl);
  if (resolved.origin !== new URL(manifestUrl).origin) throw new Error("Published data must remain on the manifest origin.");
  return resolved.href;
}

async function loadStaticManifest() {
  const manifestUrl = publishedManifestUrl();
  const manifest = await fetchStaticJson(manifestUrl, { mutable: true, errorPrefix: "Published manifest" });
  if (!manifest?.publication_id || !manifest?.run_date || !manifest?.latest_path || !manifest?.ticker_base_path) {
    throw new Error("Published manifest is incomplete.");
  }
  const latestVersion = String(manifest.latest_path).match(/^runs\/([^/]+)\/latest\.json$/)?.[1];
  const tickerVersion = String(manifest.ticker_base_path).match(/^runs\/([^/]+)\/tickers$/)?.[1];
  if (!latestVersion || latestVersion !== tickerVersion || typeof manifest.ticker_paths !== "object") {
    throw new Error("Published manifest paths are not scoped to one publication.");
  }
  state.staticManifest = { ...manifest, manifestUrl };
  return state.staticManifest;
}

function validatePublishedPayload(payload, manifest) {
  if (payload?.publication_id !== manifest.publication_id || payload?.run_date !== manifest.run_date) {
    throw new Error("Published data version does not match its manifest.");
  }
  return payload;
}

async function loadStaticLatestRows() {
  const manifest = state.staticManifest || await loadStaticManifest();
  const payload = validatePublishedPayload(
    await fetchStaticJson(resolvePublishedPath(manifest.latest_path, manifest.manifestUrl)),
    manifest
  );
  return {
    latest: payload.run_date,
    previous: "",
    rows: (payload.rows || []).map((row) => ({
      ...row,
      name: displaySecurityName(row.name, row.ticker) || row.name || row.ticker,
    })),
    previousRows: payload.previousRows || [],
    runInfo: payload.runInfo || null,
  };
}

function uniqueHistoryDateCount(rows) {
  return new Set(rows.map((row) => row.history_date || row.data_date || row.date).filter(Boolean)).size;
}

async function loadStaticTickerHistory(ticker) {
  const manifest = state.staticManifest || await loadStaticManifest();
  const safeTicker = normaliseTicker(ticker).replace(/[^A-Z0-9._-]/g, "");
  const tickerPath = String(manifest.ticker_paths?.[safeTicker] || "");
  if (!tickerPath.startsWith(`${manifest.ticker_base_path}/`)) throw new Error("Ticker is not included in the active publication.");
  const payload = validatePublishedPayload(
    await fetchStaticJson(resolvePublishedPath(tickerPath, manifest.manifestUrl)),
    manifest
  );
  if (normaliseTicker(payload.ticker) !== safeTicker) throw new Error("Published ticker payload does not match the requested ticker.");
  const rows = (payload.historyRows || payload.rows || [])
    .map((row) => ({
      ...row,
      history_date: row.data_date || row.date || row.run_date,
      data_date: row.data_date || row.date,
      name: displaySecurityName(row.name, row.ticker) || row.name || row.ticker,
    }))
    .sort((a, b) => String(b.history_date).localeCompare(String(a.history_date)));
  if (payload.snapshot && rows[0]) {
    rows[0] = {
      ...rows[0],
      ...payload.snapshot,
      history_date: rows[0].history_date,
      data_date: payload.snapshot.data_date || payload.snapshot.date || rows[0].data_date,
      name: payload.snapshot.name || rows[0].name,
    };
  }
  if (uniqueHistoryDateCount(rows) < 5) {
    throw new Error("Published data does not have enough history for this ticker.");
  }
  return {
    ticker: safeTicker,
    latest: payload.run_date,
    name: payload.snapshot?.name || rows[0]?.name || "",
    rows,
    snapshot: payload.snapshot || rows[0] || null,
    historyRows: rows,
    runInfo: payload.runInfo || null,
    profile: payload.profile || {},
  };
}

function renderWatchlistCell(row, key) {
  if (key === "ticker") {
    return `
      <span class="ticker-cell ticker-cell-rich">
        <button class="focus-toggle ${isFocusTicker(row.ticker) ? "active" : ""}" type="button" data-focus-ticker="${escapeHtml(row.ticker)}" aria-label="${isFocusTicker(row.ticker) ? "Remove" : "Add"} ${escapeHtml(row.ticker)} from Focus List">★</button>
        <span class="ticker-copy">
          <button class="ticker-link ticker-select" type="button" data-select-ticker="${escapeHtml(row.ticker)}" aria-label="Review ${escapeHtml(row.ticker)}">${escapeHtml(row.ticker)}</button>
          <span class="ticker-name">${escapeHtml(displaySecurityName(row.name, row.ticker) || row.name || row.ticker)}</span>
        </span>
      </span>
    `;
  }
  if (key === "name") {
    return escapeHtml(displaySecurityName(row.name, row.ticker) || row.name || row.ticker);
  }
  if (key === "action") {
    return renderDecisionSummary(row);
  }
  if (key === "price_summary") return renderPriceSummary(row);
  if (key === "trade_context") return renderTradeContext(row);
  if (key === "risk_summary") return renderRiskSummary(row);
  if (key === "setup") {
    return `<span class="badge pattern-pill pattern-${setupTone(row.setup)}">${escapeHtml(setupLabel(row.setup))}</span>`;
  }
  if (key === "buy_tier") return renderBuyTier(row);
  if (key === "data_provider") return renderDataProvider(row);
  if (key === "next_day_bias") return renderNextDayBias(row);
  if (key === "operator_state") return renderOperatorPressure(row);
  if (key === "next_day_plan") return `<span class="behavior-detail">${escapeHtml(payloadValue(row, "next_day_plan") || "")}</span>`;
  if (key === "notes") {
    return renderReasonSummary(row);
  }
  if (key === "score") return renderQualityScore(row);
  if (key === "day_change_pct") return renderMovePct(row[key]);
  if (key === "risk_pct_to_stop") {
    if (!executionChecksClear(row) || !["buy", "continue"].includes(actionKind(row.action))) return "-";
    const risk = payloadNumeric(row, "risk_pct_to_stop");
    return risk ? `<span class="risk-value">-${escapeHtml(fmtNumber(Math.abs(risk), 1))}%</span>` : "-";
  }
  if (key === "position_value_1k_risk") return escapeHtml(fmtNumber(payloadValue(row, "position_value_1k_risk"), 0));
  if (key === "entry_est") return escapeHtml(formatEntryZone(row) || "-");
  if (key === "stop_est" && (!executionChecksClear(row) || !["buy", "continue"].includes(actionKind(row.action)))) return "-";
  if (["close", "entry_est", "stop_est", "target_est"].includes(key)) return escapeHtml(fmtNumber(row[key], 2));
  return escapeHtml(row[key]);
}

function formatEntryZone(row) {
  const low = payloadNumeric(row, "entry_zone_low");
  const high = payloadNumeric(row, "entry_zone_high") || numericValue(row, "entry_est");
  if (low && high && low < high) return `${fmtNumber(low, 2)}-${fmtNumber(high, 2)}`;
  return fmtNumber(high || row?.entry_est, 2);
}

function renderDecisionSummary(row) {
  const kind = actionKind(row.action);
  return `
    <span class="decision-stack">
      <span class="badge ${kind}">${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>
    </span>
  `;
}

function renderPriceSummary(row) {
  const zone = formatEntryZone(row);
  const stop = numericValue(row, "stop_est");
  const secondary = [
    zone ? `Zone ${zone}` : "",
    stop ? `Stop ${fmtNumber(stop, 2)}` : ""
  ].filter(Boolean).join(" · ");
  return `
    <span class="price-stack">
      <span><strong>${escapeHtml(fmtNumber(row.close, 2))}</strong> ${renderMovePct(row.day_change_pct)}</span>
      ${secondary ? `<small>${escapeHtml(secondary)}</small>` : ""}
    </span>
  `;
}

function renderTradeContext(row) {
  const position = referenceZonePosition(row);
  const reason = position ? `Price is ${position}.` : decisionHeadline(row);
  const validation = validationSummary(row);
  const details = executionChecksClear(row)
    ? naturalActionSentence(row)
    : `${validation.split(". ")[0].replace(/\.$/, "")}.`;
  return `
    <span class="read-stack">
      <strong>${escapeHtml(reason)}</strong>
      ${details ? `<small>${escapeHtml(details)}</small>` : ""}
    </span>
  `;
}

function riskSummaryLabel(row) {
  const kind = actionKind(row.action);
  const antiLevel = String(payloadValue(row, "anti_signal_level") || "NONE").toUpperCase();
  const operator = String(payloadValue(row, "operator_state") || payloadValue(row, "operator_pressure") || "NEUTRAL").toUpperCase();
  const riskPermission = String(payloadValue(row, "risk_permission") || "").toUpperCase();
  const marketPermission = String(payloadValue(row, "market_permission") || "").toUpperCase();
  const tickerPermission = String(payloadValue(row, "ticker_permission") || "").toUpperCase();
  const walkForwardPermission = String(payloadValue(row, "walk_forward_permission") || "").toUpperCase();
  const personalityAllowed = String(payloadValue(row, "personality_setup_allowed") || "").toUpperCase();
  if (kind === "exit") return ["risk", "PROTECT CAPITAL"];
  if (kind === "avoid") return ["risk", "NO ENTRY"];
  if (row.action === "WAIT") return ["watch", "NO CLEAR EDGE"];
  if (payloadValue(row, "freshness_block") === "YES") return ["risk", "DATA TOO OLD"];
  if (antiLevel === "BLOCK") return ["risk", "DO NOT ENTER"];
  if (antiLevel === "CAUTION") return ["watch", "USE CAUTION"];
  if (payloadValue(row, "extension_state") === "EXTENDED") return ["watch", "DO NOT CHASE"];
  if (riskPermission !== "ALLOW" || marketPermission !== "ALLOW" || tickerPermission !== "ALLOW" || walkForwardPermission !== "ALLOW" || personalityAllowed === "NO") return ["risk", "WAIT"];
  if (operator.includes("BULL_TRAP") || operator.includes("DISTRIBUTION") || operator.includes("SHORT")) return ["risk", shortOperatorPressure(operator)];
  if (operator.includes("ACCUMULATION") || operator.includes("ABSORPTION") || operator.includes("BEAR_TRAP") || operator.includes("SQUEEZE")) return ["constructive", shortOperatorPressure(operator)];
  return ["strong", "CHECKS CLEAR"];
}

function renderRiskSummary(row) {
  const [tone, label] = riskSummaryLabel(row);
  return `
    <span class="risk-stack">
      <span class="badge entry-pill entry-${tone}">${escapeHtml(label)}</span>
    </span>
  `;
}

function renderReasonSummary(row) {
  const detail = behaviorDetail(row);
  const reasons = whyThisMatters(row).slice(0, 2);
  return `
    <span class="reason-stack">
      <span>${escapeHtml(detail)}</span>
      ${reasons.length ? `<small>${reasons.map(escapeHtml).join(" · ")}</small>` : ""}
    </span>
  `;
}

function searchableRowText(row) {
  return [
    ...WATCHLIST_COLUMN_KEYS.map((key) => row[key]),
    ACTION_LABELS[row.action] || row.action,
    setupLabel(row.setup),
    strengthLabel(row),
    entryQualityLabel(row),
    payloadValue(row, "buy_tier"),
    payloadValue(row, "contextual_overlay"),
    payloadValue(row, "contextual_plan"),
    payloadValue(row, "anti_signal_level"),
    payloadValue(row, "anti_signal_plan"),
    payloadValue(row, "last_outcome_label"),
    payloadValue(row, "last_outcome_reason"),
    payloadValue(row, "learning_plan"),
    payloadValue(row, "learning_adjustment"),
    payloadValue(row, "execution_plan"),
    payloadValue(row, "data_provider"),
    payloadValue(row, "data_provider_status"),
    payloadValue(row, "data_provider_error"),
    payloadValue(row, "freshness_status"),
    payloadValue(row, "freshness_plan"),
    payloadValue(row, "feedback_quality"),
    payloadValue(row, "feedback_plan"),
    payloadValue(row, "next_day_bias"),
    payloadValue(row, "next_day_plan"),
    payloadValue(row, "operator_state"),
    payloadValue(row, "operator_state_plan"),
    payloadValue(row, "operator_pressure"),
    payloadValue(row, "operator_plan"),
    payloadValue(row, "signal_quality"),
    payloadValue(row, "market_context"),
    payloadValue(row, "market_permission"),
    payloadValue(row, "ticker_permission"),
    payloadValue(row, "walk_forward_permission"),
    payloadValue(row, "risk_permission"),
    reasonCodes(row).map((code) => REASON_LABELS[code] || code.replaceAll("_", " ")).join(" "),
    whyThisMatters(row).join(" "),
  ].filter(Boolean).join(" ").toLowerCase();
}

function rowMatchesSearch(row, query, exactTickerNeedle = "") {
  if (exactTickerNeedle) return tickerSearchAliases(row).includes(exactTickerNeedle);
  const needle = String(query || "").trim().toLowerCase();
  return !needle || searchableRowText(row).includes(needle);
}

function renderMobileWatchlistSummary(row) {
  const kind = actionKind(row.action);
  const company = displaySecurityName(row.name, row.ticker) || row.name || row.ticker;
  const [riskTone, riskLabel] = riskSummaryLabel(row);
  const isRisk = ["exit", "avoid"].includes(kind);
  const activePlan = executionChecksClear(row) && ["buy", "continue"].includes(kind);
  const execution = isRisk
    ? decisionHeadline(row)
    : activePlan
      ? `${entryPlanLabel(row, { active: true })} ${formatEntryZone(row) || "-"} · Protect below ${fmtNumber(row.stop_est, 2) || "-"}`
      : `${entryPlanLabel(row)} ${formatEntryZone(row) || "unavailable"} · not an active entry`;
  return `
    <span class="mobile-watch-shell">
      <a class="mobile-watch-row" href="./ticker.html?ticker=${encodeURIComponent(row.ticker)}">
        <span class="mobile-watch-main">
          <strong>${escapeHtml(row.ticker)}</strong>
          <span>${escapeHtml(company)}</span>
          <span class="mobile-watch-signal">
            <span class="badge ${kind}">${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>
            <span class="badge entry-pill entry-${riskTone}">${escapeHtml(riskLabel)}</span>
            <span>${escapeHtml(decisionHeadline(row))}</span>
          </span>
          <span class="mobile-execution">${escapeHtml(execution)}</span>
        </span>
        <span class="mobile-watch-price">
          <strong>${escapeHtml(fmtNumber(row.close, 2))}</strong>
          ${renderMovePct(row.day_change_pct)}
        </span>
      </a>
      <button class="focus-toggle mobile-focus-toggle ${isFocusTicker(row.ticker) ? "active" : ""}" type="button" data-focus-ticker="${escapeHtml(row.ticker)}" aria-label="${isFocusTicker(row.ticker) ? "Remove" : "Add"} ${escapeHtml(row.ticker)} from Focus List">★</button>
    </span>
  `;
}

function selectedRow() {
  return state.rows.find((row) => row.ticker === state.selectedTicker) || state.visibleRows[0] || state.rows[0] || null;
}

function validationSummary(row) {
  const items = [
    ["Market", payloadValue(row, "market_permission")],
    ["Risk", payloadValue(row, "risk_permission")],
    ["Ticker", payloadValue(row, "ticker_permission")],
    ["Walk-forward", payloadValue(row, "walk_forward_permission")],
  ].filter(([, value]) => value && String(value).toUpperCase() !== "ALLOW");
  const kind = actionKind(row?.action);
  const fillState = String(payloadValue(row, "execution_fill_state") || "").toUpperCase();
  const fillProbability = Number(payloadValue(row, "execution_fill_probability"));
  if (["buy", "continue"].includes(kind) && (fillState !== "VALIDATED" || !Number.isFinite(fillProbability) || fillProbability < 0.45)) {
    items.push(["Fillability", fillState || "INSUFFICIENT"]);
  }
  const validationSentence = (label, value) => {
    const state = String(value || "").replaceAll("_", " ").toLowerCase();
    if (label === "Market") return state === "block"
      ? "The broader market is not supportive."
      : "The broader market backdrop is mixed.";
    if (label === "Risk") return "Risk controls do not allow a new position yet.";
    if (label === "Ticker") return state === "insufficient" || state === "none"
      ? "This stock does not yet have enough reliable historical examples."
      : "Past setups in this stock have not been reliable enough.";
    if (label === "Fillability") return state === "low"
      ? "Comparable entry plans were filled too rarely."
      : "Comparable entry plans do not yet have enough fill evidence.";
    return state === "insufficient" || state === "none"
      ? "The pattern has not yet been proven across enough historical periods."
      : "The pattern has not held up consistently in historical testing.";
  };
  return items.length
    ? validationSentence(items[0][0], items[0][1])
    : "Market, stock-specific, risk and historical checks are clear.";
}

function renderReferenceLevels(row, { active = false } = {}) {
  const risk = payloadNumeric(row, "risk_pct_to_stop");
  const target = numericValue(row, "target_est");
  const takeProfit1 = payloadNumeric(row, "take_profit_1");
  const reducePct = payloadNumeric(row, "take_profit_1_reduce_pct");
  const postTp1Stop = payloadNumeric(row, "post_tp1_stop");
  const rows = [
    [entryPlanLabel(row, { active }), formatEntryZone(row) || "Unavailable"],
    ...(active ? [["How to enter", payloadValue(row, "entry_zone_plan") || "Use only the stated entry plan."]] : []),
    [active ? "Protect below" : "Reference stop", fmtNumber(row.stop_est, 2) || "Unavailable"],
    ...(active ? [
      ["First profit review", takeProfit1 ? `${fmtNumber(takeProfit1, 2)} · consider trimming ${fmtNumber(reducePct || 33, 0)}%` : "Unavailable"],
      ["After first target", postTp1Stop ? `Raise protection to ${fmtNumber(postTp1Stop, 2)} or higher` : "Unavailable"],
      ["Further target", target ? fmtNumber(target, 2) : "Unavailable"],
      ["Planned downside", risk ? `${fmtNumber(Math.abs(risk), 1)}%` : "Unavailable"]
    ] : [])
  ];
  return `<dl class="execution-sheet">${rows.map(([label, value]) => `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd></div>`).join("")}</dl>`;
}

function renderTickerDetailPanel() {
  const panel = document.querySelector("#ticker-detail-panel");
  if (!panel) return;
  const row = selectedRow();
  if (!row) { panel.innerHTML = ""; return; }
  state.selectedTicker = row.ticker;
  const kind = actionKind(row.action);
  const activePlan = executionChecksClear(row) && ["buy", "continue"].includes(kind);
  panel.innerHTML = `
    <div class="detail-panel-head"><div><span class="eyebrow">Selected stock</span><h2>${escapeHtml(row.ticker)}</h2><p>${escapeHtml(displaySecurityName(row.name, row.ticker) || row.name || "")}</p></div><a href="./ticker.html?ticker=${encodeURIComponent(row.ticker)}" aria-label="Open complete ${escapeHtml(row.ticker)} detail">Open details</a></div>
    <div class="detail-price"><strong>${escapeHtml(fmtNumber(row.close, 2))}</strong>${renderMovePct(row.day_change_pct)}</div>
    <span class="badge ${kind}">${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>
    <section class="decision-callout tone-${kind}"><span class="eyebrow">What to do</span><strong>${escapeHtml(decisionHeadline(row))}</strong><p>${escapeHtml(decisionNarrative(row))}</p></section>
    ${activePlan
      ? `<section class="active-plan"><span class="eyebrow">Price plan</span>${renderReferenceLevels(row, { active: true })}</section>`
      : `<div class="inactive-plan">No entry is recommended today.</div>`}
    <details class="detail-diagnostics"><summary>Why we see it this way</summary>${renderScoreBreakdown(row)}</details>
  `;
}

function selectTicker(ticker) {
  state.selectedTicker = normaliseTicker(ticker);
  const params = new URLSearchParams(window.location.search);
  params.set("ticker", state.selectedTicker);
  window.history.replaceState(null, "", `${window.location.pathname}?${params.toString()}${window.location.hash}`);
  renderTickerDetailPanel();
}

function renderCards(counts) {
  const cards = document.querySelector("#cards");
  cards.innerHTML = executionQueues(counts).map((queue) => `
    <button class="card execution-queue tone-${queue.key} ${state.filter === queue.filter ? "active" : ""}" type="button" data-filter="${queue.filter}">
      <span>${escapeHtml(queue.label)}</span>
      <strong>${queue.count}</strong>
      <small>${escapeHtml(queue.detail)}</small>
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

function tickerList(items, limit = 3) {
  const tickers = items.map((item) => item.row?.ticker || item.ticker).filter(Boolean);
  return tickers.length ? tickers.slice(0, limit).join(" / ") : "none";
}

function riskPriority(row) {
  const seller = Number(payloadValue(row, "seller_score"));
  const volume = String(payloadValue(row, "volume_state") || "").toUpperCase();
  const dayChange = numericValue(row, "day_change_pct");
  return (
    (Number.isFinite(seller) ? seller : 0) +
    (volume === "BREAKDOWN" ? 25 : volume === "DISTRIBUTION" ? 15 : 0) +
    (dayChange < 0 ? Math.min(Math.abs(dayChange) * 3, 25) : 0) -
    convictionScore(row) * 0.25
  );
}

function renderDailyBrief(counts) {
  const panel = document.querySelector("#daily-brief");
  if (!panel) return;
  const allChanges = dailyChangeItems(state.rows, state.previousRows, state.rows.length);
  const fresh = allChanges.filter((item) => item.transition === "New Today");
  const upgrades = allChanges.filter((item) => ["Fresh Setup To Buy", "Upgraded"].includes(item.transition));
  const exits = state.rows
    .filter((row) => actionKind(row.action) === "exit")
    .sort((a, b) => riskPriority(b) - riskPriority(a));
  const priceMovers = currentDayMoverItems(state.rows);
  const topBuy = [...state.rows]
    .filter((row) => actionKind(row.action) === "buy")
    .sort((a, b) => convictionScore(b) - convictionScore(a))[0];
  const exitCount = counts.exit || 0;
  const actionTotal = (counts.buy || 0) + (counts.setup || 0);
  const headline = copyText("actionableNames", { total: actionTotal, buy: counts.buy || 0, building: counts.setup || 0 });
  const freshText = tickerList(fresh);
  const upgradesText = tickerList(upgrades);
  const moverText = tickerList(priceMovers, 2);
  const riskText = exits.length ? tickerList(exits, 2) : `${exitCount} exit-risk`;

  panel.innerHTML = `
    <div class="brief-card">
      <div class="brief-copy">
        <span class="brief-kicker">${escapeHtml(copyText("dailyBrief"))}</span>
        <h2>${escapeHtml(headline)}</h2>
        <div class="brief-points">
          <span><b>${escapeHtml(copyText("fresh"))}</b> ${escapeHtml(freshText)}</span>
          <span><b>${escapeHtml(copyText("upgraded"))}</b> ${escapeHtml(upgradesText)}</span>
          <span><b>${escapeHtml(copyText("movers"))}</b> ${escapeHtml(moverText)}</span>
          <span><b>${escapeHtml(copyText("risk"))}</b> ${escapeHtml(riskText)}</span>
        </div>
        ${renderTrafficHealth(state.runInfo, state.rows)}
      </div>
      <div class="brief-actions">
        ${topBuy ? `<a class="brief-primary" href="./ticker.html?ticker=${encodeURIComponent(topBuy.ticker)}">${escapeHtml(copyText("reviewTicker", { ticker: topBuy.ticker }))}</a>` : ""}
        <button class="brief-secondary" type="button" data-filter-brief="buy">${escapeHtml(copyText("showBuy"))}</button>
      </div>
    </div>
  `;

  panel.querySelector("[data-filter-brief]")?.addEventListener("click", () => {
    state.filter = "buy";
    renderWatchlist();
    document.querySelector("#watchlist-table")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

function securityDisplay(row) {
  const name = displaySecurityName(row.name, row.ticker);
  return name ? `${row.ticker} · ${name}` : row.ticker;
}

function reasonChips(row, previous = previousRowFor(row), limit = 3) {
  const reasons = whyThisMatters(row, previous).slice(0, limit);
  return reasons.map((reason) => `<span class="reason-chip">${escapeHtml(reason)}</span>`).join("");
}

function focusItem(row, reason) {
  if (!row) return "";
  const kind = actionKind(row.action);
  return `
    <a class="focus-item tone-${kind}" href="./ticker.html?ticker=${encodeURIComponent(row.ticker)}">
      <span class="focus-kicker">${escapeHtml(reason)}</span>
      <span class="focus-main">
        <strong>${escapeHtml(row.ticker)}</strong>
        <span>${escapeHtml(displaySecurityName(row.name, row.ticker) || row.name || "")}</span>
      </span>
      <span class="focus-meta">
        <span class="badge ${kind}">${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>
        <span>Close ${fmtNumber(row.close, 2)} ${renderMovePct(row.day_change_pct)}</span>
      </span>
      <span class="reason-row">${reasonChips(row, previousRowFor(row), 2)}</span>
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
    .filter((row) => ["buy", "continue", "setup", "watch"].includes(actionKind(row.action)))
    .sort((a, b) => Number(b.day_change_pct || 0) - Number(a.day_change_pct || 0))[0];

  const items = [
    focusItem(strongest, copyText("buyFocus")),
    focusItem(building, copyText("buildingFocus")),
    focusItem(pressure, copyText("exitFocus")),
    focusItem(bestDay, copyText("moveFocus"))
  ].filter(Boolean);

  panel.innerHTML = `
    <div class="section-heading">
      <div>
        <span>${escapeHtml(copyText("todayFocus"))}</span>
      </div>
      ${runDate ? `<span class="section-date">${escapeHtml(runDate)}</span>` : ""}
    </div>
    <div class="focus-grid">${items.join("")}</div>
  `;
}

function changedTodayCard({ row, previous, pricePct }, duplicate = false) {
  const signal = ACTION_LABELS[row.action] || row.action || "Signal";
  return `
    <a class="change-card tone-${actionKind(row.action)}" href="./ticker.html?ticker=${encodeURIComponent(row.ticker)}"${duplicate ? ' aria-hidden="true" tabindex="-1"' : ""}>
      <div class="change-card-head">
        <strong>${escapeHtml(row.ticker)}</strong>
        <span>${escapeHtml(displaySecurityName(row.name, row.ticker) || row.name || "")}</span>
      </div>
      <div class="change-card-body">
        <span class="badge ${actionKind(row.action)}">${escapeHtml(signal)}</span>
        ${transitionBadge(row, previous)}
        <span class="change-chip ${moveClass(pricePct)}">Price ${fmtSignedNumber(pricePct, 1)}%</span>
      </div>
      <div class="reason-row">${reasonChips(row, previous, 2)}</div>
    </a>
  `;
}

function moversSectionHeading(title, runDate) {
  return `
    <div class="section-heading">
      <div>
        <span>${escapeHtml(title)}</span>
      </div>
      ${runDate ? `<span class="section-date">${escapeHtml(runDate)}</span>` : ""}
    </div>
  `;
}

function renderSignalChanges() {
  const panel = document.querySelector("#signal-changes");
  if (!panel) return;
  const runDate = state.rows[0]?.run_date || "";
  const changes = dailyChangeItems(state.rows, state.previousRows);
  if (!changes.length) {
    panel.innerHTML = `
      ${moversSectionHeading(copyText("signalChanges"), runDate)}
      <div class="empty compact-empty">${escapeHtml(copyText("noScannerChanges"))}</div>
    `;
    return;
  }

  const rolling = changes.length > 1;
  const cards = changes.map((change) => changedTodayCard(change)).join("");
  const duplicateCards = rolling ? changes.map((change) => changedTodayCard(change, true)).join("") : "";
  panel.innerHTML = `
    ${moversSectionHeading(copyText("signalChanges"), runDate)}
    <div class="change-rail${rolling ? " rolling" : ""}" aria-label="Today’s movers">
      <div class="change-track">
        ${cards}
        ${duplicateCards}
      </div>
    </div>
  `;
}

function renderPriceMovers() {
  const panel = document.querySelector("#price-movers");
  if (!panel) return;
  const runDate = state.rows[0]?.run_date || "";
  const movers = currentDayMoverItems(state.rows);
  if (!movers.length) {
    panel.innerHTML = `
      ${moversSectionHeading(copyText("priceMovers"), runDate)}
      <div class="empty compact-empty">${escapeHtml(copyText("noPriceMoves"))}</div>
    `;
    return;
  }

  const rolling = movers.length > 1;
  const cards = movers.map((change) => changedTodayCard(change)).join("");
  const duplicateCards = rolling ? movers.map((change) => changedTodayCard(change, true)).join("") : "";
  panel.innerHTML = `
    ${moversSectionHeading(copyText("priceMovers"), runDate)}
    <div class="change-rail${rolling ? " rolling" : ""}" aria-label="Price movers">
      <div class="change-track">
        ${cards}
        ${duplicateCards}
      </div>
    </div>
  `;
}

function renderFocusList() {
  const panel = document.querySelector("#focus-list");
  if (!panel) return;
  const runDate = state.rows[0]?.run_date || "";
  const focusStatus = state.focusSyncing ? "Syncing..." : state.focusMessage;
  const focusControls = state.focusPin ? `
    <div class="focus-controls">
      <span>${escapeHtml(focusStatus || "Cloud Focus List unlocked.")}</span>
      <button type="button" id="focus-sign-out">Sign out</button>
    </div>
  ` : `
    <div class="focus-unlock">
      <span>
        <strong>Cloud Focus List</strong>
        <small>Enter your PIN to sync starred tickers across devices.</small>
      </span>
      <form id="focus-pin-form">
        <input id="focus-pin-input" type="password" inputmode="numeric" autocomplete="current-password" placeholder="PIN" aria-label="Focus List PIN">
        <button type="submit">Unlock</button>
      </form>
      ${focusStatus ? `<em>${escapeHtml(focusStatus)}</em>` : ""}
    </div>
  `;
  const focusRows = state.focusTickers
    .map((ticker) => state.rows.find((row) => row.ticker === ticker))
    .filter(Boolean)
    .sort((a, b) => convictionScore(b) - convictionScore(a));

  if (!focusRows.length) {
    panel.innerHTML = `
      ${moversSectionHeading(copyText("focusList"), runDate)}
      ${focusControls}
      <div class="focus-empty">
        <span>${state.focusPin ? "Star tickers in the watchlist to keep your personal list here." : "Unlock first, then star tickers from the Watchlist."}</span>
      </div>
    `;
    return;
  }

  panel.innerHTML = `
    ${moversSectionHeading(copyText("focusList"), runDate)}
    ${focusControls}
    <div class="focus-list-grid">
      ${focusRows.map((row) => {
        const kind = actionKind(row.action);
        const previous = previousRowFor(row);
        return `
          <div class="focus-list-item tone-${kind}">
            <a class="focus-list-link" href="./ticker.html?ticker=${encodeURIComponent(row.ticker)}">
              <span>
                <strong>${escapeHtml(row.ticker)}</strong>
                <small>${escapeHtml(displaySecurityName(row.name, row.ticker) || row.name || "")}</small>
              </span>
              <span class="focus-list-tags">
                ${transitionBadge(row, previous)}
                <span class="badge ${kind}">${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>
                <span class="badge conviction-pill score-${strengthTone(row)}">${escapeHtml(strengthLabel(row))}</span>
                ${renderMovePct(row.day_change_pct)}
              </span>
            </a>
            <button class="focus-remove" type="button" data-remove-focus="${escapeHtml(row.ticker)}" aria-label="Remove ${escapeHtml(row.ticker)} from Focus List">×</button>
          </div>
        `;
      }).join("")}
    </div>
  `;
}

function attachFocusControls() {
  const form = document.querySelector("#focus-pin-form");
  if (form) {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const input = document.querySelector("#focus-pin-input");
      saveFocusPin(input?.value || "");
      const unlocked = await loadCloudFocusTickers();
      if (!unlocked) saveFocusPin("");
      renderWatchlist();
    });
  }

  const signOut = document.querySelector("#focus-sign-out");
  if (signOut) {
    signOut.addEventListener("click", () => {
      saveFocusPin("");
      state.focusMessage = "Signed out on this device.";
      renderWatchlist();
    });
  }

  document.querySelectorAll("[data-remove-focus]").forEach((button) => {
    button.addEventListener("click", async () => {
      const ticker = normaliseTicker(button.dataset.removeFocus);
      state.focusTickers = state.focusTickers.filter((value) => value !== ticker);
      saveFocusTickers();
      renderWatchlist();
      await saveCloudFocusTickers();
      renderWatchlist();
    });
  });
}

function readStoredList(key) {
  try {
    const parsed = JSON.parse(localStorage.getItem(key) || "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeStoredList(key, values) {
  try {
    localStorage.setItem(key, JSON.stringify(values));
  } catch {
    // The notification center remains usable for the current session.
  }
}

function notificationForRow(row) {
  const ticker = normaliseTicker(row.ticker);
  if (!ticker) return null;
  const date = String(row.data_date || row.date || row.run_date || "").slice(0, 10);
  const stage = String(payloadValue(row, "profit_stage") || "").toUpperCase();
  const overlay = String(payloadValue(row, "contextual_overlay") || "").toUpperCase();
  const takeProfit1 = payloadNumeric(row, "take_profit_1");
  const reducePct = payloadNumeric(row, "take_profit_1_reduce_pct") || 33;
  const protectiveStop = payloadNumeric(row, "active_protective_stop") || payloadNumeric(row, "post_tp1_stop");

  if (stage === "PROTECT REMAINDER" || overlay === "PROFIT PROTECT") {
    return {
      id: `${date}:${ticker}:protect-remainder`,
      date,
      ticker,
      kind: "protect",
      title: `${ticker} · Protect remaining profit`,
      body: protectiveStop
        ? `Profit is giving back. Protect the remaining position at ${fmtNumber(protectiveStop, 2)} or follow the current EXIT signal.`
        : "Profit is giving back or supply is increasing. Reduce risk and follow the current EXIT signal.",
    };
  }
  if (stage === "TP1 REACHED" || overlay === "TAKE PROFIT 1") {
    return {
      id: `${date}:${ticker}:take-profit-1`,
      date,
      ticker,
      kind: "profit",
      title: `${ticker} · Take Profit 1 reached`,
      body: `Trim ${fmtNumber(reducePct, 0)}%${takeProfit1 ? ` near ${fmtNumber(takeProfit1, 2)}` : ""}${protectiveStop ? ` and protect the balance at ${fmtNumber(protectiveStop, 2)} or higher` : ""}.`,
    };
  }
  if (row.action === "EXIT PRESSURE" && state.focusTickers.includes(ticker)) {
    return {
      id: `${date}:${ticker}:exit-pressure`,
      date,
      ticker,
      kind: "exit",
      title: `${ticker} · Exit risk`,
      body: "This Focus List name has structural exit pressure. Review the stop and current seller evidence.",
    };
  }
  return null;
}

function notificationHistory() {
  const stored = readStoredList(APP_NOTIFICATION_HISTORY)
    .filter((item) => item && item.id && item.ticker && item.title);
  const current = state.rows.map(notificationForRow).filter(Boolean);
  const merged = new Map(stored.map((item) => [item.id, item]));
  current.forEach((item) => merged.set(item.id, item));
  const items = [...merged.values()]
    .sort((a, b) => String(b.date).localeCompare(String(a.date)) || String(b.id).localeCompare(String(a.id)))
    .slice(0, 50);
  writeStoredList(APP_NOTIFICATION_HISTORY, items);
  return items;
}

function markNotificationsRead(ids) {
  const read = new Set(readStoredList(APP_NOTIFICATION_READ));
  ids.forEach((id) => read.add(id));
  writeStoredList(APP_NOTIFICATION_READ, [...read].slice(-200));
}

function renderNotificationCenter() {
  const mount = document.querySelector("#profit-alerts");
  if (!mount) return;
  const items = notificationHistory();
  const read = new Set(readStoredList(APP_NOTIFICATION_READ));
  const unread = items.filter((item) => !read.has(item.id));
  mount.innerHTML = `
    <details class="notification-center">
      <summary>
        <span><strong>Notification Center</strong><small>Action alerts for saved positions</small></span>
        <span class="notification-count ${unread.length ? "has-unread" : ""}">${unread.length ? `${unread.length} unread` : "All read"}</span>
      </summary>
      <div class="notification-body">
        <div class="notification-toolbar">
          <span>${items.length ? `${items.length} recent alert${items.length === 1 ? "" : "s"}` : "No profit or Focus List exit alerts yet"}</span>
          ${unread.length ? '<button type="button" id="mark-notifications-read">Mark all read</button>' : ""}
        </div>
        <div class="notification-list">
          ${items.length ? items.map((item) => `
            <a class="notification-item tone-${escapeHtml(item.kind)} ${read.has(item.id) ? "read" : "unread"}" href="./ticker.html?ticker=${encodeURIComponent(item.ticker)}" data-notification-id="${escapeHtml(item.id)}">
              <span class="notification-dot" aria-hidden="true"></span>
              <span><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.body)}</small></span>
              <time>${escapeHtml(item.date || "Latest")}</time>
            </a>
          `).join("") : '<div class="notification-empty">TP1 and profit-protection events will appear here after the daily refresh.</div>'}
        </div>
      </div>
    </details>
  `;
  document.querySelector("#mark-notifications-read")?.addEventListener("click", () => {
    markNotificationsRead(items.map((item) => item.id));
    renderNotificationCenter();
  });
  mount.querySelectorAll("[data-notification-id]").forEach((link) => {
    link.addEventListener("click", () => markNotificationsRead([link.dataset.notificationId]));
  });
}

function renderWatchlist({ refreshOverview = true } = {}) {
  const counts = { buy: 0, continue: 0, setup: 0, watch: 0, exit: 0, avoid: 0 };
  state.rows.forEach((row) => {
    counts[actionKind(row.action)] += 1;
  });
  if (refreshOverview) {
    renderCards(counts);
    renderDailyBrief(counts);
    renderTodayFocus();
    renderSignalChanges();
    renderPriceMovers();
    renderFocusList();
    renderNotificationCenter();
  }

  const needle = state.query.trim().toLowerCase();
  const searchActive = Boolean(needle);
  const exactTickerNeedle = exactTickerSearchNeedle(state.query, state.rows);
  document.body.classList.toggle("search-active", searchActive);
  const [sortKey, direction] = state.sort.split("-");
  const multiplier = direction === "asc" ? 1 : -1;
  state.visibleRows = state.rows
    .filter((row) => {
      const kind = actionKind(row.action);
      if (state.filter === "building") return ["continue", "setup", "watch"].includes(kind);
      if (state.filter === "risk") return ["exit", "avoid"].includes(kind);
      return state.filter === "all" || kind === state.filter;
    })
    .filter((row) => rowMatchesSearch(row, state.query, exactTickerNeedle))
    .sort((a, b) => {
      if (sortKey === "ticker") return a.ticker.localeCompare(b.ticker) * multiplier;
      if (sortKey === "score") return (convictionScore(a) - convictionScore(b)) * multiplier;
      if (sortKey === "execution_priority") {
        const priorityMove = (payloadNumeric(a, "execution_priority") - payloadNumeric(b, "execution_priority")) * multiplier;
        if (priorityMove) return priorityMove;
        return convictionScore(b) - convictionScore(a);
      }
      return (Number(a[sortKey] || 0) - Number(b[sortKey] || 0)) * multiplier;
    });

  if (searchActive && state.visibleRows.length === 1) {
    state.selectedTicker = state.visibleRows[0].ticker;
  }

  const columns = watchlistColumns();
  const renderedRows = state.visibleRows.slice(0, state.rowLimit);
  document.querySelector("#watchlist-head").innerHTML = `<tr>${columns.map(([, label]) => `<th>${escapeHtml(label)}</th>`).join("")}</tr>`;
  document.querySelector("#watchlist-body").innerHTML = renderedRows.map((row) => `
    <tr class="row-${actionKind(row.action)} ${row.ticker === state.selectedTicker ? "selected" : ""}" style="--score-pct: ${fmtConviction(row)}%">
      ${columns.map(([key]) => `<td class="${["score", "operator_state_score", "operator_pressure_score", "close", "day_change_pct", "entry_est", "stop_est", "target_est", "risk_pct_to_stop", "position_value_1k_risk", "price_summary"].includes(key) ? "num" : ""}">${renderWatchlistCell(row, key)}</td>`).join("")}
      <td class="mobile-summary">${renderMobileWatchlistSummary(row)}</td>
    </tr>
  `).join("");
  if (refreshOverview) attachFocusControls();
  document.querySelector("#count").textContent = `${renderedRows.length} / ${state.visibleRows.length} filtered · ${state.rows.length} total`;
  const showMore = document.querySelector("#show-more");
  if (showMore) {
    showMore.classList.toggle("hidden", renderedRows.length >= state.visibleRows.length);
    showMore.textContent = `Show ${Math.min(INITIAL_WATCHLIST_ROWS, state.visibleRows.length - renderedRows.length)} more`;
  }
  const mobileCount = document.querySelector("#mobile-search-count");
  if (mobileCount) {
    mobileCount.textContent = searchActive
      ? `${state.visibleRows.length} ${copyText(state.visibleRows.length === 1 ? "result" : "results")}`
      : `${state.visibleRows.length} ${copyText("shown")}`;
  }
  document.querySelectorAll("[data-mobile-filter]").forEach((button) => {
    button.classList.toggle("active", button.dataset.mobileFilter === state.filter);
  });
  const watchlistTitle = document.querySelector(".watchlist-heading span:not(.section-date)");
  if (watchlistTitle) watchlistTitle.textContent = searchActive ? copyText("searchResults") : copyText("watchlist");
  document.querySelector("#empty").classList.toggle("hidden", state.visibleRows.length > 0);
  if (refreshOverview || searchActive) renderTickerDetailPanel();
}

function scrollToWatchlistResults() {
  if (!window.matchMedia("(max-width: 960px)").matches) return;
  const target = document.querySelector("#watchlist-table");
  if (!target) return;
  const stickyOffset = 150;
  const top = Math.max(0, target.getBoundingClientRect().top + window.scrollY - stickyOffset);
  window.history.replaceState(null, "", "#watchlist-table");
  window.scrollTo({ top, behavior: "smooth" });
}

function initTabNavigation() {
  const tabs = [...document.querySelectorAll(".app-tabbar a")];
  if (!tabs.length) return;
  const setActive = (hash) => {
    tabs.forEach((tab) => {
      const active = tab.getAttribute("href") === hash;
      tab.classList.toggle("active", active);
      if (active) tab.setAttribute("aria-current", "page");
      else tab.removeAttribute("aria-current");
    });
  };
  tabs.forEach((tab) => {
    tab.addEventListener("click", (event) => {
      const hash = tab.getAttribute("href");
      if (!hash?.startsWith("#")) return;
      const target = document.querySelector(hash);
      if (!target) return;
      event.preventDefault();
      if (target instanceof HTMLDetailsElement) target.open = true;
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
  state.focusTickers = loadFocusTickers();
  state.focusPin = loadFocusPin();
  const searchInput = document.querySelector("#search");
  const mobileSearchInput = document.querySelector("#mobile-search");
  const clearSearch = document.querySelector("#clear-search");
  const mobileClearSearch = document.querySelector("#mobile-clear-search");
  const syncSearchClear = () => {
    if (clearSearch) clearSearch.classList.toggle("hidden", !searchInput.value);
    if (mobileClearSearch) mobileClearSearch.classList.toggle("hidden", !state.query);
    if (searchInput.value !== state.query) searchInput.value = state.query;
    if (mobileSearchInput && mobileSearchInput.value !== state.query) mobileSearchInput.value = state.query;
  };
  let searchFrame = 0;
  const updateSearch = (value, shouldScroll = true) => {
    state.query = value;
    state.rowLimit = INITIAL_WATCHLIST_ROWS;
    syncSearchClear();
    cancelAnimationFrame(searchFrame);
    searchFrame = requestAnimationFrame(() => {
      renderWatchlist({ refreshOverview: false });
      if (shouldScroll && state.query.trim()) scrollToWatchlistResults();
    });
  };
  searchInput.addEventListener("input", (event) => {
    updateSearch(event.target.value);
  });
  mobileSearchInput?.addEventListener("input", (event) => {
    updateSearch(event.target.value);
  });
  if (clearSearch) {
    clearSearch.addEventListener("click", () => {
      updateSearch("", false);
      searchInput.focus();
    });
  }
  if (mobileClearSearch) {
    mobileClearSearch.addEventListener("click", () => {
      updateSearch("", false);
      mobileSearchInput?.focus();
    });
  }
  document.querySelectorAll("[data-mobile-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      state.filter = button.dataset.mobileFilter || "all";
      state.rowLimit = INITIAL_WATCHLIST_ROWS;
      renderWatchlist();
      scrollToWatchlistResults();
    });
  });
  document.querySelector("#sort").addEventListener("change", (event) => {
    state.sort = event.target.value;
    state.rowLimit = INITIAL_WATCHLIST_ROWS;
    renderWatchlist({ refreshOverview: false });
  });
  document.querySelector("#show-more")?.addEventListener("click", () => {
    state.rowLimit += INITIAL_WATCHLIST_ROWS;
    renderWatchlist({ refreshOverview: false });
  });
  document.querySelector("#watchlist-body")?.addEventListener("click", (event) => {
    const focusButton = event.target.closest("[data-focus-ticker]");
    if (focusButton) {
      event.preventDefault();
      event.stopPropagation();
      toggleFocusTicker(focusButton.dataset.focusTicker);
      return;
    }
    const tickerButton = event.target.closest("[data-select-ticker]");
    if (tickerButton) selectTicker(tickerButton.dataset.selectTicker);
  });
  syncSearchClear();
  initTabNavigation();
  try {
    const latestPayload = isGithubPagesHost()
      ? await loadStaticLatestRows()
      : await appApiFetch("/api/watchlist/latest", { fresh: true, ttl: 0 });
    state.rows = (latestPayload.rows || [])
      .map((row) => ({ ...row, name: displaySecurityName(row.name, row.ticker) || row.name || row.ticker }));
    state.previousRows = latestPayload.previousRows || [];
    state.previousByTicker = rowByTicker(state.previousRows);
    state.selectedTicker = normaliseTicker(new URLSearchParams(window.location.search).get("ticker") || state.rows[0]?.ticker || "");
    if (!state.rows.length) {
      const fallback = await loadStaticLatestRows();
      state.rows = fallback.rows;
      state.previousRows = fallback.previousRows;
      state.previousByTicker = rowByTicker(state.previousRows);
      state.runInfo = fallback.runInfo || null;
      await loadCloudFocusTickers();
      const marketData = dataDateSummary(state.rows);
      setRefreshSummary(fallback.latest, `${marketData} · saved validated data`, state.rows);
      renderWatchlist();
      return;
    }
    const marketData = dataDateSummary(state.rows);
    state.runInfo = latestPayload.runInfo || null;
    await loadCloudFocusTickers();
    setRefreshSummary(latestPayload.latest, marketData, state.rows, latestPayload.runInfo);
    renderWatchlist();
  } catch (error) {
    try {
      const fallback = await loadStaticLatestRows();
      state.rows = fallback.rows;
      state.previousRows = fallback.previousRows;
      state.previousByTicker = rowByTicker(state.previousRows);
      state.runInfo = fallback.runInfo || null;
      await loadCloudFocusTickers();
      const marketData = dataDateSummary(state.rows);
      setRefreshSummary(fallback.latest, `${marketData} · saved validated data`, state.rows);
      renderWatchlist();
    } catch {
      setStatus(error.message, false);
    }
  }
}

function renderLatestHistoryPanel(latest) {
  const panel = document.querySelector("#latest-panel");
  if (!latest) {
    panel.innerHTML = "";
    return;
  }
  const kind = actionKind(latest.action);
  const activePlan = executionChecksClear(latest) && ["buy", "continue"].includes(kind);
  panel.innerHTML = `
    <div class="latest-card tone-${actionKind(latest.action)}">
      <div class="latest-head">
        <span class="latest-label">Today's signal</span>
        <span class="badge ${kind}">${escapeHtml(ACTION_LABELS[latest.action] || latest.action)}</span>
      </div>
      <div class="latest-price"><span>Latest close</span><strong>${fmtNumber(latest.close, 2)} ${renderMovePct(latest.day_change_pct)}</strong></div>
      <section class="decision-callout tone-${kind}"><span class="eyebrow">What to do</span><strong>${escapeHtml(decisionHeadline(latest))}</strong><p>${escapeHtml(decisionNarrative(latest))}</p></section>
      ${activePlan
        ? `<section class="active-plan"><span class="eyebrow">Price plan</span>${renderReferenceLevels(latest, { active: true })}</section>`
        : `<div class="inactive-plan">No entry is recommended today.</div>`}
      <details class="detail-diagnostics"><summary>Why we see it this way</summary>${renderScoreBreakdown(latest)}</details>
    </div>
  `;
}

function historySignalSentence(rows, summaryApi) {
  const transition = summaryApi.signalTransition(rows);
  if (transition.reason === "actions") return "Signal history is unavailable because one or more sessions are missing a signal.";
  if (!transition.available) return "Signal history is unavailable.";
  const latestSignal = ACTION_LABELS[transition.currentAction] || transition.currentAction;
  if (!transition.changed) return `Unchanged at ${latestSignal} throughout the ${transition.windowSessions}-session window.`;
  const previousSignal = ACTION_LABELS[transition.previousAction] || transition.previousAction;
  if (transition.sessionsAgo === 0) return `Changed from ${previousSignal} to ${latestSignal} in the latest trading session.`;
  return `Changed from ${previousSignal} to ${latestSignal} ${transition.sessionsAgo === 1 ? "one trading session" : `${transition.sessionsAgo} trading sessions`} ago.`;
}

function pressureSummary(rows, summaryApi) {
  const comparison = summaryApi.pressureComparison(rows);
  if (!comparison.available && comparison.reason === "window") {
    return "A 5-versus-25 session comparison needs 30 valid observations and is not available yet.";
  }
  if (!comparison.available) {
    return "Price-and-volume pressure could not be compared because the source scores are incomplete.";
  }
  const recentRows = rows.slice(-5);
  const direction = comparison.shift;
  const currentKind = actionKind(rows.at(-1).action);
  const staleReminder = qualityConstraintLabel(rows.at(-1)) === "DATA OLD"
    ? " Today's data is stale, so this historical pressure is descriptive only."
    : "";
  const defensiveReminder = ["exit", "avoid"].includes(currentKind)
    ? ` This price-and-volume proxy does not override today's ${ACTION_LABELS[rows.at(-1).action] || rows.at(-1).action} signal.`
    : "";
  const contextReminder = `${staleReminder}${defensiveReminder}`;
  if (direction === "balanced") {
    return `The price-and-volume proxy shows no meaningful change between buying and selling pressure; recent volume is not giving a directional confirmation.${contextReminder}`;
  }
  const confirmingStates = direction === "buying"
    ? new Set(["DEMAND", "BREAKOUT"])
    : new Set(["DISTRIBUTION", "BREAKDOWN", "SUPPLY"]);
  const opposingStates = direction === "buying"
    ? new Set(["DISTRIBUTION", "BREAKDOWN", "SUPPLY"])
    : new Set(["DEMAND", "BREAKOUT"]);
  const confirmingDays = recentRows.filter((row) => confirmingStates.has(String(payloadValue(row, "volume_state") || "").toUpperCase())).length;
  const opposingDays = recentRows.filter((row) => opposingStates.has(String(payloadValue(row, "volume_state") || "").toUpperCase())).length;
  const controlSentence = comparison.control === "buying"
    ? " Buyers now have the advantage."
    : comparison.control === "selling"
      ? " Sellers still have the advantage."
      : " Neither side now has a clear advantage.";
  const pressureLead = `The price-and-volume proxy shifted toward ${direction} over the latest five sessions.`;
  const volumeSentence = confirmingDays >= 2 && confirmingDays > opposingDays
    ? ` Directionally supportive volume appeared on ${confirmingDays} of those sessions.`
    : opposingDays >= 2
      ? " Recent volume points the other way and does not confirm the shift."
      : " Recent volume confirmation remains limited.";
  return `${pressureLead}${controlSentence}${volumeSentence}${contextReminder}`;
}

function historyInterpretation(latest, priceMovePct, summaryApi) {
  const kind = actionKind(latest.action);
  const state = summaryApi.interpretationState(kind, {
    stale: qualityConstraintLabel(latest) === "DATA OLD",
    checksClear: executionChecksClear(latest),
  });
  if (state === "stale-exit") return "Today's data is stale. Keep the defensive Exit posture until fresh data confirms otherwise.";
  if (state === "stale-avoid") return "Today's data is stale. Continue to Avoid new entries until fresh data is available.";
  if (state === "stale") return "Today's data is stale, so the recent record cannot support an entry.";
  if (state === "exit") return "The current Exit signal takes priority over any positive move in the recent price record.";
  if (state === "avoid") return "The recent record does not establish a usable setup; the current view remains Avoid.";
  if (state === "blocked") return "Today's data and risk checks do not support an entry.";
  if (state === "setup") return "The technical picture is developing, but it has not reached an entry signal.";
  if (state === "watch") return "The recent record remains mixed; there is no confirmed entry.";
  if (state === "continue") return "The recent trend remains constructive, but this is not a fresh entry signal by itself.";
  if (state === "buy") return "The recent record is constructive and today's Buy has passed the current execution checks.";
  return `Price ${priceMovePct >= 0 ? "improved" : "weakened"} over the measured period, but there is no executable entry today.`;
}

function renderHistoryVisual(rows) {
  const visual = document.querySelector("#history-visual");
  const summaryApi = window.HistorySummary;
  if (!summaryApi?.historyMetrics || !summaryApi?.pressureComparison || !summaryApi?.signalTransition || !summaryApi?.interpretationState) {
    visual.innerHTML = "<div class=\"empty\">Recent behavior summary is temporarily unavailable.</div>";
    return;
  }
  const metrics = summaryApi.historyMetrics([...rows].reverse());
  if (metrics.reason === "dates") {
    visual.innerHTML = "<div class=\"empty\">Recent behavior summary is unavailable because session dates are incomplete.</div>";
    return;
  }
  const chronological = metrics.rows;
  if (!chronological.length) {
    visual.innerHTML = "<div class=\"empty\">No recent behavior found.</div>";
    return;
  }

  const latest = chronological.at(-1);
  const { priceMovePct = 0, maxDrawdownPct, distanceFromHighPct } = metrics;
  const periodLabel = `${chronological.length}-session summary`;
  const priceSentence = metrics.priceAvailable
    ? `Price ${priceMovePct >= 0 ? "rose" : "fell"} ${fmtNumber(Math.abs(priceMovePct), 1)}%. The maximum drawdown based on closing prices was ${fmtNumber(maxDrawdownPct, 1)}%. ${distanceFromHighPct == null ? "The distance from the period high is unavailable because one or more daily highs are missing or invalid." : `The latest close is ${fmtNumber(Math.abs(distanceFromHighPct), 1)}% below the period's highest daily high.`}`
    : "Price statistics are unavailable because one or more closing prices are missing or invalid.";

  visual.innerHTML = `
    <div class="behavior-summary" aria-label="${escapeHtml(periodLabel)}">
      <div class="behavior-summary-head"><span>${escapeHtml(periodLabel)}</span><strong>${escapeHtml(historyInterpretation(latest, priceMovePct, summaryApi))}</strong></div>
      <div><span>Price</span><strong>${escapeHtml(priceSentence)}</strong></div>
      <div><span>Signal</span><strong>${escapeHtml(historySignalSentence(chronological, summaryApi))}</strong></div>
      <div><span>Buying pressure</span><strong>${escapeHtml(pressureSummary(chronological, summaryApi))}</strong></div>
      <p class="behavior-action"><span>Today</span><strong>${escapeHtml(decisionHeadline(latest))}.</strong></p>
    </div>
  `;
}

function renderHistoryRows() {
  const timeline = document.querySelector("#timeline");
  if (!state.historyRows.length) {
    timeline.innerHTML = "<div class=\"empty\">No history found for this ticker.</div>";
    document.querySelector("#history-visual").innerHTML = "<div class=\"empty\">No recent behavior found.</div>";
    renderLatestHistoryPanel(null);
    return;
  }
  renderLatestHistoryPanel(state.historyRows[0]);
  renderHistoryVisual(state.historyRows);
  const chronological = [...state.historyRows].reverse();
  const previousByDate = new Map(chronological.map((row, index) => [row.history_date, chronological[index - 1] || null]));
  const meaningfulRows = state.historyRows.filter((row, index) => {
    const previous = previousByDate.get(row.history_date);
    return index === 0
      || !previous
      || row.action !== previous.action
      || row.setup !== previous.setup
      || Math.abs(convictionScore(row) - convictionScore(previous)) >= 8
      || Math.abs(numericValue(row, "day_change_pct")) >= 3;
  });
  const recentRows = meaningfulRows.slice(0, 3);
  const recentDates = new Set(recentRows.map((row) => row.history_date));
  const lookbackRows = state.historyRows.filter((row) => !recentDates.has(row.history_date));

  timeline.innerHTML = `
    <h3>What changed</h3>
    ${recentRows.map((row, index) => `
      <div class="moment-card tone-${actionKind(row.action)}">
        <div class="moment-date">${index === 0 ? "Latest" : escapeHtml(fmtCompactDate(row.history_date))}</div>
        <div class="moment-body">
          <span class="badge ${actionKind(row.action)}">${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>
          <p class="moment-change">${escapeHtml(historyChangeSentence(row, previousByDate.get(row.history_date)))}</p>
          <p class="subtle">${escapeHtml(recentBehaviorSummary(row, previousByDate.get(row.history_date)))}</p>
        </div>
      </div>
    `).join("")}
    <details class="raw-history">
      <summary>See earlier sessions</summary>
      <div class="lookback-grid">
      ${lookbackRows.length ? lookbackRows.map((row) => `
        <article class="lookback-card tone-${actionKind(row.action)}">
          <div class="lookback-date">
            <strong>${escapeHtml(fmtCompactDate(row.history_date))}</strong>
            <span>${escapeHtml(row.history_date)}</span>
          </div>
          <div class="lookback-main">
            <span class="badge ${actionKind(row.action)}">${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>
          </div>
          <div class="lookback-meta">
            <span>${escapeHtml(setupLabel(row.setup))}</span>
            ${renderMovePct(row.day_change_pct)}
          </div>
          <div class="lookback-price">
            <strong>${fmtNumber(row.close, 2)}</strong>
          </div>
        </article>
      `).join("") : "<div class=\"empty compact-empty\">No earlier look-back days available.</div>"}
      </div>
    </details>
  `;
}

function historyChangeSentence(row, previous) {
  if (!previous) return "This is the first recorded session.";
  const currentSignal = ACTION_LABELS[row.action] || row.action;
  const priorSignal = ACTION_LABELS[previous.action] || previous.action;
  if (currentSignal !== priorSignal) return `The view changed from ${priorSignal} to ${currentSignal}.`;
  if (row.setup !== previous.setup) return `The price pattern changed to ${setupLabel(row.setup).toLowerCase()}.`;
  const trendMove = convictionScore(row) - convictionScore(previous);
  if (Math.abs(trendMove) >= 8) return `The technical condition ${trendMove > 0 ? "strengthened" : "weakened"}.`;
  const priceMove = numericValue(row, "day_change_pct");
  if (Math.abs(priceMove) >= 3) return `Price made a larger-than-usual ${priceMove > 0 ? "upward" : "downward"} move.`;
  return "There was no important change from the prior session.";
}

async function loadHistory(ticker) {
  state.ticker = normaliseTicker(ticker);
  state.tickerName = "";
  document.querySelector("#ticker").value = state.ticker;
  document.querySelector("#history-title").textContent = state.ticker;
  document.querySelector("#ticker-name").innerHTML = "";
  setCompanyContextAvailable(false);
  document.querySelector("#company-context").innerHTML = `
    <h2>About the company</h2>
    <div class="company-context-empty subtle">Loading company information...</div>
  `;
  document.title = state.ticker;
  window.history.replaceState(null, "", `./ticker.html?ticker=${encodeURIComponent(state.ticker)}`);
  setStatus("Loading ticker history...");
  document.querySelector("#run-status").textContent = "Loading current data...";
  document.querySelector("#run-status").classList.remove("bad", "warn");
  document.querySelector("#run-status").classList.add("loading");
  try {
    const tickerPayload = isGithubPagesHost()
      ? await loadStaticTickerHistory(state.ticker)
      : await appApiFetch(`/api/ticker/${encodeURIComponent(state.ticker)}`, { fresh: true, ttl: 0 });
    const latest = tickerPayload.latest;
    state.tickerName = displaySecurityName(tickerPayload.snapshot?.name, state.ticker);
    document.querySelector("#history-title").textContent = historyDisplayTitle();
    document.title = historyDisplayTitle();
    renderCompanyBriefWithFallback(state.ticker, tickerPayload.profile || {});
    state.historyRows = tickerPayload.historyRows || [];
    const marketData = historyDateSummary(state.historyRows);
    setRefreshSummary(latest, marketData, state.historyRows, tickerPayload.runInfo);
    renderHistoryRows();
  } catch (error) {
    try {
      const fallback = await loadStaticTickerHistory(state.ticker);
      if (!fallback.rows.length) throw error;
      state.tickerName = displaySecurityName(fallback.name, state.ticker);
      document.querySelector("#history-title").textContent = historyDisplayTitle();
      document.title = historyDisplayTitle();
      state.historyRows = fallback.rows;
      const marketData = historyDateSummary(state.historyRows);
      setRefreshSummary(fallback.latest, `${marketData} · saved validated data`, state.historyRows, fallback.runInfo);
      renderCompanyBriefWithFallback(state.ticker, fallback.profile || {});
      renderHistoryRows();
    } catch (fallbackError) {
      state.historyRows = [];
      setStatus(fallbackError?.message || error.message, false);
      renderHistoryRows();
    }
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
