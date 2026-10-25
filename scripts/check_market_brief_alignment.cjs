// Read-only publication gate. It never starts a scanner, edits data or relabels dates.
const fs = require('node:fs');
const market = require('../assets/market-session');
const { validate } = require('../assets/market-brief');
const WATCHLIST_URL = 'https://dailytradingcopilot.vercel.app/api/watchlist/latest';

function alignment(brief, publication, now = new Date()) {
  validate(brief);
  const target = market.latestCompletedMarketSession(now).toISOString().slice(0, 10);
  const run = publication?.runInfo;
  const result = { ready: false, target_session: target, report_session: brief.session_date,
    watchlist_session: run?.latest_data_date || null };
  const wait = reason => ({ ...result, reason });
  if (brief.session_date !== target) return wait('The newest completed US session needs its final morning report and matching forecast card.');
  if (Date.parse(brief.issued_at) > now.getTime()) return wait('The report publication time is in the future.');
  const issue = Object.fromEntries(new Intl.DateTimeFormat('en-CA', { timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(new Date(brief.issued_at)).map(p => [p.type, p.value]));
  const issueDate = `${issue.year}-${issue.month}-${issue.day}`;
  if (issueDate < target || (issueDate === target && Number(issue.hour) * 60 + Number(issue.minute) < market.marketCloseMinutes(new Date(`${target}T00:00:00Z`)))) {
    return wait('The report was issued before the stated US session closed.');
  }
  if (!run || !['ok', 'success', 'degraded'].includes(run.status) || run.live_access_ok !== true) {
    return wait('The active watchlist publication is unavailable or not verified as live.');
  }
  if (run.latest_data_date !== target) return wait('Wait for the scanner to publish the same completed US session.');
  const rows = publication.rows;
  if (!run.publication_id || !Array.isArray(rows) || !rows.length || rows.some(row => row.publication_id !== run.publication_id)) {
    return wait('The watchlist response is empty or mixes publication identities.');
  }
  const validDate = value => typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value)
    && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value;
  if (rows.some(row => !validDate(row.data_date) || row.data_date > target)
      || !rows.some(row => row.data_date === target)) {
    return wait('The published row dates are inconsistent with the stated US session.');
  }
  return { ...result, ready: true, publication_id: run.publication_id,
    partial_coverage: run.status === 'degraded' || Number(run.symbols_failed || 0) > 0 || rows.some(row => row.data_date < target) };
}

async function main() {
  const args = process.argv.slice(2);
  const candidate = args.indexOf('--candidate');
  const fixture = args.indexOf('--watchlist');
  if (candidate < 0 || !args[candidate + 1]) throw new Error('Use --candidate path/to/market-brief.json [--watchlist saved-publication.json].');
  const brief = JSON.parse(fs.readFileSync(args[candidate + 1], 'utf8'));
  let publication;
  if (fixture >= 0) {
    publication = JSON.parse(fs.readFileSync(args[fixture + 1], 'utf8'));
  } else {
    const response = await fetch(WATCHLIST_URL, { cache: 'no-store', redirect: 'error', signal: AbortSignal.timeout(20000) });
    if (!response.ok) throw new Error(`Published watchlist unavailable (HTTP ${response.status}); preserve the existing summary.`);
    const body = await response.text();
    if (body.length > 10 * 1024 * 1024) throw new Error('Unexpected watchlist response size.');
    publication = JSON.parse(body);
  }
  const result = alignment(brief, publication);
  console.log(JSON.stringify(result));
  if (!result.ready) process.exitCode = 2;
}

module.exports = { alignment };
if (require.main === module) main().catch(() => {
  console.error('Alignment check failed: verify candidate schema and live publication; do not publish or relabel older data.');
  process.exitCode = 1;
});
