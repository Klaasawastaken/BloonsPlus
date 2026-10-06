(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  else {root.BloonsStartup=api;api.prepareTheme();document.addEventListener('DOMContentLoaded',()=>api.mount());}
})(typeof globalThis==='object'?globalThis:this,function(){
  const key='bloondesk-save-v1';
  function preferences(){try{return JSON.parse(localStorage.getItem(key)||'{}');}catch{return {};}}
  function prepareTheme(){const saved=preferences();document.documentElement.dataset.theme=saved.theme==='dark'?'dark':'light';}
  function startIntro(options={},dependencies={}) {
    const schedule=dependencies.setTimeout||setTimeout, cancel=dependencies.clearTimeout||clearTimeout;
    const onChange=dependencies.onChange||(()=>{}), timers=new Set();
    const configured=['full','reduced','off'].includes(options.mode)?options.mode:'full';
    const mode=configured==='off'?'off':options.reducedMotion||options.softwareRendering?'reduced':configured;
    let disposed=false, sequence=0, serviceTimer=null, brandTimer=null;
    const state={mode,branding:mode!=='off',readiness:'loading',shellReady:false,serviceReady:false,error:''};
    function publish(){if(!disposed)onChange({...state});}
    function later(fn,ms){let id;id=schedule(()=>{timers.delete(id);cancel(id);fn();},ms);timers.add(id);return id;}
    function clear(id){if(id!==null){cancel(id);timers.delete(id);}}
    function ready(){if(state.readiness!=='failed')state.readiness=state.shellReady&&state.serviceReady?'ready':'loading';if(state.readiness==='ready'){clear(serviceTimer);serviceTimer=null;}publish();}
    function dismiss(){clear(brandTimer);brandTimer=null;state.branding=false;publish();}
    function probe() {
      const current=++sequence;clear(serviceTimer);state.error='';state.shellReady=false;state.serviceReady=false;state.readiness='loading';publish();
      // A readiness callback starts immediately; branding never gates the shell.
      try {
        const shell=typeof options.shellReady==='function'?options.shellReady():options.shellReady;
        Promise.resolve(shell).then(value=>{
          if(disposed||current!==sequence)return;state.shellReady=value===true;
          if(!state.shellReady)throw new Error('The app shell is not ready.');ready();
        }).catch(error=>{if(!disposed&&current===sequence){state.readiness='failed';state.error=error.message;publish();}});
      }catch(error){state.readiness='failed';state.error=error.message;publish();}
      serviceTimer=later(()=>{if(current!==sequence||disposed)return;sequence++;state.readiness='failed';state.error=state.serviceReady?'The app shell did not become ready. Reload the app.':'The local controller did not respond. Retry when it is available.';publish();},8000);
      Promise.resolve().then(()=>typeof options.serviceReady==='function'?options.serviceReady():options.serviceReady).then(value=>{
        if(disposed||current!==sequence)return;
        if(value!==true)throw new Error('The local controller is not ready.');
        state.serviceReady=true;ready();
      }).catch(error=>{
        if(disposed||current!==sequence)return;
        clear(serviceTimer);serviceTimer=null;state.readiness='failed';state.error=error.message||'The local controller is unavailable.';publish();
      });
    }
    publish();
    if(state.branding)brandTimer=later(dismiss,options.firstLaunch?2400:mode==='reduced'?1000:1600);
    probe();
    return {dismiss,retry:probe,cleanup(){disposed=true;sequence++;for(const timer of timers)cancel(timer);timers.clear();}};
  }
  function mount() {
    const branding=document.getElementById('startup-branding'),status=document.getElementById('startup-service-status');
    if(!branding||!status)return;
    const saved=preferences(),selection=document.getElementById('startup-mode');
    if(selection)selection.value=['full','reduced','off'].includes(saved.startupMode)?saved.startupMode:'full';
    let firstLaunch=true;try{firstLaunch=localStorage.getItem('bloonsStartupSeen')!=='1';}catch{}
    const intro=startIntro({mode:saved.startupMode,firstLaunch,reducedMotion:matchMedia('(prefers-reduced-motion: reduce)').matches,
      softwareRendering:new URL(location.href).searchParams.get('softwareRendering')==='1',
      shellReady:()=>!!document.querySelector('main'),
      serviceReady:async()=>{const response=await fetch('/api/setup/controller',{cache:'no-store',signal:AbortSignal.timeout(8000)});if(!response.ok)throw new Error('The local controller is unavailable.');return (await response.json()).protocolVersion===1;}
    },{onChange:value=>{
      branding.hidden=!value.branding;branding.dataset.motion=value.mode;
      status.hidden=value.readiness==='ready';status.dataset.state=value.readiness;
      document.getElementById('startup-service-message').textContent=value.readiness==='failed'?'Local controller needs attention. Your navigation remains available.':'Connecting to the local controller…';
      document.getElementById('startup-retry').hidden=value.readiness!=='failed';
      document.getElementById('startup-service-details').textContent=rootRedact(value.error);
      if(!value.branding)try{localStorage.setItem('bloonsStartupSeen','1');}catch{}
    }});
    const escape=event=>{if(event.key==='Escape')intro.dismiss();};
    document.addEventListener('keydown',escape);
    document.getElementById('startup-retry').addEventListener('click',intro.retry);
    window.addEventListener('pagehide',()=>{intro.cleanup();document.removeEventListener('keydown',escape);},{once:true});
    function rootRedact(text){return globalThis.BloonsSupport?.redact(text)||text.replace(/(?:[a-z]:\\Users\\|\/home\/)[^\n]+/gi,'[user path removed]');}
  }
  return {startIntro,prepareTheme,mount};
});
