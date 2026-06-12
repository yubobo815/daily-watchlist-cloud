const ACTION_LABELS = {
  "BUY CANDIDATE": "BUY",
  "STRONG CONTINUATION": "TRENDING",
  "SETUP FORMING": "BUILDING",
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
  ["buy_tier", "Tier"],
  ["next_day_bias", "Next Day"],
  ["operator_state", "Operator"],
  ["next_day_plan", "Plan"],
  ["score", "Trend Quality"],
  ["close", "Close"],
  ["day_change_pct", "Chg%"],
  ["setup", "Pattern"],
  ["adaptive_mode", "Market Behavior"],
  ["psychology", "Tape"],
  ["entry_est", "Ref Zone"],
  ["stop_est", "Stop"],
  ["target_est", "Target"],
  ["risk_pct_to_stop", "Risk%"],
  ["position_value_1k_risk", "Pos@1k"],
  ["notes", "Behavior Note"]
];

const SUMMARY_CARDS = [
  ["buy", "BUY"],
  ["continue", "TRENDING"],
  ["setup", "BUILDING"],
  ["watch", "WATCH"],
  ["exit", "EXIT"],
  ["avoid", "AVOID"]
];

const ACTION_TONE = {
  buy: "#0f8a5f",
  continue: "#0891b2",
  setup: "#b7791f",
  watch: "#2f5fb3",
  exit: "#b42318",
  avoid: "#667085"
};

const KIND_LABELS = {
  buy: "BUY",
  continue: "TRENDING",
  setup: "BUILDING",
  watch: "WATCH",
  exit: "EXIT",
  avoid: "AVOID"
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
  data_stale_block: "Stale data blocked execution",
  cached_data_ok: "Cached data recent enough",
  top_buy_tier: "A+ buy tier",
  buy_watch_tier: "Buy watch tier",
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
  missing_execution_proof: "Execution proof pending"
};

const APP_DISCLAIMER = "This tool is intended for reference and analysis only. Do not consider this as financial or investment advice.";
const SUPABASE_CACHE_TTL_MS = 2 * 60 * 1000;
const JSON_CACHE_PREFIX = "daily-trade-copilot:json:v1:";
const API_CACHE_PREFIX = "daily-trade-copilot:api:v1:";
const FOCUS_LIST_KEY = "daily-trade-copilot:focus-tickers:v1";
const FOCUS_PIN_KEY = "daily-trade-copilot:focus-pin:v1";
const STATIC_FALLBACK_MAX_AGE_DAYS = 10;
const PUBLISHED_HISTORY_CSV_URL = "https://yubobo815.github.io/daily-watchlist-cloud/watchlist_behavior_history_latest.csv";

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
  runInfo: null
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
  return state.tickerName || state.ticker;
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

  if (!summary && !highlights && !nextReport && !website && !industry) {
    target.innerHTML = `
      <h2>Company Context</h2>
      <div class="company-context-empty subtle">No company context available yet.</div>
    `;
    return;
  }

  target.innerHTML = `
    <h2>Company Context</h2>
    <details class="company-brief">
      <summary>
        ${industry ? `<div class="company-kicker">${escapeHtml(industry)}</div>` : ""}
        ${summary ? `<p>${escapeHtml(summary)}</p>` : ""}
        ${summary && summary.length > 120 ? `<span class="company-toggle" data-open="Show less" data-closed="Show more"></span>` : ""}
      </summary>
      <div class="company-facts">
        ${highlights ? `<div><span>Latest report</span><strong>${escapeHtml(highlights)}</strong></div>` : ""}
        ${nextReport ? `<div><span>Next report</span><strong>${escapeHtml(nextReport)}</strong></div>` : ""}
        ${website ? `<div><span>Website</span><strong><a href="${escapeHtml(website)}" target="_blank" rel="noopener noreferrer">${escapeHtml(new URL(website).hostname.replace(/^www\./, ""))}</a></strong></div>` : ""}
      </div>
      <span class="company-source">Source: ${escapeHtml(source)}</span>
    </details>
  `;
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
  if (Array.isArray(raw)) return raw.filter(Boolean);
  if (typeof raw === "string") {
    try {
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed.filter(Boolean) : [];
    } catch {
      return raw.split(",").map((item) => item.trim()).filter(Boolean);
    }
  }
  return [];
}

function scannerScoreValue(row) {
  const adjusted = payloadValue(row, "adjusted_score");
  const raw = adjusted === "" || adjusted == null ? payloadValue(row, "score") : adjusted;
  const number = Number(raw);
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
  if (text.includes("BEAR_TRAP") || text.includes("SQUEEZE") || text.includes("ACCUMULATION") || text.includes("ABSORPTION")) return "constructive";
  return "watch";
}

function shortOperatorPressure(value) {
  const text = String(value || "NEUTRAL").toUpperCase();
  if (text === "ACCUMULATION") return "ACCUM";
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
    ["R", payloadValue(row, "risk_permission")]
  ];
  return `<span class="gate-stack">${gates.map(([label, value]) => `
    <span class="badge gate-pill gate-${permissionTone(value)}" title="${label}: ${escapeHtml(String(value || "UNKNOWN"))}">${label}${permissionShort(value)}</span>
  `).join("")}</span>`;
}

function auditGateValues(row) {
  return [
    payloadValue(row, "market_permission"),
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

function strengthLabel(rowOrScore) {
  if (typeof rowOrScore === "object" && actionKind(rowOrScore.action) === "exit") return "Exit Risk";
  const band = scoreBand(convictionScore(rowOrScore));
  if (band === "strong") return "High";
  if (band === "constructive") return "Building";
  if (band === "weak") return "Neutral";
  return "Weak";
}

function strengthTone(rowOrScore) {
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

function fmtRawScore(row) {
  return fmtNumber(numericValue(row, "score"), 1);
}

function behaviorDetail(row) {
  const kind = actionKind(row.action);
  const pattern = setupLabel(row.setup);
  const score = convictionScore(row);
  const move = numericValue(row, "day_change_pct");
  const tape = row.psychology || "Mixed tape";
  const mode = row.adaptive_mode || "Mixed mode";
  const note = String(row.notes || "").trim();
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
  if (!state.focusPin) return false;
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
  if (!state.focusPin) return false;
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
  await saveCloudFocusTickers();
  renderWatchlist();
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
      <svg viewBox="0 0 180 104" role="img" aria-label="Trend quality ${strengthLabel(row)}">
        <path class="gauge-track" pathLength="100" d="M 24 84 A 66 66 0 0 1 156 84" />
        <path class="gauge-zone zone-risk" pathLength="100" d="M 24 84 A 66 66 0 0 1 156 84" />
        <path class="gauge-zone zone-weak" pathLength="100" d="M 24 84 A 66 66 0 0 1 156 84" />
        <path class="gauge-zone zone-constructive" pathLength="100" d="M 24 84 A 66 66 0 0 1 156 84" />
        <path class="gauge-zone zone-strong" pathLength="100" d="M 24 84 A 66 66 0 0 1 156 84" />
        <path class="gauge-pointer" d="${pointer}" />
        <circle class="gauge-hub" cx="90" cy="63" r="4.2" />
      </svg>
      <div class="gauge-readout">
        <strong>${escapeHtml(strengthLabel(row))}</strong>
        <small>raw ${escapeHtml(fmtRawScore(row))}</small>
      </div>
    </div>
  `;
}

function renderScoreBreakdown(row) {
  const atrPct = Number(payloadValue(row, "atr_pct"));
  const buyer = Number(payloadValue(row, "buyer_score"));
  const seller = Number(payloadValue(row, "seller_score"));
  const volume = payloadValue(row, "volume_state") || "NEUTRAL";
  const market = payloadValue(row, "market_context") || "UNKNOWN";
  const quality = payloadValue(row, "signal_quality") || strengthLabel(row);
  const personality = payloadValue(row, "personality_type") || "BALANCED";
  const entryQuality = entryQualityLabel(row);
  const entryQualityScore = Number(payloadValue(row, "entry_quality_score") || payloadValue(row, "buy_quality_score"));
  const nextDayBias = payloadValue(row, "next_day_bias") || "NEUTRAL";
  const nextDayScore = Number(payloadValue(row, "next_day_bias_score"));
  const emotion = Number(payloadValue(row, "emotion_score"));
  const location = Number(payloadValue(row, "trend_location_score"));
  const setupContext = Number(payloadValue(row, "setup_context_score"));
  const operatorPressure = payloadValue(row, "operator_state") || payloadValue(row, "operator_pressure") || "NEUTRAL";
  const operatorScore = Number(payloadValue(row, "operator_state_score") ?? payloadValue(row, "operator_pressure_score"));
  const bullTrap = Number(payloadValue(row, "bull_trap_score"));
  const bearTrap = Number(payloadValue(row, "bear_trap_score"));
  const distribution = Number(payloadValue(row, "distribution_score"));
  const absorption = Number(payloadValue(row, "absorption_score"));
  const shortProxy = Number(payloadValue(row, "short_pressure_proxy"));
  const buyTier = payloadValue(row, "buy_tier") || "n/a";
  const freshnessStatus = payloadValue(row, "freshness_status") || "UNKNOWN";
  const dataAge = Number(payloadValue(row, "data_age_days"));
  const feedbackQuality = payloadValue(row, "feedback_quality") || "NO HISTORY";
  const feedbackReturn = Number(payloadValue(row, "feedback_return_pct"));
  const feedbackDrawdown = Number(payloadValue(row, "feedback_max_drawdown_pct"));
  const items = [
    ["Execution Tier", buyTier],
    ["Freshness", `${freshnessStatus}${Number.isFinite(dataAge) ? ` ${fmtNumber(dataAge, 0)}d` : ""}`],
    ["Next Day", `${nextDayBias}${Number.isFinite(nextDayScore) ? ` ${fmtNumber(nextDayScore, 0)}/100` : ""}`],
    ["Operator", `${operatorPressure}${Number.isFinite(operatorScore) ? ` ${fmtNumber(operatorScore, 0)}/100` : ""}`],
    ["Feedback", `${feedbackQuality}${Number.isFinite(feedbackReturn) ? ` ${fmtSignedNumber(feedbackReturn, 1)}%` : ""}${Number.isFinite(feedbackDrawdown) ? ` / DD ${fmtNumber(feedbackDrawdown, 1)}%` : ""}`],
    ["Trend", row.adaptive_mode || "Mixed"],
    ["Candle", buyer >= seller ? `Buyer ${fmtNumber(buyer, 0)}` : `Seller ${fmtNumber(seller, 0)}`],
    ["Volume", volume],
    ["Market", market],
    ["Quality", quality],
    ["Entry Quality", entryQuality
      ? `${entryQuality}${Number.isFinite(entryQualityScore) ? ` ${fmtNumber(entryQualityScore, 0)}/100` : ""}`
      : "n/a"],
    ["Personality", String(personality).replace(/_/g, " ")],
    ["Emotion", Number.isFinite(emotion) ? `${fmtNumber(emotion, 0)}/100` : "n/a"],
    ["MA Location", Number.isFinite(location) ? `${fmtNumber(location, 0)}/100` : "n/a"],
    ["Setup Context", Number.isFinite(setupContext) ? `${fmtNumber(setupContext, 0)}/100` : "n/a"],
    ["Distribution", Number.isFinite(distribution) ? `${fmtNumber(distribution, 0)}/100` : "n/a"],
    ["Absorption", Number.isFinite(absorption) ? `${fmtNumber(absorption, 0)}/100` : "n/a"],
    ["Bull Trap", Number.isFinite(bullTrap) ? `${fmtNumber(bullTrap, 0)}/100` : "n/a"],
    ["Bear Trap", Number.isFinite(bearTrap) ? `${fmtNumber(bearTrap, 0)}/100` : "n/a"],
    ["Short Proxy", Number.isFinite(shortProxy) ? `${fmtNumber(shortProxy, 0)}/100` : "n/a"],
    ["Volatility", Number.isFinite(atrPct) ? `ATR ${fmtNumber(atrPct, 1)}%` : "n/a"]
  ];
  return `
    <div class="score-explainer">
      <div class="score-explainer-head">
        <span>Scanner Read</span>
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
    chips.push(`<span class="change-chip ${moveClass(scoreMove)}">Quality ${fmtSignedNumber(scoreMove, 0)}</span>`);
  }
  return chips.join(" ") || `<span class="change-chip quiet">Steady</span>`;
}

function setStatus(message, ok = true) {
  const status = document.querySelector("#status");
  const runStatus = document.querySelector("#run-status");
  if (status) status.textContent = message;
  if (runStatus) runStatus.classList.toggle("bad", !ok);
}

function runHealthSummary(runInfo) {
  if (!runInfo) return "";
  const parts = [];
  const failed = Number(runInfo.symbols_failed || 0);
  const stale = Number(runInfo.symbols_stale_cache || 0);
  const liveOk = runInfo.live_access_ok;
  if (liveOk === false) parts.push("source degraded");
  if (stale) parts.push(`${stale} cached`);
  if (failed) parts.push(`${failed} failed`);
  if (runInfo.scanner_version) parts.push(`scanner ${runInfo.scanner_version}`);
  return parts.length ? ` · ${parts.join(" · ")}` : "";
}

function renderRunHealthPanel(runInfo, rows = []) {
  const panel = document.querySelector("#run-health-panel");
  if (!panel) return;
  panel.innerHTML = "";
  panel.hidden = true;
}

function runHealthStatus(runInfo, rows = []) {
  const failed = Number(runInfo?.symbols_failed || 0);
  const stale = Number(runInfo?.symbols_stale_cache || 0);
  const staleBlocks = Number(runInfo?.payload?.stale_execution_blocks || 0);
  const pendingGates = auditGatePendingCount(rows);
  const analyzed = Number(runInfo?.symbols_analyzed || rows.length || 0);
  const total = Number(runInfo?.symbols_total || rows.length || 0);
  const liveOk = runInfo?.live_access_ok;
  const latestData = runInfo?.latest_data_date || dataDateSummary(rows).replace(/^Market data:\s*/, "") || "unknown";
  const hasRows = rows.length > 0 || analyzed > 0;
  const hasIssue = liveOk === false || failed > 0 || stale > 0 || pendingGates > 0 || staleBlocks > 0;
  const tone = !hasRows || staleBlocks > 0 ? "bad" : hasIssue ? "warn" : "ok";
  const label = tone === "bad" ? "Execution blocked" : tone === "warn" ? "Data caution" : "Live data healthy";
  const caveats = [
    staleBlocks ? `${staleBlocks} stale-data blocks` : "",
    pendingGates ? `${pendingGates} execution proof pending` : "",
    stale ? `${stale} cached` : "",
    failed ? `${failed} failed` : "",
    liveOk === false ? "source degraded" : "",
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
    const stalePrefix = isStaleMarketDate(latest, rows) ? "Market data may lag · " : "";
    const pendingGates = auditGatePendingCount(rows);
    const gateSummary = pendingGates ? ` · ${pendingGates} execution proof pending` : "";
    runStatus.textContent = `${stalePrefix}Updated ${latest} · ${marketData}${runHealthSummary(runInfo)}${gateSummary}`;
    runStatus.classList.toggle("warn", Boolean(
      runInfo && (
        runInfo.live_access_ok === false
        || Number(runInfo.symbols_failed || 0)
        || Number(runInfo.symbols_stale_cache || 0)
        || Number(runInfo.payload?.stale_execution_blocks || 0)
        || auditGatePendingCount(rows)
      )
    ));
    runStatus.classList.toggle("bad", Boolean(runInfo && Number(runInfo.payload?.stale_execution_blocks || 0)));
  }
  if (status) status.textContent = "";
  if (disclaimer) disclaimer.textContent = APP_DISCLAIMER;
  if (runStatus && !(runInfo && Number(runInfo.payload?.stale_execution_blocks || 0))) runStatus.classList.remove("bad");
  renderRunHealthPanel(runInfo, rows);
}

function fallbackAgeDays(runDate) {
  if (!runDate) return Infinity;
  const parsed = new Date(`${runDate}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return Infinity;
  return Math.floor((Date.now() - parsed.getTime()) / 86400000);
}

function assertFreshStaticFallback(runDate) {
  if (fallbackAgeDays(runDate) > STATIC_FALLBACK_MAX_AGE_DAYS) {
    throw new Error("Live data is unavailable and the offline archive is too old to display safely.");
  }
}

async function fetchStaticJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) throw new Error(`Static fallback returned HTTP ${response.status}.`);
  return response.json();
}

function parseCsvLine(line) {
  const values = [];
  let value = "";
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const next = line[index + 1];
    if (quoted && char === "\"" && next === "\"") {
      value += "\"";
      index += 1;
    } else if (char === "\"") {
      quoted = !quoted;
    } else if (!quoted && char === ",") {
      values.push(value);
      value = "";
    } else {
      value += char;
    }
  }
  values.push(value);
  return values;
}

function parseCsv(text) {
  const lines = String(text || "").replace(/\r\n/g, "\n").replace(/\r/g, "\n").split("\n").filter(Boolean);
  const headers = parseCsvLine(lines.shift() || "");
  return lines.map((line) => {
    const values = parseCsvLine(line);
    return headers.reduce((row, header, index) => {
      row[header] = values[index] ?? "";
      return row;
    }, {});
  });
}

async function loadStaticLatestRows() {
  const fallback = await fetchStaticJson("./data/latest.json");
  assertFreshStaticFallback(fallback.run_date);
  return {
    latest: fallback.run_date,
    previous: "",
    rows: (fallback.rows || []).map((row) => ({
      ...row,
      run_date: row.run_date || fallback.run_date,
      data_date: row.data_date || row.date,
      name: displaySecurityName(row.name, row.ticker) || row.name || row.ticker,
    })),
    previousRows: [],
  };
}

function uniqueHistoryDateCount(rows) {
  return new Set(rows.map((row) => row.history_date || row.data_date || row.date).filter(Boolean)).size;
}

async function loadPublishedTickerHistory(ticker) {
  const response = await fetch(`${PUBLISHED_HISTORY_CSV_URL}?v=${Date.now()}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`Published history returned HTTP ${response.status}.`);
  return parseCsv(await response.text())
    .filter((row) => normaliseTicker(row.ticker) === ticker)
    .map((row) => ({
      ...row,
      history_date: row.history_date || row.data_date || row.date || row.run_date,
      data_date: row.data_date || row.date || row.history_date,
      name: displaySecurityName(row.name, row.ticker) || row.name || row.ticker,
      payload: row,
    }))
    .sort((a, b) => String(b.history_date).localeCompare(String(a.history_date)));
}

async function loadStaticTickerHistory(ticker) {
  const fallback = await fetchStaticJson("./data/history.json");
  const rawRows = fallback.by_ticker?.[ticker] || fallback.by_ticker?.[ticker.replace(".", "-")] || (fallback.rows || []).filter((row) => row.ticker === ticker);
  let rows = rawRows
    .map((row) => ({
      ...row,
      history_date: row.data_date || row.date || row.run_date,
      data_date: row.data_date || row.date,
      name: displaySecurityName(row.name, row.ticker) || row.name || row.ticker,
      payload: row,
    }))
    .sort((a, b) => String(b.history_date).localeCompare(String(a.history_date)));
  if (uniqueHistoryDateCount(rows) < 5) {
    rows = await loadPublishedTickerHistory(ticker);
  }
  if (uniqueHistoryDateCount(rows) < 5) {
    throw new Error("Live history is unavailable and the published archive does not have enough history for this ticker.");
  }
  const fallbackRunDate = fallback.run_date || rows.map((row) => row.run_date).filter(Boolean).sort().at(-1) || rows[0]?.history_date || "";
  assertFreshStaticFallback(fallbackRunDate);
  return {
    latest: rows[0]?.run_date || fallbackRunDate,
    name: rows[0]?.name || "",
    rows,
  };
}

function renderWatchlistCell(row, key) {
  if (key === "ticker") {
    return `
      <span class="ticker-cell">
        <button class="focus-toggle ${isFocusTicker(row.ticker) ? "active" : ""}" type="button" data-focus-ticker="${escapeHtml(row.ticker)}" aria-label="${isFocusTicker(row.ticker) ? "Remove" : "Add"} ${escapeHtml(row.ticker)} from Focus List">★</button>
        <a class="ticker-link" href="./history.html?ticker=${encodeURIComponent(row.ticker)}">${escapeHtml(row.ticker)}</a>
      </span>
    `;
  }
  if (key === "name") {
    return escapeHtml(displaySecurityName(row.name, row.ticker) || row.name || row.ticker);
  }
  if (key === "action") {
    const kind = actionKind(row.action);
    return `
      <span class="signal-stack">
        <span class="badge ${kind}">${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>
        ${renderEntryQualityPill(row)}
      </span>
    `;
  }
  if (key === "setup") {
    return `<span class="badge pattern-pill pattern-${setupTone(row.setup)}">${escapeHtml(setupLabel(row.setup))}</span>`;
  }
  if (key === "buy_tier") return renderBuyTier(row);
  if (key === "next_day_bias") return renderNextDayBias(row);
  if (key === "operator_state") return renderOperatorPressure(row);
  if (key === "next_day_plan") return `<span class="behavior-detail">${escapeHtml(payloadValue(row, "next_day_plan") || "")}</span>`;
  if (key === "notes") {
    return `<span class="behavior-detail">${escapeHtml(behaviorDetail(row))}</span>`;
  }
  if (key === "score") return `<span class="badge conviction-pill score-${strengthTone(row)}">${escapeHtml(strengthLabel(row))}</span>`;
  if (key === "day_change_pct") return renderMovePct(row[key]);
  if (key === "risk_pct_to_stop") return escapeHtml(fmtNumber(payloadValue(row, "risk_pct_to_stop"), 1));
  if (key === "position_value_1k_risk") return escapeHtml(fmtNumber(payloadValue(row, "position_value_1k_risk"), 0));
  if (["close", "entry_est", "stop_est", "target_est"].includes(key)) return escapeHtml(fmtNumber(row[key], 2));
  return escapeHtml(row[key]);
}

function searchableRowText(row) {
  return [
    ...WATCHLIST_COLUMNS.map(([key]) => row[key]),
    ACTION_LABELS[row.action] || row.action,
    setupLabel(row.setup),
    strengthLabel(row),
    entryQualityLabel(row),
    payloadValue(row, "buy_tier"),
    payloadValue(row, "execution_plan"),
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

function renderMobileWatchlistSummary(row) {
  const kind = actionKind(row.action);
  const company = displaySecurityName(row.name, row.ticker) || row.name || row.ticker;
  const pattern = setupLabel(row.setup);
  const strength = strengthLabel(row);
  const entry = entryQualityLabel(row);
  const secondary = [entry, strength, pattern && pattern !== "None" ? pattern : ""].filter(Boolean).join(" · ");
  return `
    <span class="mobile-watch-shell">
      <a class="mobile-watch-row" href="./history.html?ticker=${encodeURIComponent(row.ticker)}">
        <span class="mobile-watch-main">
          <strong>${escapeHtml(row.ticker)}</strong>
          <span>${escapeHtml(company)}</span>
          <span class="mobile-watch-signal">
            <span class="badge ${kind}">${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>
            <span>${escapeHtml(secondary)}</span>
          </span>
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
  const headline = `${actionTotal} actionable names: ${counts.buy || 0} BUY, ${counts.setup || 0} BUILDING`;
  const freshText = tickerList(fresh);
  const upgradesText = tickerList(upgrades);
  const moverText = tickerList(priceMovers, 2);
  const riskText = exits.length ? tickerList(exits, 2) : `${exitCount} exit-risk`;

  panel.innerHTML = `
    <div class="brief-card">
      <div class="brief-copy">
        <span class="brief-kicker">Daily Brief</span>
        <h2>${escapeHtml(headline)}</h2>
        <div class="brief-points">
          <span><b>Fresh</b> ${escapeHtml(freshText)}</span>
          <span><b>Upgraded</b> ${escapeHtml(upgradesText)}</span>
          <span><b>Movers</b> ${escapeHtml(moverText)}</span>
          <span><b>Risk</b> ${escapeHtml(riskText)}</span>
        </div>
        ${renderTrafficHealth(state.runInfo, state.rows)}
      </div>
      <div class="brief-actions">
        ${topBuy ? `<a class="brief-primary" href="./history.html?ticker=${encodeURIComponent(topBuy.ticker)}">Review ${escapeHtml(topBuy.ticker)}</a>` : ""}
        <button class="brief-secondary" type="button" data-filter-brief="buy">Show BUY</button>
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
    <a class="focus-item tone-${kind}" href="./history.html?ticker=${encodeURIComponent(row.ticker)}">
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
    focusItem(strongest, "Buy"),
    focusItem(building, "Building"),
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

function changedTodayCard({ row, previous, pricePct }, duplicate = false) {
  const signal = ACTION_LABELS[row.action] || row.action || "Signal";
  return `
    <a class="change-card tone-${actionKind(row.action)}" href="./history.html?ticker=${encodeURIComponent(row.ticker)}"${duplicate ? ' aria-hidden="true" tabindex="-1"' : ""}>
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
      ${moversSectionHeading("Signal Changes", runDate)}
      <div class="empty compact-empty">No major scanner changes versus the previous run.</div>
    `;
    return;
  }

  const rolling = changes.length > 1;
  const cards = changes.map((change) => changedTodayCard(change)).join("");
  const duplicateCards = rolling ? changes.map((change) => changedTodayCard(change, true)).join("") : "";
  panel.innerHTML = `
    ${moversSectionHeading("Signal Changes", runDate)}
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
      ${moversSectionHeading("Price Movers", runDate)}
      <div class="empty compact-empty">No large current-day price moves.</div>
    `;
    return;
  }

  const rolling = movers.length > 1;
  const cards = movers.map((change) => changedTodayCard(change)).join("");
  const duplicateCards = rolling ? movers.map((change) => changedTodayCard(change, true)).join("") : "";
  panel.innerHTML = `
    ${moversSectionHeading("Price Movers", runDate)}
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
      ${moversSectionHeading("Focus List", runDate)}
      ${focusControls}
      <div class="focus-empty">
        <span>${state.focusPin ? "Star tickers in the watchlist to keep your personal list here." : "Unlock first, then star tickers from the Watchlist."}</span>
      </div>
    `;
    return;
  }

  panel.innerHTML = `
    ${moversSectionHeading("Focus List", runDate)}
    ${focusControls}
    <div class="focus-list-grid">
      ${focusRows.map((row) => {
        const kind = actionKind(row.action);
        const previous = previousRowFor(row);
        return `
          <div class="focus-list-item tone-${kind}">
            <a class="focus-list-link" href="./history.html?ticker=${encodeURIComponent(row.ticker)}">
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

function renderWatchlist() {
  const counts = { buy: 0, continue: 0, setup: 0, watch: 0, exit: 0, avoid: 0 };
  state.rows.forEach((row) => {
    counts[actionKind(row.action)] += 1;
  });
  renderCards(counts);
  renderDailyBrief(counts);
  renderTodayFocus();
  renderSignalChanges();
  renderPriceMovers();
  renderFocusList();

  const needle = state.query.trim().toLowerCase();
  const searchActive = Boolean(needle);
  document.body.classList.toggle("search-active", searchActive);
  const [sortKey, direction] = state.sort.split("-");
  const multiplier = direction === "asc" ? 1 : -1;
  state.visibleRows = state.rows
    .filter((row) => state.filter === "all" || actionKind(row.action) === state.filter)
    .filter((row) => !needle || searchableRowText(row).includes(needle))
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

  document.querySelector("#watchlist-head").innerHTML = `<tr>${WATCHLIST_COLUMNS.map(([, label]) => `<th>${label}</th>`).join("")}</tr>`;
  document.querySelector("#watchlist-body").innerHTML = state.visibleRows.map((row) => `
    <tr class="row-${actionKind(row.action)}" style="--score-pct: ${fmtConviction(row)}%">
      ${WATCHLIST_COLUMNS.map(([key]) => `<td class="${["score", "operator_state_score", "operator_pressure_score", "close", "day_change_pct", "entry_est", "stop_est", "target_est", "risk_pct_to_stop", "position_value_1k_risk"].includes(key) ? "num" : ""}">${renderWatchlistCell(row, key)}</td>`).join("")}
      <td class="mobile-summary">${renderMobileWatchlistSummary(row)}</td>
    </tr>
  `).join("");
  document.querySelectorAll("[data-focus-ticker]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      toggleFocusTicker(button.dataset.focusTicker);
    });
  });
  attachFocusControls();
  document.querySelector("#count").textContent = `${state.visibleRows.length} / ${state.rows.length} shown`;
  const mobileCount = document.querySelector("#mobile-search-count");
  if (mobileCount) mobileCount.textContent = searchActive ? `${state.visibleRows.length} result${state.visibleRows.length === 1 ? "" : "s"}` : `${state.visibleRows.length} shown`;
  document.querySelectorAll("[data-mobile-filter]").forEach((button) => {
    button.classList.toggle("active", button.dataset.mobileFilter === state.filter);
  });
  const watchlistTitle = document.querySelector(".watchlist-heading span:not(.section-date)");
  if (watchlistTitle) watchlistTitle.textContent = searchActive ? "Search Results" : "Watchlist";
  document.querySelector("#empty").classList.toggle("hidden", state.visibleRows.length > 0);
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
  const updateSearch = (value, shouldScroll = true) => {
    state.query = value;
    syncSearchClear();
    renderWatchlist();
    if (shouldScroll && state.query.trim()) scrollToWatchlistResults();
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
      renderWatchlist();
      scrollToWatchlistResults();
    });
  });
  document.querySelector("#sort").addEventListener("change", (event) => {
    state.sort = event.target.value;
    renderWatchlist();
  });
  syncSearchClear();
  initTabNavigation();
  try {
    const latestPayload = await appApiFetch("/api/watchlist/latest", { fresh: true, ttl: 0 });
    state.rows = (latestPayload.rows || [])
      .map((row) => ({ ...row, name: displaySecurityName(row.name, row.ticker) || row.name || row.ticker }));
    state.previousRows = latestPayload.previousRows || [];
    state.previousByTicker = rowByTicker(state.previousRows);
    if (!state.rows.length) {
      const fallback = await loadStaticLatestRows();
      state.rows = fallback.rows;
      state.previousRows = fallback.previousRows;
      state.previousByTicker = rowByTicker(state.previousRows);
      state.runInfo = fallback.runInfo || null;
      await loadCloudFocusTickers();
      const marketData = dataDateSummary(state.rows);
      setRefreshSummary(fallback.latest, `${marketData} · static fallback`, state.rows);
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
      setRefreshSummary(fallback.latest, `${marketData} · static fallback`, state.rows);
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
  panel.innerHTML = `
    <div class="latest-card tone-${actionKind(latest.action)}">
      <div class="latest-head">
        <span class="latest-label">Current read</span>
        <span class="badge ${actionKind(latest.action)}">${escapeHtml(ACTION_LABELS[latest.action] || latest.action)}</span>
      </div>
      <div class="latest-metrics">
        <div><span>Close</span><strong>${fmtNumber(latest.close, 2)} ${renderMovePct(latest.day_change_pct)}</strong></div>
        <div><span>Trend Quality</span><strong>${escapeHtml(strengthLabel(latest))}</strong></div>
        <div><span>Pattern</span><strong>${escapeHtml(setupLabel(latest.setup))}</strong></div>
        <div><span>Ref Zone</span><strong>${fmtNumber(latest.entry_est, 2)}</strong></div>
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
        <title>${escapeHtml(row.history_date)} · trend quality ${escapeHtml(strengthLabel(row))} · raw rank ${fmtNumber(row.score, 1)} · close ${fmtNumber(row.close, 2)}</title>
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
        <span>Optional chart</span>
        <strong>Daily scanner bars</strong>
      </summary>
      <div class="chart-card">
      <div class="chart-heading">
        <div>
          <span>Trend Quality Detail</span>
          <strong>Daily trend-quality bars</strong>
          <p class="chart-note">Bars show normalized scanner trend quality. The thin dotted line shows close-price direction, scaled only for shape comparison.</p>
        </div>
        <div class="chart-latest">
          <span>Latest</span>
          <strong>${escapeHtml(strengthLabel(latest))}</strong>
        </div>
      </div>
      <svg class="history-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(state.ticker)} 30-day trend quality and price chart">
        <rect x="${pad.left}" y="${pad.top}" width="${plotWidth}" height="${plotHeight}" class="plot-bg" />
        ${gridLines}
        ${scoreBars}
        <path d="${pricePath}" class="price-line" />
        ${dateTicks}
      </svg>
      <div class="chart-legend">
        <span><i class="legend-score"></i> daily quality bars</span>
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
  const previousByDate = new Map(chronological.map((row, index) => [row.history_date, chronological[index - 1] || null]));
  const recentRows = state.historyRows.slice(0, Math.min(6, state.historyRows.length));
  const lookbackRows = state.historyRows.slice(recentRows.length);

  timeline.innerHTML = `
    <h3>Recent Behavior</h3>
    ${recentRows.map((row, index) => `
      <div class="moment-card tone-${actionKind(row.action)}">
        <div class="moment-date">${index === 0 ? "Latest" : escapeHtml(fmtCompactDate(row.history_date))}</div>
        <div class="moment-body">
          <span class="badge ${actionKind(row.action)}">${escapeHtml(ACTION_LABELS[row.action] || row.action)}</span>
          <div class="change-chips">${renderHistoryChangeChips(row, previousByDate.get(row.history_date))}</div>
          <p class="subtle">Close: ${fmtNumber(row.close, 2)} ${renderMovePct(row.day_change_pct)} · Trend Quality: ${escapeHtml(strengthLabel(row))} · Pattern: ${escapeHtml(setupLabel(row.setup))}</p>
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
            <strong>${escapeHtml(strengthLabel(row))}</strong>
          </div>
          <div class="lookback-meta">
            <span>${escapeHtml(setupLabel(row.setup))}</span>
            ${renderMovePct(row.day_change_pct)}
          </div>
          <div class="bar"><span class="score-${scoreBand(convictionScore(row))}" style="width: ${Math.max(2, convictionScore(row))}%"></span></div>
          <div class="lookback-price">
            <strong>${fmtNumber(row.close, 2)}</strong>
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
  document.querySelector("#company-context").innerHTML = `
    <h2>Company Context</h2>
    <div class="company-context-empty subtle">Loading company context...</div>
  `;
  document.title = state.ticker;
  window.history.replaceState(null, "", `./history.html?ticker=${encodeURIComponent(state.ticker)}`);
  setStatus("Loading ticker history...");
  document.querySelector("#run-status").textContent = "No history loaded";
  document.querySelector("#run-status").classList.add("bad");
  try {
    const tickerPayload = await appApiFetch(`/api/ticker/${encodeURIComponent(state.ticker)}`, { fresh: true, ttl: 0 });
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
      setRefreshSummary(fallback.latest, `${marketData} · static fallback`, state.historyRows);
      renderCompanyBrief({});
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
