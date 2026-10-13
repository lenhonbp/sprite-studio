#!/usr/bin/env node
/** Run actual local PixiJS/Chromium; no downloads, fabricated baseline or empty success. */
import {createServer} from 'node:http';
import {readFile,writeFile,mkdir,realpath} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';

export function validateResult(timeline, result) {
  if (!result || typeof result !== 'object') return ['Missing engine result'];
  const errors = Array.isArray(result.errors) ? [...result.errors] : ['Engine error list missing'];
  const expected = timeline.clips.flatMap(c => c.frames.map((f,index) => ({clip:c.name,id:f.id,index,duration_ms:f.duration_ms})));
  if (!expected.length) errors.push('No expected frames');
  const actual = Array.isArray(result.frames) ? result.frames : [];
  if (actual.length !== expected.length) errors.push('Rendered frame count differs from complete timeline');
  for (let i=0;i<expected.length;i++) {
    const a=actual[i], e=expected[i];
    if (!a || ['clip','id','index','duration_ms'].some(k => a[k]!==e[k])) errors.push('Frame/order/timing mismatch at '+i);
    if (a && (a.width!==timeline.cell_size[0] || a.height!==timeline.cell_size[1] || a.differentPixels || !a.visiblePixels || !a.png?.startsWith('data:image/png;base64,'))) errors.push('Invalid rendered evidence at '+i);
  }
  if (typeof result.version!=='string' || !result.version.startsWith('8.')) errors.push('Actual PixiJS v8 version missing');
  return errors;
}

async function main() {
  const args=process.argv.slice(2), option=name=>args[args.indexOf(name)+1];
  for (const key of ['--release','--pixi-build','--out']) if (!args.includes(key) || !option(key)) throw new Error('Required '+key);
  const release=await realpath(option('--release')), engine=await realpath(option('--pixi-build'));
  const output=path.resolve(option('--out')), assets=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../assets');
  const identity=JSON.parse(await readFile(path.join(release,'export-manifest.json'),'utf8'));
  for (const [name,hash] of Object.entries(identity.files)) {
    if (path.basename(name)!==name) throw new Error('Unsafe export path');
    const bytes=await readFile(path.join(release,name));
    if (createHash('sha256').update(bytes).digest('hex')!==hash) throw new Error('Changed export '+name);
  }
  const timeline=JSON.parse(await readFile(path.join(release,'animations.json'),'utf8'));
  if (!Array.isArray(timeline.clips) || !timeline.clips.length) throw new Error('Nonempty clip array required');
  let playwright;
  try {playwright=createRequire(path.join(process.cwd(),'package.json'))(args.includes('--playwright-module')?path.resolve(option('--playwright-module')):'playwright');} catch {throw new Error('Project must supply playwright and Chromium; no engine/browser was downloaded');}
  const server=createServer(async(req,res)=>{
    try {
      const u=new URL(req.url,'http://127.0.0.1'); let file,root;
      if(u.pathname==='/engine.js') file=engine;
      else if(u.pathname==='/harness.html') file=path.join(assets,'pixi-runtime-harness.html');
      else if(u.pathname.startsWith('/release/')) {root=release;file=await realpath(path.join(root,decodeURIComponent(u.pathname.slice(9))));
        const rel=path.relative(root,file);if(rel.startsWith('..')||path.isAbsolute(rel))throw new Error('Path outside release');}
      else {res.writeHead(404);res.end();return;}
      const bytes=await readFile(file);const ext=path.extname(file);
      res.writeHead(200,{'Content-Type':({'.html':'text/html','.mjs':'text/javascript','.js':'text/javascript','.json':'application/json','.png':'image/png'})[ext]||'application/octet-stream'});res.end(bytes);
    } catch {res.writeHead(404);res.end();}
  });
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
  let browser;
  try {
    browser=await playwright.chromium.launch({headless:true,...(args.includes('--chromium')?{executablePath:option('--chromium')}:{})});
    const page=await browser.newPage(), pageErrors=[];page.on('pageerror',e=>pageErrors.push(String(e)));
    await page.goto(`http://127.0.0.1:${server.address().port}/harness.html`);
    await page.waitForFunction(()=>window.__HARNESS_DONE__===true,null,{timeout:120000});
    const result=await page.evaluate(()=>window.__HARNESS_RESULT__);
    result.errors=(result.errors||[]).concat(pageErrors);
    const errors=validateResult(timeline,result);
    await mkdir(output,{recursive:false});
    const captured = Array.isArray(result.frames)?result.frames:[];
    for (let i=0;i<captured.length;i++) {
      const f=captured[i]; if(typeof f.png!=='string' || !f.png.startsWith('data:image/png;base64,')) continue;
      const filename=`frame-${String(i).padStart(5,'0')}.png`;
      await writeFile(path.join(output,filename),Buffer.from(f.png.split(',')[1],'base64'));f.capture=filename;delete f.png;
    }
    const report={...result,status:errors.length?'blocked':'rendered_engine_pass',errors,source_binding:identity.binding,
      export_manifest_sha256:createHash('sha256').update(await readFile(path.join(release,'export-manifest.json'))).digest('hex')};
    await writeFile(path.join(output,'runtime-render.json'),JSON.stringify(report,null,2));
    console.log(JSON.stringify({status:report.status,frames:captured.length,errors,output}));process.exitCode=errors.length?1:0;
  } finally {await browser?.close();await new Promise(resolve=>server.close(resolve));}
}
if(process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) main().catch(e=>{console.error(JSON.stringify({status:'invalid_input_or_environment',error:String(e)}));process.exitCode=2;});
