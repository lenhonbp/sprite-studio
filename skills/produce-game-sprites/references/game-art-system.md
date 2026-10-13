# Game-art system extension

The core skill remains sprite-first, but a production game needs multiple asset families to share one visual language. Use this guide when the request expands beyond characters.

## Route by runtime asset role

Choose the smallest production route that directly matches the deliverable:

| Asset family | Production route | Key contract |
|---|---|---|
| Character/monster animation | Existing sprite workflow | animation-set + production metadata |
| UI/HUD/menu/icons | UI/UX workflow | ui-contract |
| Props/items/equipment | Pack/variant workflow | shared silhouette/scale/palette + upgrade lineage |
| VFX | VFX workflow | socket, timing, blend/alpha, loop/one-shot |
| Terrain/tiles/maps | Environment workflow | tile footprint, anchor, seam/layer/collision policy |
| Cutout/Spine | Modular workflow | rig/slot/atlas geometry + runtime version |
| Audio/game design | Adjacent capability | keep separate from sprite acceptance gates |

Do not combine multiple generative steps merely because they are available. Every generative hop can alter identity, scale, palette, edge treatment and geometry.

## Shared art-system tokens

Across asset families, record only the tokens that matter to the project:

- camera/projection and facing convention;
- native pixel density or HD scale tier;
- palette/value range and outline language;
- material/shading rules and light direction;
- world scale: character height, tile size, prop scale tiers;
- UI border/icon language and rarity colors;
- VFX brightness/translucency limits;
- export sampling and alpha policy.

A character family can pass its own QA and still fail the game-art system if its scale or rendering language does not fit the map/UI.

## Same-style packs and upgrades

For related assets and upgrade variants:

- hold one reviewed reference/style system constant;
- describe the concrete difference per variant rather than repeating generic quality wording;
- preserve canvas, scale and anchor across related variants;
- add transparent room only in the direction required by the largest upgrade/effect;
- inspect every output rather than assuming pack-level consistency;
- keep upgrade lineage and source revision in provenance metadata;
- for equipment that attaches to a body, validate grip/slot/anchor compatibility, not only appearance.

Use batch generation for ideation/coverage; use individual repair for weak members.

## Related game systems

Keep audio and game-design acceptance separate from visual asset acceptance. Preserve event IDs and timing so sound and gameplay systems can use them later without changing the art pipeline.
