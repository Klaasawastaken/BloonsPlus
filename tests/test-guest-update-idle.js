const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require.resolve('../lib/vm-setup'), 'utf8');
const start = source.indexOf('async function updateGuest()');
const code = source.slice(start, source.indexOf('async function openVmWindow', start));
const jobCode = source.slice(source.indexOf('const job = '), source.indexOf('function pythonExe('));
const publicStart = source.indexOf('function publicJob()');
const publicCode = source.slice(publicStart, source.indexOf('\n}', publicStart) + 2);

async function run(remote, connected = true) {
  let installs = 0, probes = 0;
  const context = { isGuest:()=>false, vmFetch:async()=>remote, statusCache:null, Date, Set, setTimeout:fn=>fn(),
    getStatus:async()=>({ steps:[{id:'connected',done:typeof connected === 'function' ? connected(++probes) : connected}] }),
    provisionVm:async()=>{ installs++; } };
  vm.createContext(context);
  vm.runInContext(jobCode + '\n' + publicCode + '\n' + code, context);
  let error;
  try { await vm.runInContext('updateGuest()', context); }
  catch (caught) { error = caught; }
  for (let i = 0; i < 80; i++) await Promise.resolve();
  return {installs, error, probes, job:vm.runInContext('publicJob()', context)};
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
  assert.equal(idle.job.state, 'complete');
  const disconnected = await run('{"running":false}', false);
  assert.equal(disconnected.job.state, 'failed');
  assert.match(disconnected.job.error, /connect|validation/i);
  const recovered = await run('{"running":false}', probe => probe >= 3);
  assert.equal(recovered.job.state, 'complete', 'Allow the updated app time to reconnect');
  assert.equal(recovered.probes, 3);
  console.log('VM update requires an explicitly idle guest.');
})().catch(error=>{console.error(error); process.exitCode=1;});
