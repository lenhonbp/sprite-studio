# Rig-first: assign rig positions before cutting parts

## The problem this fixes

Cutting a character into parts (modular equipment, HD cutout rigs, part reskins)
and reassembling them misaligns when the rig is defined *after* the cut:

- Pivots inferred from a part's bounding box drift: nearly invisible stray alpha
  inflates the bounds and shifts the apparent pivot after scaling. A pivot guessed
  from pixels is not a designed joint.
- No canonical coordinate space declared before cutting, so each part carries its
  own implicit offset and reassembly becomes guesswork.
- No numeric reassembly check, so drift is discovered only by eye — usually late.

## Rule

**Define the rig on the neutral master first, cut second, verify reassembly
against the master with numbers before any animation or equipment swap.**

This applies to every workflow that separates a character into parts. Whole-image
frame animation (no cutting) does not need it.

## Protocol

### 1. Pick the canonical pose

Use the neutral master per direction (usually idle frame 0). All rig coordinates
are cell-local `xy` points in pixels, same convention as landmark measurements:
origin at the cell's top-left, x right, y down. Record the cell size and the
declared ground origin alongside the rig.

### 2. Mark joints on the actual pixels

Mark on the neutral master image — never from memory or from a different pose.
Standard joint names (use anatomical left/right, not screen left/right):

- `neck`, `shoulder.L`, `shoulder.R`, `elbow.L`, `elbow.R`, `wrist.L`, `wrist.R`
- `grip` (weapon hand contact point; separate from the wrist when the weapon
  extends beyond the hand)
- `hip.L`, `hip.R`, `knee.L`, `knee.R`, `ankle.L`, `ankle.R`

Add attachment anchors as needed: `head` (headgear), `back` (cape/quiver),
`waist` (belt items), `handheld` (off-hand item). One rig per direction — a
back-view shoulder is not the front-view shoulder mirrored.

### 3. Define parts against the rig

Each part records:

- `name`, `rect` (`x, y, w, h` in cell-local pixels) with a 2–4 px overlap margin
  into its neighbor — a hard edge-to-edge cut always shows a seam when rotated.
- `pivot`: the joint the part rotates around, in **body coordinates**
  (cell-local on the neutral master), not part-local. Store both; the part-local
  pivot is derived, never the source of truth.
- `draw_order` and facing-specific occlusion (which part covers which, per
  direction).

Write this as `rig.json` (schema: [rig-map.example.json](../assets/rig-map.example.json)).

### 4. Cut parts per rig.json

Cut exactly the declared rects. Do not re-trim, re-center or "clean up" bounds
afterwards — any change to a part's pixels invalidates its pivot.

### 5. Mandatory reassembly gate

Place full-canvas parts at `(0,0)` and rect-sized crops at their declared rect
origin. This neutral placement does not infer a transform from a pivot. Composite
in declared draw order, then compare against the neutral master:

- Lossless reassembly: **every RGBA pixel must match exactly**, including alpha.
  Grayscale NCC remains a diagnostic and cannot override changed colors or alpha.
- Every part pivot must be an integer point inside the cell, on that part's visible
  pixels. When `pivot_joint` is declared, `pivot_body` must exactly equal the
  corresponding declared joint. No anatomical mapping is invented for a part
  without `pivot_joint`.
- Part names must be unique safe basenames; rects must be positive and contained
  in the cell. Invalid declarations are input errors, not visual approval failures.

Run `scripts/verify_rig.py` for this check. If it fails, fix the rig or the part
rects — never proceed to animation hoping motion will hide it. Rotation
magnifies pivot error: a 1 px pivot offset becomes a multi-pixel arc at the
part's far end.

### 6. Then animate or swap

Author joint rotations against the same rig; equipment swaps reuse the same
`rig.json`. A reskin must preserve part rect size and pivot — changing either
is a new rig, requiring a new reassembly gate.

## Common failures

| Symptom | Likely cause | Fix |
|---|---|---|
| Parts drift when reassembled | Pivot inferred from part bbox after cutting | Re-mark joints on the master, rewrite rig.json, re-cut |
| Seam line at a joint when rotating | No overlap margin in part rects | Add 2–4 px overlap, re-cut, re-verify |
| Weapon detaches at swing extremes | `grip` not marked separately from `wrist` | Mark the true contact point on the master |
| Back view reassembles wrong | Front-view rig mirrored blindly | Mark a separate rig per direction |
| Passes still, breaks in motion | Pivot error < 1 px at neutral | Tighten: error scales with rotation radius |

This gate checks neutral source placement and declared pivot consistency only.
It does not measure joints after rotation or prove an animated skeleton is correct.
If layered semi-transparent overlap changes the master during compositing, revise
the source layers/masks to reproduce it exactly before proceeding.
