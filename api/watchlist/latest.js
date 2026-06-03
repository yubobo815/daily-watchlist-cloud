const {
  encodeFilterValue,
  recentRunDates,
  runInfo,
  sortRows,
  supabaseSelect,
} = require("../_supabase");

module.exports = async function handler(request, response) {
  try {
    const [latest, previous] = await recentRunDates(2);
    if (!latest) {
      response.setHeader("Cache-Control", "public, s-maxage=30, stale-while-revalidate=120");
      response.status(200).json({
        latest: "",
        previous: "",
        rows: [],
        previousRows: [],
        runInfo: null,
      });
      return;
    }

    const latestRowsPromise = supabaseSelect(`watchlist_snapshots?select=*&run_date=eq.${encodeFilterValue(latest)}&order=score.desc`);
    const previousRowsPromise = previous
      ? supabaseSelect(`watchlist_snapshots?select=*&run_date=eq.${encodeFilterValue(previous)}&order=score.desc`)
      : Promise.resolve([]);
    const [latestRows, previousRows, latestRunInfo] = await Promise.all([
      latestRowsPromise,
      previousRowsPromise,
      runInfo(latest),
    ]);

    response.setHeader("Cache-Control", "public, s-maxage=45, stale-while-revalidate=180");
    response.status(200).json({
      latest,
      previous: previous || "",
      rows: sortRows(latestRows),
      previousRows: sortRows(previousRows),
      runInfo: latestRunInfo,
    });
  } catch (error) {
    response.status(502).json({ error: error.message || "Watchlist latest unavailable." });
  }
};
