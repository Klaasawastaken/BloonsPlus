const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
class Element {
  constructor() { this.hidden = false; this.disabled = false; this.value = ''; this.style = {}; this.listeners = {}; this.classList = { add() {}, remove() {}, toggle() {} }; }
  addEventListener(name, fn) { this.listeners[name] = fn; }
  querySelector() { return new Element(); }
  replaceChildren(...children) { this.children = children; }
  setAttribute() {}
  insertAdjacentElement() {}
}
(async () => {
  const elements = new Map();
  const get = id => { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); };
  const status = { applicable: true, allDone: true, vm: { state: 'online' }, steps: [{ id: 'vm', done: true, title: 'VM' }], job: {} };
  let updateCount = 0, pendingUpdate, statusReads = 0;
  const documentListeners = {};
  const context = {
    document: { getElementById: get, createElement: () => new Element(), addEventListener: (name, fn) => { documentListeners[name] = fn; } },
    sessionStorage: { getItem() {}, setItem() {} }, localStorage: { getItem() {}, setItem() {} },
    setTimeout: () => 1, clearTimeout() {}, AbortSignal,
    BloonsSetupClient: require('../assets/app/setup-client'),
    fetch: async (url, options) => {
      if (options?.method === 'POST' && JSON.parse(options.body).operation === 'update') { updateCount++; if (pendingUpdate) await pendingUpdate; return { ok: false, status: 503, json: async () => ({ error: 'Bridge unavailable' }) }; }
      if(url.startsWith('/api/setup/session'))return {ok:true,json:async()=>({protocolVersion:1,sessionId:'a'.repeat(32),sequence:0,
        phase:status.allDone?'complete':status.job.running?'validating':status.job.error?'failed':status.next?.button?'idle':'restart_required',
        humanAction:!status.next?.button&&!status.allDone?'restart':null,operationOutstanding:!!status.job.running,
        status:status.next?.message||'Checking setup',error:status.job.error?{message:status.job.error}:null,completedWeight:status.allDone?100:0})};
      statusReads++;
      return { ok: true, json: async () => status };
    },
  };
  vm.runInNewContext(fs.readFileSync('assets/app/setup-bar.js', 'utf8'), context);
  const flush = async () => { for (let i = 0; i < 40; i++) await Promise.resolve(); };
  await flush();
  assert.match(get('vm-settings-status').textContent, /Ready:/);
  status.allDone = false;
  status.steps = [{ id: 'connected', done: false, state: 'failed', title: 'VM connection', detail: 'Bridge unavailable' }];
  status.next = { id: 'connected', button: 'Retry connection', message: 'Reconnect the VM app.' };
  status.job = { state: 'failed', stepId: 'connected', error: 'Bridge unavailable', running: false };
  await get('vm-settings-refresh').listeners.click();
  assert.match(get('vm-settings-steps').children[0].textContent, /Failed/);
  assert.match(get('vm-settings-steps').children[0].className, /failed/);
  status.steps[0].state = 'validating';
  status.job = { state: 'validating', stepId: 'connected', running: true, activity: 'Verifying connection' };
  await get('vm-settings-refresh').listeners.click();
  assert.match(get('vm-settings-steps').children[0].textContent, /Validating/);
  status.allDone = true;
  status.steps = [{ id: 'vm', done: true, title: 'VM' }];
  status.job = {};
  await get('vm-settings-refresh').listeners.click();
  const readsBeforeOpen = statusReads;
  await documentListeners['bloons-settings-open']();
  assert.equal(statusReads, readsBeforeOpen + 1, 'opening Settings fetches fresh setup state');
  await get('vm-settings-update').listeners.click();
  assert.match(get('vm-settings-status').textContent, /Could not update VM: Bridge unavailable/);
  await get('vm-settings-refresh').listeners.click();
  assert.match(get('vm-settings-status').textContent, /Bridge unavailable/, 'poll must not erase an action failure');
  let release;
  pendingUpdate = new Promise(resolve => { release = resolve; });
  const first = get('vm-settings-update').listeners.click();
  const second = get('vm-settings-update').listeners.click();
  await flush();
  assert.equal(updateCount, 2, 'duplicate click must not submit a second concurrent job');
  assert.equal(get('vm-settings-update').disabled, true);
  release(); await Promise.all([first, second]);
  assert.equal(get('vm-settings-chip').textContent, 'NEEDS ATTENTION');
  assert.equal(get('vm-settings-update').disabled, false, 'failed action can be retried after fresh status');
  status.allDone = false;
  status.vm = { state: 'missing' };
  status.steps = [{ id: 'vm', done: false, title: 'VM' }];
  status.next = { button: 'Set up VM', message: 'Create your game VM.' };
  await get('vm-settings-refresh').listeners.click();
  assert.equal(get('vm-settings-start').hidden, false);
  assert.equal(get('vm-settings-update').hidden, true, 'no update control before a VM exists');
  assert.equal(get('vm-settings-update-hint').hidden, true);
  assert.equal(get('vm-settings-advanced').hidden, false, 'ISO override remains available during creation');
  status.next = { message: 'Restart Windows to enable virtualization.' };
  await get('vm-settings-refresh').listeners.click();
  assert.equal(get('vm-settings-start').hidden, true, 'no dead action for a reboot-only step');
  assert.equal(get('vm-settings-actions').hidden, true);
  status.applicable = false;
  await get('vm-settings-refresh').listeners.click();
  assert.equal(get('vm-settings-advanced').hidden, true);
  assert.equal(get('vm-settings-checks').hidden, true);
  assert.equal(get('vm-settings-actions').hidden, true, 'guest does not offer host-only setup');
  const html = fs.readFileSync('index.html', 'utf8');
  assert.ok(html.indexOf('settings-appearance') < html.indexOf('panel vm-settings-panel'));
  assert.equal((html.match(/id="vm-settings-update"/g) || []).length, 1);
  assert.ok(html.indexOf('assets/app/setup-client.js') < html.indexOf('assets/app/setup-bar.js'), 'shared client loads before its renderer');
  for(const prefix of ['setup-bar','vm-settings'])for(const action of ['pause','restart-now','restart-later','open-vm'])
    assert.ok(html.includes(`id="${prefix}-${action}"`),`Missing human setup action ${prefix}-${action}`);
  assert.ok(!fs.readFileSync('assets/app/setup-bar.js','utf8').includes("classList.toggle('setup-prepage'"),'Missing VM setup must not hide navigation behind a full-page intro');
  const actions=[];
  let snapshot={protocolVersion:1,sessionId:'a'.repeat(32),sequence:0,phase:'restart_required',humanAction:'restart',status:'Restart Windows to continue',completedWeight:8};
  status.applicable=true;status.allDone=false;status.vm={state:'online'};status.job={running:false};
  context.confirm=()=>false;
  context.fetch=async(url,options)=>{
    if(url==='/api/setup/status')return {ok:true,json:async()=>status};
    if(url.endsWith('/command')){
      const body=JSON.parse(options.body);assert.equal(body.sequence,snapshot.sequence);actions.push(body.action);
      if(body.action==='restart_later')snapshot.restartDeferred=true;
      if(body.action==='cancel'){snapshot.queued=false;snapshot.phase='cancelled';snapshot.humanAction='resume';}
    }
    snapshot.sequence++;
    return {ok:true,json:async()=>structuredClone(snapshot)};
  };
  vm.runInNewContext(fs.readFileSync('assets/app/setup-bar.js','utf8'),context);await flush();
  await get('vm-settings-start').listeners.click();await flush();
  assert.equal(get('vm-settings-restart-now').hidden,false);
  await get('vm-settings-restart-now').listeners.click();assert.equal(actions.length,0,'Declining restart submitted a command');
  await get('vm-settings-restart-later').listeners.click();assert.deepEqual(actions,['restart_later']);
  assert.equal(get('vm-settings-restart-later').hidden,true,'Deferred restart choice did not persist in the shared view');
  snapshot={...snapshot,phase:'recovering',humanAction:'wait_replay',queued:true,status:'Waiting for replay'};
  await get('vm-settings-refresh').listeners.click();
  assert.equal(get('vm-settings-pause').hidden,false);
  await get('vm-settings-pause').listeners.click();assert.equal(actions.at(-1),'cancel');
  assert.equal(get('vm-settings-pause').hidden,true,'Pause retained queued work');
  console.log('Settings action failure, refresh and duplicate-job checks passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
