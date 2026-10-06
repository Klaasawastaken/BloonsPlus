const assert = require('node:assert/strict');
const {startIntro} = require('../assets/app/startup');
const appSource=require('node:fs').readFileSync('assets/app/app.js','utf8');
assert.ok(appSource.indexOf('let automationStatusLoading = false;') < appSource.indexOf('\nrender();'),'First render called automation status before its guard was initialized');
function fixture(options = {}) {
  const timers = new Map(); let next = 0, initialized = false;
  const states = [];
  const intro = startIntro({mode:'full', firstLaunch:false, shellReady:()=>{initialized=true;return true;}, serviceReady:async()=>true,...options}, {
    setTimeout:(fn,ms)=>{const id=++next;timers.set(id,{fn,ms});return id;},clearTimeout:id=>timers.delete(id),onChange:s=>states.push(s)
  });
  return {intro,timers,states,initialized:()=>initialized};
}
const flush = async()=>{for(let i=0;i<10;i++)await Promise.resolve();};
(async()=>{
  const full=fixture();assert.equal(full.initialized(),true,'Shell was delayed behind branding');
  await flush();assert.equal(full.states.at(-1).readiness,'ready');
  assert.ok([...full.timers.values()].some(timer=>timer.ms>=1000&&timer.ms<=2000));
  full.intro.dismiss();assert.equal(full.states.at(-1).branding,false);
  const off=fixture({mode:'off'});await flush();assert.equal(off.states.at(-1).branding,false);
  assert.equal(off.timers.size,0,'Off or successful readiness imposed a timer');
  const reduced=fixture({reducedMotion:true});assert.equal(reduced.states[0].mode,'reduced');
  const guest=fixture({softwareRendering:true});assert.equal(guest.states[0].mode,'reduced');
  const first=fixture({firstLaunch:true});assert.ok([...first.timers.values()].some(timer=>timer.ms>=2000&&timer.ms<=3000));
  let attempt=0;
  const failure=fixture({serviceReady:()=>{attempt++;return Promise.reject(new Error('Service unavailable'));}});
  await flush();assert.equal(failure.states.at(-1).readiness,'failed');failure.intro.dismiss();
  assert.equal(failure.states.at(-1).readiness,'failed','Skip concealed a real readiness failure');
  await flush();assert.equal(attempt,1,'Persistent failure retried without user action');
  failure.intro.retry();await flush();assert.equal(attempt,2);
  const delayed=fixture({serviceReady:()=>new Promise(()=>{})});
  [...delayed.timers.values()].find(timer=>timer.ms===8000).fn();await flush();
  assert.equal(delayed.states.at(-1).readiness,'failed');
  delayed.intro.cleanup();assert.equal(delayed.timers.size,0,'Cleanup retained timers');
  const brokenShell=fixture({shellReady:()=>{throw new Error('Shell unavailable');}});
  await flush();assert.equal(brokenShell.states.at(-1).readiness,'failed','A synchronous shell failure became a permanent spinner');brokenShell.intro.cleanup();
  const slowShell=fixture({shellReady:()=>new Promise(()=>{})});await flush();
  assert.ok([...slowShell.timers.values()].some(timer=>timer.ms===8000),'Unready shell lost its deadline');slowShell.intro.cleanup();
  let shellChecks=0;
  const retryShell=fixture({shellReady:()=>++shellChecks===1?true:new Promise(()=>{})});await flush();
  retryShell.intro.retry();await flush();
  assert.equal(retryShell.states.at(-1).readiness,'loading','Retry reused a stale shell readiness observation');retryShell.intro.cleanup();
  for(const f of [full,off,reduced,guest,first,failure])f.intro.cleanup();
  console.log('App startup: concurrent shell, Full/Reduced/Off, guest rendering, bounded service readiness and explicit retry passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
