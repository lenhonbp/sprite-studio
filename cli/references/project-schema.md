# Project schema: nhon-le-rig/v1

All coordinates use a single canvas, x right and y down. Rotation is degrees clockwise; scale must be positive. Bone/slot/clip/asset IDs use ASCII letters, digits, `_` and `-`, with an alphanumeric first character. JSON project assets are embedded PNG data URLs, with no external URLs or arbitrary file reads.

| Field | Meaning |
|---|---|
| `id`, `name` | Safe machine ID and human label |
| `canvas`, `origin` | `[width,height]` and fixed ground point in canvas pixels |
| `representation` | `hd` with smoothing or `pixel` with nearest-neighbor sampling |
| `bones[]` | Unique `id`, `parent` (ID or null), local `x,y,rotation,scaleX,scaleY` |
| `attachments` | ID → `{image,width,height,pivot:[x,y]}`; pivot in rendered attachment pixels |
| `slots[]` | `id,bone,attachment` (ID or null), `drawOrder` and optional local transform |
| `sockets[]` | `id,bone` and optional local transform; positions follow hierarchy |
| `clips[]` | `id,action,direction,duration_ms,loop,tracks,slotTracks,events` |

Bone tracks map bone IDs to strictly ordered unique keys: `{time_ms,x?,y?,rotation?,scaleX?,scaleY?,easing?,spin?}`. Values are absolute local values, not deltas. Missing channels retain rest transforms; the earliest authored channel value applies from its key time onward. Sparse channels interpolate independently.

`easing` on the earlier key controls interpolation toward the later key: `linear`, `smooth` (smoothstep), or `step`. Rotation takes the shortest arc unless the earlier key has `spin:true`. At a looping duration the sampler wraps to zero. Nonloops clamp to terminal time.

Slot tracks map slot IDs to strictly ordered `{time_ms,attachment?,drawOrder?}`. They switch discretely. Rest slot transforms apply after the bone's world transform. Equipment is therefore anchored in the bone's coordinate system.

Events are `{name,time_ms}`, with integer times in 0 <= time_ms < duration_ms (zero is valid; the terminal duration is excluded). This editor displays markers; final gameplay dispatch remains a target-engine test. Renderer frames use rounded cumulative millisecond boundaries, preserving total duration exactly. Nonloop final frames sample the exact terminal pose.

Limits: canvas 16–4096 pixels, 256 bones, 512 slots, 128 clips, 3000 frames/clip. CLI render enforces a 256 million sampled-pixel budget; browser export a 64 million budget. These caps guard runaway memory, not runtime texture acceptance.

## v2 optional authoring data (backward compatible)

Keep `nhon-le-rig/v1`; old projects load unchanged. Slots optionally store `opacity` in 0..1. Slot-track keys support x, y, rotation, scaleX, scaleY, opacity and easing alongside step attachment/drawOrder. Transform/opacity interpolation uses the same sparse-channel logic as bones. Attachment/order switch at their key timestamp.

`skins` maps safe preset IDs to `{slotId: attachmentIdOrNull}`. Applying a skin changes base attachments; existing animated slot overrides remain intact. `requirements` optionally declares `{actions:[...], directions:[...]}`. Coverage reports available clip pairs; it never synthesizes artwork or grants QA approval. Keep requirements in exported frame manifests rather than deleting missing directions to pass QA.

Sockets remain bone-local x/y values. Events have integer `time_ms`, a safe name and optional JSON payload. IK is an authoring solve whose ancestor rotations are baked into normal keys; there is no persistent runtime constraint. A selected joint must have parents and nonzero lever arms. Unreachable targets retain limb lengths and report residual.

Bones optionally declare `ikLimit:{min,max}` in absolute bone-local degrees. `bone-settings` accepts `limit` or null to remove it. The solver clamps rotations to these bounds; manual tracks are intentionally not clamped. Inspect anatomical/occlusion behavior independently.
