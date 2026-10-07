const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

async function observe({ bright = 0.109, label = '', white = '', outline = '', natural = '', width = 1920 } = {}) {
  const height = width * 9 / 16;
  const data = Buffer.alloc(width * height * 4);
  const box = { x: Math.round(1300 * width / 2560), y: Math.round(760 * height / 1440),
    w: Math.round(430 * width / 2560), h: Math.round(110 * height / 1440) };
  // Green scenery behind a Selected label polluted the former density fallback.
  let n = 0;
  for (let y = box.y; y < box.y + box.h; y++) for (let x = box.x; x < box.x + box.w; x++) {
    const rgb = n++ < box.w * box.h * bright ? [135, 235, 40] : [60, 140, 70];
    data.set([...rgb, 255], (y * width + x) * 4);
  }
  let result = '', done;
  const finished = new Promise(resolve => { done = resolve; });
  vm.runInNewContext(fs.readFileSync('tools/read-hero-selection.js', 'utf8'), {
    Buffer,
    require(name) {
      if (name === '../lib/ocr') return {
        async readTitle(bytes, crop, options = {}) {
          if (crop.y < height / 4) return 'Obyn Greenfoot';
          return options.classify ? options.classify(255, 255, 255) ? white : label : outline;
        },
        async readNaturalText(bytes, crop) { return crop.y < height / 4 ? '' : natural; },
        shutdown: done,
      };
      if (name === 'pngjs') return { PNG: { sync: { read: () => ({ width, height, data }) } } };
      throw Error(name);
    },
    process: { stdin: { async *[Symbol.asyncIterator]() { yield Buffer.from('synthetic'); } },
      stdout: { write(value) { result += value; } }, stderr: { write(value) { throw Error(value); } } },
  });
  await finished;
  return JSON.parse(result);
}

(async () => {
  for (const width of [960, 1920, 2560]) {
    for (const label of ['SELECTED', 'seLecYeo', 'seLecvep']) {
      assert.equal((await observe({ width, label, outline: 'SELECT' })).button, 'selected',
        'Read the isolated Selected glyphs despite green scenery and truncated outline OCR');
    }
    assert.equal((await observe({ width, bright: 0.322, label: 'a r pr', natural: '( select) )' })).button, 'select');
    assert.equal((await observe({ width, bright: 0.304, white: 'SELECT', natural: 'selecr' })).button, 'select', 'Read white letters without the button border');
    assert.equal((await observe({ width, label: '' })).button, 'unknown', 'Scenery alone proves neither state');
    assert.equal((await observe({ width, label: 'selection' })).button, 'unknown', 'No broad fuzzy match');
    assert.equal((await observe({ width, label: 'selected', natural: 'UNLOCK' })).button, 'unknown', 'Conflicting unlock text is not selection');
    assert.equal((await observe({ width, bright: 0.322, label: 'seLecYeo' })).button, 'unknown', 'Dense green fill cannot corroborate fuzzy Selected');
  }
  console.log('Hero button states require text evidence; green backgrounds never prove selection.');
})().catch(error => { console.error(error); process.exitCode = 1; });
