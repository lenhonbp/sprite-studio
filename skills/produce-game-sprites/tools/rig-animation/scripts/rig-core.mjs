import {validateStudio,applyStudioOp,studioUsesAsset} from './studio-core.mjs';
// Shared deterministic core: browser editor and agent CLI use these same functions.
export const VERSION='2.2.0';
export const ID=/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$/;
export const TRANSFORMS=['x','y','rotation','scaleX','scaleY'];
const own=(o,k)=>o&&Object.hasOwn(o,k)?o[k]:undefined;
const finite=n=>typeof n==='number'&&Number.isFinite(n);
export function multiply(a,b){return [a[0]*b[0]+a[2]*b[1],a[1]*b[0]+a[3]*b[1],a[0]*b[2]+a[2]*b[3],a[1]*b[2]+a[3]*b[3],a[0]*b[4]+a[2]*b[5]+a[4],a[1]*b[4]+a[3]*b[5]+a[5]];}
export function matrix(p){const r=(p.rotation??0)*Math.PI/180,c=Math.cos(r),s=Math.sin(r),sx=p.scaleX??1,sy=p.scaleY??1;return [c*sx,s*sx,-s*sy,c*sy,p.x??0,p.y??0];}
export function point(m,x=0,y=0){return [m[0]*x+m[2]*y+m[4],m[1]*x+m[3]*y+m[5]];}
export function inverse(m){const d=m[0]*m[3]-m[1]*m[2];if(Math.abs(d)<1e-10)throw Error('Singular transform');return [m[3]/d,-m[1]/d,-m[2]/d,m[0]/d,(m[2]*m[5]-m[3]*m[4])/d,(m[1]*m[4]-m[0]*m[5])/d];}
export function validateProject(p){
 const fail=m=>{throw Error(m)};
 if(!p||p.schema!=='nhon-le-rig/v1')fail('Unsupported project schema');
 if(!ID.test(p.id))fail('Invalid project id');
 if(!Array.isArray(p.canvas)||p.canvas.length!==2||p.canvas.some(n=>!Number.isInteger(n)||n<16||n>4096))fail('Canvas must be 16..4096 integer pixels');
 if(!Array.isArray(p.origin)||p.origin.length!==2||p.origin.some((n,i)=>!finite(n)||n<0||n>p.canvas[i]))fail('Invalid ground origin');
 if(!['pixel','hd'].includes(p.representation))fail('Invalid representation');
 if(!Array.isArray(p.bones)||!p.bones.length||p.bones.length>256)fail('Expected 1..256 bones');
 const bones=new Map();
 const transforms=(obj,label)=>{for(const k of TRANSFORMS)if(obj[k]!==undefined&&!finite(obj[k]))fail(`${label}: ${k} must be finite`);for(const k of ['scaleX','scaleY'])if(obj[k]!==undefined&&obj[k]<=0)fail(`${label}: scale must be positive`);};
 for(const b of p.bones){if(!ID.test(b.id)||bones.has(b.id))fail('Invalid or duplicate bone id');bones.set(b.id,b);transforms(b,b.id);if(b.ikLimit&&(!finite(b.ikLimit.min)||!finite(b.ikLimit.max)||b.ikLimit.min>b.ikLimit.max))fail('Invalid IK angular limit');}
 for(const b of p.bones){const seen=new Set([b.id]);let c=b;while(c.parent!=null){if(!bones.has(c.parent))fail(`${b.id}: parent missing`);if(seen.has(c.parent))fail('Bone hierarchy cycle');seen.add(c.parent);c=bones.get(c.parent);}}
 if(!p.attachments||typeof p.attachments!=='object'||Array.isArray(p.attachments))fail('Attachments must be an object');
 for(const [id,a]of Object.entries(p.attachments)){if(!ID.test(id)||!a||!finite(a.width)||!finite(a.height)||a.width<=0||a.height<=0||a.width>4096||a.height>4096)fail('Invalid attachment dimensions');if(!Array.isArray(a.pivot)||a.pivot.length!==2||a.pivot.some(n=>!finite(n)))fail('Invalid attachment pivot');if(typeof a.image!=='string'||!/^data:image\/png;base64,[A-Za-z0-9+/=]+$/.test(a.image)||a.image.length>24000000)fail('Attachments require embedded PNG data');}
 if(!Array.isArray(p.slots)||p.slots.length>512)fail('Invalid slots');const slots=new Set();
 for(const s of p.slots){if(!ID.test(s.id)||slots.has(s.id)||!bones.has(s.bone))fail('Invalid or duplicate slot');slots.add(s.id);if(s.attachment!==null&&!Object.hasOwn(p.attachments,s.attachment))fail('Slot attachment missing');if(!finite(s.drawOrder))fail('Invalid draw order');transforms(s,s.id);if(s.opacity!==undefined&&(!finite(s.opacity)||s.opacity<0||s.opacity>1))fail('Invalid slot opacity');}
 if(!Array.isArray(p.clips)||!p.clips.length||p.clips.length>128)fail('Expected 1..128 clips');const clips=new Set();
 for(const c of p.clips){if(!ID.test(c.id)||clips.has(c.id))fail('Invalid or duplicate clip');clips.add(c.id);if(!Number.isInteger(c.duration_ms)||c.duration_ms<1||c.duration_ms>600000||typeof c.loop!=='boolean')fail('Invalid clip clock');if(!ID.test(c.direction)||!ID.test(c.action))fail('Clip needs action and direction');if(c.events!==undefined&&(!Array.isArray(c.events)||c.events.length>10000))fail('Invalid event list');for(const tracks of [c.tracks,c.slotTracks])if(tracks!==undefined&&(!tracks||typeof tracks!=='object'||Array.isArray(tracks)))fail('Invalid track map');
  for(const [id,keys] of Object.entries(c.tracks??{})){if(!bones.has(id)||!Array.isArray(keys)||keys.length>20000)fail('Invalid bone track');let last=-1;for(const k of keys){if(!finite(k.time_ms)||k.time_ms<0||k.time_ms>c.duration_ms||k.time_ms<=last)fail('Keyframes must be ordered, unique and inside clip');last=k.time_ms;transforms(k,id);if(k.easing!==undefined&&!['linear','smooth','step'].includes(k.easing))fail('Unknown easing');}}
  for(const [id,keys]of Object.entries(c.slotTracks??{})){if(!slots.has(id)||!Array.isArray(keys)||keys.length>20000)fail('Invalid slot track');let last=-1;for(const k of keys){if(!finite(k.time_ms)||k.time_ms<0||k.time_ms>c.duration_ms||k.time_ms<=last)fail('Invalid slot key time');last=k.time_ms;if(k.attachment!==undefined&&k.attachment!==null&&!Object.hasOwn(p.attachments,k.attachment))fail('Slot key attachment missing');if(k.drawOrder!==undefined&&!finite(k.drawOrder))fail('Invalid slot key order');transforms(k,id);if(k.opacity!==undefined&&(!finite(k.opacity)||k.opacity<0||k.opacity>1))fail('Invalid slot key opacity');if(k.easing!==undefined&&!['linear','smooth','step'].includes(k.easing))fail('Invalid slot easing');}}
  for(const e of c.events??[])if(!Number.isInteger(e.time_ms)||!ID.test(e.name)||e.time_ms<0||e.time_ms>=c.duration_ms||typeof e.name!=='string')fail('Invalid event');
 }
 if(p.skins!==undefined&&(!p.skins||typeof p.skins!=='object'||Array.isArray(p.skins)||Object.keys(p.skins).length>256))fail('Invalid skins');if(p.sockets!==undefined&&(!Array.isArray(p.sockets)||p.sockets.length>512))fail('Invalid socket list');
 for(const [id,skin]of Object.entries(p.skins??{})){if(!ID.test(id)||!skin||typeof skin!=='object'||Array.isArray(skin))fail('Invalid skin');for(const [slot,a]of Object.entries(skin)){if(!slots.has(slot)||(a!==null&&!Object.hasOwn(p.attachments,a)))fail('Invalid skin attachment');}}
 const sockets=new Set();for(const s of p.sockets??[]){if(!ID.test(s.id)||sockets.has(s.id)||!bones.has(s.bone))fail('Invalid socket');sockets.add(s.id);transforms(s,s.id);}
 if(p.requirements){if(!Array.isArray(p.requirements.actions)||!Array.isArray(p.requirements.directions))fail('Coverage requires actions and directions');coverageReport(p);}
 validateStudio(p);
 return {valid:true,bones:bones.size,slots:slots.size,attachments:Object.keys(p.attachments).length,clips:clips.size};
}
export function localTime(clip,time){if(!finite(time))throw Error('Time must be finite');return clip.loop?((time%clip.duration_ms)+clip.duration_ms)%clip.duration_ms:Math.max(0,Math.min(time,clip.duration_ms));}
export function sampleTrack(base,keys,time){
 const out={x:base.x??0,y:base.y??0,rotation:base.rotation??0,scaleX:base.scaleX??1,scaleY:base.scaleY??1};
 for(const field of TRANSFORMS){const ks=(keys??[]).filter(k=>k[field]!==undefined);if(!ks.length||time<ks[0].time_ms)continue;let a=ks[0],b=null;for(const k of ks){if(k.time_ms<=time)a=k;else{b=k;break;}}if(!b){out[field]=a[field];continue;}let f=(time-a.time_ms)/(b.time_ms-a.time_ms);if(a.easing==='step')f=0;else if(a.easing==='smooth')f=f*f*(3-2*f);let delta=b[field]-a[field];if(field==='rotation'&&a.spin!==true)delta=((delta+180)%360+360)%360-180;out[field]=a[field]+delta*f;}
 return out;
}
export function samplePose(p,clipId,time=0){
 const clip=p.clips.find(c=>c.id===clipId);if(!clip)throw Error('Clip missing');const t=localTime(clip,time),locals=Object.create(null),world=Object.create(null),byId=new Map(p.bones.map(b=>[b.id,b]));
 for(const b of p.bones)locals[b.id]=sampleTrack(b,own(clip.tracks,b.id),t);
 const resolve=id=>{if(world[id])return world[id];const b=byId.get(id);return world[id]=b.parent?multiply(resolve(b.parent),matrix(locals[id])):matrix(locals[id]);};for(const b of p.bones)resolve(b.id);
 const slots=p.slots.map(s=>{const v={...s};for(const k of own(clip.slotTracks,s.id)??[]){if(k.time_ms>t)break;if(k.attachment!==undefined)v.attachment=k.attachment;if(k.drawOrder!==undefined)v.drawOrder=k.drawOrder;}Object.assign(v,sampleTrack(s,own(clip.slotTracks,s.id),t));const alphaKeys=(own(clip.slotTracks,s.id)??[]).filter(k=>k.opacity!==undefined);v.opacity=sampleTrack({x:s.opacity??1},alphaKeys.map(k=>({...k,x:k.opacity})),t).x;v.world=multiply(world[s.bone],matrix(v));return v;}).sort((a,b)=>a.drawOrder-b.drawOrder);
 const sockets=Object.fromEntries((p.sockets??[]).map(s=>[s.id,{bone:s.bone,position:point(multiply(world[s.bone],matrix(s))),matrix:multiply(world[s.bone],matrix(s))}]));
 return {clipId,time_ms:t,locals,world,slots,sockets};
}
export function drawPose(ctx,p,pose,images){ctx.imageSmoothingEnabled=p.representation!=='pixel';for(const s of pose.slots){if(s.attachment===null)continue;const a=p.attachments[s.attachment],im=images[s.attachment];if(!im)continue;ctx.save();ctx.globalAlpha*=s.opacity??1;ctx.transform(...s.world);ctx.drawImage(im,-a.pivot[0],-a.pivot[1],a.width,a.height);ctx.restore();}}
export function upsertKey(p,clipId,boneId,time,values){
 const c=p.clips.find(c=>c.id===clipId);if(!c||!p.bones.some(b=>b.id===boneId))throw Error('Clip or bone missing');if(!finite(time)||time<0||time>c.duration_ms)throw Error('Key outside clip');
 const draft=structuredClone(p),dc=draft.clips.find(x=>x.id===clipId);dc.tracks??={};const ks=own(dc.tracks,boneId)??[];dc.tracks[boneId]=ks;let k=ks.find(k=>k.time_ms===time);if(!k){k={time_ms:time};ks.push(k);}for(const f of [...TRANSFORMS,'easing','spin'])if(values[f]!==undefined)k[f]=values[f];ks.sort((a,b)=>a.time_ms-b.time_ms);validateProject(draft);Object.assign(p,draft);return k;
}
export function scheduleFrames(clip,fps=24){
 if(!finite(fps)||fps<1||fps>120)throw Error('FPS must be 1..120');const n=Math.ceil(clip.duration_ms*fps/1000);if(n>3000)throw Error('Frame budget exceeded');
 const result=[];for(let i=0;i<n;i++){const start=Math.round(i*1000/fps),end=Math.min(Math.round((i+1)*1000/fps),clip.duration_ms);if(end>start)result.push({index:result.length,time_ms:start,sample_time_ms:start,duration_ms:end-start});}
 if(!clip.loop&&result.length)result.at(-1).sample_time_ms=clip.duration_ms;return result;
}
export function auditPose(p,pose){const bounds=[],outside=[];for(const s of pose.slots){if(s.attachment===null||s.opacity===0)continue;const a=p.attachments[s.attachment],corners=[[-a.pivot[0],-a.pivot[1]],[a.width-a.pivot[0],-a.pivot[1]],[-a.pivot[0],a.height-a.pivot[1]],[a.width-a.pivot[0],a.height-a.pivot[1]]].map(q=>point(s.world,...q));const b={slot:s.id,xmin:Math.min(...corners.map(q=>q[0])),xmax:Math.max(...corners.map(q=>q[0])),ymin:Math.min(...corners.map(q=>q[1])),ymax:Math.max(...corners.map(q=>q[1]))};bounds.push(b);if(b.xmin<0||b.ymin<0||b.xmax>p.canvas[0]||b.ymax>p.canvas[1])outside.push(s.id);}return {bounds,possible_canvas_intrusion:outside};}

// Every authoring operation validates a detached draft before returning it.
export function applyOperation(source,op){
 validateProject(source);if(!op||typeof op.type!=='string')throw Error('Operation type required');const p=structuredClone(source);
 const c=()=>{const v=p.clips.find(x=>x.id===op.clip);if(!v)throw Error('Clip missing');return v;};
 const b=()=>{const v=p.bones.find(x=>x.id===op.bone);if(!v)throw Error('Bone missing');return v;};
 const s=()=>{const v=p.slots.find(x=>x.id===op.slot);if(!v)throw Error('Slot missing');return v;};
 const unique=(id,items)=>{if(!ID.test(id)||items.some(x=>x.id===id))throw Error('Invalid or duplicate id');};
 switch(op.type){
 case 'add-clip':unique(op.id,p.clips);p.clips.push({id:op.id,action:op.action??op.id,direction:op.direction??p.clips[0].direction,duration_ms:op.duration??800,loop:op.loop??true,tracks:{},events:[]});break;
 case 'add-bone':unique(op.id,p.bones);p.bones.push({id:op.id,parent:op.parent??null,x:op.x??0,y:op.y??30,rotation:0});break;
 case 'add-slot':unique(op.id,p.slots);p.slots.push({id:op.id,bone:op.bone,attachment:op.attachment??null,drawOrder:op.drawOrder??p.slots.length});break;
 case 'rename-clip':unique(op.id,p.clips);c().id=op.id;for(const b of p.studio?.bindings??[])if(b.clip===op.clip)b.clip=op.id;break;
 case 'duplicate-clip':{unique(op.id,p.clips);const copy=structuredClone(c());copy.id=op.id;if(op.action!==undefined)copy.action=op.action;if(op.direction!==undefined)copy.direction=op.direction;p.clips.push(copy);break;}
 case 'delete-clip':if(p.clips.length===1)throw Error('Keep at least one clip');c();p.clips=p.clips.filter(x=>x.id!==op.clip);if(p.studio)p.studio.bindings=p.studio.bindings.filter(b=>b.clip!==op.clip);break;
 case 'bone-settings':if(op.limit===null)delete b().ikLimit;else b().ikLimit=op.limit;break;
 case 'rename-bone':{unique(op.id,p.bones);b().id=op.id;for(const x of p.bones)if(x.parent===op.bone)x.parent=op.id;for(const x of [...p.slots,...p.sockets??[]])if(x.bone===op.bone)x.bone=op.id;for(const x of p.clips)if(Object.hasOwn(x.tracks??{},op.bone)){x.tracks[op.id]=x.tracks[op.bone];delete x.tracks[op.bone];}break;}
 case 'delete-bone':{b();const ids=new Set([op.bone]);let count;do{count=ids.size;for(const x of p.bones)if(ids.has(x.parent))ids.add(x.id);}while(count!==ids.size);if(ids.size===p.bones.length)throw Error('Keep at least one bone');const slots=new Set(p.slots.filter(x=>ids.has(x.bone)).map(x=>x.id));p.bones=p.bones.filter(x=>!ids.has(x.id));p.slots=p.slots.filter(x=>!slots.has(x.id));p.sockets=(p.sockets??[]).filter(x=>!ids.has(x.bone));for(const x of p.clips){for(const id of ids)delete x.tracks?.[id];for(const id of slots)delete x.slotTracks?.[id];}for(const skin of Object.values(p.skins??{}))for(const id of slots)delete skin[id];break;}
 case 'reparent':{const bone=b();const rest={...p,clips:[{...p.clips[0],tracks:{},slotTracks:{}}]},pose=samplePose(rest,rest.clips[0].id,0);if(op.parent!==null&&!p.bones.some(x=>x.id===op.parent))throw Error('Parent missing');const m=op.parent===null?pose.world[bone.id]:multiply(inverse(pose.world[op.parent]),pose.world[bone.id]);const sx=Math.hypot(m[0],m[1]),sy=Math.hypot(m[2],m[3]);if(Math.abs(m[0]*m[2]+m[1]*m[3])>1e-7*sx*sy)throw Error('Reparent creates shear; choose a uniformly scaled parent');bone.parent=op.parent;Object.assign(bone,{x:m[4],y:m[5],rotation:Math.atan2(m[1],m[0])*180/Math.PI,scaleX:sx,scaleY:sy});if(p.clips.some(x=>(own(x.tracks,bone.id)??[]).length))throw Error('Clear animated track before preserving rest-space reparent');break;}
 case 'project':if(op.name!==undefined)p.name=String(op.name).slice(0,160);if(op.canvas)p.canvas=op.canvas;if(op.origin)p.origin=op.origin;if(op.representation)p.representation=op.representation;if(op.requirements)p.requirements=op.requirements;break;
 case 'set-slot':Object.assign(s(),op.values);break;
 case 'delete-slot':s();p.slots=p.slots.filter(x=>x.id!==op.slot);for(const x of p.clips)delete x.slotTracks?.[op.slot];for(const skin of Object.values(p.skins??{}))delete skin[op.slot];break;
 case 'slot-key':{s();const clip=c();clip.slotTracks??={};const keys=own(clip.slotTracks,op.slot)??[];clip.slotTracks[op.slot]=keys;let k=keys.find(x=>x.time_ms===op.time);if(!k){k={time_ms:op.time};keys.push(k);}for(const field of [...TRANSFORMS,'attachment','drawOrder','opacity','easing'])if(op.values?.[field]!==undefined)k[field]=op.values[field];keys.sort((a,b)=>a.time_ms-b.time_ms);break;}
 case 'remove-slot-key':s();c().slotTracks??={};c().slotTracks[op.slot]=(own(c().slotTracks,op.slot)??[]).filter(x=>x.time_ms!==op.time);break;
 case 'move-key':{const clip=c(),tracks=op.slot?clip.slotTracks:clip.tracks,id=op.slot??op.bone,keys=own(tracks,id)??[],key=keys.find(x=>x.time_ms===op.from);if(!key)throw Error('Key missing');if(keys.some(x=>x!==key&&x.time_ms===op.to))throw Error('Destination already has a key');key.time_ms=op.to;keys.sort((a,b)=>a.time_ms-b.time_ms);break;}
 case 'retime':{const clip=c(),ratio=op.duration/clip.duration_ms;for(const keys of [...Object.values(clip.tracks??{}),...Object.values(clip.slotTracks??{})])for(const k of keys)k.time_ms=Math.round(k.time_ms*ratio);for(const e of clip.events??[])e.time_ms=Math.min(op.duration-1,Math.round(e.time_ms*ratio));for(const b of p.studio?.bindings??[])if(b.clip===op.clip&&b.trigger==='time')b.start_ms=Math.min(op.duration-1,Math.round(b.start_ms*ratio));clip.duration_ms=op.duration;break;}
 case 'clear-track':b();delete c().tracks?.[op.bone];break;
 case 'pose-key':{const pose=op.pose??samplePose(p,op.clip,op.sourceTime??op.time);for(const [id,values]of Object.entries(pose.locals??{}))upsertKey(p,op.clip,id,op.time,values);break;}
 case 'event':{const clip=c();clip.events??=[];if(op.remove){clip.events=clip.events.filter((e,i)=>i!==op.index);break;}const event={name:op.name,time_ms:op.time};if(op.payload!==undefined)event.payload=op.payload;if(op.index!==undefined){if(!clip.events[op.index])throw Error('Event missing');clip.events[op.index]=event;}else clip.events.push(event);clip.events.sort((a,b)=>a.time_ms-b.time_ms);break;}
 case 'socket':{p.sockets??=[];if(op.remove){if(!p.sockets.some(x=>x.id===op.id))throw Error('Socket missing');p.sockets=p.sockets.filter(x=>x.id!==op.id);break;}const socket=p.sockets.find(x=>x.id===op.id);if(socket)Object.assign(socket,{bone:op.bone,x:op.x,y:op.y});else p.sockets.push({id:op.id,bone:op.bone,x:op.x,y:op.y});break;}
 case 'save-skin':if(!ID.test(op.id))throw Error('Invalid skin id');p.skins??={};p.skins[op.id]=Object.fromEntries(p.slots.map(x=>[x.id,x.attachment]));break;
 case 'apply-skin':{const skin=own(p.skins,op.id);if(!skin)throw Error('Skin missing');for(const slot of p.slots)if(Object.hasOwn(skin,slot.id))slot.attachment=skin[slot.id];break;}
 case 'delete-skin':if(!own(p.skins,op.id))throw Error('Skin missing');delete p.skins[op.id];break;
 case 'delete-attachment':{if(studioUsesAsset(p,op.id))throw Error('Attachment is in use by VFX or a variant');if(!Object.hasOwn(p.attachments,op.id))throw Error('Attachment missing');if(p.slots.some(x=>x.attachment===op.id)||p.clips.some(x=>Object.values(x.slotTracks??{}).some(ks=>ks.some(k=>k.attachment===op.id)))||Object.values(p.skins??{}).some(x=>Object.values(x).includes(op.id)))throw Error('Attachment is in use by a slot, key or skin');delete p.attachments[op.id];if(p.studio)delete p.studio.assetInfo[op.id];break;}
 case 'ik':return solveIK(p,op.clip,op.bone,op.time,op.target,op.depth??2,op.rest??false).project;
 case 'fx-put':case 'fx-delete':case 'fx-binding':case 'fx-unbind':case 'scene':case 'asset-put':case 'asset-info':applyStudioOp(p,op);break;
 default:throw Error('Unknown authoring operation: '+op.type);
 }
 validateProject(p);return p;
}
// CCD positions the selected joint by rotating its ancestors; baked keys use no runtime IK.
export function solveIK(source,clipId,effector,time,target,depth=2,rest=false){
 validateProject(source);if(!Array.isArray(target)||target.length!==2||target.some(n=>!finite(n))||!Number.isInteger(depth)||depth<1||depth>16)throw Error('Invalid IK target or depth');
 const p=structuredClone(source),byId=new Map(p.bones.map(b=>[b.id,b])),end=byId.get(effector);if(!end)throw Error('Effector missing');const chain=[];let b=end;while(b.parent&&chain.length<depth){b=byId.get(b.parent);chain.push(b.id);}if(!chain.length)throw Error('IK needs a parent chain');
 const view=rest?{...p,clips:[{...p.clips.find(c=>c.id===clipId),tracks:{},slotTracks:{}}]}:p,locals=samplePose(view,clipId,time).locals;
 const worlds=()=>{const world=Object.create(null);const resolve=id=>{const b=byId.get(id);return world[id]??=b.parent?multiply(resolve(b.parent),matrix(locals[id])):matrix(locals[id]);};for(const b of p.bones)resolve(b.id);return world;};
 let error=Infinity,iterations=0;for(;iterations<64;iterations++){let w=worlds();error=Math.hypot(...point(w[effector]).map((n,i)=>n-target[i]));if(error<.05)break;for(const id of chain){w=worlds();const parent=byId.get(id).parent,parentWorld=parent?w[parent]:[1,0,0,1,0,0],inv=inverse(parentWorld),cur=point(inv,...point(w[effector])),goal=point(inv,...target),local=locals[id],a=[cur[0]-local.x,cur[1]-local.y],z=[goal[0]-local.x,goal[1]-local.y];if(Math.hypot(...a)<1e-8||Math.hypot(...z)<1e-8)continue;let delta=(Math.atan2(z[1],z[0])-Math.atan2(a[1],a[0]))*180/Math.PI;delta=((delta+180)%360+360)%360-180;local.rotation+=delta;const limit=byId.get(id).ikLimit;if(limit)local.rotation=Math.max(limit.min,Math.min(limit.max,local.rotation));}}
 for(const id of chain){if(rest)byId.get(id).rotation=locals[id].rotation;else upsertKey(p,clipId,id,time,{rotation:locals[id].rotation});}validateProject(p);error=Math.hypot(...point(worlds()[effector]).map((n,i)=>n-target[i]));return {project:p,error_px:error,iterations,reached:error<.5};
}
export function sheetLayout(canvas,count,maxSize=2048,gutter=2){
 if(!Number.isInteger(count)||count<1||!Number.isInteger(maxSize)||maxSize<64||maxSize>4096||!Number.isInteger(gutter)||gutter<0||gutter>32)throw Error('Invalid sheet layout');const [w,h]=canvas,cw=w+2*gutter,ch=h+2*gutter,cols=Math.floor(maxSize/cw),rows=Math.floor(maxSize/ch);if(!cols||!rows)throw Error('Cell exceeds sheet size');const per=cols*rows,pages=[];for(let start=0;start<count;start+=per){const n=Math.min(per,count-start),pageCols=Math.min(cols,n);pages.push({width:pageCols*cw,height:Math.ceil(n/cols)*ch,frames:Array.from({length:n},(_,i)=>({index:start+i,x:(i%cols)*cw+gutter,y:Math.floor(i/cols)*ch+gutter,w,h}))});}return pages;
}
export function coverageReport(p,actions=p.requirements?.actions??[...new Set(p.clips.map(c=>c.action))],directions=p.requirements?.directions??[...new Set(p.clips.map(c=>c.direction))]){if(!Array.isArray(actions)||!Array.isArray(directions)||!actions.length||!directions.length||actions.length>64||directions.length>32||actions.some(x=>!ID.test(x))||directions.some(x=>!ID.test(x)))throw Error('Invalid coverage requirements');const rows=[];for(const action of new Set(actions))for(const direction of new Set(directions)){const clips=p.clips.filter(c=>c.action===action&&c.direction===direction).map(c=>c.id);rows.push({action,direction,clips,present:clips.length>0});}return {required:rows.length,present:rows.filter(x=>x.present).length,missing:rows.filter(x=>!x.present),rows,visual_status:'not_reviewed',runtime_status:'not_tested'};}
export function hasArtwork(p){return p.slots.some(s=>s.attachment!==null)||p.clips.some(c=>Object.values(c.slotTracks??{}).some(keys=>keys.some(k=>k.attachment!==undefined&&k.attachment!==null)));}
