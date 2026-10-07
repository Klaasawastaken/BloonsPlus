const { app, BrowserWindow, session } = require('electron');
const fs = require('node:fs'), http = require('node:http'), path = require('node:path');
const root = path.resolve(__dirname, '../../docs');
const profile = process.env.BLOONS_RENDERER_TEST_PROFILE;
if (!profile) throw new Error('Use test-site-accessibility-renderer.js for profile isolation and cleanup');
app.setPath('userData', profile); app.setPath('sessionData', profile); app.setPath('logs', profile);
app.disableHardwareAcceleration(); app.on('window-all-closed', () => {});
const failures = [], errors = [];
let win, pages = 0, contrasts = 0, interactions = 0, context;
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
async function press(keyCode, modifiers = []) {
  win.webContents.sendInputEvent({ type: 'keyDown', keyCode, modifiers });
  if(keyCode==='Enter')win.webContents.sendInputEvent({type:'char',keyCode:'\r',modifiers});
  win.webContents.sendInputEvent({ type: 'keyUp', keyCode, modifiers });
  await pause(70);
}
(async () => {
  await app.whenReady(); await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = 'http://127.0.0.1:' + server.address().port;
  session.defaultSession.webRequest.onBeforeRequest((details, callback) => callback({ cancel: !details.url.startsWith(origin + '/') && !details.url.startsWith('data:') }));
  win = new BrowserWindow({ show: false, width: 1280, height: 900, webPreferences: { offscreen: true, backgroundThrottling: false, contextIsolation: true, sandbox: true } });
  win.webContents.on('console-message', (_event, _level, message) => { if (message.includes('Uncaught')) errors.push(message); });
  await win.loadURL(origin + '/fixture-prefs');
  win.webContents.debugger.attach('1.3');
  await win.webContents.debugger.sendCommand('Emulation.setFocusEmulationEnabled', { enabled: true });
  await win.webContents.debugger.sendCommand('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
  for (const width of [1280, 390]) for (const theme of ['light', 'dark']) {
    await win.webContents.debugger.sendCommand('Emulation.setDeviceMetricsOverride', { width, height: 900, deviceScaleFactor: 1, mobile: false });
    await inspect(`localStorage.setItem('bloons-guide-theme',${JSON.stringify(theme)})`);
    for (const page of ['', 'subscriptions/', 'wiki/vm-connection/', 'download/']) {
      context = { width, theme, page }; await win.loadURL(origin + '/' + page); win.webContents.focus();
      await win.webContents.debugger.sendCommand('Emulation.setFocusEmulationEnabled', { enabled: true });
      await pause(120); pages++;
      check(await inspect('innerWidth') === width, 'Requested CSS viewport missing');
      check(await inspect('document.documentElement.dataset.theme') === theme, 'Theme missing');
      check(await inspect('document.documentElement.scrollWidth<=innerWidth+1'), 'Document overflows');
      const ratios = await inspect(`(()=>{
        const l=c=>{const v=c.match(/[\\d.]+/g).slice(0,3).map(Number).map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4});return v[0]*.2126+v[1]*.7152+v[2]*.0722};
        return ['bg','solid','soft','mint','blue'].map(name=>{const probe=document.createElement('span');probe.style.cssText='color:var(--muted);background:var(--'+name+')';document.body.append(probe);const style=getComputedStyle(probe),a=l(style.color),b=l(style.backgroundColor);probe.remove();return {surface:name,ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)}});
      })()`);
      for (const value of ratios) { contrasts++; check(Number.isFinite(value.ratio) && value.ratio >= 4.5, 'Secondary text contrast', value); }
      await win.webContents.debugger.sendCommand('DOM.enable');
      await win.webContents.debugger.sendCommand('CSS.enable');
      const {root: domRoot} = await win.webContents.debugger.sendCommand('DOM.getDocument');
      const states = [
        ['.site-footer>div:nth-child(2)>a', 'hover', 'color', 4.5],
        ['.site-footer>div:nth-child(2)>a', 'focus-visible', 'outlineColor', 3],
        ['#theme-toggle', 'focus-visible', 'outlineColor', 3],
      ];
      if(width===1280)states.push(['.topbar nav a:not([aria-current])','hover','color',4.5]);
      if(page==='subscriptions/')states.push(['[data-billing="annual"]','focus-visible','outlineColor',3]);
      if(page==='download/')states.push(['.download-faq summary','focus-visible','outlineColor',3]);
      for(const [selector,pseudo,property,minimum] of states){
        const {nodeId} = await win.webContents.debugger.sendCommand('DOM.querySelector',{nodeId:domRoot.nodeId,selector});
        check(!!nodeId,'Interaction target missing',selector);if(!nodeId)continue;
        await win.webContents.debugger.sendCommand('CSS.forcePseudoState',{nodeId,forcedPseudoClasses:[pseudo]});await pause(250);
        const samples=await inspect(`(()=>{
          const el=document.querySelector(${JSON.stringify(selector)}),style=getComputedStyle(el),foreground=style[${JSON.stringify(property)}];
          const l=c=>{const v=c.match(/[\\d.]+/g).slice(0,3).map(Number).map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4});return v[0]*.2126+v[1]*.7152+v[2]*.0722};
          return ['bg','solid','soft','mint','blue'].map(name=>{const probe=document.createElement('span');probe.style.background='var(--'+name+')';document.body.append(probe);const background=getComputedStyle(probe).backgroundColor,a=l(foreground),b=l(background);probe.remove();return {surface:name,foreground,background,ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05),outlineStyle:style.outlineStyle,outlineWidth:parseFloat(style.outlineWidth)}});
        })()`);
        for(const sample of samples){interactions++;check(Number.isFinite(sample.ratio)&&sample.ratio>=minimum&&
          (property!=='outlineColor'||sample.outlineStyle!=='none'&&sample.outlineWidth>0),'Interaction contrast',{selector,pseudo,minimum,...sample});}
        await win.webContents.debugger.sendCommand('CSS.forcePseudoState',{nodeId,forcedPseudoClasses:[]});await pause(250);
      }

      if (width === 390) {
        await inspect("document.querySelector('.menu-toggle').focus()"); await press('Enter'); await press('Tab');
        check(await inspect("!document.querySelector('#mobile-nav').hidden && !!document.activeElement.closest('#mobile-nav')"), 'Menu did not open with keyboard');
        await press('Escape');
        check(await inspect("document.querySelector('#mobile-nav').hidden && document.querySelector('.menu-toggle').getAttribute('aria-expanded')==='false' && document.activeElement.matches('.menu-toggle')"), 'Escape did not restore toggle focus');
        await inspect("document.querySelector('.menu-toggle').focus()"); await press('Tab');
        check(await inspect("!!document.activeElement.closest('main') && document.activeElement.getClientRects().length>0"), 'Tab after Escape did not reach visible main content');
        await inspect("window.__fixtureFocus=document.activeElement");
        await press('Escape');
        check(await inspect("document.activeElement===window.__fixtureFocus"), 'Closed menu stole Escape focus');
        await press('Tab', ['shift']);
        check(await inspect("document.activeElement.matches('.menu-toggle')"), 'Reverse traversal did not reach toggle');
        await press('Enter'); await inspect("document.querySelector('#theme-toggle').focus();document.querySelector('main').click()");
        check(await inspect("document.querySelector('#mobile-nav').hidden && document.activeElement.matches('#theme-toggle')"), 'Pointer dismissal stole focus');
      }
      if (page === 'wiki/vm-connection/') {
        const table = await inspect(`(()=>{const t=document.querySelector('table'),w=t.closest('.wiki-table-scroll'),caption=t.querySelector('caption');return {wrapped:!!w,tabIndex:w?.tabIndex,role:w?.getAttribute('role'),named:!!caption.id&&w?.getAttribute('aria-labelledby')===caption.id,columns:t.querySelectorAll('thead th[scope=col]').length,rows:t.querySelectorAll('tbody th[scope=row]').length,scrollable:!!w&&w.scrollWidth>w.clientWidth}})()`);
        check(table.wrapped && table.tabIndex === 0 && table.role === 'region' && table.named && table.columns === 2 && table.rows === 8, 'Table semantics or keyboard access missing', table);
        if (width === 390 && table.wrapped) {
          check(table.scrollable, 'Table should scroll inside its region');
          await inspect("const w=document.querySelector('.wiki-table-scroll');w.scrollIntoView({block:'center'});w.focus()");
          await press('Right'); await pause(250);
          check(await inspect("document.querySelector('.wiki-table-scroll').scrollLeft>0"), 'Arrow key did not scroll the table');
          await press('Tab');
          check(await inspect("!document.activeElement.matches('.wiki-table-scroll')"), 'Tab trapped in table region');
        }
      }
    }
  }
  console.log(JSON.stringify({ pages, contrasts, interactions, failures, errors }));
  win.destroy(); server.closeAllConnections(); server.close(() => app.exit(failures.length || errors.length ? 1 : 0));
})().catch(error => { console.error(context, error.stack, errors); if (win && !win.isDestroyed()) win.destroy(); server.closeAllConnections(); app.exit(1); });
