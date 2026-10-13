# Verification scope v3.3.1

Passed checks cover: schema validation; transactional batch rollback; per-user data isolation; unique request ID reconciliation; CAS race conflicts; global undo/redo; view state; technical preflight; MCP tool/resource contract; embedded bridge initialization; polling before local view upload; offline pause/resume; retention of a draft after a lost reply followed by another actor's edit; local snapshot/recovery; all-or-nothing backup import; storage quota rejection; DOM interactions with native canvas; standalone embedded bundle; CLI rig mathematics and render contracts.

The server storage and MCP host in these tests are in-memory mocks. Vault tests exercise localStorage fallback; native IndexedDB behavior, eviction policy and cross-browser persistence have not been tested in a real browser. DOM/canvas tests are not CSS, native touch, Safari downloads or actual ChatGPT iframe QA. Actual target-engine runtime acceptance and production animation art review are not completed. Native publishing confirms the hosted version; it does not add these missing gates.

Demo artwork: one southeast direction, idle/walk/attack cutout proof. Missing camera views and action sets are not synthesized by validation. Preserve source and perform visual/runtime checks before releasing assets.

Local edition: passed real temporary filesystem, independent CLI processes racing on one revision, retained state across new app instances, actual newline JSON-RPC stdio child process, and in-process editor API changes visible to CLI/MCP and back. Covered localhost cookie, rejected foreign origin/host, import revision guard, export overwrite guard, active/dead lock behavior, corrupt state retention. The native Node HTTP listener was not exercised via a real browser. These checks do not claim native IndexedDB, visual layout or actual host MCP installation.

Full-skill integration: all 71 base v3.8 skill files retained and hashed; base resources unchanged except SKILL.md routing and personal UI metadata. Added CommonJS scope fixes timeline.js when inside the ESM app; rig module retains ESM. Passed 118 Python tests, 15 timeline assertions, 23 mocked player DOM/canvas assertions, clip-clock/render-result regressions, 45 rig tests, modular/offline editor canvas tests, local/service/bridge/vault tests, and the bundle audit. Negative audit exercises rejected a stale generated browser core and a missing skill resource. The art CLI was also invoked from outside the repository working directory.

A fresh-thread forward task used the optimized sample and bundled skill to edit attack_se/arm_front at 300ms, rendered 35 PNGs across three clips and exercised validate/inspect/preview/motion-check/review-template/qa. Only two attack PNGs changed; 33 other frames were byte-identical. Technical inspection passed, while motion inspection reported nine socket flags (largest weapon-tip step ~152.727 px). Actual representative static frames/contact sheets were viewed. QA remained blocked with unseen playback/ground/transitions and unresolved socket findings; runtime remains not_tested. This is evidence that the integration preserves the gates, not production approval of the demo. No model-generated new art or actual engine acceptance was performed.

Field revision 3.3.1 now exercises the native Node HTTP listener on an ephemeral 127.0.0.1 port. Real client tests cover assets/MIME, cookie/origin/host, oversized streamed bodies, 24 edits/history budget, six independent process conflicts, bridge synchronization over actual HTTP, network/lost-response retention, restart session renewal, actual MCP stdio invalid envelopes, export, SIGKILL before atomic rename and dead-lock recovery. Unicode history is bounded by encoded UTF-8 bytes. See FIELD-TEST.md. Browser DOM in bridge scenarios remains a minimal mock; real browser rendering/touch and specific MCP host integration remain unverified.

For v4.1 multi-engine tests and scope see [FIELD-V4.1.md](FIELD-V4.1.md).

## v4.1.1 handoff verification

Read [HANDOFF-CHECKS.md](HANDOFF-CHECKS.md) for read-only VFX verification,
baseline hashes, texture budgets, environment checks and atomic portable packaging.
Actual run results: [FIELD-V4.1.1.md](FIELD-V4.1.1.md). Existing engine/art gates remain.
