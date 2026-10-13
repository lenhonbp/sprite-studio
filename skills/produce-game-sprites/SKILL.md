---
name: produce-game-sprites
description: Produce coherent game-art systems through an agent-led, provider-independent workflow. Use for sprites and directional animation, editable raster rigs, baked IK, bone/keyframe and equipment authoring, UI/HUD/UX kits, component slicing and state systems, props/items/equipment variants, VFX, top-down/isometric environment assets, modular/Spine reskins, temporal/roster consistency, visual QA, atlas handoff and Godot/PixiJS integration. Use the companion process-sprite-sheets skill for advanced source reconstruction and raster processing when available.
---

# Produce Game Sprites · Game Art Production v3.8

v3.8 (2026-10-09): bind production dependencies into QA/export; strict RGBA rig and bundle verification; action × direction coverage; deterministic multipage/trim/extrusion with exact pixel round-trip; shared pose/event clock; local rendered-runtime harness and final release gates. Read [v3.8 verification](references/verification-v3.8.md) for observed tests and remaining runtime limitations.

**Made by Nhon Le**

Make the agent own the art decisions, evidence, repairs and delivery. Use the available editing capability to execute that plan. A written plan or passing script is not proof of good artwork.

## Start and route

1. Inspect supplied art and the actual project before changing anything. Reuse camera, style, topology, naming and runtime conventions. Resolve this skill's installed path dynamically.
2. Run `python3 <skill>/scripts/sprite_tools.py doctor`. Check callable image-generation/editing tools separately; the doctor only detects local executables and Python dependencies. Read [tool-routing.md](references/tool-routing.md).
3. Select a feasible route: native editable art; reference-guided generation; source-preserving reconstruction; or hybrid layers. Prefer existing editable sources for corrections. Do not fabricate unavailable capabilities, silently replace a pixel artist with geometric placeholders, or claim that still-image translation is articulated animation.
4. Read [production-workflow.md](references/production-workflow.md) and classify the runtime asset role. For animation read [motion-design.md](references/motion-design.md) and [consistency-contracts.md](references/consistency-contracts.md). For UI/HUD read [ui-ux-production.md](references/ui-ux-production.md). UI production requires evidence-bound visual review and runtime interaction verification, not only structural `ui-check`. For environments/maps read [environment-production.md](references/environment-production.md). For Spine/modular work read [spine-modular-production.md](references/spine-modular-production.md); for separate effects read [vfx-production.md](references/vfx-production.md). For sellable multi-effect VFX packs (effect taxonomy, provider recipes, sales bundle, AI disclosure, marketplace policy gates) read [vfx-pack.md](references/vfx-pack.md). Use [game-art-system.md](references/game-art-system.md) when several asset families must share one art direction. For hands-on authored art read [native-production.md](references/native-production.md); for mixed-grid sheets, alpha, reskins or turnarounds read [alpha-and-sheets.md](references/alpha-and-sheets.md). Before slicing/repacking sheets, read [sheet-processing-bridge.md](references/sheet-processing-bridge.md). For export read [engine-handoff.md](references/engine-handoff.md).
5. Work under the user's project or an output directory, not this skill folder. Preserve original files. Choose routine implementation details autonomously; ask only for missing information that changes the asset contract or an actual authorization boundary.

## Route by runtime asset, not by generator name

- **Character/monster sprite animation:** use the existing animation contract and three gates.
- **Editable bone/keyframe rigs:** read [rig-editor-bridge.md](references/rig-editor-bridge.md) and use the integrated `tools/rig-animation` module with Nhon Le Sprite Studio. Preserve the same production and QA gates for rendered candidates.
- **UI/HUD/menu/icon kit:** create `ui-contract.json` from [ui-contract.example.json](assets/ui-contract.example.json), keep final text in the runtime layer by default, validate states/touch/nine-slice with `ui-check`, slice only reviewed explicit rectangles with `ui-slice`, bind a fresh visual review with `ui-review-template`/`ui-qa`, then verify actual screens and interactions with `ui-runtime-template`/`ui-runtime-verify`. A generated UI sheet is source material, not a finished UX.
- **Props/items/equipment packs:** freeze one style/source direction, keep scale/anchor consistent, record upgrade lineage, and repair weak members individually rather than repeatedly regenerating the whole pack.
- **VFX:** keep effect timing/alpha/blend/socket metadata separate from body animation when practical; run `vfx-check`, then `vfx-review-template`/`vfx-qa`, then actual target-runtime `vfx-runtime-template`/`vfx-runtime-verify`. For pack-for-sale production, run `vfx-pack-plan` before generation, `vfx-pack-bundle-check` for structural integrity and `vfx-pack-release-check` for current per-effect visual/runtime gates before upload; see [vfx-pack.md](references/vfx-pack.md) for the taxonomy, provider recipes and marketplace policy gates.
- **Terrain/tiles/maps:** define logical footprint, pivot/depth anchor, collision and seam policy independently from outer image bounds; run `environment-check`, bind assembled-map evidence with `environment-review-template`/`environment-qa`, then verify depth/collision/seams in the target runtime with `environment-runtime-template`/`environment-runtime-verify`.
- **Spine/cutout/modular:** inspect rig/runtime/atlas first, preserve topology for appearance-only edits, replace the smallest attachment possible, and round-trip in the target runtime.
- **Game design/audio:** treat as adjacent capabilities. They may consume the same contracts/events but do not become substitutes for sprite/UI visual or runtime acceptance.

## Establish one production contract

Write `art-contract.md` describing the shared game-art direction: identity/revision, pixel/HD representation, camera/projection, native scale, palette/outline/light/material language and runtime sampling. For character animation also declare anatomy, equipment/handedness, ground origin, motion space, required directions/actions, durations, loops, terminal poses, transitions and gameplay events. Separate visual effects, root movement and hitboxes. For UI use `ui-contract.json` as the authoritative component/state/layout contract instead of forcing UI into `animation-set.json`.

Use `init-animation` to scaffold an explicit action × direction matrix without placeholder art, or create `animation-set.json` from [animation-set.example.json](assets/animation-set.example.json), adapting every example value. Read [toolkit.md](references/toolkit.md) for the strict schema. Declare `coverage.actions` and `coverage.directions`, with deliberate exceptions recorded in the art contract; list every required clip in `required_clips`, then explicitly order every frame with its relative path and duration. This catches missing actions; do not delete requirements to make QA pass. Track provider/tool, prompt or edit recipe, source references, candidate revision and applicable costs in `production-log.md`. For nontrivial animation families, also create `production-metadata.json` from [production-metadata.example.json](assets/production-metadata.example.json) and declare only the landmarks/sockets/depth/locomotion/collision/provenance fields that are meaningful for the asset. Treat them as review instruments, not inferred truth. Declare `production_contracts` for art direction, metadata, keyposes, family and slice provenance. Conventional co-located art/metadata/family/slice contracts are also bound automatically. Changed dependency bytes invalidate review and export identity; missing or invalid declared contracts block QA/export.

Use `process-sprite-sheets`' production contract instead when that installed skill better matches source reconstruction, landmarks, shared layers, attachment anchors or source reconstruction requirements. Keep one authoritative contract; do not independently maintain two disagreeing manifests. Use this skill for production direction, that skill for processing and validation. Its CLI schema differs from this toolkit's schema.

## Produce in stages

1. **Master:** inspect/approve one character at native size and gameplay size. Stabilize proportions, silhouette, materials, equipment and camera before expansion.
2. **Motion proof:** produce one representative action in one direction. Design the pose sequence: preparation → contact/impact → follow-through → recovery. For gait, design contact, passing and opposing contact. Adapt to actual anatomy. Before expansion, create a pose plan from [keypose-plan.example.json](assets/keypose-plan.example.json) and run keypose-check. Check every image's canvas, origin and index; then visually inspect grip and action phases. Structural preflight does not prove artwork quality.
3. **Directions:** establish the required facings from the same master. Inspect each direction's occlusion and handedness. Mirror only when the character is truly symmetric and the project allows it.
4. **Expansion:** produce small coherent clips using approved first pose, key poses and references. Keep one canvas and origin; leave room for the actual weapon/effect path. Use host-supported image tools for generation/editing when required by host policy; use native project sources for code/vector editing. Do not assume a prompt can enforce exact frame topology.
5. **Normalization:** before slicing an aggregate generated sheet, create a reviewed sheet-layout contract and run `sheet-separability-check`. If it reports overlap/no-gutter risk, do not midpoint-slice or watershed-split and then repair the amputated result; hidden composited pixels are unavailable. Regenerate isolated cells/strips, use editable layers/source reconstruction, or switch to a deterministic/native rig. Once the source is separable, extract to explicit named frames, retain durations, dispose/composite animated sources correctly, and pad without resampling. Preserve known origin offsets. Never auto-center every frame by its changing bounding box. When keeping a larger authoring master and a smaller runtime derivative, apply one family/clip-wide transform and origin mapping to every frame, preserve the master, and re-run Technical + Visual QA on the runtime derivative.
6. **Rig before cut (modular/cutout work):** when a character is separated into parts (modular equipment, HD cutout rigs, part reskins), define the rig on the neutral master FIRST — joints and anchors in body coordinates saved as `rig.json` — then cut, then verify reassembly against the master with `scripts/verify_rig.py` (exact RGBA reconstruction, pivots on opaque pixels; NCC is diagnostic) before any animation or swap. Follow [rig-map.md](references/rig-map.md); schema: [rig-map.example.json](assets/rig-map.example.json).
7. **Consistency instrumentation:** for animation that can drift, run `motion-check` against current `production-metadata.json` before visual approval. Inspect flagged adjacent-frame pairs, static regions, sockets, depth profiles and locomotion calibration. Thresholds identify suspicious changes only; unflagged frames still require visual review. For a multi-character roster, create a family contract and run `family-check` before claiming the set shares one art direction.
8. **Review and repair:** follow the gates below. Freeze the candidate before editing, declare affected frame IDs, and fix the smallest affected group; include neighboring poses, opposing gait phases or related directions when the problem spans them. Run `repair-diff BEFORE AFTER --allowed-frame ID` (repeat per ID) to prove untouched files and timing/geometry remain unchanged. A `scope_pass` is preservation evidence, not artistic approval. Dependency edits block a frame-only repair; use `checkpoint` to identify invalidated clips and redo affected reviews. After two unsuccessful repairs of the same defect, change method (editable key pose, smaller clip, simpler design or a different available tool) rather than repeating the same prompt.

Do not generate an entire character roster before a representative set passes. If work is interrupted, resume from the contract, log and approved candidates rather than resubmitting generation jobs. Do not weaken the acceptance criteria to fit the output.

## Keep three acceptance gates separate

### Technical

For sprite animation run `validate`, `inspect` and `preview`. When a consistency contract exists, also run `motion-check`; for roster deliveries also run `family-check`. For UI run `ui-check` after deterministic slicing/export. For environments run `environment-check`; for VFX run `vfx-check`. Structural success is never visual approval. Verify actual dimensions, exact clip/frame/state count, readability of files, alpha/text policy, durations, edge contact, nine-slice geometry, anchors/footprints, VFX timing/canvas and suspicious duplicates. The toolkit reports possible clipping, drift and non-universal heuristics as review items, not universal artistic failures.

### Visual

Prepare current preview/screenshot evidence, then run `review-template --evidence PATH` (repeat for each artifact) to bind a **new blank schema-2 review** to current contract, image and evidence hashes. Old unbound reviews must be recreated. Open the current contact sheet and playback using available vision/browser capabilities, inspect all clips and directions, then resolve each dependency finding in `finding_reviews` with bound evidence and concrete observations, and fill each check with verdict and concrete observations/frame references. Review identity, camera/facing, anatomy/grip, motion/timing, origin/ground behavior, transparency/clipping and transitions/events. Explicitly compare landmark continuity, frame-to-frame identity/material stability, socket-to-visible-art alignment, direction-specific occlusion/depth and family consistency when applicable. Follow [visual-review.md](references/visual-review.md).

Never fill observations from intended prompts. Never update an old completed review's digest to bypass re-review. If images cannot be viewed, leave the visual gate incomplete. Use evidence paths from the template's evidence_files keys; keep every inspected artifact unchanged. Run `qa` with the filled review. It checks evidence binding and assertions, not independent visual truth.

For UI use `ui-review-template` → inspect actual screen/component evidence → `ui-qa`. For environments use `environment-review-template`/`environment-qa` on assembled-map evidence. For VFX use `vfx-review-template`/`vfx-qa` on current effect playback/contact-sheet evidence, including socket alignment and light/dark readability. These profiles preserve the same rule: a completed form without actual inspected evidence is not approval.

### Runtime

Use [field-verification.md](references/field-verification.md) for real-scale art, planted feet, transition continuity, rendered impact frames, hit/miss tests and runtime evidence. For UI, runtime acceptance additionally requires current evidence for responsive layout, safe area, touch/input behavior, states, localization overflow and nine-slice behavior across every declared `runtime_test_matrix` case. Before visual approval, a **draft scene may load raw candidate frames** to reveal gameplay defects; mark it `raw_source_test`, preserve its source binding and never treat it as an approved release or a verified export. This enables visual engine testing without weakening the release gate.

Export only after current technical+visual approval. Verify actual target engine import, correct facing, timing/events, loop/terminal behavior, scale/filtering, origin and texture budget in a test scene. Keep runtime status `not_tested` until it runs in the requested engine/project. Reuse check_godot.gd or check_pixi.cjs for a headless smoke check where appropriate, then perform actual visual engine review; the smoke checks do not approve rendering, art or combat-event dispatch. An offline HTML preview or valid engine resource file does not count as runtime acceptance. After the actual engine test, create runtime-template with captured evidence, fill actual observations, then run runtime-verify. Finish with `release-check` to bind the current source, visual review, exported bytes and runtime review together. It checks export/evidence identity and reviewer assertions; it does not independently run the engine or prove artistic truth. UI uses `ui-runtime-template`/`ui-runtime-verify`; environments use `environment-runtime-template`/`environment-runtime-verify`; VFX uses `vfx-runtime-template`/`vfx-runtime-verify`. Every final runtime template requires the corresponding current visual review to be approved first.

## Standalone toolkit

Require Python 3.10+ and Pillow. Do not install or call external paid services merely to run these commands.

```bash
python3 <skill>/scripts/sprite_tools.py validate animation-set.json
python3 <skill>/scripts/sprite_tools.py inspect animation-set.json --out inspect-01.json
python3 <skill>/scripts/sprite_tools.py preview animation-set.json --out preview-01
python3 <skill>/scripts/sprite_tools.py motion-check animation-set.json --contract production-metadata.json --out motion-check-01.json
python3 <skill>/scripts/sprite_tools.py review-template animation-set.json --evidence preview-01/contact-sheet.png --evidence preview-01/index.html --out review-01.json
# View current files and fill observations before QA.
python3 <skill>/scripts/sprite_tools.py qa animation-set.json --review review-01.json --out qa-01.json
python3 <skill>/scripts/sprite_tools.py pack animation-set.json --review review-01.json --out release-01
```

Use `sheet-separability-check` before deterministic slicing of aggregate generated sheets, `keypose-check` before transition generation, `motion-check` for temporal/metadata/calibration review signals, `family-check` for roster invariants, `ui-check` for UI component/state/touch/nine-slice structure, `ui-slice` for explicit non-resampled component extraction, `ui-review-template`/`ui-qa` and `ui-runtime-template`/`ui-runtime-verify` for UI gates, `environment-check`/`vfx-check` plus their evidence-bound visual/runtime commands for those contract types, `vfx-pack-plan`/`vfx-pack-bundle-check` for sellable VFX packs, `repair-diff` after scoped corrections, and `runtime-template`/`runtime-verify` for sprite engine acceptance. Use `extract` for GIF/WebP or an explicitly described grid, and `pad` for lossless motion-space preparation. See command help and [toolkit.md](references/toolkit.md). `pack` writes one or more atlases (optional trim/extrusion with original offsets), generic timeline metadata, PixiJS-compatible frame metadata, a Godot SpriteFrames resource, timed and shared-clock PixiJS adapters, an export identity manifest and an initially blank runtime review. It does not create Spine skeletons or prove engine compatibility by itself.

## Finish honestly

Deliver authored/editable sources when available, approved frames, atlas/timeline data, visual proofs, QA results and actual runtime evidence. Report engine/version, tests performed, unresolved stages and practical limitations. Distinguish observed defects, inferred causes and newly designed motion. Save user deliverables through the host's storage workflow; never label a draft or unresolved family production-ready.

For source-driven sheet reconstruction and raster processing, use the companion `process-sprite-sheets` skill when installed; keep one authoritative asset contract and revalidate the frames in this skill's workflow.

For maintenance and representative forward tasks, read [evaluation.md](references/evaluation.md).

## Integrated rig animation tools

For parent-child cutout motion, editable bone keyframes, baked IK, animated equipment, gameplay events, sockets, coverage and GIF/sheet previews, use `tools/rig-animation/scripts/rig-tool.mjs`. Read [rig-editor-bridge.md](references/rig-editor-bridge.md) before authoring and [the agent workflow](tools/rig-animation/references/agent-workflow.md) for the CLI and schema. Render candidate frames into this skill’s animation-set and production-metadata schemas; preserve all three acceptance gates.

## Studio sprite/VFX authoring

For nondestructive raster variants, texture flipbooks, seeded particle layers, socket trails, shared clip/event preview and candidate VFX export, read [studio-production.md](references/studio-production.md). Use the integrated rig-animation v2.2 production CLI even when no containing repository is available. For engine selection and adding adapters, read [multi-engine-handoff.md](references/multi-engine-handoff.md). Preserve separate visual and runtime acceptance.

## Unified repository routing

Read [rig-editor-bridge.md](references/rig-editor-bridge.md) for the Git/local workspace route when a containing repository provides the editor and studio CLI. Use its AGENTS.md and docs/LOCAL.md; keep source revision and all three acceptance gates. Use the standalone toolkit normally when installed outside that repository.
