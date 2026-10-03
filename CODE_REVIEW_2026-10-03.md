# Code review — 3 October 2026

Review of the current source, recent file changes, route metadata, and read-only local API responses.
This is a source review, not proof that every route wins. No gameplay was started during this review.

## Recent implementation work

- Replay placement recovery now learns per-map legal/illegal spots and terrain appearance samples,
  ranks alternatives, estimates path coverage, and considers nearby support towers.
- Terrain motion sampling and ORB feature tracking attempt to follow towers on moving platforms.
- Placement confirmation checks, free-placement visual checks, and failure screenshots supplement cash OCR.
- Save-file hotkeys are passed to replay on each launch and mapped to physical key codes. The UI
  lists missing bindings and suggests unused keys.
- Cash OCR loads its neural model lazily. HUD recovery cancels held ghosts and closes panels;
  repeated unreadable frames can still invoke Escape.
- Lives monitoring can trigger emergency spending. Surplus spending can buy additional upgrades
  and bring later purchases forward while a route is waiting for a round.
- Failure reports include action/state evidence and a bounded full log. Losses are classified,
  early placement failures receive limited retries, and late losses enter a strengthening queue.
- A separate sweep dashboard polls the guest, attempts recovery after selected interruptions,
  and keeps the VM display open. Playthrough content endpoints support edits with backups.
- Medal decoding now treats SuperChimps as CHIMPS and uses a numeric threshold of 0x100000;
  low attempt counters are no longer counted as earned medals.
- Sweep ordering prioritizes the CHIMPS prerequisite chain and shuffles the remaining branches.

## Remaining gaps found

1. **Running server and source differ.** During review, `/api/farm/status` responded, but
   `/api/route-failures` returned 404 even though that endpoint exists in current `server.js`.
   The responding installation needs deployment/restart before its new failure API can be used.
2. **Boss execution is incomplete.** The generator copies an ordinary map recording, removes
   banned placement lines, and does not construct a complete boss economy/damage strategy.
   The UI still submits it as a normal file replay. Boss-specific filename handling in JS does
   not supply the Python boss navigation/execution flow. Stored routes are keyed by boss and
   variant rather than event ID, which also permits stale weekly routes.
3. **Max all towers is incomplete.** It reads the inventory and launches the XP farm runner.
   There is no complete tower-by-tower farming and unlock-purchase loop behind this control.
4. **CHIMPS behavior can change at runtime.** Surplus spending is enabled for CHIMPS, and
   placement search can move recorded positions. Preserving the route file alone does not
   preserve its actual execution.
5. **Absent save records can exclude maps.** With a readable profile, sweep eligibility is
   restricted to maps present in the profile map records. A missing record needs to be distinguished
   from a locked map so unplayed maps are not silently dropped.
6. **Route editing is local to the serving process.** `/api/playthroughs/content` reads/writes
   local files without forwarding to the guest. Editing through the host endpoint therefore does
   not itself update the route the VM runs.
7. **Placement learning is heuristic.** Frame differences and ghost tint are not definitive tower
   identity checks. Motion sampling can include bloons/projectiles; terrain classes do not encode
   every tower footprint. These mechanisms need live validation on the special maps.
8. **Some recovery still leaves/restarts runs.** Repeated opening placement failure deliberately
   enters GOTO_HOME; the watchdog can terminate stalled replay processes. This differs from the
   requested policy of recovering within the live match whenever possible.
9. **Hotkey handling has a partial fallback.** Unbound tower actions become unavailable, while
   unbound upgrade/play bindings retain older defaults. This can send the wrong action when users
   customize or clear those bindings.

The saved route coverage report dated 29 September lists 878 eligible map/mode pairs out of 1,204
across 86 maps, with 326 gaps. Eligibility includes imported and reused routes and is not a count
of locally verified victories. The report should be regenerated after further route changes.

## Repository preparation

The repository includes working engine sources as ordinary files, preserving their attribution
and license files. Local saves, player progress, credentials, dependencies, and build output are
excluded. A neutral `userconfig.example.json` supports fresh checkouts; the installer builder uses
that example when no private userconfig exists.
