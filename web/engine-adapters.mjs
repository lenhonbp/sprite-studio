// Portable baked-VFX handoff. Engine SDKs remain project-owned, never bundled.
export const ENGINE_TARGETS=Object.freeze([
 {id:'generic',name:'Generic PNG + JSON',version:'nhon-le-vfx-baked/v1',file:null,checks:'manifest/clock'},
 {id:'canvas',name:'Canvas / HTML5',version:'Canvas 2D',file:'canvas-vfx.mjs',checks:'native canvas pixels'},
 {id:'phaser',name:'Phaser',version:'3.x',file:'phaser-vfx.mjs',checks:'API-model contract'},
 {id:'three',name:'Three.js',version:'Sprite API',file:'three-vfx.mjs',checks:'API-model contract'},
 {id:'unity',name:'Unity',version:'6 / SpriteRenderer',file:'NhonLeVfxPlayer.cs',checks:'source only; compiler unavailable'},
 {id:'cocos',name:'Cocos Creator',version:'3.8 / 2D',file:'cocos-vfx.ts',checks:'transpiled API-model contract'},
 {id:'godot',name:'Godot',version:'4.x',file:'godot-vfx.gd',checks:'source only; engine unavailable'},
 {id:'pixi',name:'PixiJS',version:'8.x',file:'pixi-vfx.mjs',checks:'API-model contract'}
].map(x=>Object.freeze({...x,runtime:'not_tested'})));
export function engineTargets(){return ENGINE_TARGETS.map(x=>({...x}));}
export function selectEngines(target='all'){if(target==='all')return engineTargets();const found=ENGINE_TARGETS.find(x=>x.id===target);if(!found)throw Error('Unknown engine: '+target+'; choose all or '+ENGINE_TARGETS.map(x=>x.id).join(', '));return [{...found}];}
// Indentation inside source strings protects ESM declarations from the offline bundler.
export const VFX_CLOCK_SOURCE=`// Engine-independent candidate clock. Events are data; the game owns dispatch.
  export function validateBakedManifest(m){
 const pair=(a)=>Array.isArray(a)&&a.length===2&&a.every(Number.isFinite);
 if(m?.schema!=='nhon-le-vfx-baked/v1'||m.coordinate_space!=='actor_canvas_baked'||!pair(m.canvas)||m.canvas.some(v=>!Number.isInteger(v)||v<1)||!pair(m.origin)||!Number.isFinite(m.duration_ms)||m.duration_ms<=0||typeof m.loop!=='boolean'||!Array.isArray(m.effects))throw Error('Invalid baked VFX manifest');
 const ids=new Set();for(const e of m.effects){if(typeof e.id!=='string'||ids.has(e.id)||!['back','front'].includes(e.depth)||!['normal','additive'].includes(e.blend)||!Array.isArray(e.frames)||!e.frames.length)throw Error('Invalid effect track');ids.add(e.id);let end=0;for(const f of e.frames){if(typeof f.page!=='string'||!/^[-a-zA-Z0-9_]+[.]png$/.test(f.page)||!Array.isArray(f.rect)||f.rect.length!==4||!f.rect.every(Number.isInteger)||f.rect[0]<0||f.rect[1]<0||f.rect[2]!==m.canvas[0]||f.rect[3]!==m.canvas[1]||!Number.isFinite(f.time_ms)||!Number.isFinite(f.duration_ms)||f.duration_ms<=0||f.time_ms<end||f.time_ms+f.duration_ms>m.duration_ms)throw Error('Invalid frame interval or atlas rectangle');end=f.time_ms+f.duration_ms;}}
 return m;
}
  export function checkPage(page,frame){const width=page?.naturalWidth??page?.width,height=page?.naturalHeight??page?.height;if(!Number.isFinite(width)||!Number.isFinite(height)||frame.rect[0]+frame.rect[2]>width||frame.rect[1]+frame.rect[3]>height)throw Error('Atlas page missing or frame outside image: '+frame.page);return page;}
  export function createVfxClock(manifest){const m=structuredClone(validateBakedManifest(manifest));let elapsed=0,ended=false;
 function seek(ms){if(!Number.isFinite(ms))throw Error('Finite milliseconds required');elapsed=Math.max(0,ms);ended=!m.loop&&elapsed>=m.duration_ms;const time=m.loop?elapsed%m.duration_ms:elapsed;return m.effects.map(effect=>({effect,frame:ended?null:effect.frames.find(f=>time>=f.time_ms&&time<f.time_ms+f.duration_ms)??null}));}
 return {manifest:m,seek,advance(ms){if(!Number.isFinite(ms)||ms<0)throw Error('Nonnegative finite delta required');return seek(elapsed+ms);},get elapsed(){return elapsed;},get ended(){return ended;}};
}
`;
export const VFX_CLOCK_TYPES=`// Types for importing the shared .mjs clock in TypeScript projects.
  export interface BakedFrame {page:string;rect:[number,number,number,number];time_ms:number;duration_ms:number;}
  export interface BakedTrack {id:string;depth:'back'|'front';blend:'normal'|'additive';frames:BakedFrame[];}
  export interface BakedManifest {schema:'nhon-le-vfx-baked/v1';coordinate_space:'actor_canvas_baked';canvas:[number,number];origin:[number,number];duration_ms:number;loop:boolean;effects:BakedTrack[];events?:unknown[];}
  export function validateBakedManifest(m:unknown):BakedManifest;
  export function checkPage<T extends {width:number;height:number}>(page:T|undefined,frame:BakedFrame):T;
  export function createVfxClock(manifest:unknown):{manifest:BakedManifest;seek(ms:number):{effect:BakedTrack;frame:BakedFrame|null}[];advance(ms:number):{effect:BakedTrack;frame:BakedFrame|null}[];readonly elapsed:number;readonly ended:boolean;};
`;
export const CANVAS_VFX_ADAPTER=`// Canvas 2D candidate. pages: Map<atlas path, decoded image>. No image loader or timer is hidden here.
  import {createVfxClock,checkPage} from './vfx-clock.mjs';
  export function createCanvasVfxPlayer(manifest,pages){const clock=createVfxClock(manifest);for(const e of clock.manifest.effects)for(const f of e.frames)checkPage(pages.get(f.page),f);let sampled=clock.seek(0);
 function draw(ctx,depth,originX=0,originY=0){if(!['back','front'].includes(depth))throw Error('Draw back or front around the actor');ctx.save();try{for(const {effect,frame}of sampled){if(effect.depth!==depth||!frame)continue;ctx.globalAlpha=1;ctx.globalCompositeOperation=effect.blend==='additive'?'lighter':'source-over';ctx.drawImage(pages.get(frame.page),...frame.rect,originX-clock.manifest.origin[0],originY-clock.manifest.origin[1],...clock.manifest.canvas);}}finally{ctx.restore();}}
 return {draw,seek(ms){sampled=clock.seek(ms);},advance(ms){sampled=clock.advance(ms);},get ended(){return clock.ended;}};
}
`;
export const PHASER_VFX_ADAPTER=`// Phaser 3 candidate. Queue pages in scene.preload, instantiate only after loading.
  import {createVfxClock,validateBakedManifest} from './vfx-clock.mjs';
  export function preloadPhaserVfx(scene,manifest,baseUrl,prefix){validateBakedManifest(manifest);if(!prefix)throw Error('Use a pack-unique texture prefix');const keys={};for(const e of manifest.effects)for(const f of e.frames)if(!keys[f.page]){const key=prefix+':'+f.page;if(scene.textures.exists(key))throw Error('Texture key already exists: '+key);scene.load.image(key,new URL(f.page,baseUrl).href);keys[f.page]=key;}return keys;}
  export function createPhaserVfxPlayer(Phaser,scene,manifest,pageKeys){const clock=createVfxClock(manifest),m=clock.manifest;
 for(const e of m.effects)for(const f of e.frames){const texture=scene.textures.get(pageKeys[f.page]);if(!pageKeys[f.page]||!scene.textures.exists(pageKeys[f.page])||f.rect[0]+f.rect[2]>texture.source[0].width||f.rect[1]+f.rect[3]>texture.source[0].height)throw Error('Missing or undersized atlas: '+f.page);}
 const root=scene.add.container(0,0),back=scene.add.container(0,0),front=scene.add.container(0,0);root.add([back,front]);const owned=[],sprites=m.effects.map(e=>{const s=scene.add.image(-m.origin[0],-m.origin[1],pageKeys[e.frames[0].page]);s.setOrigin(0,0);s.setBlendMode(e.blend==='additive'?Phaser.BlendModes.ADD:Phaser.BlendModes.NORMAL);(e.depth==='back'?back:front).add(s);return s;});let serial=0;
 function apply(rows){rows.forEach(({frame},i)=>{const s=sprites[i];s.setVisible(!!frame);if(!frame)return;const key=pageKeys[frame.page],texture=scene.textures.get(key);let cached=owned.find(x=>x.key===key&&x.rect===frame.rect.join(','));if(!cached){let name;do{name='nhonle-vfx-'+serial++;}while(texture.has(name));texture.add(name,0,...frame.rect);cached={key,rect:frame.rect.join(','),name};owned.push(cached);}s.setTexture(key,cached.name);});}
 apply(clock.seek(0));return {root,back,front,seek(ms){apply(clock.seek(ms));},advance(ms){apply(clock.advance(ms));},get ended(){return clock.ended;},destroy(){root.destroy(true);for(const f of owned)scene.textures.get(f.key).remove(f.name);}};
}
`;
export const THREE_VFX_ADAPTER=`// Three.js candidate for an orthographic 2D overlay. Atlas textures must use flipY=true (TextureLoader).
  import {createVfxClock,checkPage} from './vfx-clock.mjs';
  export function createThreeVfxPlayer(THREE,manifest,pages,{pixelsPerUnit=100}={}){if(!Number.isFinite(pixelsPerUnit)||pixelsPerUnit<=0)throw Error('Positive pixelsPerUnit required');const clock=createVfxClock(manifest),m=clock.manifest;
 for(const e of m.effects)for(const f of e.frames){const texture=pages.get(f.page);if(texture?.flipY!==true)throw Error('Use flipY=true atlas textures');checkPage(texture.image,f);}
 const root=new THREE.Group(),back=new THREE.Group(),front=new THREE.Group();root.add(back,front);const cache=new Map(),sprites=m.effects.map(e=>{const material=new THREE.SpriteMaterial({transparent:true,toneMapped:false,depthTest:false,depthWrite:false,blending:e.blend==='additive'?THREE.AdditiveBlending:THREE.NormalBlending});const s=new THREE.Sprite(material);s.scale.set(m.canvas[0]/pixelsPerUnit,m.canvas[1]/pixelsPerUnit,1);s.position.set((m.canvas[0]/2-m.origin[0])/pixelsPerUnit,(m.origin[1]-m.canvas[1]/2)/pixelsPerUnit,0);s.renderOrder=e.depth==='back'?-1:1;(e.depth==='back'?back:front).add(s);return s;});
 function apply(rows){rows.forEach(({frame},i)=>{const s=sprites[i];s.visible=!!frame;if(!frame)return;const key=frame.page+':'+frame.rect.join(',');let t=cache.get(key);if(!t){const page=pages.get(frame.page),[x,y,w,h]=frame.rect;t=page.clone();t.colorSpace=THREE.SRGBColorSpace;t.repeat.set(w/page.image.width,h/page.image.height);t.offset.set(x/page.image.width,1-(y+h)/page.image.height);t.generateMipmaps=false;t.minFilter=page.magFilter;t.needsUpdate=true;cache.set(key,t);}s.material.map=t;s.material.needsUpdate=true;});}
 apply(clock.seek(0));return {root,back,front,seek(ms){apply(clock.seek(ms));},advance(ms){apply(clock.advance(ms));},get ended(){return clock.ended;},destroy(){root.removeFromParent();for(const s of sprites)s.material.dispose();for(const t of cache.values())t.dispose();root.clear();}};
}
`;
export const COCOS_VFX_ADAPTER=`// Cocos Creator 3.8 candidate. Load atlas Texture2D objects in the project; supply verified straight-alpha materials.
  import {Node,Sprite,SpriteFrame,UITransform,Rect,Size,Vec2,Material,Texture2D} from 'cc';
  import {createVfxClock,checkPage} from './vfx-clock.mjs';
  export function createCocosVfxPlayer(manifest:any,pages:Map<string,Texture2D>,materials:{normal:Material,additive:Material}){
 const clock=createVfxClock(manifest),m=clock.manifest;for(const e of m.effects){if(!materials[e.blend as 'normal'|'additive'])throw Error('Material required: '+e.blend);for(const f of e.frames)checkPage(pages.get(f.page),f);}
 const root=new Node('NhonLeVfx'),back=new Node('back'),front=new Node('front');root.addChild(back);root.addChild(front);const cache=new Map<string,SpriteFrame>();const sprites=m.effects.map((e:any)=>{const n=new Node(e.id);(e.depth==='back'?back:front).addChild(n);n.setPosition(-m.origin[0],m.origin[1],0);const ui=n.addComponent(UITransform);ui.setAnchorPoint(0,1);ui.setContentSize(m.canvas[0],m.canvas[1]);const s=n.addComponent(Sprite);s.sizeMode=Sprite.SizeMode.CUSTOM;s.trim=false;s.customMaterial=materials[e.blend as 'normal'|'additive'];return s;});
 function apply(rows:any[]){rows.forEach(({frame},i)=>{const s=sprites[i];s.node.active=!!frame;if(!frame)return;const key=frame.page+':'+frame.rect.join(',');let f=cache.get(key);if(!f){f=new SpriteFrame();f.texture=pages.get(frame.page)!;f.rect=new Rect(frame.rect[0],frame.rect[1],frame.rect[2],frame.rect[3]);f.originalSize=new Size(m.canvas[0],m.canvas[1]);f.offset=new Vec2(0,0);cache.set(key,f);}s.spriteFrame=f;});}
 apply(clock.seek(0));return {root,back,front,seek(ms:number){apply(clock.seek(ms));},advance(ms:number){apply(clock.advance(ms));},get ended(){return clock.ended;},destroy(){root.destroy();for(const f of cache.values())f.destroy();}};
}
`;
// Import supplies Texture2D pages and pipeline-specific materials; no assumed Resources/URL layout.
export const UNITY_VFX_ADAPTER=`// Unity 6 candidate. Compile and test in your project before runtime approval.
using System;
using System.Collections.Generic;
using UnityEngine;
public sealed class NhonLeVfxPlayer : MonoBehaviour {
 [Serializable] public sealed class Frame { public string page; public int[] rect; public float time_ms, duration_ms; }
 [Serializable] public sealed class Track { public string id, depth, blend; public Frame[] frames; }
 [Serializable] public sealed class Manifest { public string schema, coordinate_space; public int[] canvas; public float[] origin; public float duration_ms; public bool loop; public Track[] effects; }
 public float pixelsPerUnit=100f; public string sortingLayer="Default"; public int bodySortingOrder=0;
 public Material normalMaterial, additiveMaterial; public bool autoAdvance=false;
 Manifest manifest; float elapsed; readonly List<SpriteRenderer> renderers=new List<SpriteRenderer>();
 readonly Dictionary<string,Sprite> sprites=new Dictionary<string,Sprite>();
 public bool Ended { get { return manifest!=null && !manifest.loop && elapsed>=manifest.duration_ms; } }
 public void Initialize(string json, IDictionary<string,Texture2D> pages) {
  if(manifest!=null)throw new InvalidOperationException("Create a new player to change packs");
  var m=JsonUtility.FromJson<Manifest>(json);
  if(m==null||m.schema!="nhon-le-vfx-baked/v1"||m.coordinate_space!="actor_canvas_baked"||m.canvas==null||m.canvas.Length!=2||m.origin==null||m.origin.Length!=2||m.canvas[0]<=0||m.canvas[1]<=0||!Finite(m.origin[0])||!Finite(m.origin[1])||!Finite(m.duration_ms)||m.duration_ms<=0||m.effects==null||!Finite(pixelsPerUnit)||pixelsPerUnit<=0)throw new ArgumentException("Invalid VFX manifest or scale");
  var ids=new HashSet<string>();
  foreach(var e in m.effects){if(e==null||String.IsNullOrEmpty(e.id)||!ids.Add(e.id)||(e.blend!="normal"&&e.blend!="additive")||(e.depth!="back"&&e.depth!="front")||e.frames==null||e.frames.Length==0)throw new ArgumentException("Invalid track");
   if((e.blend=="additive"?additiveMaterial:normalMaterial)==null)throw new ArgumentException("Assign project-owned straight-alpha materials");
   float end=0;foreach(var f in e.frames){Texture2D page;if(f==null||f.page==null||f.rect==null||f.rect.Length!=4||f.rect[0]<0||f.rect[1]<0||f.rect[2]!=m.canvas[0]||f.rect[3]!=m.canvas[1]||!Finite(f.time_ms)||!Finite(f.duration_ms)||f.duration_ms<=0||f.time_ms<end||f.time_ms+f.duration_ms>m.duration_ms||!pages.TryGetValue(f.page,out page)||page==null||f.rect[0]+f.rect[2]>page.width||f.rect[1]+f.rect[3]>page.height)throw new ArgumentException("Invalid frame/page");end=f.time_ms+f.duration_ms;}}
  try { foreach(var e in m.effects){var n=new GameObject(e.id);n.transform.SetParent(transform,false);var r=n.AddComponent<SpriteRenderer>();r.sharedMaterial=e.blend=="additive"?additiveMaterial:normalMaterial;r.sortingLayerName=sortingLayer;r.sortingOrder=bodySortingOrder+(e.depth=="back"?-1:1);renderers.Add(r);
   foreach(var f in e.frames){var key=f.page+":"+String.Join(",",f.rect);if(sprites.ContainsKey(key))continue;var t=pages[f.page];var rect=new Rect(f.rect[0],t.height-f.rect[1]-f.rect[3],f.rect[2],f.rect[3]);var pivot=new Vector2(m.origin[0]/m.canvas[0],1f-m.origin[1]/m.canvas[1]);sprites[key]=Sprite.Create(t,rect,pivot,pixelsPerUnit,0,SpriteMeshType.FullRect);}}
  manifest=m;SeekMs(0); } catch {ClearOwned();throw;}
 }
 static bool Finite(float v){return !Single.IsNaN(v)&&!Single.IsInfinity(v);}
 public void SeekMs(float ms){if(manifest==null)throw new InvalidOperationException("Initialize first");if(!Finite(ms))throw new ArgumentException("Finite milliseconds required");elapsed=Mathf.Max(0,ms);var t=manifest.loop?elapsed%manifest.duration_ms:elapsed;
  for(var i=0;i<manifest.effects.Length;i++){var r=renderers[i];r.enabled=false;if(Ended)continue;foreach(var f in manifest.effects[i].frames)if(t>=f.time_ms&&t<f.time_ms+f.duration_ms){r.sprite=sprites[f.page+":"+String.Join(",",f.rect)];r.enabled=true;break;}}
 }
 public void AdvanceMs(float ms){if(!Finite(ms)||ms<0)throw new ArgumentException("Nonnegative finite delta required");SeekMs(elapsed+ms);}
 void Update(){if(autoAdvance&&manifest!=null)AdvanceMs(Time.deltaTime*1000f);}
 void ClearOwned(){foreach(var r in renderers)if(r!=null){r.enabled=false;Destroy(r.gameObject);}renderers.Clear();foreach(var s in sprites.Values)if(s!=null)Destroy(s);sprites.Clear();manifest=null;elapsed=0;}
 void OnDestroy(){ClearOwned();}
}
`;
export function enginePackFiles(manifest,target,legacy={}){const targets=selectEngines(target),files={'vfx-clock.mjs':VFX_CLOCK_SOURCE,'vfx-clock.d.mts':VFX_CLOCK_TYPES},sources={canvas:CANVAS_VFX_ADAPTER,phaser:PHASER_VFX_ADAPTER,three:THREE_VFX_ADAPTER,cocos:COCOS_VFX_ADAPTER,unity:UNITY_VFX_ADAPTER,...legacy};for(const t of targets)if(t.file){if(!sources[t.id])throw Error('Adapter source missing: '+t.id);files[t.file]=sources[t.id];}
 files['engine-pack.json']=JSON.stringify({schema:'nhon-le-engine-pack/v1',manifest:'vfx.json',selected_engine:target,targets,geometry:{rect_origin:'top_left',axis:'x_right_y_down',origin:'actor_ground_in_canvas_pixels',coordinates:manifest.coordinate_space,untrimmed_frame_size:manifest.canvas,reattach_to_socket:false},texture:{format:'RGBA PNG',alpha:'straight',color:'sRGB',filtering:'project_owned',mipmaps:'disable_for_atlas_or_add_gutters'},clock:{unit:'milliseconds',interval:'half_open',loop:manifest.loop,events:'game_owned_shared_clock',terminal:'hide_all_tracks'},acceptance:{technical:'candidate_export',visual:'not_reviewed',runtime:'not_tested'}},null,2);
 files['ENGINE-INTEGRATION.md']=ENGINE_GUIDE;return files;}
export const ENGINE_GUIDE=`# Nhon Le portable VFX pack

Every target consumes vfx.json and the same PNG bytes. All adapters are candidates;
no target-engine runtime is approved by export or API-model tests. This is a baked
RGBA flipbook pipeline, not conversion to native GPU particles or shader graphs.
Do not generate gameplay damage or events from rendered frames. Drive seek from
one game-owned clip clock; manifest.events remains the game's event source.
Atlas rects are top-left PNG pixels. Frame canvas is untrimmed; position the actor
at origin, preserve front/back and per-track normal/additive blending. Do not
reattach a baked socket trajectory to a moving socket. Source rig stays editable.

## Canvas / HTML5
Import createCanvasVfxPlayer from canvas-vfx.mjs. Decode every page into a Map.
Use player.seek(clipTimeMs), player.draw(ctx,'back',actorX,actorY), draw the actor,
then player.draw(ctx,'front',actorX,actorY). It preserves context state and does
not clear the canvas. Use a project-owned loader and requestAnimationFrame loop.

## Phaser 3
In preload, fetch/load the JSON before queuing PNGs or use a scene with manifest
already available. preloadPhaserVfx(scene,manifest,absoluteBaseUrl,uniquePackKey)
queues scene.load.image and returns pageKeys. In create call
createPhaserVfxPlayer(Phaser,scene,manifest,pageKeys). Insert actor between back
and front with root.addAt(actor,1). Call seek(gameClipTimeMs) in update; Phaser's
delta is milliseconds. Pages are borrowed; destroy frees only player frame names.

## Three.js
Load each PNG using TextureLoader into a Map; require flipY=true. Instantiate
createThreeVfxPlayer(THREE,manifest,pages,{pixelsPerUnit:100}). Use an orthographic
camera facing the XY plane, identity actor rotation and body renderOrder=0;
tracks have -1/+1. This is a camera-facing sprite overlay, not perspective/world
mesh animation. Cloned PNG textures use SRGBColorSpace and materials disable tone mapping.
Renderer output color space, alpha and transparency ordering are project-owned. Pages are borrowed; destroy frees cloned textures/materials.
Use LinearFilter/NearestFilter consistently; mipmaps are disabled for cropped pages.

## Unity 6
Copy NhonLeVfxPlayer.cs into Assets. Create one component per clip pack; load JSON
and Texture2D pages using your existing importer/Addressables/Resources/URL loader,
then Initialize(json,pages). PNG pixels/size must be unchanged by platform imports;
disable compression/resizing/mipmaps and choose filtering. Set pixelsPerUnit and
bodySortingOrder to the actor's values. Assign normalMaterial/additiveMaterial
for the project's Built-in/URP pipeline with straight-alpha blending; both sample
_MainTex. Do not use a premultiplied-alpha material for straight PNG bytes.
Call SeekMs(gameClipTimeMs); autoAdvance is optional and defaults false. Sprite
rect Y and pivot are converted to bottom-left/Y-up. Textures/materials are borrowed.
This source has not been compiled or played in a Unity editor in the handoff.

## Cocos Creator 3.8
Copy cocos-vfx.ts and vfx-clock.mjs into the project; enable importing JS modules
or provide matching declarations. Pass the JSON, Map<string,Texture2D> atlas
pages and project-owned normal/additive Material objects to createCocosVfxPlayer.
The player creates 2D Sprite/UITransform nodes with top-left anchor and Y-up
placement. Put the actor between back and front via sibling order; all three
must share compatible Canvas/layer/masks. Call seek(gameClipTimeMs), or
advance(dtSeconds*1000). Texture import must preserve PNG size and straight alpha.
Custom materials should use Cocos's sprite texture binding; pages/materials are
borrowed, generated SpriteFrames are destroyed with the player. Engine/editor
compilation and rendered mobile playback still require project validation.

## Godot 4 / PixiJS 8
Existing godot-vfx.gd and pixi-vfx.mjs retain their interfaces. Godot attaches to
Node2D at actor ground origin; configure z ordering for the body. Pixi returns
root/back/front; insert body between them. Both preserve millisecond timing and
hide completed one-shots. Adapt the Godot automatic process if using a shared
combat clock; never run two independent clocks for actor and impact effects.

## Other engines
Use generic target for Unreal/Paper2D, Defold, LÖVE, Bevy, custom engines, editors
and any tool accepting PNG. This delivers PNG + origin/time/blend/depth JSON,
not a native importer for those engines. Map top-left rectangles, coordinate Y,
scale, per-frame duration, alpha and event clock explicitly. Add a registered
adapter and meaningful tests before advertising it as an adapter-supported target.

## Acceptance
Check asymmetric atlas cells (not only row zero), origin, loop boundary, exact
terminal hide, seek backwards, before/after body, normal/additive on dark/light,
import scaling/filtering/color space, clip transitions and device performance.
Bind actual engine evidence with the bundled skill's VFX runtime workflow.
Keep runtime not_tested until that target/version and evidence are verified.
`;
