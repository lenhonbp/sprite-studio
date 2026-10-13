import fs from 'node:fs/promises';import path from 'node:path';import {createHash,randomUUID} from 'node:crypto';
const hash=s=>createHash('sha256').update(s).digest('hex');
export function diskBucket(directory){
 const dir=path.resolve(directory),file=path.join(dir,'state.json'),lock=path.join(dir,'write.lock');
 async function read(){try{return await fs.readFile(file,'utf8');}catch(e){if(e.code==='ENOENT')return null;throw e;}}
 async function locked(fn){await fs.mkdir(dir,{recursive:true});const nonce=randomUUID(),deadline=Date.now()+5000;let handle;
  while(!handle){try{handle=await fs.open(lock,'wx',0o600);}catch(e){if(e.code!=='EEXIST')throw e;if(Date.now()>deadline)throw Error('Workspace đang bị khóa. Chạy doctor; nếu tiến trình đã dừng, dùng unlock.');await new Promise(r=>setTimeout(r,40));}}
  try{await handle.writeFile(JSON.stringify({pid:process.pid,nonce,createdAt:new Date().toISOString()}));await handle.close();return await fn();}finally{await handle.close().catch(()=>{});try{const owner=JSON.parse(await fs.readFile(lock,'utf8'));if(owner.nonce===nonce)await fs.unlink(lock);}catch{}}
 }
 return {directory:dir,file,lock,async get(){const body=await read();return body===null?null:{etag:hash(body),json:async()=>JSON.parse(body)};},async head(){const body=await read();return body===null?null:{etag:hash(body),customMetadata:{version:String(JSON.parse(body).version)}};},async put(key,body,options){return locked(async()=>{const old=await read();if(options.onlyIf instanceof Headers){if(old!==null)return null;}else if(old===null||hash(old)!==options.onlyIf.etagMatches)return null;JSON.parse(body);const tmp=path.join(dir,'.state-'+randomUUID()+'.tmp');try{const out=await fs.open(tmp,'wx',0o600);try{await out.writeFile(body);await out.sync();}finally{await out.close();}await fs.rename(tmp,file);return {etag:hash(body)};}finally{await fs.rm(tmp,{force:true});}});}};
}
export async function lockInfo(directory){try{const info=JSON.parse(await fs.readFile(path.join(directory,'write.lock'),'utf8'));if(!Number.isInteger(info.pid)||info.pid<=0)throw Error('Khóa không hợp lệ; dừng mọi tiến trình trước khi kiểm tra write.lock thủ công.');try{process.kill(info.pid,0);info.active=true;}catch(e){info.active=e.code!=='ESRCH';}return info;}catch(e){if(e.code==='ENOENT')return null;throw e;}}
export async function unlockDead(directory){const info=await lockInfo(directory);if(!info)return false;if(info.active)throw Error('Tiến trình giữ khóa vẫn hoạt động; không xóa khóa.');await fs.unlink(path.join(directory,'write.lock'));return true;}
