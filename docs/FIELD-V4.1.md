# v4.1.0 multi-engine audit / field — 2026-10-11

Made by Nhon Le. Scope: engine-independent baked VFX export, seven concrete
adapter sources plus generic PNG/JSON, editor/CLI selection, full skill routing.
Authoring schema and raster masters are preserved. No native body animation
controller, shader graph or GPU particle conversion is added.

## Checks actually executed

- Nine engine tests: target/file selection, manifest validation, half-open clock/
  gaps/backwards seek/loop/terminal, independent native-canvas pixel comparison,
  explicit Phaser/Three API-model mapping/resource ownership, Cocos TypeScript
  transpilation with Node plus explicit API model, real CLI processes and exact
  PNG/geometry/timing equality between generic and all-target exports.
- Phaser test runs two players over borrowed pages, then disposes one and proves
  the other's frame names still exist. Three test uses asymmetric nonzero atlas
  rows and checks UV Y conversion, Y-up actor origin, sRGB annotation, disabled
  tone mapping and destruction of owned clones, leaving borrowed pages intact.
- Canvas test draws nonzero-row asymmetric atlas cells, then an intervening body,
  then additive front VFX and compares actual pixels with an independent draw
  reference across start, gap, frame boundary, active end and clip terminal.
  It verifies the caller's context alpha/composite state is restored.
- Modular editor and generated offline HTML: actual downloaded ZIP source bytes
  match the canonical adapter/clock/type/guide text. Phaser and generic selection
  includes only selected adapter files and preserves unrelated unsaved forms.
  DOM is a model, while raster work uses native canvas; browser CSS/touch is not
  inferred from these results.
- Existing 17 production and 45 rig tests passed; service/local/bridge/vault
  suites and real HTTP field (six-process CAS, rollback, restart, stdio, network
  recovery and crash-before-rename) passed on the v4.1 code.

Two first-run test assertions were corrected: native canvas stores a quantized
alpha value, and floating-point UV math requires numeric tolerance. Exact PNG/
RGBA comparisons remain exact. Three's source additionally annotates cloned PNG
textures sRGB and disables material tone mapping; renderer output remains owned
by the game. Unity candidate cleanup also destroys owned child nodes and sprites
on disposal or failed allocation; this is source-reviewed, not Unity runtime tested.
The original v4 art findings still stand in FIELD-V4.md.

## Source and acceptance boundaries

Unity source has not been compiled, and Cocos has not been compiled in its editor.
Node TypeScript transformation is syntax/transpilation evidence, not Cocos SDK
validation. Phaser/Three/Pixi tests use explicit API models; their SDK/GPU/game
rendering has not run. Godot engine is unavailable in this environment. All
exported engine targets keep runtime not_tested and visual not_reviewed.

Engine SDKs, project loaders, Unity/Cocos blend materials and phone runtime
performance remain project-owned. Three supports an orthographic sprite overlay
with TextureLoader flipY=true; perspective meshes and ImageBitmap UV conventions
are outside this adapter contract. Body pack's original native Godot/Pixi resource
outputs are unchanged; other engines can consume generic sprite data but no new
native body controller is advertised. Generic targets do not claim native Unreal,
Defold, LÖVE or Bevy importers.

## Reproduce

Run npm run build, npm run audit, npm test, npm run test:production,
npm run test:engines, npm run test:field and npm run test:canvas. Node 22.13+ is
required for the test suite's TypeScript transformation; ordinary production CLI
needs Node 22+. Rendering needs optional @napi-rs/canvas; tests used the installed
runtime fallback. No engine downloads or native binaries are included.

## Independent handoff and final archive — 2026-10-12

A fresh agent used only the bundled skill and the raw combat-vfx source to make
Phaser, Unity and generic packs at 24 FPS. Each has 45 active frame PNGs/three
tracks and nine atlas files, eight of which are referenced by active frames.
All nine per-target VFX contract checks reported no errors and review_required;
this is technical preflight, not visual approval. Source SHA256 remained
606581005513aab326866f13f38b572af285c07b045d6125dc1f1e9e9c1055fa.

Independent checks passed for the real clip clock, all 45 native source RGBA/
atlas cells, Phaser's actual exported timelines through an explicit API model,
and matching final adapter bytes to the stable exporter. An additional Unity
source-substring assertion expected the older unguarded disposal statement and
failed after cleanup gained null checks, child-node disposal and a helper. Its
failure log is retained; it is not counted as Unity compilation/runtime success.
Current Unity source was inspected and remains source-only candidate evidence.
Initial concurrent-build outputs were retained and replaced by new final paths;
no source or live .studio data was overwritten.

The packaged source was extracted and passed audit, nine engine tests, 45 rig
checks, modular/offline editor ZIP-byte/selection/draft tests and the full
service/local/bridge/vault suite. Production and HTTP field tests had also passed
on the same v4.1 implementation. See [field-summary.json](evidence-v41/field-summary.json)
and [independent-checks.txt](evidence-v41/independent-checks.txt). All visual/runtime
gates remain explicit; no independent source-string test can approve an engine.
