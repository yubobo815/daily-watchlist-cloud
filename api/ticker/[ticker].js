const {
  encodeFilterValue,
  HISTORY_FIELDS,
  isValidTicker,
  normalizeTicker,
  rowDto,
  runInfo,
  selectList,
  SNAPSHOT_FIELDS,
  supabaseSelect,
} = require("../_supabase");
const { fetchCompanyProfile } = require("../company");
const { publishedTickerPayload } = require("../_published_data");

function withTimeout(promise, milliseconds, fallback) {
  return Promise.race([
    promise,
    new Promise((resolve) => {
      setTimeout(() => resolve(fallback), milliseconds);
    }),
  ]);
}

function mergeSnapshotIntoLatestHistory(snapshot, historyRow) {
  return {
    ...historyRow,
    ...snapshot,
    name: snapshot.name || historyRow.name,
    data_date: snapshot.data_date || historyRow.data_date,
    adjusted_score: snapshot.adjusted_score ?? snapshot.payload?.adjusted_score ?? historyRow.adjusted_score,
    payload: {
      ...(historyRow.payload || {}),
      ...(snapshot.payload || {}),
    },
  };
}

async function handler(request, response) {
  const ticker = normalizeTicker(request.query?.ticker);
  if (!isValidTicker(ticker)) {
    response.status(400).json({ error: "Invalid ticker." });
    return;
  }

  try {
    // The list page is snapshot-led, so detail must use the identical current run.
    const runRows = await supabaseSelect("watchlist_snapshots?select=run_date&order=run_date.desc&limit=1");
    const latest = runRows[0]?.run_date;
    if (!latest) {
      response.status(404).json({ error: `No 30-day history found for ${ticker}.` });
      return;
    }

    const [snapshotRows, historyRows, latestRunInfo, profile] = await Promise.all([
      supabaseSelect(`watchlist_snapshots?select=${selectList(SNAPSHOT_FIELDS)}&ticker=eq.${encodeFilterValue(ticker)}&run_date=eq.${encodeFilterValue(latest)}&limit=1`),
      supabaseSelect(`watchlist_behavior_history?select=${selectList(HISTORY_FIELDS)}&ticker=eq.${encodeFilterValue(ticker)}&run_date=eq.${encodeFilterValue(latest)}&order=history_date.desc`),
      runInfo(latest),
      withTimeout(fetchCompanyProfile(ticker).catch(() => ({})), 1800, {}),
    ]);

    const snapshot = snapshotRows[0] ? rowDto(snapshotRows[0]) : null;
    const rows = historyRows.map((row) => rowDto(row, { historical: true }));
    if (snapshot && rows[0]) {
      rows[0] = mergeSnapshotIntoLatestHistory(snapshot, rows[0]);
    }

    const profileReady = profile && Object.keys(profile).length > 0;
    response.setHeader("Cache-Control", profileReady
      ? "public, max-age=0, s-maxage=30, stale-while-revalidate=60"
      : "public, max-age=0, s-maxage=10, stale-while-revalidate=20");
    response.status(200).json({
      ticker,
      latest,
      snapshot,
      historyRows: rows,
      runInfo: latestRunInfo,
      profile,
    });
  } catch (error) {
    console.error(error);
    const profile = await withTimeout(fetchCompanyProfile(ticker).catch(() => ({})), 1800, {});
    response.setHeader("Cache-Control", "no-store");
    response.status(200).json(await publishedTickerPayload(ticker, profile));
  }
}

module.exports = handler;
module.exports.mergeSnapshotIntoLatestHistory = mergeSnapshotIntoLatestHistory;
