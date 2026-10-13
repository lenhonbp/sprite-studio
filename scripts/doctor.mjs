#!/usr/bin/env node
import {spawnSync} from 'node:child_process';
import {canvasBackend} from '../skills/produce-game-sprites/tools/rig-animation/scripts/rig-tool.mjs';
const [major,minor]=process.versions.node.split('.').map(Number);
const nodeReady=major>=22,testReady=major>22||(major===22&&minor>=13);
const checks=[{name:'node',version:process.versions.node,status:nodeReady?'ready':'missing',purpose:'Local editor, CLI, MCP',action:nodeReady?null:'Install Node 22 or newer'},
{name:'engine_test_api',status:testReady?'ready':'missing',purpose:'Cocos source type-erasure checks',action:testReady?null:'Use Node 22.13 or newer for test:engines'}];
try{const {createCanvas}=await canvasBackend();const png=createCanvas(1,1).toBuffer('image/png');if(png.length<33)throw Error('PNG encoding failed');checks.push({name:'native_canvas',status:'ready',purpose:'CLI rendering and pixel verification'});}catch(e){checks.push({name:'native_canvas',status:'optional_missing',purpose:'CLI rendering and pixel verification',action:'Run npm install; offline/browser rendering does not need this dependency',detail:e.message});}
const python=process.env.STUDIO_PYTHON??(process.platform==='win32'?'python':'python3');
const result=spawnSync(python,['-c','import sys,json; print(json.dumps({"version":sys.version.split()[0],"supported":sys.version_info >= (3,10)}))'],{encoding:'utf8',timeout:10000});
let py;try{py=JSON.parse(result.stdout);}catch{}
checks.push({name:'python',status:py?.supported?'ready':'optional_missing',version:py?.version??null,purpose:'Build, release verification and full art toolkit',action:py?.supported?null:'Install Python 3.10+; set STUDIO_PYTHON if necessary'});
const pillow=py?.supported?spawnSync(python,['-c','import PIL; print(PIL.__version__)'],{encoding:'utf8',timeout:10000}):null;
checks.push({name:'pillow',status:pillow?.status===0?'ready':'optional_missing',version:pillow?.status===0?pillow.stdout.trim():null,purpose:'Python sprite/art QA',action:pillow?.status===0?null:'Install Pillow in the selected Python environment'});
console.log(JSON.stringify({schema:'nhon-le-environment-check/v1',local_editor:nodeReady?'ready':'blocked',checks,engine_runtime:'not_tested',note:'Does not install dependencies, start servers, inspect private projects, or prove engine compatibility.'},null,2));
if(!nodeReady)process.exitCode=1;
