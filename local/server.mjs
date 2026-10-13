import http from 'node:http';import {randomBytes,timingSafeEqual} from 'node:crypto';import {pathToFileURL} from 'node:url';
import {localWorker,options} from './workspace.mjs';
export async function createLocalApp(directory){const {worker,ws}=await localWorker(directory),token=randomBytes(32).toString('hex');
 const equal=s=>{const b=Buffer.from(s??'');return b.length===token.length&&timingSafeEqual(b,Buffer.from(token));};
 return {ws,async fetch(request){const url=new URL(request.url),allowed=/^(127\.0\.0\.1|localhost)$/.test(url.hostname);if(!allowed)return new Response('Host rejected',{status:403});
  const origin=request.headers.get('origin');if(origin&&origin!==url.origin)return new Response('Origin rejected',{status:403});
  const path=url.pathname,privateRoute=path==='/api/studio'||path==='/mcp';
  const cookie=request.headers.get('cookie')?.split(';').map(x=>x.trim()).find(x=>x.startsWith('studio_session='))?.slice('studio_session='.length);
  if(privateRoute&&!equal(cookie))return new Response(JSON.stringify({error:'Mở editor trên localhost để tạo phiên cục bộ.'}),{status:401,headers:{'content-type':'application/json'}});
  const headers=new Headers(request.headers);headers.set('oai-authenticated-user-id','local-workspace');headers.delete('oai-authenticated-user-email');
  const forwarded=new Request(request,{headers});const response=await worker.fetch(forwarded,{BUCKET:ws.bucket});
  const out=new Headers(response.headers);out.set('referrer-policy','same-origin');out.set('x-frame-options','SAMEORIGIN');
  if(request.method==='GET'&&(path==='/'||path==='/index.html'||path==='/health')){out.set('set-cookie','studio_session='+token+'; HttpOnly; SameSite=Strict; Path=/');out.set('cache-control','no-store');}
  return new Response(response.body,{status:response.status,headers:out});
 }};
}
export async function serve({directory,port=8787}){if(!Number.isInteger(port)||port<0||port>65535)throw Error('Port phải từ 0 đến 65535');const app=await createLocalApp(directory);let actualPort=port;
 const server=http.createServer(async(req,res)=>{try{
  const host=req.headers.host;if(host!==`127.0.0.1:${actualPort}`&&host!==`localhost:${actualPort}`){res.writeHead(403).end('Host rejected');return;}
  let bytes=0;const chunks=[];for await(const chunk of req){bytes+=chunk.length;if(bytes>5_000_000){res.writeHead(413).end('Request too large');return;}chunks.push(chunk);}
  const body=chunks.length?Buffer.concat(chunks):undefined,request=new Request('http://'+host+req.url,{method:req.method,headers:req.headers,...(body?{body}:{} )});
  const response=await app.fetch(request);res.writeHead(response.status,Object.fromEntries(response.headers));res.end(Buffer.from(await response.arrayBuffer()));
 }catch(e){res.writeHead(500,{'content-type':'application/json'}).end(JSON.stringify({error:e.message}));}});
 await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(port,'127.0.0.1',()=>{actualPort=server.address().port;resolve();});});return {server,port:actualPort,directory:app.ws.bucket.directory};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){const args=process.argv.slice(2),i=args.indexOf('--port');serve({...options(args),port:Number(i<0?8787:args[i+1])}).then(({server,port,directory})=>{console.log('Nhon Le Sprite Studio: http://127.0.0.1:'+port+'\nWorkspace: '+directory+'\nCtrl+C để dừng.');for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>server.close(()=>process.exit(0)));}).catch(e=>{console.error(e.message);process.exitCode=1;});}
