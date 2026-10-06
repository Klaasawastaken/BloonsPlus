const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const server = fs.readFileSync(require.resolve('../server'), 'utf8').replace(/\r\n/g, '\n');
const start = server.indexOf("  if (pathname === '/api/achievements/steam') {");
const end = server.indexOf("  if (pathname === '/api/progress') {", start);
assert.ok(start >= 0 && end > start);
const branch = server.slice(start, end);
const achievements = [{ name: 'Fixture achievement', unlocked: true, unlockedAt: 123,
  description: 'Offline fixture', progress: { current: 20, target: 20 } }];

async function respond({ guest = false, remote = null, local = { available: true, achievements }, method = 'GET' } = {}) {
  let complete, status, headers, remoteCalls = 0, localCalls = 0;
  const result = new Promise(resolve => { complete = resolve; });
  vm.runInNewContext(`(function(){${branch}})()`, {
    pathname: '/api/achievements/steam', req: { method },
    res: { writeHead(code, values) { status = code; headers = values; },
      end(body) { complete({ status, headers, body: body ? JSON.parse(body) : null }); } },
    vmSetup: { isGuest: () => guest },
    vmFetch: async route => { assert.equal(route, '/api/achievements/steam'); remoteCalls++; return remote; },
    readSteamAchievements: () => { localCalls++; if (local instanceof Error) throw local; return local; },
  });
  return { ...await result, remoteCalls, localCalls };
}

const app = fs.readFileSync('assets/app/app.js', 'utf8').replace(/\r\n/g, '\n');
const uiStart = app.indexOf('async function loadSteamAchievements() {');
const uiEnd = app.indexOf('\n}\n', uiStart) + 2;
const ui = app.slice(uiStart, uiEnd);
async function bannerFor(body) {
  const banner = {};
  const context = { document: { querySelector: () => banner }, AbortSignal,
    fetch: async () => ({ ok: true, json: async () => body }),
    achievementIdOf: name => name, applySteamAchievements: () => {}, renderAchievements: () => {} };
  await vm.runInNewContext(ui + '\nloadSteamAchievements()', context);
  return banner.textContent;
}

(async () => {
  const guest = await respond({ guest: true });
  assert.equal(guest.body.hostFallback, false, 'Guest cache is local to the guest, not a host fallback');
  assert.equal(guest.body.sourceTransport, 'local');
  assert.equal(guest.body.source, 'steam-local-guest');
  assert.equal(guest.remoteCalls, 0, 'Guest must not attempt to relay through another VM');
  assert.equal(guest.localCalls, 1);
  assert.deepEqual(guest.body.achievements, achievements);

  // Compatibility: an older guest may still send the wrong fallback label.
  const relay = await respond({ remote: JSON.stringify({ available: true, achievements,
    hostFallback: true, source: 'steam-local-host' }) });
  assert.equal(relay.body.hostFallback, false, 'Successful VM relay must replace the guest fallback label');
  assert.equal(relay.body.sourceTransport, 'vm');
  assert.equal(relay.body.source, 'steam-local-vm');
  assert.equal(relay.localCalls, 0);
  assert.deepEqual(relay.body.achievements, achievements);
  assert.match(await bannerFor(relay.body), /VM.*Steam/);
  assert.doesNotMatch(await bannerFor(guest.body), /this PC|VM cache is not reachable/);

  for (const remote of [null, 'Not found', '{', JSON.stringify({ available: false, reason: 'No cache' })]) {
    const fallback = await respond({ remote });
    assert.equal(fallback.body.hostFallback, true);
    assert.equal(fallback.body.sourceTransport, 'host');
    assert.equal(fallback.body.source, 'steam-local-host');
    assert.deepEqual(fallback.body.achievements, achievements);
    assert.match(await bannerFor(fallback.body), /this PC/);
  }
  const missing = await respond({ guest: true, local: new Error('No cache') });
  assert.equal(missing.body.available, false);
  assert.equal(missing.body.reason, 'No cache');
  assert.equal(missing.body.hostFallback, false);
  assert.match(await bannerFor(missing.body), /unavailable: No cache/);
  for (const reply of [guest, relay, missing]) {
    assert.equal(reply.status, 200);
    assert.equal(reply.headers['Cache-Control'], 'no-store');
  }
  const denied = await respond({ method: 'POST' });
  assert.equal(denied.status, 405);
  assert.equal(denied.localCalls + denied.remoteCalls, 0);
  console.log('Achievement source labels preserve cache values and distinguish guest, VM relay and host fallback.');
})().catch(error => { console.error(error); process.exitCode = 1; });
