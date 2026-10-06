const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('lib/vm-setup.js', 'utf8');
function cut(name) {
  const start = source.indexOf(`function ${name}(`);
  const asyncStart = source.lastIndexOf('async ', start);
  const from = asyncStart === start - 6 ? asyncStart : start;
  const next = source.indexOf('\n}', start) + 2;
  assert.ok(start >= 0 && next > start, name);
  return source.slice(from, next);
}
const jobCode = source.slice(source.indexOf('const job = '), source.indexOf('function pythonExe('));
function harness({ readyAfterAction = true, fail = false, stepId = 'appsandbox', enabled = true } = {}) {
  let ready = false, actions = 0;
  const observations = [];
  const context = {
    Date, Set, STEPS: [{ id: stepId, title: stepId }],
    statusCache: null,
    getStatus: async () => {
      observations.push(vm.runInContext('publicJob()', context));
      return { applicable: true, allDone: ready, steps: [{ id: stepId, done: ready }],
        next: ready ? null : { id: stepId } };
    },
    installAppSandbox: async () => {
      actions++;
      observations.push(vm.runInContext('publicJob()', context));
      if (fail) throw new Error('download failed');
      ready = readyAfterAction;
    },
  };
  context.enableVmp = context.installAppSandbox;
  context.checkVmp = async () => ({ enabled });
  context.runSetupScript = context.installAppSandbox;
  vm.createContext(context);
  vm.runInContext(jobCode + '\n' + ['publicJob', 'runSetup', 'start'].map(cut).join('\n'), context);
  return { context, observations, actions: () => actions };
}
const flush = async () => { for (let i = 0; i < 30; i++) await Promise.resolve(); };
(async () => {
  const good = harness();
  vm.runInContext('start()', good.context);
  await flush();
  assert.equal(vm.runInContext('publicJob().state', good.context), 'complete');
  assert.ok(good.observations.some(job => job.state === 'installing' && job.stepId === 'appsandbox'));
  assert.ok(good.observations.some(job => job.state === 'validating'), 'Validate after the action');
  assert.equal(good.actions(), 1);
  assert.equal(vm.runInContext("setupStepState('appsandbox', true)", good.context), 'complete');
  assert.equal(vm.runInContext("setupStepState('vm', true)", good.context), 'already-ready');
  assert.equal(vm.runInContext("setupStepState('connected', false)", good.context), 'pending');
  assert.equal(vm.runInContext("setupStepState('vmp', false, true)", good.context), 'restart-required');

  const unready = harness({ readyAfterAction: false });
  await assert.rejects(vm.runInContext('runSetup({})', unready.context), /readiness|validation/i);
  assert.equal(unready.actions(), 1, 'An unvalidated step must not reinstall in a loop');

  const failed = harness({ fail: true });
  vm.runInContext('start()', failed.context); await flush();
  const failure = vm.runInContext('publicJob()', failed.context);
  assert.equal(failure.running, false);
  assert.equal(failure.state, 'failed');
  assert.equal(failure.stepId, 'appsandbox');
  assert.match(failure.error, /download failed/);
  vm.runInContext('start()', failed.context); await flush();
  assert.ok(failed.observations.some(job => job.state === 'retrying' && job.attempt === 2));
  assert.equal(failed.actions(), 2);
  for (const enabled of [true, false]) {
    const reboot = harness({ stepId: 'vmp', enabled });
    vm.runInContext('start()', reboot.context); await flush();
    assert.equal(vm.runInContext('publicJob().state', reboot.context), 'restart-required');
    assert.equal(reboot.actions(), enabled ? 0 : 1);
  }
  const signIn = harness({ stepId: 'steam', readyAfterAction: false });
  vm.runInContext('start()', signIn.context); await flush();
  const waiting = vm.runInContext('publicJob()', signIn.context);
  assert.equal(waiting.state, 'checking');
  assert.equal(waiting.running, false);
  assert.equal(waiting.error, null, 'Steam sign-in is a user step, not failure');
  assert.equal(signIn.actions(), 1);
  console.log('Setup phase, validation boundary, failure and retry checks passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
