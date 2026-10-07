const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
(async () => {
  const masks = [], values = ['unreadable', 'Admiral Brickell', 'PSI', 'Ezili', 'selected', '', ''];
  let output = '', error = '';
  let finish;
  const done = new Promise(resolve => { finish = resolve; });
  const context = {
    Buffer,
    require(name) {
      if (name === '../lib/ocr') return {
        async readTitle(bytes, box, options = {}) { if (options.classify) masks.push(options.classify); return values.shift(); },
        async readNaturalText() { return ''; },
        shutdown: finish,
      };
      if (name === 'pngjs') return { PNG: { sync: { read: () => ({ width: 2, height: 2, data: Buffer.alloc(16) }) } } };
      throw new Error('Unexpected dependency '+name);
    },
    process: {
      stdin: { async *[Symbol.asyncIterator]() { yield Buffer.from('fixture'); } },
      stdout: { write(value) { output += value; } },
      stderr: { write(value) { error += value; } },
    },
  };
  vm.runInNewContext(fs.readFileSync('tools/read-hero-selection.js', 'utf8'), context);
  await done;
  assert.equal(error, '');
  assert.deepEqual(JSON.parse(output).titleCandidates, ['unreadable','admiralbrickell','psi','ezili']);
  assert.equal(JSON.parse(output).button, 'selected');
  assert.deepEqual(JSON.parse(output).buttonCandidates, ['selected'], 'Retain the OCR inputs used for button classification');
  assert.equal(masks.length, 6);
  assert.equal(masks[0](30,210,238), true, 'retain cyan titles');
  assert.equal(masks[1](255,200,30), true, 'read yellow titles');
  assert.equal(masks[1](245,110,35), true, 'read orange titles');
  assert.equal(masks[1](255,20,5), false, 'exclude red ribbon');
  assert.equal(masks[1](250,250,250), false, 'exclude white border');
  assert.equal(masks[2](185,105,240), true, 'read violet titles');
  assert.equal(masks[2](30,210,238), false, 'separate cyan from violet');
  assert.equal(masks[2](250,250,250), false, 'exclude white border');
  assert.equal(masks[3](220,45,195), true, 'read saturated magenta hero titles');
  assert.equal(masks[3](220,45,35), false, 'exclude red ribbon');
  assert.equal(masks[3](250,250,250), false, 'exclude white border');
  assert.equal(masks[4](135,235,40), true, 'isolate bright Selected glyphs');
  assert.equal(masks[4](60,140,70), false, 'exclude green hero scenery');
  console.log('Hero title color masks retain OCR candidates without inferring a hero.');
})().catch(error => { console.error(error); process.exitCode = 1; });
