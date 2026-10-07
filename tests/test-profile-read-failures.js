const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require.resolve('../assets/app/app.js'), 'utf8');
const code = source.slice(source.indexOf('let pendingLocalSaveRead'),source.indexOf('async function loadDetectedProgress'));
(async () => {
  let next = async () => { throw new Error('synthetic network loss'); };
  const context = vm.createContext({fetch:(...args)=>next(...args),AbortSignal:{timeout:()=>null}});
  vm.runInContext(code,context);
  const offline = await context.readLocalSaveProgress();
  assert.equal(offline.ok,false);
  assert.equal(offline.profile.available,false);
  assert.equal(offline.profile.source,'vm-unavailable');
  next=async()=>({ok:true,status:200,json:async()=>({available:true,accountIdentity:'a'})});
  const recovered=await context.readLocalSaveProgress();
  assert.equal(recovered.ok,true);
  assert.ok(recovered.sequence>offline.sequence);
  assert.equal(context.currentLocalSaveRead(offline),recovered);
  next=async()=>({ok:true,status:200,json:async()=>{throw new SyntaxError('invalid JSON');}});
  const broken=await context.readLocalSaveProgress();
  assert.equal(broken.profile.available,false);
  assert.equal(context.currentLocalSaveRead(recovered),broken,'A late scanner cannot revive readable status after a broken response');
  for (const value of [null, [], {}]) {
    next=async()=>({ok:true,status:200,json:async()=>value});
    const invalid=await context.readLocalSaveProgress();
    assert.equal(invalid.ok,false,'Malformed profile responses must invalidate stale availability');
  }
  console.log('Profile read failure: network loss, parse failure, fresh recovery and late-response precedence pass.');
})().catch(error=>{console.error(error);process.exitCode=1;});
