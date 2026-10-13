import {spawnSync} from 'node:child_process';
for(const file of ['test-local.mjs','test-service.mjs','test-bridge.mjs','test-vault.mjs']){const r=spawnSync(process.execPath,[file],{stdio:'inherit'});if(r.status!==0)process.exit(r.status??1);}
