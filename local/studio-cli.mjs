import fs from 'node:fs/promises';import path from 'node:path';import {randomUUID} from 'node:crypto';
import {workspace,options} from './workspace.mjs';import {lockInfo,unlockDead} from './disk-bucket.mjs';
import {validateProject} from '../web/rig-core.mjs';
const argv=process.argv.slice(2);
try{
 const {directory}=options(argv),di=argv.indexOf('--data');if(di>=0)argv.splice(di,2);const [command,...rest]=argv;
 if(!command||command==='help'){console.log('studio read | check | call TOOL --args-file JSON | import SOURCE --revision N | export NEW.json | doctor | unlock [--data ABS_DIR]');}
 else if(command==='doctor'){const info=await lockInfo(directory);console.log(JSON.stringify({node:process.version,directory,lock:info,stateFile:path.join(directory,'state.json'),editorCommand:'npm start -- --data '+directory},null,2));}
 else if(command==='unlock'){console.log(JSON.stringify({removed:await unlockDead(directory)}));}
 else{const ws=await workspace(directory);let result;
  if(command==='read')result=await ws.call('studio_read');
  else if(command==='check')result=await ws.call('studio_check');
  else if(command==='call'){const i=rest.indexOf('--args-file');if(i<0)throw Error('Dùng --args-file để giữ JSON và requestId nguyên vẹn.');const args=JSON.parse(await fs.readFile(rest[i+1],'utf8'));result=await ws.call(rest[0],args);}
  else if(command==='export'){if(!rest[0])throw Error('Cần đường dẫn kết quả mới');const r=await ws.call('studio_read');await fs.mkdir(path.dirname(path.resolve(rest[0])),{recursive:true});await fs.writeFile(rest[0],JSON.stringify(r.project,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({exported:path.resolve(rest[0]),revision:r.projectRevision}));}
  else if(command==='import'){const i=rest.indexOf('--revision');if(!rest[0]||i<0)throw Error('Đọc trước rồi import SOURCE --revision N');const source=await fs.readFile(rest[0],'utf8');if(source.length>4_000_000)throw Error('Project chung tối đa 4 MB');const project=JSON.parse(source);validateProject(project);result=await ws.call('studio_replace',{baseRevision:Number(rest[i+1]),requestId:randomUUID(),project});}
  else throw Error('Lệnh không hợp lệ');
  if(result){const {toolResult}=await import('./workspace.mjs');const reply=toolResult(result);console.log(JSON.stringify(reply.structuredContent,null,2));}
 }
}catch(e){console.error(JSON.stringify({error:e.message,status:e.status??400}));process.exitCode=1;}
