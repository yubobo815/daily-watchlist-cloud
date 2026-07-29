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
    if (!latest) {
      response.setHeader("Cache-Control", "no-store");
      response.status(200).json(published);
      return;
    }

    const [latestRunInfo, previousRunInfo] = await Promise.all([
      runInfo(latest),
      previous ? runInfo(previous) : Promise.resolve(null),
    ]);
    const latestPublication = latestRunInfo?.publication_id || latestRunInfo?.payload?.publication_id;
    const previousPublication = previousRunInfo?.publication_id || previousRunInfo?.payload?.publication_id;
    if (!latestPublication) throw new Error("Latest validated publication is missing its id.");
    const [latestRows, previousRows] = await Promise.all([
      supabaseSelect(`watchlist_snapshots?select=${selectList(SNAPSHOT_FIELDS)}&run_date=eq.${encodeFilterValue(latest)}&publication_id=eq.${encodeFilterValue(latestPublication)}&order=score.desc`),
      previous && previousPublication
        ? supabaseSelect(`watchlist_snapshots?select=${selectList(SNAPSHOT_FIELDS)}&run_date=eq.${encodeFilterValue(previous)}&publication_id=eq.${encodeFilterValue(previousPublication)}&order=score.desc`)
        : Promise.resolve([]),
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
