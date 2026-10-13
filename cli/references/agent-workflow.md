

# Animate Game Rigs · v2.0

**Made by Nhon Le**

Use the same `scripts/rig-core.mjs` for the browser editor and agent CLI. Preserve authored source pixels and rig coordinates. This tool authors cutout transforms; it does not redraw anatomy or synthesize unseen directions.

## Start

1. Inspect source art, camera, handedness, required directions and actual engine conventions. Apply the production contract and Technical → Visual → Runtime gates from `produce-game-sprites`.
2. Read [project schema](project-schema.md) before changing rig data. The module root is `<sprite-skill>/tools/rig-animation`; resolve the installed `produce-game-sprites` path dynamically. Open the supplied project or use `<rig-module>/assets/demo-project.json` only for functional examples.
3. For modular cutting, define body-space joints first and verify neutral reassembly with the companion skill's `verify_rig.py`. A newly authored assembly from separated parts has no original flattened master: label its provenance honestly and inspect overlap; do not claim exact reconstruction against an unseen source.
4. Validate the project with `node <rig-module>/scripts/rig-tool.mjs validate PROJECT`.
5. Keep changes under the user's project directory; outputs must use new paths. Preserve input source files.

## Execute agent actions

```bash
node <rig-module>/scripts/rig-tool.mjs sample hero.rig.json --clip attack_se --time 340
node <rig-module>/scripts/rig-tool.mjs set-key hero.rig.json --clip attack_se --bone arm_front --time 340 --values '{"rotation":-65,"easing":"smooth"}' --out hero-v2.rig.json
node <rig-module>/scripts/rig-tool.mjs set-slot hero-v2.rig.json --slot hat --attachment hat --order 8 --out hero-v3.rig.json
node <rig-module>/scripts/rig-tool.mjs render hero-v3.rig.json --fps 24 --out candidate-01
```

Use `add-bone` for an explicit parent and local position. Use `set-slot` for appearance or layer changes. Use `sample` to inspect world matrices and sockets, then inspect the visible rendered grip: numeric attachment consistency alone cannot establish a correct hand contact point.

The renderer uses `@napi-rs/canvas`. If absent, install it in a user-owned dependency directory following the host's dependency/network policy, and set `CODEX_PRIMARY_RUNTIME_NODE_MODULES` to that directory's `node_modules`. The CLI also checks its installed module dependencies. The math/editor need no external image-generation service. Use available host image tools when new artwork or hidden anatomy must be drawn.

## Author motion

- Keep one ground origin and canvas for all frames. Store rest transforms in bones; store absolute bone-local animated values in clip tracks. Declare directions separately; one southeast rig does not establish eight-direction coverage.
- Author wind-up, impact, follow-through and recovery for attacks. For walking, inspect foot placement and calibrate stride in the actual game; rotating a complete leg is a limited cutout demonstration, not a fully drawn gait.
- Preserve local grip children and slots through all poses. Use separate slots or slot tracks for front/rear equipment. Draw order alone cannot invent occluded cape folds.
- Use `linear`, `smooth` or `step` per-channel interpolation. Rotation follows the shortest arc unless a key declares `spin:true`. Loop end values should match their first key to avoid a seam.
- A one-shot renderer samples its exact terminal pose for the final exported frame. Keep gameplay event time separate from the sampled artwork.
- Edit the smallest affected track/slot. Rendering a new project revision invalidates previous visual evidence; run current QA again.

## Handoff to v3.8

Read [integration workflow](integration.md). Render writes PNGs, `animation-set.json`, mathematical socket metadata, source project, source hash, art contract and a report. These are **candidate frames**, not approved atlases. Run companion `inspect`, `preview`, `motion-check`, bound visual review and `qa`. Only then run `pack`. Complete actual target-engine review before `release-check`.

Report observed canvas clipping, timing, exact source revision, inspected visual defects and untested runtime behavior. Never fill a visual review from the intended keyframes. Keep the demo's source/provenance label when using its generated parts.

## Editor

Open the companion Nhon Le Sprite Studio Site or its downloadable standalone HTML. Import/export the same `.rig.json`; use Rig mode for rest transforms and animation mode for keyframes. Browser exports PNG frame ZIPs with the v3.8 manifest. Save JSON before replacing a project; browser autosave is device-local and may run out of space. The CLI is the implemented agent interface; no live MCP server is bundled in this release.

Read [observed verification](verification.md) before reporting tested capability. The companion editor is available at https://nhon-le-sprite-studio.lethanhnhon22847.chatgpt.site.

## v2 authoring operations

Use `edit PROJECT --op JSON --out NEW.json` for transactional edits. Supported operation types: add-clip, add-bone, add-slot, rename-clip, duplicate-clip, delete-clip, bone-settings, rename-bone, delete-bone (including descendant tracks/slots/sockets), reparent (preserve rest world; reject sheared or animated reparent), project, set-slot, delete-slot, slot-key, remove-slot-key, move-key, retime, clear-track, pose-key, event, socket, save-skin, apply-skin, delete-skin, delete-attachment and ik. See concrete CLI examples below. Every operation returns a validated detached candidate; preserve originals. Rename IDs across references; never manually change a bone ID without its tracks, sockets and slot links. Key retiming rejects rounded collisions rather than overwriting keys.

```bash
node <rig-module>/scripts/rig-tool.mjs edit hero.rig.json --op '{"type":"duplicate-clip","clip":"attack_se","id":"attack_variant_se"}' --out hero-v2.rig.json
node <rig-module>/scripts/rig-tool.mjs edit hero-v2.rig.json --op '{"type":"slot-key","clip":"attack_variant_se","slot":"hat","time":300,"values":{"attachment":"hat","opacity":0.5,"drawOrder":10}}' --out hero-v3.rig.json
node <rig-module>/scripts/rig-tool.mjs edit hero-v3.rig.json --op '{"type":"event","clip":"attack_variant_se","name":"impact","time":300}' --out hero-v4.rig.json
node <rig-module>/scripts/rig-tool.mjs ik hero-v4.rig.json --clip attack_variant_se --bone grip --time 350 --target '[350,330]' --depth 2 --out hero-v5.rig.json
node <rig-module>/scripts/rig-tool.mjs coverage hero-v5.rig.json --actions idle,walk,run,attack,hit,dead --directions s,se,e,ne,n,nw,w,sw
node <rig-module>/scripts/rig-tool.mjs sheet hero-v5.rig.json --clip attack_variant_se --fps 12 --out sheets-01
node <rig-module>/scripts/rig-tool.mjs gif hero-v5.rig.json --clip attack_variant_se --fps 12 --out attack-preview.gif
```

Inspect IK `reached` and `error_px`. Reduce the ancestor depth if the torso must stay fixed. Set per-bone `ikLimit:{min,max}` (absolute bone-local degrees) using `bone-settings` before solving if the body must stay inside a safe angular range. The demo limits torso to -10..10° and front arm to -95..75°. These limits constrain IK only, not manual animation edits. CCD uses parent rotations, preserves lengths and may report an unreachable or unconverged target. Visually check the grip against source artwork after solving.

Candidate sheets have deterministic untrimmed rectangles, page names, exact durations, origin and cell-local sockets in `spritesheet.json`; they are authoring previews, not approved v3.8 runtime atlases. Render frame PNGs and pass v3.8 QA before its engine-ready pack. GIF uses a fixed 255-color palette plus alpha threshold and quantized centiseconds; use it for motion preview only, keeping PNG masters. Sheet and GIF outputs refuse overwrite and preserve source JSON.
