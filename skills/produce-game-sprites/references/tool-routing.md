# Choose available tools

Inventory first: project files, editable source, renderer, image tools, animation tools, local executables, vision, runtime. Record observed availability. Python/Pillow processes pixels; it does not replace character drawing or a motion model.

| Situation | Route | Mandatory evidence |
|---|---|---|
| Existing editable art | Preserve source layers/tags; edit key poses in the project’s native format | Inspect rendered output and retained source timing |
| New bitmap character, image-generation capability available | Generate master → referenced key poses → small clips | Open actual images, check identity and action |
| Existing vector/code art | Edit source primitives/rig, render at native target | Inspect contours and articulated motion |
| Stable body with reusable equipment | Hybrid body/attachments/VFX | Check grip, occlusion and attachment trajectory |
| Existing sheet or animation | Map topology first; preserve source timing/offsets | Reconstruct cells before restyling |
| UI/HUD/menu work | Wireframe/reference → textless kit → named states/components → runtime layout | `ui-check`, component/state proof and actual screen UX evidence |
| Aggregate UI/asset sheet | Review segmentation/rectangles → deterministic crop or component redraw | Stable names, exact bounds, no accidental labels/text |
| Props/items/upgrades | One approved style source → coherent pack/variants → per-member repair | Scale/anchor/style lineage and gameplay readability |
| Terrain/map/tiles | Logical footprint/anchor → assembled preview → seam/depth/collision review | Map screenshot, repeated seam test, runtime sort proof |
| Spine/cutout/modular | Inspect rig/atlas → smallest part edit → reassembly/runtime round-trip | Slot/attachment/atlas geometry and target-runtime playback |
| Optional hosted capability explicitly requested and available | Use the host-supported capability | Inspect final media and record its source/revision |
| No usable drawing/generation tool | Complete contract, source mapping, QA/packaging of real supplied art; report blocked creation | Never invent a generation result |

Use the host's required image tool for raster generation/editing. Do not route around tool restrictions with shell HTTP requests. Processing supplied/generated frames into sheets or validating them is a separate task. Respect project-installed versions and dependency policies.

When no motion tool exists but editable layered art does, construct articulated key poses and authored in-betweens. This is feasible for simple stylized designs, but not proof of equivalent quality to a learned motion model. Translation/rotation of an entire still can be a deliberate hit reaction or floating idle; it cannot stand in for a required walk/run/sword attack. Declare any such limited motion explicitly.

Fallback changes must preserve the asset contract or be reported as a scope limitation. Tool availability does not prove that the result meets the art direction; inspect the actual output.


For UI/UX read [ui-ux-production.md](ui-ux-production.md); for multiple asset families read [game-art-system.md](game-art-system.md); for environment work read [environment-production.md](environment-production.md); for Spine/modular work read [spine-modular-production.md](spine-modular-production.md); for VFX read [vfx-production.md](vfx-production.md). Route by the requested runtime asset, not by whatever generator happens to be available.
