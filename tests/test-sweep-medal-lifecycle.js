const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'lib/automation.js'), 'utf8').replace(/\r\n/g, '\n');
const {medalsFromMapRecord} = require(path.join(root, 'data/catalogs/medal-progress'));
const {canAttempt} = require(path.join(root, 'lib/replay-monitor'));
function fn(name) {
  const start = source.indexOf(`function ${name}(`);
  assert.ok(start >= 0, name);
  const from = source.slice(start-6,start) === 'async ' ? start-6 : start;
  return source.slice(from, source.indexOf('\n}\n', start)+2);
}
const production = [source.slice(source.indexOf('const CHIMPS_CRITICAL_PATH ='), source.indexOf('function getMissingMedals(')),
  ...['medalProfileIdentity','rememberConfirmedMedal','mergeSavedMedalHistory','syncMedalsFromObservations','loadMedalsFromProfileSave','savedMedalState','getMissingMedals','sweepCandidates',
      'confirmClear','waitForSavedClear','saveSweepProgress','profileRouteAttempts','saveRouteAttempt','recordObservedClear','ensureOutcomeCount',
      'runBlackBorderSweep'].map(fn)].join('\n');
function fixture() {
  const disk = new Map();
  const result = {runs:[],logs:[],waits:[],failures:[]};
  let progress = {}, profile;
  let rankHook = null, runHook = null, waitHook = null, readHook = null, catalogHook = null;
  const mapNames = {example:{name:'Example'}};
  const cfg = {medals:{example:{}}, unlocked_maps:{example:true},bloonsPlusMedalsInitialized:true,bloonsPlusMedalsVerifiedV2:true};
  disk.set('config',JSON.stringify(cfg)); disk.set('maps',JSON.stringify(mapNames));disk.set('observations',JSON.stringify({maps:{}}));
  const combos = {example:{easy:[{filename:'candidate-a',isOriginalGamemode:true}], medium:[{filename:'candidate-b',isOriginalGamemode:true}]}};
  const fakeFs = {
    readFileSync(file) {assert.ok(disk.has(file), `Unexpected read ${file}`);return disk.get(file);},
    writeFileSync(file,data) {assert.ok(['config','observations.tmp'].includes(file), `Unexpected write ${file}`);disk.set(file,data);},
    renameSync(from,to) {assert.equal(from,'observations.tmp');assert.equal(to,'observations');disk.set(to,disk.get(from));disk.delete(from);}
  };
  const clone = value => JSON.parse(JSON.stringify(value));
  const context = {
    path, createHash:require('node:crypto').createHash, fs:fakeFs,USERCONFIG_PATH:'config',MAPS_PATH:'maps',OBSERVATIONS_PATH:'observations',MODE_ATTEMPTS_KEY:'attempts',
    normalizeMapName:name=>name.toLowerCase().replace(/[^a-z0-9]/g,''),medalsFromMapRecord,canAttempt,
    readLocalProgress:()=>readHook ? readHook() : profile,loadProgress:()=>clone(progress),saveProgress:value=>{progress=clone(value);},
    getAvailableCombos:async()=>{if(catalogHook)catalogHook();return combos;}, isMapUnlocked:()=>true,buildSweepMapOrder:maps=>maps,
    restoreAttemptsLostToNavigation:identity=>context.profileRouteAttempts(clone(progress),identity), getMapMechanics:()=>({status:'standard-visual-check'}),
    UNRELIABLE_MAPS:new Set(),MODES_REQUIRING_VERIFIED_ROUTE:new Set(),SWEEP_ENGINE_VERSION:'fixture',
    categoryForMapSlug:()=> 'Beginner',rankCandidatesForProfile:entries=>{if(rankHook)rankHook();return entries;},
    routeAttemptHash:file=>file+'-hash',MAX_GAME_RELAUNCHES:3,
    pushLog:(_job,line)=>result.logs.push(line),recordMedalGain:()=>{},markRouteVerified:()=>{},
    recordRouteFailure:(...args)=>{result.failures.push(args);return {};},failedHeroSelectionBeforeGame:()=>false,
    setTimeout:(resolve,ms)=>{result.waits.push(ms);assert.ok(result.waits.length<30,'Unbounded wait');if(waitHook)waitHook(ms);resolve();},
    runOne:async(job,args)=>{result.runs.push(args);assert.ok(result.runs.length<10,'Unbounded replay');return runHook(job,args);}
  };
  vm.createContext(context);vm.runInContext(production,context);
  const setProfile = (easy,medium=true,file='account-a') => {
    profile={available:true,file,mapProgress:{Example:{difficult:{Easy:{modes:{Standard:easy,PrimaryOnly:true,Deflation:true}},
      Medium:{modes:{Standard:medium,MilitaryOnly:true,Reverse:true,Apopalypse:true}},
      Hard:{modes:{Standard:true,MagicOnly:true,DoubleMoabHealth:true,HalfCash:true,AlternateBloonsRounds:true,Impoppable:true,Clicks:true}}}}}};
  };
  setProfile(false);
  return {result,context,disk,combos,setProfile,get profile(){return profile;},set profile(p){profile=p;},get progress(){return progress;}, get attempts(){return progress.routeAttemptsByProfile?.[context.job.medalProfileIdentity]||{};},
    set catalogHook(h){catalogHook=h;},
    set readHook(h){readHook=h;},
    set rankHook(h){rankHook=h;},set runHook(h){runHook=h;},set waitHook(h){waitHook=h;},
    async run(){const job={stopRequested:false};context.job=job;await vm.runInContext('runBlackBorderSweep(job)',context);return job;}};
}
(async()=>{
 const findings=[];
 {const f=fixture();f.setProfile(true);await f.run();assert.equal(f.result.runs.length,0);assert.equal(f.progress.blackBorderSweep.status,'complete');findings.push('PASS: all owned medals launch no replay');}
 {const f=fixture();f.rankHook=()=>f.setProfile(true);await f.run();assert.equal(f.result.runs.length,0);assert.equal(f.progress.blackBorderSweep.counts.confirmed,0);findings.push('PASS: medal becomes owned after candidate selection; final gate skips it');}
 {const f=fixture();f.setProfile(null,false);f.runHook=async()=>{f.setProfile(null,true);return {exitCode:0,victoryObserved:true};};await f.run();assert.equal(f.result.runs.length,1);assert.equal(f.result.runs[0][2],'medium');assert.equal(f.progress.blackBorderSweep.counts.confirmed,1);findings.push('PASS: unreadable Easy skipped; readable missing Medium can clear');}
 {const f=fixture();f.runHook=async()=>({exitCode:0,victoryObserved:true});let waits=0;f.waitHook=()=>{if(++waits===2)f.setProfile(true);};await f.run();assert.equal(f.progress.blackBorderSweep.counts.confirmed,1);assert.equal(f.result.waits.length,2);await f.run();assert.equal(f.result.runs.length,1);findings.push('PASS: delayed saved medal confirmed, then skipped on next sweep');}
 {const f=fixture();f.profile={available:false};f.waitHook=()=>{f.context.job.stopRequested=true;};await f.run();assert.equal(f.result.runs.length,0);assert.deepEqual(f.result.waits,[15000]);findings.push('PASS: unavailable profile waits without gameplay and honors stop');}
 {const f=fixture();f.runHook=async()=>({exitCode:0,victoryObserved:true});await f.run();assert.equal(f.progress.blackBorderSweep.counts.confirmed,0);assert.equal(f.result.waits.length,10);f.setProfile(true);await f.run();assert.equal(f.result.runs.length,1);findings.push('PASS: late save beyond confirmation window remains uncredited and is skipped when eventually owned');}
 {const f=fixture();f.runHook=async()=>({exitCode:1,defeatObserved:true,notable:['screen INGAME!','screen DEFEAT!']});await f.run();assert.equal(f.result.failures.length,1);await f.run();assert.equal(f.result.runs.length,1);assert.equal(f.attempts.example.easy['candidate-a'].attempts,1);findings.push('PASS: played failure remains consumed after sweep restart');}
 {const f=fixture();f.combos.example.easy.push({filename:'alternate',isOriginalGamemode:true});f.runHook=async(_job,args)=>{if(args[1]==='candidate-a')return {exitCode:1,defeatObserved:true,notable:['screen INGAME!','screen DEFEAT!']};f.setProfile(true);return {exitCode:0,victoryObserved:true};};await f.run();assert.equal(f.result.runs.length,2);assert.equal(f.result.failures.length,1);assert.equal(f.progress.blackBorderSweep.counts.confirmed,1);assert.equal(f.attempts.example.easy['candidate-a'].outcome,'unconfirmed');findings.push('PASS: alternate candidate clears while prior defeat stays recorded');}
 {const f=fixture();f.runHook=async()=>{f.setProfile(true);return {exitCode:0,victoryObserved:true};};await f.run();f.setProfile(false);await f.run();assert.equal(f.result.runs.length,1);findings.push('PASS: unchanged cleared candidate remains blocked despite save regression');}
 {const f=fixture();f.runHook=async()=>{f.setProfile(true);return {exitCode:0,victoryObserved:true};};await f.run();f.setProfile(false);f.combos.example.easy=[{filename:'candidate-new-version',isOriginalGamemode:true}];await f.run();assert.equal(f.result.runs.length,1,'A regressed save must not replay a confirmed medal through another candidate');findings.push('PASS: confirmed medal survives save regression and changed candidate');}
 {const f=fixture();f.runHook=async()=>{f.setProfile(true,true,'account-b');return {exitCode:0,victoryObserved:true};};await f.run();assert.equal(f.progress.blackBorderSweep.counts.confirmed,0,'A different save source cannot confirm this run');assert.equal(f.progress.blackBorderSweep.status,'blocked');findings.push('PASS: changed source cannot receive clear credit');}
 {const f=fixture();f.runHook=async(job)=>{f.setProfile(true);job.stopAfterReplay=true;return {exitCode:0,victoryObserved:true};};await f.run();f.setProfile(false);f.combos.example.easy=[{filename:'different-candidate',isOriginalGamemode:true}];await f.run();assert.equal(f.result.runs.length,1,'Stop after replay must persist the earned medal before the loop exits');findings.push('PASS: stop-after-replay persists confirmed ownership');}
 {const f=fixture();f.setProfile(true);await f.run();f.setProfile(false,true,'account-b');f.runHook=async()=>{f.setProfile(true,true,'account-b');return {exitCode:0,victoryObserved:true};};await f.run();assert.equal(f.result.runs.length,1,'Another source must not inherit the first source ownership');assert.equal(Object.keys(f.progress.savedMedalsByProfile).length,2);findings.push('PASS: ownership histories stay isolated between save sources');}
 {const f=fixture();f.rankHook=()=>f.setProfile(false,true,'account-b');await f.run();assert.equal(f.result.runs.length,0);assert.equal(f.progress.blackBorderSweep.status,'blocked');findings.push('PASS: source change before launch blocks input');}
 {const f=fixture();f.runHook=async()=>{f.setProfile(true);return {exitCode:0,victoryObserved:true};};await f.run();f.setProfile(false,true,'account-b');f.runHook=async()=>{f.setProfile(true,true,'account-b');return {exitCode:0,victoryObserved:true};};await f.run();assert.equal(f.result.runs.length,2,'Account A clear must not block the same missing route for B');findings.push('PASS: route admission is isolated between save sources');}
 {const f=fixture();f.runHook=async()=>{f.setProfile(true);const a=f.profile;f.setProfile(true,true,'account-b');const b=f.profile;let reads=0;f.readHook=()=>reads++===0?b:a;return {exitCode:0,victoryObserved:true};};await f.run();assert.equal(f.progress.blackBorderSweep.counts.confirmed,0,'A detected source mismatch must stay rejected when later reads return to the original source');assert.equal(f.progress.blackBorderSweep.status,'blocked');findings.push('PASS: source mismatch is latched through confirmation');}
 {const f=fixture();let changed=false;f.rankHook=()=>{if(changed)return;changed=true;f.setProfile(true);const owned=f.profile;f.setProfile(false);const regressed=f.profile;let reads=0;f.readHook=()=>reads++===0?owned:regressed;};f.runHook=async()=>({exitCode:1,defeatObserved:true});await f.run();await f.run();assert.equal(f.result.runs.length,0,'The exact owned launch snapshot must persist before a subsequent read regresses');findings.push('PASS: final launch-gate ownership survives an immediately regressed read');}
 {const f=fixture();f.setProfile(true);await f.run();f.profile={available:true,file:'account-b',mapProgress:{}};await f.run();assert.equal(f.progress.blackBorderSweep.status,'incomplete','Missing records on a different source cannot inherit the previous source completion');assert.equal(f.result.runs.length,0);assert.equal(JSON.parse(f.disk.get('config')).medals.example.easy,null);findings.push('PASS: missing map on changed source stays unknown and incomplete');}
 {const f=fixture();f.setProfile(true);f.catalogHook=()=>f.setProfile(false,true,'account-b');await f.run();assert.equal(f.progress.blackBorderSweep.status,'blocked','A source change while preparing an empty queue cannot report completion for the new account');assert.equal(f.result.runs.length,0);findings.push('PASS: empty-queue completion remains bound to its starting source');}
 console.log(findings.join('\n'));
 console.log(findings.length+' complete sweep lifecycle checks passed without gameplay.');
})().catch(error=>{console.error(error);process.exitCode=1;});