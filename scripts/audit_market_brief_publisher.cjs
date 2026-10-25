const assert=require('node:assert/strict');
const {createPublisher,digest,stable,CHECKS}=require('./publish_market_brief.cjs');
const base=structuredClone(require('../data/market-brief.json'));
delete base.provenance;
const head='b'.repeat(40), main='a'.repeat(40), merged='d'.repeat(40);
const candidate=structuredClone(base);
candidate.provenance=Object.fromEntries(['report','forecast'].map((key,i)=>[key,{id:base.sources[i].url.split('/d/')[1].split('/')[0],modified_at:base.sources[i].modified_at,sha256:'c'.repeat(64)}]));
const asFile=x=>({encoding:'base64',sha:'f'.repeat(40),content:Buffer.from(JSON.stringify(x)).toString('base64')});

function mock(overrides={}) {
  const calls=[];
  const api=async(method,path,body)=>{
    calls.push({method,path,body});
    if(method==='GET'&&path==='/git/ref/heads/main')return{object:{sha:overrides.main||main}};
    if(method==='GET'&&path.includes('/contents/'))return asFile(path.includes(head)?candidate:overrides.current||base);
    if(method==='POST'&&path==='/git/refs')return{};
    if(method==='PUT'&&path.startsWith('/contents/'))return{commit:{sha:head}};
    if(method==='POST'&&path==='/pulls')return{number:25,user:{login:'github-actions[bot]'}};
    if(method==='POST'&&path.endsWith('/dispatches'))return null;
    if(method==='GET'&&path.includes('/actions/workflows/quality.yml/runs'))return{workflow_runs:[{id:123,head_sha:head,status:'completed',conclusion:overrides.quality||'success'}]};
    if(method==='GET'&&path.includes('/actions/runs/123/jobs'))return{jobs:CHECKS.map(name=>({name,conclusion:overrides.job||'success'}))};
    if(method==='GET'&&path==='/pulls/25')return{state:'open',user:{login:'github-actions[bot]'},head:{sha:overrides.head||head,ref:'codex/market-brief-sync-123-1',repo:{full_name:'yubobo815/daily-watchlist-cloud'}},base:{ref:'main'}};
    if(method==='GET'&&path.includes('/pulls/25/files'))return overrides.files||[{filename:'data/market-brief.json',status:'modified'}];
    if(method==='GET'&&path==='/branches/main')return{protected:true,protection:{enabled:true,required_status_checks:{contexts:CHECKS,checks:CHECKS.map(context=>({context,app_id:15368}))}}};
    if(method==='GET'&&path.includes('/check-runs'))return{check_runs:CHECKS.map((name,id)=>({id,name,head_sha:head,app:{id:overrides.app||15368},status:'completed',conclusion:overrides.check||'success'}))};
    if(method==='GET'&&path.endsWith('/status'))return{statuses:[]};
    if(method==='PUT'&&path==='/pulls/25/merge')return{merged:true,sha:merged};
    throw Error('Unexpected test request '+method+' '+path);
  };
  return{api,calls};
}

async function test(){
  let m=mock();
  const p=createPublisher(m.api,async()=>{});
  const state=await p.prepare(candidate,'123','1');
  assert.equal(state.head,head);
  assert.equal(state.digest,digest(candidate));
  assert.ok(m.calls.some(c=>c.method==='POST'&&c.path.endsWith('/dispatches')));
  const result=await p.merge(candidate,state);
  assert.equal(result.merge_sha,merged);
  assert.deepEqual(m.calls.find(c=>c.path.endsWith('/merge')).body,{sha:head,merge_method:'squash'});
  for(const settings of [{main:'e'.repeat(40)},{head:'e'.repeat(40)},{files:[{filename:'assets/app.js',status:'modified'}]},{app:999},{check:'failure'}]){
    m=mock(settings);
    await assert.rejects(()=>createPublisher(m.api,async()=>{}).merge(candidate,state));
    assert.ok(!m.calls.some(c=>c.path.endsWith('/merge')),'Never merge an unsafe candidate');
  }
  for(const settings of [{quality:'failure'},{job:'failure'}]){
    m=mock(settings);
    await assert.rejects(()=>createPublisher(m.api,async()=>{}).prepare(candidate,'123','1'));
  }
  m=mock({current:candidate});
  assert.deepEqual(await createPublisher(m.api).prepare(candidate,'123','1'),{changed:false});
  assert.ok(!m.calls.some(c=>c.method!=='GET'));
  assert.equal(stable({z:1,a:{y:2,x:1}}),stable({a:{x:1,y:2},z:1}));
  console.log('Market brief publisher: exact SHA, real CI, immutable forecasts, data-only PR, protected merge and no-op controls passed.');
}
test().catch(e=>{console.error(e);process.exitCode=1;});
