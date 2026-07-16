const {
  committedPublicationMatches,
  encodeFilterValue,
  recentRunDates,
  rowDto,
  runInfo,
  selectList,
  SNAPSHOT_FIELDS,
  sortRows,
  supabaseSelect,
} = require("../_supabase");
const { publishedLatestPayload } = require("../_published_data");

module.exports = async function handler(request, response) {
  try {
    const [[latest, previous], published] = await Promise.all([
      recentRunDates(2),
      publishedLatestPayload(),
    ]);
    if (
      published.runInfo?.status === "published_fallback"
      && published.latest
      && (!latest || String(published.latest) > String(latest))
    ) {
      response.setHeader("Cache-Control", "public, max-age=0, s-maxage=15, stale-while-revalidate=30");
      response.status(200).json(published);
      return;
    }
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
    if (!committedPublicationMatches(latestRunInfo, latestRows)) {
      response.setHeader("Cache-Control", "no-store");
      response.status(200).json(published);
      return;
    }

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
    response.status(200).json(await publishedLatestPayload());
  }
};
