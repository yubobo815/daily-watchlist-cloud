const assert = require('node:assert/strict');
const {createPreparedPublisher} = require('./publish_prepared_market_brief.cjs');
const {CHECKS} = require('./publish_market_brief.cjs');
const repo='yubobo815/daily-watchlist-cloud', head='b'.repeat(40), main='a'.repeat(40);
const now=()=>new Date('2026-10-31T05:00:00Z');
const base=structuredClone(require('../data/market-brief.json'));
const candidate=structuredClone(base);
candidate.session_date='2026-10-30';candidate.issued_at='2026-10-30T22:45:35.798Z';
candidate.forecast.id='drive:report_fixture_123#us-original-outlook';
candidate.forecast.evaluates_at='2026-11-04T21:00:00Z';
candidate.sources=[{label:'Original',url:'https://drive.google.com/file/d/report_fixture_123/view',modified_at:candidate.issued_at},{label:'Treasury',url:'https://home.treasury.gov/'}];
candidate.provenance=Object.fromEntries(['report','forecast'].map(key=>[key,{id:'report_fixture_123',modified_at:candidate.issued_at,sha256:'c'.repeat(64)}]));
const file=x=>({encoding:'base64',size:JSON.stringify(x).length,content:Buffer.from(JSON.stringify(x)).toString('base64')});
function mock(o={}) {
  const calls=[];
  const pr={number:40,state:'open',draft:false,user:{login:o.author||'yubobo815'},head:{sha:o.head||head,ref:'codex/market-brief-ready-2026-10-30',repo:{full_name:repo}},base:{ref:'main'}};
  const api=async(method,path,body)=>{
    calls.push({method,path,body});
    if(path==='/git/ref/heads/main')return{object:{sha:o.main||main}};
    if(path.startsWith('/contents/'))return file(path.includes(head)?candidate:o.current||base);
    if(path==='/pulls?state=open&base=main&per_page=100')return o.none?[]:[pr];
    if(path==='/pulls/40')return pr;
    if(path.startsWith('/pulls/40/files'))return o.files||[{filename:'data/market-brief.json',status:'modified'}];
    if(path.startsWith('/git/commits/'))return{parents:[{sha:o.parent||main}]};
    if(path==='/actions/runs/100')return{repository:{full_name:repo},head_branch:'main',path:'.github/workflows/daily-watchlist-pages.yml',event:'schedule'};
    if(path.startsWith('/actions/runs/100/jobs'))return{jobs:[{name:'verify-and-activate',conclusion:o.activation||'success',steps:[{name:'Activate Supabase publication',conclusion:o.activation||'success'}]}]};
    if(path.startsWith('/actions/workflows/quality.yml/runs'))return{workflow_runs:[{id:200,head_sha:head,event:o.event||'pull_request',path:'.github/workflows/quality.yml',status:'completed',conclusion:o.quality||'success'}]};
    if(path.startsWith('/actions/runs/200/jobs'))return{jobs:CHECKS.map(name=>({name,conclusion:o.job||'success'}))};
    if(path==='/branches/main')return{protected:true,protection:{enabled:true,required_status_checks:{contexts:CHECKS,checks:CHECKS.map(context=>({context,app_id:15368}))}}};
    if(path.includes('/check-runs'))return{check_runs:CHECKS.map((name,id)=>({id,name,head_sha:head,app:{id:o.app||15368},status:'completed',conclusion:o.check||'success'}))};
    if(path.endsWith('/status'))return{statuses:[]};
    if(method==='PUT'&&path==='/pulls/40/merge')return{merged:true,sha:'d'.repeat(40)};
    throw Error('Unexpected test request '+method+' '+path);
  };
  const live=async()=>({runInfo:{publication_id:o.publication||'publication-100',live_access_ok:true,status:'degraded'},rows:[{publication_id:o.publication||'publication-100',ticker:'AAPL',data_date:o.date||'2026-10-30'}]});
  return{calls,p:createPreparedPublisher(api,live,async()=>{},now)};
}
async function test(){
  let m=mock();const state=await m.p.inspect('100','publication-100');
  const result=await m.p.merge(state);assert.equal(result.head,head);
  assert.deepEqual(m.calls.find(c=>c.path.endsWith('/merge')).body,{sha:head,merge_method:'squash'});
  assert.ok(!m.calls.some(c=>c.method==='POST'),'Never create/approve PRs or fabricate checks');
  for(const o of [{author:'github-actions[bot]'},{files:[{filename:'assets/app.js',status:'modified'}]},
    {parent:'e'.repeat(40)},{activation:'failure'},{date:'2026-10-29'},{publication:'different'},
    {event:'workflow_dispatch'},{quality:'failure'},{job:'failure'},{app:99},{check:'failure'}]){
    m=mock(o);
    await assert.rejects(async()=>{const s=await m.p.inspect('100','publication-100');await m.p.merge(s);});
    assert.ok(!m.calls.some(c=>c.path.endsWith('/merge')));
  }
  m=mock({main:'e'.repeat(40)});await assert.rejects(()=>m.p.merge(state));
  m=mock({none:true,current:candidate});const noop=await m.p.inspect('100','publication-100');
  assert.equal(noop.changed,false);assert.deepEqual(noop.candidate,candidate,'No-op must still supply candidate for live Drive verification');
  console.log('Prepared publisher: trusted activation, owner-only data PR, real PR CI, exact head/base, live US date and protected merge gates passed.');
}
test().catch(e=>{console.error(e);process.exitCode=1;});
