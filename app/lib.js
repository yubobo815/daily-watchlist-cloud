export const ACTION_LABELS = {
  "BUY CANDIDATE": "BUY",
  "SETUP FORMING": "SETUP",
  "WATCH TREND": "WATCH",
  "EXIT PRESSURE": "EXIT",
  "WAIT": "WAIT",
  "WAIT / AVOID": "AVOID"
};

export const SETUP_LABELS = {
  "BREAKOUT BUY": "BO",
  "MOMENTUM BUY": "MOM",
  "PULLBACK BUY": "PB",
  "EARLY PULLBACK BUY": "EPB",
  "REVERSAL BUY": "REV",
  "NONE": "-"
};

export function actionKind(action) {
  return {
    "BUY CANDIDATE": "buy",
    "SETUP FORMING": "setup",
    "WATCH TREND": "watch",
    "EXIT PRESSURE": "exit",
    "WAIT": "avoid",
    "WAIT / AVOID": "avoid"
  }[action] || "avoid";
}

export function fmtNumber(value, digits = 1) {
  if (value === null || value === undefined || value === "") return "";
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(digits) : String(value);
}

export function csvEscape(value) {
  const text = value === null || value === undefined ? "" : String(value);
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

export function downloadCsv(filename, rows, columns) {
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

export async function getSupabaseConfig() {
  const envConfig = {
    url: process.env.NEXT_PUBLIC_SUPABASE_URL || "",
    anonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ""
  };
  if (envConfig.url && envConfig.anonKey) return envConfig;

  if (typeof window !== "undefined" && window.WATCHLIST_SUPABASE?.url && window.WATCHLIST_SUPABASE?.anonKey) {
    return window.WATCHLIST_SUPABASE;
  }

  if (typeof window === "undefined") return null;

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

export async function supabaseFetch(path) {
  const config = await getSupabaseConfig();
  if (!config) {
    throw new Error("Supabase browser config is missing. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in Vercel.");
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

export async function latestRunDate() {
  const rows = await supabaseFetch("watchlist_snapshots?select=run_date&order=run_date.desc&limit=1");
  return rows[0]?.run_date || null;
}
