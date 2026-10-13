import fs from 'node:fs/promises';import path from 'node:path';import {fileURLToPath} from 'node:url';
import {diskBucket} from './disk-bucket.mjs';import {createWorker,handleTool,toolResult} from '../server/service.mjs';
export const root=path.resolve(fileURLToPath(new URL('..',import.meta.url)));
export function options(argv=process.argv.slice(2)){const i=argv.indexOf('--data');if(i>=0&&(!argv[i+1]||argv[i+1].startsWith('--')))throw Error('--data cần đường dẫn');return {directory:path.resolve(i<0?path.join(root,'.studio'):argv[i+1]??'.studio')};}
export async function workspace(directory){const bucket=diskBucket(directory),demo=JSON.parse(await fs.readFile(path.join(root,'web/demo-project.json'),'utf8'));return {bucket,demo,async call(name,args={}){return handleTool(name,args,'local-workspace',bucket,demo);}};}
export async function localWorker(directory){const ws=await workspace(directory),assets=Object.create(null);for(const f of await fs.readdir(path.join(root,'web'))){const type={html:'text/html; charset=utf-8',mjs:'text/javascript',css:'text/css',json:'application/json'}[f.split('.').at(-1)];if(type)assets['/'+f]={text:await fs.readFile(path.join(root,'web',f),'utf8'),type};}
 assets['/index.html'].text=assets['/index.html'].text.replace('<title>', '<title>Local · ').replace('v4.1.1</span>','v4.1.1 Local</span>');
 assets['/index.html'].text=assets['/index.html'].text.replace('<script type="module" src="editor.mjs"></script>','<script>window.STUDIO_LOCAL=true;</script><script type="module" src="editor.mjs"></script>');
 const widget=(await fs.readFile(path.join(root,'Nhon-Le-Sprite-Studio.html'),'utf8')).replace('window.STUDIO_DEMO=','window.STUDIO_EMBEDDED=true;window.STUDIO_DEMO=');return {ws,worker:createWorker(assets,widget,ws.demo)};
}
export {toolResult};
