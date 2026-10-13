# UI/UX production system

This module extends the sprite-production skill into game-interface art without treating a generated UI image as a finished interface. A UI asset is production-ready only when the visual kit, interaction states, layout behavior, text policy, runtime scaling, and in-game usability have all been verified.

## Treat sheets as source material

Keep a generated or supplied UI sheet as source material, review its segmentation, and turn approved pieces into named runtime components. Refine weak pieces individually, export explicit size variants, record their mapping, and integrate them only after reviewing the real HUD layout.

Transfer the pattern, not the dependency:

1. **Reference the existing game first.** Use a gameplay screenshot, layout sketch, wireframe, or existing UI kit to preserve art direction and information hierarchy.
2. **Generate textless structural art.** Panels, tabs, buttons, badges, slots, frames, bars, arrows, cursors and ornaments should normally exclude final copy. Text belongs to the runtime localization layer unless the design explicitly requires decorative lettering.
3. **Separate aggregate ideation from runtime assets.** A generated sheet is a design source. Slice or recreate reviewed components into stable named files. Do not ship an arbitrary sheet crop with unknown padding and dimensions.
4. **Regenerate weak components individually.** One good panel does not make every icon or button in a sheet production-ready. Fix the smallest weak component while preserving shared style tokens.
5. **Keep one style system.** Palette, border thickness, corner language, material, highlight/shadow logic, icon stroke, spacing and state treatment must remain consistent across screens.
6. **Use generated segmentation only as a starting point.** Verify component bounds manually. Automatic segmentation cannot know semantic groups, nine-slice borders, invisible hit areas or desired runtime padding.

## Establish `ui-contract.json`

Start from `assets/ui-contract.example.json`. Adapt every value. The contract records:

- representation: pixel or HD;
- reference canvas and layout scale policy;
- safe-area policy;
- text/localization policy;
- minimum interactive touch target declared by the project;
- component role, state, group, source path and logical/touch size;
- optional nine-slice margins;
- required state sets;
- screen-flow/component references;
- runtime pixel-snap/integer-scale expectations;
- optional sheet slicing rectangles;
- optional `runtime_test_matrix` declaring required viewports, locales and input modes for final field verification.

Run:

```bash
python3 <skill>/scripts/sprite_tools.py ui-check ui-contract.json
```

The checker verifies structure, file readability, state coverage, touch-target declarations, safe-area content bounds, nine-slice source/logical geometry, text policy, safe project-relative paths and referenced components. It returns `review_required` when structurally valid because UX quality still needs human/runtime review.

## UI states are not optional decoration

For every interactive component, declare the states the actual game needs. Typical state families:

- button: default, pressed, disabled; hover/focus only when the platform uses them;
- tab: selected and unselected;
- slot: empty, occupied, selected, locked, invalid/drop-target;
- progress bar: frame, fill, optional warning/critical treatment;
- skill: ready, cooldown, unavailable, selected/aiming;
- item: normal, selected, equipped, rarity/quality overlays where applicable.

Do not fake states by tinting at runtime unless the art direction explicitly allows it. If a state changes silhouette, border, iconography or material, author it as a real state asset.

## Build layout before ornament

A beautiful panel is not UX. Define each screen's primary job and reading order before art polish:

1. primary information;
2. primary action;
3. secondary actions;
4. persistent navigation;
5. contextual feedback/error state.

For portrait mobile games, reserve gesture-safe and device-safe margins in layout code. Do not bake the entire screen background and controls into one image. Anchor interface groups to logical edges/containers so the layout survives aspect-ratio changes.

## Runtime sizing and nine-slice

Use fixed-size art only when the component is truly fixed. For variable panels and buttons, declare a nine-slice region that protects corners/borders and stretches only the center/edge zones. Never stretch pixel-art corners with non-integer resampling. For pixel UI, prefer integer scaling and pixel-aligned placement when the runtime permits it.

The checker validates only that declared nine-slice margins fit inside the source image. Visual confirmation must still verify that the chosen stretch zones contain no ornaments, glyphs, bevel corners or asymmetric highlights that would distort.

## Touch and readability

The contract's `minimum_touch_size` is project-owned. Do not silently invent a platform threshold. Interactive components can have a larger invisible touch area than their visual art. Verify:

- neighboring targets do not overlap or cause ambiguous taps;
- essential text remains readable at actual gameplay scale;
- color alone is not the only distinction for critical states;
- icons remain distinguishable in grayscale/low brightness where practical;
- destructive/rare actions have clear affordance and feedback;
- HUD does not cover combat-critical world space.

## Sheet slicing

When a reviewed aggregate sheet has reliable known rectangles, define `slices` in `ui-contract.json` and run:

```bash
python3 <skill>/scripts/sprite_tools.py ui-slice ui-contract.json --out <directory>
```

The tool validates every slice before writing any output, then crops declared rectangles without resampling. Duplicate slice IDs/outputs, parent-path escapes and out-of-bounds rectangles block before the output directory is created. It never guesses semantic names or nine-slice margins. For automatic provider segmentation, convert reviewed segmentation bounds into explicit `slices` first.

## UI acceptance gates

### Technical

- files open and match declared dimensions;
- required states exist;
- alpha and text policy are respected;
- nine-slice margins are valid;
- runtime names/paths are deterministic;
- pixel assets preserve intended sampling;
- no accidental sheet labels or model-generated text remain.

### Visual

- hierarchy is obvious at gameplay size;
- spacing, border weight, palette, material and icon language are coherent;
- selected/pressed/disabled/cooldown states read instantly;
- decorative detail does not reduce text or icon legibility;
- components still look correct at min/max intended panel sizes.

### Runtime UX

Test actual screens, not an isolated atlas:

- primary action reachable with intended input mode;
- touch targets work at device scale;
- safe-area and aspect-ratio variations do not hide controls;
- dynamic/localized text does not overflow;
- inventory/list content handles empty, short, full and overflow cases;
- transitions, modal focus, back/cancel and error states behave correctly;
- HUD remains readable during actual motion/combat.

A screenshot of a generated UI sheet is evidence of art direction, not proof of usable UX.

## Evidence-bound UI gates (v3.5)

A clean `ui-check` is only the technical gate. Create a fresh visual review bound to current component bytes and current screen evidence:

```bash
python3 <skill>/scripts/sprite_tools.py ui-review-template ui-contract.json \
  --evidence ui-screen-reference.png --out ui-review.json
# Inspect the bound evidence, fill every row with real observations/evidence names.
python3 <skill>/scripts/sprite_tools.py ui-qa ui-contract.json \
  --review ui-review.json --out ui-qa.json
```

The UI visual checks cover hierarchy/readability, state distinction, style consistency, text/localization fit, safe-area layout and nine-slice scaling. A changed component invalidates the binding and forces a new review.

For the actual runtime gate, use the approved current visual review and capture real target-engine/device/browser evidence:

```bash
python3 <skill>/scripts/sprite_tools.py ui-runtime-template ui-contract.json \
  --visual-review ui-review.json --evidence runtime-ui.png --out ui-runtime-review.json
# Record actual engine/version/project, tested viewports/locales/input modes/devices, and fill checks.
python3 <skill>/scripts/sprite_tools.py ui-runtime-verify ui-contract.json \
  --visual-review ui-review.json --review ui-runtime-review.json --out ui-runtime-qa.json
```

If `runtime_test_matrix` is declared, every required viewport, locale and input mode must be represented in the runtime review. The verifier checks binding/assertion completeness; it still cannot independently operate the game, so fabricated observations are not evidence.
