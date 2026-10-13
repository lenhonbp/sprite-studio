# Rig editor bridge

Made by Nhon Le.

Use the integrated `tools/rig-animation` module for authored layered raster motion and agent CLI operations. Preserve body-space joint definitions and source layers; the companion is an authoring tool, not QA approval. Its render output includes animation-set.json, production-metadata.json with mathematical sockets, art-contract.md with source hash, and rig-source.json. Run this toolkit’s inspect, preview and motion-check, inspect actual output, create current bound reviews, then QA/export and actual target-engine acceptance.

The companion demo has one direction and three limited cutout clips. Do not infer missing camera views, claim Spine skeleton export, or treat the preview as a finished game asset.

Call `node <this-skill>/tools/rig-animation/scripts/rig-tool.mjs` for validate, sample, set-key, set-slot, add-bone render, edit, ik, coverage, sheet and gif. The module shares its mathematical core with the published Nhon Le Sprite Studio editor.

The integrated module is now v2.0: baked CCD IK, clip/bone management, event/socket authoring, animated equipment transforms/opacity, skin presets and coverage requirements share the same validated source with the editor. Preserve raster sources and all v3.8 acceptance gates.

## Live agent editor v3

Use the connected Nhon Le Sprite Studio plugin when the user wants to edit the rig shown in chat or the hosted editor. Open with `studio_open`; read with `studio_read` before any mutation. Use returned `revision` as `baseRevision` and a fresh unique `requestId`. `studio_edit` applies 1–50 operations atomically. It supports the rig core operations and `{type: "bone-key", clip, bone, time, values}`. Follow actual tool schemas. Use `studio_view` to select a clip, bone, slot, time in milliseconds, playback or stage tool. Shared `studio_undo` / `studio_redo` include both chat and manual changes.

Preserve rasters; online projects are limited to 4 MB and shared history to 20 steps / approximately 8 MB. UI receives full project through tool-result `_meta`; the model sees the rig without PNG bytes. Read-only queries do not create a stored project. If a revision conflicts, reread and explain the concurrent change; never replace the whole project to bypass a conflict. Retry uncertain network writes with the identical request ID and identical arguments. IDs are remembered for the latest 32 requests; after that, reconcile state before retrying.

Example: read the current selected clip/bone/time; inspect its sampled rotation; add a bone-key with the desired absolute rotation; then use studio_view to show that exact pose. Do not invent a delta operation or assume the first clip is selected. IK is bounded CCD and may leave a residual; inspect the returned pose and do not claim an unreachable target was reached.

For the original hosted Site, if the plugin is unavailable and the user requests that Site, use Sites get_site(include_mcp_connection=true) for project `appgprj_6acb43addfcc8191953af0524bd6698e`, then offer the returned plugin ID through plugin management. Do not create a duplicate plugin. The editor is at https://nhon-le-sprite-studio.lethanhnhon22847.chatgpt.site . A host that supports MCP Apps can show the editor in chat; other hosts can still call tools. CLI remains the fallback for local JSON, larger projects and native exports. Validate visual motion and target-engine behavior through the existing production gates; a connected editor is not QA approval.

## Unified Git/local workspace

When this skill is inside a repository with AGENTS.md, package.json scripts.start, local/studio-cli.mjs and docs/LOCAL.md, read those instructions first. Run npm start from that repository. Use the shared studio CLI or configured MCP stdio to edit the active local project. Read revision before editing, retain identical arguments when retrying, and keep drafts on conflict. The module CLI edits standalone JSON, not the active workspace: export with studio export, operate on a fresh candidate, then studio import with the revision read before making that candidate. If the workspace has changed, compare and reconcile rather than import with a newly invented revision.

The canonical rig implementation is tools/rig-animation/scripts; browser assets are generated from it by the repository build and checked by npm run audit. Do not edit generated web copies. Run npm run rig -- help and npm run art -- --help from the repository for rig authoring and the full production toolkit. Render candidate frames, then run inspect/preview/motion-check and actual evidence reviews; a rig source check never approves rendered art or runtime. The toolkit's sheet-processing companion remains optional and separate; do not imply it is bundled or merge incompatible schemas.
