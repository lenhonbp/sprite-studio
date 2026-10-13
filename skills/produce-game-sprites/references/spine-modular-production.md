# Spine and modular cutout production

Use for Spine/cutout characters, modular equipment and atlas-part reskins. The goal is to change appearance without breaking rig topology or runtime compatibility.

## Spine and modular production rules

Choose the smallest edit that satisfies the requested change. Preserve the project’s rig and atlas structure unless a rig revision is part of the task:

1. **Inspect first.** Record runtime/source version, animation names, skins, slots, attachments, atlas pages and region geometry before edits.
2. **Preserve topology.** Appearance edits must not silently rename bones/slots/attachments, alter mesh topology, change region count or invalidate atlas mapping unless the task explicitly calls for a rig change.
3. **Replace the smallest unit possible.** If one weapon/hat/armor piece is wrong, replace that attachment rather than regenerating the whole character.
4. **Preserve region geometry.** Keep selected part size, position, orientation and pivot/attachment assumptions unless the rig is intentionally updated with it.
5. **Clean editor artifacts geometrically.** Atlas frames/labels should be removed using known region/layout geometry, not fragile color matching.
6. **Round-trip runtime test.** Load the final package in the target runtime and play representative animations before approval.

Follow the project’s installed Spine runtime and export contract; do not assume a universal version or conversion path.

## Modular equipment

The existing `rig.json`/rig-map workflow remains authoritative for body-space joints and anchors. Equipment additionally needs:

- owning slot/attachment name;
- draw-order relationship;
- grip/socket relationship;
- allowed body variants;
- pivot and local transform;
- overlap/occlusion masks when needed;
- visual bounds and runtime hit/collision behavior kept separate.

Validate neutral reassembly first, then representative animation poses, then runtime swapping.
