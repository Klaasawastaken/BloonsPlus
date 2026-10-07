const {app,BrowserWindow,session}=require('electron');
const fs=require('node:fs'),http=require('node:http'),path=require('node:path');
const root=path.resolve(__dirname,'../..');
const folder=process.env.BLOONS_RENDERER_TEST_PROFILE;
if(!folder)throw new Error('Run through test-app-appearance-renderer.js to isolate and clean up the profile');
app.setPath('userData',folder);app.setPath('sessionData',folder);app.setPath('logs',folder);
app.disableHardwareAcceleration();app.on('window-all-closed',()=>{});
const results=[],failures=[],errors=[],contrast=[];let win,server,stage="startup";
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const combo={cubism:{hard:[{filename:'fixture-only.btd6',requirements:{hero:'Sauda',towers:{dart_monkey:[5,2,0],sniper_monkey:[0,2,4]}}}],chimps:[{filename:'fixture-chimps.btd6',requirements:{hero:'Sauda',towers:{dart_monkey:[5,2,0]}}}]},logs:{easy:[{filename:'fixture-easy.btd6',requirements:{towers:{dart_monkey:[2,0,0]}}}]}};
const setup={protocolVersion:1,sessionId:'a'.repeat(32),sequence:0,phase:'complete',status:'Ready',completedWeight:100};
server=http.createServer((req,res)=>{
 const route=new URL(req.url,'http://localhost').pathname;
 if(route==='/api/setup/session/bootstrap'&&req.method==='POST'){req.resume();res.setHeader('Content-Type','application/json');res.end(JSON.stringify(setup));return;}
 if(req.method!=='GET'){errors.push('Unexpected mutation '+req.method+' '+route);res.writeHead(405);res.end();return;}
 if(route==='/fixture-prefs'){res.setHeader('Content-Type','text/html');res.end('<!doctype html><title>Private fixture</title>');return;}
 if(route.startsWith('/api/')){
  let body={};
  if(route==='/api/setup/controller')body={protocolVersion:1};
  else if(route==='/api/setup/session')body=setup;
  else if(route==='/api/setup/status')body={applicable:true,allDone:true,vm:{state:'online'},job:{running:false},steps:['vmp','appsandbox','daemon','iso','vm','provision','connected','steam'].map(id=>({id,title:id,done:true,state:'complete'})),next:{message:'Ready'}};
  else if(route==='/api/progress/local-save')body={available:false,reason:'Synthetic unavailable profile; no real saves read'};
  else if(route==='/api/progress')body={source:'live-scan',maps:{},towers:{},achievements:{}};
  else if(route==='/api/farm/status')body={running:false,victories:3,defeats:1,log:['[fixture] Idle'],runtime:{available:true},progress:{},serverTime:Date.now()};
  else if(route==='/api/game-state')body={state:null};
  else if(route==='/api/game-status')body={running:false};
  else if(route==='/api/playthrough-combos')body=combo;
  else if(route==='/api/map-order')body={maps:{}};
  else if(route==='/api/upgrade-memory')body={runs:{}};
  else if(route==='/api/route-failures')body={failures:[]};
  else if(route==='/api/achievements/steam')body={available:false,achievements:[]};
  else if(route==='/api/routes')body={routes:[]};
  else if(route==='/api/playthroughs')body=[];
  res.setHeader('Content-Type','application/json');res.end(JSON.stringify(body));return;
 }
 const file=path.resolve(root,decodeURIComponent(route==='/'?'index.html':route.slice(1)));
 if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return;}
 const mime={'.html':'text/html','.css':'text/css','.js':'application/javascript','.svg':'image/svg+xml','.png':'image/png','.ico':'image/x-icon','.json':'application/json'};
 if(!mime[path.extname(file)]){res.writeHead(404);res.end();return;}
 res.setHeader('Content-Type',mime[path.extname(file)]);fs.createReadStream(file).pipe(res);
});

(async()=>{
 await app.whenReady();await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const origin='http://127.0.0.1:'+server.address().port;
 session.defaultSession.webRequest.onBeforeRequest((d,cb)=>cb({cancel:!d.url.startsWith(origin+'/')&&!d.url.startsWith('data:')}));
 win=new BrowserWindow({show:false,width:1440,height:900,webPreferences:{offscreen:true,backgroundThrottling:false,contextIsolation:true,sandbox:true}});
 win.webContents.on('console-message',(_event,level,message)=>{if(level>=2)console.error(message)});
 await win.loadURL(origin+'/fixture-prefs');
 await win.webContents.executeJavaScript('localStorage.setItem("bloondesk-save-v1",JSON.stringify({startupMode:"off",theme:"light"}));localStorage.setItem("bloonsStartupSeen","1");localStorage.setItem("bloonsSetupPrepageSeen","1")');
 await win.loadURL(origin+'/');await delay(1000);
 win.webContents.debugger.attach('1.3');
 await win.webContents.debugger.sendCommand('DOM.enable');await win.webContents.debugger.sendCommand('CSS.enable');
 await win.webContents.executeJavaScript(`(()=>{const probe=document.createElement('div');probe.id='appearance-contrast';probe.style.cssText='position:fixed;left:0;top:0;background:var(--bg);z-index:99999';probe.innerHTML='<button id="contrast-primary" class="primary-button">Start sweep</button><span class="tier-pill invalid">Locked</span><span class="tier-pill unknown">Unknown</span><span class="eyebrow green">Automation</span>';document.body.append(probe)})()`);
 const {root:documentNode}=await win.webContents.debugger.sendCommand('DOM.getDocument');
 const {nodeId:primaryNode}=await win.webContents.debugger.sendCommand('DOM.querySelector',{nodeId:documentNode.nodeId,selector:'#contrast-primary'});
 const measureContrast=async(theme,hover)=>{
  const values=await win.webContents.executeJavaScript(`(()=>{
   const luminance=color=>{const channels=color.match(/[\\d.]+/g).slice(0,3).map(Number).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4});return channels[0]*.2126+channels[1]*.7152+channels[2]*.0722};
   return [...document.querySelectorAll('#appearance-contrast>*')].map(el=>{const c=getComputedStyle(el),bg=c.backgroundColor==='rgba(0, 0, 0, 0)'?getComputedStyle(el.parentElement).backgroundColor:c.backgroundColor,a=luminance(c.color),b=luminance(bg);return {selector:el.className,ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05),foreground:c.color,background:bg}});
  })()`);
  for(const value of (hover?values.slice(0,1):values)){const result={theme,hover,...value};contrast.push(result);if(!Number.isFinite(value.ratio)||value.ratio<4.5)failures.push({kind:'contrast',...result});}
 };
 if(process.env.BLOONS_APPEARANCE_NEGATIVE==='1')await win.webContents.executeJavaScript("(()=>{const style=document.createElement('style');style.textContent='#settings .settings-appearance{display:flex;justify-content:space-between;gap:24px}';document.head.append(style)})()");
 const dimensions=[[1440,900],[1080,680],[550,800],[420,800]];
 for(const [width,height] of dimensions)for(const zoom of (width>=1080?[1,1.25,1.5,2]:[1])){
  win.setContentSize(width,height);win.webContents.setZoomFactor(zoom);await delay(60);
  for(const theme of ['light','dark']){
   stage=JSON.stringify({width,zoom,theme});
   await win.webContents.executeJavaScript(`(()=>{const r=document.querySelector('#theme-setting input[value="${theme}"]');r.checked=true;r.dispatchEvent(new Event('change',{bubbles:true}));document.querySelector('.nav-item[data-view="settings"]').click()})()`);
   await delay(400);
   await measureContrast(theme,false);
   await win.webContents.debugger.sendCommand('CSS.forcePseudoState',{nodeId:primaryNode,forcedPseudoClasses:['hover']});await delay(250);
   await measureContrast(theme,true);
   await win.webContents.debugger.sendCommand('CSS.forcePseudoState',{nodeId:primaryNode,forcedPseudoClasses:[]});await delay(250);
   for(const value of ['full','reduced','off']){
    const result=await win.webContents.executeJavaScript(`(()=>{const s=document.getElementById('startup-mode');s.value='${value}';s.dispatchEvent(new Event('change',{bubbles:true}));const b=s.nextElementSibling,t=b.firstElementChild,p=s.closest('.settings-appearance'),r=b.getBoundingClientRect(),pr=p.getBoundingClientRect(),hint=p.querySelector('.field-hint').getBoundingClientRect();return {text:t.textContent,client:t.clientWidth,scroll:t.scrollWidth,width:r.width,left:r.left,right:r.right,panelLeft:pr.left,panelRight:pr.right,hintTop:hint.top,controlBottom:r.bottom,persisted:JSON.parse(localStorage.getItem('bloondesk-save-v1')).startupMode,cssWidth:innerWidth}})()`);
    const context={windowWidth:width,zoom,theme,value,...result};results.push(context);
    if(result.scroll>result.client+1||result.client<=0||result.width<80)failures.push({kind:'clipped',...context});
    if(result.left<result.panelLeft||result.right>result.panelRight||result.hintTop+1<result.controlBottom)failures.push({kind:'layout',...context});
    if(result.persisted!==value||result.text.toLowerCase()!==value)failures.push({kind:'preference',...context});
   }
   await win.webContents.executeJavaScript("document.getElementById('startup-mode').nextElementSibling.scrollIntoView({block:'center',behavior:'instant'})");await delay(100);
   await win.webContents.executeJavaScript("document.getElementById('startup-mode').nextElementSibling.click()");await delay(100);
   const menu=await win.webContents.executeJavaScript("(()=>{const r=document.querySelector('.app-select-menu').getBoundingClientRect();return {inside:r.left>=0&&r.top>=0&&r.right<=innerWidth+1&&r.bottom<=innerHeight+1,options:document.querySelectorAll('.app-select-menu [role=option]').length}})()");
   if(!menu.inside||menu.options!==3)failures.push({kind:'menu',width,zoom,theme,...menu});
   win.webContents.sendInputEvent({type:'keyDown',keyCode:'Escape'});win.webContents.sendInputEvent({type:'keyUp',keyCode:'Escape'});await delay(20);
   if(!await win.webContents.executeJavaScript("(()=>{const b=document.getElementById('startup-mode').nextElementSibling;return b.getAttribute('aria-expanded')==='false'&&document.activeElement===b})()"))failures.push({kind:'escape-focus',width,zoom,theme});
  }
 }
 console.log(JSON.stringify({checks:results.length,contrastChecks:contrast.length,failures,errors,scope:'Actual hidden renderer; synthetic APIs; desktop zoom and narrow widths; no physical DPI or screen-reader claim'}));
 win.destroy();server.closeAllConnections();server.close(()=>app.exit(failures.length||errors.length?1:0));
})().catch(error=>{console.error(stage,error.stack);if(win&&!win.isDestroyed())win.destroy();server.closeAllConnections();app.exit(1)});
