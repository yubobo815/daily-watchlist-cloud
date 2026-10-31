// Publish only owner-curated ready PRs with real pull_request Quality checks.
// No PR creation with GITHUB_TOKEN, approval APIs, fake statuses or admin bypass.
const fs = require('node:fs');
const { stable, digest, validateCandidate, CHECKS } = require('./publish_market_brief.cjs');
const { alignment, fetchPublication } = require('./check_market_brief_alignment.cjs');
const market = require('../assets/market-session');
const REPO = 'yubobo815/daily-watchlist-cloud';
const FILE = 'data/market-brief.json';
const READY = /^codex\/market-brief-ready-\d{4}-\d{2}-\d{2}(?:-\d+)?$/;
const ensure = (ok, message) => { if (!ok) throw new Error(message); };
const isSha = value => typeof value === 'string' && /^[0-9a-f]{40}$/.test(value);

function createPreparedPublisher(api, live = fetchPublication, sleep = ms => new Promise(resolve => setTimeout(resolve, ms)), clock = () => new Date()) {
  async function mainSnapshot() {
    const ref = await api('GET', '/git/ref/heads/main');
    ensure(isSha(ref.object?.sha), 'Cannot resolve protected main.');
    const item = await api('GET', `/contents/${FILE}?ref=${ref.object.sha}`);
    return { head: ref.object.sha, brief: decode(item) };
  }
  function decode(item) {
    ensure(item.encoding === 'base64' && item.size <= 32768 && typeof item.content === 'string', 'Expected a bounded public JSON snapshot.');
    return JSON.parse(Buffer.from(item.content, 'base64').toString('utf8'));
  }
  async function safePR(number) {
    const pr = await api('GET', `/pulls/${number}`);
    ensure(pr.state === 'open' && !pr.draft && pr.user?.login === 'yubobo815' && READY.test(pr.head?.ref || '') && pr.head?.repo?.full_name === REPO && pr.base?.ref === 'main' && isSha(pr.head?.sha), 'Only an owner-curated ready PR in this repository is eligible.');
    const files = await api('GET', `/pulls/${number}/files?per_page=100`);
    ensure(files.length === 1 && files[0].filename === FILE && files[0].status === 'modified', 'A ready PR must change only the public brief JSON.');
    const commit = await api('GET', `/git/commits/${pr.head.sha}`);
    ensure(commit.parents?.length === 1 && isSha(commit.parents[0].sha), 'Expected one data-only commit from the tested main base.');
    const candidate = decode(await api('GET', `/contents/${FILE}?ref=${pr.head.sha}`));
    return { pr, candidate, base: commit.parents[0].sha };
  }
  async function upstream(runId, publicationId) {
    ensure(/^\d+$/.test(runId || '') && typeof publicationId === 'string' && publicationId.trim(), 'A verified upstream run and publication are required.');
    const run = await api('GET', `/actions/runs/${runId}`);
    ensure(run.repository?.full_name === REPO && run.head_branch === 'main' && run.path === '.github/workflows/daily-watchlist-pages.yml' && ['schedule', 'workflow_dispatch', 'push'].includes(run.event), 'The caller must be the trusted main-branch watchlist workflow.');
    const jobs = await api('GET', `/actions/runs/${runId}/jobs?per_page=100`);
    const job = jobs.jobs?.find(j => j.name === 'verify-and-activate');
    ensure(job?.conclusion === 'success' && job.steps?.some(s => s.name === 'Activate Supabase publication' && s.conclusion === 'success'), 'Watchlist verification and activation have not succeeded.');
    const publication = await live();
    ensure(publication.runInfo?.publication_id === publicationId && publication.runInfo?.live_access_ok === true && ['success', 'ok', 'degraded'].includes(publication.runInfo?.status), 'The upstream publication is not the active verified live snapshot.');
    return publication;
  }
  async function inspect(runId, publicationId) {
    const publication = await upstream(runId, publicationId);
    const base = await mainSnapshot();
    const target = market.latestCompletedMarketSession(clock()).toISOString().slice(0, 10);
    const prs = await api('GET', '/pulls?state=open&base=main&per_page=100');
    const matches = prs.filter(pr => pr.user?.login === 'yubobo815' && READY.test(pr.head?.ref || '') && pr.head.ref.includes(target));
    // Even a no-op is re-verified against Drive by the workflow. Source changes
    // fail the hash gate rather than silently hiding an updated report.
    if (!matches.length && base.brief.session_date === target && base.brief.provenance) {
      ensure(alignment(base.brief, publication, clock()).ready, 'Published summary is not aligned.');
      return { changed: false, candidate: base.brief };
    }
    ensure(matches.length === 1, 'A unique owner-curated ready PR is missing; prepare content before the watchlist finishes.');
    const item = await safePR(matches[0].number);
    validateCandidate(item.candidate, base.brief, clock());
    ensure(item.base === base.head, 'Main advanced after preparation; the curator must refresh and retest the ready PR.');
    const aligned = alignment(item.candidate, publication, clock());
    ensure(aligned.ready, 'Prepared report and the active US watchlist do not align.');
    return { changed: true, repo: REPO, pr: item.pr.number, branch: item.pr.head.ref, head: item.pr.head.sha, base: item.base,
      upstream: String(runId), publication: publicationId, digest: digest(item.candidate), candidate: item.candidate };
  }
  async function quality(state) {
    for (let attempt = 0; attempt < 80; attempt++) {
      const runs = await api('GET', `/actions/workflows/quality.yml/runs?event=pull_request&branch=${encodeURIComponent(state.branch)}&per_page=30`);
      const run = runs.workflow_runs?.filter(r => r.head_sha === state.head && r.event === 'pull_request' && r.path === '.github/workflows/quality.yml').sort((a,b) => b.id-a.id)[0];
      if (run?.status === 'completed') {
        ensure(run.conclusion === 'success', 'The real pull_request Quality workflow failed.');
        const jobs = await api('GET', `/actions/runs/${run.id}/jobs?per_page=100`);
        ensure(CHECKS.every(name => jobs.jobs?.some(j => j.name === name && j.conclusion === 'success')), 'All three real Quality jobs must pass on the exact ready head.');
        return;
      }
      await sleep(15000);
    }
    throw new Error('Real PR Quality checks are missing or not complete; do not substitute workflow_dispatch checks.');
  }
  async function merge(state) {
    ensure(state.changed && state.repo === REPO && isSha(state.head) && isSha(state.base) && Number.isInteger(state.pr) && READY.test(state.branch || ''), 'Invalid prepared publisher state.');
    ensure(digest(state.candidate) === state.digest, 'The prepared snapshot changed after inspection.');
    await quality(state);
    const base = await mainSnapshot();
    ensure(base.head === state.base, 'Main changed during CI; refresh and retest rather than bypassing strict protection.');
    const item = await safePR(state.pr);
    ensure(item.pr.head.sha === state.head && item.base === state.base && stable(item.candidate) === stable(state.candidate), 'Ready PR changed during CI.');
    validateCandidate(item.candidate, base.brief, clock());
    const publication = await upstream(state.upstream, state.publication);
    ensure(alignment(item.candidate, publication, clock()).ready, 'Live publication or the completed US session advanced; do not merge.');
    const branch = await api('GET', '/branches/main');
    const required = branch.protection?.required_status_checks;
    ensure(branch.protected === true && branch.protection?.enabled === true && required && CHECKS.every(name => required.contexts?.includes(name)), 'Required main protection must remain intact.');
    const checks = await api('GET', `/commits/${state.head}/check-runs?per_page=100`);
    const statuses = await api('GET', `/commits/${state.head}/status`);
    for (const { context, app_id } of required.checks?.length ? required.checks : required.contexts.map(context => ({context, app_id:null}))) {
      const check = (checks.check_runs || []).filter(c => c.name === context && c.head_sha === state.head && (CHECKS.includes(context) ? c.app?.id === 15368 : app_id == null || c.app?.id === app_id)).sort((a,b) => b.id-a.id)[0];
      ensure(check ? check.status === 'completed' && check.conclusion === 'success' : app_id == null && statuses.statuses?.some(s => s.context === context && s.state === 'success'), 'A required protected check is not successful on the exact tested head.');
    }
    const result = await api('PUT', `/pulls/${state.pr}/merge`, { sha: state.head, merge_method: 'squash' });
    ensure(result.merged === true && isSha(result.sha), 'Protected merge was refused; no bypass was attempted.');
    return { merged: true, pr: state.pr, head: state.head, merge_sha: result.sha, url: `https://github.com/${REPO}/pull/${state.pr}` };
  }
  return { inspect, quality, merge, upstream };
}

async function main() {
  const [mode, statePath, candidatePath] = process.argv.slice(2);
  ensure(['inspect','wait','merge'].includes(mode) && statePath && candidatePath, 'Use inspect|wait|merge state.json candidate.json');
  ensure(process.env.GITHUB_ACTIONS === 'true' && process.env.GITHUB_REPOSITORY === REPO && process.env.GITHUB_REF === 'refs/heads/main', 'Publishing is restricted to the intended main workflow.');
  ensure(process.env.GH_TOKEN, 'The scoped workflow token is missing.');
  const api = async (method, path, body) => {
    const response = await fetch(`https://api.github.com/repos/${REPO}${path}`, { method,
      headers: {Authorization:`Bearer ${process.env.GH_TOKEN}`,Accept:'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28',...(body?{'Content-Type':'application/json'}:{})},
      body:body?JSON.stringify(body):undefined,redirect:'error',signal:AbortSignal.timeout(30000) });
    ensure(response.ok, `GitHub ${method} ${path.split('?')[0]} failed (${response.status}); no force publication.`);
    return response.status === 204 ? null : response.json();
  };
  const publisher = createPreparedPublisher(api);
  if (mode === 'inspect') {
    const state = await publisher.inspect(process.env.UPSTREAM_RUN_ID, process.env.EXPECTED_PUBLICATION_ID);
    fs.writeFileSync(statePath, JSON.stringify(state)+'\n');
    fs.writeFileSync(candidatePath, JSON.stringify(state.candidate,null,2)+'\n');
    if (process.env.GITHUB_OUTPUT) fs.appendFileSync(process.env.GITHUB_OUTPUT, `changed=${state.changed}\n`);
    console.log(JSON.stringify({changed:state.changed,pr:state.pr,head:state.head}));
  } else {
    const state = JSON.parse(fs.readFileSync(statePath,'utf8'));
    ensure(stable(JSON.parse(fs.readFileSync(candidatePath,'utf8'))) === stable(state.candidate), 'Candidate file changed.');
    if (mode === 'wait') await publisher.quality(state);
    else console.log(JSON.stringify(await publisher.merge(state)));
  }
}
module.exports = {createPreparedPublisher};
if(require.main===module)main().catch(error=>{console.error(error.message);process.exitCode=1;});
