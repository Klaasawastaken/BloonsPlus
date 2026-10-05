const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const { Readable, Transform } = require('node:stream');
const { pipeline } = require('node:stream/promises');
const source = fs.readFileSync(require.resolve('../lib/vm-setup'), 'utf8');
const start = source.indexOf('async function download(');
const fn = source.slice(start, source.indexOf('// ---------- step actions', start));
async function main() {
  const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'bloons-download-test-'));
  try {
    const target = path.join(folder, 'installer.bin');
    async function run(range, body, length = body.length, status = 206) {
      fs.writeFileSync(target + '.part', Buffer.alloc(10));
      if (fs.existsSync(target)) fs.unlinkSync(target);
      const response = new Response(body, {status, headers:{'content-range':range, 'content-length':String(length)}});
      const context = {fs, path, AbortSignal, Readable, Transform, pipeline, Date, Number, String,
        fileExists: fs.existsSync, fetch: async () => response, job:{}, note:()=>{}, gb:String,
        target};
      return vm.runInNewContext(fn + '\ndownload("https://example.invalid/file", target, "Test")', context);
    }
    await assert.rejects(run('bytes 10-14/20', '12345'), /ended early/);
    assert.equal(fs.existsSync(target), false, 'A partial range must not become a completed installer');
    assert.equal(fs.statSync(target + '.part').size, 15, 'Keep valid partial bytes for a future resume');
    await assert.rejects(run('bytes 9-13/20', '12345'), /resume/);
    assert.equal(fs.statSync(target + '.part').size, 10, 'Wrong range must not append');
    await assert.rejects(run('bytes 10-14/20', '12345', 8), /range|length/);
    await assert.rejects(run('bytes 10-14/*', '12345'), /range|size/);
    await assert.rejects(run('bytes 10-14/20', '1234567890', 5), /match the resume range/);
    assert.equal(fs.statSync(target + '.part').size, 10, 'Discard bytes outside the declared range');
    await run('bytes 10-19/20', '1234567890');
    assert.equal(fs.statSync(target).size, 20);
    assert.equal(fs.existsSync(target + '.part'), false);
    await run('', 'fresh-file', 10, 200);
    assert.equal(fs.readFileSync(target, 'utf8'), 'fresh-file', 'A server ignoring Range replaces the stale partial');
    console.log('Setup resumed-download checks passed without network requests.');
  } finally {
    assert.equal(path.dirname(folder), os.tmpdir());
    assert.ok(path.basename(folder).startsWith('bloons-download-test-'));
    fs.rmSync(folder, {recursive:true, force:true});
  }
}
main().catch(error=>{ console.error(error); process.exitCode=1; });
