import assert from 'node:assert/strict';import fs from 'node:fs/promises';import os from 'node:os';import path from 'node:path';import http from 'node:http';import {pathToFileURL} from 'node:url';import {spawn} from 'node:child_process';import {randomUUID} from 'node:crypto';
import {serve} from './local/server.mjs';import {workspace,root} from './local/workspace.mjs';import {connectStudio} from './web/agent-bridge.mjs';
const dir=await fs.mkdtemp(path.join(os.tmpdir(),'studio-field-'));let service,base,cookie='';const passed=[];
const run=(file,args=[],input)=>new Promise((resolve,reject)=>{const p=spawn(process.execPath,[path.join(root,file),...args],{stdio:['pipe','pipe','pipe']});let out='',err='';const timer=setTimeout(()=>{p.kill();reject(Error('Child timeout'));},20000);p.stdout.on('data',x=>out+=x);p.stderr.on('data',x=>err+=x);p.on('error',reject);p.on('close',code=>{clearTimeout(timer);resolve({code,out,err});});p.stdin.end(input);});
const cli=args=>run('local/studio-cli.mjs',[...args,'--data',dir]);
const edit=(baseRevision,value,id=randomUUID())=>({baseRevision,requestId:id,operations:[{type:'bone-key',clip:'attack_se',bone:'arm_front',time:300,values:{rotation:value}}]});
const nativeFetch=globalThis.fetch,realInterval=globalThis.setInterval,realTimeout=globalThis.setTimeout;
async function request(url,options={}){const headers=new Headers(options.headers);if(cookie)headers.set('cookie',cookie);headers.set('origin',base);const r=await nativeFetch(base+url,{...options,headers,signal:AbortSignal.timeout(12000)});const set=r.headers.get('set-cookie');if(set)cookie=set.split(';')[0];return r;}
const api=async(name,args={})=>request('/api/studio',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({name,args})});
const read=async()=>(await (await api('studio_read')).json())._meta.studio;
const stop=async()=>{if(service){await new Promise(r=>service.server.close(r));service=null;}};
try{
 service=await serve({directory:dir,port:0});base='http://127.0.0.1:'+service.port;
 let r=await request('/');assert.equal(r.status,200);const page=await r.text();assert.match(page,/Sprite Studio/);assert.match(page,/window.STUDIO_LOCAL=true/);assert.ok(cookie);
 for(const [file,mime]of [['/editor.mjs','javascript'],['/rig-core.mjs','javascript'],['/studio.css','css'],['/demo-project.json','json']]){r=await request(file);assert.equal(r.status,200);assert.match(r.headers.get('content-type'),new RegExp(mime));await r.arrayBuffer();}
 assert.equal((await nativeFetch(base+'/api/studio',{method:'POST',body:'{}'})).status,401);
 assert.equal((await nativeFetch(base+'/',{headers:{origin:'https://foreign.example'}})).status,403);
 const badHost=await new Promise((resolve,reject)=>{const q=http.request(base+'/',{headers:{host:'foreign.example'}},r=>{r.resume();resolve(r.statusCode);});q.on('error',reject);q.end();});assert.equal(badHost,403);
 r=await request('/api/studio',{method:'POST',body:'x'.repeat(5_000_001)});assert.equal(r.status,413);await r.text();assert.equal((await request('/health')).status,200);
 assert.equal((await request('/api/studio')).status,405);assert.equal((await request('/missing')).status,404);passed.push('real HTTP assets, cookie, host/origin, body limit, method, missing route');
 assert.equal((await read()).projectRevision,0);await assert.rejects(()=>fs.access(path.join(dir,'state.json')));
 let rev=0;for(let i=0;i<24;i++){r=await api('studio_edit',edit(rev,i));assert.equal(r.status,200,await r.clone().text());rev=(await r.json())._meta.studio.projectRevision;}
 const record=JSON.parse(await fs.readFile(path.join(dir,'state.json'),'utf8'));assert.equal(record.projectRevision,24);assert.ok(record.past.length<=20);assert.ok(Buffer.byteLength(JSON.stringify([record.past,record.future]))<=8_000_100);
 assert.equal((await api('studio_edit',{...edit(rev,1),operations:[edit(rev,1).operations[0],{type:'NOPE'}]})).status,400);assert.equal((await read()).projectRevision,24);
 const files=await Promise.all(Array.from({length:6},async(_,i)=>{const f=path.join(dir,'race-'+i+'.json');await fs.writeFile(f,JSON.stringify(edit(rev,30+i)));return f;}));
 const results=await Promise.all(files.map(f=>cli(['call','studio_edit','--args-file',f])));assert.equal(results.filter(x=>x.code===0).length,1);assert.ok(results.filter(x=>x.code!==0).every(x=>JSON.parse(x.err).status===409));rev++;
 const stable=await read(),once=edit(rev,77,'idempotent-http-write');r=await api('studio_edit',once);assert.equal(r.status,200);rev++;r=await api('studio_edit',once);assert.equal(r.status,200);assert.equal((await r.json())._meta.studio.projectRevision,rev);assert.equal((await api('studio_edit',{...once,operations:edit(rev,88).operations})).status,409);
 passed.push('24 consecutive edits, bounded history, transactional rollback, six-process CAS, identical retry');
 let project=(await read()).project,state=(await read()).view,poll;
 const els=new Map();globalThis.document={hidden:false,getElementById:id=>{if(!els.has(id))els.set(id,{hidden:true,textContent:''});return els.get(id);}};globalThis.confirm=()=>true;globalThis.location={protocol:'http:'};globalThis.window={STUDIO_LOCAL:true};
 globalThis.setInterval=fn=>{poll=fn;return 0;};globalThis.setTimeout=(fn,ms,...args)=>ms===500||ms===200?{}:realTimeout(fn,ms,...args);
 let lost=false,offline=false;globalThis.fetch=async(url,options)=>{if(offline)throw Error('Simulated network loss');const r=await request(url,options);if(lost&&options?.body&&JSON.parse(options.body).name==='studio_replace'){lost=false;await r.arrayBuffer();throw Error('Lost response after commit');}return r;};
 const editor={get project(){return structuredClone(project);},get state(){return {...state};},busy:false,load:async p=>{project=structuredClone(p);},select:v=>{state={...v};}};
 await connectStudio(editor);assert.equal(window.studioSync.connected,true);
 editor.busy=true;project.name='Drag draft';window.studioSync.dirty();await poll();assert.notEqual((await read()).project.name,'Drag draft');editor.busy=false;await poll();assert.equal((await read()).project.name,'Drag draft');rev++;
 await els.get('agentPause').onclick();project.name='Paused draft';window.studioSync.dirty();await poll();assert.equal((await read()).project.name,'Drag draft');await els.get('agentPause').onclick();assert.equal((await read()).project.name,'Paused draft');rev++;
 offline=true;project.name='Network draft';window.studioSync.dirty();await poll();assert.equal(window.studioSync.unsynced,true);offline=false;await poll();assert.equal((await read()).project.name,'Network draft');rev++;
 lost=true;project.name='Reply lost draft';window.studioSync.dirty();await poll();assert.equal(window.studioSync.unsynced,true);assert.equal((await read()).project.name,'Reply lost draft');await poll();assert.equal(window.studioSync.unsynced,false);assert.equal((await read()).projectRevision,++rev);
 project.name='Concurrent draft';window.studioSync.dirty();await api('studio_edit',edit(rev,88));rev++;await poll();assert.equal(window.studioSync.unsynced,true);assert.equal(project.name,'Concurrent draft');assert.equal(els.get('agentReload').hidden,false);await els.get('agentReload').onclick();assert.equal(window.studioSync.unsynced,false);
 passed.push('actual HTTP bridge drag/pause, offline retention, lost-response idempotency, concurrent draft conflict');
 const port=service.port;await stop();service=await serve({directory:dir,port});assert.equal((await nativeFetch(base+'/api/studio',{method:'POST',headers:{cookie},body:'{}'})).status,401);
 const fresh=await workspace(dir);await fresh.call('studio_edit',edit(rev,99));rev++;
 await poll();assert.equal(project.clips.find(x=>x.id==='attack_se').tracks.arm_front.find(x=>x.time_ms===300).rotation,99,'open editor must resume after local server restart without ChatGPT login');assert.equal(els.get('agentSignin').hidden,true);
 passed.push('server stop/restart retains project and open editor renews local session');
 const exported=path.join(dir,'field-export.rig.json');assert.equal((await cli(['export',exported])).code,0);assert.equal(JSON.parse(await fs.readFile(exported,'utf8')).id,project.id);
 const mcpInput=[{jsonrpc:'2.0',id:1,method:'initialize',params:{protocolVersion:'2025-11-25'}},{jsonrpc:'2.0',id:2,method:'tools/call',params:{name:'studio_read',arguments:{}}},{method:'initialize',id:3},{jsonrpc:'2.0',id:4,method:'tools/call',params:{name:'studio_check',arguments:{}}}].map(JSON.stringify).join('\n')+'\n';
 const mcp=await run('local/mcp-stdio.mjs',['--data',dir],mcpInput);assert.equal(mcp.code,0,mcp.err);const lines=mcp.out.trim().split('\n').map(JSON.parse);assert.equal(lines[1].result.structuredContent.revision,rev);assert.equal(lines[2].error.code,-32600,'stdio initialize must validate JSON-RPC envelope');assert.ok(lines[3].result.structuredContent);
 passed.push('export retained source, actual stdio parser and shared project/check');
 const invalid=await cli(['read','--data']);assert.notEqual(invalid.code,0);assert.ok(JSON.parse(invalid.err).error);
 // Kill a real writer after fsync but before atomic rename; old committed state survives.
 const crashFile=path.join(dir,'crash.mjs'),beforeCrash=await fs.readFile(path.join(dir,'state.json'));
 await fs.writeFile(crashFile,"import fs from 'node:fs/promises';import {workspace} from '"+pathToFileURL(path.join(root,'local/workspace.mjs')).href+"';fs.rename=async()=>process.kill(process.pid,'SIGKILL');const ws=await workspace("+JSON.stringify(dir)+");await ws.call('studio_edit',"+JSON.stringify(edit(rev,123))+");");
 const crash=await run(path.relative(root,crashFile));assert.notEqual(crash.code,0);assert.deepEqual(await fs.readFile(path.join(dir,'state.json')),beforeCrash);
 assert.equal(JSON.parse((await cli(['doctor'])).out).lock.active,false);assert.equal(JSON.parse((await cli(['unlock'])).out).removed,true);assert.equal((await api('studio_edit',edit(rev,123))).status,200);rev++;
 const unicodeDir=path.join(dir,'unicode'),uw=await workspace(unicodeDir),unicode=(await uw.call('studio_read')).project;unicode.name='漢'.repeat(600000);let ur=await uw.call('studio_replace',{baseRevision:0,requestId:randomUUID(),project:unicode});for(let i=0;i<6;i++)ur=await uw.call('studio_edit',edit(ur.projectRevision,i));assert.ok(Buffer.byteLength(JSON.stringify([ur.past,ur.future]))<=8_000_000);
 passed.push('structured invalid CLI error, SIGKILL before rename retains prior state, dead-lock recovery, UTF-8 history byte budget');console.log(JSON.stringify({status:'passed',cases:passed,finalRevision:rev},null,2));
}catch(e){console.error(JSON.stringify({status:'failed',passed,error:e.message},null,2));throw e;}
finally{globalThis.fetch=nativeFetch;globalThis.setInterval=realInterval;globalThis.setTimeout=realTimeout;await stop();await fs.rm(dir,{recursive:true,force:true});}
