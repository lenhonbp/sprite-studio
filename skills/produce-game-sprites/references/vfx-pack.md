# Sellable VFX pack production (vfx-pack)

For in-game VFX authoring and QA gates read [vfx-production.md](vfx-production.md) first.
This document covers the *pack-for-sale* layer: effect taxonomy for generation
recipes, provider generation recipes, post-processing, sheet assembly,
the itch.io-ready sales bundle and marketplace policy gates.

## 1. Effect taxonomy

Use these fixed taxonomy ids in the pack spec so prompt recipes, reviews and
the bundle manifest share one vocabulary:

- `hit-spark` — tiny impact flash, 3–5 frames, one-shot
- `impact-burst` — radial burst with decay, 5–10 frames, one-shot
- `slash-arc` — weapon arc trail, 4–8 frames, one-shot
- `muzzle-flash` — short flash at barrel/socket, 2–4 frames, one-shot
- `explode-burst` — large explosion, anticipation → blast → smoke tail, 8–16 frames, one-shot
- `status-aura` — looped aura (burn/frost/shock), 4–8 frames, seamless loop
- `projectile-trail` — looping streak, 3–6 frames, loop or one-shot
- `ground-crack` — decal that appears and lingers, hold terminal frame
- `magic-circle` — summoning ring, fade-in → hold → fade-out
- `heal-glow` — soft rising particles, loop or one-shot
- `smoke-plume` — slow dissipating smoke, 6–12 frames
- `portal-gate` — swirling gate, looped

Declare the taxonomy per effect in `vfx-pack.json`; `vfx-pack-plan` rejects
anything outside the list so a typo cannot silently change a pack's content.

## 2. Provider recipes (not installed API integrations)

These adapter names select production recipes. This skill does not implement
provider authentication, SDK calls, retries or network generation. Inspect the
host's actual tools and provider documentation before choosing a provider.
Record the provider/model, seed, prompt, date and `vfx_id` for every effect.
Never assume a trial, price or commercial-use license from this document.

- **pixellab**, **retro_diffusion**, **scenario** — possible image-generation
  providers; verify their current animation capabilities and licensing first.
- **embergen** — simulation-based flipbook authoring; inspect the installed
  tool and export settings.
- **native** — authored animation in an available editor.
- **other** — a named alternative with documented capabilities.

Use an approved motion proof before expanding any recipe into a full pack.

### Prompt recipe rules (VFX)

Append these to every generation prompt, verbatim intent:

- `EXACTLY {N} cells in a {rows}x{cols} grid, horizontal strip preferred`
- `identical camera, scale and palette across all cells`
- `no zoom, resize, morphing or background change between cells`
- `native RGBA transparency, preserve soft alpha` when supported; otherwise
  declare the background/removal method and prove edge quality first
- taxonomy keyword, e.g. `taxonomy: impact-burst`
- effect timing hint, e.g. `anticipation → blast → smoke dissipate`

Keep `fixed_seed` constant for the whole pack; change the seed only to
regenerate a rejected effect, never to "improve" an approved one.

### Cost discipline

Declare `cost_per_effect_usd` before generating. `vfx-pack-plan` computes the
pack total as **cost per effect × effect count**, independent of frame count.
This estimate assumes one successful effect; log retry costs separately. Do not
put per-frame or per-request pricing into a per-effect field. Re-check the provider's current pricing before any paid
run — the numbers in the research snapshot age fast. Never present a credit
balance or per-generation price from memory as current.

## 3. Post-processing

1. **Alpha preservation:** use native RGBA masters whenever possible. A flat
   chroma-key image does not contain the original soft alpha and foreground
   colors; cleanup cannot recover them exactly. For smoke/glow, use editable
   sources or regenerate transparent masters. Any approximation needs edge
   review over both light and dark backgrounds.
2. **Grid split:** cut on exact cell boundaries only. If cells touch or
   overlap, stop: hidden composited pixels cannot be recovered. Regenerate
   isolated strips or use an editable source instead (see
   [sheet-processing-bridge.md](sheet-processing-bridge.md)).
3. **Pixel-snap and palette lock:** reduce to the declared palette; no
   resampling.
4. **Alignment:** anchor every frame on the burst center (or declared socket),
   not on each frame's own bounding box.
5. **QA:** build a GIF preview per effect and run it through the normal
   `vfx-review-template`/`vfx-qa` visual gate with playback evidence.

## 4. Sheet assembly

The bundle validator expects a **uniform untrimmed row-major grid**. Copy
explicit source RGBA frames into equal cells without resizing, recentering,
alpha compositing or trimming. The declared frame order controls cell order.

Aseprite `--sheet-type packed` produces rectangle-packed output and is not this
schema. An Aseprite export must be converted into the uniform grid and the
skill's metadata schema; its native JSON is not the metadata accepted below.

Requirements enforced by `vfx-pack-bundle-check`:

- exact grid cell count and cell size;
- every source is readable, explicit, nonempty and obeys its alpha policy;
- every ordered cell matches its source RGBA bytes, including hidden RGB;
- metadata binds frame IDs, paths, durations, loop, blend, alpha and events;
- GIF count, size, loop, per-frame timing and pixels match the preview mode.

GIF supports binary transparency, not soft alpha. For soft effects, create a
composited GIF over a declared opaque background and keep RGBA PNG masters.
Declare metadata `gif_preview: {"mode":"composite","background_rgb":[20,20,20]}`.
For binary-alpha effects, `{"mode":"binary-alpha"}` is also supported. GIF
palette quantization permits a mean RGB error of at most 8 per channel;
alpha must match exactly. Each duration must differ from the declared duration
by less than 10 ms, allowing GIF centisecond rounding, and must remain positive.
Looped effects require GIF loop=0; one-shots must omit the loop extension.

Example metadata (frame entries copied in exact order from the pack spec):

```json
{
  "vfx_id": "fire_burst",
  "loop": false,
  "blend_intent": "additive",
  "alpha_policy": "soft",
  "events": {"visual_peak_ms":120,"gameplay_hit_ms":60},
  "frames": [{"id":"fx_000","path":"vfx/fire_burst_000.png","duration_ms":60}],
  "gif_preview": {"mode":"composite","background_rgb":[20,20,20]}
}
```

## 5. Sales bundle

`vfx-pack-bundle-check` validates this layout:

```
bundle/
  LICENSE                 # your terms: single-seat commercial, no resale as-is
  README.md               # pack contents, install/usage notes
  AI_DISCLOSURE.txt       # required when any frame is AI-generated
  generation-log.csv      # vfx_id, model, seed, prompt, date per effect
  pack-manifest.json      # pack_id + per-effect sheet/gif/meta paths
  sheets/<vfx_id>.png
  previews/<vfx_id>.gif   # the itch.io storefront demo
  meta/<vfx_id>.json      # frames, durations, blend intent
```

Manifest `effects` must be an array of unique declared IDs, each with exact
`sheet`, `gif` and `meta` paths:

```json
{"pack_id":"ember_fx_pack_01","effects":[{"vfx_id":"fire_burst",
 "sheet":"sheets/fire_burst.png","gif":"previews/fire_burst.gif",
 "meta":"meta/fire_burst.json"}]}
```

Keep a nonempty `generation-log.csv` with unique columns `vfx_id,model,seed,prompt,date`
and complete data rows covering every effect. Multiple rows per effect can log
retries. Logs support provenance review; they do not prove copyright ownership.
LICENSE, README and AI disclosure files must be nonempty. The disclosure file
inside a ZIP does **not** complete the itch.io product-page disclosure.

## 6. Marketplace policy gates and source dates

These are policy snapshots checked **2026-10-09**, not publication approval.
Re-read the target's official rules before uploading. Commands never upload.

| Marketplace | Declared AI-generated pack |
|---|---|
| itch.io | Declare AI use on the product page using its AI Disclosure setting; an archive text file is insufficient. |
| GameDev Market | New generative-AI assets are not accepted; planning blocks this target. |
| Unity Asset Store | Verify current submission guidelines and disclosure requirements; the planner emits a reminder, not certification. |
| Other targets | Check current official terms and allowed licenses before publication. |

Official sources:

- [itch.io creator quality guidelines](https://itch.io/docs/creators/quality-guidelines#ai-disclosure),
  accessed 2026-10-09: disclosure is enforced for asset pages; untagged pages may be delisted.
- [GameDev Market policy update](https://www.gamedevmarket.net/news/an-important-update-on-generative-ai-assets-on-gdm),
  published 2025-08-27, accessed 2026-10-09: explains nonacceptance of generative-AI assets.
- [U.S. Copyright Office Part 2 announcement](https://www.copyright.gov/newsnet/2025/1060.html),
  published 2025-01-29, accessed 2026-10-09: protection depends on sufficient
  human expressive authorship. Prompts alone do not establish it. Creative
  arrangements or modifications may qualify case by case; cleanup, slicing,
  assembly and QA do not automatically make generated content copyrightable.
  This is U.S. guidance, not a worldwide ownership determination.

## 7. Commands

```bash
python3 <skill>/scripts/sprite_tools.py vfx-pack-plan vfx-pack.json --out pack-plan.json
python3 <skill>/scripts/sprite_tools.py vfx-pack-bundle-check vfx-pack.json --dir bundle/ --out pack-bundle.json
```

`vfx-pack-plan` validates the spec, computes per-effect and pack totals
(frames, duration, cost estimate), lists every deliverable the bundle must
contain, and blocks marketplace policy violations. `vfx-pack-bundle-check`
verifies the built bundle directory: required files, sheet grid geometry, GIF
frame parity, metadata consistency, and any declared per-effect
`vfx_contract` re-validated through `vfx-check`. Keep each contract next to
`vfx-pack.json` with project-relative frame paths (the same convention as
`vfx-contract.example.json`), so the same contract passes standalone
`vfx-check` and the pack bundle check.

Both report `ready` or `blocked`; bundle reports also expose `structural_ready`,
`source_binding` hashes for source PNGs, `artifact_binding` hashes for bundle
files and `spec_binding`. A change to any bound file requires a fresh check. A `ready` bundle is still not for sale until
the per-effect visual (`vfx-qa`) and target-runtime (`vfx-runtime-verify`)
gates pass — bundle checks validate files and geometry, never art.
