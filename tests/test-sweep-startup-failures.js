const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require.resolve('../lib/automation'), 'utf8');
const start = source.indexOf('      const result = await runOne(job,');
const code = source.slice(start, source.indexOf('      const cleared = await waitForSavedClear', start));
const heroFailureStart = source.indexOf('function failedHeroSelectionBeforeGame(');
const heroFailure = source.slice(heroFailureStart, source.indexOf('function stateMatchesAttempt(', heroFailureStart));
async function check(result, relaunch = false) {
  const records = [];
  const context = {
    job:{}, entry:{filename:'route'}, gamemode:'hard', map:'logs', counts:{skippedModes:0},
    relaunches:0, MAX_GAME_RELAUNCHES:2, focusFailures:0,
    attemptedFiles:new Set(['route']), attempted:new Set(),
    runOne:async()=>result, relaunchGame:async()=>relaunch,
    recordRouteFailure:(...args)=>records.push(args),
    saveSweepProgressFor:()=>{}, pushLog:()=>{}, markMedalSeen:()=>{},
    setTimeout:fn=>fn(),
  };
  await vm.runInNewContext(heroFailure + '(async()=>{for(let pass=0;pass<1;pass++){'+code+'}})()', context);
  return records;
}
(async()=>{
  for(const reason of ['game-unavailable','invalid-window','spawn-error','stop-failed']) {
    assert.equal((await check({reason})).length, 1, reason);
  }
  assert.equal((await check({reason:'game-unavailable'}, true)).length, 1, 'Relaunch must preserve evidence too');
  for(const line of ['could not be focused','Traceback (most recent call last)','stopping before map click','map page is not visible','map tile did not open','ERROR hero Select button is unconfirmed']) {
    assert.equal((await check({reason:'exit',exitCode:1,notable:[line]})).length, 1, line);
  }
  assert.equal((await check({reason:'exit',exitCode:0,notable:['MEDAL_ALREADY_EARNED']})).length, 0);
  assert.equal((await check({reason:'exit',exitCode:0,notable:['screen INGAME!']})).length, 0, 'Normal outcomes are recorded later');
  console.log('Pre-game failures persist without consuming route attempts.');
})().catch(error=>{console.error(error);process.exitCode=1;});
