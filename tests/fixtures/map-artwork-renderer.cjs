const {app,BrowserWindow,session}=require('electron');
const fs=require('node:fs'),http=require('node:http'),path=require('node:path');
const root=path.resolve(__dirname,'../..');
const folder=process.env.BLOONS_RENDERER_TEST_PROFILE;
if(!folder)throw new Error('Run through test-map-artwork-renderer.js to isolate and clean up the profile');
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
  else if(route==='/api/progress')body={source:'live-scan',maps:{'Monkey Meadow':{medals:Object.fromEntries(['easy','primary_only','deflation','medium','military_only','reverse','apopalypse','hard','magic_monkeys_only','double_hp_moabs','half_cash','alternate_bloons_rounds','impoppable','chimps'].map(mode=>[mode,true]))}},towers:{},achievements:{}};
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
 await app.whenReady();await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const origin='http://127.0.0.1:'+server.address().port;
 session.defaultSession.webRequest.onBeforeRequest((d,cb)=>cb({cancel:!d.url.startsWith(origin+'/')&&!d.url.startsWith('data:')}));
 win=new BrowserWindow({show:false,width:1440,height:900,webPreferences:{offscreen:true,backgroundThrottling:false,contextIsolation:true,sandbox:true}});
 win.webContents.setWindowOpenHandler(()=>{errors.push('Unexpected external window');return {action:'deny'}});
 win.webContents.on('render-process-gone',(_e,d)=>errors.push('Renderer exit '+d.reason));
 const evaluate=async expression=>{
  const result=await win.webContents.executeJavaScript(`(()=>{try{return eval(${JSON.stringify(expression)})}catch(error){return {fixtureError:error.stack}}})()`);
  if(result?.fixtureError)throw new Error(result.fixtureError);
  return result;
 };
 const check=(condition,kind,context={})=>{results.push({kind,ok:!!condition,...context});if(!condition)failures.push({kind,...context})};
 for(const fallback of [false,true])for(const theme of ['light','dark']){
  const context={fallback,theme};stage=JSON.stringify(context);
  await win.loadURL(origin+'/fixture-prefs');
  await evaluate(`localStorage.setItem('bloondesk-save-v1',JSON.stringify({startupMode:'off',theme:${JSON.stringify(theme)}}));localStorage.setItem('bloonsStartupSeen','1');localStorage.setItem('bloonsSetupPrepageSeen','1');localStorage.removeItem('bloonsplus-last-view')`);
  await win.loadURL(origin+'/');await delay(1000);
  await evaluate(`(()=>{
   window.artworkObservers=[];
   if(${fallback})window.IntersectionObserver=undefined;
   else {
    const Native=window.IntersectionObserver;
    window.IntersectionObserver=class {
     constructor(callback,options){this.disconnected=false;this.targets=new Set();this.native=new Native(callback,options);window.artworkObservers.push(this)}
     observe(target){this.targets.add(target);this.native.observe(target)}
     unobserve(target){this.targets.delete(target);this.native.unobserve(target)}
     disconnect(){this.disconnected=true;this.targets.clear();this.native.disconnect()}
    };
   }
   detectedProgress={maps:{[mapChoices[0].name]:{medals:Object.fromEntries(MEDAL_SLOTS.map(([mode])=>[mode,true]))}}};
   document.querySelector('.nav-item[data-view="blackborder"]').click();
  })()`);
  await delay(300);
  const initial=await evaluate(`(()=>{
   const main=document.querySelector('main');window.artworkLabelSnapshot=[...document.querySelectorAll('#maps-grid .medal')].map(e=>[e.className,e.title]);
   window.artworkFirstCard=document.querySelector('#maps-grid .map-card');
   window.artworkScrollTarget=main.scrollHeight>main.clientHeight?main:document.scrollingElement;
   const cards=[...document.querySelectorAll('#maps-grid .map-card')],medals=cards.flatMap(c=>[...c.querySelectorAll('.medal')]);
   const visible=medals.filter(e=>{const r=e.getBoundingClientRect();return r.top<innerHeight&&r.bottom>0});
   return {cards:cards.length,expected:mapChoices.length,medals:medals.length,svg:medals.filter(e=>e.querySelector('svg')).length,visible:visible.length,visibleArt:visible.filter(e=>e.querySelector('svg')).length,height:artworkScrollTarget.scrollHeight,legend:document.querySelectorAll('#medal-legend .medal svg').length,labels:medals.every(e=>!!e.title),done:cards[0].classList.contains('done')};
  })()`);
  check(initial.cards===initial.expected&&initial.medals===initial.expected*14,'all-map-and-medal-slots',{...context,initial});
  check(initial.labels&&initial.done&&initial.legend===14,'labels-earned-state-and-eager-legend',context);
  check(initial.visible>0&&initial.visibleArt===initial.visible,'visible-artwork-ready',{...context,initial});
  check(fallback?initial.svg===initial.medals:initial.svg<initial.medals,'lazy-artwork-or-eager-fallback',{...context,initial});
  await evaluate('artworkScrollTarget.scrollTop=artworkScrollTarget.scrollHeight;void 0');await delay(300);
  const bottom=await evaluate(`(()=>{const last=document.querySelector('#maps-grid').lastElementChild;const r=last.getBoundingClientRect();return {art:last.querySelectorAll('.medal svg').length,visible:r.top<innerHeight&&r.bottom>0,height:artworkScrollTarget.scrollHeight,labels:JSON.stringify([...document.querySelectorAll('#maps-grid .medal')].map(e=>[e.className,e.title]))===JSON.stringify(artworkLabelSnapshot)}})()`);
  check(bottom.visible&&bottom.art===14,'scroll-loads-last-card',{...context,bottom});
  check(bottom.height===initial.height&&bottom.labels,'scroll-preserves-height-and-labels',{...context,bottom});
  await evaluate(`(()=>{detectedProgress.maps[mapChoices[0].name].updatedAt=new Date().toISOString();renderMaps()})()`);
  check(await evaluate('document.querySelector("#maps-grid .map-card")===artworkFirstCard'),'unchanged-content-retains-nodes',context);
  await evaluate(`(()=>{const s=document.querySelector('#maps-search');s.value=mapChoices[1].name;s.dispatchEvent(new Event('input',{bubbles:true}));artworkScrollTarget.scrollTop=0})()`);await delay(200);
  check(await evaluate('document.querySelectorAll("#maps-grid .map-card").length===1&&document.querySelector("#maps-grid b").textContent===mapChoices[1].name&&document.querySelectorAll("#maps-grid .medal svg").length===14'),'search-keeps-complete-visible-row',context);
  check(fallback||await evaluate('artworkObservers.length>=2&&artworkObservers.slice(0,-1).every(o=>o.disconnected&&o.targets.size===0)'),'rerender-disconnects-old-observers',context);
  await evaluate(`(()=>{detectedProgress.maps[mapChoices[1].name]={medals:{easy:true}};renderMaps()})()`);await delay(200);
  check(await evaluate('document.querySelector("#maps-grid .mode-easy").title==="Easy: earned"&&document.querySelector("#maps-grid .mode-hard").title==="Hard: not scanned"'),'save-refresh-updates-labels',context);
  await evaluate(`(()=>{const s=document.querySelector('#maps-search');s.value='';s.dispatchEvent(new Event('input',{bubbles:true}));const h=document.querySelector('#maps-hide-done');h.checked=true;h.dispatchEvent(new Event('change',{bubbles:true}))})()`);await delay(200);
  check(await evaluate('document.querySelectorAll("#maps-grid .map-card").length===mapChoices.length-1&&![...document.querySelectorAll("#maps-grid b")].some(e=>e.textContent===mapChoices[0].name)'),'hide-complete-keeps-all-other-maps',context);
  await evaluate(`(()=>{const s=document.querySelector('#maps-search');s.value='fixture-no-map-123';s.dispatchEvent(new Event('input',{bubbles:true}))})()`);await delay(100);
  check(await evaluate('document.querySelector("#maps-grid").textContent==="No maps match."&&document.querySelectorAll("#maps-grid .medal").length===0'),'empty-filter',context);
 }
 console.log(JSON.stringify({checks:results.length,failures,errors,scope:'Hidden actual app renderer, synthetic saves; scrolling, filters, labels, theme, observer lifecycle and eager fallback'}));
 win.destroy();server.closeAllConnections();server.close(()=>app.exit(failures.length||errors.length?1:0));
})().catch(error=>{console.error(stage,error.stack);if(win&&!win.isDestroyed())win.destroy();server.closeAllConnections();app.exit(1)});
