# Verify art in the moving game

## Source scene versus release acceptance

A draft scene can load candidate PNGs directly before `pack`. Label this `raw_source_test`, record the manifest/image binding and exact scene revision, and keep production export blocked while visual defects remain. It proves observations about that candidate and scene, not atlas parsing or the user's actual game. Re-test the approved exported atlas separately. Do not call an isolated sample project the user's project.

Record engine/version, renderer, viewport, visible character height, asset scale/filter, camera scale, commands, logs and captured images/video. A software OpenGL renderer is still actual rendering; label it accurately and leave device performance untested. Exit code zero is insufficient: check parse/runtime errors, capture existence/dimensions, movie frame count and duration. Some movie writers can fail while the engine exits successfully. Use an existing absolute output directory. Review rendered sequences around each contact, impact, transition and terminal hold. State whether review used real-time playback or timestamped frame stepping; do not claim a movie was watched merely because it was generated.

## Feet and locomotion

Mark anatomical foot contacts in the source and the stance intervals; landmarks are designed values until checked against visible pixels. For each planted interval, capture several frames with the game root moving. Compute or measure the foot in world coordinates using the actual origin, scale, transforms and camera. The planted foot should stay within the project's declared tolerance. Include loop wrap and stop/start. Report units and sampling uncertainty.

An in-place gait can look convincing while the game speed makes it slide. Opposing hip motion alone does not establish a grounded step. Match stride to movement speed, or adjust movement to an approved stride. Tune each facing: sideways hip rotation is not a substitute for front/back depth, knee lift, foreshortening and occlusion. If the cutout cannot produce convincing depth, author those key poses with the available art tool and preserve the established identity. Leave that motion family blocked until reviewed.

## Transitions and combat

Test idle→walk→idle, walk→attack→idle, attack interrupted by hit/death, direction changes, and death holding without an automatic revival. Compare roots before and after the transition. Explicit scene resets are distinct from gameplay transitions; resetting the root for every clip can hide a teleport bug. The first frame of an action should be a valid entry pose, not just a picture that looks good alone.

Use one authoritative clip clock for pose selection and gameplay events, or the engine's documented frame/event mechanism. An independent timer can fire at the intended millisecond while the displayed sprite is still on the preceding frame. Log clip instance, local time, displayed frame and event identifier; capture just before/at/after impact. Derive timing from metadata, not a hard-coded duplicate. Test ordinary updates, a delta that crosses multiple frames, pause/resume, terminal hold, loop wrap and interrupted clips. Dispatch one-shot damage once per intended attack instance; interruption must cancel pending damage when the game contract requires it.

Event counts alone do not prove combat works. Test an in-range target, an out-of-range target, and the intended hit volume in each facing. Separate event dispatch, collision result and damage application. Inspect weapon tip/grip versus the hit region on the actual impact pose. A target flash or a drawn arc triggered unconditionally is a diagnostic effect, not evidence of contact. Preserve weapon handedness while changing screen-space attack geometry.

## Repair scope

Freeze the before candidate, declare affected frame IDs and source parameters, and keep adjacent poses available for review. Restore an authoritative good frame when corruption is isolated; otherwise edit the actual key pose, attachment, material or clock. Re-render only the necessary group. Run:

```bash
python3 <skill>/scripts/sprite_tools.py repair-diff before/animation-set.json after/animation-set.json \
  --allowed-frame attack_south_03 --out repair-scope.json
```

Repeat `--allowed-frame` for every intentionally changed frame. The command requires unchanged identity/order/durations/events/geometry and byte-identical untouched images; paths may differ after relocation. Unknown scope IDs or spillover block the comparison. A successful comparison does not prove the correction works. For a legitimate full geometry/timeline revision, make a new contract revision and review it; do not broaden scope silently to get a pass. Bind a fresh visual review after all repairs.

For realistic capability testing, include small independent faults in a copied candidate: wrong weapon attachment, shifted foot/root, scale drift and material/outfit drift. Have a fresh reviewer inspect the actual artifacts without the fault list. Keep these test faults separate from natural defects and from live assets. Do not infer general repair ability from undoing an injected fault alone.


## v3.3 metadata in runtime

Treat sockets, hitboxes and locomotion calibration as authored inputs that must survive engine transforms. During runtime capture, log the displayed frame ID and transformed socket/hitbox positions at important events. For weapon attacks, compare visible weapon tip to the actual hit volume. For casting, compare cast_origin to spawned VFX.

Use the declared `planted_foot_tolerance_px` only after converting through the actual sprite scale/camera transform; it is not a substitute for measuring world-space foot stability. For H5/mobile performance, compare the declared raw budget with the real packed texture dimensions, simultaneous visible actors and target-device/browser memory/performance.


## UI runtime field matrix

For UI, do not infer runtime usability from an atlas or static mockup. Exercise every viewport, locale and input mode declared in `runtime_test_matrix`. Capture actual screens for safe-area behavior, long/short localized copy, state transitions, nine-slice min/max sizes and touch interaction. Record engine/browser/device, viewport and scale. `ui-runtime-verify` checks coverage and bound assertions but does not operate the interface independently.

## Environment runtime field checks

For environments, capture an assembled moving scene rather than isolated props. Walk across seams and transitions, pass behind/in front of tall occluders, collide with declared logical footprints, test camera zoom/scale and inspect sampling at native gameplay resolution. Use `environment-runtime-verify` only after the current assembled-map visual review passes.

## VFX runtime field checks

For VFX, test the actual engine blend mode on both light and dark gameplay backgrounds, attach to the transformed runtime socket, log displayed frame/time at gameplay hit, test interruption/terminal behavior and spawn the declared simultaneous-instance budget. A visual arc triggered unconditionally is not evidence that collision/damage aligns with the authored hit event.
