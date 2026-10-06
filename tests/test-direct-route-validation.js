const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(require.resolve('../lib/automation'), 'utf8');
const start = source.indexOf('function startFarm(');
const prefix = source.slice(start, source.indexOf('  const job = engineLock.beginJob', start));
const catalog = {monkeys:{dart:{type:'primary'},sniper:{type:'military'}},heros:{}};
function check(text, mode = 'hard', missing = 0, available = true) {
  return vm.runInNewContext(prefix + 'return {ready:true};}\nstartFarm({type:"file",file:"route",gamemode:mode})', {
    mode, require:require('node:module').createRequire(require.resolve('../lib/automation')), path, AUTOBTD6_DIR:'.',
    fs:{readFileSync:()=>JSON.stringify(catalog)},
    engineLock:{getCurrentJob:()=>null}, FARM_TYPES:['file'], getRuntime:()=>({available:true}),
    parsePlaythroughFile:()=>({mapSlug:'logs',gamemodeSlug:'hard'}),
    MODES_REQUIRING_VERIFIED_ROUTE:new Set(), isMapUnlocked:()=>true,
    getPlaythroughContent:()=>text, getRecordedCombos:()=>({}),
    routeRequirements:()=>({hero:null,towers:{dart:[1,0,0]}}),
    rankCandidatesForProfile:entries=>entries.map(entry=>({...entry,profileReadiness:{missing,unknown:0}})),
    readLocalProgress:()=>({available}),
  });
}
assert.match(check('upgrade absent path 0').error || '', /unplaced/i);
assert.match(check('place sniper s0 at 10, 20', 'primary_only').error || '', /forbidden/i);
assert.match(check('place dart d0 at 10, 20\nupgrdae d0 path 0').error || '', /malformed/i);
assert.match(check('place dart d0 at 10, 20', 'hard', 1).error || '', /prerequisites/i,
  'A route absent from sweep candidates still needs account requirements checked');
assert.equal(check('place dart d0 at 10, 20').ready, true);
assert.match(check('place dart d0 at 10, 20\nspecial2 d0', 'hard', 1, false).error || '', /prerequisites/i,
  'Explicit second-special binding failure must block even without a readable profile');
console.log('Direct route starts enforce command, mode and account requirements.');
