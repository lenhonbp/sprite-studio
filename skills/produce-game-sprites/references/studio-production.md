# Sprite Studio v4 production authoring

Keep produce-game-sprites v3.8's Technical → Visual → Runtime gates. The integrated
rig-animation v2.2 tools add optional `studio` production data to existing rig/v1
sources. Old sources remain valid. Samples are technical candidates, not approved
character art or a production-ready effect pack.

## Authoring and agent route

When working in the containing Sprite Studio repository, read AGENTS.md and
`docs/PRODUCTION.md`. UI, live studio CLI and local MCP share revision CAS and
undo/redo. Read before editing. Submit effect/asset operations in one atomic batch;
new assets must use new IDs. Preserve raster masters and variant lineage.

Outside the repository, use this skill's standalone module:

```
node <skill>/tools/rig-animation/scripts/production-cli.mjs help
node <skill>/tools/rig-animation/scripts/production-cli.mjs check hero.rig.json
node <skill>/tools/rig-animation/scripts/production-cli.mjs sample hero.rig.json --clip attack_se --time 333
node <skill>/tools/rig-animation/scripts/production-cli.mjs edit hero.rig.json --args operations.json --out candidate.rig.json
node <skill>/tools/rig-animation/scripts/production-cli.mjs preview candidate.rig.json --clip attack_se --time 333 --background dark --out proof.png
node <skill>/tools/rig-animation/scripts/production-cli.mjs vfx candidate.rig.json --clip attack_se --fps 24 --out candidate-vfx
```

Render requires the optional @napi-rs/canvas dependency; authoring/check/sample do
not. Use project-owned textures or authored/generator candidates, never pass a
procedural texture sample off as hand-painted production art. Select a small
representative effect before expanding a pack.

## Contract

The optional `studio` object has schema `nhon-le-production/v1`, effects,
bindings, assetInfo and scene. Read the portable core's validation and sampling
code at `tools/rig-animation/scripts/studio-core.mjs` for exact constraints.

- Effect: ID, name, duration_ms, loop, blend (normal/additive), deterministic uint32
  seed and ordered layers. Each layer has texture, half-open start/end, offset,
  rotation, size/alpha curves spanning 0..1, and RGB tint.
- Layers: sprite with optional ordered PNG flipbook; texture particle burst or
  timed emitter with lifetime/speed/gravity/spread; connected socket trail with
  width/history/samples. Position curves and GPU shader graphs are not implemented.
- Binding: effect+clip, time trigger or named gameplay event, actor origin/socket/
  world space, offset, follow flag, front/back depth. Repeated named events produce
  separate instances. Clip clock controls reset; effects do not persist through
  a clip transition. `follow` moves emission origin at birth; emitted particles
  retain their world position trajectory. Trail points follow historical socket
  positions. It is not a live hitbox or a damage model.
- Asset: preserve original embedded PNG; save edits with a new ID and variantOf.
  Optional role, source, license and tags document provenance, not ownership proof.

Linked socket/event deletion fails validation. Unbind first, then delete within
one batch. Rename/retime clips preserves time bindings. Do not invent missing
poses, directional occlusion, or socket positions from metadata.

## Export and acceptance

`vfx` outputs isolated RGBA frames, atlas pages, millisecond timing, per-effect
front/back split, blend intent, original source, candidate Canvas/Phaser/Three/Unity/Cocos/Godot/Pixi adapters
and per-track vfx contracts. Baked coordinates are **actor canvas coordinates**:
align the exported origin with the actor ground origin. Do not attach the baked
trajectory to the moving weapon socket again. Keep character and additive effects
separate. Sprite `rig-tool render/sheet/gif` remains body/equipment export only.

Run `vfx-check` on each exported `*-contract.json`; inspect contact sheets and
light/dark playback, then bind evidence using `vfx-review-template`/`vfx-qa`.
Only after actual target-engine tests use vfx-runtime-template/verify. Check front/
back layering, origin, texture filtering, alpha, blend, loop seams, contact poses,
transitions and target-device performance. Adapter files and native canvas proofs
alone do not meet the runtime gate.

`source-unpack` writes editable PNG files plus a manifest; `source-pack` assembles
it back without changing PNG bytes. Do not edit the live .studio state directly;
import the reassembled source through studio_replace with a current revision.

Socket/layer offsets use the sampled socket transform. Optional binding inheritRotation follows socket angle for sprite/emission direction; textures retain authored pixel size. Trail orientation follows path tangents. Native sampling caches pose transforms within each sample.

Baked export trims leading/trailing transparent padding from each track, preserving absolute frame timestamps and active_start/end_ms. Internal transparent frames remain and can block visual QA. Contracts cover the active interval and retain clip clock/events as context. Clip completion clears effects in preview and adapters; authored tails crossing clip end are reported, not automatically repaired.

Select engines with `production-cli.mjs engines` and `vfx --engine all|generic|canvas|phaser|three|unity|cocos|godot|pixi`. Read [multi-engine-handoff.md](multi-engine-handoff.md) for supported scope and engine-owned import/material settings.
