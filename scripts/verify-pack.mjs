#!/usr/bin/env node
// Reads data only. Never imports or executes code from the inspected export.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {isDeepStrictEqual} from 'node:util';
import {VFX_CLOCK_SOURCE,enginePackFiles} from '../web/engine-adapters.mjs';
import {PIXI_VFX_ADAPTER,GODOT_VFX_ADAPTER,vfxFiles} from '../web/production-export.mjs';
import {validateProject} from '../web/rig-core.mjs';
import {canvasBackend,rasterImages} from '../skills/produce-game-sprites/tools/rig-animation/scripts/rig-tool.mjs';
import {nativeTint} from '../skills/produce-game-sprites/tools/rig-animation/scripts/production-cli.mjs';

const {validateBakedManifest}=await import('data:text/javascript;base64,'+Buffer.from(VFX_CLOCK_SOURCE).toString('base64'));
const sha=b=>createHash('sha256').update(b).digest('hex');
const requireThat=(value,message)=>{if(!value)throw Error(message);};
const same=(a,b,label)=>requireThat(isDeepStrictEqual(a,b),label+' differs');
const safeName=n=>typeof n==='string'&&n.length>0&&!n.includes('\\')&&!n.includes(':')&&!n.includes('\0')&&!path.posix.isAbsolute(n)&&n.split('/').every(p=>p&&p!=='.'&&p!=='..');
const crcTable=Uint32Array.from({length:256},(_,n)=>{for(let k=0;k<8;k++)n=(n&1)?0xedb88320^(n>>>1):n>>>1;return n>>>0;});
function crc32(b){let c=0xffffffff;for(const n of b)c=crcTable[(c^n)&255]^(c>>>8);return (c^0xffffffff)>>>0;}

export function pngInfo(b,label){
 requireThat(b.length>=33&&b.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])),'Invalid PNG: '+label);
 let pos=8,ihdr=false,idat=false,iend=false,width,height;
 while(pos<b.length){
  requireThat(pos+12<=b.length,'Truncated PNG chunk: '+label);
  const len=b.readUInt32BE(pos),end=pos+12+len,type=b.toString('ascii',pos+4,pos+8);
  requireThat(end<=b.length,'Truncated PNG data: '+label);
  requireThat(crc32(b.subarray(pos+4,end-4))===b.readUInt32BE(end-4),'PNG CRC mismatch: '+label);
  if(!ihdr){requireThat(type==='IHDR'&&len===13,'Missing PNG IHDR: '+label);width=b.readUInt32BE(pos+8);height=b.readUInt32BE(pos+12);requireThat(width>0&&height>0&&width*height<=64000000,'PNG pixel budget exceeded: '+label);requireThat(b[pos+16]===8&&b[pos+17]===6&&b[pos+18]===0&&b[pos+19]===0&&b[pos+20]===0,'Expected noninterlaced 8-bit RGBA PNG: '+label);ihdr=true;}
  else requireThat(type!=='IHDR','Duplicate PNG IHDR: '+label);
  if(type==='IDAT')idat=true;
  if(type==='IEND'){requireThat(len===0&&end===b.length&&idat,'Invalid PNG end: '+label);iend=true;}
  pos=end;
 }
 requireThat(iend,'Missing PNG IEND: '+label);return {width,height,rgba_bytes:width*height*4};
}

async function inventory(root){
 const files=new Map();let total=0;
 async function walk(dir,rel='',depth=0){
  requireThat(depth<12,'Pack directory nesting exceeds 12');
  const names=(await fs.readdir(dir)).sort();
  for(const name of names){
   const relative=rel?rel+'/'+name:name;requireThat(safeName(relative),'Unsafe pack filename: '+relative);
   const file=path.join(dir,name),st=await fs.lstat(file);requireThat(!st.isSymbolicLink(),'Symlink forbidden: '+relative);
   if(st.isDirectory())await walk(file,relative,depth+1);
   else {requireThat(st.isFile(),'Not a regular file: '+relative);requireThat(st.size<=64000000,'File exceeds 64 MB: '+relative);total+=st.size;requireThat(total<=512000000&&files.size<10000,'Pack exceeds 512 MB / 10000 files');files.set(relative,{path:file,bytes:st.size});}
  }
 }
 await walk(root);return {files,total};
}

export async function verifyPack(directory,options={}){
 const report={schema:'nhon-le-pack-verification/v1',status:'failed',checks:[],errors:[],warnings:[],visual:'not_reviewed',runtime:'not_tested'};
 try{
  const root=await fs.realpath(directory);requireThat((await fs.stat(root)).isDirectory(),'Pack must be an extracted directory');
  const {files,total}=await inventory(root),used=new Set(),observedHashes=new Map();
  const read=async name=>{requireThat(safeName(name),'Unsafe reference: '+name);requireThat(files.has(name),'Missing pack file: '+name);used.add(name);const b=await fs.readFile(files.get(name).path);requireThat(b.length===files.get(name).bytes,'File changed during verification: '+name);const digest=sha(b);requireThat(!observedHashes.has(name)||observedHashes.get(name)===digest,'File changed during verification: '+name);observedHashes.set(name,digest);return b;};
  const json=async name=>JSON.parse((await read(name)).toString('utf8'));
  const m=validateBakedManifest(await json('vfx.json'));requireThat(m.effects.length>0,'Empty VFX pack');
  requireThat(m.effects.length<=128&&m.effects.reduce((n,e)=>n+e.frames.length,0)<=10000,'Track/frame budget exceeded');
  requireThat(Number.isFinite(m.fps)&&m.fps>0,'Invalid export FPS');
  const source=await json('source.rig.json');validateProject(source);
  const clip=source.clips.find(c=>c.id===m.clip);requireThat(clip,'Source clip missing');
  same(m.canvas,source.canvas,'Source canvas');same(m.origin,source.origin,'Source origin');same(m.events,clip.events??[],'Source events');same(m.duration_ms,clip.duration_ms,'Source duration');same(m.loop,clip.loop,'Source loop');
  const metadata=await json('engine-pack.json');requireThat(typeof metadata.selected_engine==='string','Missing selected engine');
  const expected=enginePackFiles(m,metadata.selected_engine,{pixi:PIXI_VFX_ADAPTER,godot:GODOT_VFX_ADAPTER});
  same(metadata,JSON.parse(expected['engine-pack.json']),'Engine metadata');
  for(const [name,data]of Object.entries(expected))if(name!=='engine-pack.json')requireThat((await read(name)).equals(Buffer.from(data)),'Adapter/document differs from bundled version: '+name);
  report.engine=metadata.selected_engine;report.checks.push('manifest_intervals','source_geometry_events','bundled_adapter_bytes');
  const pngs=new Map();let decodedPixels=0;
  const inspect=async name=>{if(!pngs.has(name)){const info=pngInfo(await read(name),name);decodedPixels+=info.width*info.height;requireThat(decodedPixels<=128000000,'PNG inspection exceeds 128 million pixels');pngs.set(name,info);}return pngs.get(name);};
  const referencedPages=new Set(),framePaths=new Set();let frames=0;
  for(const e of m.effects){
   requireThat(/^[-a-zA-Z0-9_]+$/.test(e.id),'Unsafe effect id');
   const effect=source.studio?.effects.find(f=>f.id===e.effect);requireThat(effect,'Source effect missing: '+e.id);
   same(e.id,e.effect+'_'+e.depth,'Track identifier');same(e.blend,effect.blend,'Source blend');
   same(e.bindings,source.studio.bindings.filter(b=>b.clip===m.clip&&b.effect===e.effect&&b.depth===e.depth),'Source bindings');requireThat(e.bindings.length>0,'Track has no bindings');
   same(e.active_start_ms,e.frames[0].time_ms,'Active start');same(e.active_end_ms,e.frames.at(-1).time_ms+e.frames.at(-1).duration_ms,'Active end');
   const contract=await json(e.id+'-contract.json');
   const wanted={schema_version:1,vfx_id:e.id,representation:source.representation,attachment_space:'actor',loop:m.loop,blend_intent:e.blend,alpha_policy:'soft',cell_size:m.canvas,clip_duration_ms:m.duration_ms,active_start_ms:e.active_start_ms,active_end_ms:e.active_end_ms,clip_events:m.events,frames:e.frames.map((f,i)=>({id:'frame_'+i,path:f.path,duration_ms:f.duration_ms})),events:{},performance_budget:{max_simultaneous_instances:1,allow_large_transparent_canvas:true}};
   same(contract,wanted,'Track contract '+e.id);
   for(const f of e.frames){
    requireThat(typeof f.empty==='boolean','Missing frame empty flag');requireThat(!framePaths.has(f.path),'Repeated frame path');framePaths.add(f.path);
    requireThat(typeof f.path==='string'&&f.path.startsWith('frames/'+e.id+'/')&&f.path.endsWith('.png'),'Invalid frame path');
    const p=await inspect(f.page),s=await inspect(f.path);same([s.width,s.height],m.canvas,'Frame dimensions '+f.path);
    requireThat(f.rect[0]+f.rect[2]<=p.width&&f.rect[1]+f.rect[3]<=p.height,'Atlas rectangle outside page: '+f.page);referencedPages.add(f.page);frames++;
   }
  }
  const boundTracks=new Set(source.studio.bindings.filter(b=>b.clip===m.clip).map(b=>b.effect+'_'+b.depth));same(new Set(m.effects.map(e=>e.id)),boundTracks,'Source track coverage');
  // Include unused transparent atlas pages emitted before endpoint trimming in the budget.
  for(const name of files.keys())if(name.endsWith('.png'))await inspect(name);
  const atlasPages=[...pngs].filter(([name])=>!name.startsWith('frames/'));
  const rgbaBytes=atlasPages.reduce((n,[,p])=>n+p.rgba_bytes,0);
  report.resources={files:files.size,file_bytes:total,tracks:m.effects.length,frames,atlas_pages:atlasPages.length,referenced_atlas_pages:referencedPages.size,atlas_rgba_bytes:rgbaBytes,max_texture_dimension:Math.max(...atlasPages.map(([,p])=>Math.max(p.width,p.height)))};
  const unused=atlasPages.map(([name])=>name).filter(n=>!referencedPages.has(n));if(unused.length)report.warnings.push({code:'unused_atlas_pages',files:unused});
  if(options.maxTextureSize!==undefined)requireThat(report.resources.max_texture_dimension<=options.maxTextureSize,'Texture dimension exceeds requested budget');
  if(options.maxTextureMiB!==undefined)requireThat(rgbaBytes<=options.maxTextureMiB*1024*1024,'Atlas RGBA memory exceeds requested budget');
  report.checks.push('png_chunks_crc_dimensions','track_contracts','atlas_bounds','source_track_coverage');
  if(options.pixels||options.rerender){
   const {createCanvas,loadImage}=await canvasBackend();
   async function rgba(bytes,rect){const img=await loadImage(bytes),r=rect??[0,0,img.width,img.height],c=createCanvas(r[2],r[3]),cx=c.getContext('2d');cx.drawImage(img,...r,0,0,r[2],r[3]);return Buffer.from(cx.getImageData(0,0,r[2],r[3]).data);}
   for(const page of referencedPages){
    const bytes=await read(page),info=pngs.get(page),img=await loadImage(bytes),c=createCanvas(info.width,info.height),cx=c.getContext('2d');cx.drawImage(img,0,0);
    for(const e of m.effects)for(const f of e.frames)if(f.page===page){const a=Buffer.from(cx.getImageData(...f.rect).data),b=await rgba(await read(f.path));requireThat(a.equals(b),'Atlas/frame pixels differ: '+f.path);let visible=false;for(let i=3;i<a.length;i+=4)if(a[i]){visible=true;break;}requireThat(f.empty===!visible,'Frame empty flag differs: '+f.path);}
   }
   report.checks.push('decoded_atlas_frame_pixels');
   if(options.rerender){
    const backend=await rasterImages(source),fresh=await vfxFiles(source,m.clip,m.fps,{...backend,tint:nativeTint(backend.createCanvas),encode:c=>c.toBuffer('image/png')},64000000,metadata.selected_engine);
    same(fresh.manifest,m,'Re-rendered manifest');
    for(const [name,bytes]of Object.entries(fresh.files))if(name.endsWith('.png'))requireThat((await rgba(await read(name))).equals(await rgba(bytes)),'Re-rendered pixels differ: '+name);
    report.checks.push('source_rerender_pixels');
   }
  }else report.warnings.push({code:'pixels_not_decoded',message:'Use --pixels to compare atlas/frame pixels; --rerender also checks source rendering.'});
  await read('README.txt');const extra=[...files.keys()].filter(n=>!used.has(n));if(extra.length)report.warnings.push({code:'additional_files',files:extra});
  report.file_hashes={};for(const [name]of files)report.file_hashes[name]=sha(await read(name));
  same([...files.keys()],[...(await inventory(root)).files.keys()],'Pack inventory during verification');
  report.pack_sha256=sha(JSON.stringify(report.file_hashes));
  if(options.baseline){
   const old=JSON.parse(await fs.readFile(options.baseline,'utf8'));
   requireThat(old.schema===report.schema&&old.status==='passed'&&old.file_hashes&&old.pack_sha256===sha(JSON.stringify(old.file_hashes)),'Invalid baseline report');
   same(report.file_hashes,old.file_hashes,'Pack bytes versus baseline');report.checks.push('baseline_sha256');
  }
  report.status='passed';
 }catch(e){report.errors.push(e.message);}
 return report;
}

export async function verifyMain(args){
 if(!args.length||args[0]==='help'||args[0]==='--help'){console.log('verify-pack DIR [--pixels | --rerender] [--baseline REPORT.json] [--max-texture-size PIXELS] [--max-texture-mib MIB] [--out NEW_REPORT.json]\nRead-only technical checks. Reports must be outside DIR. Engine/art acceptance stays unreviewed.');return;}
 const [directory,...rest]=args,options={};let out;const seen=new Set();
 for(let i=0;i<rest.length;i++){
  const flag=rest[i];requireThat(!seen.has(flag),'Duplicate option: '+flag);seen.add(flag);
  if(flag==='--pixels')options.pixels=true;
  else if(flag==='--rerender')options.rerender=true;
  else {requireThat(['--baseline','--out','--max-texture-size','--max-texture-mib'].includes(flag),'Unknown option: '+flag);const value=rest[++i];requireThat(value&&!value.startsWith('--'),'Value required: '+flag);if(flag==='--out')out=value;else if(flag==='--baseline')options.baseline=value;else {const n=Number(value);requireThat(Number.isFinite(n)&&n>0&&(flag!=='--max-texture-size'||Number.isInteger(n)),'Positive budget required: '+flag);options[flag==='--max-texture-size'?'maxTextureSize':'maxTextureMiB']=n;}}
 }
 if(out){const root=await fs.realpath(directory),parent=await fs.realpath(path.dirname(path.resolve(out)));requireThat(parent!==root&&!parent.startsWith(root+path.sep),'Report must be outside the inspected pack');}
 const report=await verifyPack(directory,options),serialized=JSON.stringify(report,null,2)+'\n';
 if(out)await fs.writeFile(out,serialized,{flag:'wx'});
 console.log(serialized.trim());if(report.status!=='passed')process.exitCode=1;return report;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href)verifyMain(process.argv.slice(2)).catch(e=>{console.error(JSON.stringify({status:'failed',errors:[e.message]}));process.exitCode=1;});
