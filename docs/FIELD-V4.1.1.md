# v4.1.1 handoff audit / field — 2026-10-13

This patch adds repository-level verification and packaging. The bundled
produce-game-sprites v3.8 skill and rig-animation v2.2.0 resources are unchanged;
all 71 baseline skill resources and shared-source parity still pass audit.
No new engine compatibility or artwork approval is asserted.

## Changes and observed defects

- The previous release script required `git rev-parse HEAD` after opening the
  destination ZIP, so an extracted directory without Git could fail after leaving
  a partial archive. Packaging now stages and verifies a ZIP before an exclusive
  atomic publish, works without Git, and refuses to replace existing output.
- Checksums now cover release metadata too. A source tree digest binds actual
  packaged bytes even if no commit exists; Git dirty state is recorded honestly.
  Inventory/path validation rejects extra/missing/duplicate entries and symlinks.
- The previous handoff had no whole-export post-extraction checker. `verify:pack`
  now checks source/manifest/contract consistency, PNG CRC/dimensions, atlas bounds,
  exact bundled adapter bytes, SHA-256 baselines and optional texture budgets.
  `--pixels` decodes and compares frame/atlas RGBA; `--rerender` also compares a
  fresh source bake. Code from the inspected pack is never executed.
- `doctor` reports available local prerequisites without installing or mutating
  project state. UI/server version is 4.1.1; offline and worker artifacts rebuilt.

## Completed checks in this run

Environment: Node 24.19.0, Python 3.12.14, Pillow 12.3.0 and native canvas available.
Logs are in [evidence-v4.1.1](evidence-v4.1.1).

| Check | Result |
| --- | --- |
| New pack checker regressions | 14 passed |
| New ZIP mechanism regressions | 6 passed |
| Engine adapter tests | 9 passed; API models/native pixels as documented in v4.1 |
| Production/VFX tests | 17 passed |
| Rig/native tests | 45 passed |
| Python skill regressions | 118 passed |
| Skill JS checks | 15 timeline assertions, 23 mocked DOM/canvas assertions, clip-clock coverage/negative cases passed |
| Editor | Modular and offline each completed with exit 0, including actual downloaded adapter bytes and draft retention; mocked DOM/native canvas |
| Service/local/bridge/vault | Passed; CLI/MCP subprocesses, shared CAS, conflict/restart/history/auth, storage and draft protections |
| HTTP field | Real loopback server passed, including six-process CAS, rollback, restart, lost response, crash recovery and VFX operations |
| Build/audit | ESM artifact valid; full skill retention, JSON, links and generated parity passed |

Two initial new test fixtures were corrected: a source mutation used an invalid
`opacity` field instead of a valid alpha curve, and a traversal mutation changed
only the manifest so contract consistency correctly failed first. The revised
fixtures mutate valid alpha data and both path references to reach the intended
re-render/path checks. These did not require weakening application validation.

## Real export field

Exported untouched `projects/combat-vfx.rig.json`, `attack_se`, 24 FPS, engine `all`
through the actual CLI into a new directory. Deep verification passed, then a
separate baseline verification passed without changing pack bytes.

- 45 active frame files, 3 tracks, 9 atlas pages, 8 referenced pages.
- 71 files / 1,815,391 bytes; largest atlas dimension 1,548 pixels.
- Estimated atlas RGBA bytes: 63,901,440, including the unreferenced page.
- Explicit 2,048-pixel texture and 128 MiB atlas budgets passed.
- One warning: `slash_front-2.png` is unused after endpoint trim. It was not deleted.
- Every active frame matched its atlas cell, including nonzero rows; all generated
  PNGs matched a fresh bake of the bundled source through the native renderer.
- Technical report: [real-export-check.json](evidence-v4.1.1/real-export-check.json).

The report keeps visual `not_reviewed` and runtime `not_tested`. SHA-256 baselines
are change detection, not signed provenance or approval. The checker targets
unmodified Studio baked-VFX exports; customized adapters need project review.

## Archive acceptance

A candidate archive was extracted to a fresh directory and its checksums verified.
Handoff regressions and doctor passed there; the extracted checker also passed
the full 24 FPS source re-render check. Repackaging the extracted directory without
Git passed with null commit/dirty metadata and the same source-tree digest.
All bundled skill files were compared byte-for-byte with the delivered v4.1.0 ZIP;
none changed. See [archive-field.json](evidence-v4.1.1/archive-field.json).
The final archive is checked again after extraction before delivery.

## Remaining limits

Unity/Cocos/Godot editor/compiler and target browser/GPU/device acceptance remain
outstanding. DOM models do not test CSS, touch, Safari or ChatGPT MCP iframe hosting.
Source re-render is an internal consistency check, not an independent engine renderer.
Existing demo light-background additive readability and cut-off tail concerns from
v4 remain unapproved; no art was silently repaired or reapproved in this patch.
The app still requires actual host/MCP connection; no background-agent guarantee.
No live Site was published and no user Git remote was pushed in this run.
