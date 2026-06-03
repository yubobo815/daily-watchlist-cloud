const SUPABASE_CONFIG = {
  url: process.env.SUPABASE_URL || "",
  anonKey: process.env.SUPABASE_ANON_KEY || "",
};

const ALLOWED_QUERY_KEYS = new Set(["select", "run_date", "ticker", "order", "limit"]);
const MAX_LIMIT = 1200;
const TABLE_SELECTS = {
  watchlist_snapshots: new Set(["*", "run_date", "name,payload"]),
  watchlist_behavior_history: new Set(["*", "run_date"]),
  watchlist_refresh_runs: new Set(["*"]),
};
const TABLE_ORDERS = {
  watchlist_snapshots: new Set(["score.desc", "run_date.desc"]),
  watchlist_behavior_history: new Set(["run_date.desc", "history_date.desc"]),
  watchlist_refresh_runs: new Set(["run_date.desc"]),
};

function allowedSelect(table, value) {
  return TABLE_SELECTS[table]?.has(value);
}

function normalisePositiveLimit(value) {
  const limit = Number(value || "0");
  if (!Number.isInteger(limit) || limit < 1) return "";
  return String(Math.min(limit, MAX_LIMIT));
}

function parseSupabasePath(path) {
  const [table, query = ""] = path.split("?", 2);
  if (!TABLE_SELECTS[table] || !query) return null;
  const params = new URLSearchParams(query);
  if (!allowedSelect(table, params.get("select") || "")) return null;
  for (const key of params.keys()) {
    if (!ALLOWED_QUERY_KEYS.has(key)) return null;
  }
  if (params.has("limit")) {
    const limit = normalisePositiveLimit(params.get("limit"));
    if (!limit) return null;
    params.set("limit", limit);
  }
  const order = params.get("order");
  if (order && !TABLE_ORDERS[table]?.has(order)) return null;
  const ticker = params.get("ticker");
  if (ticker && !/^eq\.[A-Z0-9.^-]{1,12}$/.test(ticker)) return null;
  const runDate = params.get("run_date");
  if (runDate && !/^eq\.\d{4}-\d{2}-\d{2}$/.test(runDate)) return null;
  return `${table}?${params.toString()}`;
}

export default async function handler(request, response) {
  if (!SUPABASE_CONFIG.url || !SUPABASE_CONFIG.anonKey) {
    response.status(500).json({ error: "Supabase server config is missing." });
    return;
  }

  const path = String(request.query.path || "");
  const safePath = parseSupabasePath(path);
  if (!safePath) {
    response.status(400).json({ error: "Unsupported Supabase path." });
    return;
  }

  const baseUrl = SUPABASE_CONFIG.url.replace(/\/$/, "");
  const result = await fetch(`${baseUrl}/rest/v1/${safePath}`, {
    headers: {
      apikey: SUPABASE_CONFIG.anonKey,
      Authorization: `Bearer ${SUPABASE_CONFIG.anonKey}`,
    },
  });

  const text = await result.text();
  response.setHeader("Cache-Control", "public, s-maxage=60, stale-while-revalidate=300");
  response.status(result.status).send(text);
}
