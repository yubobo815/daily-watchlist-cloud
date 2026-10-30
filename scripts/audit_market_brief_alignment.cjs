const assert = require('node:assert/strict');
const { alignment, fetchPublication } = require('./check_market_brief_alignment.cjs');
const source = require('../data/market-brief.json');
// Freeze test chronology, not published research: future daily updates must not
// change the historical date cases exercised by this isolated audit.
const brief = { ...source, session_date: '2026-10-23', issued_at: '2026-10-23T23:12:41.730Z',
  forecast: { ...source.forecast, id: 'alignment-test-fixture-only', evaluates_at: '2026-10-28T20:00:00Z' } };
const now = new Date('2026-10-24T01:00:00Z');
function published() {
  return { latest: '2026-10-25', runInfo: { status: 'success', live_access_ok: true,
    publication_id: 'verified-publication', latest_data_date: brief.session_date, symbols_failed: 0 },
    rows: [{ ticker: 'AAPL', publication_id: 'verified-publication', data_date: brief.session_date }] };
}
assert.equal(alignment(brief, published(), now).ready, true);
// Melbourne run dates are NOT US session dates; Friday remains latest on Monday morning.
assert.equal(alignment(brief, published(), new Date('2026-10-25T23:00:00Z')).ready, true);
const partial = published();
partial.runInfo.status = 'degraded'; partial.runInfo.symbols_failed = 2;
partial.rows.push({ ticker: 'MSFT', publication_id: 'verified-publication', data_date: '2026-10-22' });
assert.equal(alignment(brief, partial, now).partial_coverage, true);
const mixedMarkets = published();
mixedMarkets.runInfo.latest_data_date = '2026-10-26';
mixedMarkets.rows.push({ ticker: 'EOS.AX', publication_id: 'verified-publication', data_date: '2026-10-26' });
assert.equal(alignment(brief, mixedMarkets, now).ready, true, 'ASX dates must not block current US data');
const asxOnly = published(); asxOnly.rows[0].ticker = 'EOS.AX';
assert.equal(alignment(brief, asxOnly, now).ready, false, 'An ASX row must not establish US freshness');
for (const mutate of [
  p => { p.runInfo.status = 'running'; },
  p => { p.runInfo.live_access_ok = false; },
  p => { p.rows = []; },
  p => { p.rows[0].publication_id = 'other'; },
  p => { p.rows[0].data_date = '2026-10-26'; },
  p => { p.rows[0].data_date = '2026-10-22'; },
  p => { p.rows[0].data_date = '2026-02-30'; },
  p => { delete p.rows[0].ticker; },
]) {
  const p = published(); mutate(p); assert.equal(alignment(brief, p, now).ready, false);
}
assert.equal(alignment(brief, published(), new Date('2026-10-26T21:00:00Z')).ready, false, 'Never publish a Friday report as the new Monday session');
assert.equal(alignment(brief, published(), new Date('2026-10-23T22:00:00Z')).ready, false, 'No future report publication time');
assert.equal(alignment({ ...brief, issued_at: '2026-10-23T18:00:00Z' }, published(), now).ready, false, 'No intraday report labelled final close');
console.log('Market brief alignment: same completed US session, live publication identity, partial coverage, weekends and fail-closed waiting passed.');

async function retryAudit() {
  const fallback = published(); fallback.runInfo.status = 'published_fallback'; fallback.runInfo.live_access_ok = false;
  const ok = value => ({ ok: true, text: async () => JSON.stringify(value) });
  async function sequence(steps) {
    let calls = 0; const delays = [];
    const value = await fetchPublication(async (url, options) => {
      assert.equal(url, 'https://dailytradingcopilot.vercel.app/api/watchlist/latest');
      assert.equal(options.cache, 'no-store');
      assert.equal(options.redirect, 'error');
      const step = steps[calls++];
      if (step instanceof Error) throw step;
      return step;
    }, async delay => { delays.push(delay); });
    return { value, calls, delays };
  }
  const recovered = await sequence([ok(fallback), ok(published())]);
  assert.equal(recovered.calls, 2);
  assert.deepEqual(recovered.delays, [1000]);
  assert.equal(alignment(brief, recovered.value, now).ready, true);
  const blocked = await sequence([ok(fallback), ok(fallback), ok(fallback)]);
  assert.equal(blocked.calls, 3);
  assert.deepEqual(blocked.delays, [1000, 3000]);
  assert.equal(alignment(brief, blocked.value, now).ready, false, 'Exhausted retries never bypass the live gate');
  assert.equal((await sequence([new Error('network'), ok(published())])).calls, 2);
  assert.equal((await sequence([{ ok: false, status: 503 }, ok(published())])).calls, 2);
  const older = published(); older.rows[0].data_date = '2026-10-22';
  assert.equal((await sequence([ok(older)])).calls, 1, 'Do not refetch valid but old publications');
  let calls = 0;
  await assert.rejects(() => fetchPublication(async () => { calls++; return { ok: false, status: 403 }; }, async () => {}), /403/);
  assert.equal(calls, 1, 'Do not retry permission failures');
  calls = 0;
  await assert.rejects(() => fetchPublication(async () => { calls++; return { ok: true, text: async () => '{invalid' }; }, async () => {}));
  assert.equal(calls, 1, 'Invalid content fails closed without retries');
  calls = 0;
  await assert.rejects(() => fetchPublication(async () => { calls++; throw new Error('offline'); }, async () => {}));
  assert.equal(calls, 3, 'Transport retries are bounded');
  console.log('Market brief readiness retries: transient recovery, bounded fallback, and unchanged fail-closed gates passed.');
}
retryAudit().catch(error => { console.error(error); process.exitCode = 1; });
