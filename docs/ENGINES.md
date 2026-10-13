# Sprite Studio v4.1 — multi-engine export

Made by Nhon Le. The authoring engine and source format are independent of game
engines. This release adds engine selection to the **baked VFX** pipeline.
Body/sprite/UI/environment sources remain portable PNG/atlas/timeline data; their
existing native body resource exporter has not been rewritten for every engine.

| Target | Bundled integration | Verification in this release |
| --- | --- | --- |
| Generic | PNG, vfx.json, engine-pack.json, shared clock | Schema/timing/byte equality |
| Canvas / HTML5 | canvas-vfx.mjs | Native Canvas 2D pixel comparisons |
| Phaser 3 | phaser-vfx.mjs, preload helper | Explicit API-model contract tests |
| Three.js | three-vfx.mjs, Sprite overlay | Explicit API-model UV/origin/resource tests |
| Unity 6 | NhonLeVfxPlayer.cs, SpriteRenderer | Reviewed source; editor/compiler unavailable |
| Cocos Creator 3.8 | cocos-vfx.ts + shared .mjs/.d.mts | Node TypeScript transpilation + explicit API model |
| Godot 4 | godot-vfx.gd | Existing candidate source, no engine run |
| PixiJS 8 | pixi-vfx.mjs | Existing explicit API-model clock tests |

All target runtimes remain not_tested. Native canvas checks do not certify a
browser, GPU or an engine scene. Engine versions are intended API families,
not claims that every future or older version is compatible.

## Use

In the VFX tab, choose Engine xuất before exporting. Default is all adapters.
The choice does not modify source or discard unsaved forms.

```
npm run production -- engines
npm run production -- vfx projects/combat-vfx.rig.json --clip attack_se --fps 12 --engine all --out vfx-all
npm run production -- vfx projects/combat-vfx.rig.json --clip attack_se --fps 12 --engine unity --out vfx-unity
npm run production -- vfx projects/combat-vfx.rig.json --clip attack_se --fps 12 --engine generic --out vfx-portable
npm run test:engines
```

The selected pack includes one manifest, the same RGBA PNGs, source rig, QA
contracts, selected adapter(s) and ENGINE-INTEGRATION.md. No engine SDK, binary,
paid service, provider credential or asset loader is bundled. Generic has no
engine-specific adapter. Unknown names fail before creating an output directory.

## Common mapping

The pack records top-left rects, X-right/Y-down pixels, actor ground origin,
straight alpha, per-track normal/additive, front/back, half-open millisecond
intervals and terminal hiding. Export paths are actor-canvas baked; do not attach
the effect to a moving socket again. The game owns the clip/event/damage clock.
Unity converts rect Y/pivot and uses project-owned materials. Cocos uses Y-up
nodes/top-left UI anchor and project-owned sprite materials. Three requires an
orthographic overlay and flipY=true textures. Atlas imports must preserve size
and avoid edge bleeding; set project filtering and color handling explicitly.

For Unreal/Paper2D, Defold, LÖVE, Bevy or another engine, use generic PNG + JSON
and implement a project importer. No native importer for these targets is included.
The registry can be extended without changing source or re-authoring the asset.
Read the bundled skill's [multi-engine handoff](../skills/produce-game-sprites/references/multi-engine-handoff.md).

## Official API references inspected

- [Canvas compositing](https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/globalCompositeOperation)
- [Phaser Texture.add](https://docs.phaser.io/api-documentation/class/textures-texture)
- [Phaser Image](https://docs.phaser.io/phaser/concepts/gameobjects/image)
- [Three Texture](https://threejs.org/docs/pages/Texture.html)
- [Three SpriteMaterial](https://threejs.org/docs/pages/SpriteMaterial.html)
- [Unity Sprite.Create](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Sprite.Create.html)
- [Unity JsonUtility](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/JsonUtility.FromJson.html)
- [Cocos 3.8 Sprite](https://docs.cocos.com/creator/3.8/manual/en/ui-system/components/editor/sprite.html)
- [Cocos 3.8 UI materials](https://docs.cocos.com/creator/3.8/manual/en/ui-system/components/engine/ui-material.html)
- [Cocos SpriteFrame](https://docs.cocos.com/creator/3.8/api/en/class/SpriteFrame)
- [Cocos UITransform](https://docs.cocos.com/creator/3.8/api/en/class/UITransform)

Official documentation review supports the source design; it is not an engine
compile/play test. See [FIELD-V4.1.md](FIELD-V4.1.md) for actual evidence and limits.

The engine test suite uses Node 22.13+ for built-in TypeScript transformation; production commands remain Node 22+.
