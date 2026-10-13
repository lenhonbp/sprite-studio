# Visual evidence and bounded repair

Render/capture current evidence, then create a fresh schema-2 review template with repeated --evidence paths immediately before reviewing. The template prebinds each evidence file's hash; changing an artifact invalidates it. Each clip has seven required checks:

- identity: face/hair/outfit/equipment/material continuity;
- camera_facing: camera height, facing, scale and occlusion;
- anatomy_grip: body count/proportions, handedness, held weapon contact;
- motion_timing: intended action, rhythm, phase progression and loop/terminal behavior;
- origin_ground: ground line/root movement and feet relative to actual gameplay motion;
- alpha_clipping: alpha edges, sufficient weapon/VFX margins and background removal;
- transitions_events: entry/exit pose and event alignment with intended game logic.

For each check, use `pass`, `fail` or `unknown`, add concrete observations naming frames, and list inspected evidence paths. Never copy the desired contract as an observation. Use the template's evidence_files keys in each row's evidence list. Never rewrite evidence hashes in a completed review. A nonempty text assertion is mechanically checkable, but honesty and artistic interpretation remain the agent's responsibility. The toolkit hash binding detects changed inputs; it does not prove a reviewer looked at them.

For multi-direction families, compare identity across all facings against each other, not only each facing against the contract. A costume element can pass per-facing review and still be absent in one facing (observed: full-length trousers present in down/left/right but missing in up). Cross-facing comparison is a required step of the identity check.

Open contact-sheet.png and the current offline canvas player. Its frame stepping, onion skin, origin guides and millisecond timing expose phase defects; WebP playback is an additional comparison. Inspect all required frames natively and at gameplay size, all directions, light/dark alpha backgrounds and transitions. If browser playback is unavailable, use an available animation viewer; static frames alone leave timing unverified. Leave affected checks `unknown` until evidence exists.

For each defect, record severity, clip/frame IDs, observed symptom and hypothesis separately. Repair the smallest affected group while preserving the master. Re-run automatic inspection and generate a new blank review; never stamp new hashes into an old approved review.

An AI edit redraws the whole image, so a repaired frame can shift static regions by ~1px even when the defect is elsewhere (observed: breathing-frame edit moved the foot outline). When a frame is repaired by AI edit, pin static regions — feet, ground contact, anchor points — by copying them from the source frame, choosing the seam row per facing where outlines match best. Verify with a red/blue overlay diff on the pinned region and require zero pixel difference there; bounding-box comparison alone is not sufficient evidence.

Two failed attempts at the same defect trigger a changed technique: draw/edit a key pose, split a long action, separate effects, use an available native source, or report a precise capability blocker. Budget exhaustion never authorizes pretending a pass. Do not replace an articulated motion with a camera shake and call the requested action complete.

Runtime observations are separate: record engine version, commands/actions, current export identity, logs/screenshots and defects. Do not mark engine acceptance from a GIF or HTML canvas alone.


## v3.3 review additions

When `motion-check.json` exists, use it as a locator, not as evidence that a clip passed. Inspect every flagged pair and sample unflagged pairs. Under identity/anatomy/motion checks, explicitly look for hair/outfit/hand/weapon shape mutation, palette/value flicker, landmark jumps and static-region drift.

When sockets exist, overlay or otherwise inspect their declared positions against the visible hand, weapon base/tip, cast origin and feet. When depth profiles exist, verify actual occlusion in every bound direction. For a roster, use `family-check` plus a side-by-side sheet and record whether camera, body scale, outline/material language and cadence remain coherent.
