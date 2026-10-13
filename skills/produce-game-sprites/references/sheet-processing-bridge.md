# Sheet processing bridge

Use produce-game-sprites for production direction and acceptance; use the installed process-sprite-sheets raster processor for specialized extraction. Resolve both installed paths dynamically and read its SKILL.md and references/raster-cli.md before use. Do not copy an older ZIP over that processor. If unavailable, use a capable project tool; do not claim the standalone extract supports gutters or arbitrary rectangles.

## Choose the operation

| Source/task | Processor | Constraint |
|---|---|---|
| Known equal animation cells | grid | Declare rows, columns, cell dimensions, margins and gaps; exact fit, no discarded remainder. |
| Isolated irregular items | auto | Connected regions are geometry, not semantic objects; detached VFX can split and touching items can merge. Review every cut. |
| Rows grouped into multi-direction actions | analyze-action-blocks | Confirm direction/action/phase order from source evidence, never aspect ratio or filenames. |
| Enlarged pixel blocks | detect-grid / recover-grid | This estimates the native pixel lattice, NOT animation cell boundaries. Recovery is a separate candidate requiring review. |
| Animated GIF/WebP | composed-frame extraction | Preserve disposal/composition and decoded duration; do not slice the first still. |
| Registered source/restyle comparison | compare-clone | Same dimensions/grid; restyle metrics do not approve anatomy or timing. |

## Preflight → cut → reconstruct → review

1. Preserve the source and bind its decoded RGBA hash. Inspect source topology and editable metadata. For aggregate generated poses, run sheet-separability-check against a reviewed layout before automatic slicing. A separable status only screens alpha/gutter risk; it neither determines exact rectangles nor proves every pose is complete. Opaque matte needs a reviewed alpha candidate before this heuristic is meaningful. Overlap/hidden pixels require isolated regeneration or editable/native reconstruction, not midpoint/watershed splitting.
2. Freeze explicit named rectangles and action/direction/phase mapping. Check bounds, duplicate IDs/outputs, unintended rectangle overlaps, complete expected slots and gutter exclusion before writing. Use a fresh output directory. Preserve intentional empty frames.
3. Cut without resampling. Keep animation cells untrimmed by default; if trimming is required, record retained pixel bounds and offset, restore into the original cell canvas, and keep origin expressed in that canvas. Do not infer actor roots from weapon/cape bounds or move each frame to its lowest visible pixel. Never bottom-align or auto-center an already registered animation.
4. Create slice-provenance.json and run `python3 <produce-skill>/scripts/verify_slices.py slice-provenance.json`. It checks safe paths, source identity, unique IDs/outputs, rectangles, offsets, duration/origin metadata and exact RGBA reconstruction. It does not cut, infer semantics, prove origin correctness or approve art. Bind the report and manifest as fresh review evidence. A changed source/manifest/output invalidates that evidence.
5. Inspect numbered cut previews against the source, all PNGs and playback at runtime size. Check intact hands/feet/weapons/VFX, consistent origin, all directions/actions and terminal/empty frames. Run the chosen authoritative contract's technical and visual gates, then actual runtime verification. Exact crop fidelity cannot reveal that the authored rectangle itself amputates a pose.

## Provenance schema 1

Paths are relative to the provenance file directory. `source_rgba_sha256` hashes decoded RGBA bytes (not PNG encoding); dimensions are separately checked. `expected_ids` is the full ordered extraction list. Each frame declares `id`, `output`, `source_rect` [x,y,w,h], `offset` [x,y] inside that rectangle, `origin` [x,y] in original-cell coordinates, and positive integer `duration_ms`. The output is either the full rectangle or a losslessly trimmed part padded back at offset. Nonzero pixels may not be omitted. Shared cell size and shared origin are required by this strict animation profile. For intentionally varying registration, retain full cells or use the processor's production contract rather than weakening this profile.

Use reviewed named rectangles for icons/UI instead; do not force item packs into an animation timeline.

## One authoritative manifest

| Meaning | produce-game-sprites | process-sprite-sheets production |
|---|---|---|
| Required coverage | required_clips | Exact named slots and clips |
| Timeline | Explicit ordered frames + duration_ms | Slot durations, clips, events |
| Registration | Canvas/origin + production metadata | Native canvas/origin + source mapping/layers |
| Acceptance | validate → bound qa → runtime-verify | validate-contract → bound qa → verify-runtime |

This table is conceptual, not an interchangeable JSON schema. Read toolkit.md or the processor's production-manifest.md for the selected owner. Translate IDs/order/timing/source offsets explicitly when importing extracted frames; validate the destination and compare coverage/timing. Keep slice provenance as evidence, not a competing gameplay contract. Do not pretend a schema converter exists.

Keep authoring masters and apply one family-wide master→runtime transform. Re-run technical/visual QA after conversion. GIF is a lossy preview (256 colours, 10 ms timing); preserve native PNGs and exact timeline metadata. Do not silently retime clips to match preview rounding.
