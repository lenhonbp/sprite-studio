# Alpha, grids and frame editing

For actual slicing, read [sheet-processing-bridge.md](sheet-processing-bridge.md). Use the installed raster processor for margins/gaps or source reconstruction, preserve provenance and run verify_slices.py before fresh visual/runtime acceptance.

## Alpha policy

Declare binary or soft alpha when needed. Opaque pixel actors can use hard edges; spells, glass, smoke and HD contours may need translucency. Do not binarize every asset because the game is pixel art. Inspect against light and dark at native and integer enlarged scales.

Check matte halos, lost holes, removed highlights and erased soft effects. Color-key removal can erase a matching costume color: color distance is not subject segmentation. Compare retained and cleaned backgrounds when both exist.

## Grid integrity

Treat pixels as authored geometry. Nearest enlargement preserves them; shrinking a painting does not establish a pixel grid. Automatic detection can fail on simple blocks, detailed scenes and mixed-grid batches. Inspect each object independently when grids differ. Use process-sprite-sheets recovery tools where appropriate, then inspect actual outputs.

Optional max_colors measures distinct visible RGB colors, excluding transparent padding. It is a budget, not proof of good contours/clusters. Soft-alpha levels are measured separately.

## Editing and segmentation

Appearance edits should preserve source frame mapping and durations unless retiming is designed. Video-reference regeneration may resample the action, changing duration/count; treat it as a new timeline candidate.

A segmentation rectangle is only a candidate crop. Check completeness, non-overlap, transparent margins and IDs. Weapon bounds are not actor root. Preserve crop offsets; do not infer direction/phase order from position.

Use a capable project processor for arbitrary grids, trimmed frames or shared layers. Standalone extract only handles exact row-major cells without gutters. Fully composite GIF/WebP disposal before extraction and retain decoded durations.

## Turnaround sampling

Keep posture, root and camera stable. Label selected views from actual facing and physical left/right, not uniform frame indices: generated rotation speed may vary. Preserve asymmetric equipment and front/back occlusion. Repair ambiguous views before expanding actions.
