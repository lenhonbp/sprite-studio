# Sprite Studio

**AI-assisted sprite, rig-animation and VFX production studio for games** — made by [Nhơn Lê](https://github.com/lenhonbp).

Design pixel-art characters, animate them with editable raster rigs, author multi-layer VFX, QA everything with evidence — then export to **Canvas/HTML5, Phaser, Three.js, Unity, Cocos Creator, Godot, PixiJS**, or generic PNG + JSON. One source of truth, every engine.

![version](https://img.shields.io/badge/version-4.1.1-blue) ![license](https://img.shields.io/badge/license-MIT-green) ![node](https://img.shields.io/badge/node-22%2B-brightgreen)

## Why Sprite Studio?

- **Agent-led art production** — the bundled `produce-game-sprites` skill (v3.8) lets an AI agent own art decisions, repairs and delivery with verifiable QA gates, instead of generating loose images.
- **Editable raster rigs** — pose characters with bone/keyframe rigs on real PNG layers (v2.2), bake IK, keep the source pixels untouched.
- **VFX Studio** — multi-layer texture / flipbook / particle / trail effects with size & alpha curves, normal/additive blending, socket and event previews, and a VFX timeline.
- **One export, every engine** — pick the target in the editor or pass `--engine`; same art, origin and timing everywhere. No rebuilding assets per engine.
- **Evidence, not vibes** — `verify:pack` checks PNG/atlas/timing/contracts/adapters with SHA-256 baselines; field-test reports ship in `docs/`.
- **Runs anywhere** — zero-install offline HTML, local server, CLI, or MCP for agents.

## Quickstart

### Option A — Offline (no install)

1. Download the [latest release](../../releases) and unzip.
2. Open **`Nhon-Le-Sprite-Studio.html`** in Chrome, Edge, Firefox or Safari on desktop.
3. Edit, preview and export — no Node.js or Python required.

### Option B — Local server (recommended)

Requires **Node.js 22+**.

```bash
git clone https://github.com/lenhonbp/sprite-studio.git
cd sprite-studio
npm start
# open http://127.0.0.1:8787
```

The editor, CLI and local MCP share the same data, revisions and undo/redo.
No `npm install` needed for this mode. Full guide: [docs/LOCAL.md](docs/LOCAL.md).

### Option C — As an agent skill

```bash
npm run rig -- help      # rig JSON tooling
npm run art -- --help     # full sprite / UI / VFX / environment toolkit
npm run audit             # verify skill files and rig code
npm run test:skill        # run the skill test suite
```

Requires **Python 3.10+** and **Pillow** for the toolkit. Read [AGENTS.md](AGENTS.md) when opening this repo with an agent. Skill source: [skills/produce-game-sprites](skills/produce-game-sprites).

## What's inside

| Area | Highlights |
|---|---|
| Sprite production | AI-assisted character/prop/UI generation, directional animation, palette & pivot QA, atlas handoff |
| Rig animation (v2.2) | Editable PNG-layer rigs, bone/keyframe authoring, baked IK, equipment layers |
| VFX Studio (v4) | Texture/flipbook/particle/trail layers, curves, blend modes, timeline, socket/event preview |
| Engine adapters (v4.1) | Canvas/HTML5 · Phaser · Three.js · Unity · Cocos Creator · Godot · PixiJS · Generic PNG+JSON |
| QA & handoff | `verify:pack` (SHA-256 baselines, texture budgets), contracts, release gates, field-test evidence |

Try the sample project: open `projects/combat-vfx.rig.json` — character + slash trail + hit burst + aura. (Sample art is unreviewed.)

## Key commands

```bash
npm run doctor                  # check your environment
npm run production -- help      # production CLI
npm run production -- engines   # list export targets
npm run test:engines            # adapter checks (Node 22.13+)
npm run verify:pack -- DIR --rerender   # verify a pack, optionally re-render from source
npm run test                    # full test suite
```

## Documentation

- [docs/LOCAL.md](docs/LOCAL.md) — local server, MCP config, Git workflow
- [docs/PRODUCTION.md](docs/PRODUCTION.md) — VFX Studio and production pipeline
- [docs/ENGINES.md](docs/ENGINES.md) — export targets and verification scope
- [docs/INTEGRATION.md](docs/INTEGRATION.md) — components and editor → QA flow
- [docs/HANDOFF-CHECKS.md](docs/HANDOFF-CHECKS.md) — handoff verification
- [docs/QA.md](docs/QA.md) — quality gates
- [docs/FIELD-V4.1.1.md](docs/FIELD-V4.1.1.md) — latest audit notes
- [AGENTS.md](AGENTS.md) — guide for AI agents working in this repo

> Most deep-dive docs are currently in Vietnamese; the README, CLI help and skill contracts are in English. Contributions translating docs are welcome.

## Project structure

```
skills/          agent skill (produce-game-sprites v3.8)
web/             editor UI
local/           local server, CLI, MCP (stdio)
server/          shared server code
cli/             rig and art tooling
scripts/         build, audit, verify, production CLIs
docs/            guides, QA and field-test evidence
projects/        sample rig projects
dist/            built offline bundle
```

## Contributing

Issues and pull requests are welcome. Run `npm run doctor` and `npm test` before submitting. For art contributions, keep AI-generation logs so provenance stays transparent.

## License

MIT — see [LICENSE](LICENSE).

## Author

**Nhơn Lê** — game developer & toolmaker. Sprite Studio is the production pipeline behind his H5 game art workflow.
