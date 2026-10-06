const assert = require('node:assert/strict');
const { createSetupSession } = require('../lib/setup-session');
const sessionId = 'a'.repeat(32), owner = 'b'.repeat(64);
function fixture(overrides = {}) {
  let starts = 0, status = { applicable: true, allDone: false,
    next: { id: 'provision' }, vm: { state: 'online' }, steps: [{ id: 'provision', done: false }], job: { running: false } };
  let replay = { running: false };
  const checkpoints = [];
  const dependencies = {
    getStatus: async fresh => { assert.equal(fresh, true); return status; },
    getReplayStatus: async () => replay,
    start: async () => { starts++; status.job.running = true; return status.job; },
    persist: snapshot => checkpoints.push(structuredClone(snapshot)),
    now: () => Date.now(), ...overrides,
  };
  const session = createSetupSession({ sessionId, owner, operation: 'install', options: {} }, dependencies);
  return { session, starts: () => starts, checkpoints,
    replay: value => { replay = value; }, status: value => { status = value; } };
}
async function start(f) {
  return f.session.command({ sessionId, sequence: f.session.snapshot().sequence, action: 'start' });
}
(async () => {
  const measured = fixture();
  measured.status({applicable:true,allDone:false,steps:[{id:'iso',done:false}],job:{running:true,stepId:'iso',numerator:42,denominator:100,scope:'Download'}});
  await measured.session.observe();
  assert.equal(measured.session.snapshot().numerator,42);
  assert.equal(measured.session.snapshot().denominator,100);
  assert.equal(measured.session.snapshot().indeterminate,false);
  measured.status({applicable:true,allDone:false,steps:[{id:'vm',done:false}],job:{running:true,stepId:'vm'}});
  await measured.session.observe();
  assert.equal(measured.session.snapshot().numerator,null,'Unknown new stage must not retain old byte progress');
  const fresh = fixture();
  await assert.rejects(fresh.session.command({sessionId: 'c'.repeat(32), sequence: 0, action: 'start'}), /stale/i);
  await assert.rejects(fresh.session.command({sessionId, sequence: -1, action: 'start'}), /stale/i);
  await start(fresh); assert.equal(fresh.starts(), 1);
  assert.throws(()=>fresh.session.configure({isoPath:'changed.iso'}),/active/,'Active setup options changed under its owner');
  await assert.rejects(fresh.session.command({sessionId, sequence: fresh.session.snapshot().sequence, action: 'start'}), /already|active/i);
  assert.equal(fresh.starts(), 1);
  for (const replay of [{running: true}, null, {}, {running: 'false'}]) {
    const busy = fixture(); busy.replay(replay); await start(busy);
    assert.equal(busy.starts(), 0, 'Active or unknown replay cannot be deployed over');
    assert.equal(busy.session.snapshot().humanAction, 'wait_replay');
    busy.replay({running: false}); await busy.session.observe();
    assert.equal(busy.starts(), 1, 'Queued environment work resumes after a fresh idle observation');
  }
  const cancel = fixture(); cancel.replay({running: true}); await start(cancel);
  await cancel.session.command({sessionId, sequence: cancel.session.snapshot().sequence, action: 'cancel'});
  cancel.replay({running:false}); await cancel.session.observe();
  assert.equal(cancel.starts(), 0, 'Cancel must not leave a queued mutation');
  const ready = fixture(); ready.status({applicable:true, allDone:true, steps:[{id:'connected',done:true},{id:'steam',done:true}],job:{running:false}});
  await start(ready); assert.equal(ready.starts(), 0); assert.equal(ready.session.snapshot().phase, 'complete');
  let updates=0;
  const update=createSetupSession({sessionId,owner,operation:'update',options:{}},{
    getStatus:async()=>({applicable:true,allDone:true,steps:[{id:'connected',done:true},{id:'steam',done:true}],job:{running:false}}),
    getReplayStatus:async()=>({running:false}),start:async options=>{assert.equal(options.operation,'update');updates++;}
  });
  await update.command({sessionId,sequence:update.snapshot().sequence,action:'start'});
  assert.equal(updates,1,'A ready environment skipped an explicit app update');
  let updateState='waiting-replay';
  const waitingUpdate=createSetupSession({sessionId,owner,operation:'update',options:{}},{
    getStatus:async()=>({applicable:true,allDone:true,steps:[{id:'connected',done:true},{id:'steam',done:true}],job:{running:false,state:updateState}}),
    getReplayStatus:async()=>({running:false}),start:async()=>{}
  });
  await waitingUpdate.command({sessionId,sequence:0,action:'start'});await waitingUpdate.observe();
  assert.notEqual(waitingUpdate.snapshot().phase,'complete','An update waiting on replay was declared complete');
  assert.equal(waitingUpdate.snapshot().queued,true);
  const throwsOnStart=fixture({start:async()=>{throw new Error('Operator did not launch');}});
  await start(throwsOnStart);
  assert.equal(throwsOnStart.session.snapshot().operationOutstanding,false,'A rejected launch retained an owner');
  const failedOwner=fixture();await start(failedOwner);
  failedOwner.status({applicable:true,allDone:false,steps:[{id:'iso',done:false}],job:{running:false,error:'download failed'}});
  await failedOwner.session.observe();
  assert.equal(failedOwner.session.snapshot().operationOutstanding,false,'Known terminal failure kept a phantom owner');
  failedOwner.session.configure({isoPath:'replacement.iso'});
  assert.equal(failedOwner.session.options().isoPath,'replacement.iso');
  const unknown = fixture(); unknown.status({allDone: true});
  await start(unknown); assert.notEqual(unknown.session.snapshot().phase, 'complete', 'Incomplete observation is not readiness');
  assert.equal(unknown.starts(), 0);
  const restart = fixture(); restart.status({applicable:true,allDone:false,next:{id:'vmp'},steps:[{id:'vmp',done:false,state:'restart-required'}],job:{running:false,state:'restart-required'}});
  await restart.session.observe();
  assert.equal(restart.session.snapshot().phase, 'restart_required');
  await restart.session.command({sessionId,sequence:restart.session.snapshot().sequence,action:'restart_later'});
  assert.equal(restart.session.snapshot().restartDeferred, true);
  assert.ok(restart.checkpoints.at(-1).restartDeferred);
  const unchanged = fresh.session.snapshot(); await fresh.session.observe();
  assert.equal(fresh.session.snapshot().planWeight, unchanged.planWeight);
  assert.throws(() => createSetupSession({sessionId,owner,operation:'invented'}, {}), /operation/i);
  const checkpoint = fresh.checkpoints.at(-1);
  const recovered = createSetupSession({sessionId,owner,operation:'install',options:{},checkpoint}, {
    getStatus:async()=>({applicable:true,allDone:false,next:{id:'provision'},vm:{state:'online'},steps:[{id:'provision',done:false}],job:{running:false}}),
    getReplayStatus:async()=>({running:false}),start:async()=>{throw new Error('Must not duplicate an unobserved setup owner');},
  });
  await recovered.observe();
  assert.equal(recovered.snapshot().humanAction,'wait_setup','A reopened observer must not treat a lost setup owner as idle');
  const readyWithLostOwner=createSetupSession({sessionId,owner,operation:'install',options:{},checkpoint},{
    getStatus:async()=>({applicable:true,allDone:true,steps:[{id:'connected',done:true},{id:'steam',done:true}],job:{running:false}}),
    getReplayStatus:async()=>({running:false}),start:async()=>{}
  });
  await readyWithLostOwner.observe();
  assert.equal(readyWithLostOwner.snapshot().humanAction,'wait_setup','Ready files concealed an unobserved setup owner');
  const slow = fixture({getStatus:async()=>{await new Promise(resolve=>setTimeout(resolve,5));return {applicable:true,allDone:false,next:{id:'provision'},steps:[{id:'provision',done:false}],job:{running:false}};}});
  const first = start(slow);
  await assert.rejects(start(slow),/active/i); await first;
  assert.equal(slow.starts(),1,'Concurrent starts cannot race fresh probes');
  const retry = fixture();
  retry.status({applicable:true,allDone:false,next:{id:'provision'},steps:[{id:'provision',done:false}],job:{running:false,error:'Earlier bridge failure'}});
  await retry.session.observe();
  assert.equal(retry.session.snapshot().phase,'failed');
  await retry.session.command({sessionId,sequence:retry.session.snapshot().sequence,action:'retry'});
  assert.equal(retry.starts(),1,'An old failed job must not prevent an explicit fresh retry');
  let rebootStarts=0;
  const afterReboot=createSetupSession({sessionId,owner,operation:'install',options:{},checkpoint:{...checkpoint,operationBootIdentity:'old-boot'}},{
    getStatus:async()=>({applicable:true,allDone:false,next:{id:'provision'},steps:[{id:'provision',done:false}],job:{running:false}}),
    getBootIdentity:async()=> 'new-boot',getReplayStatus:async()=>({running:false}),start:async()=>{rebootStarts++;},
  });
  await afterReboot.observe();
  assert.notEqual(afterReboot.snapshot().humanAction,'wait_setup','A confirmed new host boot releases old host work for fresh checks');
  await afterReboot.command({sessionId,sequence:afterReboot.snapshot().sequence,action:'resume'});
  assert.equal(rebootStarts,1);
  const laterBusy=fixture();await start(laterBusy);
  laterBusy.status({applicable:true,allDone:false,next:{id:'provision'},steps:[{id:'provision',done:false}],job:{running:false,state:'waiting-replay'}});
  laterBusy.replay({running:true});await laterBusy.session.observe();
  assert.equal(laterBusy.session.snapshot().humanAction,'wait_replay');
  assert.equal(laterBusy.starts(),1);
  laterBusy.replay({running:false});await laterBusy.session.observe();
  assert.equal(laterBusy.starts(),2,'Fresh safe boundaries resume queued remaining setup');
  console.log('Shared setup session: fresh probes, ownership waits, stale commands, cancellation, validation and checkpoints passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
