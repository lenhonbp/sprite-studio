# Agent workflow

Made by Nhon Le.

Choose the Git/local workflow in docs/LOCAL.md or the cloud plugin if connected. Local studio CLI edits share .studio with the local editor; rig-tool edits a separate JSON which needs import. Never claim a separate-file edit updated a live editor until imported/synchronized.

1. `studio_open {}` opens the MCP Apps resource when the host supports it.
2. `studio_read {}` returns the rig without embedded PNG bytes, current `revision` and `view` (clipId, boneId, slotId, time). Read before editing; sample rotation is an absolute value.
3. `studio_edit {baseRevision, requestId, operations}` applies 1–50 operations atomically. Use a unique requestId. Support the core operation schema in `web/rig-core.mjs`; bone keys use `{type:"bone-key", clip, bone, time, values}`. Preserve source rasters.
4. `studio_view {requestId, view}` selects the pose/playback/tool without adding to rig undo history.
5. `studio_undo` / `studio_redo` use current baseRevision and requestId. History includes UI and agent edits.
6. `studio_check {}` provides bounded technical preflight. It never approves art/runtime quality.

Example: after read returns revision 4 and the desired bone, send:
```json
{"baseRevision":4,"requestId":"example-unique-edit-0001","operations":[{"type":"bone-key","clip":"attack_se","bone":"arm_front","time":300,"values":{"rotation":-45,"easing":"smooth"}}]}
```
Do not reuse that literal request ID for multiple edits. If response is uncertain, retry with **identical ID and identical arguments**. Server remembers the latest 32 IDs and supplies the acknowledged project revision. If the project changed in the meantime, preserve the draft and reconcile; never overwrite the latest shared source to force a retry through. A real conflict requires a fresh read and intent-aware change.

`studio_poll` and `studio_replace` are app-only UI tools. Full rasters are passed through result `_meta` for the editor. Model-visible results omit raster bytes. UI uses the MCP Apps postMessage bridge; the standalone web uses authenticated same-origin API.

Local CLI is an alternative for offline JSON and native exports. Follow produce-game-sprites v3.8 Technical → Visual → Runtime gates when producing game assets.

## Git/local v3.3

For the shared local editor + agent CLI + stdio MCP workflow, use docs/LOCAL.md. This mode does not require the cloud plugin or authenticated hosting headers. All processes must use the same absolute data directory.
