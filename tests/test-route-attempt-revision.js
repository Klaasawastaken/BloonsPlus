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
assert.equal(hash('logs'), previous, 'Unrelated prior failures must remain excluded');
assert.equal(hash('geared'), previous);
assert.equal(hash('polyphemus'), hash('polyphemus'), 'Revision must be stable across sweep restarts');
console.log('Targeted attempt revision preserves unrelated failure exclusions.');
