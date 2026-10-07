const { app, BrowserWindow, session } = require('electron');
const fs = require('node:fs'), http = require('node:http'), path = require('node:path');
const root = path.resolve(__dirname, '../../docs');
const profile = process.env.BLOONS_RENDERER_TEST_PROFILE;
if (!profile) throw new Error('Use test-site-pixel-contrast-renderer.js for profile isolation and cleanup');
app.setPath('userData', profile); app.setPath('sessionData', profile); app.setPath('logs', profile);
app.disableHardwareAcceleration(); app.on('window-all-closed', () => {});
const errors = [];
let win, pages = 0;
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
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

const { nativeImage }=require('electron');
const lum=c=>c.map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((n,v,i)=>n+v*[.2126,.7152,.0722][i],0);
const contrast=(a,b)=>{a=lum(a);b=lum(b);return(Math.max(a,b)+.05)/(Math.min(a,b)+.05)};
(async()=>{
 await app.whenReady();await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const origin='http://127.0.0.1:'+server.address().port;
 session.defaultSession.webRequest.onBeforeRequest((d,cb)=>cb({cancel:!d.url.startsWith(origin+'/')&&!d.url.startsWith('data:')}));
 win=new BrowserWindow({show:false,width:1280,height:900,webPreferences:{offscreen:true,backgroundThrottling:false,contextIsolation:true,sandbox:true}});
 await win.loadURL(origin+'/fixture-prefs');win.webContents.debugger.attach('1.3');
 const send=(method,params)=>win.webContents.debugger.sendCommand(method,params);
 await send('Emulation.setFocusEmulationEnabled',{enabled:true});
 await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
 const results=[];
 const negativeControl=process.env.BLOONS_CONTRAST_NEGATIVE_CONTROL==='1';
 for(const theme of (negativeControl?['light']:['light','dark']))for(const page of (negativeControl?['']:['','features/','subscriptions/','download/','about/','contributors/','wiki/','wiki/getting-started/'])){
  await inspect(`localStorage.setItem('bloons-guide-theme',${JSON.stringify(theme)})`);
  console.log('Loading '+theme+' '+page);await win.loadURL(origin+'/'+page);await send('Emulation.setFocusEmulationEnabled',{enabled:true});
  await inspect(`(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(i=>{i.loading='eager';return Promise.race([i.decode().catch(()=>{}),new Promise(r=>setTimeout(r,2000))])}));const s=document.createElement('style');s.textContent='html{scrollbar-width:none!important}::-webkit-scrollbar{display:none!important}*,*::before,*::after{animation:none!important;transition:none!important}.reveal{opacity:1!important;transform:none!important}';document.head.append(s)})()`);
  // Full-page capture suppresses the scrollbar; stabilize that layout before
  // measuring text ranges so narrow glyphs do not shift during capture.
  await pause(100);
  if(negativeControl)await inspect(`document.querySelector('.preview-tag span').style.cssText='color:rgb(245,246,241)!important;background:rgb(245,246,241)!important'`);
  const nodes=await inspect(`(()=>{if(!document.querySelector('main h1'))throw Error('Expected page content is missing');const items=[],w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;while(n=w.nextNode()){if(!n.textContent.trim()||['SCRIPT','STYLE','SVG'].includes(n.parentElement.tagName)||n.parentElement.closest('[aria-hidden="true"]')||n.parentElement.matches('.brand .plus')||n.parentElement.closest('.sr-only')||!n.parentElement.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}))continue;const e=n.parentElement,c=getComputedStyle(e),r=document.createRange();r.selectNode(n);const rects=[...r.getClientRects()].filter(x=>x.width&&x.height).map(x=>({x:x.x,y:x.y+scrollY,width:x.width,height:x.height}));if(!rects.some(r=>r.x+r.width>0&&r.x<innerWidth&&r.y+r.height>0&&r.y<document.documentElement.scrollHeight)||c.visibility!=='visible')continue;let opacity=1,images=[];for(let a=e;a;a=a.parentElement){const cs=getComputedStyle(a);opacity*=Number(cs.opacity);if(cs.backgroundImage!=='none')images.push(cs.backgroundImage)}if(opacity<.999)continue;const color=c.color.match(/[\\d.]+/g).map(Number);items.push({text:n.textContent.trim().slice(0,80),selector:e.tagName+'.'+e.className,color,rects,images,size:parseFloat(c.fontSize),weight:parseFloat(c.fontWeight)})}return {items,width:innerWidth,height:document.documentElement.scrollHeight,theme:document.documentElement.dataset.theme}})()`);
  if(nodes.theme!==theme)throw Error('Wrong theme');
  const shot=async()=>{const r=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width:nodes.width,height:nodes.height,scale:1}});const im=nativeImage.createFromDataURL('data:image/png;base64,'+r.data);return {buf:im.toBitmap(),...im.getSize()}};
  const before=await shot();
  await inspect(`(()=>{const s=document.createElement('style');s.textContent='*,*::before,*::after{-webkit-text-fill-color:transparent!important;text-shadow:none!important}';document.head.append(s)})()`);await pause(50);
  const after=await shot();if(before.width!==after.width||before.height!==after.height)throw Error('Capture mismatch');
  // Find glyph coverage independently of the original text color. Comparing
  // the original to the background would silently miss invisible/faint text.
  await inspect(`(()=>{const s=document.createElement('style');s.id='contrast-mask';s.textContent='*,*::before,*::after{-webkit-text-fill-color:#000!important}';document.head.append(s)})()`);await pause(50);
  const black=await shot();
  await inspect(`document.getElementById('contrast-mask').textContent='*,*::before,*::after{-webkit-text-fill-color:#fff!important}'`);await pause(50);
  const white=await shot();
  if(black.width!==after.width||black.height!==after.height||white.width!==after.width||white.height!==after.height)throw Error('Glyph mask geometry changed');
  const scale=before.width/nodes.width;
  for(const n of nodes.items){let minimum=Infinity,pixels=0;const rgb=n.color.slice(0,3),alpha=n.color[3]??1;
   for(const r of n.rects)for(let y=Math.max(0,Math.floor(r.y*scale));y<Math.min(after.height,Math.ceil((r.y+r.height)*scale));y++)for(let x=Math.max(0,Math.floor(r.x*scale));x<Math.min(after.width,Math.ceil((r.x+r.width)*scale));x++){
    const i=(y*after.width+x)*4,b=[after.buf[i+2],after.buf[i+1],after.buf[i]],a=[black.buf[i+2],black.buf[i+1],black.buf[i]],w=[white.buf[i+2],white.buf[i+1],white.buf[i]];
    if(Math.max(...a.map((v,j)=>Math.abs(v-w[j])))<1)continue;
    const fg=rgb.map((v,j)=>v*alpha+b[j]*(1-alpha));minimum=Math.min(minimum,contrast(fg,b));pixels++;
   }
   {const threshold=n.size>=24||(n.size>=18.667&&n.weight>=700)?3:4.5;results.push({theme,page,text:n.text,selector:n.selector,images:n.images.length,pixels,ratio:pixels?+minimum.toFixed(3):null,threshold,passes:pixels>0&&minimum>=threshold})}
  }
  pages++;console.log('Audited '+theme+' '+(page||'/'));
 }
 const report={pages,errors,checks:results.length,failures:results.filter(x=>!x.passes),scope:'Actual rendered backgrounds under independently located glyph pixels with computed foreground color; excludes ancestor opacity, clipped screen-reader-only and aria-hidden content. Brand-logo lettering is exempt; small concept symbols use the stricter text threshold. This does not certify all states or accessible names.'};
 console.log(JSON.stringify(report));win.destroy();server.closeAllConnections();server.close(()=>app.exit(0));
})().catch(e=>{console.error(e.stack);if(win&&!win.isDestroyed())win.destroy();server.closeAllConnections();app.exit(1)});
