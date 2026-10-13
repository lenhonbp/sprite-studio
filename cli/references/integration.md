# Integration with produce-game-sprites v3.8

1. Preserve the source `.rig.json` and real raster layers. Render to a fresh candidate directory:
   `node <sprite-skill>/tools/rig-animation/scripts/rig-tool.mjs render hero.rig.json --fps 24 --out candidate-01`.
2. Run `python <sprite-skill>/scripts/sprite_tools.py validate candidate-01/animation-set.json` and `inspect ... --out inspect-01.json`.
3. Run `preview ... --out proof-01` and `motion-check ... --contract candidate-01/production-metadata.json --out motion-01.json`.
4. Open contact sheets and actual playback. Inspect anatomy, grip, extreme poses, layer swaps, ground behavior, transitions and every required direction. The tool's socket values are authored rig positions, not observed artwork landmarks.
5. Create a fresh bound review with `review-template ... --evidence proof-01/contact-sheet.png --evidence proof-01/index.html --out review-01.json`. Fill only checks actually observed. Unseen playback/runtime remains incomplete.
6. Run `qa`; only current technical and visual approval allows `pack`. Test the result in the actual target-engine project and complete the companion runtime and release gates.

The rig editor exports candidates without faking approval. Its proof is not a Spine skeleton, target-game import or ready-made eight-direction production character. Runtime atlas export stays owned by the v3.8 toolkit.

The bundled raster demo is newly assembled from generated isolated parts. Its master kit and reviewed rectangles are retained in the companion Site source under `authoring-source`; initial body placement and motion are authored. It demonstrates editor/CLI behavior and supplies only southeast idle, walk and attack.

The bundled demo uses a uniform half-size source-image derivative with unchanged rendered dimensions/pivots; the full authoring project remains available from the editor.
