# Production v3.3 consistency contracts

Use these contracts to make common sprite failures observable without pretending that automation can judge art.

## Motion landmarks

For animation families that drift or deform, create `production-metadata.json` from `assets/production-metadata.example.json`. Landmarks are designed body-space observations in cell pixels: head, pelvis, feet, grip, knees or other joints useful to the action. Record only points that can be reviewed against visible pixels; do not invent a hidden skeleton and call it measured truth.

Landmarks serve three purposes: compare adjacent poses, pin repair-sensitive regions, and make directional/body proportion drift easy to inspect. Large landmark steps are review flags, not automatic art failures. A fast attack can legitimately move a wrist or weapon tip farther than a breathing clip.

## Weapon and VFX sockets

Declare sockets where runtime attachments or effects actually need them. Prefer semantic names such as `hand_main`, `hand_off`, `weapon_base`, `weapon_tip`, `cast_origin`, `head_fx`, `body_center`, `foot_l`, `foot_r`. A socket can vary per frame. Missing sockets declared in
`required_sockets_by_action` are structural blockers because runtime attachments
cannot safely guess them. Incomplete observed `required_landmarks` remain warnings;
record only visible measurements, never invented coordinates. For an attack, review the visible hand/grip, socket, weapon art, trail/VFX and hit event together.

Do not substitute sockets for visual grip review. A numerically stable socket attached to a malformed hand is still malformed art.

## Directional depth/occlusion

Top-down 3/4 sprites need an explicit depth profile per facing. Declare a back-to-front layer order, then bind clips to the applicable profile. Review rear/front arm swaps, weapon crossing, hair/cape order, robe/leg overlap and rear/front VFX. Mirroring an asymmetric profile is not automatically valid.

## Temporal consistency

Run:

```bash
python3 <skill>/scripts/sprite_tools.py motion-check animation-set.json \
  --contract production-metadata.json --out motion-check.json
```

The checker can report silhouette-area jumps, alpha-bounding-box center jumps, pixel-art palette drift, landmark/socket jumps and declared static-region changes, including the
last→first boundary of looping clips. `temporal_thresholds.socket_step_px` defaults
to 16 px and is a review threshold, not a hard artistic limit. Thresholds are suspicion thresholds. Inspect every flagged pair and also sample unflagged pairs; absence of flags is not visual approval.

For AI-edited frames, static-region checks are particularly useful for feet, ground-contact pixels, belt buckles, face features or other areas expected to remain identical. Do not declare large moving regions static just to force a low drift number.

## Locomotion calibration

For each in-place locomotion clip, record stride pixels, cycle duration, pixels-per-world-unit and target game speed. `motion-check` reports the implied speed and declared tolerance. This is a calibration aid only. Runtime field verification still measures planted feet in actual world/camera transforms.

## Collision metadata

Per-frame hurtboxes/hitboxes may be included in the metadata contract. Keep them in cell coordinates and inside the cell. Review the hit volume on the actual impact pose. Runtime tests must still separate event dispatch, collision intersection and damage application.

## Transition matrix

List meaningful clip transitions rather than assuming every first/last pose is compatible. At minimum cover idle↔walk, walk→attack→idle, attack interrupted by hit/death, direction changes and death terminal hold. Structural checks verify referenced clips exist; visual/runtime gates verify continuity.

## Provenance

For repaired/generated production frames, record method, tool/model/version when known, parent frame IDs and source/reference lineage. Provenance exists to make repairs reproducible and to prevent an agent from losing the approved source chain. It is not a quality score.

## Roster/family consistency

Create `family-contract.json` from `assets/family-contract.example.json`, then run:

```bash
python3 <skill>/scripts/sprite_tools.py family-check family-contract.json --out family-check.json
```

The checker compares declared representation/cell invariants, the full required action × direction matrix, reference origin Y and visible reference-frame height. Then perform side-by-side visual review at native and gameplay scale for camera, head/body ratio, outline weight, value range, materials, weapon scale and cadence. Automated geometry alone cannot prove that a roster belongs to one art direction.

## Performance budget

Record a conservative raw RGBA frame budget and expected simultaneous actor count where H5/mobile limits matter. `motion-check` reports a raw frame-memory estimate. The packed atlas/runtime GPU cost still depends on atlas dimensions, texture format, engine/browser behavior and duplication, so final performance acceptance belongs to runtime profiling.

### Intentional coverage exceptions

`invariants.allowed_missing_pairs` may exempt only explicitly named combinations.
Each entry is an object with `action`, `direction` and a nonempty `reason`, for example:

```json
{"action":"dead","direction":"north","reason":"Shared south-facing corpse is an approved project design"}
```

Presence of every action and every direction separately does not establish matrix
coverage. Duplicate resolved member-manifest paths are rejected. Exceptions are
project decisions, never automatically inferred from missing files.

### Source-sheet preflight

`sheet-separability-check` examines all four group edges and requires a continuous
transparent gutter (`minimum_gutter_px`, default 2) between pose centers. The report
binds its result to the current source SHA256. Optional layout `source_sha256` must
match the image before the result can be used. A fresh report is required after
source edits. Projection confidence remains heuristic: transparent gaps cannot prove
anatomy, restore occluded pixels or grant visual approval.

UI slice outputs are resolved before preflight. Alias paths, parent-file/child-path
conflicts, and the reserved `ui-slices.json` manifest path are rejected before
creating an output directory.
