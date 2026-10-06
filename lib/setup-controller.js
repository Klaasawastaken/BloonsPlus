const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { createSetupSession } = require('./setup-session');

function controllerOwner(root) {
  return crypto.createHash('sha256').update(path.resolve(root).replace(/[\\/]+$/, '').toLowerCase(), 'utf8').digest('hex');
}
function secretMatches(candidate, expected) {
  return typeof candidate === 'string' && /^[a-f0-9]{64}$/.test(candidate)
    && crypto.timingSafeEqual(Buffer.from(candidate, 'hex'), Buffer.from(expected, 'hex'));
}
function boundedJson(file) {
  const stat = fs.statSync(file);
  if (!stat.isFile() || stat.size > 65536) throw new Error('Invalid setup handoff');
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}
function writeCheckpoint(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const temporary = `${file}.${crypto.randomUUID()}.tmp`;
  let descriptor;
  try {
    descriptor = fs.openSync(temporary, 'wx', 0o600);
    fs.writeFileSync(descriptor, JSON.stringify(value)); fs.fsyncSync(descriptor);
    fs.closeSync(descriptor); descriptor = undefined;
    fs.renameSync(temporary, file);
  } finally {
    if (descriptor !== undefined) fs.closeSync(descriptor);
    try { fs.unlinkSync(temporary); } catch { /* Already atomically published. */ }
  }
}
function readBody(req) {
  return new Promise((resolve, reject) => {
    let body = '', length = 0;
    req.on('data', chunk => {
      length += chunk.length;
      if (length > 16384) { reject(new Error('Setup request too large')); req.destroy(); }
      else body += chunk;
    });
    req.on('end', () => { try { resolve(JSON.parse(body || '{}')); } catch { reject(new Error('Invalid JSON')); } });
    req.on('error', reject);
  });
}

function createSetupController({ root, dataRoot, port, dependencies, setupOnly = false }) {
  const owner = controllerOwner(root);
  const checkpointPath = path.join(dataRoot, 'setup-sessions', owner, 'session.json');
  const handoffDir = path.join(dataRoot, 'setup-handoff');
  let session = null, key = null, activeId = null;
  function send(res, code, body) {
    res.writeHead(code, { 'Content-Type':'application/json', 'Cache-Control':'no-store', 'X-Content-Type-Options':'nosniff' });
    res.end(JSON.stringify(body));
  }
  function validCaller(req) {
    const host = req.headers.host;
    const allowed = [`127.0.0.1:${port}`, `localhost:${port}`];
    return ['127.0.0.1','::1','::ffff:127.0.0.1'].includes(req.socket.remoteAddress)
      && allowed.includes(host) && (!req.headers.origin || req.headers.origin === `http://${host}`);
  }
  function authenticated(req) {
    const cookie = String(req.headers.cookie || '').split(';').map(value=>value.trim()).find(value=>value.startsWith('BloonsSetupKey='));
    return key && secretMatches(req.headers['x-bloons-setup-key'] || cookie?.slice('BloonsSetupKey='.length), key);
  }
  function previous() { try { return boundedJson(checkpointPath); } catch { return null; } }
  function attach(config) {
    let checkpoint;
    const receipt = previous(); checkpoint = receipt?.snapshot || receipt;
    session = createSetupSession({...config, checkpoint}, {...dependencies,persist:value=>writeCheckpoint(checkpointPath,{snapshot:value,options:session.options()})});
    key = config.key; activeId = config.sessionId;
  }
  async function handle(req, res, route) {
    if (!validCaller(req)) return send(res,403,{error:'Setup request origin is not allowed'});
    try {
      if (route === '/api/setup/controller' && req.method === 'GET')
        return send(res,200,{protocolVersion:1, owner, pid:process.pid, version:require('../package.json').version, setupOnly});
      if (route === '/api/setup/session/bootstrap' && req.method === 'POST') {
        // Only the app's same-origin renderer may establish its HttpOnly cookie.
        // Native clients use a contained handoff and a header instead.
        if (req.headers.origin !== `http://${req.headers.host}`) return send(res,403,{error:'Open setup from the app'});
        const body = await readBody(req);
        if (!session || (body.operation === 'update' && session.snapshot().phase === 'complete')) {
          const receipt=previous(), saved=receipt?.snapshot || receipt;
          const recoverable=saved?.owner===owner && saved.phase!=='complete';
          attach({sessionId:recoverable ? saved.sessionId : crypto.randomBytes(16).toString('hex'),key:crypto.randomBytes(32).toString('hex'),owner,
            operation:recoverable ? saved.operation : body.operation === 'update' ? 'update' : 'resume',options:recoverable && receipt?.options ? receipt.options : body.options || {}});
        }
        if(body.options && !session.snapshot().operationOutstanding && !session.snapshot().queued && session.snapshot().phase!=='complete')session.configure(body.options);
        res.setHeader('Set-Cookie',`BloonsSetupKey=${key}; HttpOnly; SameSite=Strict; Path=/api/setup/session`);
        return send(res,200,session.snapshot());
      }
      if (route === '/api/setup/session/connect' && req.method === 'POST') {
        const body = await readBody(req);
        if (!/^[a-f0-9]{32}$/.test(body.handoffId)) return send(res,400,{error:'Invalid setup identifier'});
        let handoff;
        try { handoff = boundedJson(path.join(handoffDir, `${body.handoffId}.json`)); }
        catch { return send(res,400,{error:'Setup handoff is unavailable'}); }
        if (handoff.protocolVersion !== 1 || handoff.owner !== owner || handoff.sessionId !== body.handoffId)
          return send(res,409,{error:'Setup controller protocol or owner does not match'});
        if (!/^[a-f0-9]{64}$/.test(handoff.key) || !secretMatches(req.headers['x-bloons-setup-key'],handoff.key))
          return send(res,403,{error:'Setup session authentication failed'});
        if (!Number.isSafeInteger(handoff.createdAt) || handoff.createdAt > Date.now()+60000 || Date.now()-handoff.createdAt > 15*60000)
          return send(res,409,{error:'Setup handoff expired; reopen setup'});
        if (session && activeId !== handoff.sessionId && (session.snapshot().operationOutstanding || !['complete','failed','cancelled'].includes(session.snapshot().phase)))
          return send(res,409,{error:'Another setup session is active'});
        if (!session || activeId !== handoff.sessionId) {
          attach(handoff);
        }
        key = handoff.key;
        return send(res,200,session.snapshot());
      }
      if (!session || !authenticated(req)) return send(res,403,{error:'Setup session authentication required'});
      if (route === '/api/setup/session/release' && req.method === 'POST') {
        if (session.snapshot().phase !== 'complete') return send(res,409,{error:'Environment must be validated before releasing setup'});
        send(res,200,{released:setupOnly});
        if (setupOnly && dependencies.release) setImmediate(dependencies.release);
        return;
      }
      if (route === '/api/setup/session' && req.method === 'GET') {
        try { return send(res,200,await session.observe()); }
        catch (error) { if (/already active/.test(error.message)) return send(res,200,session.snapshot()); throw error; }
      }
      if (route === '/api/setup/session/command' && req.method === 'POST')
        return send(res,200,await session.command(await readBody(req)));
      return send(res,404,{error:'Unknown setup session endpoint'});
    } catch (error) {
      const conflict = /stale|already|active|Unsupported/i.test(error.message);
      send(res,conflict ? 409 : 400,{error:error.message});
    }
  }
  return {handle, checkpointPath, setPort:value=>{port=value;}};
}

module.exports = { createSetupController, controllerOwner };
