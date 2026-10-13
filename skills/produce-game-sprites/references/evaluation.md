# Evaluate this skill

Run deterministic processing regressions:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 <skill>/scripts/test_sprite_tools.py
```

The fixtures are synthetic shapes. Passing these tests verifies processing and gate mechanics, not art quality, a generation model or engine playback.

Coverage: manifest required clips/IDs/event bounds; blank and stale review rejection; changed-pixel invalidation; missing evidence; alpha/size/empty-frame failures; lossless atlas crop reconstruction; retained durations/events; Godot text output; separate not_tested runtime status; fixed texture budget; padding without resampling; animated WebP extraction; explicit grid slicing; overwrite refusal; duplicate warnings; malformed input objects; vfx-pack spec taxonomy/adapter/marketplace-policy validation; sales-bundle file/grid/GIF-parity/manifest checks.

For behavior evaluation, give a fresh agent only the skill path, a user-like task and raw inputs. Keep expected findings separate. Use new output directories and inspect actual artifacts. Do not seed reviews with intended answers.

Suggested tasks:
1. Prepare a supplied two-frame "walk" set for Godot. Include a technically valid set with visually static movement. Expect real inspection and a justified export decision, not trust in the filename.
2. Create a new character with only the available image tool and Python. Expect an identity master, action key poses, staged expansion and truthful motion limitations.
3. Repair an existing eight-direction asymmetric sword character with a weapon-hand change in one view. Expect source topology preservation, handedness review and bounded repair.
4. Resume after changing one source frame following approval. Expect new review binding and invalidation of dependent exports.
5. Integrate a approved set when the requested engine is absent. Expect an explicit not_tested runtime status rather than a claim that HTML playback proves engine acceptance.

During initial validation on 2026-10-06, 13 processing regressions passed in Python 3.12 with Pillow 12.3. Those regressions did not validate target-engine playback or drawing quality.

## Production v2 validation

Run the current tests rather than relying on recorded counts:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 <skill>/scripts/test_sprite_tools.py
node <skill>/scripts/test_timeline.cjs
node <skill>/scripts/test_player.cjs
```

On 2026-10-06 the v2 suite passed 23 Python regressions, 15 timeline assertions and 23 DOM/canvas assertions. DOM/canvas tests use mocks: they verify control/timing/draw contracts, not real browser rendering. Browser visual playback was not validated because a compatible browser executable could not be installed from the available download route.

Actual official Godot 4.7.2 was obtained separately for a headless smoke test. Import, atlas regions, authored frame timing, real AnimatedSprite2D advancement and loop/terminal holds passed on a synthetic fixture. Visual engine acceptance remains not_tested, and a synthetic technical fixture is not approved character art.

A fresh agent used v2 on supplied two-frame character PNGs. It inspected native and enlarged light/dark views, created a fresh schema-2 evidence-bound review and blocked export for a symmetric stance toggle without alternating gait. Facing, ground behavior, transitions and timed visual playback remained unknown. This validates rejection behavior, not successful production of high-quality new character art.

Actual PixiJS 8.22.0 was installed in an isolated temporary test directory. Its real Spritesheet parser and AnimatedSprite, using the exported adapter and decoded atlas bytes, passed geometry/anchor, frame timing and loop/terminal tests. Browser/GPU rendering and combat-event dispatch remain not_tested.

## Production v3.3 consistency regressions

Also test `motion-check` with a deliberate palette/silhouette/static-region drift, missing socket coverage, bad collision bounds and a stride/speed mismatch. Test `family-check` with two members that disagree on required actions and with a reference-size warning. These tests verify detection/contract behavior only.

Suggested forward task: repair a four-direction sword attack where the grip stays visually correct but the weapon-tip socket jumps on one frame; expect the checker to surface the pair and the agent to inspect/fix the actual art or socket rather than merely increasing thresholds.

## Production v3 capability boundaries

Use a real raster character family in addition to synthetic tests. A generated multi-view cutout kit and authored shoulder/hip/knee rig can produce consistent held equipment. Inspect source topology, stray alpha bounds, attachment extremes and direction-specific depth before trusting it. An observed 20-clip/116-frame prototype demonstrated that a complete manifest can still have clipped death poses and unconvincing front/back gait.

For a blind fault task, a fresh agent identified hand switching on the impact frame, root shift, scale pop and whole-body palette drift, plus natural sword clipping in late death frames. A four-frame restoration passed scoped byte preservation for the other 112 files; this tests detection and preservation, not arbitrary artwork reconstruction. Padding a clipped family required a separately declared origin revision.

Actual Godot 4.7.2 software OpenGL rendering exposed a timer firing while the displayed pose remained one frame behind and a root reset at walk→attack. Verify the displayed impact pose and transition roots, not just nominal milliseconds or event counts. A raw-source scene with a unified clip clock can test these before production approval. Keep grounded front/back motion, fully redrawn collapse, exported-atlas integration and target-device performance unapproved until their own evidence exists.

## Production v3.3 validation — 2026-10-06

Current local regression suite after the v3.3 consistency additions:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_sprite_tools.py      # 25 tests
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_verify_rig.py        # 6 tests
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_quality_checks.py    # 7 tests
node scripts/test_timeline.cjs                                      # 15 assertions
node scripts/test_player.cjs                                        # 23 assertions
```

All passed in the validation environment: **38 Python tests**, **15 timeline assertions**, **23 mocked DOM/canvas assertions**. `py_compile` also passed for every Python script. These checks did not execute a target engine; actual target-engine visual acceptance remains mandatory before a production-ready claim.

The new v3.3 tests cover: temporal/silhouette/static-region detection; landmark/socket contract coverage; invalid sockets/collision/transition references; locomotion speed calibration; performance estimate plumbing; family invariant comparison; visible-height review warnings; required-action blocking; and CLI wiring. These tests validate detection mechanics, not artistic truth.

## Game Art Production v3.4 UI/UX regressions

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 <skill>/scripts/test_ui_checks.py
```

The v3.4 suite adds 7 UI contract/slicing regressions covering: structurally valid UI staying `review_required`; required-state blocking; runtime-text vs baked-text rejection; invalid nine-slice blocking; project-minimum touch-target warnings; exact non-resampled slice geometry; and out-of-bounds slice rejection.

Suggested behavioral tasks:

1. Take a generated HUD sheet and a target portrait screenshot. Expect the agent to treat the sheet as source material, define named runtime components/states, keep final text dynamic, and show an actual screen mockup/runtime view before claiming UX quality.
2. Provide default/pressed button art but omit disabled state while the contract requires it. Expect `ui-check` to block structural completion without inventing the missing state.
3. Give a beautiful fixed-size panel that must host short and long localized copy. Expect a nine-slice/runtime-text solution and overflow testing, not image stretching with baked text.
4. Give an isometric/tall prop with transparent padding. Expect logical base pivot/footprint depth sorting and an assembled map test rather than recropping the source to equal bounds.
5. Request a one-weapon Spine reskin. Expect smallest-part replacement/preserve-topology behavior and target-runtime round-trip, not full-character regeneration.

## Game Art Production v3.4 validation — 2026-10-06

Current local regression suite after the broader game-art/UI additions:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_sprite_tools.py      # 25 tests
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_verify_rig.py        # 6 tests
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_quality_checks.py    # 7 tests
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_ui_checks.py         # 7 tests
node scripts/test_timeline.cjs                                      # 15 assertions
node scripts/test_player.cjs                                        # 23 assertions
```

All passed in the validation environment: **45 Python tests**, **15 timeline assertions**, **23 mocked DOM/canvas assertions**. `py_compile` passed for every Python script, every bundled JSON example parsed successfully, and all internal Markdown file links resolved. Actual target-engine UI interaction and visual acceptance remain runtime gates.

## Game Art Production v3.5 field hardening — 2026-10-06

The v3.5 pass added 10 field-hardening regressions and executable evidence gates for UI, environment and VFX. Current full regression suite:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  scripts.test_sprite_tools scripts.test_verify_rig scripts.test_quality_checks \
  scripts.test_ui_checks scripts.test_field_hardening   # 55 tests
node scripts/test_timeline.cjs                            # 15 assertions
node scripts/test_player.cjs                              # 23 mocked assertions
```

All passed in the inspection environment. `py_compile` passed for every Python script, every bundled JSON example parsed, and all internal Markdown links resolved.

Adversarial checks additionally confirmed that parent-path frame escape is rejected, duplicate UI slice outputs fail before an output directory is created, impossible safe areas block, changed bound UI assets stale their visual/runtime reviews, missing UI field-matrix coverage blocks runtime verification, invalid environment pivots block, and VFX canvas mismatch blocks.

The end-to-end fixture intentionally demonstrated fail-closed behavior: a technically valid sprite with no true playback review could not pass `qa` or `pack`; UI/environment/VFX could pass current structural and inspected synthetic visual proofs, but their blank runtime reviews all remained blocked. Godot, a real browser and the `pixi.js` package were unavailable in that environment, so target-engine runtime acceptance remained outstanding rather than being simulated into a pass. See `FIELD-QA-v3.6.md` for the sheet-separability field report.


## v3.8 maintenance acceptance

Read [verification-v3.8.md](verification-v3.8.md) for this update's evidence. Run the complete Python suite, timeline and mocked-player JS suites, plus test_clip_clock.mjs. Test invalid sockets through qa and pack (not only motion-check); metadata-only stale review and repair-scope rejection; incomplete family matrices; alpha-only rig corruption; normalized UI output aliases; forged/truncated VFX sheets/GIFs/logs; multipage and trimmed original RGBA reconstruction; missing engine/empty runtime coverage. Independent forward tasks must leave unknown visual/runtime checks incomplete. Preserve old evaluation records as history, never as proof of the current runtime.
