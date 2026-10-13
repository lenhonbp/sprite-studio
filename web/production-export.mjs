import {validateProject,samplePose,scheduleFrames,sheetLayout} from './rig-core.mjs';
import {sampleEffects,drawEffects,studioReport} from './studio-core.mjs';
import {enginePackFiles,selectEngines} from './engine-adapters.mjs';
export function sourceBundleFiles(project){validateProject(project);const p=structuredClone(project),files={};for(const [id,a]of Object.entries(p.attachments)){const path='images/'+id+'.png';files[path]=Uint8Array.from(atob(a.image.split(',')[1]),c=>c.charCodeAt(0));a.image_file=path;delete a.image;}files['source.json']=JSON.stringify({schema:'nhon-le-source-bundle/v1',project:p},null,2);return files;}
export async function vfxFiles(p,clipId,fps,backend,maxPixels=64000000,engine='all'){selectEngines(engine);validateProject(p);studioReport(p);const c=p.clips.find(c=>c.id===clipId);if(!c)throw Error('Clip missing');const schedule=scheduleFrames({...c,loop:true},fps),effects=p.studio?.effects.filter(f=>p.studio.bindings.some(b=>b.clip===clipId&&b.effect===f.id))??[];if(!effects.length)throw Error('Clip chưa có VFX');const groups=effects.reduce((n,f)=>n+new Set(p.studio.bindings.filter(b=>b.clip===clipId&&b.effect===f.id).map(b=>b.depth)).size,0);if(schedule.length*groups*p.canvas[0]*p.canvas[1]>maxPixels)throw Error('VFX export pixel budget exceeded');const {createCanvas,images,encode,tint}=backend,files={},manifest={schema:'nhon-le-vfx-baked/v1',clip:clipId,canvas:p.canvas,origin:p.origin,fps,duration_ms:c.duration_ms,loop:c.loop,events:c.events??[],coordinate_space:'actor_canvas_baked',visual:'not_reviewed',runtime:'not_tested',effects:[]},cell=createCanvas(...p.canvas),cx=cell.getContext('2d');
 for(const f of effects){for(const depth of ['back','front']){const bindings=p.studio.bindings.filter(b=>b.clip===clipId&&b.effect===f.id&&b.depth===depth);if(!bindings.length)continue;const row={id:f.id+'_'+depth,effect:f.id,depth,blend:f.blend,bindings,frames:[]};for(const [pi,page]of sheetLayout(p.canvas,schedule.length).entries()){const atlas=createCanvas(page.width,page.height),ax=atlas.getContext('2d'),file=row.id+'-'+pi+'.png';for(const rect of page.frames){const frame=schedule[rect.index];cx.clearRect(0,0,...p.canvas);drawEffects(cx,sampleEffects(p,clipId,frame.time_ms,samplePose,depth,f.id),images,tint);const rgba=cx.getImageData(0,0,...p.canvas);ax.putImageData(rgba,rect.x,rect.y);let nonempty=false;for(let ai=3;ai<rgba.data.length;ai+=4)if(rgba.data[ai]){nonempty=true;break;}const frameFile='frames/'+row.id+'/'+String(frame.index).padStart(4,'0')+'.png';files[frameFile]=await encode(cell);row.frames.push({empty:!nonempty,path:frameFile,page:file,rect:[rect.x,rect.y,rect.w,rect.h],time_ms:frame.time_ms,duration_ms:frame.duration_ms});}files[file]=await encode(atlas);}const first=row.frames.findIndex(r=>!r.empty);if(first<0)throw Error('Effect track has no visible baked frames: '+row.id);let last=row.frames.length-1;while(row.frames[last].empty)last--;for(const [i,r]of row.frames.entries())if(i<first||i>last)delete files[r.path];row.frames=row.frames.slice(first,last+1);row.active_start_ms=row.frames[0].time_ms;row.active_end_ms=row.frames.at(-1).time_ms+row.frames.at(-1).duration_ms;manifest.effects.push(row);files[row.id+'-contract.json']=JSON.stringify({schema_version:1,vfx_id:row.id,representation:p.representation,attachment_space:'actor',loop:c.loop,blend_intent:f.blend,alpha_policy:'soft',cell_size:p.canvas,clip_duration_ms:c.duration_ms,active_start_ms:row.active_start_ms,active_end_ms:row.active_end_ms,clip_events:c.events??[],frames:row.frames.map((r,i)=>({id:'frame_'+i,path:r.path,duration_ms:r.duration_ms})),events:{},performance_budget:{max_simultaneous_instances:1,allow_large_transparent_canvas:true}},null,2);}}
 files['vfx.json']=JSON.stringify(manifest,null,2);files['source.rig.json']=JSON.stringify(p,null,2);files['README.txt']='Candidate baked VFX. Actor canvas coordinates: align origin with actor origin, do not reattach baked motion to socket. Each effect keeps its blend mode. Frames are half-open intervals; gameplay events remain separate. Engine adapters are candidates requiring target-engine QA. Do not bake character and additive VFX into the same normal-blended texture.';Object.assign(files,enginePackFiles(manifest,engine,{pixi:PIXI_VFX_ADAPTER,godot:GODOT_VFX_ADAPTER}));return {files,manifest};
}
// Adapters consume authored millisecond durations instead of a fixed animationSpeed.
export const PIXI_VFX_ADAPTER=`// PixiJS v8 candidate adapter. Pass your imported PIXI namespace and extracted pack base URL.
  export async function createVfxPlayer(PIXI, baseUrl, manifest){
 const root=new PIXI.Container(), back=new PIXI.Container(), front=new PIXI.Container(), pages=new Map(), cache=new Map(), sprites=[];
 root.addChild(back,front);
 for(const e of manifest.effects){for(const f of e.frames)if(!pages.has(f.page))pages.set(f.page,await PIXI.Assets.load(new URL(f.page,baseUrl).href));
 const sprite=new PIXI.Sprite();sprite.position.set(-manifest.origin[0],-manifest.origin[1]);sprite.blendMode=e.blend==='additive'?'add':'normal';(e.depth==='back'?back:front).addChild(sprite);sprites.push([e,sprite]);}
 let elapsed=0,ended=false;
 function seek(ms){elapsed=Math.max(0,ms);ended=!manifest.loop&&elapsed>=manifest.duration_ms;const t=manifest.loop?elapsed%manifest.duration_ms:elapsed;
 for(const [e,sprite]of sprites){const f=e.frames.find(f=>t>=f.time_ms&&t<f.time_ms+f.duration_ms);sprite.visible=!!f&&!ended;if(!f)continue;const key=f.page+':'+f.rect.join(',');let texture=cache.get(key);if(!texture){texture=new PIXI.Texture({source:pages.get(f.page).source,frame:new PIXI.Rectangle(...f.rect)});cache.set(key,texture);}sprite.texture=texture;}}
 seek(0);return {root,back,front,seek,advance(deltaMs){seek(elapsed+deltaMs);},get ended(){return ended;},destroy(){root.destroy({children:true});for(const t of cache.values())t.destroy(false);}};
}
`;
export const GODOT_VFX_ADAPTER=`# Godot 4 candidate adapter. Attach to Node2D at actor ground origin.
extends Node2D
@export var manifest_path: String = "res://vfx/vfx.json"
var manifest: Dictionary
var elapsed: float = 0.0
var sprites: Array[Sprite2D] = []
var pages: Dictionary = {}
var playing: bool = true
func _ready() -> void:
 manifest = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
 for effect in manifest.effects:
  var sprite := Sprite2D.new()
  sprite.centered = false
  sprite.z_index = -1 if effect.depth == "back" else 1
  sprite.position = -Vector2(manifest.origin[0], manifest.origin[1])
  var mat := CanvasItemMaterial.new()
  mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD if effect.blend == "additive" else CanvasItemMaterial.BLEND_MODE_MIX
  sprite.material = mat
  add_child(sprite)
  sprites.append(sprite)
  for frame in effect.frames:
   if not pages.has(frame.page):
    pages[frame.page] = load(manifest_path.get_base_dir().path_join(frame.page))
 seek_ms(0.0)
func seek_ms(ms: float) -> void:
 elapsed = maxf(ms, 0.0)
 var ended: bool = not manifest.loop and elapsed >= manifest.duration_ms
 var t: float = fmod(elapsed, manifest.duration_ms) if manifest.loop else elapsed
 for i in range(manifest.effects.size()):
  var sprite: Sprite2D = sprites[i]
  sprite.visible = false
  if ended:
   continue
  for frame in manifest.effects[i].frames:
   if t >= frame.time_ms and t < frame.time_ms + frame.duration_ms:
    var texture := AtlasTexture.new()
    texture.atlas = pages[frame.page]
    texture.region = Rect2(frame.rect[0], frame.rect[1], frame.rect[2], frame.rect[3])
    sprite.texture = texture
    sprite.visible = true
    break
func _process(delta: float) -> void:
 if playing:
  seek_ms(elapsed + delta * 1000.0)
`;
