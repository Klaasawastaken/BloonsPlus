const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require.resolve('../lib/automation'), 'utf8');
function extract(name) {
  const start = source.indexOf(`function ${name}(`);
  assert.notEqual(start, -1, `Missing production function ${name}`);
  const asyncStart = source.slice(start - 6, start) === 'async ' ? start - 6 : start;
  return source.slice(asyncStart, source.indexOf('\n}\n', start) + 2);
}
async function check(states, result, stopped = false) {
  let reads = 0, waits = 0;
  const job = { stopRequested: stopped }, logs = [];
  const answer = await vm.runInNewContext(`${extract('confirmClear')}\n${extract('waitForSavedClear')}\nwaitForSavedClear('map', 'hard', result, job)`, {
    job, result, savedMedalState: () => states[Math.min(reads++, states.length - 1)],
    pushLog: (_job, text) => logs.push(text),
    setTimeout: (resolve, delay) => { assert.equal(delay, 2000); waits++; resolve(); },
  });
  return { answer, reads, waits, logs };
}
(async () => {
  assert.equal((await check([true], { victoryObserved:true })).waits, 0);
  const delayed = await check([false, null, true], { victoryObserved:true });
  assert.equal(delayed.answer, true);
  assert.equal(delayed.waits, 2);
  const missing = await check([false], { victoryObserved:true });
  assert.equal(missing.answer, false);
  assert.equal(missing.waits, 10, 'Delayed confirmation is bounded to 20 seconds');
  assert.equal((await check([true], { defeatObserved:true })).reads, 0);
  assert.equal((await check([true], { victoryObserved:true, defeatObserved:true })).reads, 0);
  assert.equal((await check([true], {})).waits, 0);
  assert.equal((await check([false], { victoryObserved:true }, true)).waits, 0);
  console.log('Delayed saved-medal confirmation checks passed without gameplay.');
})().catch(error => { console.error(error); process.exitCode = 1; });
