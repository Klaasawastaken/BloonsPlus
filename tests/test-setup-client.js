const assert=require('node:assert/strict');
const {createClient}=require('../assets/app/setup-client');
(async()=>{
  const calls=[];let sequence=3,rejected=false,hold;
  const client=createClient({fetch:async(url,options={})=>{
    calls.push({url,options});if(hold)await hold;
    const body=options.body?JSON.parse(options.body):{};
    if(url.endsWith('/command')) {
      assert.equal(body.sessionId,'a'.repeat(32));assert.equal(body.sequence,sequence);
      if(!rejected){rejected=true;sequence++;return {ok:false,status:409,json:async()=>({error:'Stale setup command'})};}
      sequence++;
    }
    return {ok:true,status:200,json:async()=>({protocolVersion:1,sessionId:'a'.repeat(32),sequence,phase:'validating'})};
  }});
  await client.begin({isoPath:'existing.iso'});
  assert.equal(calls[0].url,'/api/setup/session/bootstrap');
  assert.equal(calls.filter(call=>call.url.endsWith('/command')).length,2,'Explicit conflict did not refresh once');
  assert.ok(calls.every(call=>call.options.credentials==='same-origin'));
  assert.ok(!JSON.stringify(calls).includes('X-Bloons-Setup-Key'),'Native secret leaked into frontend');
  let release;hold=new Promise(resolve=>{release=resolve;});
  const first=client.observe();await assert.rejects(client.observe(),/already active/);release();await first;hold=null;
  const malformed=createClient({fetch:async()=>({ok:true,status:200,json:async()=>({screen:'BTD6'})})});
  await assert.rejects(malformed.begin({}),/protocol|snapshot/i);
  const offline=createClient({fetch:async()=>{throw new Error('offline');}});
  await assert.rejects(offline.begin({}),/offline/);assert.equal(offline.connected,false);
  console.log('Setup frontend client: scoped cookie, shared sequence, bounded conflict retry, duplicate refusal and malformed/offline response checks passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
