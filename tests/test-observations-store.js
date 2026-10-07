const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const syncFs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { createObservationWriter } = require('../lib/observations-store');

(async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'bloons-observations-'));
  const file = path.join(root, 'game-observations.json');
  const prior = { maps: {}, achievements: { retained: true } };
  const addMedal = value => { (value.maps.example ||= {}).easy = true; };
  try {
    await fs.writeFile(file, JSON.stringify(prior));
    const scheduleScanner = raw => {
      queueMicrotask(() => {
        const latest = JSON.parse(syncFs.readFileSync(file, 'utf8'));
        latest.newScannerField = true;
        syncFs.writeFileSync(file, JSON.stringify(latest));
      });
      return raw;
    };
    const interleaved = createObservationWriter({io: {...syncFs, ...fs,
      readFile: async (...args) => scheduleScanner(await fs.readFile(...args)),
      readFileSync: (...args) => scheduleScanner(syncFs.readFileSync(...args))}});
    await interleaved(file, addMedal);
    const interleavedSaved = JSON.parse(await fs.readFile(file, 'utf8'));
    assert.equal(interleavedSaved.newScannerField, true, 'Same-process scanner update must not be overwritten');
    assert.equal(interleavedSaved.maps.example.easy, true);
    for (const code of ['EPERM', 'EACCES', 'EBUSY']) {
      await fs.writeFile(file, JSON.stringify(prior));
      let attempts = 0; const waits = [];
      const update = createObservationWriter({ io: { ...syncFs, renameSync: (a, b) => {
        if (++attempts === 1) {
          syncFs.writeFileSync(file, JSON.stringify({ ...prior, newScannerField: true }));
          throw Object.assign(new Error('simulated transient conflict'), { code });
        }
        return syncFs.renameSync(a, b);
      } }, delay: async ms => waits.push(ms) });
      await update(file, addMedal);
      const saved = JSON.parse(await fs.readFile(file, 'utf8'));
      assert.equal(saved.maps.example.easy, true);
      assert.equal(saved.achievements.retained, true);
      assert.equal(saved.newScannerField, true, 'Retry must merge into the fresh document');
      assert.equal(attempts, 2); assert.deepEqual(waits, [50]);
    }
    for (const code of ['EPERM', 'ENOSPC', 'EIO']) {
      await fs.writeFile(file, JSON.stringify(prior));
      let attempts = 0; const waits = [];
      const update = createObservationWriter({ io: { ...syncFs, renameSync: () => {
        attempts++; throw Object.assign(new Error('persistent conflict'), { code });
      } }, delay: async ms => waits.push(ms) });
      await assert.rejects(update(file, addMedal), error => error.code === code);
      assert.deepEqual(JSON.parse(await fs.readFile(file, 'utf8')), prior);
      assert.equal(attempts, code === 'EPERM' ? 4 : 1);
      assert.deepEqual(waits, code === 'EPERM' ? [50, 100, 200] : []);
      assert.deepEqual(await fs.readdir(root), ['game-observations.json']);
    }
    const update = createObservationWriter();
    for (const invalid of ['{', 'null', '[]', '{"maps":[]}']) {
      await fs.writeFile(file, invalid);
      await assert.rejects(update(file, addMedal));
      assert.equal(await fs.readFile(file, 'utf8'), invalid, 'Unreadable data must not be replaced with defaults');
    }
    await fs.unlink(file);
    await update(file, addMedal);
    assert.equal(JSON.parse(await fs.readFile(file, 'utf8')).maps.example.easy, true);
    await Promise.all(Array.from({ length: 12 }, (_, i) => update(file, value => { value['field' + i] = i; })));
    const saved = JSON.parse(await fs.readFile(file, 'utf8'));
    for (let i = 0; i < 12; i++) assert.equal(saved['field' + i], i, 'Queued update lost');
    assert.deepEqual(await fs.readdir(root), ['game-observations.json']);
    console.log('Observation persistence: transient/persistent errors, fresh merge, prior preservation, malformed input, initialization and queued updates pass.');
  } finally {
    assert.equal(path.dirname(root), os.tmpdir());
    assert.ok(path.basename(root).startsWith('bloons-observations-'));
    await fs.rm(root, { recursive: true, force: true });
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
