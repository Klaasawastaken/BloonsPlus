const assert = require('node:assert/strict');
const { uiFarmStatus } = require('../lib/status-view');
const status = {
  running: true, paused: false, stopAfterReplay: true, vm: true,
  replay: { screen: 'INGAME', round: 82 }, checkpoint: { nextStep: 20 },
  log: Array.from({ length: 2000 }, (_, i) => `Log line ${i}`),
  victories: 3, defeats: 1,
  progress: {
    blackBorderSweep: { currentMap: 'one_two_tree', gamemode: 'chimps', counts: { confirmed: 3 } },
    achievementsSweep: { completedFiles: ['a', 'b'] },
    lastRun: { log: ['old run'] }, blackBorderRouteAttempts: { privateHistory: 'preserved' },
  },
};
const before = JSON.stringify(status);
const result = uiFarmStatus(status);
assert.equal(JSON.stringify(status), before);
assert.deepEqual(result.progress.blackBorderSweep, status.progress.blackBorderSweep);
assert.deepEqual(result.progress.achievementsSweep, status.progress.achievementsSweep);
assert.equal(result.progress.lastRun, undefined);
assert.equal(result.progress.blackBorderRouteAttempts, undefined);
for (const key of ['running', 'paused', 'stopAfterReplay', 'vm', 'replay', 'checkpoint', 'log', 'victories', 'defeats']) {
  assert.deepEqual(result[key], status[key]);
}
assert.equal(result.log.length, 2000);
assert.deepEqual(uiFarmStatus({ running: false }).progress, {});
console.log('UI status projection checks passed; full logs and active controls retained.');

// Exercise the actual server handler without starting a server or VM.
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require.resolve('../server.js'), 'utf8');
const start = source.indexOf("  if (pathname === '/api/farm/status') {");
const branch = source.slice(start, source.indexOf("  if (pathname === '/api/heroes')", start));
async function handler(view) {
  return new Promise((resolve, reject) => {
    const context = {
      req: { method: 'GET' }, pathname: '/api/farm/status',
      requestUrl: new URL(`http://localhost/api/farm/status${view ? '?view=ui' : ''}`),
      res: { writeHead: code => assert.equal(code, 200), end: text => resolve(JSON.parse(text)) },
      automation: { getStatus: () => ({ running: false }) },
      vmFetch: async path => { assert.equal(path, '/api/farm/status'); return JSON.stringify(status); },
      vmSetup: { isGuest: () => false }, pendingStart: null,
      lastVmFarmStatus: null, lastVmFarmStatusAt: 0, uiFarmStatus, Date,
    };
    try { vm.runInNewContext(`(function () { ${branch} })()`, context); } catch (error) { reject(error); }
  });
}
(async () => {
  const full = await handler(false);
  const ui = await handler(true);
  assert.deepEqual(full.progress, status.progress);
  assert.equal(ui.progress.lastRun, undefined);
  assert.deepEqual(ui.progress.blackBorderSweep, status.progress.blackBorderSweep);
  assert.deepEqual(ui.log, status.log);
  assert.equal(ui.vm, true);
  assert.equal(ui.statusStale, false);
  console.log('Actual full/UI status handler checks passed without live input.');
})().catch(error => { console.error(error); process.exitCode = 1; });
