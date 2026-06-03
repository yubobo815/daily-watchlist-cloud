const SUPABASE_CONFIG = {
  url: process.env.SUPABASE_URL || "https://lzuwwiabrnebboxriemu.supabase.co",
  anonKey: process.env.SUPABASE_ANON_KEY || process.env.SUPABASE_KEY || "sb_publishable_tCTML11CHw0fwtYWD9_I-Q_ne39UiHw",
};

const READABLE_TABLES = new Set([
  "watchlist_snapshots",
  "watchlist_behavior_history",
  "watchlist_refresh_runs",
]);

function parseSupabasePath(path) {
  const [table, query = ""] = path.split("?", 2);
  if (!READABLE_TABLES.has(table) || !query) return null;
  const params = new URLSearchParams(query);
  const limit = Number(params.get("limit") || "0");
  if (limit && limit > 1200) params.set("limit", "1200");
  return `${table}?${params.toString()}`;
}

export default async function handler(request, response) {
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
