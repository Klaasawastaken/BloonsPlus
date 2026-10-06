// Persist the complete screenshot path, including spaces in Windows folders.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(require.resolve('../lib/automation'), 'utf8');
const start = source.indexOf('function stateMatchesAttempt(');
const code = source.slice(start, source.indexOf('\nfunction loadFailureHistory(', start));
const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'bloons-failure-path-'));
try {
  const recordPath = path.join(folder, 'failures.json');
  const environment = {fs, path, AUTOBTD6_DIR:folder, FAILURES_PATH:recordPath,
    FAILURES_LOG_PATH:path.join(folder, 'failures.log'), FINAL_ROUND:{hard:80},
    loadFailureHistory:()=>[], classifyRouteFailure:()=> 'navigation-bug', classifyLoss:()=> 'navigation'};
  vm.runInNewContext(code + '\nthis.record = recordRouteFailure;', environment);
  const shot = String.raw`C:\Users\[USER]\Documents\Bloons App\resources\app\autobtd6\failure-shots\hero-picker.png`;
  environment.record('sanctuary', 'hard', 'candidate.btd6', {
    runStartedAt:Date.now(), reason:'exit', exitCode:2,
    notable:['FAILURE_SHOT older.png', 'FAILURE_SHOT ' + shot], raw:[]});
  const history = JSON.parse(fs.readFileSync(recordPath, 'utf8'));
  assert.equal(history[0].screenshot, shot, 'Failure history truncated the frame path at the first space');
  for (const suffix of [' action={"action":"place","pos":[12,34]}', ' reason=round/cash unreadable', ' reason=upgrade-unconfirmed']) {
    environment.record('sanctuary', 'hard', 'candidate.btd6', {
      runStartedAt:Date.now(), reason:'exit', exitCode:2, notable:['[time] FAILURE_SHOT ' + shot + suffix], raw:[]});
    assert.equal(JSON.parse(fs.readFileSync(recordPath, 'utf8'))[0].screenshot, shot,
      'The production diagnostic suffix is not part of the filename');
  }
  environment.record('sanctuary', 'hard', 'candidate.btd6', {
    runStartedAt:Date.now(), reason:'exit', exitCode:2, notable:['DEBUG no frame'], raw:[]});
  assert.equal(JSON.parse(fs.readFileSync(recordPath, 'utf8'))[0].screenshot, null);
  console.log('Failure screenshot paths retain spaces and the newest saved frame.');
} finally {
  const resolved = path.resolve(folder);
  if (!resolved.startsWith(path.resolve(os.tmpdir()) + path.sep) || !path.basename(resolved).startsWith('bloons-failure-path-'))
    throw new Error('Unsafe failure fixture cleanup path');
  fs.rmSync(resolved, {recursive:true, force:true});
}
