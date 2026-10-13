import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const python=process.env.STUDIO_PYTHON??(process.platform==='win32'?'python':'python3');
const script=fileURLToPath(new URL('../skills/produce-game-sprites/scripts/sprite_tools.py',import.meta.url));
const child=spawn(python,[script,...process.argv.slice(2)],{stdio:'inherit'});
child.on('error',e=>{console.error('Không chạy được Python: '+e.message+'; đặt STUDIO_PYTHON nếu cần.');process.exitCode=1;});
child.on('exit',(code,signal)=>{process.exitCode=code??1;});
