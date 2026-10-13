#!/usr/bin/env node
export * from '../skills/produce-game-sprites/tools/rig-animation/scripts/production-cli.mjs';
import {productionMain} from '../skills/produce-game-sprites/tools/rig-animation/scripts/production-cli.mjs';
import {pathToFileURL} from 'node:url';
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href)productionMain(process.argv.slice(2)).catch(e=>{console.error(JSON.stringify({error:e.message}));process.exitCode=1;});
