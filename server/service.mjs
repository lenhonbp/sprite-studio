import {projectReport} from '../web/project-report.mjs';
import {validateProject,applyOperation,upsertKey,samplePose,coverageReport,solveIK} from '../web/rig-core.mjs';
export const UI_URI='ui://nhon-le/studio-v4.html';
const LIMIT=4_000_000,HISTORY=8_000_000;
const fail=(message,status=400)=>Object.assign(Error(message),{status});
const schema=properties=>({type:'object',properties,additionalProperties:false});
const base={baseRevision:{type:'integer',minimum:0},requestId:{type:'string',minLength:8,maxLength:100}};
export const toolsList=[
 {name:'studio_check',description:'Read-only technical preflight at fps (default 24): source size, missing action/direction pairs, export budget and bounded pose sampling. Does not approve visual art or game runtime.',inputSchema:schema({fps:{type:'number',minimum:1,maximum:120}}),annotations:{readOnlyHint:true}},
 {name:'studio_poll',description:'App-only lightweight polling; return unchanged when knownVersion matches the shared state.',inputSchema:schema({knownVersion:{type:'integer',minimum:-1}}),annotations:{readOnlyHint:true},_meta:{ui:{visibility:['app']}}},
 {name:'studio_open',description:'Open Nhon Le Sprite Studio in chat. Read the current shared rig, selection and revision. No data mutation.',inputSchema:schema({}),annotations:{readOnlyHint:true},_meta:{ui:{resourceUri:UI_URI},'openai/outputTemplate':UI_URI}},
 {name:'studio_read',description:'Read shared rig without raster bytes: all bones, slots, clips/keys, sockets, skins, selected clip/bone/time, revision, history and coverage. Read before editing.',inputSchema:schema({}),annotations:{readOnlyHint:true}},
 {name:'studio_edit',description:'Atomically apply 1–50 rig authoring operations, using baseRevision from studio_read and a unique requestId. Supports core applyOperation types (ik, slot-key, event, socket, retime, clips/bones/slots/skins/project), production (fx-put/fx-delete/fx-binding/fx-unbind/asset-put/asset-info/scene), plus {type:"bone-key",clip,bone,time,values}. Entire batch rolls back on error. Conflict requires fresh read; never silently overwrite.',inputSchema:{...schema({...base,operations:{type:'array',minItems:1,maxItems:50,items:{type:'object',additionalProperties:true}}}),required:['baseRevision','requestId','operations']},annotations:{readOnlyHint:false,destructiveHint:false,idempotentHint:true}},
 {name:'studio_view',description:'Select shared clipId, boneId, slotId, effectId, time (ms), playing or tool (move/rotate/ik/pan); the editor follows. Does not modify the rig or undo history.',inputSchema:{...schema({requestId:base.requestId,view:{type:'object',properties:{clipId:{type:'string'},boneId:{type:'string'},slotId:{type:['string','null']},effectId:{type:['string','null']},time:{type:'number',minimum:0},playing:{type:'boolean'},tool:{enum:['move','rotate','ik','pan']}},additionalProperties:false}}),required:['requestId','view']},annotations:{readOnlyHint:false,destructiveHint:false,idempotentHint:true}},
 ...['undo','redo'].map(action=>({name:'studio_'+action,description:'Shared '+action+' for the latest rig edit, whether from chat or manual editor. Requires current baseRevision and unique requestId.',inputSchema:{...schema(base),required:['baseRevision','requestId']},annotations:{readOnlyHint:false,destructiveHint:false,idempotentHint:true}})),
 {name:'studio_replace',description:'Replace the shared rig with a validated full project. Used by the editor for manual changes/import. Preserves shared undo. Online project limit 4 MB; full raster bytes should not be invented.',inputSchema:{...schema({...base,project:{type:'object',additionalProperties:true}}),required:['baseRevision','requestId','project']},annotations:{readOnlyHint:false,destructiveHint:false,idempotentHint:true},_meta:{ui:{visibility:['app']}}}
];
function checked(p){validateProject(p);if(new TextEncoder().encode(JSON.stringify(p)).length>LIMIT)throw fail('Project trực tuyến tối đa 4 MB; dùng bản offline/CLI cho nguồn lớn.',413);return p;}
function normalizeView(p,v={}){const c=p.clips.find(c=>c.id===v.clipId)??p.clips[0];return {clipId:c.id,boneId:p.bones.some(b=>b.id===v.boneId)?v.boneId:p.bones[0].id,effectId:p.studio?.effects.some(f=>f.id===v.effectId)?v.effectId:null,slotId:p.slots.some(s=>s.id===v.slotId)?v.slotId:p.slots[0]?.id??null,time:Math.max(0,Math.min(Number(v.time)||0,c.duration_ms)),playing:!!v.playing,tool:['move','rotate','ik','pan'].includes(v.tool)?v.tool:'move'};}
function patchView(p,old,patch){if(!patch||typeof patch!=='object'||Array.isArray(patch))throw fail('view phải là object');for(const [k,v]of Object.entries(patch)){if(!['clipId','boneId','slotId','effectId','time','playing','tool'].includes(k))throw fail('Trường view không hợp lệ');if(k==='clipId'&&!p.clips.some(c=>c.id===v)||k==='boneId'&&!p.bones.some(b=>b.id===v)||k==='slotId'&&v!==null&&!p.slots.some(s=>s.id===v)||k==='effectId'&&v!==null&&!p.studio?.effects.some(f=>f.id===v)||k==='time'&&(!Number.isFinite(v)||v<0)||k==='playing'&&typeof v!=='boolean'||k==='tool'&&!['move','rotate','ik','pan'].includes(v))throw fail('Giá trị view không hợp lệ: '+k);}return normalizeView(p,{...old,...patch});}
function trim(r){while(r.past.length+r.future.length>20||new TextEncoder().encode(JSON.stringify([r.past,r.future])).length>HISTORY){if(r.past.length)r.past.shift();else if(r.future.length)r.future.shift();else break;}}
export function summary(r){const p=r.project;return {version:'4.1.1',revision:r.projectRevision,stateVersion:r.version,view:r.view,undo:r.past.length,redo:r.future.length,updatedAt:r.updatedAt,lastAction:r.lastAction,operationReport:r.operationReport??[],project:{...p,attachments:Object.fromEntries(Object.entries(p.attachments).map(([id,a])=>[id,{...a,image:undefined}]))},coverage:coverageReport(p),pose:samplePose(p,r.view.clipId,r.view.time)};}
export function toolResult(r){if(r.unchanged)return {content:[],structuredContent:{unchanged:true}};if(r.check)return {content:[{type:'text',text:JSON.stringify(r.check)}],structuredContent:r.check};return {content:[{type:'text',text:JSON.stringify(summary(r))}],structuredContent:summary(r),_meta:{studio:{version:r.version,projectRevision:r.projectRevision,ackRevision:r.ackRevision??r.projectRevision,project:r.project,view:r.view,undo:r.past.length,redo:r.future.length}}};}
export async function handleTool(name,args={},identity,bucket,demo){
 if(!identity)throw fail('Đăng nhập ChatGPT để đồng bộ project.',401);
 if(!bucket)throw fail('Kho project chưa được kết nối.',503);
 if(!toolsList.some(t=>t.name===name))throw fail('Unknown tool');
 const key='studio/users/'+encodeURIComponent(identity)+'/active.json';
 const defaultRecord=()=>({version:0,projectRevision:0,project:structuredClone(demo),view:normalizeView(demo),past:[],future:[],requests:[],updatedAt:null,lastAction:'demo'});
 const read=async()=>{const o=await bucket.get(key);return {r:o?await o.json():defaultRecord(),etag:o?.etag};};
 if(name==='studio_poll'&&typeof bucket.head==='function'){const h=await bucket.head(key);if(Number(h?.customMetadata?.version??0)===args.knownVersion)return {unchanged:true};}
 if(name==='studio_check')return {check:projectReport((await read()).r.project,args.fps??24)};
 if(['studio_open','studio_read','studio_poll'].includes(name)){return (await read()).r;}
 if(typeof args.requestId!=='string'||args.requestId.length<8||args.requestId.length>100)throw fail('requestId từ 8 đến 100 ký tự');
 const fingerprint=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify({name,args}))))).map(x=>x.toString(16).padStart(2,'0')).join('');
 for(let attempt=0;attempt<4;attempt++){
  const {r,etag}=await read(),previous=r.requests.find(x=>x.id===args.requestId);
  if(previous){if(previous.hash!==fingerprint)throw fail('requestId đã dùng cho một lệnh khác',409);return {...r,ackRevision:previous.revision??r.projectRevision};}
  if(name!=='studio_view'&&(!Number.isInteger(args.baseRevision)||args.baseRevision!==r.projectRevision))throw fail('Project đã thay đổi. Lưu JSON bản đang chỉnh rồi tải bản chung; agent cần studio_read trước khi thử lại.',409);
  if(name==='studio_view')r.view=patchView(r.project,r.view,args.view);
  else{
   const old=r.project;r.operationReport=[];
   if(name==='studio_undo'||name==='studio_redo'){const from=name==='studio_undo'?r.past:r.future,to=name==='studio_undo'?r.future:r.past;if(!from.length)throw fail('Không có bước '+name.slice(7));to.push(old);r.project=from.pop();}
   else{
    let p=old;
    if(name==='studio_replace')p=checked(args.project);
    else if(name==='studio_edit'){
     if(!Array.isArray(args.operations)||args.operations.length<1||args.operations.length>50)throw fail('1–50 operations');
     r.operationReport=[];p=structuredClone(old);for(const op of args.operations){if(op.type==='bone-key'){upsertKey(p,op.clip,op.bone,op.time,op.values);validateProject(p);}else if(op.type==='ik'){const solved=solveIK(p,op.clip,op.bone,op.time,op.target,op.depth??2,op.rest??false);p=solved.project;r.operationReport.push({type:'ik',bone:op.bone,target:op.target,error_px:solved.error_px,reached:solved.reached,iterations:solved.iterations});}else p=applyOperation(p,op);}checked(p);
    }
    r.past.push(old);r.future=[];r.project=p;
   }
   r.projectRevision++;r.view=normalizeView(r.project,{...r.view,playing:false});trim(r);
  }
  r.version++;r.updatedAt=new Date().toISOString();r.lastAction=name;r.requests.push({id:args.requestId,hash:fingerprint,revision:r.projectRevision});r.requests=r.requests.slice(-32);
  const result=await bucket.put(key,JSON.stringify(r),{onlyIf:etag?{etagMatches:etag}:new Headers({'If-None-Match':'*'}),httpMetadata:{contentType:'application/json'},customMetadata:{version:String(r.version)}});
  if(result)return {...r,ackRevision:r.projectRevision};
 }
 throw fail('Có thao tác đồng thời; vui lòng thử lại.',409);
}
async function boundedBody(request){if(Number(request.headers.get('content-length'))>5_000_000)throw fail('Request quá lớn',413);if(!request.body)return '';const reader=request.body.getReader(),decoder=new TextDecoder(),parts=[];let bytes=0;try{while(true){const {value,done}=await reader.read();if(done)break;bytes+=value.byteLength;if(bytes>5_000_000){await reader.cancel();throw fail('Request quá lớn',413);}parts.push(decoder.decode(value,{stream:true}));}parts.push(decoder.decode());return parts.join('');}finally{reader.releaseLock();}}
export function createWorker(assets,widget,demo){return {async fetch(request,env){const url=new URL(request.url),path=url.pathname;const json=(body,status=200)=>new Response(JSON.stringify(body),{status,headers:{'content-type':'application/json','cache-control':'no-store'}});try{
 if(path==='/health')return json({ok:true,version:'4.1.1',storage:!!env.BUCKET});
 if(path==='/api/studio'){
  if(request.method!=='POST')return json({error:'POST required'},405);
  if(request.headers.get('origin')&&request.headers.get('origin')!==url.origin)return json({error:'Origin rejected'},403);
  if(Number(request.headers.get('content-length'))>5_000_000)throw fail('Request quá lớn',413);
  const text=await boundedBody(request);if(text.length>5_000_000)throw fail('Request quá lớn',413);const {name,args}=JSON.parse(text);
  const r=await handleTool(name,args,request.headers.get('oai-authenticated-user-id'),env.BUCKET,demo);return json(toolResult(r));
 }
 if(path==='/mcp'){
  if(request.method==='GET')return new Response(null,{status:405,headers:{Allow:'POST'}});
  if(request.method!=='POST')return new Response(null,{status:405});
  const body=await boundedBody(request);if(body.length>5_000_000)throw fail('Request quá lớn',413);let q;try{q=JSON.parse(body);}catch{return json({jsonrpc:'2.0',id:null,error:{code:-32700,message:'Parse error'}});}
  if(!q||q.jsonrpc!=='2.0'||typeof q.method!=='string')return json({jsonrpc:'2.0',id:q?.id??null,error:{code:-32600,message:'Invalid request'}});
  if(q.id===undefined)return new Response(null,{status:202});
  let result;
  if(q.method==='server/discover')result={supportedVersions:['2026-07-28'],capabilities:{tools:{},resources:{}}};
  else if(q.method==='initialize')result={protocolVersion:q.params?.protocolVersion??'2025-06-18',capabilities:{tools:{},resources:{}},serverInfo:{name:'Nhon Le Sprite Studio',version:'4.1.1'}};
  else if(q.method==='ping')result={};
  else if(q.method==='tools/list')result={tools:toolsList};
  else if(q.method==='resources/list')result={resources:[{uri:UI_URI,name:'Sprite Studio',mimeType:'text/html;profile=mcp-app'}]};
  else if(q.method==='resources/read'){if(q.params?.uri!==UI_URI)throw fail('Resource not found');result={contents:[{uri:UI_URI,mimeType:'text/html;profile=mcp-app',text:widget,_meta:{ui:{csp:{connectDomains:[],resourceDomains:[]}},'openai/widgetDescription':'Interactive sprite rig editor with shared chat editing and undo.'}}]};}
  else if(q.method==='tools/call'){try{result=toolResult(await handleTool(q.params?.name,q.params?.arguments,request.headers.get('oai-authenticated-user-id'),env.BUCKET,demo));}catch(e){result={isError:true,content:[{type:'text',text:e.message}],structuredContent:{error:e.message,status:e.status??400}};}}
  else return json({jsonrpc:'2.0',id:q.id,error:{code:-32601,message:'Method not found'}});
  return json({jsonrpc:'2.0',id:q.id,result});
 }
 if(request.method!=='GET'&&request.method!=='HEAD')return new Response('Method not allowed',{status:405});
 const a=assets[path==='/'?'/index.html':path];if(!a)return new Response('Not found',{status:404});return new Response(request.method==='HEAD'?null:a.text,{headers:{'content-type':a.type,'cache-control':'no-cache','x-content-type-options':'nosniff'}});
 }catch(e){return json({error:e.message},e.status??400);}}};}
