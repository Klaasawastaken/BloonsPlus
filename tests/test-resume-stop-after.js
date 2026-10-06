const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync(require.resolve('../lib/automation'), 'utf8');
const start = source.indexOf("if (type === 'resume' && result.exitCode === 0 && checkpointWon");
assert.ok(start >= 0, 'Find the actual post-resume continuation branch');
const end = source.indexOf('\n      }, error =>', start);
assert.ok(end > start);
const branch = source.slice(start, end);

function continuation(overrides = {}, busy = false) {
  const timers = [], starts = [];
  const context = {
    type: 'resume', result: { exitCode: 0 }, checkpointWon: true,
    plausible: true, interruptedSweep: true, job: { stopAfterReplay: false, stopRequested: false },
    setTimeout(callback) { timers.push(callback); },
    engineLock: { getCurrentJob: () => busy ? {} : null },
    startFarm: options => starts.push(options.type),
    ...overrides,
  };
  vm.runInNewContext(branch, context);
  for (const timer of timers) timer();
  return starts;
}

assert.deepEqual(continuation(), ['black-border-sweep']);
assert.deepEqual(continuation({ job: { stopAfterReplay: true, stopRequested: false } }), [],
  'A completed resumed replay must honor Stop after this replay');
assert.deepEqual(continuation({ job: { stopAfterReplay: false, stopRequested: true } }), [],
  'Explicit Stop must prevent automatic continuation');
assert.deepEqual(continuation({ plausible: false }), [], 'No unconfirmed medal continuation');
assert.deepEqual(continuation({ result: { exitCode: 2 } }), [], 'No automatic retry after failed resume');
assert.deepEqual(continuation({}, true), [], 'Respect the shared engine lock');
console.log('Resumed sweep continuation honors stop flags, saved-clear confirmation and the engine lock.');
