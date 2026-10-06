const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('lib/vm-bridge.js','utf8');
const begin=source.indexOf('async function vmReplayState(');
assert.ok(begin>=0,'A fresh replay ownership probe is required');
const end=source.indexOf('\n}',begin)+2;
const script=source.slice(begin,end);
async function probe(remote,sshResult) {
  let calls=0, command;
  const context={vmFetch:async()=>remote,vmSshPort:async()=>12345,SSH_KEY:'fixture-key',Buffer,JSON,
    execFile:(_file,args,_options,callback)=>{calls++;command=args.at(-1);callback(null,JSON.stringify(sshResult),'');}};
  vm.createContext(context);
  const result=await vm.runInContext(script+'\nvmReplayState()',context);
  return {result,calls,command};
}
(async()=>{
  const busy=await probe('{"running":true}',{running:false});
  assert.equal(busy.result.running,true);assert.equal(busy.calls,0);
  const idle=await probe('{"running":false}',null);assert.equal(idle.calls,0);assert.equal(idle.result.running,false);
  const fresh=await probe(null,{running:false});assert.equal(fresh.result.running,false);assert.equal(fresh.calls,1);
  const unknown=await probe(null,{running:'false'});assert.equal(unknown.result,null);
  const command=Buffer.from(fresh.command.split(' ').at(-1),'base64').toString('utf16le');
  assert.match(command,/Get-Process/);assert.match(command,/\.MainModule\.FileName/);assert.match(command,/OwnedProcess/);
  assert.match(command,/GetConstructor\(\[type\[\]\]@\(\[string\],\[Func\[string\]\]\)\)/,'Reflection must include the actual optional boot identity parameter');
  assert.doesNotMatch(command,/Stop-Process|Start-Process|Set-Acl|schtasks|Remove-Item/i,'Fallback observation cannot alter guest state');
  console.log('Setup replay probe: fresh API, bounded read-only SSH fallback, exact process/native ownership and unknown states passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
