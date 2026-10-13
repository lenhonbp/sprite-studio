# v4.0.0 audit / field evidence — 2026-10-11

This is a tool release. Character/VFX samples remain unapproved. No claim of
production art or actual game-engine acceptance is made.

## Executed checks

- Full base skill: 118 Python tests, 15 timeline assertions, 23 mocked DOM/canvas
  assertions and clip-clock/render negative regressions passed.
- Rig: 45 native/core/CLI regressions passed.
- Production: 17 regressions passed: legacy compatibility, seeded seek invariance,
  half-open event clocks, repeated events, emitter birth-space, connected trail,
  PNG flipbook order, strict curves/references/budgets, protected linked deletion,
  clip rename/retime, asset source preservation and lineage cycles, exact native
  atlas/frame RGBA roundtrip, source bundle byte roundtrip and safe paths/symlinks,
  real CLI processes, mock Pixi clock contract, socket offset/rotation, terminal
  clip behavior, mislabeled/oversized native PNG rejection.
- Modular and single-file offline editors executed through minimal DOM with native
  canvas: presets, timeline, brush/eraser infrastructure, stroke undo/redo, raster
  variant/source retention, project undo/redo, invalid edit retention, unsaved form
  protection and actual VFX/source ZIP encoding. This does not verify browser CSS,
  touch, download UX or native IndexedDB.
- Real HTTP/CLI field: new production module assets served; one atomic texture+FX+
  socket binding batch; idempotent retry; effect selection; independent CLI read;
  invalid batch rollback; six-process CAS (one success/five conflicts); shared
  undo/redo; source export; disk restart persistence. New production final revision4.
- Existing field suite passed unchanged except current version labels: native HTTP,
  cookie/origin/host/body checks, 24 edits/history bound, six-process CAS, actual
  bridge code against HTTP with a minimal editor, lost response/offline draft,
  restart cookie renewal, stdio MCP parser, SIGKILL before atomic rename and UTF-8
  history cap. Existing field final revision33. See FIELD-TEST.md for detailed scope.
- Build artifact imports as valid ESM. Audit retains all71 original skill resources,
  original raster master, portable reference links and canonical generated copies.

## Independent forward task

A fresh agent received only the bundled skill, raw combat source and task: warm
orange slash, move hit event40ms later, preserve original raster/unaffected clips,
export12FPS, inspect dark/light and run technical checks. No live state touched.

Preservation/source roundtrip and exact atlas crop comparisons passed. First export
had30 full-clock frame cells. Leading/trailing transparent padding caused VFX
contracts to fail. Recheck with corrected export has21 active frame PNGs across
3 tracks; all3 vfx-check contracts pass. Atlas pages retain the same source clock
rectangles, and active frames retain absolute timestamps. Burst event373ms begins
visually at417ms in the12FPS bake; sample373ms already has particles. This is
sampling quantization, not an event rewrite.

Actual current contact sheets and799/800ms proofs were inspected. Preview now
clears effects at800ms like adapters. Bound visual QA intentionally remains
blocked on light-background hue/readability, burst tail cutoff and insufficient
composite/loop evidence for aura. Native rendered proofs are not engine evidence.
The sample is a technical test fixture, not a finished JX1 skill animation.

## Bugs corrected through audit

- Disconnected trail dabs replaced with connected textured path segments.
- Floating point alpha at curve end could become negative and trigger a false seam
  warning; endpoints now return exact authored values.
- Layers with zero alpha no longer alter the previous trail draw accidentally.
- Export front/back splits preserve layering intent and budget counts both tracks.
- Empty leading/trailing baked padding is trimmed without shifting absolute time;
  internal blanks remain for QA to detect. Per-track active-interval contracts keep
  the full clip clock and events as context.
- Terminal preview and adapter clocks agree; authored tail cutoff is reported.
- Socket local offsets and optional emission rotation use the sampled transform.
- New raster candidates check PNG header/native dimensions; brush limits use actual
  source pixels. Source image paths reject parent/symlink escapes.
- Offline bundling now removes only module declarations, preserving downloadable
  adapter export syntax; modular/offline ZIP adapter bytes match exactly and import.
- Select input-before-change ordering, export draft retention and per-panel saves
  now retain unrelated drafts; these event sequences have regression checks.
- Unsaved production forms and raster drafts prevent incoming editor replacement.

## Remaining acceptance

No actual Godot/Pixi runtime, real browser layout/touch/Safari download, ChatGPT
MCP Apps iframe, host-specific MCP config, Windows/macOS filesystem, GPU performance
or target-phone battery/overdraw test was performed. Godot/Aseprite were unavailable;
Pixi adapter clock tests use explicit fake objects. Candidate adapters reference
official engine APIs but require project-specific import/render/playback evidence.
No external image API, shader graph or automatic directional art is implemented.
Live source still has4MB cap; separated PNG bundles are for editable Git handoff,
not a bypass of live storage limits. All generated art proofs stay candidates.
