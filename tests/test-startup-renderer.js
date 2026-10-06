// Actual startup assets in an isolated Chromium window; no live controller calls.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const root = path.resolve('.');
const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'bloons-startup-renderer-'));
const main = path.join(folder, 'checks.cjs');
const reportPath = path.join(folder, 'result.json');
fs.writeFileSync(main, `
const {app,BrowserWindow,session}=require('electron');
const http=require('node:http'),fs=require('node:fs'),path=require('node:path');
const root=${JSON.stringify(root)},folder=${JSON.stringify(folder)};
const report=value=>fs.writeFileSync(${JSON.stringify(reportPath)},JSON.stringify(value));
app.setPath('userData',folder);app.setPath('sessionData',folder);app.setPath('logs',folder);
app.disableHardwareAcceleration();app.commandLine.appendSwitch('no-sandbox');
app.on('window-all-closed',()=>{});
let active,win,server;const failures=[],observations=[];
const check=(value,message)=>{if(!value)throw Error(message);};
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
server=http.createServer((req,res)=>{
 const route=new URL(req.url,'http://localhost').pathname;
 // Startup establishes a setup observation session; this fixture never executes commands.
 if(route==='/api/setup/session/bootstrap'&&req.method==='POST'){
  req.resume();res.setHeader('Content-Type','application/json');
  res.end(JSON.stringify({protocolVersion:1,sessionId:'a'.repeat(32),sequence:0,phase:'idle',status:'Connect your game later',completedWeight:0}));return;
 }
 if(req.method!=='GET'){failures.push('Unexpected mutation request: '+req.method+' '+route);res.writeHead(405);res.end();return;}
 if(route==='/fixture-prefs'){res.setHeader('Content-Type','text/html');res.end('<!doctype html><title>Fixture preferences</title>');return;}
 if(route.startsWith('/api/')){
  if(route==='/api/progress/local-save'){active.profileRequests=(active.profileRequests||0)+1;return;}
  let body={};
  if(route==='/api/setup/controller'){
   if(active.service==='pending')return;
   body={protocolVersion:1};
  }else if(route==='/api/setup/session')body={protocolVersion:1,sessionId:'a'.repeat(32),sequence:0,phase:'idle',status:'Connect your game later',completedWeight:0};
  else if(route==='/api/setup/status')body={applicable:true,allDone:false,vm:{state:'missing'},job:{running:false},steps:[],next:{message:'Connect your game later'}};
  else if(route.includes('playthroughs'))body=[];
  else if(route.includes('routes'))body={routes:[]};
  else if(route.includes('farm/status'))body={running:false,log:[],progress:{}};
  res.setHeader('Content-Type','application/json');res.end(JSON.stringify(body));return;
 }
 const file=path.resolve(root,decodeURIComponent(route==='/'?'index.html':route.slice(1)));
 if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return;}
 const allowed=new Set(['.html','.css','.js','.svg','.png','.ico','.woff2']);
 if(!allowed.has(path.extname(file))){res.writeHead(404);res.end();return;}
 res.setHeader('Content-Type',({'.html':'text/html','.css':'text/css','.js':'application/javascript','.svg':'image/svg+xml','.png':'image/png','.ico':'image/x-icon','.woff2':'font/woff2'})[path.extname(file)]);
 fs.createReadStream(file).pipe(res);
});
(async()=>{
 report({stage:'app-ready-wait'});await app.whenReady();await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const origin='http://127.0.0.1:'+server.address().port;
 session.defaultSession.webRequest.onBeforeRequest((details,callback)=>callback({cancel:!details.url.startsWith(origin+'/')&&!details.url.startsWith('data:')}));
 for(const scenario of [
  {name:'off-slow-profile',mode:'off',first:false,rate:1,software:false,service:'ready'},
  {name:'first-throttled',mode:'full',first:true,rate:4,software:false,service:'ready'},
  {name:'guest-throttled',mode:'full',first:false,rate:4,software:true,service:'ready'},
  {name:'service-timeout-retry',mode:'off',first:false,rate:4,software:false,service:'pending'}
 ]){
  active={...scenario};
  report({stage:scenario.name+' create',observations});
  win=new BrowserWindow({show:false,width:1440,height:900,backgroundColor:'#11192b',webPreferences:{offscreen:true,backgroundThrottling:false,contextIsolation:true,sandbox:true}});
  win.webContents.on('console-message',(_event,level,message)=>{if(message.includes('Uncaught'))failures.push(message);});
  win.webContents.on('render-process-gone',(_event,details)=>failures.push('Renderer exited: '+JSON.stringify(details)));
  report({stage:scenario.name+' created',observations});
  report({stage:scenario.name+' preference navigation',observations});
  await win.loadURL(origin+'/fixture-prefs');
  // Chromium needs an initialized renderer before its Emulation command resolves.
  win.webContents.debugger.attach('1.3');
  report({stage:scenario.name+' CPU command',observations});
  await win.webContents.debugger.sendCommand('Emulation.setCPUThrottlingRate',{rate:scenario.rate});
  report({stage:scenario.name+' preferences',observations});
  await win.webContents.executeJavaScript('localStorage.setItem("bloondesk-save-v1",'+JSON.stringify(JSON.stringify({startupMode:scenario.mode,theme:'dark'}))+');localStorage.setItem("bloonsStartupSeen",'+JSON.stringify(scenario.first?'0':'1')+');');
  const started=Date.now();await win.loadURL(origin+(scenario.software?'/?softwareRendering=1':'/'));
  report({stage:scenario.name+' loaded',observations});
  const initial=await win.webContents.executeJavaScript('({navigation:!!document.querySelector(".rail"),main:!!document.querySelector("main"),branding:!document.getElementById("startup-branding").hidden,mode:document.getElementById("startup-branding").dataset.motion,theme:document.documentElement.dataset.theme})');
  check(initial.navigation&&initial.main,'Slow profile hid the shell: '+scenario.name);
  check(initial.theme==='dark','Theme preference lost: '+scenario.name);
  if(scenario.mode==='off')check(!initial.branding,'Off imposed a branding delay');
  if(scenario.software)check(initial.mode==='reduced','Software-rendered guest retained full motion');
  const shellMs=Date.now()-started;
  report({stage:scenario.name+' settle',observations});
  const settled=await win.webContents.executeJavaScript('new Promise((resolve,reject)=>{const started=performance.now();function check(){const brand=document.getElementById("startup-branding"),status=document.getElementById("startup-service-status");if(brand.hidden&&(status.hidden||status.dataset.state==="failed"))return resolve({elapsedMs:performance.now()-started,brandingHidden:brand.hidden,readiness:status.hidden?"ready":status.dataset.state,retryVisible:!document.getElementById("startup-retry").hidden});if(performance.now()-started>11000)return reject(Error("Startup remained unresolved"));setTimeout(check,25)}check()})');
  if(scenario.service==='ready')check(settled.readiness==='ready','Slow profile prevented local readiness');
  else{
   check(settled.readiness==='failed'&&settled.retryVisible,'Timed-out controller left a spinner');
   active.service='ready';await win.webContents.executeJavaScript('document.getElementById("startup-retry").click()');
   const recovered=await win.webContents.executeJavaScript('new Promise((resolve,reject)=>{const started=performance.now();function check(){if(document.getElementById("startup-service-status").hidden)return resolve(true);if(performance.now()-started>2500)return reject(Error("Explicit retry did not recover"));setTimeout(check,25)}check()})');
   check(recovered,'Explicit readiness retry failed');
  }
  const frameTiming=await win.webContents.executeJavaScript('new Promise(resolve=>{const samples=[];let previous,done=false;const end=setTimeout(()=>{done=true;resolve({frames:samples.length,available:false})},2000);function tick(now){if(done)return;if(previous!==undefined)samples.push(now-previous);previous=now;if(samples.length<60)return requestAnimationFrame(tick);done=true;clearTimeout(end);samples.sort((a,b)=>a-b);resolve({frames:samples.length,available:true,medianMs:samples[30],maxMs:samples[samples.length-1]})}requestAnimationFrame(tick)})');
  check(active.profileRequests>0,'Slow profile fixture was never requested');
  observations.push({name:scenario.name,cpuThrottle:scenario.rate,shellMs,profileRequests:active.profileRequests,...settled,frameTiming});
  report({stage:scenario.name+' finished',observations});
  win.destroy();win=null;
 }
 check(failures.length===0,'Renderer or mutation failures: '+JSON.stringify(failures));
 report({passed:true,observations,scope:'Isolated actual renderer, simulated slow APIs and 4x renderer CPU throttle; not physical weak-hardware or clean-launch acceptance.'});
 server.closeAllConnections();server.close(()=>app.exit(0));
})().catch(error=>{report({error:error.stack,failures});if(win&&!win.isDestroyed())win.destroy();server.closeAllConnections();app.exit(1);});
`);
try {
  const environment = {...process.env}; delete environment.ELECTRON_RUN_AS_NODE;
  const result = spawnSync(require('electron'), [main], {env:environment, windowsHide:true, timeout:40000, encoding:'utf8'});
  const report = fs.existsSync(reportPath) ? JSON.parse(fs.readFileSync(reportPath, 'utf8')) : {};
  assert.equal(result.status, 0, report.error ? JSON.stringify({error:report.error,failures:report.failures,stderr:result.stderr}) : ('stage='+report.stage+' '+(result.error?.message || result.stderr)));
  assert.equal(report.passed, true, report.error);
  assert.equal(report.observations.length, 4);
  console.log('Actual startup renderer passed:', JSON.stringify(report));
} finally {
  // This fixture owns only its fresh temporary directory.
  const resolved = fs.realpathSync(folder);
  assert.equal(path.dirname(resolved), fs.realpathSync(os.tmpdir()));
  assert.ok(path.basename(resolved).startsWith('bloons-startup-renderer-'));
  fs.rmSync(resolved, {recursive:true, force:true});
}
