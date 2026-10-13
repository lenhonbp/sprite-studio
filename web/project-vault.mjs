// Device-local shelf and crash recovery. Export a file for durable, portable ownership.
export function createVault({indexedDB=globalThis.indexedDB,storage}={}){
 if(storage===undefined){try{storage=globalThis.localStorage;}catch{storage=null;}}
 const KEY='nhon-le-studio-vault-v1',MAX=32_000_000;let dbPromise,chain=Promise.resolve();
 const empty=()=>({schema:'nhon-le-vault/v1',items:[],recovery:null});
 const size=p=>new TextEncoder().encode(JSON.stringify(p)).length;
 const db=()=>dbPromise??=new Promise((resolve,reject)=>{if(!indexedDB){resolve(null);return;}const r=indexedDB.open('nhon-le-studio-projects',1);r.onupgradeneeded=()=>r.result.createObjectStore('vault');r.onsuccess=()=>resolve(r.result);r.onerror=()=>resolve(null);r.onblocked=()=>reject(Error('Đóng tab Studio cũ rồi mở lại thư viện.'));});
 const run=fn=>{const job=chain.then(async()=>{const d=await db();if(!d){const state=JSON.parse(storage?.getItem(KEY)??'null')??empty();const out=fn(state);if(fn.write){if(!storage)throw Error('Trình duyệt chặn lưu thiết bị; hãy lưu JSON.');storage.setItem(KEY,JSON.stringify(state));}return out;}return new Promise((resolve,reject)=>{const tx=d.transaction('vault',fn.write?'readwrite':'readonly'),store=tx.objectStore('vault');let result;const req=store.get('state');req.onsuccess=()=>{try{const s=req.result??empty();result=fn(s);if(fn.write)store.put(s,'state');}catch(e){reject(e);tx.abort();}};tx.oncomplete=()=>resolve(result);tx.onerror=()=>reject(tx.error??Error('Không lưu được thư viện; hãy xuất JSON.'));tx.onabort=()=>reject(tx.error??Error('Lưu bị hủy; hãy xuất JSON.'));});});chain=job.catch(()=>{});return job;};
 const write=fn=>{fn.write=true;return run(fn);};
 const validSize=p=>{const n=size(p);if(n>MAX)throw Error('Thư viện thiết bị tối đa 32 MB mỗi bản; hãy lưu JSON cho nguồn lớn.');return n;};
 return {
  list:()=>run(s=>s.items.map(({project,...meta})=>meta)),
  read:id=>run(s=>structuredClone(s.items.find(x=>x.id===id)?.project??null)),
  save:(project,name=project.name??project.id)=>write(s=>{const bytes=validSize(project);if(s.items.length>=20||s.items.reduce((n,i)=>n+i.bytes,0)+bytes>MAX)throw Error('Thư viện đầy (20 bản / 32 MB). Xuất backup rồi xóa bản không cần.');const id=crypto.randomUUID();s.items.push({id,name:String(name).slice(0,100),bytes,updatedAt:new Date().toISOString(),project:structuredClone(project)});return id;}),
  remove:id=>write(s=>{s.items=s.items.filter(x=>x.id!==id);}),
  recovery:()=>run(s=>structuredClone(s.recovery)),
  recover:project=>write(s=>{validSize(project);s.recovery={project:structuredClone(project),updatedAt:new Date().toISOString()};}),
  exportAll:()=>run(s=>structuredClone({schema:s.schema,items:s.items})),
  importAll:(backup,validate)=>write(s=>{if(backup?.schema!=='nhon-le-vault/v1'||!Array.isArray(backup.items)||backup.items.length>20)throw Error('Backup thư viện không hợp lệ.');const entries=backup.items.map(x=>{validate(x.project);return {id:crypto.randomUUID(),name:String(x.name??x.project.id).slice(0,100),bytes:validSize(x.project),updatedAt:new Date().toISOString(),project:structuredClone(x.project)};});if(s.items.length+entries.length>20||[...s.items,...entries].reduce((n,i)=>n+i.bytes,0)>MAX)throw Error('Backup vượt giới hạn thư viện; không có bản nào được nhập.');s.items.push(...entries);return entries.length;})
 };
}
