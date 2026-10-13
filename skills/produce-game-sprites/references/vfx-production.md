# VFX sprite production

VFX should usually remain separate from character body frames so timing, blending, reuse and repair stay controllable.

## Contract

For each effect declare:

- one-shot or loop;
- frame timing and terminal behavior;
- world-space, actor-space or socket-space attachment;
- socket name and offset when attached;
- blend intent (normal/additive or engine equivalent);
- soft/binary alpha requirement;
- native canvas/origin;
- hit/gameplay event relationship;
- overdraw/performance budget;
- whether the effect may extend beyond the character cell.

## Production rules

- preserve translucency for smoke, glow and energy when the art direction needs it;
- do not force soft VFX through binary-alpha cleanup;
- author anticipation/impact/decay phases rather than uniform brightness across frames;
- separate gameplay hit timing from the brightest visual frame when design requires it, but declare both;
- keep trail direction and weapon-tip/socket alignment coherent across adjacent frames;
- inspect against both dark and light gameplay backgrounds;
- for looped aura/environment effects, inspect end-to-start motion and alpha continuity;
- atlas VFX only after final timing and bounds are stable.

## Structural checker

Create `vfx-contract.json` from the bundled example and run:

```bash
python3 <skill>/scripts/sprite_tools.py vfx-check vfx-contract.json --out vfx-check.json
```

The checker validates safe project-relative frame paths, static/readable images, common canvas, optional declared cell size, authored durations, alpha policy, attachment/socket metadata, event times inside the effect duration and basic simultaneous-memory estimates. It deliberately does not approve perceived impact, engine blend result, overdraw or gameplay-hit alignment; those stay visual/runtime gates.

## Evidence-bound VFX gates

After `vfx-check`, bind current contact-sheet/playback evidence:

```bash
python3 <skill>/scripts/sprite_tools.py vfx-review-template vfx-contract.json \
  --evidence vfx-proof.png --out vfx-review.json
python3 <skill>/scripts/sprite_tools.py vfx-qa vfx-contract.json \
  --review vfx-review.json --out vfx-qa.json
```

Then verify the actual target-engine result:

```bash
python3 <skill>/scripts/sprite_tools.py vfx-runtime-template vfx-contract.json \
  --visual-review vfx-review.json --evidence vfx-runtime.png --out vfx-runtime.json
python3 <skill>/scripts/sprite_tools.py vfx-runtime-verify vfx-contract.json \
  --visual-review vfx-review.json --review vfx-runtime.json --out vfx-runtime-qa.json
```

Final runtime evidence must show the real blend mode, authored playback timing, transformed socket attachment, gameplay-hit alignment, simultaneous effects and target-device/browser performance.

## Sellable packs

`vfx-check` validates one effect's production contract. When the deliverable is
a multi-effect pack for sale (itch.io bundle, GIF previews, AI disclosure,
marketplace policy gates), run the vfx-pack module instead — spec and bundle
validation, generation recipes and the sales playbook live in
[vfx-pack.md](vfx-pack.md). Per-effect `vfx-check` contracts declared in the
pack spec are re-validated by `vfx-pack-bundle-check`.
