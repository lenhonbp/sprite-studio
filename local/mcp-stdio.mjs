// Newline-delimited JSON-RPC; stdout is protocol only, no startup logs.
import {localWorker,options} from './workspace.mjs';
const {directory}=options(),{worker,ws}=await localWorker(directory);let input=Buffer.alloc(0);
async function dispatch(line){let q;try{q=JSON.parse(line);}catch{return {jsonrpc:'2.0',id:null,error:{code:-32700,message:'Parse error'}};}
 if(!q||q.jsonrpc!=='2.0'||typeof q.method!=='string'||(q.id!==undefined&&q.id!==null&&!['string','number'].includes(typeof q.id)))return {jsonrpc:'2.0',id:null,error:{code:-32600,message:'Invalid request'}};
 if(q.id===undefined)return null;
 if(q?.method==='initialize'){return {jsonrpc:'2.0',id:q.id??null,result:{protocolVersion:['2025-03-26','2025-06-18','2025-11-25','2026-07-28'].includes(q.params?.protocolVersion)?q.params.protocolVersion:'2025-11-25',capabilities:{tools:{},resources:{}},serverInfo:{name:'Nhon Le Sprite Studio Local',version:'3.3.1'}}};}
 const request=new Request('http://127.0.0.1/mcp',{method:'POST',headers:{'content-type':'application/json','oai-authenticated-user-id':'local-workspace'},body:JSON.stringify(q)});const response=await worker.fetch(request,{BUCKET:ws.bucket});if(response.status===202)return null;return response.json();
}
try{for await(const chunk of process.stdin){input=Buffer.concat([input,chunk]);let pos;while((pos=input.indexOf(10))>=0){const line=input.subarray(0,pos);input=input.subarray(pos+1);if(line.length>5_000_000)throw Error('MCP message exceeds 5 MB');if(!line.toString('utf8').trim())continue;const result=await dispatch(line.toString('utf8'));if(result){const data=JSON.stringify(result)+'\n';if(!process.stdout.write(data))await new Promise(resolve=>process.stdout.once('drain',resolve));}}if(input.length>5_000_000)throw Error('MCP message exceeds 5 MB');}if(input.length)throw Error('MCP input must end with newline');}catch(e){console.error(e.message);process.exitCode=1;}
