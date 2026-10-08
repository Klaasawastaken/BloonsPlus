const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require.resolve('../assets/app/app.js'), 'utf8');
const fragment = source.slice(source.indexOf('const reportDialog ='), source.indexOf("document.querySelector('#report-close')"));

function fixture() {
  const listeners = [], requests = [], timers = new Map(); let id = 0;
  const dialog = { open: false, showModal() { this.open = true; } };
  const fields = { '#issue-report-dialog': dialog, '#report-preview': {},
    '#report-description': { value: 'fixture description' }, '#report-submit': {} };
  const context = {
    document: { querySelector: selector => fields[selector],
      querySelectorAll: () => [{ addEventListener: (_, fn) => listeners.push(fn) }] },
    latestRunLog: 'fixture round=60', latestAutomationStatus: { vm: true },
    window: { BloonsSupport: { redact: value => value } }, AbortController,
    setTimeout: fn => { timers.set(++id, fn); return id; }, clearTimeout: id => timers.delete(id),
    fetch: (url, options) => new Promise((resolve, reject) => {
      assert.equal(url, '/api/setup/controller');
      assert.equal(options.cache, 'no-store');
      requests.push({ resolve, reject, signal: options.signal });
    }),
  };
  vm.runInNewContext(fragment, context);
  return { open: () => listeners[0](), requests, timers, fields,
    body: () => new URL(fields['#report-submit'].href).searchParams.get('body') };
}
async function drain() { for (let i = 0; i < 8; i++) await Promise.resolve(); }
async function reply(request, value, ok = true) {
  request.resolve({ ok, json: async () => value }); await drain();
}
(async () => {
  const current = fixture(); current.open();
  assert.ok(current.body().includes('App: Bloons+ unknown'), 'Never guess the installed version while its lookup is pending');
  assert.equal(current.requests.length, 1);
  current.fields['#report-description'].value = 'edited while loading';
  await reply(current.requests[0], { protocolVersion: 1, version: '0.1.37-preview.99' });
  assert.ok(current.body().includes('App: Bloons+ 0.1.37-preview.99'));
  assert.ok(current.body().includes('edited while loading'));
  assert.equal(current.timers.size, 0);

  for (const value of [null, {}, { protocolVersion: 2, version: '1.0.0' },
    { protocolVersion: 1, version: 'private arbitrary text' }, { protocolVersion: 1, version: 100 },
    ...['1.2.3-..', '01.2.3', '1.2.3-01', '1.2.3+..'].map(version => ({ protocolVersion: 1, version }))]) {
    const bad = fixture(); bad.open(); await reply(bad.requests[0], value);
    assert.ok(bad.body().includes('App: Bloons+ unknown'));
  }
  for (const cause of ['http', 'network', 'parse']) {
    const bad = fixture(); bad.open();
    if (cause === 'http') await reply(bad.requests[0], { version: '1.0.0' }, false);
    else if (cause === 'parse') bad.requests[0].resolve({ ok: true, json: async () => { throw new Error('invalid JSON'); } });
    else bad.requests[0].reject(new Error('offline'));
    await drain(); assert.ok(bad.body().includes('App: Bloons+ unknown'));
    assert.equal(bad.timers.size, 0);
  }
  const race = fixture(); race.open(); race.open();
  assert.ok(race.requests[0].signal.aborted);
  await reply(race.requests[1], { protocolVersion: 1, version: '1.0.0' });
  await reply(race.requests[0], { protocolVersion: 1, version: '0.1.0' });
  assert.ok(race.body().includes('App: Bloons+ 1.0.0'), 'A stale response must not overwrite the new report identity');
  const timeout = fixture(); timeout.open();
  [...timeout.timers.values()][0]();
  assert.ok(timeout.requests[0].signal.aborted);
  timeout.requests[0].reject(new Error('timeout')); await drain();
  assert.ok(timeout.body().includes('App: Bloons+ unknown'));
  console.log('Issue-report identity: observed version, unknown/failure fallback, edits, timeout and stale-response checks pass.');
})().catch(error => { console.error(error); process.exitCode = 1; });
