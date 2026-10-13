import assert from 'node:assert/strict';
import fs from 'node:fs/promises';import os from 'node:os';import path from 'node:path';
import {spawn} from 'node:child_process';import {randomUUID} from 'node:crypto';
import {createLocalApp} from './local/server.mjs';import {workspace,root,options} from './local/workspace.mjs';
import {lockInfo,unlockDead} from './local/disk-bucket.mjs';
const dir=await fs.mkdtemp(path.join(os.tmpdir(),'studio-local-'));
function processRun(file,args=[],input){return new Promise((resolve,reject)=>{const child=spawn(process.execPath,[path.join(root,file),...args],{stdio:['pipe','pipe','pipe']});let out='',err='';const timeout=setTimeout(()=>{child.kill();reject(Error('Child timeout'));},20000);child.stdout.on('data',x=>out+=x);child.stderr.on('data',x=>err+=x);child.on('error',reject);child.on('close',code=>{clearTimeout(timeout);resolve({code,out,err});});child.stdin.end(input);});}
const cli=(args)=>processRun('local/studio-cli.mjs',[...args,'--data',dir]);
const command=(revision,id=randomUUID())=>({baseRevision:revision,requestId:id,operations:[{type:'bone-key',clip:'idle_se',bone:'root',time:250,values:{rotation:12}}]});
try{
 assert.throws(()=>options(['--data']),/đường dẫn/);
 const app=await createLocalApp(dir),base='http://127.0.0.1:8787';
 const page=await app.fetch(new Request(base+'/'));assert.equal(page.status,200);assert.match(await page.text(),/v4.1.1 Local/);
 const cookie=page.headers.get('set-cookie').split(';')[0];
 const api=async(name,args={})=>app.fetch(new Request(base+'/api/studio',{method:'POST',headers:{cookie,'content-type':'application/json'},body:JSON.stringify({name,args})}));
 assert.equal((await app.fetch(new Request(base+'/api/studio',{method:'POST',body:'{}'}))).status,401);
 assert.equal((await app.fetch(new Request(base+'/',{headers:{origin:'https://evil.example'}}))).status,403);
 assert.equal((await app.fetch(new Request('http://evil.example/'))).status,403);
 let read=await (await api('studio_read')).json();assert.equal(read._meta.studio.projectRevision,0);
 const argsFile=path.join(dir,'args.json');await fs.writeFile(argsFile,JSON.stringify(command(0,'first-edit')));
 let result=await cli(['call','studio_edit','--args-file',argsFile]);assert.equal(result.code,0,result.err);assert.equal(JSON.parse(result.out).revision,1);
 read=await (await api('studio_poll',{knownVersion:0})).json();assert.equal(read._meta.studio.projectRevision,1);
 const project=read._meta.studio.project;project.name='Edited in editor';
 assert.equal((await api('studio_replace',{project,baseRevision:1,requestId:'manual-edit'})).status,200);
 result=await cli(['read']);assert.equal(JSON.parse(result.out).project.name,'Edited in editor');
 // Independent processes must never both accept the same base revision.
 const otherFile=path.join(dir,'other.json');await fs.writeFile(argsFile,JSON.stringify(command(2,'race-a-edit')));await fs.writeFile(otherFile,JSON.stringify(command(2,'race-b-edit')));
 const races=await Promise.all([cli(['call','studio_edit','--args-file',argsFile]),cli(['call','studio_edit','--args-file',otherFile])]);assert.equal(races.filter(r=>r.code===0).length,1);assert.equal(JSON.parse(races.find(r=>r.code!==0).err).status,409);
 const requests=[{jsonrpc:'2.0',id:1,method:'initialize',params:{protocolVersion:'2025-11-25'}},{jsonrpc:'2.0',method:'notifications/initialized'},{jsonrpc:'2.0',id:2,method:'tools/list'},{jsonrpc:'2.0',id:3,method:'tools/call',params:{name:'studio_edit',arguments:command(3,'mcp-edit')}},{jsonrpc:'2.0',id:4,method:'tools/call',params:{name:'studio_read',arguments:{}}}];
 result=await processRun('local/mcp-stdio.mjs',['--data',dir],requests.map(q=>JSON.stringify(q)).join('\n')+'\n');assert.equal(result.code,0,result.err);
 const replies=result.out.trim().split('\n').map(JSON.parse);assert.equal(replies.length,4);assert.equal(replies[0].result.protocolVersion,'2025-11-25');assert.equal(replies[1].result.tools.length,9);assert.equal(replies[3].result.structuredContent.revision,4);
 read=await (await api('studio_poll',{knownVersion:3})).json();assert.equal(read._meta.studio.projectRevision,4);
 assert.equal((await api('studio_undo',{baseRevision:4,requestId:'undo-edit'})).status,200);
 assert.equal((await (await workspace(dir)).call('studio_read')).projectRevision,5);
 const restarted=await createLocalApp(dir);assert.equal((await restarted.ws.call('studio_read')).projectRevision,5);
 assert.equal((await restarted.fetch(new Request(base+'/api/studio',{method:'POST',headers:{cookie},body:'{}'}))).status,401);
 const exported=path.join(dir,'export.json');assert.equal((await cli(['export',exported])).code,0);assert.notEqual((await cli(['export',exported])).code,0);
 assert.notEqual((await cli(['import',exported])).code,0);assert.equal((await cli(['import',exported,'--revision','5'])).code,0);
 await fs.writeFile(path.join(dir,'write.lock'),JSON.stringify({pid:process.pid}));assert.equal((await lockInfo(dir)).active,true);await assert.rejects(()=>unlockDead(dir),/vẫn hoạt động/);await fs.unlink(path.join(dir,'write.lock'));
 await fs.writeFile(path.join(dir,'write.lock'),JSON.stringify({pid:2147483647}));assert.equal(await unlockDead(dir),true);
 await fs.writeFile(path.join(dir,'state.json'),'broken');await assert.rejects(()=>(async()=>{const ws=await workspace(dir);return ws.call('studio_read');})());assert.equal(await fs.readFile(path.join(dir,'state.json'),'utf8'),'broken');
 console.log('Local passed: editor API ↔ CLI ↔ MCP stdio; cross-process CAS, restart, auth, import/export, lock, corrupt-state retention.');
}finally{await fs.rm(dir,{recursive:true,force:true});}
