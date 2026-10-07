// Synthetic profiles only: no player save, account totals or live input.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {createRequire} = require('node:module');
const knowledge = require('../data/catalogs/monkey-knowledge');
const nodes = ['BonusMonkey', 'BonusGlueGunner', 'MasterDoubleCross'];
const profile = (disabled, enabled=true) => ({acquired:[...nodes], disabled, enabled});
assert.equal(knowledge.activity(profile(['BonusMonkey']), 'BonusMonkey'), false);
assert.equal(knowledge.activity(profile(['BonusMonkey']), 'BonusGlueGunner'), true);
assert.equal(knowledge.activity(profile(['BonusMonkey']), 'MasterDoubleCross'), true);
assert.deepEqual(knowledge.summarize(profile(['BonusMonkey'])), {state:'partial',active:nodes.slice(1)});
assert.deepEqual(knowledge.summarize(profile([],false)), {state:'disabled',active:[]});
assert.deepEqual(knowledge.summarize(profile([])), {state:'enabled',active:nodes});
assert.equal(knowledge.activity(profile([]), 'NotOwned'), false);
assert.equal(knowledge.activity({acquired:['Bonus Monkey Knowledge'],enabled:true}, 'BonusMonkey'), true);
assert.equal(knowledge.activity({acquired:['BonusMonkey'],disabled:['Bonus Monkey Knowledge'],enabled:true}, 'BonusMonkey'), false);
assert.equal(knowledge.activity(profile(['NotOwned']), 'MasterDoubleCross'), true);
for (const disabled of [null, {}, 'BonusMonkey', [42], [{}], ['']]) {
  assert.equal(knowledge.activity(profile(disabled), 'BonusMonkey'), null);
  assert.deepEqual(knowledge.summarize(profile(disabled)), {state:'unknown',active:null});
}
for (const enabled of [null, undefined, 'true', 1]) {
  assert.equal(knowledge.activity({...profile([]),enabled}, 'BonusMonkey'), null);
}
assert.deepEqual(knowledge.ids(['BonusMonkey',{id:'bonus_monkey'},{name:'MasterDoubleCross'}]), ['BonusMonkey','MasterDoubleCross']);
assert.equal(knowledge.activity({acquired:null, enabled:true}, 'BonusMonkey'), null);

// Execute the real save-to-profile path, replacing only discovery/decryption.
const saveFile = require.resolve('../lib/btd6-save-progress');
const saveSource = fs.readFileSync(saveFile,'utf8');
function decode(fixture) {
  const before=JSON.stringify(fixture);
  const result=vm.runInNewContext(saveSource + '\nfindProfileSave=()=>"synthetic"; decodeProfileSave=()=>fixture; readLocalProgress();', {
    require:createRequire(saveFile), module:{exports:{}}, fixture,
  });
  assert.equal(JSON.stringify(fixture),before,'Save input is never mutated');
  return JSON.parse(JSON.stringify(result));
}
const decoded = decode({acquiredKnowledge:nodes, paidForKnowledge:['MasterDoubleCross'], disabledKnowledge:['BonusMonkey'], knowledgeDisabled:false});
assert.equal(decoded.available,true);
assert.deepEqual(decoded.monkeyKnowledge.acquired,nodes);
assert.deepEqual(decoded.monkeyKnowledge.paidFor,['MasterDoubleCross']);
assert.deepEqual(decoded.monkeyKnowledge.disabled,['BonusMonkey']);
assert.deepEqual(decoded.monkeyKnowledge.active,nodes.slice(1));
assert.equal(decoded.monkeyKnowledge.bonusMonkey,true,'Unlocked display remains ownership, not activation');
assert.equal(decoded.monkeyKnowledge.state,'partial');
assert.equal(decode({acquiredKnowledge:nodes,disabledKnowledge:null,knowledgeDisabled:false}).monkeyKnowledge.state,'unknown');
assert.equal(decode({acquiredKnowledge:nodes,knowledgeDisabled:false}).monkeyKnowledge.state,'enabled','Legacy save without switches remains supported');
assert.deepEqual(decode({acquiredKnowledge:nodes,disabledKnowledge:[],knowledgeDisabled:true}).monkeyKnowledge.active,[]);
for (const acquiredKnowledge of [null, 'BonusMonkey', 12, {BonusMonkey:'yes'}, [{}]]) {
  const mk=decode({acquiredKnowledge,disabledKnowledge:[],knowledgeDisabled:false}).monkeyKnowledge;
  assert.equal(mk.state,'unknown','Malformed ownership must stay unknown through the real decoder');
  assert.equal(mk.acquired,null);
  assert.equal(mk.bonusMonkey,null);
}

const browser={};
vm.runInNewContext(fs.readFileSync('data/catalogs/monkey-knowledge.js','utf8'),browser);
for (const disabled of [[],['BonusMonkey'],null]) {
  for (const id of nodes) assert.equal(browser.BloonsKnowledge.activity(profile(disabled),id),knowledge.activity(profile(disabled),id));
}
const html=fs.readFileSync('index.html','utf8');
assert.ok(html.indexOf('data/catalogs/monkey-knowledge.js')>=0);
assert.ok(html.indexOf('data/catalogs/monkey-knowledge.js')<html.indexOf('assets/app/app.js'));

// Replay launch uses active points, not legacy ownership booleans or guessed
// global enablement. Test the actual production launch expressions.
const automation=fs.readFileSync('lib/automation.js','utf8');
const bonusCode=automation.slice(automation.indexOf('  const bonusMonkeyEnabled ='),automation.indexOf("  // map-mechanics.js's status"));
for (const [mk, dart, glue] of [
  [profile([]),true,true], [profile(['BonusMonkey']),false,true],
  [profile(['BonusGlueGunner']),true,false], [profile([],false),false,false],
  [profile(null),false,false], [{...profile([]),enabled:null},false,false],
]) {
  const result=vm.runInNewContext(bonusCode+';[bonusMonkeyEnabled,bonusGlueEnabled]',{profile:{available:true,monkeyKnowledge:mk},knowledgeState:knowledge});
  assert.deepEqual(Array.from(result),[dart,glue]);
}

// Both ownership details and selected-route marks use the same active state.
const app=fs.readFileSync('assets/app/app.js','utf8');
class Element {
  constructor(){this.children=[];this.textContent='';}
  append(...children){this.children.push(...children);}
  replaceChildren(...children){this.children=children;}
}
const textOf=element=>[element.textContent,...element.children.map(textOf)].join(' ');
function render(mk) {
  const elements=Object.fromEntries(['#profile-unlock-status','#profile-monkey-knowledge','#specific-tower-requirements'].map(id=>[id,new Element()]));
  elements['#playthrough-map-select']={value:'synthetic'};
  elements['#playthrough-variation-select']={value:'hard'};
  const context={BloonsKnowledge:knowledge,detectedProgress:{localProfile:{available:true,monkeyKnowledge:mk},towers:{}},
    comboData:{synthetic:{hard:[{requirements:{knowledge:['MasterDoubleCross'],towers:{}}}]}},
    document:{querySelector:id=>elements[id],createElement:()=>new Element()},
    unlockedUpgradeSet:()=>new Set(),mapProgressKey:value=>String(value).toLowerCase(),
  };
  vm.runInNewContext(app.slice(app.indexOf('function renderProfileUnlocks()'),app.indexOf('async function loadPlaythroughs()'))+';renderProfileUnlocks();renderTowerRequirements();',context);
  return elements;
}
const partial=render({...profile(['MasterDoubleCross']),paidFor:nodes});
assert.match(textOf(partial['#profile-monkey-knowledge']),/partly enabled/);
assert.match(textOf(partial['#profile-monkey-knowledge']),/Master Double Cross — inactive/);
assert.match(textOf(partial['#specific-tower-requirements']),/individually disabled/);
assert.match(textOf(partial['#specific-tower-requirements']),/× Required knowledge/);
assert.match(textOf(render(profile(null))['#specific-tower-requirements']),/\? Required knowledge/);
assert.match(textOf(render(profile([]))['#specific-tower-requirements']),/✓ Required knowledge/);
console.log('Synthetic knowledge ownership, per-point activation, save decoding, replay flags and UI agree.');
