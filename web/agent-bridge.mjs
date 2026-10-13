export async function connectStudio(api){
 const status=document.getElementById('agentStatus'),reload=document.getElementById('agentReload'),publish=document.getElementById('agentPublish'),retry=document.getElementById('agentRetry'),pause=document.getElementById('agentPause');
 const embedded=!!window.STUDIO_EMBEDDED,online=embedded||(typeof location!=='undefined'&&/^https?:$/.test(location.protocol));
 if(!online){status.textContent='Offline · thư viện và JSON trên thiết bị';return;}
 retry.hidden=false;pause.hidden=false;
 let rev=0,version=-1,dirty=false,busy=false,applying=false,conflict=false,lastView='',timer,pendingWrite=null,connected=false,initial=true,active=true,bridgeReady=!embedded;
 const pending=new Map();let serial=0;
 const rpc=(method,params)=>new Promise((resolve,reject)=>{const id=++serial,timeout=setTimeout(()=>{pending.delete(id);reject(Error('Agent chưa phản hồi; thử kết nối lại hoặc lưu JSON.'));},20000);pending.set(id,{resolve,reject,timeout});window.parent.postMessage({jsonrpc:'2.0',id,method,params},'*');});
 const notify=(method,params)=>window.parent.postMessage({jsonrpc:'2.0',method,params},'*');
 const context=()=>{if(embedded&&bridgeReady)rpc('ui/update-model-context',{structuredContent:{studioRevision:rev,selection:api.state,unsynced:dirty,conflict,paused:!active}}).catch(()=>{});};
 const requestId=()=>crypto.randomUUID();
 const call=async(name,args={})=>{let result;if(embedded){result=await rpc('tools/call',{name,arguments:args});}else{const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),20000);try{const send=()=>fetch('/api/studio',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({name,args}),signal:controller.signal});let response=await send();if(response.status===401&&window.STUDIO_LOCAL){await response.arrayBuffer();const session=await fetch('/health',{cache:'no-store',signal:controller.signal});if(!session.ok)throw Error('Không thể nối lại phiên local; thử lại khi server hoạt động.');await session.arrayBuffer();response=await send();}result=await response.json();document.getElementById('agentSignin').hidden=!!window.STUDIO_LOCAL||response.status!==401;if(!response.ok)throw Object.assign(Error(result.error??'Không thể đồng bộ'),{status:response.status});}finally{clearTimeout(timeout);}}if(result.isError)throw Object.assign(Error(result.content?.[0]?.text??'Lệnh thất bại'),{status:result.structuredContent?.status});return result;};
 function label(message){status.textContent=message;reload.hidden=!conflict;publish.hidden=!conflict;pause.textContent=active?'Tạm dừng đồng bộ':'Tiếp tục đồng bộ';}
 const apply=async(result,force=false)=>{
  const s=result?._meta?.studio;if(!s||s.version<version)return;
  if(!force&&(!active||dirty||api.busy)){if(active&&s.projectRevision!==rev){conflict=true;label('Có bản mới · lưu JSON rồi chọn cách tiếp tục');context();}return;}
  applying=true;document.getElementById('editorWorkspace').inert=true;document.getElementById('editorHeader').inert=true;
  try{if(s.projectRevision!==rev||initial)await api.load(s.project,false);api.select(s.view);rev=s.projectRevision;version=s.version;initial=false;dirty=false;pendingWrite=null;conflict=false;lastView=JSON.stringify(api.state);connected=true;document.getElementById('undo').disabled=!s.undo;document.getElementById('redo').disabled=!s.redo;label('Đã đồng bộ · phiên bản '+rev);context();}finally{applying=false;document.getElementById('editorWorkspace').inert=false;document.getElementById('editorHeader').inert=false;}
 };
 const save=async()=>{
  if(!dirty||busy||conflict||!connected||!active)return;
  if(api.busy){timer=setTimeout(save,200);return;}
  busy=true;pendingWrite??={baseRevision:rev,requestId:requestId(),project:api.project};const sent=pendingWrite,generation=JSON.stringify(sent.project);
  try{const result=await call('studio_replace',sent),s=result._meta.studio;
   // A retry may acknowledge an older write while returning a newer shared rig.
   if(s.ackRevision!==undefined&&s.projectRevision!==s.ackRevision){rev=s.ackRevision;pendingWrite=null;conflict=true;dirty=true;label('Bản đã lưu có thay đổi mới · lưu JSON rồi chọn bản');context();return;}
   rev=s.projectRevision;version=s.version;pendingWrite=null;dirty=JSON.stringify(api.project)!==generation;if(!dirty){document.getElementById('undo').disabled=!s.undo;document.getElementById('redo').disabled=!s.redo;label('Đã đồng bộ · phiên bản '+rev);context();}else timer=setTimeout(save,200);
  }catch(e){if(e.status===409){conflict=true;label('Xung đột · lưu JSON rồi chọn bản chung');}else label('Chưa đồng bộ · '+e.message);context();}finally{busy=false;}
 };
 const reconnect=async()=>{
  if(busy||api.busy)return;busy=true;active=true;
  try{if(!bridgeReady){await rpc('ui/initialize',{appInfo:{name:'Nhon Le Sprite Studio',version:'3.3.1'},appCapabilities:{},protocolVersion:'2026-01-26'});bridgeReady=true;notify('ui/notifications/initialized',{});}
   label('Đang kết nối project chung…');const result=await call('studio_read'),s=result._meta.studio;connected=true;
   if((initial&&!embedded&&JSON.stringify(api.project)!==JSON.stringify(s.project))||(dirty&&s.projectRevision!==rev)){if(initial){rev=s.projectRevision;version=s.version;initial=false;}conflict=true;dirty=true;label('Bản thiết bị khác bản chung · lưu JSON rồi chọn bản');}
   else if(!dirty)await apply(result,true);
   else label('Đã kết nối · đang chờ lưu bản thiết bị');
  }catch(e){label('Chưa kết nối · '+e.message);}finally{busy=false;}if(dirty&&!conflict)await save();context();
 };
 window.studioSync={get applying(){return applying;},get connected(){return connected&&active;},get unsynced(){return dirty;},get paused(){return !active;},dirty(){if(applying)return;dirty=true;label(!active?'Đã tạm dừng · thay đổi lưu trên thiết bị':conflict?'Có hai bản khác nhau · lưu JSON rồi chọn bản':'Đang chờ đồng bộ…');clearTimeout(timer);timer=setTimeout(save,500);},async history(action){if(busy||api.busy||!active)return;if(dirty){await save();if(dirty)return;}busy=true;try{await apply(await call('studio_'+action,{baseRevision:rev,requestId:requestId()}),true);}catch(e){label(e.message);}finally{busy=false;}}};
 retry.onclick=reconnect;
 pause.onclick=async()=>{if(active){active=false;clearTimeout(timer);label('Đã tạm dừng · chỉ chỉnh và lưu trên thiết bị');context();}else await reconnect();};
 reload.onclick=async()=>{if(busy||api.busy||!confirm('Tải bản chung sẽ thay bản đang chỉnh. Bạn đã lưu JSON hoặc lưu vào thư viện chưa?'))return;busy=true;active=true;try{await apply(await call('studio_read'),true);}catch(e){label(e.message);}finally{busy=false;}};
 publish.onclick=async()=>{if(busy||api.busy||!confirm('Dùng toàn bộ bản đang chỉnh thay bản chung? Bản chung hiện tại vẫn nằm trong undo.'))return;busy=true;active=true;let ready=false;try{const result=await call('studio_read');rev=result._meta.studio.projectRevision;version=result._meta.studio.version;connected=true;conflict=false;dirty=true;pendingWrite=null;ready=true;}catch(e){label(e.message);}finally{busy=false;}if(ready)await save();};
 if(embedded)window.addEventListener('message',event=>{if(event.source!==window.parent||event.data?.jsonrpc!=='2.0')return;const m=event.data;if(pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);clearTimeout(p.timeout);m.error?p.reject(Error(m.error.message)):p.resolve(m.result);}else if(m.method==='ui/notifications/tool-result'&&!busy){apply(m.params).catch(e=>label(e.message));}});
 // Keep the retry UI available even if initialization/auth fails.
 await reconnect();
 setInterval(async()=>{if(!active||!connected||busy||applying||api.busy||document.hidden)return;if(dirty){await save();return;}busy=true;try{const view=JSON.stringify(api.state),r=await call('studio_poll',{knownVersion:version});if(r._meta?.studio?.version>version)await apply(r);else if(view!==lastView)await apply(await call('studio_view',{requestId:requestId(),view:api.state}));}catch(e){label('Kết nối gián đoạn · '+e.message);}finally{busy=false;}},2000);
}
