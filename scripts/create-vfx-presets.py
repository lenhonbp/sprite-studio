"""Small authored procedural texture samples; never replaces character art."""
from PIL import Image
from pathlib import Path
import math,io,base64,json
root=Path(__file__).resolve().parent.parent
textures={}
for name in ['soft_glow','spark_brush','smoke_brush']:
 im=Image.new('RGBA',(64,64))
 for y in range(64):
  for x in range(64):
   dx=(x-31.5)/31.5;dy=(y-31.5)/31.5
   if name=='soft_glow': a=max(0,1-math.hypot(dx,dy))**2
   elif name=='spark_brush':a=max(0,1-math.sqrt((dx*.5)**2+(dy*3.2)**2))**1.5
   else:a=max(0,1-math.hypot(dx,dy))**1.2*(.7+.3*math.sin(x*.38)*math.cos(y*.21))
   im.putpixel((x,y),(255,255,255,round(a*255)))
 out=io.BytesIO();im.save(out,format='PNG');textures[name]={'image':'data:image/png;base64,'+base64.b64encode(out.getvalue()).decode(),'width':64,'height':64,'pivot':[32,32]}
(root/'skills/produce-game-sprites/tools/rig-animation/assets/vfx-presets.mjs').write_text('export const FX_TEXTURES='+json.dumps(textures)+';\n'+'''export function effectPreset(kind,id=kind){
 const base={id:'layer_1',kind:'particles',texture:'soft_glow',start_ms:0,end_ms:700,offset:[0,0],rotation:0,size:[[0,18],[.15,28],[1,0]],alpha:[[0,1],[.3,.9],[1,0]],color:[255,210,115],count:24,emit_ms:0,life_ms:650,speed:130,angle:0,spread:360,gravity:60,radius:3};
 if(kind==='aura'){Object.assign(base,{end_ms:1200,emit_ms:1000,life_ms:200,speed:-20,radius:36,color:[110,185,255],count:40,alpha:[[0,0],[.2,.8],[1,0]],size:[[0,8],[.5,13],[1,2]]});}
 if(kind==='slash'){Object.assign(base,{kind:'trail',texture:'spark_brush',end_ms:600,color:[130,220,255],width:24,history_ms:180,samples:40,size:[[0,24],[1,4]],alpha:[[0,.9],[1,0]]});for(const k of ['count','emit_ms','life_ms','speed','angle','spread','gravity','radius'])delete base[k];}
 if(kind==='smoke'){Object.assign(base,{texture:'smoke_brush',end_ms:1000,emit_ms:200,life_ms:800,speed:35,angle:-90,spread:60,gravity:-20,radius:12,color:[130,140,160],size:[[0,12],[1,65]],alpha:[[0,0],[.15,.65],[1,0]]});}
 return {id,name:kind,duration_ms:base.end_ms,loop:kind==='aura',blend:kind==='smoke'?'normal':'additive',seed:12345,layers:[base]};
}
''')
