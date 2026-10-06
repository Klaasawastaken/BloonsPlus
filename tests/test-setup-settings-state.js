const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
class Element {
  constructor() { this.hidden = false; this.disabled = false; this.value = ''; this.style = {}; this.listeners = {}; this.classList = { add() {}, remove() {}, toggle() {} }; }
  addEventListener(name, fn) { this.listeners[name] = fn; }
  querySelector() { return new Element(); }
  replaceChildren() {}
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
    fetch: async (url, options) => {
      if (options?.method === 'POST') { updateCount++; if (pendingUpdate) await pendingUpdate; return { ok: false, status: 503, json: async () => ({ error: 'Bridge unavailable' }) }; }
      statusReads++;
      return { ok: true, json: async () => status };
    },
  };
  vm.runInNewContext(fs.readFileSync('assets/app/setup-bar.js', 'utf8'), context);
  const flush = async () => { for (let i = 0; i < 8; i++) await Promise.resolve(); };
  await flush();
  assert.match(get('vm-settings-status').textContent, /Ready:/);
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
  console.log('Settings action failure, refresh and duplicate-job checks passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
