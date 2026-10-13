# Engine handoff

The standalone packer emits deterministic atlas pages within the declared texture limit, preserving original canvas/origin and per-frame durations. atlas_policy enables trimming and edge extrusion; defaults are multipage=true, trim=false, extrude=false. Export verifies exact RGBA reconstruction from saved PNGs and refuses to overwrite a release directory. Layers/attachment rig import still require the project pipeline.

## Godot

Copy all atlas PNGs and sprite_frames.tres together into the test project. The resource uses relative atlas references, AtlasTexture regions/margins (when trimmed), named clips and frame duration multipliers with speed 1, so values are seconds. Assign the resource to AnimatedSprite2D. Set its offset so the declared origin is at the node's world root (with centered=true: offset = cell_size/2 - origin). Select texture filtering appropriate to pixel/HD representation.

Verify resource parsing and actual playback in the installed Godot version. Check clip names, facing selection, one-shot death, movement speed, damage/cast event times and transition timing. A headless parse check only proves loading, not visual motion quality. Capture actual scene output when available.

## PixiJS

Read animations.json.atlases to load every atlas page and its Pixi metadata, then combine textures by globally unique frame ID. A single page retains atlas.png/pixi-atlas.json; multiple pages use atlas-000.png/pixi-atlas-000.json and so on. Metadata includes sourceSize, spriteSourceSize, optional trim offsets, anchors and animation frame names. Load through the project's PixiJS version and local dependency conventions. The generic animations.json is authoritative for per-frame durations/events; do not assume AnimatedSprite consumes arbitrary millisecond metadata. Use the exported pixi-adapter.mjs to convert duration_ms to AnimatedSprite frame objects with time in milliseconds, or a project timeline player. The adapter takes the project's PIXI namespace and already parsed sheet, disables automatic ticker updates, sets the origin anchor and loop policy. The legacy createTimedSprite caller owns sprite.update(ticker), clip transitions and event dispatch. Prefer createClockedSprite for gameplay events: call controller.advance(deltaMs) once per game tick; do not also call sprite.update. Its shared clock sets the event pose before each callback, handles variable durations, loop boundaries and interruption, and holds one-shot terminal poses. A callback pause holds at the event time and discards the remainder of that tick; resume advances from that point. The project still owns hit/collision logic and cross-clip transitions. Set anchor from origin divided by cell dimensions and use nearest filtering for pixel art.

Test texture loading, anchor, per-frame timing, direction/clip selection, loops/terminal holds and gameplay events. Do not silently download a CDN runtime. Verify exact installed library documentation/version when adding integration code.

## Acceptance record

After export, runtime-review.template.json starts not_tested. Run the actual engine/project, capture logs/screenshots, then use runtime-template with those --evidence paths to create a fresh blank bound review. Record engine/version/project/reviewer, observations and visual/headless/automated modes. Run runtime-verify; it checks unchanged files and complete assertions, not independent engine truth. Report which checks were visual versus headless. Keep blockers explicit if the target engine is missing. pack creates an export candidate; release-check enforces current source/visual/export/runtime identity before finished-release acceptance.

Texture memory estimate for RGBA atlases = sum(page width × page height × 4 bytes) before mipmaps/driver overhead. Texture max size is a contract constraint, not a quality knob. Do not reduce scale to fit a budget without reviewing readability.

## Reusable Godot smoke check

Copy scripts/check_godot.gd into an isolated test project alongside the exported release. Import textures, then run:

```bash
<godot> --headless --path <test-project> --editor --import
<godot> --headless --path <test-project> --script res://check_godot.gd -- res://release
```

The script loads the actual SpriteFrames, checks named clips/atlas geometry/durations and advances AnimatedSprite2D to test loops and terminal holds. A headless_pass is not visual approval. It does not test combat-event dispatch, world-space foot contact, rendered filtering or the user's complete game. The original package contains a historical v2 smoke record. This v3.8 update has not rerun Godot; no engine compatibility is inferred from that record.

Official timing/resource reference: https://docs.godotengine.org/en/stable/classes/class_spriteframes.html
Official PixiJS reference: https://pixijs.download/release/docs/scene.AnimatedSprite.html


## Reusable PixiJS smoke check

Use the project's installed PixiJS v8; never download a CDN runtime implicitly. Decode each page PNG to raw RGBA with Pillow. Pass a single file for a one-page release or a directory containing atlas-000.rgba etc. for multiple pages, then run:

```bash
node <skill>/scripts/check_pixi.cjs <release> <atlas.rgba> <local-pixi-module-path>
```

The script uses the actual PixiJS Spritesheet parser and exported timed-sprite adapter to check geometry, anchors, authored timing and loop/terminal holds. The texture uses decoded real atlas bytes in BufferImageSource. It does not test browser PNG loading, GPU rendering, visual filtering, gameplay event dispatch or the user's full project. The original package contains a historical v2 PixiJS 8.22.0 smoke record. This v3.8 update has not rerun the actual PixiJS parser/rendering; keep runtime status not_tested until local execution.

## UI/HUD handoff

Generated UI art is not a screen layout. Keep component art, runtime text and interaction geometry separate.

### Godot UI

Use `Control`/container hierarchy and project-appropriate anchors/offsets rather than absolute coordinates tied to one phone size. Use `NinePatchRect` (or ThemeBox equivalents) for panels/buttons whose declared nine-slice contract allows resizing. Keep runtime/localized text in Label/RichTextLabel or project text components rather than baking copy into panel textures. For pixel UI, verify filtering and pixel alignment at the actual stretch mode; a technically integer-sized texture can still blur when parent controls or viewport scaling introduce fractional transforms.

Test at the project's minimum, reference and maximum supported aspect ratios, including notched/safe-area layouts where the project supports them. Verify empty/full inventory, long localized strings, modal back/cancel behavior and disabled/selected/cooldown states.

### PixiJS UI

Build screens from named component sprites/containers rather than a single composite screenshot. For scalable panels, use the project's PixiJS nine-slice primitive or equivalent and keep declared corner regions unscaled. Keep hit areas explicit; the visible sprite bounds need not equal the touch target. For pixel UI, inspect `resolution`, CSS/browser scaling and sprite transforms together so the final device presentation does not land on fractional source pixels unexpectedly.

Use the `ui-contract.json` paths/state groups as the mapping source. `ui-check` proves only that the declared assets and structural rules are coherent; actual browser/device interaction remains a runtime gate.


## Actual local PixiJS rendered harness

Run from a project that already supplies Playwright, a Chromium executable and a local PixiJS v8 UMD build. No downloads, empty baselines or mocks count as runtime success.

```bash
node <skill>/scripts/runtime_render.mjs --release release-01 --pixi-build <local-pixi-umd.js> --chromium <local-chromium> --out runtime-render-01
```

Playwright resolves from the current project, or pass `--playwright-module <absolute-module-directory>`. If Chromium is managed by that Playwright installation, omit --chromium. A missing engine/browser exits 2. Output must be new. The server binds only loopback and rejects release paths outside the release directory.

The harness verifies export hashes, loads the actual Spritesheet parser/PNG textures, renders every declared frame at original canvas size, captures PNGs, compares full-canvas pixels against independently reconstructed atlas references, and checks authored timing, loop/terminal holds and event-pose alignment. Missing/reordered/blank frames, engine errors or version failures block success. A rendered_engine_pass covers this isolated atlas/clock fixture, not motion artistry, collision hits, transitions, device performance or the complete game. Canvas references share exported atlas bytes; pack's exact original-frame RGBA round-trip supplies source equivalence.

Declare engine_target in animation-set.json when an exact project version is required. Inspect real captured evidence; create runtime-template, complete only observed runtime checks, then run runtime-verify and release-check. runtime-render.json does not automatically fill or approve a reviewer form. This harness has syntax/unit/negative-case coverage in v3.8 but has not been run against a real PixiJS/Chromium installation in this session.

PixiJS trim semantics: https://pixijs.com/8.x/guides/components/textures
Godot AtlasTexture margin: https://docs.godotengine.org/en/stable/classes/class_atlastexture.html
