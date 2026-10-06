(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.BloonsSetupClient=api;})(globalThis,function(){
  function createClient(dependencies={}) {
    const request=dependencies.fetch||fetch;
    let snapshot=null,busy=false;
    async function call(route,body) {
      const response=await request(route,{cache:'no-store',credentials:'same-origin',signal:AbortSignal.timeout(15000),
        ...(body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{})});
      const value=await response.json().catch(()=>{throw new Error('The setup controller returned an invalid response. Reopen the app.');});
      if(!response.ok){const error=new Error(value.error||`Setup request failed (${response.status})`);error.status=response.status;throw error;}
      if(value.protocolVersion!==1||!/^[a-f0-9]{32}$/.test(value.sessionId)||!Number.isSafeInteger(value.sequence)||value.sequence<0||typeof value.phase!=='string')throw new Error('The setup snapshot protocol does not match this app. Update or repair BloonsPlus.');
      snapshot=value;return value;
    }
    async function exclusive(work){if(busy)throw new Error('A setup check or command is already active.');busy=true;try{return await work();}finally{busy=false;}}
    async function bootstrap(options){return call('/api/setup/session/bootstrap',{operation:options?.operation||'resume',options:options?{isoPath:options.isoPath||''}:undefined});}
    async function observe(){
      if(!snapshot)await bootstrap();
      try{return await call('/api/setup/session');}
      catch(error){if(error.status!==403)throw error;await bootstrap();return call('/api/setup/session');}
    }
    async function command(action){
      for(let attempt=0;attempt<3;attempt++){
        await observe();
        try{return await call('/api/setup/session/command',{sessionId:snapshot.sessionId,sequence:snapshot.sequence,action});}
        catch(error){if(error.status!==409||attempt===2)throw error;}
      }
    }
    return {
      get connected(){return snapshot!==null;},snapshot:()=>snapshot?structuredClone(snapshot):null,
      observe:()=>exclusive(observe),command:action=>exclusive(()=>command(action)),
      begin:options=>exclusive(async()=>{await bootstrap(options);const current=await observe();if(current.phase==='complete'||current.operationOutstanding||current.queued||current.phase==='restart_required')return current;return command(current.phase==='idle'?'start':'resume');})
    };
  }
  return {createClient};
});
