const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const {selectSteamAccount}=require('../lib/steam-account');
for (const [ids,account,expected] of [
 [['111','222'],{state:'active',id:'222'},'222'],
 [['111','222'],{state:'active',id:'333'},null],
 [['111','222'],{state:'unknown'},null],
 [['111'],{state:'unknown'},'111'],
 [['111','111'],{state:'unknown'},'111'],
 [['111'],{state:'inactive'},null],
 [[],{state:'unknown'},null],
]) assert.equal(selectSteamAccount(ids,account),expected);
const accountSource=fs.readFileSync('lib/steam-account.js','utf8');
const regFn=accountSource.slice(accountSource.indexOf('function readActiveSteamAccount('),accountSource.indexOf('function selectSteamAccount('));
for(const [out,expected] of [['ActiveUser REG_DWORD 0xde',{state:'active',id:'222'}],['ActiveUser REG_DWORD 0x0',{state:'inactive',id:null}],['bad',{state:'unknown',id:null}]]) {
 assert.deepEqual(JSON.parse(JSON.stringify(vm.runInNewContext(regFn+';readActiveSteamAccount()',{execFileSync:()=>out}))),expected);
}
const profileSource=fs.readFileSync('lib/btd6-save-progress.js','utf8');
const profileFn=profileSource.slice(profileSource.indexOf('function findProfileSave('),profileSource.indexOf('function decodeProfileSave('));
const statsSource=fs.readFileSync('lib/steam-progress.js','utf8');
const statsFn=statsSource.slice(statsSource.indexOf('function findStatsFile('),statsSource.indexOf('let cache ='));
for(const account of [{state:'active',id:'222'},{state:'unknown'},{state:'inactive'}]) {
 const fakeFs={readdirSync:()=>['111','222'].map(name=>({name,isDirectory:()=>true})),existsSync:p=>p.endsWith(path.join('960090','local','Profile.Save'))};
 const result=vm.runInNewContext(profileFn+';findProfileSave()',{fs:fakeFs,path,APP_ID:'960090',steamRoots:()=>['fake-steam'],selectSteamAccount,readActiveSteamAccount:()=>account});
 assert.equal(result,account.state==='active'?path.join('fake-steam','userdata','222','960090','local','Profile.Save'):null);
 const stats=vm.runInNewContext(statsFn+';findStatsFile("fake-steam",account)',{path,account,selectSteamAccount,fs:{readdirSync:()=>['UserGameStats_111_960090.bin','UserGameStats_222_960090.bin','UserGameStatsSchema_960090.bin']}});
 assert.equal(stats,account.state==='active'?path.join('fake-steam','appcache','stats','UserGameStats_222_960090.bin'):null);
}
const cacheFn=statsSource.slice(statsSource.indexOf('let cache ='),statsSource.indexOf('function computeSteamAchievements('));
let active='111',calls=0;const cacheCtx={readActiveSteamAccount:()=>({state:'active',id:active}),computeSteamAchievements:a=>{calls++;return {account:a.id};}};
vm.runInNewContext(cacheFn+';readSteamAchievements();readSteamAchievements()',cacheCtx);
assert.equal(calls,1);active='222';vm.runInNewContext('readSteamAchievements()',cacheCtx);assert.equal(calls,2);
console.log('Account selection: active identity, ambiguity, logged-out state, profile/stats parity and cache switching pass.');
