const SUPABASE_CONFIG = {
  url: process.env.SUPABASE_URL || "",
  anonKey: process.env.SUPABASE_ANON_KEY || "",
};

function assertSupabaseConfig() {
  if (!SUPABASE_CONFIG.url || !SUPABASE_CONFIG.anonKey) {
    throw new Error("Supabase server config is missing.");
  }
}

function supabaseBaseUrl() {
  return SUPABASE_CONFIG.url.replace(/\/$/, "");
}

async function supabaseSelect(path) {
  assertSupabaseConfig();
  const response = await fetch(`${supabaseBaseUrl()}/rest/v1/${path}`, {
    headers: {
      apikey: SUPABASE_CONFIG.anonKey,
      Authorization: `Bearer ${SUPABASE_CONFIG.anonKey}`,
    },
  });
  const text = await response.text();
  if (!response.ok) {
    throw new Error(`Supabase returned HTTP ${response.status}: ${text.slice(0, 300)}`);
  }
  return text ? JSON.parse(text) : [];
}

function encodeFilterValue(value) {
  return encodeURIComponent(String(value));
}

function normalizeTicker(value) {
  return String(value || "").trim().toUpperCase().replace("BRK.B", "BRK-B");
}

function isValidTicker(value) {
  return /^[A-Z0-9.^-]{1,12}$/.test(value);
}

function sortRows(rows) {
  return [...rows].sort((a, b) => {
    const aScore = Number(a.adjusted_score ?? a.payload?.adjusted_score ?? a.score ?? 0);
    const bScore = Number(b.adjusted_score ?? b.payload?.adjusted_score ?? b.score ?? 0);
    if (bScore !== aScore) return bScore - aScore;
    return String(a.ticker || "").localeCompare(String(b.ticker || ""));
  });
}

async function recentRunDates(limit = 2) {
  const dates = [];
  try {
    const runRows = await supabaseSelect(`watchlist_refresh_runs?select=run_date&order=run_date.desc&limit=${limit}`);
    runRows.forEach((row) => {
      if (row.run_date && !dates.includes(row.run_date)) dates.push(row.run_date);
    });
  } catch {
    // Older deployments may not have refresh run rows yet.
  }
  if (dates.length >= limit) return dates.slice(0, limit);

  const snapshotRows = await supabaseSelect("watchlist_snapshots?select=run_date&order=run_date.desc&limit=600");
  snapshotRows.forEach((row) => {
    if (row.run_date && !dates.includes(row.run_date)) dates.push(row.run_date);
  });
  return dates.slice(0, limit);
}

async function runInfo(runDate) {
  if (!runDate) return null;
  try {
    const rows = await supabaseSelect(`watchlist_refresh_runs?select=*&run_date=eq.${encodeFilterValue(runDate)}&limit=1`);
    return rows[0] || null;
  } catch {
    return null;
  }
}

module.exports = {
  encodeFilterValue,
  isValidTicker,
  normalizeTicker,
  recentRunDates,
  runInfo,
  sortRows,
  supabaseSelect,
};
