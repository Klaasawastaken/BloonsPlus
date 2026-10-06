const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('lib/automation.js', 'utf8').replace(/\r\n/g, '\n');
const start = source.indexOf('function routeAttemptHash(');
const fn = source.slice(start, source.indexOf('\nfunction loadVerifiedRoutes', start));
const SWEEP_ENGINE_VERSION = 'test-engine';
const content = 'original recording unchanged';
const previous = createHash('sha256').update(SWEEP_ENGINE_VERSION).update('\0').update(content).digest('hex');
function hash(map) {
  return vm.runInNewContext(fn + '\nrouteAttemptHash(filename)', {
    filename:map+'#chimps#1920x1080.btd6', SWEEP_ENGINE_VERSION, createHash,
    parsePlaythroughFile:()=>({mapSlug:map}), PLAYTHROUGHS_DIR:'unused',
    path:{join:()=>''}, fs:{readFileSync:()=>content},
  });
}
assert.notEqual(hash('polyphemus'), previous, 'Evidenced engine fix allows a new missing-medal attempt');
assert.notEqual(hash('one_two_tree'), previous, 'Recorded stationary Heli drift also affected One Two Tree');
assert.equal(hash('logs'), previous, 'Unrelated prior failures must remain excluded');
assert.equal(hash('geared'), previous);
assert.equal(hash('polyphemus'), hash('polyphemus'), 'Revision must be stable across sweep restarts');
console.log('Targeted attempt revision preserves unrelated failure exclusions.');

function infernal(mode, body = 'place heli heli0 at 137, 800') {
  return vm.runInNewContext(fn + '\nrouteAttemptHash(filename)', {
    filename:'infernal#'+mode+'#2560x1440#converted.btd6', SWEEP_ENGINE_VERSION, createHash,
    parsePlaythroughFile:()=>({mapSlug:'infernal',gamemodeSlug:mode}), PLAYTHROUGHS_DIR:'unused',
    path:{join:()=>''}, fs:{readFileSync:()=>Buffer.from(body)},
  });
}
const body = 'place heli heli0 at 137, 800';
const oldHintsHash = createHash('sha256').update(SWEEP_ENGINE_VERSION+':infernal-heli-hints-v1').update('\0').update(body).digest('hex');
assert.notEqual(infernal('reverse'), oldHintsHash);
assert.notEqual(infernal('alternate_bloons_rounds'), oldHintsHash);
assert.equal(infernal('reverse'), infernal('reverse'), 'Do not keep resetting the failure exclusion');
assert.equal(infernal('hard'), oldHintsHash, 'Other Infernal modes keep their existing attempt revision');
assert.equal(infernal('chimps'), createHash('sha256').update(SWEEP_ENGINE_VERSION).update('\0').update(body).digest('hex'));
console.log('Live-confirm revision is limited to the two evidenced Infernal modes.');
