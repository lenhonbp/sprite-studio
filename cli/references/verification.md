# Observed verification · 2026-10-11

Made by Nhon Le.

- Shared-core/CLI suite: 27 tests passed, including real PNG rendering, socket hierarchy, sparse channels, loop/terminal sampling, exact duration sums, invalid-source declarations, cyclic parents, transactional key edits and refused overwrites.
- Editor exercised with a mocked DOM and a real native canvas: key edits, undo/redo, rest-rig mode, equipment swaps, invalid reparent, added bones/clips, copy/paste, duration changes, JSON save, PNG/ZIP export and empty project creation passed. ZIP CRC/content round-trip and v3.8 manifest validation passed.
- Final southeast demo rendered 35 frames at 12 fps for idle/walk/attack, with no visible canvas-edge contact or empty frames; companion inspection had no errors. Original v1 full Site demo source SHA-256: `9955f14faf542e8dc18ec29d15deb0f0f15d86fee27416f1f7dc5758fa855c24`.
- A fresh agent used the actual skill to equip a hat and author an attack revision, rendered 69 frames and prepared v3.8 proof. It found a source grip/pivot mismatch by inspecting artwork; the final demo was corrected from measured palm and handle landmarks, preserving raster source pixels.
- The original companion v3.8 Python suite: 118 tests passed. Skill frontmatter validation passed.

Limits: no browser-control capability was available, so responsive CSS, browser downloads and pointer behavior have not been checked in a real browser. Mocked interaction tests are not browser QA. No actual Godot/PixiJS gameplay import or visual playback approval was performed. The demo remains an unapproved authored cutout example; temporal/ground/transition findings still need visual and runtime review. No live MCP server, deformable mesh or Spine skeleton export is implemented.

## v2 verification

The original 27 core/CLI tests still pass. Eighteen additional tests cover transactional authoring, reference cleanup, key collisions, sparse slot transforms/alpha, events/skins/sockets, feasible and unreachable CCD IK, action × direction gaps, sheet page geometry, actual sheet-to-frame RGBA round-trip and external GIF decoding with timing/overwrite checks. Expanded mocked DOM/native canvas tests exercise slot keys, events, sockets, presets, clip duplication/deletion, coverage requirements, actual sheet/GIF downloads, key pointer dragging, IK pointer input and viewport panning. This remains mocked interaction verification; no real browser/CSS or Godot/PixiJS runtime approval is claimed.

The v2 demo adds authored IK bounds (torso -10..10°, front arm -95..75°). Its full editor source SHA-256 is `e6677380cfcfb6cf5f2be58626972db3446e04707dd2dabd7c8454d459d5807c`. Both modular and standalone bundled editor paths passed the mocked DOM/native canvas scenario. An independent authoring task generated all three export types and identified an unreachable grip target; angular bounds improved observed torso posture, but did not make that target reachable. No candidate was promoted to an approved release.
