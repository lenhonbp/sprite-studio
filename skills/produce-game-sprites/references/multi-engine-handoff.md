# Engine-independent asset and VFX handoff

Made by Nhon Le. Keep one editable source and target-engine adapters at the edge.
Do not fork authoring, frame timing, origins or art contracts for each engine.

## Scope and selection

The produce-game-sprites toolkit's body/UI/environment PNGs and generic atlas/
timeline metadata are portable. Existing body `pack` still generates its original
Godot/Pixi resources; do not claim it generates native Unity/Cocos/Phaser body
animation controllers. The rig-animation v2.2 **baked VFX** exporter adds concrete
adapter source for Canvas 2D, Phaser 3, Three.js Sprite, Unity 6 SpriteRenderer,
Cocos Creator 3.8, Godot 4 and PixiJS 8. Generic PNG + JSON is available without
any engine-specific adapter. Unreal/Paper2D, Defold, LÖVE, Bevy and custom engines
can use the generic data but do not yet have bundled native importers.

List targets without reading a project or requiring canvas:

```
node <skill>/tools/rig-animation/scripts/production-cli.mjs engines
node <skill>/tools/rig-animation/scripts/production-cli.mjs vfx hero.rig.json --clip attack_se --fps 12 --engine phaser --out candidate-phaser
```

`--engine` accepts all (default), generic, canvas, phaser, three, unity, cocos,
godot or pixi. Unknown targets fail before rendering/writing. Engine selection
changes adapter files only: PNG bytes, frame geometry and authored times remain
identical. Read engine-pack.json for the selected target, source file, coordinate
mapping and actual check level. Read the exported ENGINE-INTEGRATION.md for setup.
In the containing repository use `npm run production -- engines` or the editor's
Engine xuất selector. Exports refuse an existing output directory.

## Integration rules

- PNG is straight-alpha RGBA/sRGB; atlas rects use top-left pixel coordinates.
  Preserve original size; disable importer compression/downscaling, atlas rotation
  and inappropriate mipmaps. Choose filtering from the art/project contract.
- Frames remain full canvas. Align exported origin with the actor ground point.
  Convert Y for upward-axis runtimes; Unity also converts atlas rect and pivot.
  Do not reattach already baked socket paths to the moving weapon socket.
- Draw back tracks, actor, then front tracks. Preserve normal/additive separately.
  Unity/Cocos require project-owned verified materials; no assumed URP/Built-in
  shader, premultiplied-alpha convention or universal loader is silently added.
- Use seek(gameClipTimeMs) from one clock. Use milliseconds, half-open intervals,
  hide at one-shot completion, loop at exact duration, and reset on clip change.
  Keep gameplay events/damage dispatch in the game; never infer hits from PNGs.
- Three's adapter targets a camera-facing orthographic XY overlay with flipY=true
  TextureLoader pages. It is not a world mesh/skeleton or perspective controller.
- Load pages with the project's asset manager. New players borrow textures and
  materials; destroy the player-owned frames/textures/scene nodes on clip disposal.
  Shared-clock .mjs and .d.mts files accompany TypeScript integration.

## Verification and extension

Run vfx-check and inspect actual current light/dark imagery; keep visual review
blocked when the sample is unreadable or cuts off. API-model/Node transpilation
checks are technical tests, not target-engine compilation or rendered acceptance.
Keep runtime not_tested until the actual requested engine/version/project runs,
with current evidence for origin, nonzero atlas rows, exact timing, transitions,
blend/layering and target-device performance. Use the VFX evidence-bound runtime
workflow; generic export does not bypass it.

Add future adapters in tools/rig-animation/scripts/engine-adapters.mjs and register
an honest check level. Preserve the baked schema and all existing targets. Test
nonzero atlas rows, asymmetric pixels, interval gaps, seek backwards, terminal/
loop boundaries, borrowed-resource ownership and blend/depth before release.
If the containing repository exists, sync browser assets with npm run build and
run npm run test:engines plus existing tests. Do not implement a new engine by
renaming another adapter or inventing a compatibility verdict.
