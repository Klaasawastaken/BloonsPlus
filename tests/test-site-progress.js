const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('docs/site.js', 'utf8').split('// A slim progress indicator')[1];
assert.ok(source, 'Reading progress implementation missing');
function harness(reduced = false) {
  const listeners = {}, mediaListeners = {}, documentListeners = {}, frames = new Map();
  let counter = 0, writes = 0;
  const bar = { setAttribute() {}, style: {} };
  Object.defineProperty(bar.style, 'transform', { set(value) { writes++; this.value = value; } });
  const media = { matches: reduced, addEventListener: (name, fn) => mediaListeners[name] = fn };
  const document = { hidden: false, createElement: () => bar, body: { append() {} },
    documentElement: { scrollHeight: 2000 }, addEventListener: (name, fn) => documentListeners[name] = fn };
  const context = { document, innerHeight: 1000, scrollY: 500,
    matchMedia: () => media, addEventListener: (name, fn) => listeners[name] = fn,
    requestAnimationFrame(fn) { const id = ++counter; frames.set(id, fn); return id; },
    cancelAnimationFrame(id) { frames.delete(id); } };
  vm.runInNewContext('// A slim progress indicator' + source, context);
  return { frames, listeners, media, document, bar, get writes() { return writes; },
    motion(value) { media.matches = value; mediaListeners.change?.({ matches: value }); },
    visibility(hidden) { document.hidden = hidden; documentListeners.visibilitychange?.(); },
    flush() { for (const [id, fn] of [...frames]) { frames.delete(id); fn(); } } };
}
const reduced = harness(true);
reduced.listeners.scroll(); reduced.listeners.resize();
assert.equal(reduced.frames.size, 0);
assert.equal(reduced.writes, 0);
reduced.motion(false); reduced.flush();
assert.equal(reduced.bar.style.value, 'scaleX(0.5)');
const active = harness();
active.listeners.scroll(); active.listeners.scroll(); active.listeners.resize();
assert.equal(active.frames.size, 1);
active.motion(true);
assert.equal(active.frames.size, 0);
active.motion(false); active.visibility(true);
assert.equal(active.frames.size, 0);
active.listeners.scroll(); assert.equal(active.frames.size, 0);
active.visibility(false); active.flush();
assert.equal(active.bar.style.value, 'scaleX(0.5)');
console.log('Site progress respects reduced motion, visibility and one pending frame');
