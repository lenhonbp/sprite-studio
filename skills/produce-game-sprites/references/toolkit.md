# Standalone toolkit contract

`repair-diff BEFORE AFTER --allowed-frame ID --out NEW.json` verifies scoped preservation. Repeat the frame option as needed. It compares declared geometry/order/timing/events and frame file bytes plus production dependency hashes, allowing frame path relocation. Dependency edits require a new review. Contract changes, unknown scope IDs and changed frames outside scope exit 1; valid input with preserved scope exits 0 with `scope_pass` and `art_approval: not_evaluated`. Missing/invalid inputs exit 2. Re-review the actual correction separately; a full geometry or timing change requires a new contract revision.

Use Python 3.10+ and Pillow. Run from any working directory using the resolved skill path. Commands never contact an API. Outputs must use new paths; the tool refuses overwrite. Invalid schema/I/O exits 2. QA incomplete/failure exits 1; successful utilities exit 0 without implying artistic/runtime approval.

## animation-set.json schema 1

| Field | Contract |
|---|---|
| schema_version | Integer 1 |
| asset_id | Nonempty ASCII letters/digits/underscore/hyphen |
| representation | pixel or hd |
| cell_size | Two positive integer pixels, common to all frames |
| origin | Two finite cell-local coordinates including boundary |
| alpha_policy | Optional binary or soft (default soft); binary rejects semitransparent pixels |
| max_colors | Optional positive distinct-visible-RGB budget for pixel representation |
| alpha_required | Boolean; true requires some transparent pixels in each frame |
| max_texture_size | Positive integer, default 2048 |
| gutter | Nonnegative integer gap per side, default 2; populated with edge pixels when extrude=true |
| coverage | Optional actions/directions lists; requires their full cross-product. Optional exceptions: two-element [action,direction] lists within that matrix; document each reason in art-contract.md |
| production_contracts | Optional role→safe relative file path mapping: art_contract, metadata, keyposes, family, slice_provenance |
| atlas_policy | Optional boolean multipage (default true), trim (false), extrude (false) |
| engine_target | Optional {name: PixiJS or Godot, version: exact nonempty version}; runtime review must match |
| required_clips | Nonempty list of unique required clip names |
| clips | Nonempty list of unique named clips |

Each clip: name/action/direction use safe ASCII names; loop is boolean; frames is an explicitly ordered nonempty list. Each frame has a globally unique id, a safe project-relative path contained under the manifest directory, and positive integer duration_ms. Static PNG/WebP inputs only; animated files must be extracted first. Events are optional objects with safe name and integer time_ms inside the clip duration. For one-shots, hold the final pose in the engine. A manifest can include designed timing; record that fact in the art contract.

The example intentionally omits required clips: adapt it, supply real frames, and complete required actions before validate can succeed. It is not an approved production preset.

## Production v3.3 consistency metadata

For nontrivial animation, create `production-metadata.json` from `assets/production-metadata.example.json`. It may declare observed/designed landmarks, frame sockets, direction depth profiles, static regions, temporal suspicion thresholds, locomotion calibration, transition references, collision boxes, provenance and conservative performance budgets. Read [consistency-contracts.md](consistency-contracts.md). Declare this file in production_contracts.metadata; the conventional filename is also detected. inspect/qa/pack run its structural gate and bind its bytes. Structural errors block export. Temporal flags and missing observed landmarks require explicit finding_reviews, never automatic art acceptance.

## UI contract schema 1

Create `ui-contract.json` from `assets/ui-contract.example.json`. Core fields: `ui_system_id`, `representation`, `reference_canvas`, `safe_area`, `text_policy`, project-owned `minimum_touch_size`, `runtime`, `components`, optional `required_state_groups`, `screen_flows`, `slices`, and `runtime_test_matrix`. Each component declares unique id/group/role/state, relative final path, logical size and optional touch size, nine-slice margins, text/alpha policy. `ui-check` validates structure and files but returns `ux_approval: not_evaluated`.

`ui-slice` crops only explicit reviewed rectangles from declared source sheets. It never auto-detects semantic components, guesses names or chooses nine-slice margins.

## Commands

- doctor: report Python/Pillow and detected executable paths; separately inspect agent image/vision capabilities.
- ui-check UI_CONTRACT --out report.json: validate UI component files, unique state groups, project touch-target minimums, runtime-text policy, nine-slice geometry, screen references and slicing declarations. Structural success still requires visual and runtime UX review.
- ui-slice UI_CONTRACT --out DIR: preflight every declared slice, then crop explicit reviewed rectangles without resampling and write `ui-slices.json`; refuses duplicate ids/outputs, unsafe paths, out-of-bounds rectangles and an existing output directory.
- ui-review-template UI_CONTRACT --evidence PATH --out review.json: create a blank visual UI review bound to current component bytes and inspected evidence.
- ui-qa UI_CONTRACT --review review.json --out report.json: require complete evidence-bound visual observations; changed components stale the review.
- ui-runtime-template UI_CONTRACT --visual-review review.json --evidence PATH --out runtime.json: require an approved current UI visual review and create a blank actual-runtime review.
- ui-runtime-verify UI_CONTRACT --visual-review review.json --review runtime.json --out report.json: require actual engine/browser/device metadata, current binding, required viewport/locale/input coverage, visual interaction checks and evidence.
- environment-check CONTRACT --out report.json: validate environment/prop file/anchor/footprint/collision structure; assembled-map art/runtime approval remains separate.
- environment-review-template / environment-qa: bind current assembled-map evidence and require complete visual observations for style/scale/projection, seams, pivot/depth/occlusion, collision footprint, composition and sampling.
- environment-runtime-template / environment-runtime-verify: bind an approved current environment review, then require actual runtime evidence for import/sampling, assembled seams, depth sorting/occlusion, collision/walkability, camera scale and performance.
- vfx-check CONTRACT --out report.json: validate VFX file/canvas/timing/alpha/socket/event/budget structure; visual impact/blending/runtime hit alignment remain separate.
- vfx-review-template / vfx-qa: bind current VFX proof and require complete visual observations for phase readability, direction, alpha, socket alignment, light/dark readability and loop/terminal treatment.
- vfx-runtime-template / vfx-runtime-verify: bind an approved current VFX review, then require actual engine evidence for blend/import, playback timing, socket transforms, gameplay-hit alignment, multi-instance readability and overdraw/performance.

- motion-check MANIFEST --contract production-metadata.json --out report.json: validate v3.3 consistency metadata and report adjacent-frame silhouette/bbox/palette/landmark drift, declared static-region changes, socket/landmark coverage, depth bindings, locomotion speed calibration, collision bounds, provenance coverage and a raw RGBA budget estimate. Exit 1 only for structural contract errors; suspicious metrics remain review findings because automation does not approve art.
- family-check family-contract.json --out report.json: compare a roster's declared representation/cell/action × direction invariants plus reference-frame origin/visible height. Warnings require side-by-side visual review; they are not automatic art failure.
- validate MANIFEST: validate structure and required clips only.
- inspect MANIFEST --out report.json: inspect real frame dimensions, alpha, bounds, exact pixel duplicates and declared production dependencies; bind their bytes and contract with SHA-256.
- preview MANIFEST --out DIR: native contact sheet, lossless WebP per clip, and offline canvas player with immutable embedded frames, exact authored timing, frame stepping, integer zoom, onion skin, origin guides, light/dark backgrounds and declared terminal holds. The canvas follows the manifest, independent of WebP container loop flags; verify actual engine behavior separately. Whole-clip exact duplicates may be coalesced by WebP encoding, so the manifest/contact sheet remain authoritative for frame count.
- review-template MANIFEST --evidence PATH --out review.json: repeat --evidence for every inspected artifact. Create a fresh blank schema-2 review bound to current inputs and evidence hashes. Fill rows with evidence names from evidence_files; do not stamp new hashes into a completed review.
- qa MANIFEST --review review.json --out report.json: combine technical checks with bound reviewer verdicts, observations and prebound unchanged evidence file references. Resolve evidence relative to review file. This checks assertions, not artistic truth.
- pack MANIFEST --review review.json --out DIR: gate on QA, pack deterministic fixed-cell or trimmed atlas pages within max_texture_size, optionally extrude edges into gutters, and write timeline/PixiJS/Godot data and adapters. Reopen the PNGs and reconstruct each original canvas for exact RGBA equality. Refuse hidden transparent RGB loss when trimming, overflow with multipage=false, and existing output directories.
- extract SOURCE --out DIR: fully composed animated GIF/WebP to RGBA PNG sequence and duration list. Missing source durations require an explicit --duration-ms fallback; invalid authored timing is not silently replaced.
- extract SHEET --cell W H --duration-ms N --out DIR: explicit row-major exact grid only; no inferred topology, spacing or direction order. For gutters/offsets use a capable sheet processor.
- pad SOURCE --padding LEFT TOP RIGHT BOTTOM --out NEW.png: preserve pixels while expanding transparent canvas; add LEFT/TOP to the declared origin.

Alpha checks cannot detect a convincing opaque baked background when transparency is optional. Bounding boxes do not identify actual feet. Duplicate warnings are compatible with authored holds and require visual interpretation. A valid contract, preview or export does not establish runtime acceptance.

Use input/output files from the user's project directory. Keep artwork sources immutable, and retain a separate production log. This toolkit does not independently enforce repair budgets or artistic correctness. Runtime verification checks complete assertions and unchanged export/evidence identity, not independent engine truth.


## Key poses and runtime

- keypose-check PLAN --out report.json: total_frames >=2; at least two static key poses, unique indices including 0, common cell_size and per-pose origin, nonempty pose role and relative paths. Generic frame counts are unrestricted; optional providers may impose even counts or other limits. Fail on geometry/origin differences before generation.
- runtime-template RELEASE --evidence PATH --out review.json: verify export file identities, create schema-2 blank actual-engine review bound to the export manifest and evidence files.
- runtime-verify RELEASE --review review.json --out report.json: require actual engine/version/project/reviewer, complete import/playback/facing-origin/filter-scale/transitions-events/texture-budget assertions and unchanged evidence. Playback/facing/filter checks require visual evidence mode. Headless-only checks cannot pass those gates. Unknowns block approval.

Existing unbound review files from v1 are deliberately rejected. Recreate them and inspect current artifacts rather than transplanting old assertions.


## v3.8 dependency and release workflow

`production_contracts` uses paths relative to animation-set.json. Conventional co-located art-contract.md, production-metadata.json, family-contract.json and slice-provenance.json are auto-detected even without a declaration. Keypose paths must be declared. Dependency children (family member manifests/images, keypose images and slice source/outputs) are hashed too. Family membership must match the current normalized manifest and frame paths. Slice provenance must match current full-canvas output paths, frame order, geometry/origin and durations; transformed derivatives need a new matching provenance contract. Removing a conventional contract invalidates an existing review; declare required contracts explicitly so removal also blocks structural QA.

The blank review template includes `finding_reviews`. For every ID in inspect.dependencies.findings, add `{verdict:"pass", observation:"concrete inspected finding and rationale", evidence:["bound-evidence-path"]}` only after actual inspection. IDs are bound to current inputs; fresh findings require a fresh review. Heuristic metrics alone cannot establish visual success.

```bash
python3 <skill>/scripts/sprite_tools.py init-animation --asset-id hero --actions idle walk run attack1 attack2 hit death --directions n ne e se s sw w nw --cell 64 64 --origin 32 56 --out hero-project
python3 <skill>/scripts/sprite_tools.py checkpoint animation-set.json --out checkpoint-01.json
# Resume after edits; result lists invalidated clips/dependencies.
python3 <skill>/scripts/sprite_tools.py checkpoint animation-set.json --previous checkpoint-01.json --out checkpoint-02.json
python3 <skill>/scripts/sprite_tools.py release-check animation-set.json --review visual-review.json --release release-01 --runtime-review runtime-review.json --out final-release.json
python3 <skill>/scripts/sprite_tools.py vfx-pack-release-check vfx-pack.json --dir bundle-01 --out final-pack.json
```

Scaffolding creates contracts only, with unapproved timing and no images. Missing frames must fail inspect until authored. checkpoint records input identity; it does not approve art or resume external jobs. release-check additionally rejects exports stale against current sources/dependencies or bound to another visual review.

A VFX pack structural `ready` means bundle integrity only; `art_approval` remains not_evaluated. Each pack effect must declare safe pack-relative `vfx_contract`, `visual_review`, and `runtime_review` for vfx-pack-release-check. The contract/source identity is checked by the bundle gate. Every per-effect visual/runtime gate must pass before release_approved. Marketplace submission and policy eligibility remain separate.
