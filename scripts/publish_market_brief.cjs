// Native GITHUB_TOKEN publisher. No stored PAT, bypass, review approval or fake checks.
const fs = require('node:fs');
const crypto = require('node:crypto');
const { validate } = require('../assets/market-brief');
const market = require('../assets/market-session');
const REPO = 'yubobo815/daily-watchlist-cloud';
const FILE = 'data/market-brief.json';
const CHECKS = ['Audit (Python 3.11)', 'Audit (Python 3.12)', 'Browser UAT'];
const stable = value => JSON.stringify(value, (_, v) => v && !Array.isArray(v) && typeof v === 'object' ? Object.fromEntries(Object.keys(v).sort().map(k => [k, v[k]])) : v);
const digest = value => crypto.createHash('sha256').update(stable(value)).digest('hex');
const requireTrue = (ok, message) => { if (!ok) throw new Error(message); };
const sha = value => typeof value === 'string' && /^[0-9a-f]{40}$/.test(value);

function validateCandidate(candidate, current, now = new Date()) {
  validate(candidate);
  requireTrue(/^\d{4}-\d{2}-\d{2}$/.test(candidate.session_date), 'Invalid session date.');
  const session = new Date(`${candidate.session_date}T00:00:00Z`);
  requireTrue(market.isMarketSession(session) && session <= market.latestCompletedMarketSession(now), 'The report must refer to an actually completed US market session.');
  const clock = Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(new Date(candidate.issued_at)).map(p=>[p.type,p.value]));
  const issueDate = `${clock.year}-${clock.month}-${clock.day}`;
  requireTrue(issueDate > candidate.session_date || (issueDate === candidate.session_date && Number(clock.hour)*60+Number(clock.minute) >= market.marketCloseMinutes(session)), 'Report publication precedes the stated US market close.');
  const endClock = Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(new Date(candidate.forecast.evaluates_at)).map(p=>[p.type,p.value]));
  const endSession = new Date(`${endClock.year}-${endClock.month}-${endClock.day}T00:00:00Z`);
  requireTrue(market.isMarketSession(endSession) && Number(endClock.hour)*60+Number(endClock.minute) === market.marketCloseMinutes(endSession), 'Forecast settlement must be an official US session close.');
  requireTrue(candidate.session_date >= current.session_date && Date.parse(candidate.issued_at) >= Date.parse(current.issued_at), 'Refusing to publish older research.');
  if (candidate.forecast.id === current.forecast.id) requireTrue(stable(candidate.forecast) === stable(current.forecast), 'An existing forecast cannot be retrospectively revised.');
  requireTrue(candidate.provenance && Object.keys(candidate.provenance).sort().join(',') === 'forecast,report', 'Verified source provenance is required.');
  for (const source of Object.values(candidate.provenance)) {
    requireTrue(/^[A-Za-z0-9_-]{10,120}$/.test(source.id) && /^[0-9a-f]{64}$/.test(source.sha256), 'Invalid verified source identity.');
    requireTrue(candidate.sources.some(s => s.url === `https://drive.google.com/file/d/${source.id}/view` && s.modified_at === source.modified_at), 'Source timestamps must match verified provenance.');
  }
}

function createPublisher(api, sleep = ms => new Promise(resolve => setTimeout(resolve, ms))) {
  async function currentMain() {
    const ref = await api('GET', `/git/ref/heads/main`);
    requireTrue(sha(ref.object?.sha), 'Cannot resolve current main.');
    const file = await api('GET', `/contents/${FILE}?ref=${ref.object.sha}`);
    requireTrue(file.encoding === 'base64' && sha(file.sha), 'Cannot resolve the public snapshot.');
    return { head: ref.object.sha, file, brief: JSON.parse(Buffer.from(file.content, 'base64').toString('utf8')) };
  }

  async function waitQuality(branch, head) {
    for (let attempt = 0; attempt < 100; attempt++) {
      const runs = await api('GET', `/actions/workflows/quality.yml/runs?branch=${encodeURIComponent(branch)}&event=workflow_dispatch&per_page=10`);
      const run = (runs.workflow_runs || []).find(r => r.head_sha === head);
      if (run?.status === 'completed') {
        requireTrue(run.conclusion === 'success', 'Required Quality workflow failed; the PR remains unmerged.');
        const jobs = await api('GET', `/actions/runs/${run.id}/jobs?per_page=100`);
        requireTrue(CHECKS.every(name => jobs.jobs.some(job => job.name === name && job.conclusion === 'success')), 'Not all required test jobs passed on the candidate commit.');
        return run.id;
      }
      await sleep(15000);
    }
    throw new Error('Quality checks timed out; the PR remains unmerged. Rerun sync.');
  }

  async function protectedChecks(head) {
    // The public branch endpoint is readable without administration permission.
    // Exact base-SHA matching below independently enforces up-to-date testing.
    const branch = await api('GET', '/branches/main');
    const required = branch.protection?.required_status_checks;
    requireTrue(branch.protected === true && branch.protection?.enabled === true && required, 'The protected main branch must remain enabled.');
    requireTrue(CHECKS.every(name => required.contexts.includes(name)), 'Expected protected checks are missing; refusing automatic release.');
    const checks = await api('GET', `/commits/${head}/check-runs?per_page=100`);
    const statuses = await api('GET', `/commits/${head}/status`);
    const expected = required.checks?.length ? required.checks : required.contexts.map(context => ({ context, app_id: null }));
    return expected.every(({ context, app_id }) => {
      const check = checks.check_runs.filter(c => c.name === context && c.head_sha === head && (CHECKS.includes(context) ? c.app?.id === 15368 : app_id == null || c.app?.id === app_id)).sort((a,b) => b.id-a.id)[0];
      if (check) return check.status === 'completed' && check.conclusion === 'success';
      return app_id == null && statuses.statuses.some(s => s.context === context && s.state === 'success');
    });
  }

  async function prepare(candidate, runId, runAttempt) {
    requireTrue(/^\d+$/.test(runId) && /^\d+$/.test(runAttempt), 'Invalid workflow run identity.');
    const base = await currentMain();
    validateCandidate(candidate, base.brief);
    if (stable(candidate) === stable(base.brief)) return { changed: false };
    const branch = `codex/market-brief-sync-${runId}-${runAttempt}`;
    await api('POST', '/git/refs', { ref: `refs/heads/${branch}`, sha: base.head });
    const commit = await api('PUT', `/contents/${FILE}`, {
      message: `Sync market brief for US session ${candidate.session_date}`,
      branch, sha: base.file.sha, content: Buffer.from(JSON.stringify(candidate, null, 2)+'\n').toString('base64'),
    });
    const head = commit.commit?.sha;
    requireTrue(sha(head), 'GitHub did not return the candidate commit.');
    const pr = await api('POST', '/pulls', {
      title: `Update market brief — ${candidate.session_date}`, head: branch, base: 'main', maintainer_can_modify: false,
      body: `Automated market-only update from the authorized Drive folder.\n\nUS session: ${candidate.session_date}\nForecast: ${candidate.forecast.id}\n\nOnly data/market-brief.json is changed. Original dates, forecasts and source identities are retained. Required Quality jobs must pass on this exact head SHA before merging. No scanner or rebuild is run.`,
    });
    requireTrue(Number.isInteger(pr.number) && pr.user?.login === 'github-actions[bot]', 'Unexpected pull-request identity.');
    // A default token does not automatically run trusted CI without approval.
    // Explicit workflow_dispatch is supported and executes the real Quality
    // workflow on the exact data-only commit; it does not approve a PR run.
    await api('POST', '/actions/workflows/quality.yml/dispatches', { ref: branch });
    const qualityRun = await waitQuality(branch, head);
    return { changed: true, repo: REPO, branch, head, base: base.head, pr: pr.number, qualityRun, digest: digest(candidate) };
  }

  async function merge(candidate, state) {
    requireTrue(state.changed === true && state.repo === REPO && sha(state.head) && sha(state.base) && /^codex\/market-brief-sync-\d+-\d+$/.test(state.branch) && Number.isInteger(state.pr), 'Invalid publisher state.');
    requireTrue(state.digest === digest(candidate), 'Candidate changed after validation.');
    const base = await currentMain();
    requireTrue(base.head === state.base, 'Main advanced while tests ran; rerun sync against current main.');
    validateCandidate(candidate, base.brief);
    const pr = await api('GET', `/pulls/${state.pr}`);
    requireTrue(pr.state === 'open' && pr.user?.login === 'github-actions[bot]' && pr.head?.sha === state.head && pr.head?.ref === state.branch && pr.head?.repo?.full_name === REPO && pr.base?.ref === 'main', 'Pull request changed or belongs to another author/repository.');
    const files = await api('GET', `/pulls/${state.pr}/files?per_page=100`);
    requireTrue(files.length === 1 && files[0].filename === FILE && files[0].status === 'modified', 'Only the public market brief may be released.');
    const file = await api('GET', `/contents/${FILE}?ref=${state.head}`);
    requireTrue(stable(JSON.parse(Buffer.from(file.content,'base64').toString('utf8'))) === stable(candidate), 'PR snapshot differs from the tested candidate.');
    let clear = false;
    for (let i=0; i<12 && !clear; i++) {
      clear = await protectedChecks(state.head);
      if (!clear) await sleep(5000);
    }
    requireTrue(clear, 'Required protected checks have not all passed on the exact tested head.');
    const merged = await api('PUT', `/pulls/${state.pr}/merge`, { sha: state.head, merge_method: 'squash' });
    requireTrue(merged.merged === true && sha(merged.sha), 'Protected merge was not completed.');
    return { pr: state.pr, merge_sha: merged.sha, url: `https://github.com/${REPO}/pull/${state.pr}` };
  }
  return { prepare, merge };
}

async function main() {
  const [mode, candidatePath, statePath] = process.argv.slice(2);
  requireTrue(['prepare','merge'].includes(mode) && candidatePath && statePath, 'Usage: publish_market_brief.cjs prepare|merge candidate.json state.json');
  requireTrue(process.env.GITHUB_ACTIONS === 'true' && process.env.GITHUB_REPOSITORY === REPO && process.env.GITHUB_REF === 'refs/heads/main', 'Publishing is restricted to the main workflow in the intended repository.');
  const token = process.env.GH_TOKEN;
  requireTrue(token, 'GitHub workflow token is missing.');
  const api = async (method, path, body) => {
    const response = await fetch(`https://api.github.com/repos/${REPO}${path}`, {
      method, headers: { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', ...(body ? {'Content-Type':'application/json'} : {}) },
      body: body ? JSON.stringify(body) : undefined, signal: AbortSignal.timeout(30000), redirect: 'error',
    });
    requireTrue(response.ok, `GitHub ${method} ${path.split('?')[0]} failed with HTTP ${response.status}. The snapshot was not force-published.`);
    return response.status === 204 ? null : response.json();
  };
  const candidate = JSON.parse(fs.readFileSync(candidatePath,'utf8'));
  const publisher = createPublisher(api);
  const result = mode === 'prepare'
    ? await publisher.prepare(candidate, process.env.GITHUB_RUN_ID, process.env.GITHUB_RUN_ATTEMPT)
    : await publisher.merge(candidate, JSON.parse(fs.readFileSync(statePath,'utf8')));
  fs.writeFileSync(statePath, JSON.stringify(result, null, 2)+'\n');
  if (process.env.GITHUB_OUTPUT && mode === 'prepare') fs.appendFileSync(process.env.GITHUB_OUTPUT, `changed=${result.changed}\n`);
  console.log(JSON.stringify(result));
}

module.exports = { createPublisher, stable, digest, validateCandidate, CHECKS };
if (require.main === module) main().catch(error => { console.error(error.message); process.exitCode=1; });
