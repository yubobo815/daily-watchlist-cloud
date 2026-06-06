const {
  encodeFilterValue,
  recentRunDates,
  rowDto,
  runInfo,
  selectList,
  SNAPSHOT_FIELDS,
  sortRows,
  supabaseSelect,
} = require("../_supabase");
const { staticLatestPayload } = require("../_static_data");

module.exports = async function handler(request, response) {
  try {
    const [latest, previous] = await recentRunDates(2);
    if (!latest) {
      response.setHeader("Cache-Control", "no-store");
      response.status(200).json({
        latest: "",
        previous: "",
        rows: [],
        previousRows: [],
        runInfo: null,
      });
      return;
    }

    const latestRowsPromise = supabaseSelect(`watchlist_snapshots?select=${selectList(SNAPSHOT_FIELDS)}&run_date=eq.${encodeFilterValue(latest)}&order=score.desc`);
    const previousRowsPromise = previous
      ? supabaseSelect(`watchlist_snapshots?select=${selectList(SNAPSHOT_FIELDS)}&run_date=eq.${encodeFilterValue(previous)}&order=score.desc`)
      : Promise.resolve([]);
    const [latestRows, previousRows, latestRunInfo] = await Promise.all([
      latestRowsPromise,
      previousRowsPromise,
      runInfo(latest),
    ]);

    response.setHeader("Cache-Control", "public, max-age=0, s-maxage=15, stale-while-revalidate=30");
    response.status(200).json({
      latest,
      previous: previous || "",
      rows: sortRows(latestRows.map(rowDto)),
      previousRows: sortRows(previousRows.map(rowDto)),
      runInfo: latestRunInfo,
    });
  } catch (error) {
    console.error(error);
    response.setHeader("Cache-Control", "no-store");
    response.status(200).json(staticLatestPayload());
  }
};
