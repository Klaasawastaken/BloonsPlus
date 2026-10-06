const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const timers=[],windows=[];
class Window {
  constructor(options){this.options=options;this.events={};this.loads=[];this.destroyed=false;this.webContents={setWindowOpenHandler(){},on:(name,handler)=>this.events[name]=handler,getURL:()=>this.loads.at(-1)||''};windows.push(this);}
  isDestroyed(){return this.destroyed;}
  loadURL(url){this.loads.push(url);return url.startsWith('data:')?Promise.resolve():Promise.reject(new Error('offline'));}
  setAppDetails(){}
}
const app={disableHardwareAcceleration(){},commandLine:{appendSwitch(){}},on(){},whenReady:()=>({then(){}})};
const context={module:{exports:{}},__dirname:process.cwd(),process:{env:{},platform:'win32',on(){}},
  require:name=>name==='electron'?{app,BrowserWindow:Window,shell:{},nativeTheme:{shouldUseDarkColors:true}}:name==='./server.js'?{}:name==='node:fs'?{existsSync:()=>false,appendFileSync(){}}:require(name),
  setTimeout:fn=>timers.push(fn),encodeURIComponent,URL};
vm.runInNewContext(fs.readFileSync('electron-main.js','utf8')+'\nmodule.exports={createWindow,loadWithRetry};',context);
const flush=async()=>{for(let i=0;i<6;i++)await Promise.resolve();};
(async()=>{
  context.module.exports.createWindow();const win=windows[0];await flush();
  for(let i=0;i<20;i++){timers.shift()();await flush();}
  assert.ok(win.loads.at(-1).startsWith('data:'),'Persistent controller failure never showed recovery');
  assert.equal(timers.length,0,'Unlimited loader retries');
  let prevented=false;
  assert.equal(typeof win.events['will-navigate'],'function','Recovery link has no bounded retry handler');
  win.events['will-navigate']({preventDefault(){prevented=true;}},'http://127.0.0.1:4173/');await flush();
  assert.equal(prevented,true);assert.ok(timers.length>0,'Retry did not start a new bounded attempt');
  win.destroyed=true;const before=win.loads.length;timers.shift()();await flush();assert.equal(win.loads.length,before,'Closed window received delayed navigation');
  assert.equal(win.options.backgroundColor,'#11192b');
  console.log('Electron startup: stable theme, bounded initial/recovery retries and closed-window guard passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
