const { app, BrowserWindow, session } = require('electron');
const fs = require('node:fs'), http = require('node:http'), path = require('node:path');
const root = path.resolve(__dirname, '../../docs');
const profile = process.env.BLOONS_RENDERER_TEST_PROFILE;
if (!profile) throw new Error('Use test-site-spacing-renderer.js for profile isolation and cleanup');
app.setPath('userData', profile); app.setPath('sessionData', profile); app.setPath('logs', profile);
app.disableHardwareAcceleration(); app.on('window-all-closed', () => {});
const failures = [], errors = [];
let win, pages = 0, context;
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const check = (condition, issue, details) => { if (!condition) failures.push({ ...context, issue, details }); };
const server = http.createServer((req, res) => {
  if (req.method !== 'GET') { errors.push('Unexpected mutation'); res.writeHead(405); res.end(); return; }
  const pathname = new URL(req.url, 'http://localhost').pathname;
  if (pathname === '/fixture-prefs') { res.end('<!doctype html><title>Isolated fixture</title>'); return; }
  let file = path.resolve(root, decodeURIComponent(pathname.slice(1)));
  if (file === root || fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  const mime = { '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.webp': 'image/webp', '.woff2': 'font/woff2', '.ico': 'image/x-icon' };
  if (!file.startsWith(root + path.sep) || !mime[path.extname(file)] || !fs.existsSync(file)) { res.writeHead(404); res.end(); return; }
  res.setHeader('Content-Type', mime[path.extname(file)]); fs.createReadStream(file).pipe(res);
});
const inspect = code => win.webContents.executeJavaScript(code);
(async () => {
  await app.whenReady(); await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = 'http://127.0.0.1:' + server.address().port;
  session.defaultSession.webRequest.onBeforeRequest((details, callback) => callback({cancel: !details.url.startsWith(origin + '/') && !details.url.startsWith('data:')}));
  win = new BrowserWindow({show:false,width:1280,height:900,webPreferences:{offscreen:true,backgroundThrottling:false,contextIsolation:true,sandbox:true}});
  await win.loadURL(origin+'/fixture-prefs');win.webContents.debugger.attach('1.3');
  await win.webContents.debugger.sendCommand('Emulation.setFocusEmulationEnabled',{enabled:true});
  await win.webContents.debugger.sendCommand('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  for(const width of [1280,390]) for(const theme of ['light','dark']) for(const spacing of [false,true]) {
    await win.webContents.debugger.sendCommand('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:false});
    await inspect(`localStorage.setItem('bloons-guide-theme',${JSON.stringify(theme)})`);
    for(const page of ['contributors/','subscriptions/']) {
      context={width,theme,spacing,page};await win.loadURL(origin+'/'+page);
      await win.webContents.debugger.sendCommand('Emulation.setFocusEmulationEnabled',{enabled:true});
      if(spacing)await inspect(`(()=>{const s=document.createElement('style');s.textContent='*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}';document.head.append(s)})()`);
      await pause(120);pages++;
      const state=await inspect(`(()=>{const hero=document.querySelector('.people-intro,.subscription-intro'),img=hero.querySelector('img'),h=hero.querySelector('h1'),box=img.getBoundingClientRect(),heading=h.getBoundingClientRect(),r=document.createRange();r.selectNodeContents(h);const cs=getComputedStyle(h);return {width:innerWidth,theme:document.documentElement.dataset.theme,scroll:document.documentElement.scrollWidth,image:{loaded:img.complete&&img.naturalWidth>0,right:box.right,bottom:box.bottom,width:box.width,height:box.height,natural:img.naturalWidth/img.naturalHeight},heading:{left:heading.left,right:heading.right,bottom:heading.bottom},text:[...r.getClientRects()].map(r=>({left:r.left,right:r.right,bottom:r.bottom})),font:parseFloat(cs.fontSize),letter:parseFloat(cs.letterSpacing),word:parseFloat(cs.wordSpacing),line:parseFloat(cs.lineHeight)}})()`);
      check(state.width===width&&state.theme===theme,'Fixture mismatch',state);
      check(state.scroll<=width+1,'Document overflows',state);
      check(state.image.loaded&&state.image.right<=width+1,'Hero art outside viewport',state.image);
      check(Math.abs(state.image.width/state.image.height/state.image.natural-1)<.02,'Hero art stretched',state.image);
      check(state.text.every(r=>r.left>=state.heading.left-1&&r.right<=state.heading.right+1),'Heading text outside its column',state);
      if(spacing)check(Math.abs(state.letter/state.font-.12)<.01&&Math.abs(state.word/state.font-.16)<.01&&Math.abs(state.line/state.font-1.5)<.01,'Text overrides missing',state);
    }
  }
  console.log(JSON.stringify({pages,failures,errors}));win.destroy();server.closeAllConnections();server.close(()=>app.exit(failures.length||errors.length?1:0));
})().catch(error=>{console.error(context,error.stack);if(win&&!win.isDestroyed())win.destroy();server.closeAllConnections();app.exit(1)});
