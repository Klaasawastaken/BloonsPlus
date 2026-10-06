const assert = require('node:assert/strict'), fs = require('node:fs'), vm = require('node:vm'), path = require('node:path');
const source = fs.readFileSync('lib/automation.js','utf8').replace(/\r\n/g,'\n');
const fn = name => {const start=source.indexOf(`function ${name}(`); return source.slice(start,source.indexOf('\n}\n',start)+2);};
const blocked='logs#hard#1920x1080#converted#source_btd6bot.btd6';
const moving='sanctuary#hard#1920x1080#converted#source_btd6bot#selection-preserved.btd6';
const incompatible='sanctuary#medium#1920x1080#source_btd6bot#compat#from_hard.btd6';
function combos(confirmed={}, routeTexts={}, files=[blocked,moving,incompatible]) {
  const context={path,PROJECT_ROOT:'/project',AUTOBTD6_DIR:'/auto',PLAYTHROUGHS_DIR:'/routes',ONLINE_GUIDE_SOURCES_PATH:'/guides',
    CHIMPS_REUSE_MODES:['easy','medium','hard','impoppable'],HARD_REUSE_MODES:['easy','medium'],
    REUSE_MODES_BY_SOURCE:{hard:['easy','medium'],chimps:['easy','medium','hard','impoppable']},
    fs:{readFileSync(file){
      if(file.endsWith('towers.json'))return JSON.stringify({monkeys:{dart:{type:'primary'}},heros:{}});
      if(file.endsWith('route-selection-guard.json'))return JSON.stringify({[blocked]:{hash:'audited'}});
      if(file==='/guides')return '{}';
      return routeTexts[path.basename(file)] || 'place dart dart0 at 100, 200\n';
    }},require:module=>require('../lib/'+module.replace('./','')),
    loadVerifiedRoutes:()=>confirmed,routeHash:()=> 'audited',routeRequirements:()=>({})};
  vm.runInNewContext(['parsePlaythroughFile','reusePreservesOpeningPhase','routeCandidatePriority','compareRouteCandidates','getRecordedCombos'].map(fn).join('\n')+
    `\nfunction listPlaythroughs(){return ${JSON.stringify(files)}.map(parsePlaythroughFile);} this.result=getRecordedCombos();this.phase=reusePreservesOpeningPhase;this.parse=parsePlaythroughFile;`,context);
  return context;
}
const missing=combos();
assert.equal(missing.result.logs,undefined);
assert.ok(missing.result.sanctuary.hard.some(route=>route.filename===moving));
assert.equal(missing.result.sanctuary.medium,undefined);
assert.equal(missing.result.sanctuary.easy,undefined);
assert.equal(missing.phase('sanctuary','chimps','impoppable'),true);
assert.equal(missing.phase('geared','hard','medium'),false);
assert.equal(missing.phase('logs','hard','medium'),true);
assert.equal(missing.parse(incompatible).converted,true);
assert.equal(missing.parse(incompatible).generatedSourceGamemode,'hard');
const won=combos({[blocked]:{hard:{hash:'audited'}},[incompatible]:{medium:{hash:'audited'}}});
assert.ok(won.result.logs.hard.some(route=>route.filename===blocked));
assert.ok(won.result.sanctuary.medium.some(route=>route.filename===incompatible));
const manual='logs#chimps#1920x1080#converted#source_btd6bot#manual-preserved.btd6';
const renamed='logs#hard#1920x1080#converted#source_btd6bot#fromChimps.btd6';
const manualBody='autostart on\nsource round 6\nautostart off\nplace dart dart0 at 100, 200\nplay twice\nsource round 7 after play\nround 8\nsource round 8\n';
const controls=combos({}, {[manual]:manualBody,[renamed]:manualBody}, [manual,renamed]);
assert.ok(controls.result.logs.chimps.some(route=>route.filename===manual));
assert.ok(controls.result.logs.impoppable.some(route=>route.filename===manual));
for(const mode of ['easy','medium','hard']) assert.equal(controls.result.logs[mode],undefined,mode);
assert.equal(controls.phase('logs','chimps','hard',manualBody),false);
assert.equal(controls.phase('logs','chimps','impoppable',manualBody),true);
assert.equal(controls.phase('logs','hard','medium','source round 3\n'),false);
assert.equal(controls.phase('logs','deflation','deflation','source round 31\n'),true);
assert.equal(controls.phase('logs','chimps','easy','round 6\n'),true,'ordinary routes keep approved reuse');
const confirmedControls=combos({[manual]:{hard:{hash:'audited'}},[renamed]:{hard:{hash:'audited'}}},
  {[manual]:manualBody,[renamed]:manualBody},[manual,renamed]);
assert.ok(confirmedControls.result.logs.hard.some(route=>route.filename===renamed));
const confirmedReuse=combos({[manual]:{hard:{hash:'audited'}}},{[manual]:manualBody},[manual]);
assert.ok(confirmedReuse.result.logs.hard.some(route=>route.filename===manual));
const {validateRoute,strategySignature}=require('../lib/route-validation');
const catalog=JSON.parse(fs.readFileSync('autobtd6/towers.json','utf8'));
assert.deepEqual(validateRoute('place mortar a at 100, 200\nupgrade a path 0 at 300, 400\nretarget a to 800, 900 at 500, 600\nspecial a at 600, 700\nsell a at 700, 800','hard',catalog),[]);
assert.ok(validateRoute('place dart a at 100, 200\nupgrade a path 0 at -1, 300','hard',catalog).length);
assert.notEqual(strategySignature('place dart a at 100, 200\nupgrade a path 0 at 300, 400'),strategySignature('place dart a at 100, 200\nupgrade a path 0 at 301, 400'));
console.log('Audited copies blocked by content; exact target wins retained; phase-incompatible reuse excluded; selector grammar valid.');
