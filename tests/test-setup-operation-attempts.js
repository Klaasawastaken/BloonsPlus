const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require.resolve('../lib/vm-setup'), 'utf8');
function cut(name) {
  const start = source.indexOf(`function ${name}(`);
  assert.ok(start >= 0, name);
  const from = source.slice(start - 6, start) === 'async ' ? start - 6 : start;
  return source.slice(from, source.indexOf('\n}', start) + 2);
}
function harness(stepId = 'appsandbox') {
  let ready = false, fail = false, held = null, installs = 0;
  const observations = [];
  const context = { Date, Set, statusCache: null, isGuest: () => false,
    vmFetch: async () => '{"running":false}',
    getStatus: async () => ({ applicable: true, allDone: ready,
      next: ready ? null : { id: stepId },
      steps: [{ id: stepId, done: ready }, { id: 'connected', done: true }] }),
    STEPS: [{ id: stepId, title: stepId }],
  };
  async function install() {
    installs++;
    observations.push(vm.runInContext('publicJob()', context));
    if (held) await held;
    if (fail) throw new Error('Fixture download failure');
    ready = true;
  }
  context.provisionVm = context.installAppSandbox = install;
  vm.createContext(context);
  const jobCode = source.slice(source.indexOf('const job = '), source.indexOf('function pythonExe('));
  vm.runInContext(jobCode + '\n' + ['publicJob', 'runSetup', 'start', 'updateGuest'].map(cut).join('\n'), context);
  return { observations, installs: () => installs,
    run: code => vm.runInContext(code, context),
    missing: () => { ready = false; }, fail: value => { fail = value; },
    hold: promise => { held = promise; } };
}
async function flush() { for (let i = 0; i < 80; i++) await Promise.resolve(); }
(async () => {
  // A successful operation must not turn the next independent update into a retry.
  const updates = harness();
  await updates.run('updateGuest()'); await flush();
  assert.equal(updates.run('publicJob().state'), 'complete');
  await updates.run('updateGuest()'); await flush();
  assert.deepEqual(updates.observations.map(job => [job.state, job.attempt]),
    [['installing', 1], ['installing', 1]], 'New update inherited a completed update\'s attempt');

  const setup = harness();
  setup.run('start()'); await flush(); setup.missing();
  setup.run('start()'); await flush();
  assert.deepEqual(setup.observations.map(job => [job.state, job.attempt]),
    [['installing', 1], ['installing', 1]], 'Fresh setup inherited completed step attempts');

  // A genuine retry of the same failed operation must retain its attempt count.
  for (const call of ['start()', 'updateGuest()']) {
    const retry = harness(); retry.fail(true);
    await retry.run(call); await flush();
    assert.equal(retry.run('publicJob().state'), 'failed');
    retry.fail(false); await retry.run(call); await flush();
    assert.deepEqual(retry.observations.map(job => [job.state, job.attempt]),
      [['installing', 1], ['retrying', 2]], `Lost retry history for ${call}`);
  }

  const changed = harness('provision'); changed.fail(true);
  await changed.run('updateGuest()'); await flush();
  changed.fail(false); changed.run('start()'); await flush();
  assert.deepEqual(changed.observations.map(job => [job.state, job.attempt]),
    [['installing', 1], ['installing', 1]], 'A different operation inherited failed update attempts');

  const setupThenUpdate = harness('provision'); setupThenUpdate.fail(true);
  setupThenUpdate.run('start()'); await flush();
  setupThenUpdate.fail(false); await setupThenUpdate.run('updateGuest()'); await flush();
  assert.deepEqual(setupThenUpdate.observations.map(job => [job.state, job.attempt]),
    [['installing', 1], ['installing', 1]], 'An app update inherited failed environment setup attempts');

  const owned = harness(); let release;
  owned.hold(new Promise(resolve => { release = resolve; }));
  await owned.run('updateGuest()'); await flush();
  const before = owned.run('publicJob()');
  owned.run('start()'); await owned.run('updateGuest()'); await flush();
  assert.equal(owned.installs(), 1, 'Duplicate request started competing work');
  assert.deepEqual(owned.run('publicJob()'), before, 'Duplicate request reset active operation state');
  release(); await flush();
  console.log('Setup attempts: independent operations, genuine retries and active ownership passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
