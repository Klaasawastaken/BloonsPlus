const {app,BrowserWindow,session}=require('electron');
const fs=require('node:fs'),http=require('node:http'),path=require('node:path');
const root=path.resolve(__dirname,'../..');
const folder=process.env.BLOONS_RENDERER_TEST_PROFILE;
if(!folder)throw new Error('Run through test-app-report-renderer.js to isolate and clean up the profile');
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
  if(route==='/api/setup/controller')body={protocolVersion:1,version:'9.8.7-fixture.1'};
  else if(route==='/api/setup/session')body=setup;
  else if(route==='/api/setup/status')body={applicable:true,allDone:true,vm:{state:'online'},job:{running:false},steps:['vmp','appsandbox','daemon','iso','vm','provision','connected','steam'].map(id=>({id,title:id,done:true,state:'complete'})),next:{message:'Ready'}};
  else if(route==='/api/progress/local-save')body={available:false,reason:'Synthetic unavailable profile; no real saves read'};
  else if(route==='/api/progress')body={source:'live-scan',maps:{},towers:{},achievements:{}};
  else if(route==='/api/farm/status')body={running:false,victories:3,defeats:1,log:['[fixture] round=60 map=cubism password=fixture-private-value', 'C:\\Users\\FixtureAccount\\run.log contact fixture-person@example.invalid'],runtime:{available:true},progress:{},serverTime:Date.now()};
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
 await app.whenReady(); await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const origin='http://127.0.0.1:'+server.address().port;
 session.defaultSession.webRequest.onBeforeRequest((d,cb)=>cb({cancel:!d.url.startsWith(origin+'/')&&!d.url.startsWith('data:')}));
 win=new BrowserWindow({show:false,width:1440,height:900,webPreferences:{offscreen:true,backgroundThrottling:false,contextIsolation:true,sandbox:true}});
 win.webContents.setWindowOpenHandler(()=>{errors.push('Unexpected external window');return {action:'deny'}});
 win.webContents.on('render-process-gone',(_event,details)=>errors.push('Renderer exit '+details.reason));
 await win.loadURL(origin+'/fixture-prefs');
 await win.webContents.executeJavaScript('localStorage.setItem("bloondesk-save-v1",JSON.stringify({startupMode:"off",theme:"light"}));localStorage.setItem("bloonsStartupSeen","1");localStorage.setItem("bloonsSetupPrepageSeen","1")');
 await win.loadURL(origin+'/');await delay(1000);
 if(process.env.BLOONS_REPORT_NEGATIVE==='1')await win.webContents.executeJavaScript("document.getElementById('issue-report-dialog').showModal=function(){this.show()};void 0");
 win.webContents.debugger.attach('1.3');
 await win.webContents.debugger.sendCommand('Accessibility.enable');
 const evaluate=expression=>win.webContents.executeJavaScript(expression);
 const key=async(keyCode,modifiers=[])=>{win.webContents.sendInputEvent({type:'keyDown',keyCode,modifiers});if(keyCode==='Enter')win.webContents.sendInputEvent({type:'char',keyCode:'\r',modifiers});win.webContents.sendInputEvent({type:'keyUp',keyCode,modifiers});await delay(25)};
 const check=(condition,kind,context)=>{results.push({kind,ok:!!condition,...context});if(!condition)failures.push({kind,...context})};

 // A native dialog in a separate hidden window establishes Chromium's focus
 // boundary: offscreen windows can temporarily focus BODY before wrapping.
 // Accept that neutral boundary only when this baseline independently proves it;
 // never accept an underlying app control receiving focus.
 const native=new BrowserWindow({show:false,width:600,height:500,webPreferences:{offscreen:true,backgroundThrottling:false,contextIsolation:true,sandbox:true}});
 await native.loadURL(origin+'/fixture-prefs');
 await native.webContents.executeJavaScript("document.body.innerHTML='<button id=outside>Outside</button><dialog><button id=first>First</button><button id=last>Last</button></dialog>';document.querySelector('dialog').showModal();document.getElementById('last').focus()");
 await delay(150);
 const nativeTraversal=[];
 for(let i=0;i<6;i++){
  native.webContents.sendInputEvent({type:'keyDown',keyCode:'Tab'});native.webContents.sendInputEvent({type:'keyUp',keyCode:'Tab'});await delay(40);
  nativeTraversal.push(await native.webContents.executeJavaScript("({tag:document.activeElement.tagName,id:document.activeElement.id,inside:document.querySelector('dialog').contains(document.activeElement),focused:document.hasFocus()})"));
 }
 const nativeBoundary=nativeTraversal.some(x=>x.tag==='BODY')&&nativeTraversal.every(x=>x.inside||x.tag==='BODY');
 native.destroy();
 for(const [width,height] of [[1440,900],[550,700]])for(const theme of ['light','dark'])for(const entry of ['logs','settings']){
  const context={width,height,theme,entry};stage=JSON.stringify(context);
  win.setContentSize(width,height);await evaluate(`(()=>{const r=document.querySelector('#theme-setting input[value="${theme}"]');r.checked=true;r.dispatchEvent(new Event('change',{bubbles:true}));document.querySelector('.nav-item[data-view="${entry}"]').click()})()`);await delay(200);
  const launcher=entry==='logs'?'report-issue':'settings-report-issue';
  await evaluate(`document.getElementById('${launcher}').focus()`);await key('Enter');
  let state=await evaluate(`(()=>{const d=document.getElementById('issue-report-dialog'),r=d.getBoundingClientRect();return {open:d.open,modal:d.matches(':modal'),inside:d.contains(document.activeElement),width:r.width,fit:r.left>=0&&r.right<=innerWidth+1&&r.top>=0&&r.bottom<=innerHeight+1,overflow:d.scrollWidth>d.clientWidth+1,view:document.querySelector('.view:not(.hidden)').id}})()`);
  check(state.open&&state.modal&&state.inside,'open-modal-focus',{...context,state});
  check(state.fit&&!state.overflow,'dialog-bounds',{...context,state});
  const barrier=await evaluate(`(()=>{document.getElementById('${launcher}').focus();return document.activeElement.id!=='${launcher}'})()`);
  check(barrier,'background-focus-blocked',context);
  await evaluate("document.getElementById('report-close').focus()");
  const traversal=[];
  for(let i=0;i<9;i++){await key('Tab');traversal.push(await evaluate(`(()=>{const e=document.activeElement;return {id:e.id,tag:e.tagName,inside:document.getElementById('issue-report-dialog').contains(e)}})()`))}
  check(traversal.every(x=>x.inside||(nativeBoundary&&x.tag==='BODY'))&&traversal.some(x=>x.id==='report-description')&&traversal.some(x=>x.id==='report-submit'),'tab-contained',{...context,traversal});
  await evaluate("document.getElementById('report-close').focus()");await key('Tab',['shift']);
  if(nativeBoundary&&await evaluate("document.activeElement.tagName==='BODY'"))await key('Tab',['shift']);
  check(await evaluate("document.getElementById('issue-report-dialog').contains(document.activeElement)&&document.activeElement.id==='report-submit'"),'reverse-tab-wrap',context);
  await evaluate("document.getElementById('report-description').value='accountId=fixture-description-secret user@example.invalid';document.getElementById('report-description').dispatchEvent(new Event('input',{bubbles:true}))");
  const output=await evaluate("(()=>{const u=new URL(document.getElementById('report-submit').href);return {origin:u.origin,path:u.pathname,body:u.searchParams.get('body'),preview:document.getElementById('report-preview').textContent}})()");
  check(output.origin==='https://github.com'&&output.path==='/Klaasawastaken/BloonsPlus/issues/new'&&output.body.includes('round=60')&&output.preview.includes('cubism'),'reviewable-context',context);
  check(output.body.includes('App: Bloons+ 9.8.7-fixture.1'),'observed-controller-version',context);
  check(!/fixture-private-value|FixtureAccount|fixture-description-secret|fixture-person@|user@example/i.test(output.body+output.preview),'redacted-preview-and-link',context);
  const ax=(await win.webContents.debugger.sendCommand('Accessibility.getFullAXTree')).nodes.filter(n=>!n.ignored);
  const has=(role,name)=>ax.some(n=>n.role?.value===role&&n.name?.value===name);
  check(has('dialog','Report an issue')&&has('button','Close issue report')&&has('textbox','WHAT HAPPENED?')&&has('link','Continue to GitHub ↗'),'accessible-names',context);
  await key('Escape');
  check(await evaluate(`!document.getElementById('issue-report-dialog').open&&document.activeElement.id==='${launcher}'&&document.querySelector('.view:not(.hidden)').id==='${entry}'`),'escape-restores-entry',context);
  await key('Enter');await evaluate("document.getElementById('report-close').focus()");await key('Enter');
  check(await evaluate(`!document.getElementById('issue-report-dialog').open&&document.activeElement.id==='${launcher}'`),'close-restores-entry',context);
 }
 console.log(JSON.stringify({checks:results.length,nativeBoundary,nativeTraversal,failures,errors,scope:'Actual hidden Electron renderer; synthetic APIs and keyboard events; no physical screen-reader claim'}));
 win.destroy();server.closeAllConnections();server.close(()=>app.exit(failures.length||errors.length?1:0));
})().catch(error=>{console.error(stage,error.stack);if(win&&!win.isDestroyed())win.destroy();server.closeAllConnections();app.exit(1)});
