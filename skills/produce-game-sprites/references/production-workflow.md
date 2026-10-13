# Production direction

## Freeze references

Assign roles: identity master, style sample, camera sample, motion reference and source topology. Do not treat every reference as interchangeable. Record exact files/revisions. A still does not reveal hidden body structure or unseen animation; design those parts and label them as designed.

Keep prompts concise: subject + view + action + essential identity constraint. Reuse the same approved reference block. Start with the shortest sufficient instruction, inspect pixels, then add constraints for observed failures. Avoid hoping that long negative keyword lists will repair anatomy.

## Build a useful character proof

For a top-down martial-arts character, start with the project's actual camera and scale. If unspecified, propose a compact representative set; do not silently assume four or eight directions as a requirement. Include an action with weapon reach to exercise canvas padding, grip and silhouettes.

Separate:
- master identity: proportions, outfit, weapon hand and colors;
- direction poses: camera-facing anatomy and occlusion;
- action poses: gait, wind-up, strike, recoil and terminal posture;
- export settings: cell size, timing, origin and texture memory.

Generate or draw small coherent groups. An action's first pose should already belong to that action. Use key poses to constrain complex attacks before asking for arbitrary in-betweens. Re-inspect direction poses before animation.

Keep approved files immutable. Use candidate directories (`attempt-01`, `attempt-02`) and promote only after review. Log specific defects, attempted changes, actual tool result, hashes and cost when applicable. Preserve old candidate references so comparisons are possible.

## Normalization rules

For pixel art, retain the native pixel grid and nearest-neighbor integer previews. Do not repeatedly pixelate pixel-native output. Do not smooth-resize or independently crop/recenter frames to hide scale drift. For HD art, retain smooth contours and inspect alpha fringes against light and dark backgrounds.

Use the same transparent canvas per set. Record foot/root origin manually from stable source landmarks. Bounding-box centers move when swords swing and robes spread; they are not reliable roots. If an animated source has changing local patches, decode its fully composited frames before extraction. Retain frame durations, including zero/missing duration as an explicit unresolved issue rather than inventing timing.

## Rig before cut (modular and cutout work)

When the character will be separated into parts — modular equipment swaps, HD
cutout rigs, part reskins — define the rig before cutting, not after. Mark
joints and attachment anchors on the neutral master in body coordinates, save
as `rig.json`, cut parts per the rig, then verify reassembly against the master
before any animation or equipment swap. Full protocol: [rig-map.md](rig-map.md);
schema: [rig-map.example.json](../assets/rig-map.example.json); gate:
`scripts/verify_rig.py` (exact RGBA reconstruction, every pivot on opaque part pixels; NCC diagnostic only).

## Expand only after proof

Once representative motion passes, expand required facings and actions. Compare palette, body scale, handedness and same-action rhythm across views. Keep equipment effects separate if repeated generation distorts them. For asymmetric outfits, do not mirror the opposite direction blindly.

If editable-source quality is weak, improve the master/key poses first. If only timing fails, edit timing rather than redraw. If one frame is malformed, repair it with adjacent frames as context. If the master changes, re-review every dependent clip.


## Production v3.3 consistency pass

For any family where frame drift, attachments, depth or runtime movement matters, create `production-metadata.json` before final visual approval. Record only landmarks and sockets that can be defended from visible art or intentionally designed gameplay attachment points. Run `motion-check`, inspect flagged pairs and keep the report with the candidate. A clean report is not an art pass.

For top-down/3/4 characters, establish direction-specific layer order before expanding attacks. Review front/rear hand, weapon crossing, robe/leg overlap and rear/front effects separately for each facing. For in-place walk/run, calibrate stride and authored cycle duration against target world speed, then verify planted feet again in the actual engine.

When producing multiple classes/monsters from one art direction, freeze one approved reference frame per actor and create a family contract. Run `family-check`, then compare those references side by side at native and gameplay scale before bulk expansion.


## Production v3.4 game-art system pass

When the task expands beyond character sprites, keep the same evidence discipline but use the correct asset contract. UI uses `ui-contract.json`; maps use explicit footprint/pivot/layer rules; Spine/modular edits preserve rig/atlas topology; VFX keeps timing/socket/alpha separate from body art. Do not force every asset family through `animation-set.json`.

For UI, start with screen job and hierarchy, then textless structural art, then component/state extraction, then runtime layout. Use `ui-check` before claiming structural completeness and perform actual screen-level tests for safe area, aspect ratio, localization overflow and touch interaction.

For aggregate sheets, treat automatic segmentation as provisional. Promote only reviewed rectangles/names to deterministic slicing. Regenerate or redraw weak components individually instead of repeatedly transforming the entire sheet.

For environment art, verify seams and depth in an assembled test map. For modular/Spine edits, verify neutral reassembly first, representative poses second, and runtime swapping/playback last.
