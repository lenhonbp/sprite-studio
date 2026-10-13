import {spawnSync} from 'node:child_process';import {fileURLToPath} from 'node:url';
const cwd=fileURLToPath(new URL('../skills/produce-game-sprites',import.meta.url));
const python=process.env.STUDIO_PYTHON??(process.platform==='win32'?'python':'python3');
const calls=[[python,['-m','unittest','discover','-s','scripts','-p','test_*.py']],[process.execPath,['scripts/test_timeline.cjs']],[process.execPath,['scripts/test_player.cjs']],[process.execPath,['scripts/test_clip_clock.mjs']]];
for(const [cmd,args]of calls){const r=spawnSync(cmd,args,{cwd,stdio:'inherit'});if(r.error){console.error(r.error.message);process.exit(1);}if(r.status!==0)process.exit(r.status??1);}
