const assert=require('node:assert/strict'); const fs=require('node:fs'); const vm=require('node:vm');
const source=fs.readFileSync('lib/automation.js','utf8');
const helper=source.slice(source.indexOf('function failedHeroSelectionBeforeGame('),source.indexOf('\nfunction stateMatchesAttempt(',source.indexOf('function failedHeroSelectionBeforeGame(')));
const start=source.indexOf('      const heroNavigationFailed =');
const branch=source.slice(start,source.indexOf('      const cleared = await waitForSavedClear',start));
function probe(notable,defeatObserved=false){
 const env={result:{notable,defeatObserved},map:'dark_castle',gamemode:'military_only',entry:{filename:'candidate'},job:{},
 attemptedFiles:new Set(['candidate']),records:0,progress:[],messages:[],played:false};
 env.recordRouteFailure=()=>env.records++; env.pushLog=(_,line)=>env.messages.push(line);env.saveSweepProgressFor=value=>env.progress.push(value);
 vm.runInNewContext(helper+'\nfor(let pass=0;pass<1;pass++){'+branch+'played=true;}',env);
 return env;
}
for(const line of ['ERROR hero obyn_greenfoot was not found in the picker','ERROR hero selection was not confirmed after 3 Select attempts','ERROR hero Select button is unconfirmed']){
 const r=probe([line]);assert.equal(r.records,1);assert.equal(r.played,false);assert.equal(r.attemptedFiles.size,0);assert.match(r.progress[0].reason,/hero selection/);
}
for(const lines of [['ERROR hero obyn_greenfoot was not found in the picker','screen INGAME!'],['goal GOTO_INGAME fullfilled!','ERROR hero selection was not confirmed'],['screen INGAME_PAUSED!','ERROR hero Select button is unconfirmed']]){
 const r=probe(lines);assert.equal(r.records,0);assert.equal(r.played,true);assert.equal(r.attemptedFiles.size,1);
}
assert.equal(probe(['ERROR hero selection was not confirmed'],true).played,true);
assert.equal(probe(['DEBUG hero obyn_greenfoot found visually on page 0']).played,true);
console.log('Actual sweep branch preserves pre-game hero attempts and does not bypass gameplay failures.');
