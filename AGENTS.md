# Nhon Le Sprite Studio — agent workspace

Read README.md, docs/LOCAL.md and skills/produce-game-sprites/SKILL.md. For art tasks apply that bundled skill; load its references by asset role. Use Node 22+.

Start the editor with `npm start`. Use `npm run studio -- read` before a live edit. Edit using `npm run studio -- call studio_edit --args-file path/to/arguments.json`; arguments contain current baseRevision, unique requestId, and operations. UI, CLI and local MCP share the same disk state. Do not overwrite `.studio/state.json` directly or manufacture a revision. Read a real conflict and reconcile; never bypass CAS.

For MCP-capable agents, use local/mcp-stdio.mjs with an absolute --data path pointing to the same data folder as npm start. See config/mcp.example.json; do not assume a host has auto-connected MCP merely because a repository was cloned.

Export a portable source with `npm run studio -- export projects/hero.rig.json`. Rendering exported sources uses cli/scripts/rig-tool.mjs; install canvas only when native output is needed. Preserve raster sources and follow the existing Technical → Visual → Runtime gates. The demo is one direction and three unapproved cutout clips.

Keep .studio/, credentials, node_modules and generated proof caches out of Git. Source JSON intentionally exported to projects/ may be committed when the user requests it. Do not publish or push another remote just because this repository contains a Sites manifest.

Use npm run art -- COMMAND for the full production toolkit and npm run rig -- COMMAND for standalone rig sources. Keep one canonical rig implementation in skills/produce-game-sprites/tools/rig-animation/scripts. web/rig-core.mjs, web/gif-preview.mjs and demo copies are generated: npm run build refreshes them; npm run audit catches drift. Do not change the original skill acceptance gates or declare artwork approved because tests pass. The process-sprite-sheets companion is optional and not bundled.

For v4 asset/VFX work read docs/PRODUCTION.md and the bundled skill's references/studio-production.md. Use studio_edit fx-put/fx-binding/asset-put operations in the same revision history. Use studio_view effectId to select an effect. Standalone rendering: npm run production. rig-tool body exports do not include effects. Candidate VFX exports carry separate blend/depth tracks and unapproved visual/runtime status; run per-track vfx-check then evidence-bound review and real engine tests.

For v4.1 engine handoff read docs/ENGINES.md and the bundled multi-engine-handoff.md. List targets with npm run production -- engines, choose vfx --engine TARGET or generic. New engine adapters cover baked VFX; do not claim native sprite/body controllers or runtime approval for every engine.

For v4.1.1 handoff checks read docs/HANDOFF-CHECKS.md. Run npm run doctor;
verify a frozen VFX export with npm run verify:pack -- DIR --rerender --out NEW_REPORT.json.
Reports belong outside the inspected pack. A passed report is technical consistency,
not visual/runtime acceptance. Test the archive after extraction; package-release.py
supports a directory without Git and refuses to overwrite existing output.
