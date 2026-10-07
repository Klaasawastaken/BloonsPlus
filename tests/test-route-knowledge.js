const saveUpgradeNames = require('../data/catalogs/save-upgrade-names');
const knowledgeState = require('../data/catalogs/monkey-knowledge');
const assert=require('node:assert/strict'), fs=require('node:fs'), vm=require('node:vm'), path=require('node:path');
const source=fs.readFileSync('lib/automation.js','utf8');
const reqSource=source.slice(source.indexOf('function routeRequirements('),source.indexOf('\nfunction getRecordedCombos('));
const rankSource=source.slice(source.indexOf('function rankCandidatesForProfile('),source.indexOf('\nfunction restoreAttemptsLostToNavigation('));
const req=vm.runInNewContext(reqSource+';routeRequirements');
const upgrade=name=>Array(5).fill(`upgrade ${name} path 2`).join('\n');
const first='place dart a at 10, 10\n'+upgrade('a');
const second='place dart b at 20, 20\n'+upgrade('b');
assert.deepEqual(Array.from(req(first+'\n'+second,{dart:{}},{}).knowledge),['MasterDoubleCross']);
assert.equal(req(first+'\nsell a\n'+second,{dart:{}},{}).knowledge.length,0);
assert.deepEqual(Array.from(req(first+'\nsell a\nplace dart a at 10, 10\nupgrade a path 2',{dart:{}},{}).towers.dart),[0,0,5]);
function rank(knowledge) {
 const profile={available:true,monkeyKnowledge:knowledge};
 const fn=vm.runInNewContext(rankSource+';rankCandidatesForProfile',{saveUpgradeNames, knowledgeState, readLocalProgress:()=>profile,fs:{readFileSync:()=> '{}'},path,PROJECT_ROOT:'.'});
 return fn([{requirements:{towers:{},knowledge:['MasterDoubleCross']}},{requirements:{towers:{},knowledge:[]}}]);
}
assert.equal(rank({enabled:true,acquired:['MasterDoubleCross']})[0].profileReadiness.missing,0);
for(const mk of [{enabled:false,acquired:['MasterDoubleCross']},{enabled:true,acquired:[]},{}]) {
 const entry=rank(mk).find(x=>x.requirements.knowledge.length);
 assert.equal(entry.profileReadiness.missingKnowledge,1);assert.equal(entry.profileReadiness.missing,1);
 assert.match(entry.profileReadiness.knowledgeIssues[0],/MasterDoubleCross/);
}
assert.equal(rank({enabled:true,acquired:[{id:'MasterDoubleCross'}]})[0].profileReadiness.missing,0);
const individuallyDisabled = rank({enabled:true, acquired:['MasterDoubleCross'], disabled:['MasterDoubleCross']})
 .find(entry=>entry.requirements.knowledge.length);
assert.equal(individuallyDisabled.profileReadiness.missingKnowledge,1,
 'An individually disabled point cannot satisfy a route requirement');
console.log('Route knowledge requirements: concurrent T5s, selling, reused names and account state pass');
