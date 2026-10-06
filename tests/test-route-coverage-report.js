// Exercise the complete offline report, including its extracted runtime helpers.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const root = path.resolve(__dirname, '..');
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'bloons-coverage-'));
const output = path.join(temporary, 'coverage.json');
try {
  execFileSync(process.execPath, ['tools/route-coverage-report.js', '--out', output, '--quiet'],
    {cwd:root, windowsHide:true, encoding:'utf8'});
  const report = JSON.parse(fs.readFileSync(output, 'utf8'));
  assert.equal(report.modes.length, 14);
  const maps = Object.values(report.maps);
  let covered = 0;
  for (const map of maps) {
    assert.deepEqual(Object.keys(map.modes), report.modes);
    for (const candidates of Object.values(map.modes)) {
      if (!Array.isArray(candidates)) continue;
      assert.ok(candidates.length > 0);
      for (const candidate of candidates) {
        const name = candidate.replace(/ \(CHIMPS reuse\)$/, '');
        assert.ok(fs.existsSync(path.join(root, 'autobtd6/playthroughs', name)), name);
      }
      covered++;
    }
  }
  assert.equal(report.summary.maps, maps.length);
  assert.equal(report.summary.mapModePairs, maps.length * report.modes.length);
  assert.equal(report.summary.covered, covered);
  assert.equal(report.summary.missing, report.summary.mapModePairs - covered);
  console.log('Offline coverage executes current runtime helpers; totals and candidate files agree.');
} finally {
  if (fs.existsSync(output)) fs.unlinkSync(output);
  fs.rmdirSync(temporary);
}
