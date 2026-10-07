const { app, BrowserWindow, session } = require('electron');
const fs = require('node:fs'), http = require('node:http'), path = require('node:path');
const root = path.resolve(__dirname, '../../docs');
const profile = process.env.BLOONS_RENDERER_TEST_PROFILE;
if (!profile) throw new Error('Use test-site-textscale-renderer.js for profile isolation and cleanup');
app.setPath('userData', profile); app.setPath('sessionData', profile); app.setPath('logs', profile);
app.disableHardwareAcceleration(); app.on('window-all-closed', () => {});
const failures = [], errors = [], fontObservations = [];
// Opt-in network acceptance; ordinary checks keep external requests blocked.
const webFonts = process.env.BLOONS_SITE_WEB_FONTS === '1';
const contentPages = [];
function collect(folder) {
  for (const entry of fs.readdirSync(folder, { withFileTypes: true })) {
    const file = path.join(folder, entry.name);
    if (entry.isDirectory()) collect(file);
    else if (entry.name.endsWith('.html') && !/<meta[^>]+http-equiv=["']refresh["']/i.test(fs.readFileSync(file, 'utf8'))) {
      const relative = path.relative(root, file).replace(/\\/g, '/');
      contentPages.push(relative === 'index.html' ? '' : relative.replace(/index[.]html$/, ''));
    }
  }
}
collect(root);
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
  session.defaultSession.webRequest.onBeforeRequest((details, callback) => callback({cancel: !details.url.startsWith(origin + '/') && !details.url.startsWith('data:') && !(webFonts && /^https:\/\/(?:fonts[.]googleapis[.]com|fonts[.]gstatic[.]com)\//.test(details.url))}));
  win = new BrowserWindow({show:false,width:1280,height:900,webPreferences:{offscreen:true,backgroundThrottling:false,contextIsolation:true,sandbox:true}});
  await win.loadURL(origin+'/fixture-prefs');win.webContents.debugger.attach('1.3');
  await win.webContents.debugger.sendCommand('Emulation.setFocusEmulationEnabled',{enabled:true});
  if(webFonts){await win.webContents.debugger.sendCommand('DOM.enable');await win.webContents.debugger.sendCommand('CSS.enable');}
  await win.webContents.debugger.sendCommand('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  for (const width of [1280, 390]) for (const theme of ['light', 'dark']) {
    await win.webContents.debugger.sendCommand('Emulation.setDeviceMetricsOverride', { width, height:900, deviceScaleFactor:1, mobile:false });
    await inspect(`localStorage.setItem('bloons-guide-theme',${JSON.stringify(theme)})`);
    for (const page of contentPages) {
      context = { width, theme, page }; await win.loadURL(origin + '/' + page);
      if(webFonts){
        await inspect(`Promise.race([document.fonts.ready,new Promise((_,reject)=>setTimeout(()=>reject(new Error('Font readiness timeout')),15000))]).then(()=>true)`);
        const {root:doc}=await win.webContents.debugger.sendCommand('DOM.getDocument');
        for(const [selector,expected] of [['main h1','Manrope'],['main p','DM Sans']]){
          const {nodeId}=await win.webContents.debugger.sendCommand('DOM.querySelector',{nodeId:doc.nodeId,selector});
          const {fonts}=await win.webContents.debugger.sendCommand('CSS.getPlatformFontsForNode',{nodeId});
          fontObservations.push({...context,selector,fonts});
          // Variable fonts expose internal style/optical-size suffixes such as
          // Manrope ExtraLight and DM Sans 9pt. Require an actual custom font,
          // not just the CSS family declaration or a successful network request.
          check(fonts.some(f=>f.isCustomFont&&f.glyphCount>0&&(f.familyName===expected||f.familyName.startsWith(expected+' '))),
            'Web font not actually used',{selector,expected,fonts});
        }
      }

      const scaling = await inspect(`(()=>{
        const heading=document.querySelector('main h1');if(!heading)throw Error('Missing page heading');
        const before=parseFloat(getComputedStyle(heading).fontSize);
        const values=[...document.querySelectorAll('*')].map(el=>[el,parseFloat(getComputedStyle(el).fontSize)]);
        for(const [el,size] of values)if(size>0)el.style.setProperty('font-size',(size*2)+'px','important');
        return {before,after:parseFloat(getComputedStyle(heading).fontSize)};
      })()`);
      await pause(100); pages++;
      const state = await inspect(`(()=>{
        const h=document.querySelector('main h1'),rect=h.getBoundingClientRect(),range=document.createRange();range.selectNodeContents(h);
        return {width:innerWidth,theme:document.documentElement.dataset.theme,scroll:document.documentElement.scrollWidth,
          heading:{left:rect.left,right:rect.right},text:[...range.getClientRects()].map(r=>({left:r.left,right:r.right})),
          zoom:visualViewport.scale};
      })()`);
      check(state.width === width && state.theme === theme && state.zoom === 1, 'Fixture mismatch', state);
      check(Math.abs(scaling.after / scaling.before - 2) < .01, 'Text was not doubled', scaling);
      check(state.scroll <= width + 1, 'Document overflows with doubled text', state);
      check(state.text.every(rect => rect.left >= state.heading.left - 1 && rect.right <= state.heading.right + 1), 'Heading escapes its column', state);
    }
  }
  console.log(JSON.stringify({pages,contentPages:contentPages.length,webFonts,fontChecks:fontObservations.length,failures,errors,scope:'Computed font sizes doubled at fixed viewport; normal states only, no physical OS text-scaling or full clipping claim'}));win.destroy();server.closeAllConnections();server.close(()=>app.exit(failures.length||errors.length?1:0));
})().catch(error=>{console.error(context,error.stack);if(win&&!win.isDestroyed())win.destroy();server.closeAllConnections();app.exit(1)});
