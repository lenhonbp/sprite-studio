/* Actual PixiJS parser/AnimatedSprite smoke test; no rendered-browser approval.
   Usage: node check_pixi.cjs RELEASE ATLAS_RGBA_FILE [PIXI_MODULE_PATH]
   Decode each atlas PNG to raw RGBA first; pass a directory for multiple pages. Never installs a runtime. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {pathToFileURL}=require('node:url'),{createRequire}=require('node:module');
(async()=>{
  const [rawRelease,rawRGBA,modulePath]=process.argv.slice(2);
  if(!rawRelease||!rawRGBA)throw new Error('Pass release directory and decoded atlas RGBA path');
  const release=path.resolve(rawRelease);
  const PIXI=modulePath?require(path.resolve(modulePath)):createRequire(path.join(process.cwd(),'package.json'))('pixi.js');
  if(!PIXI.VERSION.startsWith('8.'))throw new Error('This smoke test targets PixiJS v8');
  const timeline=JSON.parse(fs.readFileSync(path.join(release,'animations.json'),'utf8'));
  const pages=timeline.atlases || [{data:'pixi-atlas.json',image:'atlas.png'}];
  const textures={},animations={},sheets=[];
  for(const page of pages){
    const data=JSON.parse(fs.readFileSync(path.join(release,page.data),'utf8'));
    const {w:width,h:height}=data.meta.size;
    const rawFile=fs.statSync(rawRGBA).isDirectory()?path.join(rawRGBA,path.basename(page.image,'.png')+'.rgba'):rawRGBA;
    assert.ok(pages.length===1||fs.statSync(rawRGBA).isDirectory(),'Multipage requires decoded RGBA directory');
    const bytes=fs.readFileSync(rawFile);assert.equal(bytes.length,width*height*4);
    const source=new PIXI.BufferImageSource({resource:new Uint8Array(bytes),width,height,scaleMode:timeline.representation==='hd'?'linear':'nearest'});
    const parsed=new PIXI.Spritesheet(new PIXI.Texture({source}),data);await parsed.parse();sheets.push(parsed);
    for(const [id,tex] of Object.entries(parsed.textures)){assert.ok(!textures[id],'Duplicate frame across pages');textures[id]=tex;}
  }
  for(const clip of timeline.clips)animations[clip.name]=clip.frames.map(f=>textures[f.id]);
  const sheet={textures,animations};
  const {createTimedSprite}=await import(pathToFileURL(path.join(release,'pixi-adapter.mjs')));
  for(const clip of timeline.clips){
    assert.equal(sheet.animations[clip.name].length,clip.frames.length);
    for(const frame of clip.frames){
      const tex=sheet.textures[frame.id];
      assert.equal(tex.orig.width,timeline.cell_size[0]);assert.equal(tex.orig.height,timeline.cell_size[1]);
      assert.equal(tex.defaultAnchor.x,timeline.origin[0]/timeline.cell_size[0]);
      assert.equal(tex.defaultAnchor.y,timeline.origin[1]/timeline.cell_size[1]);
    }
    const sprite=createTimedSprite(PIXI,sheet,timeline,clip.name);
    assert.equal(sprite.loop,clip.loop);assert.equal(sprite.autoUpdate,false);
    sprite.play();
    let accumulated=0, boundary=0;
    const total=clip.frames.reduce((n,f)=>n+f.duration_ms,0);
    for(let i=0;i<clip.frames.length;i++){
      assert.equal(sprite.currentFrame,i);
      // Midpoints exercise each interval without boundary round-off ambiguity.
      boundary+=clip.frames[i].duration_ms;
      const next=boundary+0.001;
      sprite.update({deltaTime:(next-accumulated)*60/1000});
      accumulated=next;
    }
    if(clip.loop){assert.equal(sprite.playing,true);assert.equal(sprite.currentFrame,0);}
    else{assert.equal(sprite.playing,false);assert.equal(sprite.currentFrame,clip.frames.length-1);}
    sprite.destroy();
  }
  for(const parsed of sheets)parsed.destroy(true);
  console.log(JSON.stringify({status:'headless_pass',engine:'PixiJS',version:PIXI.VERSION,
    checks:['Spritesheet parse','atlas geometry/anchor','per-frame timing','loop/terminal playback'],
    visual_status:'not_tested',gameplay_events:'not_tested'}));
})().catch(e=>{console.error(e);process.exit(1);});
