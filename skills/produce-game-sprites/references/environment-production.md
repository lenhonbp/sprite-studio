# Environment, tiles, maps and props

Use this module for top-down, isometric or layered environment production. A pretty tile is not map-ready until footprint, anchor, seam and layering behavior are proven in an assembled test map.

## Environment production rules

Apply these rules to every map and tile set:

- treat tile footprint as a logical contract, not as the outer PNG dimensions;
- align projected/isometric tiles by logical centers/anchors;
- do not crop or recenter generated tiles merely because transparent padding differs;
- multi-cell assets must declare their occupied footprint separately from image bounds;
- validate a composed test map and seams, not isolated tile canvases;
- keep pixel and HD sampling rules separate;
- preview parallax/background/midground/foreground layers together before approval.

## Top-down 3/4 environment contract

For the user's common portrait action-RPG case, define:

- tile/grid unit in world pixels;
- camera pitch/style convention;
- ground contact and prop pivot;
- walkable/collision footprint independent from visible bounds;
- draw-order/depth key (usually a foot/base point, not image center);
- occluder behavior for tall props;
- terrain transition vocabulary;
- prop scale tiers relative to the hero;
- shadow direction/shape policy;
- whether the map is authored as tiles, chunks, painted background, or hybrid.

## Seam and repetition QA

Build a repeated 3×3 or larger sample for seamless materials. For terrain transition atlases, test every edge/corner combination used by the game's autotile logic. Repetition artifacts that are invisible in one tile can dominate a full screen.

## Layering

Keep ground, decor, collision/logic and occlusion conceptually separate. For a tall tree/building, do not let the collision footprint equal the full transparent image bounds. Runtime sorting should use a declared base point and, for large multi-cell assets, account for the full occupied footprint.

## Props/items

Props and pickups should declare gameplay scale, ground/base pivot, collision need, interaction highlight/outline need and inventory-icon relationship. A world prop and its inventory icon may share identity while using different camera/contrast simplification.

## Structural checker

Create `environment-contract.json` from the bundled example and run:

```bash
python3 <skill>/scripts/sprite_tools.py environment-check environment-contract.json --out environment-check.json
```

The checker validates safe project-relative prop paths, readable nonempty images, base pivots, footprint cells, optional collision rectangles, occluder declarations, tile/seam metadata and basic geometry. Structural success remains `review_required`: it does not prove seam quality, depth readability, collision feel or assembled-map composition.

## Evidence-bound environment gates

After `environment-check`, capture an assembled-map proof and bind it:

```bash
python3 <skill>/scripts/sprite_tools.py environment-review-template environment-contract.json \
  --evidence assembled-map.png --out environment-review.json
# Inspect and fill every visual row.
python3 <skill>/scripts/sprite_tools.py environment-qa environment-contract.json \
  --review environment-review.json --out environment-qa.json
```

Only after visual approval create the final runtime review:

```bash
python3 <skill>/scripts/sprite_tools.py environment-runtime-template environment-contract.json \
  --visual-review environment-review.json --evidence runtime-map.png --out environment-runtime.json
python3 <skill>/scripts/sprite_tools.py environment-runtime-verify environment-contract.json \
  --visual-review environment-review.json --review environment-runtime.json --out environment-runtime-qa.json
```

Runtime evidence must cover actual seam assembly, depth sorting/occlusion, collision/walkability, camera scale and sampling in the requested engine/project.
