const assert = require('node:assert/strict');
const {createSetupSession} = require('../lib/setup-session');

for (const checkpoint of [null, undefined, {}]) {
  const session = createSetupSession({
    sessionId:'a'.repeat(32), owner:'b'.repeat(64), operation:'install', checkpoint,
  }, {getStatus:async()=>{}, getReplayStatus:async()=>{}, start:async()=>{}});
  for (const snapshot of [session.snapshot(), JSON.parse(JSON.stringify(session.snapshot()))]) {
    for (const flag of ['restartDeferred', 'queued', 'operationOutstanding']) {
      assert.equal(snapshot[flag], false, `Fresh ${flag} must be explicit false, including a missing checkpoint`);
    }
    assert.equal(snapshot.phase, 'idle');
    assert.equal(snapshot.environmentValidated, false);
    assert.equal(snapshot.sequence, 0);
  }
}
console.log('Fresh setup snapshots retain explicit false flags before and after JSON serialization');
