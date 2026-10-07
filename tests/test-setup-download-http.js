// Exercise the production download function against real loopback HTTP streams.
// No installer is executed and no external service or existing app file is used.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const { Readable, Transform } = require('node:stream');
const { pipeline } = require('node:stream/promises');

const source = fs.readFileSync(require.resolve('../lib/vm-setup'), 'utf8');
const start = source.indexOf('async function download(');
const end = source.indexOf('// ---------- step actions', start);
assert.ok(start >= 0 && end > start, 'Production download boundaries must exist');
const downloadSource = source.slice(start, end);

async function main() {
  const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'bloons-download-http-'));
  const target = path.join(folder, 'fixture.bin');
  const partial = target + '.part';
  const previous = Buffer.from('previous verified fixture');
  const body = Buffer.from(Array.from({ length: 256 * 1024 }, (_, i) => i % 251));
  let handler;
  const requests = [];
  const server = http.createServer((request, response) => {
    requests.push(request.headers.range || null);
    handler(request, response);
  });
  const sockets = new Set();
  server.on('connection', socket => {
    sockets.add(socket);
    socket.on('close', () => sockets.delete(socket));
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let timedOut = false;
  const watchdog = setTimeout(() => {
    timedOut = true;
    for (const socket of sockets) socket.destroy();
    server.close();
  }, 15000);
  const url = `http://127.0.0.1:${server.address().port}/fixture`;
  const job = {};
  const context = { fs, path, AbortSignal, Readable, Transform, pipeline, Date, Number, String,
    fileExists: fs.existsSync, fetch, job, note: () => {}, gb: String, url, target };
  const run = () => vm.runInNewContext(downloadSource + '\ndownload(url, target, "Fixture")', context);
  const reset = bytes => {
    requests.length = 0;
    fs.writeFileSync(target, previous);
    if (bytes) fs.writeFileSync(partial, bytes);
    else if (fs.existsSync(partial)) fs.unlinkSync(partial);
  };
  const unchanged = bytes => {
    assert.ok(fs.readFileSync(target).equals(previous), 'Failed transfer replaced the completed file');
    assert.ok(fs.readFileSync(partial).equals(bytes), 'Failed response changed reusable partial bytes');
  };
  const complete = () => {
    assert.ok(fs.readFileSync(target).equals(body), 'Completed transfer differs from the served bytes');
    assert.equal(fs.existsSync(partial), false, 'Completed transfer left a partial file');
    assert.equal(job.progress, null);
    assert.equal(job.numerator, null);
    assert.equal(job.denominator, null);
    assert.equal(job.scope, null);
  };
  try {
    // The server closes a real socket after delivering only part of its declared body.
    reset();
    handler = (_request, response) => {
      response.writeHead(200, { 'content-length': body.length });
      response.write(body.subarray(0, 64 * 1024));
      setTimeout(() => response.destroy(), 100);
    };
    await assert.rejects(run(), /partial download is saved/);
    const retained = fs.readFileSync(partial);
    assert.ok(retained.length > 0 && retained.length < body.length, 'Fixture must actually retain partial bytes');
    assert.ok(retained.equals(body.subarray(0, retained.length)), 'Retained bytes differ from the served prefix');
    unchanged(retained);
    handler = (request, response) => {
      const offset = Number(request.headers.range.match(/^bytes=(\d+)-$/)[1]);
      response.writeHead(206, { 'content-range': `bytes ${offset}-${body.length - 1}/${body.length}`,
        'content-length': body.length - offset });
      response.end(body.subarray(offset));
    };
    await run();
    assert.deepEqual(requests, [null, `bytes=${retained.length}-`]);
    complete();

    const prefix = body.subarray(0, 1024);
    reset(prefix);
    handler = (_request, response) => {
      response.writeHead(206, { 'content-range': `bytes 1023-${body.length - 1}/${body.length}`,
        'content-length': body.length - 1023 });
      response.end(body.subarray(1023));
    };
    await assert.rejects(run(), /invalid resume range/);
    unchanged(prefix);

    reset(prefix);
    handler = (_request, response) => { response.writeHead(404); response.end('Not found'); };
    await assert.rejects(run(), /HTTP 404/);
    unchanged(prefix);

    for (const freshStatus of [503, 200]) {
      reset(prefix);
      handler = (request, response) => {
        if (request.headers.range) {
          response.writeHead(416, { 'content-range': `bytes */${prefix.length}` });
          response.end();
        } else {
          response.writeHead(freshStatus, { 'content-length': body.length });
          response.end(body);
        }
      };
      if (freshStatus === 503) { await assert.rejects(run(), /HTTP 503/); unchanged(prefix); }
      else { await run(); complete(); }
      assert.deepEqual(requests, ['bytes=1024-', null], 'Rejected range must request a fresh complete body');
    }

    reset(prefix);
    handler = (_request, response) => {
      response.writeHead(200, { 'content-length': body.length });
      response.end(body);
    };
    await run();
    complete();
    assert.deepEqual(requests, ['bytes=1024-'], 'Ignored Range must replace the partial, not append');

    reset();
    handler = (_request, response) => {
      response.writeHead(200); // A real chunked response has no known total.
      response.write(body.subarray(0, 1024));
      response.end(body.subarray(1024));
    };
    await run();
    complete();
    assert.equal(timedOut, false, 'Loopback download fixture exceeded fifteen seconds');
    console.log('Real HTTP setup download: interrupted/resumed, wrong range, 404, 416/503, 416/fresh, ignored Range and chunked transfers passed.');
  } finally {
    clearTimeout(watchdog);
    for (const socket of sockets) socket.destroy();
    await new Promise(resolve => server.close(resolve));
    assert.equal(path.dirname(folder), os.tmpdir());
    assert.ok(path.basename(folder).startsWith('bloons-download-http-'));
    fs.rmSync(folder, { recursive: true, force: true });
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
