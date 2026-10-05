const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require.resolve('../lib/automation'), 'utf8');
const start = source.indexOf('function loadFailureHistory(');
const end = source.indexOf('\n}\n', start) + 2;
function load(readFileSync, copyFileSync = () => {}) {
  return vm.runInNewContext(source.slice(start, end) + '\nloadFailureHistory()', {
    fs: {readFileSync, copyFileSync}, FAILURES_PATH:'private-history.json', Date,
  });
}
assert.equal(load(() => '[{"route":"one"}]')[0].route, 'one');
assert.equal(load(() => {throw Object.assign(new Error(), {code:'ENOENT'});}).length, 0);
for (const damaged of ['[{', '{}', 'null']) {
  let copied = false;
  assert.equal(load(() => damaged, (from, to) => {
    assert.equal(from, 'private-history.json');
    assert.match(to, /^private-history\.json\.corrupt-\d+\.log$/);
    copied = true;
  }).length, 0);
  assert.equal(copied, true);
}
assert.throws(() => load(() => {throw Object.assign(new Error('denied'), {code:'EACCES'});}), /denied/);
assert.throws(() => load(() => '[{', () => {throw new Error('backup failed');}), /backup failed/);
console.log('Failure history preservation checks passed.');
