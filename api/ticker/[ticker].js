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
const { staticTickerPayload } = require("../_static_data");

function withTimeout(promise, milliseconds, fallback) {
  return Promise.race([
    promise,
    new Promise((resolve) => {
      setTimeout(() => resolve(fallback), milliseconds);
    }),
  ]);
}

module.exports = async function handler(request, response) {
  const ticker = normalizeTicker(request.query?.ticker);
  if (!isValidTicker(ticker)) {
    response.status(400).json({ error: "Invalid ticker." });
    return;
  }

  try {
    const runRows = await supabaseSelect(`watchlist_behavior_history?select=run_date&ticker=eq.${encodeFilterValue(ticker)}&order=run_date.desc&limit=1`);
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
    const rows = historyRows.map(rowDto);
    if (snapshot && rows[0]) {
      rows[0] = {
        ...snapshot,
        ...rows[0],
        name: snapshot.name || rows[0].name,
        data_date: snapshot.data_date || rows[0].data_date,
        payload: {
          ...(snapshot.payload || {}),
          ...(rows[0].payload || {}),
        },
      };
    }

    const profileReady = profile && Object.keys(profile).length > 0;
    response.setHeader("Cache-Control", profileReady
      ? "public, s-maxage=90, stale-while-revalidate=300"
      : "public, s-maxage=20, stale-while-revalidate=90");
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
    response.setHeader("Cache-Control", "public, s-maxage=30, stale-while-revalidate=120");
    response.status(200).json(staticTickerPayload(ticker, profile));
  }
};
