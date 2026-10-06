const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const { createSetupController, controllerOwner } = require('../lib/setup-controller');

(async () => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'bloons-setup-controller-'));
  let starts = 0, statusBusy = false;
  const dependencies = {
    getStatus: async () => ({ applicable:true, allDone:false, next:{id:'provision'}, vm:{state:'online'}, steps:[{id:'provision',done:false}], job:{running:statusBusy} }),
    getReplayStatus: async () => ({running:false}), start: async () => { starts++; statusBusy=true; },
  };
  let controller = createSetupController({ root: temp, dataRoot: temp, port: 0, dependencies });
  const server = http.createServer((req, res) => controller.handle(req, res, new URL(req.url, 'http://localhost').pathname));
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  controller.setPort(server.address().port);
  const base = `http://127.0.0.1:${server.address().port}`;
  const sessionId = crypto.randomBytes(16).toString('hex'), key = crypto.randomBytes(32).toString('hex');
  const handoffDir = path.join(temp, 'setup-handoff'); fs.mkdirSync(handoffDir);
  const handoff = {protocolVersion:1, sessionId, owner:controllerOwner(temp), operation:'install', key, options:{}, createdAt:Date.now()};
  const file = path.join(handoffDir, sessionId+'.json');
  const post = (route, body, token = key, headers = {}) => fetch(base+route, {method:'POST',headers:{'Content-Type':'application/json','X-Bloons-Setup-Key':token,...headers},body:JSON.stringify(body)});
  try {
    fs.writeFileSync(file, JSON.stringify({...handoff,protocolVersion:2}));
    assert.equal((await post('/api/setup/session/connect',{handoffId:sessionId})).status,409);
    fs.writeFileSync(file, JSON.stringify({...handoff,owner:'f'.repeat(64)}));
    assert.equal((await post('/api/setup/session/connect',{handoffId:sessionId})).status,409);
    fs.writeFileSync(file, JSON.stringify(handoff));
    assert.equal((await post('/api/setup/session/connect',{handoffId:sessionId},'0'.repeat(64))).status,403);
    assert.equal((await post('/api/setup/session/connect',{handoffId:'../secret'})).status,400);
    assert.equal((await post('/api/setup/session/connect',{handoffId:sessionId},key,{Origin:'https://evil.example'})).status,403);
    const connect = await post('/api/setup/session/connect',{handoffId:sessionId});
    assert.equal(connect.status,200); let snapshot = await connect.json();
    assert.equal(snapshot.sessionId,sessionId); assert.equal(JSON.stringify(snapshot).includes(key),false);
    assert.equal((await fetch(base+'/api/setup/session')).status,403);
    assert.equal((await post('/api/setup/session/command',{sessionId,sequence:-1,action:'start'})).status,409);
    const command = await post('/api/setup/session/command',{sessionId,sequence:snapshot.sequence,action:'start'});
    assert.equal(command.status,200); snapshot = await command.json(); assert.equal(starts,1);
    assert.equal((await post('/api/setup/session/command',{sessionId,sequence:snapshot.sequence,action:'start'})).status,409);
    assert.equal(starts,1);
    const checkpoints = fs.readFileSync(controller.checkpointPath,'utf8');
    assert.equal(checkpoints.includes(key),false,'Authentication secret must not enter public snapshots/checkpoints');
    const identity = await (await fetch(base+'/api/setup/controller')).json();
    assert.equal(identity.owner,controllerOwner(temp)); assert.equal(identity.protocolVersion,1); assert.equal(identity.pid,process.pid);
    assert.equal(JSON.stringify(identity).includes(temp),false,'Controller identity does not disclose user paths');
    assert.equal((await post('/api/setup/session/bootstrap',{},key,{Origin:'https://evil.example'})).status,403);
    const browser = await post('/api/setup/session/bootstrap',{},key,{Origin:base});
    assert.equal(browser.status,200);
    const cookie = browser.headers.get('set-cookie');
    assert.match(cookie,/HttpOnly/); assert.match(cookie,/SameSite=Strict/);
    const view = await fetch(base+'/api/setup/session',{headers:{Cookie:cookie.split(';')[0]}});
    assert.equal(view.status,200,'App and native installer share the active session');
    const badHost = await new Promise((resolve,reject)=>{
      const request=http.request(base+'/api/setup/session',{headers:{Host:'attacker.example','X-Bloons-Setup-Key':key}},response=>{response.resume();resolve(response.statusCode);});
      request.on('error',reject);request.end();
    });
    assert.equal(badHost,403,'DNS rebinding cannot address setup');
    statusBusy=false;
    controller = createSetupController({root:temp,dataRoot:temp,port:server.address().port,dependencies});
    const reopen=await post('/api/setup/session/bootstrap',{},key,{Origin:base});
    const resumed=await reopen.json();
    assert.equal(resumed.sessionId,sessionId,'App reopen must retain the outstanding owner session');
    const recoveredCookie=reopen.headers.get('set-cookie').split(';')[0];
    const recovery=await (await fetch(base+'/api/setup/session',{headers:{Cookie:recoveredCookie}})).json();
    assert.equal(recovery.humanAction,'wait_setup','Reopen cannot bypass the lost setup owner');
    const source = fs.readFileSync(path.join(__dirname,'../server.js'),'utf8');
    const timerBlock = source.slice(source.indexOf('}).listen(port'));
    assert.ok(timerBlock.indexOf('if (setupOnly) return') < timerBlock.indexOf('setInterval(collectAiObservation'), 'Setup-only mode must suppress every gameplay timer');
    assert.match(fs.readFileSync(path.join(__dirname,'../electron-main.js'),'utf8'), /if \(!setupOnly\) createWindow\(\)/);
    console.log('Setup controller: identity, key, containment, origin, stale/duplicate commands, private checkpoint and setup-only checks passed');
  } finally { await new Promise(resolve=>server.close(resolve)); fs.rmSync(temp,{recursive:true,force:true}); }
})().catch(error => {console.error(error);process.exitCode=1;});
