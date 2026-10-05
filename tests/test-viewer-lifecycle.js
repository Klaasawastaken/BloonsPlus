const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

async function main() {
  const events = {}, timers = new Map(), pending = [], revoked = [];
  let focused = false, shown = true, id = 0, urls = 0;
  const image = { hidden: true, removeAttribute(name) { delete this[name]; } };
  const status = {}, empty = {};
  const panel = { getClientRects: () => shown ? [{}] : [], closest: () => ({}) };
  const elements = { 'vm-viewer': panel, 'vm-viewer-image': image, 'vm-viewer-status': status, 'vm-viewer-empty': empty };
  const document = { hidden: false, hasFocus: () => focused, getElementById: name => elements[name],
    addEventListener: (name, fn) => events[name] = fn };
  const context = {
    document, AbortController, Date,
    addEventListener: (name, fn) => events[name] = fn,
    setTimeout: (fn, delay) => { timers.set(++id, { fn, delay }); return id; },
    clearTimeout: key => timers.delete(key),
    MutationObserver: class { constructor(fn) { events.mutation = fn; } observe() {} },
    URL: { createObjectURL: () => `frame-${++urls}`, revokeObjectURL: value => revoked.push(value) },
    fetch: (_url, { signal }) => new Promise((resolve, reject) => {
      pending.push({ resolve, signal });
      signal.addEventListener('abort', () => reject(Object.assign(new Error('aborted'), { name: 'AbortError' })));
    }),
  };
  const drain = async () => { for (let i = 0; i < 8; i++) await Promise.resolve(); };
  vm.runInNewContext(fs.readFileSync(require.resolve('../assets/app/vm-viewer.js'), 'utf8'), context);
  assert.equal(pending.length, 0, 'Unfocused app must not request frames');
  focused = true; events.focus(); events.focus();
  assert.equal(pending.length, 1, 'Only one capture can be in flight');
  pending[0].resolve({ ok: true, blob: async () => ({}) }); await drain();
  assert.equal(image.src, 'frame-1');
  assert.ok([...timers.values()].some(timer => timer.delay === 2000));
  shown = false; events.mutation();
  assert.equal(timers.size, 0, 'Leaving the category cancels the next capture');
  shown = true; events.mutation();
  assert.equal(pending.length, 2);
  focused = false; events.blur(); await drain();
  assert.equal(pending[1].signal.aborted, true);
  assert.equal(timers.size, 0, 'Blur must not restart polling');
  focused = true; events.focus();
  pending[2].resolve({ ok: true, blob: async () => ({}) }); await drain();
  assert.equal(image.src, 'frame-2');
  events.pagehide(); await drain();
  assert.equal(timers.size, 0);
  assert.ok(revoked.includes('frame-2'));
  assert.equal(typeof events.pageshow, 'function', 'Returning from the browser back/forward cache must resume the viewer');
  events.pageshow();
  assert.equal(pending.length, 4);
  events.pagehide(); await drain();
  assert.equal(timers.size, 0, 'An aborted capture must not reschedule while the page is suspended');
  document.hidden = true; events.pageshow(); events.visibilitychange();
  assert.equal(pending.length, 4, 'A hidden browser tab must not resume capture');
  document.hidden = false; events.visibilitychange();
  assert.equal(pending.length, 5);
  events.pagehide(); await drain();
  assert.equal(timers.size, 0);
  console.log('Viewer lifecycle checks passed. No VM captures or gameplay input used.');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
