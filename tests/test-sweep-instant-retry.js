// Exercise the sweep's actual failure branch: timing alone cannot refund a failed strategy.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require.resolve('../lib/automation'), 'utf8');
const start = source.indexOf('        if (', source.indexOf('        const roundText ='));
const end = source.indexOf('        const endedAtMenuWithoutResult', start);
assert.ok(start >= 0 && end > start, 'Locate the actual sweep failure handling');
const branch = source.slice(start, end);
function outcome(category, lossType='instant', instantLosses=0) {
  const env = {failure:{category,lastRound:7,finalRound:100,cash:72}, lossType,
    prior:{hash:'same',instantLosses}, hash:'same', priorAttempts:1, attemptNumber:2,
    map:'bloonarius_prime', gamemode:'chimps', entry:{filename:'original.btd6'},
    routeAttempts:{bloonarius_prime:{chimps:{}}}, attemptedFiles:new Set(['original.btd6']),
    result:{notable:[],reason:'exit'}, job:{}, roundText:'7/100', messages:[],
    saveRouteAttempt:(_map,_mode,_file,status,attempts,_hash,_reason,extra)=>({status,attempts,...extra}),
    queueRouteStrengthening:()=>{throw Error('An opening defeat is not a late loss');}};
  env.pushLog = (_job, line) => env.messages.push(line);
  vm.runInNewContext(branch, env);
  return env;
}
for (const category of ['gameplay-defeat','insufficient-data','route-corruption','upgrade-unconfirmed']) {
  const result = outcome(category);
  assert.equal(result.attemptedFiles.has('original.btd6'), true,
    category + ': a timing label must not return the same failed candidate to the pool');
  assert.ok(!result.messages.some(line => /attempt not consumed/.test(line)));
}
for (const category of ['placement-bug','ocr-stall']) {
  const result = outcome(category);
  assert.equal(result.attemptedFiles.size, 0, category + ': preserve the bounded technical retry');
  assert.equal(result.routeAttempts.bloonarius_prime.chimps['original.btd6'].attempts, 1);
  assert.equal(result.routeAttempts.bloonarius_prime.chimps['original.btd6'].instantLosses, 1);
  const exhausted = outcome(category, 'instant', 2);
  assert.equal(exhausted.attemptedFiles.size, 1, 'Third technical failure must not retry forever');
  assert.equal(exhausted.routeAttempts.bloonarius_prime.chimps['original.btd6'].attempts, 2);
}
assert.equal(outcome('placement-bug', 'instant-prevented').attemptedFiles.size, 0);
console.log('Instant defeats retry only evidenced placement/OCR failures, with the existing bound.');
