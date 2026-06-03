const SUPABASE_CONFIG = {
  url: process.env.SUPABASE_URL || "https://lzuwwiabrnebboxriemu.supabase.co",
  anonKey: process.env.SUPABASE_ANON_KEY || process.env.SUPABASE_KEY || "sb_publishable_tCTML11CHw0fwtYWD9_I-Q_ne39UiHw",
};

export default async function handler(request, response) {
  const path = String(request.query.path || "");
  if (!path.startsWith("watchlist_snapshots?")) {
    response.status(400).json({ error: "Unsupported Supabase path." });
    return;
  }

  const baseUrl = SUPABASE_CONFIG.url.replace(/\/$/, "");
  const result = await fetch(`${baseUrl}/rest/v1/${path}`, {
    headers: {
      apikey: SUPABASE_CONFIG.anonKey,
      Authorization: `Bearer ${SUPABASE_CONFIG.anonKey}`,
    },
  });

  const text = await result.text();
  response.setHeader("Cache-Control", "no-store");
  response.status(result.status).send(text);
}
