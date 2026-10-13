> Historical record supplied with the original archive; superseded for current acceptance by references/verification-v3.8.md. Engine/API claims below were not rerun during v3.8.

# FIELD / QA v3.7 — vfx-pack module (sellable VFX packs)

v3.7 adds the `vfx-pack` module to v3.6.2: a sellable multi-effect VFX pack
pipeline. New files: `references/vfx-pack.md` (taxonomy, generation adapters,
prompt recipe rules, post-processing, sheet assembly, sales bundle,
marketplace policy gates), `assets/vfx-pack.example.json`,
`scripts/vfx_pack.py` (`vfx-pack-plan`, `vfx-pack-bundle-check` wired into
`sprite_tools.py`), `scripts/test_vfx_pack.py` (15 tests). Wiring updates in
`SKILL.md` (v3.7 routing), `references/vfx-production.md` (sellable-pack
pointer), `references/evaluation.md` (coverage line).

## What was validated (2026-10-07, Python 3.12, Pillow 10.2)

- New tests: 15/15 pass — plan totals/cost math, taxonomy rejection,
  GameDev Market AI ban block, itch.io disclosure requirement, missing-seed
  and missing-log-field warnings, Unity caution; bundle completeness, sheet
  grid divisibility, GIF frame-count parity, manifest mismatch, missing-file
  errors, per-effect `vfx_check` error folding, missing bundle dir.
- Full existing suite re-run: 68 Python tests pass (sprite_tools 25,
  quality_checks 7, sheet_checks 3, verify_rig 6, verify_slices 10, ui_checks 7,
  field_hardening 10); node timeline/player assertions pass (15 + 23).
- Dogfooding: `vfx-pack-plan` on the shipped `assets/vfx-pack.example.json`
  returns `ready` with correct totals (2 effects, 8 frames, 750ms, $0.40).
- End-to-end CLI run on a synthetic two-effect fixture: `vfx-pack-plan` and
  `vfx-pack-bundle-check` both exit 0 with `ready`, zero errors.
- One real bug found and fixed during build: the example spec declared
  `vfx_contract: vfx/fire_burst.contract.json` while its frame paths were
  project-relative — `vfx-check` resolves paths relative to the contract file,
  so this resolved to `vfx/vfx/...`. Fixed the example to
  `fire_burst.contract.json` and documented the convention in vfx-pack.md.
- Packaging: zip root is `produce-game-sprites/` (same layout as v3.6.2
  source), no `__pycache__`/`*.pyc`/`.DS_Store` in the archive.

## Not validated (stated plainly)

- No real generation API was called (PixelLab/Retro Diffusion/Scenario):
  adapters are documented recipes, not tested integrations. Provider pricing
  in the doc is a research snapshot and must be re-verified before any paid run.
- No pack was submitted to any marketplace; policy gates encode researched
  rules (itch.io disclosure, GameDev Market ban) and have not faced a real
  review queue.
- Bundle `ready` is structural only; no visual or target-engine runtime QA was
  run on a real pack, and the module's own doc states this explicitly.
