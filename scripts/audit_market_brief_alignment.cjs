const assert = require('node:assert/strict');
const { alignment } = require('./check_market_brief_alignment.cjs');
const source = require('../data/market-brief.json');
// Freeze test chronology, not published research: future daily updates must not
// change the historical date cases exercised by this isolated audit.
const brief = { ...source, session_date: '2026-10-23', issued_at: '2026-10-23T23:12:41.730Z',
  forecast: { ...source.forecast, id: 'alignment-test-fixture-only', evaluates_at: '2026-10-28T20:00:00Z' } };
const now = new Date('2026-10-24T01:00:00Z');
function published() {
  return { latest: '2026-10-25', runInfo: { status: 'success', live_access_ok: true,
    publication_id: 'verified-publication', latest_data_date: brief.session_date, symbols_failed: 0 },
    rows: [{ publication_id: 'verified-publication', data_date: brief.session_date }] };
}
assert.equal(alignment(brief, published(), now).ready, true);
// Melbourne run dates are NOT US session dates; Friday remains latest on Monday morning.
assert.equal(alignment(brief, published(), new Date('2026-10-25T23:00:00Z')).ready, true);
const partial = published();
partial.runInfo.status = 'degraded'; partial.runInfo.symbols_failed = 2;
partial.rows.push({ publication_id: 'verified-publication', data_date: '2026-10-22' });
assert.equal(alignment(brief, partial, now).partial_coverage, true);
for (const mutate of [
  p => { p.runInfo.latest_data_date = '2026-10-22'; },
  p => { p.runInfo.status = 'running'; },
  p => { p.runInfo.live_access_ok = false; },
  p => { p.rows = []; },
  p => { p.rows[0].publication_id = 'other'; },
  p => { p.rows[0].data_date = '2026-10-26'; },
  p => { p.rows[0].data_date = '2026-10-22'; },
  p => { p.rows[0].data_date = '2026-02-30'; },
]) {
  const p = published(); mutate(p); assert.equal(alignment(brief, p, now).ready, false);
}
assert.equal(alignment(brief, published(), new Date('2026-10-26T21:00:00Z')).ready, false, 'Never publish a Friday report as the new Monday session');
assert.equal(alignment(brief, published(), new Date('2026-10-23T22:00:00Z')).ready, false, 'No future report publication time');
assert.equal(alignment({ ...brief, issued_at: '2026-10-23T18:00:00Z' }, published(), now).ready, false, 'No intraday report labelled final close');
console.log('Market brief alignment: same completed US session, live publication identity, partial coverage, weekends and fail-closed waiting passed.');
