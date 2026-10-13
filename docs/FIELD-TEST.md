# Field test and fixes — v3.3.1

Made by Nhon Le. Tested 2026-10-11 on Linux, Node 24.19.0, Python 3.12.14, Pillow 12.3.0 and the available native canvas. Started from the delivered v3.3 ZIP in a fresh directory, reproduced failures, repaired source and retested a fresh final ZIP. This report concerns operation and production workflow; it does not approve the demo as game art.

## Reproduced defects and corrections

| Finding | Evidence before patch | Correction |
|---|---|---|
| Existing local editor stops following after server restart | Its old cookie returned 401; a new agent key changed 88 → 99 on disk while the tab stayed at 88 | Local page declares its mode; bridge renews its HttpOnly cookie through same-origin health and retries the same request. ChatGPT sign-in stays hidden for local mode |
| History cap counts characters instead of actual stored bytes | Large Unicode source: history 7,879,134 characters but 12,679,134 UTF-8 bytes against the advertised 8 MB | Trim history using encoded UTF-8 byte length; regression keeps actual history <= 8,000,000 bytes |
| Stdio initialize accepts a malformed JSON-RPC envelope | A request missing jsonrpc received a successful initialize result | Validate the envelope and ID before dispatch; invalid request returns -32600 |
| Missing --data argument emits an uncaught stack trace | Options were evaluated before the CLI error handler | Evaluate options inside the structured error handler |
| Event schema wording is ambiguous | Authored walk event at 0ms is valid, while docs say strictly inside duration | Document 0 <= time_ms < duration_ms |

Stdio output now waits for drain when the consumer is slow. No source-schema/math changes or production-gate relaxations were introduced.

## Actual operation scenarios

`npm run test:field` starts an actual HTTP server on a temporary loopback port, uses a temporary disk workspace, and closes/removes it at completion. It tests backend transport, not a preview browser.

- Fetch HTML, module/CSS/JSON assets and verify MIME/status. Verify no-cookie rejection, foreign origin/Host rejection, unsupported method, 404, >5 MB body rejection and server still responding afterward.
- Execute 24 consecutive edits and check revision/history. Reject an invalid operation batch without changing source. Race six independent CLI processes on one revision: exactly one succeeds; five return 409. Retry identical write ID/arguments without adding a second edit; reject reuse with different arguments.
- Run the actual bridge code against real HTTP/disk with a minimal editor/DOM model. Retain a drag draft; pause/resume; simulate a failed network request; discard a response only after the backend commits; reconcile the identical retry; retain a draft when another actor edits concurrently.
- Stop and restart the server on the same port with the same disk state. Reject the old cookie, renew the local session, then load the newer agent edit in the existing editor model.
- Export the current full source; run actual stdio MCP child process; read the same revision and invoke check; reject invalid initialization envelope. Verify malformed CLI arguments produce structured errors.
- In a child process, fsync a new state temporary file then force SIGKILL before atomic rename. The previous state file stays byte-identical. Doctor reports a dead lock; unlock removes it; the next normal edit succeeds. This is a deterministic process-crash fault, not a power-loss/filesystem-damage simulation.
- Exercise a large Unicode source through real disk-backed edits and measure actual history bytes. The repaired cap holds.

The final ordinary workspace reaches revision 33. Existing unit/regression suites additionally cover identity isolation, undo/redo, selection, batch transactionality, lost-response reconciliation, snapshot/backup quota and corrupt-state retention.

## Art workflow on the full master

An independent fresh task used the ZIP's bundled skill and full authoring master. It equipped hat, added attack_contact at 333ms, added grip_proof on grip and changed the attack arm key at 340ms from -70 to -90 degrees. It rendered 35 RGBA 512x512 PNGs at 12fps. Every PNG spans transparent/partial/opaque alpha; clip durations remain idle 1200ms, walk 800ms and attack 800ms. Mathematical grip_proof matches hand_main on all sampled frames. Only three attack frames changed after the isolated key edit.

The task actually viewed representative native frames, contact sheet, light/dark before-after images and grip overlays. Technical inspection passes. Motion-check reports nine attack temporal findings; the edited swing has sampled grip/tip jumps around 139.175/167.792px, and a representative sword pose crosses the skirt/thigh. No target/collision/depth test exists. This shows successful authoring and faithful detection of review work, not acceptance of that swing. A newly bound partial visual review remains blocked; playback/transitions and runtime stay untested. No approved atlas/release was fabricated.

The demo remains one direction, three limited cutout clips. Full eight-direction characters, production animation quality and target-engine acceptance are outside these tool field tests.

## Reproduce and verification limits

```sh
npm run audit
npm test
npm run test:field
npm run test:canvas
npm run test:skill
```

Canvas tests need the optional native dependency; production toolkit tests need Python/Pillow. Existing base skill suite passed 118 Python tests plus timeline/player/clock regressions, and rig suite passed 45 tests. User source and local state are not included in the release; field fixtures are synthetic/example data created in temporary directories.

Actual browser control is unavailable in this environment. CSS, responsive layout, native pointer/touch, Safari downloads, native IndexedDB behavior and a real ChatGPT/MCP host iframe are therefore not verified. The HTTP bridge test uses a DOM model; native rendered PNG inspection uses native canvas/Pillow. Godot/PixiJS gameplay rendering and Windows/macOS process/filesystem behavior remain unverified. Restart/process-crash recovery does not guarantee power-loss or failing-disk recovery; export source backups regularly.
