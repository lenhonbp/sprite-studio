# v3.8 verification and handoff

Made by Nhon Le. Updated 2026-10-09 from the supplied full v3.7 archive. The separately supplied process-sprite-sheets devkit is a different, incomplete package and was not merged as a second authoritative schema.

## Implemented

- QA/export binds authored metadata, art direction, keyposes, family and slice provenance, including their referenced bytes. Invalid sockets/geometry block export; changes invalidate reviews. Suspicious temporal findings require bound observations.
- Family acceptance checks the complete action × direction matrix and the actual current manifest/frame paths. Explicit omissions require reasons in the family contract. Slice provenance must match current outputs, order, canvas/origin and timing. Transformed derivatives require their own provenance; an unrelated reconstruction cannot approve them.
- Rig reassembly requires exact RGBA, catching alpha-only changes. UI extraction preflights normalized aliases and output collisions. Sheet preflight examines all four edges and binds source identity.
- VFX bundle readiness checks typed metadata/manifest, log coverage, exact source-to-sheet cells, GIF preview policy/timing, and per-effect contract source bytes/events/canvas. Per-effect cost math corrected. Structural readiness is separate from visual/runtime release acceptance. Provider names describe recipes, not implemented API integrations.
- Deterministic multipage atlases, optional trim and gutter extrusion, original offsets and exact saved-PNG-to-source RGBA reconstruction. Texture budget sums pages. Single-page output names remain compatible.
- Project scaffold, change checkpoints, shared pose/event clock, local PixiJS rendered harness and final sprite/VFX release checks. Interruptions or pauses inside callbacks cancel the remaining tick; pause holds the callback event time and discards the rest of that tick.

## Observed verification

Environment: Python 3.12.14, Pillow 12.3.0, Node available. Aseprite and Godot absent. No usable local PixiJS/Chromium runtime was found for actual rendered tests.

```bash
python -m unittest discover -s scripts -p 'test_*.py'
node scripts/test_timeline.cjs
node scripts/test_player.cjs
node scripts/test_clip_clock.mjs
python <skill-creator>/scripts/quick_validate.py <skill>
```

- 118 Python tests passed. Fixtures are synthetic; assertion reviews exist only to test gate mechanics.
- 15 timeline assertions and 23 mocked DOM/canvas assertions passed. Clip-clock/render-result negative/coverage suite passed, including variable durations, loop boundaries, terminal hold, pause/resume, stop/interruption, missing/blank/reordered runtime frames and engine errors.
- Skill validation passed. Python compile, JavaScript/module syntax, JSON parsing and internal Markdown references were checked.
- Independent forward task created four RGBA attack fixtures, two directions with 90/210ms timing and weapon sockets. It inspected native contact sheets and socket overlays, left unseen playback/runtime checks unknown, and confirmed QA/export blocked. Metadata-only socket mutation invalidated its old review.
- Independent adversarial review reproduced mismatched family/slice/VFX bindings and interrupted dispatch. Fixes were rerun: unrelated contracts block, allowed family frame repairs pass, peer modifications block, and stop/pause cancels further event dispatch.

## Practical limits

No generated production artwork, real model API, actual Godot/PixiJS rendering, marketplace upload or gameplay collision test was performed during this update. The local rendered harness and engine smoke scripts are delivered for target-project execution; their current runtime status is not_tested. Unit tests and static image inspection do not establish animation quality or target-engine acceptance.

The historical FIELD-QA-v3.6/v3.7 and evaluation records remain in the archive as history. Their counts and engine claims were not rerun as evidence for v3.8. In particular v3.7's $0.40 example reflected the corrected per-effect multiplication bug; v3.8 reports two $0.05 effects as $0.10.

## Use

Start with SKILL.md and references/toolkit.md. For engine execution read references/engine-handoff.md. Keep each user's source art untouched, create fresh reviews from observed evidence, and use release-check/vfx-pack-release-check before claiming a finished runtime release.
