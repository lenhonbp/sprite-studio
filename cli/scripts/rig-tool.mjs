#!/usr/bin/env node
import path from 'node:path';import {pathToFileURL} from 'node:url';
import {main} from '../../skills/produce-game-sprites/tools/rig-animation/scripts/rig-tool.mjs';
export * from '../../skills/produce-game-sprites/tools/rig-animation/scripts/rig-tool.mjs';
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href)main(process.argv.slice(2)).catch(e=>{console.error(JSON.stringify({error:e.message}));process.exitCode=2;});
