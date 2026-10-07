// Synthetic identities only. Never load a real save or send gameplay input.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {createRequire} = require('node:module');
const file = require.resolve('../lib/btd6-save-progress');
const source = fs.readFileSync(file, 'utf8');
function decode(ownerID) {
  const fixture = {ownerID, mapInfo:{maps:{}}};
  const before = JSON.stringify(fixture);
  const result = vm.runInNewContext(source + '\nfindProfileSave=()=>"synthetic"; decodeProfileSave=()=>fixture; readLocalProgress();', {
    require:createRequire(file), module:{exports:{}}, fixture,
  });
  assert.equal(JSON.stringify(fixture), before);
  return result;
}
const first = decode('synthetic-owner-a');
assert.match(first.accountIdentity, /^[a-f0-9]{64}$/);
assert.equal(first.accountIdentity, decode('synthetic-owner-a').accountIdentity);
assert.notEqual(first.accountIdentity, decode('synthetic-owner-b').accountIdentity);
assert.ok(!JSON.stringify(first).includes('synthetic-owner-a'), 'Raw owner is not returned');
for (const value of [undefined, null, '', ' ', 42, {}, [], 'owner\nother', 'x'.repeat(513)]) {
  assert.equal(decode(value).accountIdentity, null, 'Unavailable identity never becomes a shared fallback account');
}
console.log('Save account identity is opaque, stable, isolated and read-only.');
