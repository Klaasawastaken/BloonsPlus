const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { redact } = require('../assets/app/support-report');

const fields = ['password', 'passwd', 'secret', 'authorization', 'token', 'api_key',
  'access-token', 'refresh_token', 'X-Bloons-Setup-Key', 'sessionId', 'account_id',
  'playerName', 'steam_name', 'username', 'hostName'];
const cases = fields.flatMap(field => [
  `{"${field}":"fixture-secret","round":60,"map":"skulltweak"}`,
  `{'${field}': 'fixture-secret', 'round': 60, 'map': 'skulltweak'}`,
  `${field}=fixture-secret, round=60, map=skulltweak`,
  `{"${field}":"fixture-prefix\\\"fixture-secret","round":60,"map":"skulltweak"}`,
  `{'${field}': 'fixture-prefix\\'fixture-secret', 'round':60, 'map':'skulltweak'}`,
]).concat([
  'Authorization: Bearer fixture-secret, round=60, map=skulltweak',
  'Authorization: Basic fixture-secret, round=60, map=skulltweak',
  '{"authorization":"Bearer fixture-prefix\\\"fixture-secret","round":60,"map":"skulltweak"}',
  "{'authorization':'Bearer fixture-prefix\\'fixture-secret','round':60,'map':'skulltweak'}",
  '{"password":"Authorization: Bearer fixture-prefix\\\"fixture-secret","round":60,"map":"skulltweak"}',
  "{'password':'Authorization: Basic fixture-prefix\\'fixture-secret','round':60,'map':'skulltweak'}",
  ...['\n', '\r\n'].map(newline => "{'password': 'fixture-prefix\\" + newline + "fixture-secret', 'round':60, 'map':'skulltweak'}"),
]);
for (const input of cases) {
  const actual = redact(input);
  assert.ok(!actual.includes('fixture-secret') && !actual.includes('fixture-prefix'), 'Sensitive structured value survived');
  assert.ok(actual.includes('60') && actual.includes('skulltweak'), 'Run context lost');
  assert.equal(redact(actual), actual, 'Second redaction changed output');
}
for (const input of [
  '{"password":"fixture-prefix fixture-secret',
  "{'password': 'fixture-prefix fixture-secret",
  '{"password":"fixture-prefix\\',
  '-----BEGIN ' + 'OPENSSH PRIVATE KEY-----\nfixture-secret',
  '-----BEGIN TOKEN-----\nfixture-secret\n-----END TOKEN-----',
]) assert.ok(!/fixture-(?:prefix|secret)/.test(redact(input)), 'Truncated or block credential survived');

// Exercise the actual browser report handlers with synthetic logs and a local
// DOM stand-in. No GitHub page opens and no network request is made.
const elements = new Map();
function element(id) {
  if (!elements.has(id)) elements.set(id, { value:'', handlers:{},
    addEventListener(type, handler) { this.handlers[type] = handler; },
    showModal() {}, close() {}, click() {} });
  return elements.get(id);
}
const browser = { document: {
  querySelector: element,
  querySelectorAll: () => [element('#report-issue'), element('#settings-report-issue')],
  createElement: () => element('download-anchor'),
}, latestRunLog: cases.join('\n'), latestAutomationStatus: {vm:true}, setTimeout: () => {},
  URL: {createObjectURL(blob) { browser.download = blob.text; return 'blob:fixture'; }, revokeObjectURL() {}},
  Blob: class {constructor(parts) {this.text=parts.join('');}}, };
browser.window = browser;
vm.createContext(browser);
vm.runInContext(fs.readFileSync(require.resolve('../assets/app/support-report'), 'utf8'), browser);
for (const input of cases) assert.equal(browser.BloonsSupport.redact(input), redact(input));
const app = fs.readFileSync(require.resolve('../assets/app/app'), 'utf8');
const start = app.indexOf('// Reports include only a reviewed, redacted excerpt;');
const end = app.indexOf('// ', start + 3);
assert.ok(start >= 0);
// This report block ends with its download handler; keep the exact production
// body and fail if its boundary moves instead of evaluating unrelated app code.
const block = app.slice(start, end < 0 ? undefined : end).trim();
assert.ok(block.endsWith('});'));
vm.runInContext(block, browser);
element('#report-description').value = '{"accountId":"fixture-secret"}';
element('#report-issue').handlers.click();
const report = new URL(element('#report-submit').href).searchParams.get('body');
for (const output of [report, element('#report-preview').textContent]) {
  assert.ok(!/fixture-(?:prefix|secret)/.test(output), 'Report preview/link leaked a value');
  assert.ok(output.includes('skulltweak'));
}
element('#report-download').handlers.click();
assert.ok(!/fixture-(?:prefix|secret)/.test(browser.download), 'Download leaked a value');
assert.ok(browser.download.includes('skulltweak'));
// Full route-log downloads use a separate handler. Check that every exported
// field passes through the same filter while private source records stay intact.
(async () => {
  const failures = [{at:'2026-10-07', map:'skulltweak', gamemode:'hard', route:'synthetic.btd6',
    lastRound:60, finalRound:80, reason:'accountId=fixture-secret', fullLog:cases}];
  const original = JSON.stringify(failures);
  browser.fetch = async url => {
    assert.equal(url, '/api/route-failures');
    return {ok:true, json:async () => ({available:true, failures})};
  };
  browser.AbortSignal = AbortSignal;
  browser.notify = message => {browser.notice=message;};
  const formatterStart = app.indexOf('function formatRouteFailures(');
  const formatterEnd = app.indexOf('async function loadRouteFailures()', formatterStart);
  const downloadStart = app.indexOf("document.querySelector('#download-route-failures')");
  const downloadEnd = app.indexOf("document.querySelector('#farm-file')", downloadStart);
  assert.ok(formatterStart>=0 && formatterEnd>formatterStart && downloadStart>=0 && downloadEnd>downloadStart);
  vm.runInContext(app.slice(formatterStart, formatterEnd) + app.slice(downloadStart, downloadEnd), browser);
  const button=element('#download-route-failures');
  browser.download=null;
  await button.handlers.click({currentTarget:button});
  assert.ok(browser.download && !/fixture-(?:prefix|secret)/.test(browser.download), 'Full route download leaked a value');
  assert.ok(browser.download.includes('round 60/80') && browser.download.includes('skulltweak'));
  assert.equal(JSON.stringify(failures), original, 'Private source records were changed');
  assert.equal(button.disabled, false);
  browser.download=null;
  browser.BloonsSupport=undefined;
  await button.handlers.click({currentTarget:button});
  assert.equal(browser.download, null, 'Missing privacy helper permitted a raw download');
  assert.equal(button.disabled, false);
  assert.ok(browser.notice);
  console.log('Support redaction: structured fields, truncation, browser parity and both report/route export boundaries passed');
})().catch(error => {console.error(error);process.exitCode=1;});
