# Native and editable-source production

## Choose an executable method

Use host image tools for bitmap generation/editing, native source tools for editable layers, or a real rig for articulated animation. Do not hide missing capability behind "generate frames".

- Pixel with editable source: draw key poses at native size, preserve palette/tags, render through the available editor CLI.
- HD cutout: separate torso/head/limbs/weapon/VFX, define joints and draw order, author transforms. Draw missing views for occluded anatomy; one front image cannot be stretched into every facing.
- Vector/code-native: edit the project's parts and joints, keyframe parts, rasterize at target size. Whole-image motion is valid only for deliberately rigid/floating objects.
- Reference-guided bitmap: master → action key poses with stable identity references → small transition → inspect → repair. Without a temporal model, author in-betweens using tools actually available and report limitations.
- Existing frame family: map phase/timing/source topology first, then repair/restyle within that mapping.

## Pose cards

Write one short card per key pose: clip/direction/phase, visible anatomy, weapon hand/grip, planted contact, root convention, occlusion, motion margins and gameplay event. Mark intended constraints separately from observed pixels.

Establish ready/impact/recover for a strike, opposing contacts and passing for gait. Run keypose-check before expansion to verify indices, geometry and origin. Structural checks do not verify grip, facing or readable motion; inspect images.

## Hybrid rig and equipment

Follow the rig-first protocol ([rig-map.md](rig-map.md)): define joints and
anchors on the neutral master before cutting, store them in `rig.json`, and
pass the `verify_rig.py` reassembly gate before animating or swapping
equipment. Never infer pivots from part bounding boxes after the cut — stray
alpha inflates bounds and shifts the apparent pivot. Maintain joints in body
coordinates and attachment names, anchors and facing-specific draw order. When reskinning a rig, preserve atlas region size/rotation/trim offsets and mappings. Inspect extreme poses for seams, detached weapons, stretched sleeves and mesh deformation. Body, equipment and VFX can use different techniques but must share camera/scale/timeline.

A texture sheet is not a skeleton. Preserve actual Spine skeleton/atlas/pages/version and test its runtime. Never infer .skel from PNGs or claim a reskin creates a new rig. Complete-sheet reskins may lose tiny details: compare every attachment.

Measure part rectangles in the returned pixels; a requested equal grid may have unequal rows or part proportions. Compare nonzero-alpha bounds with meaningful coverage: nearly invisible stray alpha can inflate a part's bounds and shift the apparent pivot after scaling. A coverage threshold can help locate a known opaque part, but preserve its interior soft edges and record the measurement. Never apply a blanket threshold to glow/VFX or erase legitimate translucent pixels. Inspect extracted parts and the assembled neutral pose before authoring motion. A rig kit needs appropriate overlap and missing anatomy; arbitrary slicing cannot invent joints hidden in a reference.

Evaluate each facing independently. Keep a sword attached to the anatomical right-hand part and define facing-specific occlusion/attack arcs. Inspect the fully rendered extreme pose before choosing motion margins, including low-alpha pixels at every edge. Enlarge/reposition the shared canvas with a declared origin translation instead of clipping a late death or weapon frame. A torso rotated to horizontal with articulated limbs is a cutout fall; it is not evidence of a fully redrawn collapse. State that limitation and inspect its terminal silhouette.

## Style continuity

Save a concise style block with camera, native scale, proportions, palette/materials and contours. Keep identity and action blocks separate. Use references with clear roles. Compare against the approved master rather than chaining defective candidates.

For upgrades lock anatomy/origin and describe only the desired change. Reserve source canvas for the largest approved variant. Confirm source sheet cells before cropping; intended prompt arrangement is not measured topology.
