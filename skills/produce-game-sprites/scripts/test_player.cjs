/* DOM/canvas contract tests. These do not replace real browser visual review. */
const assert=require('node:assert/strict'), fs=require('node:fs'), vm=require('node:vm'), path=require('node:path');
const template=fs.readFileSync(path.join(__dirname,'../assets/player.html'),'utf8');
const frames=[80,170,50].map((duration_ms,i)=>({id:'f'+i,duration_ms}));
const manifest={cell_size:[24,32],origin:[12,29],representation:'pixel',clips:[
  {name:'loop',loop:true,frames,events:[{name:'hit',time_ms:80}]},
  {name:'one',loop:false,frames,events:[]}
]};
const source=template.replace('__SPRITE_DATA__',JSON.stringify({manifest,images:{f0:'stub0',f1:'stub1',f2:'stub2'}}));
const canvasCalls=[];
const ctx={fillRect(){},beginPath(){},moveTo(){},lineTo(){},stroke(){},drawImage(...args){canvasCalls.push(args);}};
const els={};
for(const id of ['clip','zoom','bg','onion','guides','time','canvas','state','events','play','reset','prev','next','data']){
  els[id]={value:'',checked:false,textContent:'',append(){}};
}
els.zoom.value='1';els.bg.value='checker';els.guides.checked=true;
els.data.textContent=JSON.stringify({manifest,images:{f0:'stub0',f1:'stub1',f2:'stub2'}});
els.canvas.getContext=()=>ctx;
let raf=null;
class FakeImage {set src(v){this._src=v;this.onload();}}
const sandbox={document:{getElementById:id=>els[id],createElement:()=>({})},Image:FakeImage,console,
  requestAnimationFrame:fn=>{raf=fn;}};
sandbox.window=sandbox;
const context=vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../assets/timeline.js'),'utf8'),context);
const scripts=[...source.matchAll(/<script(?: [^>]*)?>([\s\S]*?)<\/script>/g)].map(x=>x[1]).filter(x=>x.trim()&&!x.trim().startsWith('{'));
vm.runInContext(scripts.at(-1),context);
(async()=>{
  await new Promise(resolve=>setImmediate(resolve));
  const preview=sandbox.spritePreview;
  assert.equal(preview.status.ready,true);
  assert.equal(preview.status.index,0);
  assert.equal(els.canvas.width,24);assert.equal(els.canvas.height,32);
  assert.equal(ctx.imageSmoothingEnabled,false);
  els.next.onclick();assert.equal(preview.status.index,1);assert.equal(preview.status.time,80);
  els.prev.onclick();assert.equal(preview.status.index,0);
  els.zoom.value='4';els.zoom.onchange();assert.equal(els.canvas.width,96);
  assert.equal(canvasCalls.at(-1)[3],96);
  preview.selectClip('one');preview.setTime(999);
  assert.equal(preview.status.ended,true);assert.equal(preview.status.index,2);
  assert.match(els.state.textContent,/terminal hold/);
  els.play.onclick();assert.equal(preview.status.playing,true);assert.equal(preview.status.elapsed,0);
  raf(100);raf(180);assert.equal(preview.status.index,1);
  raf(400);assert.equal(preview.status.playing,false);assert.equal(preview.status.ended,true);
  preview.selectClip('loop');els.play.onclick();raf(500);raf(800);
  assert.equal(preview.status.index,0);assert.equal(preview.status.playing,true);
  els.play.onclick();assert.equal(preview.status.playing,false);
  els.time.value='250';els.time.oninput();assert.equal(preview.status.index,2);
  els.reset.onclick();assert.equal(preview.status.elapsed,0);
  console.log('23 DOM/canvas assertions passed (mocked; browser visual review not performed)');
})().catch(e=>{console.error(e);process.exit(1);});
