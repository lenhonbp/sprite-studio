# Sprite Studio v4.1.1 — asset / sprite / VFX

Made by Nhon Le. This release adds usable production authoring to the existing
rig editor; it is not an automatic replacement for an artist or game engine.
Full produce-game-sprites v3.8 remains bundled, with rig-animation v2.2.

## Quick vertical slice

1. Run `npm start`, open the editor and import `projects/combat-vfx.rig.json`.
   This sample reuses the preserved raster master, has only SE/three clips and is
   unapproved. Select attack_se, enable VFX and the target marker, scrub/play.
2. Open the VFX tab. Select slash, burst or aura. Edit common fields, layer JSON,
   size/alpha curves and tint. Save the relevant panel. Drag a time-bound VFX range
   on the timeline to move its start. Event-bound starts move when their event is
   edited; they cannot be dragged independently from the gameplay event.
3. For an authored flipbook, import isolated PNG frames into Assets, add a sprite
   VFX layer and set frames/frame_ms in layer JSON. Names must reference existing
   image IDs. Keep frame canvas/origin consistent before importing.
4. Bind to time/event; choose socket/actor/world, offset and front/back. The follow
   flag moves the emitter at particle birth, not previously emitted particles.
   A trail follows historical socket positions. Actor space means canvas origin;
   world space means absolute canvas position. It is not a physics simulation.
5. In Assets choose a PNG and “Chỉnh raster → tạo biến thể”. Brush/alpha eraser and
   stroke undo/redo work on native image pixels. Save a new ID; original PNG bytes
   remain unchanged. Assign the variant to a slot or VFX layer separately. Raster
   canvas <=4M pixels, 32MB stroke history; larger layered edits belong in a native
   paint application. Unsaved forms/raster drafts pause incoming project updates.
6. Export VFX clip ZIP. Character exports remain separate. Source ZIP contains
   individual PNGs and source.json; use source-pack to restore embedded rig JSON.
   Import restored JSON through the live CLI with a real current revision.

Effect loops use the clip clock. A clip transition resets bindings; persistent
cross-clip effects and prewarmed GPU emitters are not implemented. Layer intervals
are [start,end), one-shot effects disappear at the end. Curves are piecewise
linear and must have ordered points spanning 0..1. A repeated named event starts
another instance. Seeded sampling is independent of playback/seek order.

## Agent operations

Use `npm run studio -- read` then studio_edit with current baseRevision and unique
requestId. Up to 50 operations in a batch; all validate or none persist.

```
{"type":"fx-put","effect":{"id":"...","name":"...","duration_ms":700,"loop":false,"blend":"additive","seed":12345,"layers":[...]}}
{"type":"fx-binding","binding":{"id":"slash_attack","effect":"slash","clip":"attack_se","trigger":"time","start_ms":100,"space":"socket","socket":"weapon_tip","offset":[0,0],"follow":true,"depth":"front"}}
{"type":"fx-unbind","id":"slash_attack"}
{"type":"fx-delete","id":"slash"}
{"type":"asset-put","id":"new_texture","attachment":{"image":"data:image/png;base64,...","width":64,"height":64,"pivot":[32,32]},"info":{"role":"vfx","variantOf":"old_texture"}}
{"type":"asset-info","id":"new_texture","info":{"role":"vfx","tags":["sword"],"source":"...","license":"..."}}
{"type":"scene","scene":{"target":[390,320],"radius":28}}
```

Use full effect definitions from a real read; do not send the ellipsis examples.
`fx-put` replaces that effect definition and preserves all other effects. For an
agent-generated image, import real PNG bytes under a new ID. Existing image IDs
cannot be overwritten by asset-put. Metadata records provenance, not a license
verification. studio_view now accepts effectId (or null), clipId and time so the
manual editor can follow the agent's selected effect.

Linked socket/event/texture deletion is blocked. Unbind/remove references before
deleting them. Clip rename updates bindings; retime scales time-based starts.
Duplicating a body clip does not automatically duplicate VFX bindings. Clip
removal removes its bindings. Root/bone/slot editing retains the existing rig
semantics and validation.

## CLI and source roundtrip

```
npm run production -- help
npm run production -- check projects/combat-vfx.rig.json
npm run production -- sample projects/combat-vfx.rig.json --clip attack_se --time 333
npm run production -- preview projects/combat-vfx.rig.json --clip attack_se --time 333 --background light --out proof.png
npm run production -- vfx projects/combat-vfx.rig.json --clip attack_se --fps 12 --engine all --out candidate-vfx
npm run production -- source-unpack projects/combat-vfx.rig.json --out editable-source
npm run production -- source-pack editable-source/source.json --out restored.rig.json
```

Render needs @napi-rs/canvas. Check/sample/JSON authoring/source roundtrip need
only Node22+. CLI refuses existing results. Source-pack rejects parent path and
symlink escapes and preserves image bytes. The live source remains embedded JSON
and has the existing 4MB cap; splitting source files for Git does not remove this
live limit. No API key/model/image provider is bundled or called.

## Export and game integration

The same portable export implementation is used by UI and CLI. It outputs:

- independent RGBA frame PNGs and atlas pages per effect/depth;
- vfx.json: half-open frame times, exact durations, blend, original bindings and
  shared clip events; source.rig.json retains authored data;
- *-contract.json for the bundled vfx-check → visual → runtime workflow;
- engine-pack.json, shared clock and selected Canvas/Phaser/Three/Unity/Cocos/Godot/Pixi candidate adapters; see [ENGINES.md](ENGINES.md).

Each baked frame is actor-canvas coordinates. Align origin with the actor ground
origin; do not reattach the baked path to a moving socket. For Pixi use returned
back/front containers around the body or insert body between them; root origin is
actor ground origin. For Godot put the adapter under the actor at ground origin;
its sprites use -1/+1 z-index. Game-owned ordering may require adaptation. Preserve
normal/additive separation. Adapters play millisecond durations and hide completed
one-shot clips. They do not apply damage or dispatch gameplay events; consume
manifest.events with your own shared gameplay clock.

Run `npm run art -- vfx-check candidate-vfx/slash_front-contract.json`. Review
light/dark playback, loop boundaries and frame/socket alignment. Bind real visual
and engine evidence through the full skill's gates. Native canvas rendering,
valid resources and mock engine tests do not approve target-runtime output.

## Limits and budgets

64 effects, 16 layers/effect, 128 bindings; each effect <=2048 emitter/trail samples,
each clip <=8192 worst-case draws including repeated events. Browser/CLI candidate
VFX export <=64M frame pixels including front/back splits. These are safeguards,
not performance guarantees; use the texture RGBA estimate and test target phones.
No automatic eight-direction drawing, Spine export, shader graph, multitrack audio,
GPU particle adapter, complete native paint-editor integration or AI provider API
is included. Artist-authored textures/poses and actual engine QA remain necessary.

Official adapter references: [PixiJS textures](https://pixijs.com/8.x/guides/components/textures),
[PixiJS scene objects/blend](https://pixijs.com/8.x/guides/components/scene-objects),
[Godot CanvasItemMaterial](https://docs.godotengine.org/en/stable/classes/class_canvasitemmaterial.html),
[Godot AtlasTexture](https://docs.godotengine.org/en/stable/classes/class_atlastexture.html).

Socket/layer offsets use the sampled socket transform. Optional binding inheritRotation follows socket angle for sprite/emission direction; textures retain authored pixel size. Trail orientation follows path tangents. Native sampling caches pose transforms within each sample.

Baked export trims leading/trailing transparent padding from each track, preserving absolute frame timestamps and active_start/end_ms. Internal transparent frames remain and can block visual QA. Contracts cover the active interval and retain clip clock/events as context. Clip completion clears effects in preview and adapters; authored tails crossing clip end are reported, not automatically repaired.
