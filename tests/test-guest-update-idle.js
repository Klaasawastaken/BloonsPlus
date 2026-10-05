const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require.resolve('../lib/vm-setup'), 'utf8');
const start = source.indexOf('async function updateGuest()');
const code = source.slice(start, source.indexOf('async function openVmWindow', start));

async function run(remote) {
  let installs = 0;
  const context = { isGuest:()=>false, job:{running:false}, vmFetch:async()=>remote,
    publicJob:()=>({}), note:()=>{}, statusCache:null,
    provisionVm:async()=>{ installs++; } };
  let error;
  try { await vm.runInNewContext(code + '\nupdateGuest()', context); }
  catch (caught) { error = caught; }
  return {installs, error};
}
(async()=>{
  for (const remote of [null, 'Not found', '{}', 'null', '[]', '{"running":null}', '{"running":0}', '{"running":"false"}', '{"running":true}']) {
    const result = await run(remote);
    assert.equal(result.installs, 0, `Must not install without confirmed idle: ${remote}`);
    assert.ok(result.error, 'Explain why updating is blocked');
  }
  const idle = await run('{"running":false}');
  assert.equal(idle.error, undefined);
  assert.equal(idle.installs, 1);
  console.log('VM update requires an explicitly idle guest.');
})().catch(error=>{console.error(error); process.exitCode=1;});
