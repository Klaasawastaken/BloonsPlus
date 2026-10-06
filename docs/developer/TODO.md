# Bloons+ roadmap and repair list

Updated 6 October 2026. Checkboxes require evidence, not merely code. Preserve original CHIMPS recordings and BTD6 saves. Gameplay stays behind simulated input.

## Current repair pass

- [x] Reproduce Infernal ABR false visual placement acceptance at x=13: screen-edge crop clipping shifts the measured centre and accepts animation/decorations. Require a complete visual probe region for no-cash confirmation. The actual-function regression fails before the fix and passes after; six HUD/placement, three held-placement and three confirmation-mode checks pass. This does not prove the Heli strategy winning. Its defeat remains persisted; do not reset route attempts blindly.


- Confirmed Bloody Puddles Reverse at round 60 (6 October 05:31:56): replay VICTORY_CONFIRMED, controller clear confirmation and authoritative VM save Medium/Reverse=1049549. Never replay the earned medal. Preview 56 boundary update completed and its worker confirmed the missing-medal sweep resumed on Infernal ABR.
- [x] Reproduce map-search Enter doing nothing in the browser. Activate the selected visible enabled row or first match through its existing click handler; preserve native input/change events. Include optgroup labels in refresh signatures. Run selected starts disabled and remains disabled for absent routes, stale controller status, owned medals or an active job. Unknown medal evidence is now labelled Waiting for game save instead of Not completed. Also prevent the global Escape shortcut from navigating away after a dropdown consumes it, or while a dialog is open. Browser verification confirms Enter selects the map and Escape closes the menu without leaving Automation. Fix the run chooser’s medal lookup to use exact normalized save/display aliases, matching Maps. Existing alias and medal-gate checks pass.


- [x] Rework Settings into connection, appearance and support sections; keep optional ISO/install details and resets collapsed, clarify retry setup, remove the unused AI Settings initializer. Preserve setup/update/reporting hooks and automatic profile detection. Browser layout reviewed; JS syntax checks pass.
- [x] Preserve pinned BTD6bot Spike Factory Normal → Smart targeting for bottom tiers 2–4 using two forward presses. Other uncertain cycles remain excluded. Six separate candidates pass full parser and strict JS legality; original recordings unchanged. Coverage is 513/1,204, with 691 gaps and four maps without eligible routes. No new victories claimed.


- [x] Preserve round-read freshness separately from a retained counter. Unreadable frames cannot refresh its timestamp; resumed checkpoints are not new observations. New failures use guest read/end timestamps to reject counters older than ten seconds for loss-stage classification, retaining the last readable number and timestamp as diagnostics. Legacy records retain their interpretation. Two runtime regressions, eight helper cases, loss/failure classification and four ledger checks pass. Live deployment pending.
- [x] Give only Infernal Reverse/ABR Heli candidates one stable new attempt revision after the live-confirm fix. Keep failure history, unrelated exclusions, other Infernal modes and original CHIMPS unchanged; owned-medal admission still applies. Targeted hash regressions pass. No route win claimed.
- Preview 54 updater completed after Infernal Reverse ended in defeat (last readable round 17; actual loss round not established while the counter was blocked). Guest confirmed the missing-medal sweep resumed and began Bloody Puddles Reverse.

- [x] Correct Infernal’s displayed terrain guidance: include the narrow left/right edge strips for Heli/Farm footprints, reserve space before support, and require live legality. Source: https://bloons.fandom.com/wiki/Infernal . This does not authorize an unobserved placement or change original recordings.

- [x] Reproduce stale confirmation-mode admission from an old private flag. Start each replay with mode unconfirmed, learn it only from the actual post-click check button, and stop persisting the setting. Preserve historical files without reading/deleting them. Three actual-block regressions pass (old flag ignored, live check clicked, absent check sends no input) plus eight nearby placement/HUD checks. Infernal recovery still needs a missing-medal run; do not mark its routes winning.

- [x] Add bounded placement-search diagnostics for footprint, active confirmation mode, candidate count and source-hint live verdicts. Infernal ABR still lost at round 19; this is instrumentation, not a repaired strategy claim.

- [x] Respect hidden optgroups in dropdown rendering/signatures, close open menus when the document becomes hidden, and give Settings error surfaces sufficient specificity in both themes. Syntax/diff checks only; broader dropdown keyboard and visual coverage remains open.
- Preview 53 boundary update completed after Infernal ABR lost at round 19; the guest confirmed the missing-medal sweep resumed. Heli recovery remains unresolved; no medal claimed.

- [x] Finish the Settings help pass: make logs/reporting directly accessible, keep installation/reset details collapsed, hide empty guest VM actions, remove obsolete calibration instructions, and start setup/update buttons disabled until fresh connection state arrives. Reuse existing redacted reporting; JS syntax/diff checks and browser accessibility tree reviewed. No active replay interrupted.

- [x] Reproduce client-geometry error masking: 304x201 and 320x180 windows incorrectly ended as minimized. Preserve transition/not-ready reasons and dimensions; reserve minimized for a zero-area/iconic client. Four actual-function geometry checks pass. No live capture failure or complete installer recovery claim.

- Confirmed Bloody Puddles Alternate Bloons Rounds at round 80 (6 October 04:58:22): replay VICTORY_CONFIRMED, controller clear confirmation and authoritative VM save Hard/AlternateBloonsRounds=1049865. Never replay the earned medal. Preview 51 updater then completed at guest idle and confirmed the missing-medal sweep restarted.

- [x] Validate resumed tower/history ledgers before atomic replacement: malformed objects, entries, tiers, positions or history must not crash later optional purchases or partially replace state. Copy only matching run/map/mode data. Four corruption/copy tests and eleven resume checks pass; a read-only current VM snapshot with eighteen towers is accepted. No actual interrupted-run recovery claim.

- [x] Reproduce missing exact tier intent in surplus upgrades: the actual planner returned no expectedUpgradeTiers. Copy the selected candidate’s target tiers into its action, independent of later roster entries/mutations. Existing observation and checkpoint machinery now receives exact intent for safe selection/retry/resume. Two intent, twenty observation and five checkpoint checks pass. Use path_index consistently in surplus logs. No live wrong-tier purchase or subsequent victory claimed from these offline checks.

- [x] Review pinned Randy-Hodges ordinary runner: start_game sends two Space presses, click sends one position click, ordinary finish sends no input, Sanctuary uses a separate manual handler. Preserve startup as observed fast intent and map clicks as exact commands; reject moving-map/manual cases. Add eight separate Hard startup candidates and one Quad BloonsPlayer startup alternative. Full Python parser and strict JS legality pass; importer repeat/overwrite preservation checks pass. Coverage remains 509/1,204; no new wins claimed.

- [x] Restrict hero-picker search to the live three-column card region. Old Geraldo/Corvus positions fell into the detail panel and repeated unchanged titles. Keep cached layout hints advisory and live title/Selected verification required; no new hero selection claimed from this source edit.

- [x] Simplify Settings maintenance: separate ordinary appearance/connection controls from installation details and the advanced preference/queue reset. Keep automatic game-profile detection out of manual settings. Disable stale setup/update actions for HTTP failures as well as network failures, and recheck controller availability after failed updates. JavaScript syntax and diff checks pass; visual review pending.

- [x] Add same-map, same-tower route coordinates as unverified placement hints after local search fails. Normalize/deduplicate source coordinates, reject malformed maps/resolutions and out-of-bounds points, require positive live preview, preserve occupancy/range checks, and exclude CHIMPS/dynamic maps from this fallback. Actual search probes pass without game input. Infernal Heli hints include (103,600), (102,571) and opposite-bank (1565,553); none newly claimed legal.

- [x] Allow one stable fresh attempt specifically for non-CHIMPS Infernal routes with Heli after this evidenced recovery change. Preserve unrelated failure exclusions, original content hashes and saved-medal skipping. Actual fingerprint checks pass. Infernal ABR round 19 and Reverse round 17 defeats remain recorded; their routes are not marked fixed or winning.

- Preview 50 deployment completed after Infernal Reverse ended; its worker confirmed the missing-medal sweep restarted. Preview 51 source changes are not yet deployed.

- [x] Diagnose Infernal ABR Heli retries from screenshot/logs: held placement remained and the run did not earn its medal at round 19. Separate learned placement spots/samples/refusals by tower or hero footprint. Remove victory-route planned-placement seeding, which incorrectly treated skipped towers as confirmed placements. Preserve legacy data without applying its broad terrain-only buckets. Offline actual-function probes and eight existing HUD/placement checks pass; this does not prove the Heli route fixed.

- [x] Prevent stale refusal caches from blacklisting changed terrain phases or earlier runs' occupied layouts. Dynamic-map spots still require live hover/click confirmation; cached refusal is not current legality evidence. Current static-run scoped refusals remain effective. Earlier negative observations remain stored for learning. Offline probes only; phase-specific live recovery remains open.

- Preview 48 deployment completed at the Infernal ABR boundary and the guest confirmed the missing-medal sweep restarted. Infernal Reverse is now active; no ABR clear claimed.

- Preview 50 published with exact packaged replay.py/automation.js/app.js source matches. Its boundary worker is live and waiting for Infernal Reverse; stop-after-replay is confirmed. Do not overwrite its reserved root payload while it waits. Heli recovery still needs live evidence; investigate tower-specific source placement hints as unverified hover candidates, not confirmed legal memory.

- [x] Remove the separate live route-verification API mode, its one-attempt-per-map branch and UI status path. Completion automation now has one missing-medal sweep; historical files preserved. Actual API rejects legacy run types before runtime startup. Five existing offline sweep checks pass (saved-medal gate, alternatives, ordering, counts and delayed medal confirmation). Deployment pending; no validation game launched.

- Confirmed Infernal Hard at round 80: replay logged VICTORY_CONFIRMED and authoritative VM save Hard/Standard=1049864. Never replay it. Preview 45 update worker completed at idle and confirmed the missing-medal sweep restarted.

- Preview 48 published. Exact packaged helper.py, automation.js and app.js match source. Boundary deployment worker is waiting while Infernal Alternate Bloons Rounds earns its missing medal; stop-after-replay is confirmed. Deployment is pending, not yet claimed.

- [x] Remove obsolete achievement sweep implementation and API run type, which ignored owned medals. Preserve historical progress data; automation status now displays the current job's victory/defeat counters instead of the obsolete recording count. Missing-medal sweep remains the supported completion loop.

- [x] Reproduce malformed saved modifiers crashing replay startup and unknown modifiers silently becoming bare upgrade keys. Reject unsupported modifier/device combinations in both replay decoding and route readiness; malformed binding entries no longer crash decoding. Supported keyboard scan codes and Shift/Alt/Ctrl preserved. Offline checks only; deployment pending at a replay boundary.

- [x] Finish Settings connection cleanup: distinguish the guest's Game Connection from host VM setup, disable stale install/update actions during controller disconnection, and label queue reset explicitly. JavaScript syntax checked; live replay left untouched.

- [x] Keep host run requests queued while VM setup/update owns the job, including ownership claimed during awaited game-status probes. Pending dispatch resumes through its existing timer after setup finishes. Pause/stop/stop-after relay remains available. Deployment pending.

- [x] Reproduce concurrent VM update requests starting two installers; recheck setup-job ownership after the awaited guest idle probe. Setup state now writes and flushes a unique temporary file before atomic replacement, preserving old state when replacement fails and rejecting non-object cache shapes. Offline checks only; clean Windows installation remains open.

- Confirmed Flooded Valley Reverse at round 60: saved Medium/Reverse=1049545 and observed replay result victory. Never replay it. Preview 42 deployed at the boundary and the missing-medal sweep resumed on Infernal Hard.

- [x] Diagnose Flooded Valley Reverse’s unselected Sniper upgrades from the live frame: placement-only close template=0.996, nudge cancel=0.400, shop cyan fraction=0.475. Recognize ordinary shop-based held placement and cancel it before selecting an existing tower. Persistent held state withholds the target click. Live deployment remains queued; screenshot private.

- Refreshed offline coverage on 6 October: 509 eligible map/mode pairs, 695 gaps (21 with rejected candidates, 674 without a found candidate). Source Auto Start controls need observed setting ownership; time-based clicks alone cannot establish faithful manual-round conversion.

- [x] Validate checkpoint unresolved-upgrade collections, action metadata and strict integer offsets before recovery. Reject duplicate recorded queue positions instead of repeating a placement/purchase. Malformed data now reaches the existing explicit resume-refusal handler. Manual Auto Start source plans remain unsupported pending observed setting control; do not relabel them faithful.

- [x] Pass a read-only Profile.Save-derived per-tower path unlock snapshot at replay launch. Optional surplus upgrades respect owned contiguous tiers; unknown names cannot authorize purchases. Unavailable snapshots retain live observation recovery. Recorded actions and game saves are unchanged; deployment pending.

- Confirmed Flooded Valley Alternate Bloons Rounds victory at 03:46:39, round 80; authoritative VM save Hard/AlternateBloonsRounds=1049865. Missing medal earned; never replay it. Preview 39 boundary update remains tracked through its existing process handle.

- [x] Enforce active T5 limits in surplus spending. Flooded Valley ABR showed Sub0 at 2-0-5 while the planner issued Sub1’s 2-0-5 purchase. Block duplicate tower/path T5 purchases; allow at most two Crossbow Masters only outside CHIMPS with enabled Master Double Cross. Original route actions unchanged; deployment pending.

- [x] Bound surplus waiting logs to round changes or changed cash after 15 seconds. Live Flooded Valley ABR logs showed income causing repeated messages every frame; purchases and failure messages remain immediate. Runtime deployment queued at a replay boundary.

- [x] Settings cleanup: remove repeated category labels, use Appearance and VM Connection cards, consolidate logs/reset into collapsed Troubleshooting, and explicitly describe queue reset. Preserve setup, theme and reset handlers. No replay interrupted.

- [x] Settings follow-up: remove duplicate introduction/category labels, shorten connection guidance and name the reset section directly. Keep setup/update/theme/reset IDs and working handlers; installation details remain collapsed.

- [x] Add executable `round N after S seconds` across parser, recorder, canonical action validation, strict JS validation and the non-blocking replay gate. Use the existing observed round-start timestamp, not per-action sleeps. Emergency wait release retains explicit offsets; overdue and mid-round resume cases log timing recovery. Nine offline timing/recording checks and eight converter checks pass. Two separate Everything Macro timing-preserved candidates pass both full Python parser and JS legality checks: Dark Castle Deflation and Tricky Tracks Impoppable. No original route replaced; live timing verification remains pending missing-medal gameplay.

- [x] Reproduce and fix false harmless classification of BloonsPlayer delays, life thresholds, speed/autostart and manual-round controls, plus Everything Macro round-relative delays. Preserve zero waits as no-ops. Add read-only `--audit-timing`: 891 files scanned, 48 legacy review candidates, four timing-preserved alternatives. Eight offline regressions pass. No original recordings regenerated. Faithful round-relative/manual-control execution remains unfinished.

- Confirmed Alpine Run CHIMPS at 23:33 on 5 October: live victory observed, Hard/Clicks=1050185 in the authoritative VM save, and controller logged `alpine_run - chimps clear confirmed`. Missing medal complete; never replay it. Stop-after-replay completed before the Preview 11 update began. Update finished at 23:34:37 without error; guest Settings and dropdown assets were checked. Missing-medal sweep resumed on One Two Tree Impoppable using its CHIMPS recording.

- [x] Audit source command semantics for BloonsPlayer, Everything Macro and Randy collection scripts. Nonzero waits/round offsets are preserved where supported; unsupported lives/manual-round/speed controls are explicitly lossy. Randy start sends Space twice; automatic finish is a literal no-input handler. Original recordings unchanged. Faithful manual-round conversion remains open below.

- [x] Bound Microsoft C++ runtime download and installation waits. Show byte progress; reject oversized, truncated and non-executable responses before launch. Keep a timed-out Windows runtime installer running and report its process rather than terminating system installation. Compiled offline payload/ownership guards and atomic-output regressions pass. A clean Windows install remains unverified.

- [x] Simplify Settings into appearance, VM setup, backups, and expandable profile/learning diagnostics; remove unused XP target and redundant status rows. Add shared searchable dropdowns, preserve live selected values without replacing focused menu rows, repair dark surfaces, and rebuild Boss Events as a clearly labelled preview. Browser checks confirmed theme changes, searchable map selection and keyboard selection without starting an owned medal. Installer/release preparation follows.

- [x] Gate support-tower coverage optimization behind experimental placement, excluding CHIMPS and changing-terrain maps. The offline regression reproduced repositioning with the experiment disabled; disabled/CHIMPS/dynamic cases now retain recorded positions. Failed-placement recovery remains available. Guest deployment pending.
- Preview 7 published and installed between replays at 23:07 on 5 October. Guest replay, placement detector and wait-runtime hashes matched source; missing-medal sweep resumed. The release contains earlier queued knowledge, route-wait, rate and installer fixes. GitHub Actions reported an outage; latest Pages deployment remained queued rather than a site build failure.


- [x] User art correction: remove generated banner PNG and references; compose README/Features from existing official BTD6 tower and map assets, retaining character proportions and attribution. Give Wiki an Engineer icon. Rebuild Subscriptions as a direct comparison with monthly/annual controls and Contributors as owner/community/help sections. Mobile checks pass at 390px; fix absolute table-caption overflow. No live replay interrupted.


- [x] Derive Master Double Cross only when a route needs two simultaneous Crossbow Masters. Gate that candidate on acquired and enabled knowledge, show the requirement in the app, and log absent/disabled/unknown knowledge. Selling/reusing a tower name no longer accumulates impossible tiers. Focused offline regressions pass; guest deployment remains queued between replays. Original recordings untouched.

- Website/README sidequest, 5 October: public page refresh completed locally with no gameplay input or controller reload. The missing-medal sweep stayed running. Actual screen-reader speech and final Pro entitlements remain distinct release checks; no checkout or production-1.0 claim added.


- Confirmed Polyphemus CHIMPS victory at 22:30:22 on 5 October, with Hard/Clicks=1050185 in the authoritative save. This missing medal is complete and must never be replayed. The queued installer through `b853fe0` finished afterward; the sweep resumed on Ancient Portal Hard. Later source changes remain queued for another batch.
- [x] Add four separate timing-preserved BTD6bot candidates: Castle Revenge, Enchanted Glade, Encrypted and Pat's Pond CHIMPS. Their executable actions match the older conversion after removing the newly preserved waits; no other loss is reported by the converter. Offline legality checks pass. New selective `--timing-candidates` mode never removes/replaces existing recordings, is idempotent and refuses to overwrite edited candidates. No victory or new map/mode coverage is claimed; gameplay remains limited to missing medals.

- [x] Tighten offline command legality: cap the knowledge-dependent Crossbow Master exception at two active towers and reject ordinary path-upgrade commands targeting heroes. Focused regressions pass; regenerated coverage remains 508 eligible map/mode pairs, 696 gaps. No route recordings were changed.
- Live observation at native 1920x1080 on 5 October: Polyphemus CHIMPS round 75 frame showed $14,396 and Glue Gunner 0-2-3, matching the reported state and panel reader. This checks one active replay frame, not all HUD layouts or 1440p. Screenshot remains private.

- [x] Prevent the Beginner Hard generator from using water-tower positions for its land-only build or recycling its own inferred guide coordinates. Candy Falls' Dart opener was at a Buccaneer position; moved only that opener to a normalized land Village position from the map's original ABR recording. Source provenance and hash updated. Three offline build/placement-selection regressions pass. This establishes a land-source coordinate, not range coverage or a guaranteed opening; guest deployment pending.

- [x] Close direct-file launch's validation bypass: previously a route filtered out of sweep candidates could still start without legality or account checks. Direct starts now validate the actual file against the requested mode and derive requirements from its commands. Regression reproduces an unplaced upgrade bypass and covers malformed commands, restricted towers and missing prerequisites. All 24 JavaScript test files pass. Batch guest deployment pending.

- [x] Restore the two missing middle-path Sniper upgrades in the Beginner Hard generator and its 26 guide-derived routes. The intended 0-2-4 build was incorrectly emitted as 0-0-4. Offline regression reproduced the omission; all 26 corrected routes pass build, legality and source-hash checks. Placement coordinates, round markers and original CHIMPS recordings are unchanged. This fixes the build mismatch, not a proof of victory. Batch guest deployment pending.
- Controller update completed between replays at 22:01 on 5 October. Guest process output showed fresh Electron processes and the stale Node controller was absent. Sweep resumed for missing Polyphemus CHIMPS; no validation-only replay was started.

### Medal sweep operating contract

- Gameplay earns missing medals only. An owned map/mode is never a validation target, including after an engine or route change.
- Keep development moving while a replay runs. Batch deployment at replay boundaries; interrupt a healthy replay only to prevent damage or corruption.
- Persist failed attempts across sweeps and continue with another eligible candidate or missing medal. A failed route must not block unrelated development.
- Generate and check candidate routes offline. Never launch BTD6 solely to validate them. Stop when every supported obtainable medal is earned; there is no later route-testing phase.
- Count a clear only with observed victory and authoritative saved-medal confirmation.

- [x] Add shared offline legality checks for multiple active heroes and duplicate active tier-five upgrades on the same tower/path. Selling releases the slot; different T5 paths remain legal. Preserve the knowledge-dependent Dart bottom-path exception outside CHIMPS. Focused tests pass; regenerated coverage remains 508 supported map/mode pairs and 696 gaps. No recordings were changed or games launched for validation.

- [x] Diagnose the stale guest controller: after the 21:46 update, Electron had restarted but the installed Node server PID 6916 still dated from 19:55. Installer now checks explicit idle state, stops only exact installed Node/Electron executable paths, and waits for exit before replacing files. Compiled pure guard checks pass; guest deployment and fresh-process verification remain pending.
- [x] Correct ordinary CHIMPS save mapping to Hard/Clicks in both app and backend. Moon Landing's CHIMPS victory at 21:45 saved Clicks=1050185 while SuperChimps remained 2. The generated BTD-Mod-Helper GameModeType enum lists Clicks as a real mode: https://raw.githubusercontent.com/gurrenm3/BTD-Mod-Helper/master/BloonsTD6%20Mod%20Helper/Api/Enums/GameModeType.cs . Paired tests cover unrelated difficulty placeholders and prevent SuperChimps overriding Clicks. Moon Landing CHIMPS is earned; never replay it.
- [x] Classify explicit startup/window and navigation failure signals before falling back to missing state evidence; offline tests preserve normal menu transitions as non-navigation events.

- [x] Stop treating the earliest retained observation as the opening round. Failure entries keep only the last 240 observations, so late defeats could be misclassified as instant failures and receive extra attempts. Classification now uses the mode's opening round; offline cases cover Hard, CHIMPS, Deflation, truncated tails and non-defeats. Deployment pending.

- [x] Persist pre-game technical failures before relaunch, skip or blocked returns. Window loss, spawn/stop failures, focus failures, pre-game crashes and map navigation errors previously bypassed the failure history. Offline branch tests confirm each is recorded once without recording owned-medal skips or consuming route attempts. Deployment pending.
- Offline gate on 5 October: all 20 existing JavaScript test files and 62 Python tests passed; local public-site HTML links and assets resolved. These do not establish clean-install readiness or prove route victories.

- [x] Require an explicit `running: false` response before remote VM updates. Previously malformed JSON or an empty status object could authorize installation while the actual replay state was unknown. Offline regression reproduces the bug and covers malformed, absent, active and idle responses. Batch deployment pending.

- [x] Extend the stationary-coordinate audit to One Two Tree: its Impoppable failure log moved heli0 `(972,94)` to `(784,97)` with nine feature matches. Allow its still-missing medals to use the corrected engine without deleting prior failure records. Other OCR/upgrade problems in that loss remain unresolved; this is not a victory claim. Offline checks now exercise the tracking branch for both stationary and moving-platform maps. Batch deployment pending.

- Latest operating rule: run only missing medals, never launch routes for validation, and stop when all supported obtainable medals are owned. Keep coding during replays and deploy batches only after a run finishes. Retain persistent failures and continue with other eligible candidates.

- [x] Identify the Polyphemus CHIMPS wrong-Heli cause: `TOWER_TRACK` rewrote heli1 `(904,506)` to `(899,284)` with eight feature matches, next to heli0 `(905,301)`. Restrict coordinate tracking to actual moving-platform maps rather than the broad dynamic-placement/access flag. Offline checks preserve stationary coordinates and unrelated route failure revisions. Original CHIMPS bytes unchanged; deployment queued, no victory claim.
- Guest batch through `f212998` installed at 21:20 on 5 October after Moon Landing Impoppable victory plus saved value `1050185`; sweep restarted successfully. No healthy replay was interrupted.

- [x] Scope saved medal modes to their actual difficulty in backend and app. A Moon Landing save exposed SuperChimps placeholders in Medium and Hard; a regression confirmed wrong-difficulty entries could overwrite earned state depending on object order. Both parsers now ignore those unrelated entries. Deployment queued.

- [x] Treat malformed explicit saved medal values as unknown, not unearned, consistently in UI and sweep. Skip unreadable modes within the current pass so other readable missing medals continue; unavailable profiles still wait without gameplay. Offline gate/parity checks pass. Pending deployment.

- [x] Use the existing read-only ownership probe before the cash gate on uncertain upgrade retries during an active run. Exact-intent mismatches now receive the same bounded queue recovery; missing intent still blocks retries. Thirty-six upgrade and ten resume checks pass, including a zero-cash already-owned target. Guest deployment queued; no live route launched for validation.

- [x] Harden game-state persistence with unique temporary files, serialized writes and cleanup after replacement/serialization failure. Three offline checks pass; transient Windows locks remain possible and no live resolution is claimed. Temporary files are excluded from Git/installers and rejected by the publication guard. Deployment queued.

- [x] Add two bounded selection retries when a readable upgrade panel contradicts the exact planned tier. Polyphemus CHIMPS round-98 defeat logs showed the second Heli reading the first Heli's 5-0-2 panel before its intended 2-0-5 purchase. Seventeen offline observation checks pass, including recovery and zero purchase input on persistent mismatch. This does not prove the underlying wrong-selection cause or a route win; deployment remains queued. Original CHIMPS recording unchanged.
- Latest guest batch through `7b3e721` deployed between runs on 5 October. Missing-medal sweep resumed after the Polyphemus CHIMPS loss; its failed candidate remains persisted and excluded. No owned medal was replayed for validation.

- [x] Allow delayed Profile.Save writes after observed sweep victories with a bounded twenty-second, read-only confirmation window. Offline checks pass; guest deployment queued. Save absence beyond the window still remains unconfirmed and needs investigation rather than a claimed clear.
- [x] Reject new route conversions that silently omit paid hero levels; four offline regressions pass. Original recordings remain unchanged.
- [x] Exclude nine existing converted recordings whose headers report dropped hero purchases using shared route validation. Offline coverage remains 508 map/mode pairs because alternatives exist. No recordings changed and no owned medals replayed. Deployment is queued for a later batch.
- [ ] Add faithful paid-hero-level support before restoring those incomplete converted candidates.
- [x] Refresh restored replay inputs from the current route; validate saved coordinates and retry counts. Ten focused recovery regressions pass; guest deployment and live resume validation remain open.
- [x] Keep mobile website navigation synchronized with desktop links, including Wiki and current-page highlighting.
- [x] Restore host/guest connectivity: reopening the desktop app started the existing VM, connected its app and completed setup without errors on 5 October. The sweep was idle afterward.
- [x] Fix subscription selector typography, selected-price contrast and keyboard focus; add a visible active-page indicator in mobile navigation.

- [x] Fix unreachable upgrade retry branch: unselected/unchanged observations now queue the same intended upgrade before dependent steps. Regression executes the actual replay reconciliation branch.
- [x] Validate this retry correction in the guest: Workshop Hard reached victory at round 80 and saved medal value 1049864. Its Heli retry confirmed 3-0-2 → 4-0-2 at round 55. This proves that recovery case, not every route.

## Queued production overhaul

Start only after the current repair work is complete, as requested on 5 October.

- Phase 1: authoritative save medals determine every gameplay target. Never run an owned medal for testing, benchmarking, changed routes or coverage. Recheck before navigation/start and reconcile after victory and restart.
- Stop the sweep when all supported obtainable medals are owned. No separate live route-testing phase. Generate and validate candidates offline; gameplay is exclusively for missing medals.
- Keep development moving while the medal sweep runs. Batch deployments between completed replays; never interrupt a healthy game for an update. Persist failures across sweeps and continue with other candidates or missing medals.
- Audit the existing architecture, regenerate coverage and retain structured historical failure evidence before extending it.
- Complete the map mechanics registry and have generation consume it; validate candidates offline before attempting their missing medals.
- Finish reliability, installer repair/resume, website and release gates from the supplied production specification. Publish v1.0.0 only when its acceptance conditions are actually met.

## Remaining current repair work

- [x] Fix surplus crosspath legality and cover it with offline regressions.
- [x] Separate interrupted/unconfirmed outcomes from observed defeats; reject stale map/mode/run evidence.
- [x] Replace cash digit-rewriting heuristics with a currency-free crop and alternate-mask recovery for invalid leading zeros.
- [x] Create a private backlog of 204 map/mode/route combinations covering 584 archived attempts.
- [x] Redo the linked README banner with original BTD6-inspired map and tower artwork.
- [ ] Deploy the local patches and validate cash at native 1080p and 1440p in the guest.
- [ ] Resolve ambiguous upgrades using observed panel tiers; do not claim the cash reader alone fixes missed purchases.
- [x] Implement ordinary-panel tier observation and bounded button retry with native-frame and offline regression evidence.
- [x] Verify the observer and 120 ms keyboard hold in a fresh VM replay; Workshop Hard victory and authoritative saved medal confirmed on 5 October.
- [ ] Keep unresolved upgrades explicit in resumable checkpoints, then validate recovery without buying a wrong tier.
  - Implemented: version-2 remaining-action snapshots; pending upgrades restored in original order; ownership probe before cash gating; owned targets removed without purchase input. Six recovery regressions pass. Live restart validation remains open.
- [ ] Review each backlog entry against its own evidence and confirm a subsequent victory plus saved medal.

## P0 — replay reliability

- [ ] Calibrate the hero picker at 1080p and 1440p. Verify displayed hero name and Select/Selected state. Current button OCR can return `unknown`; the runner now skips safely, but that still leaves modes unfinished.
- [ ] Confirm free and paid placements visually when cash is unchanged; handle free Dart Monkey knowledge and Deflation starting cash without endless retries.
- [ ] Confirm tower upgrades from the panel and tier state before advancing. Cash alone is ambiguous while bloons generate income. Retry only the same tier safely.
- [ ] Keep round OCR synchronized through tower panels, fast forward, effects and UI scaling. Check the new monotonic recovery against live 1080p/1440p runs and bound `await_round` stalls.
- [ ] Verify cash OCR with tower panels on either side and Double Cash active; reject sell-price and implausible-HUD reads.
- [ ] Never exit a viable game only because planned actions ended. Continue to actual victory or defeat, and claim a clear only after the medal is saved.
- [ ] Include game frame, action, target position, selected tower/hero, cash and round in failure evidence. Redact private profile data from shared logs.
- [ ] Add bounded recovery for placement, upgrade, navigation and stalled rounds. After a real defeat, try a different route candidate without replaying earned medals.
- [ ] Investigate known failures: Hedge CHIMPS round 6; Scrapyard CHIMPS round 42; Spa Pits ABR round 24; Spa Pits Deflation hero mismatch; Cubism upgrade and round ambiguity. Keep original CHIMPS routes intact.

## P1 — routes and sweep

- [x] Recover held placement ghosts despite rising cash. Downstream CHIMPS failure evidence showed an unplaced village ghost while round income bypassed retries. Two placement controls now override cash and visual-patch confirmation and enter existing bounded recovery. Offline recognition checks cover 1080p/1440p and missing controls; actual failed frame recognized. Guest deployment and live outcome remain pending. Original CHIMPS routes unchanged.


- [x] Add canonical `wait N seconds` route commands and preserve explicit BTD6bot waits during conversion. The replay keeps its screen loop running while the next action waits; Deflation cannot bypass the delay. Checkpoints retain an unchanged wait deadline, and edited waits restart with the current duration. Six focused timing/parser/resume/execution-gate tests pass. Manual round control, cursor aiming and recurring abilities remain separate unfinished cases; old recordings were not regenerated or live-tested.

- [x] Stop new BTD6bot conversions from labeling waits, manual round control and cursor movement as harmless omissions. Upstream `bot/commands/flow.py` explicitly uses waits to buffer commands and manual starts to spend round-end cash; cursor movement can aim towers. Offline regression reproduced six dropped-control cases. Zero-second waits remain no-ops. Existing recordings were not rewritten or newly verified.
- [ ] Add faithful timed-wait, manual-round and cursor-target support before restoring conversions that depend on them. Audit older `dropped (timing only)` headers against their source; they do not establish timing equivalence. Repeat-ability schedules and moved-tower coordinates also remain unsupported conversion cases.

- [ ] Check every route against mode restrictions, required paths, available hero, game version and map layout. Catalog presence alone does not prove victory.
- [ ] Build evidence-backed routes for missing maps/modes. Mark a converted route verified only after victory and saved medal are observed.
- [ ] Detect map mechanics including moving terrain, freezing, layout changes, obstacles and sightlines before placements or upgrades.
- [ ] Reconcile newly earned medals from the read-only profile after each run, skip saved medals, and resume partial sweeps after restarts.
- [ ] Record per-route success/failure history and exact skip reasons: locked upgrade, hero, map, restriction, or known failure.
- [ ] Confirm Expert-to-Beginner sweep and randomized order within categories without repeating excluded candidates.

## P1 — progress and diagnostics

- [x] Reset MM/hour and XP/hour samples when the save source changes or its clock moves backwards. Offline regression reproduced a false 1,497,000 MM/hour reading after switching accounts; source changes now show no rate until a fresh window exists, and clock recovery resumes normally. Source identity stays in memory only. Guest/app deployment pending.

- [x] Clear stale MM/hour and XP/hour values when samples expire or values are missing; compare veteran XP only within the same veteran rank. Focused regressions pass. Live multi-run rate validation remains below.

- [ ] Check MM/hour and XP/hour against several live VM save updates, rank changes and spending; display no rate until enough samples exist.
- [ ] Confirm level, veteran rank, Monkey Money, hero ownership, Monkey Knowledge, tower XP and T1–T5 unlocks from the VM save with source and freshness.
- [ ] Reconcile achievement progress with Steam unlock state and clearly label unsupported progress.
- [ ] Fix activity ages and victory/defeat counters; require victory plus saved medal before adding a clear.
  - Fixed future-clock activity anchors resetting as host time caught up; added numeric-string timestamp normalization and unknown-date handling. Offline tests cover ISO, Unix seconds/milliseconds, numeric strings and short/long clock skew. Counter/end-to-end host refresh checks remain outstanding.
  - Fixed the sweep counter counting raw victory screens before save confirmation. Regression covers stale screens, repeated result lines, consecutive confirmed wins and immediate defeats without double counting. Guest deployment and UI refresh verification remain queued.
- [ ] Keep redacted full logs and group route failures by actionable cause, even if an old game-state file survives.
- [ ] Keep host UI and guest controller connected after VM updates/restarts; expose the specific failing step.

## P2 — installer and distribution

- [x] Preserve the last usable installer when a rebuild fails. Final EXE assembly now writes and flushes a unique temporary file before atomic replacement, with partial-file cleanup. Offline tests reproduced the old empty-output failure and cover copy errors, locked replacement and exact payload/footer bytes. No installer was executed by these tests.

- [x] Remove HTTP 416 size-only promotion of partial downloads. A rejected range now requests the full file; a failed fresh request preserves the partial. Offline coverage includes a same-size stale file above the old 10 MiB threshold. Live clean-install verification remains open.

- [x] Make the missing-Steam installer download atomic and reusable only with a matching completed-download receipt. Six offline checks cover truncated/changed/legacy caches, HTML error responses and network interruption. Existing Steam still bypasses installation; clean-machine verification remains open.
- [x] Fix resumed-download completion checks: validate Content-Range start/end/full size and chunk length, retain valid incomplete ranges, and discard bytes outside the advertised range. Offline stream tests reproduce the formerly truncated "complete" installer and cover valid full resumes and servers ignoring Range. Clean-install/live-download verification still outstanding.
- [x] Encode guest PowerShell commands without shell quote interpolation; retain stdout/stderr diagnostics and exit codes, bound ordinary SSH calls to 60 seconds and allow Steam installation 10 minutes. Seven mocked transport checks and a read-only command in the existing VM pass. This does not prove clean-install readiness or repair rejected keys automatically.
- [ ] Validate a clean Windows install without Python, Visual C++ runtime, App Sandbox or VM; show progress and repair action per prerequisite.
- [ ] Verify Steam sign-in, BTD6 install/launch, SSH provisioning, port bridge and guest app update without storing Steam credentials.
- [ ] Test partial-install repair and reuse healthy components without changing existing Steam or game data.
- [ ] Publish the next installer with release notes, verification limits and a working site download. Do not add a separate SHA256SUMS.txt asset (user removed that requirement).
- [ ] Add trusted code signing when available; unsigned installers may show SmartScreen warnings.

## P2 — product and site

- [x] Stop hidden reading-progress work for reduced-motion and background pages; coalesce scroll/resize frames and cancel pending work on preference changes. Offline lifecycle regression passes; local subscriptions page loads with the progress marker and no console errors. Actual screen-reader speech and browser reduced-motion emulation remain unverified.

- [ ] Finish Subscriptions accessibility checks in reduced-motion mode and with a screen reader. Verified monthly/annual switching by pointer and keyboard at desktop and 390px mobile widths, light/dark theme switching and no mobile horizontal overflow on 5 October. Prices on the site are planned at $5.99/month or $49.99/year for 31 October 2026; checkout and entitlements do not exist yet. Added a polite, atomic price announcement; actual screen-reader speech still needs verification.
- [x] Tie Features, About, Wiki, Contributors and Subscriptions to BTD6 with varied actual tower artwork, named map thumbnails and independent-project attribution. Finish the compact Discord card, setup FAQ, static mobile links, sharing metadata, sitemap and latest published preview installer lookup. Local link audit and release-lookup regressions pass; mobile layout and pricing keyboard checks pass.
- [ ] Make app category switching, scrolling and the VM viewer responsive without polling viewer frames when its tab is closed.
  - Viewer lifecycle regressions confirm no requests while unfocused, category-hidden or browser-hidden, one in-flight capture, abort on blur, and no timer after page suspension. Fixed resume after browser Back/Forward cache restoration and released revoked image references. Actual browser cache restoration and broader scrolling performance still need verification; guest deployment queued.
- [ ] Tidy repo folders without blindly moving runtime data. Exclude personal saves, logs, keys, VM images and private Discord bot source.
- [x] Replace the README banner with official Wizard, Ninja, Engineer and Super Monkey artwork, linked to the website. No generated artwork or map thumbnails; preserve proportions and attribution. Clarify preview status, installation and planned Pro additions.

## Later — experimental systems

- [ ] Test autonomous strategy/placement assistance behind experimental settings, with redacted gameplay observations and route-level evidence before live decisions.
- [ ] Add boss events only after modifiers, restrictions, version compatibility and executable routes have victory checks.
- [ ] Finalize Pro features and entitlements before launch. The current examples are ideas, not shipped features.

## Completed in this pass

- [x] Refuse to start a route when the hero picker cannot confirm the required hero.
- [x] Verify live hero Select/Selected state at 1920×1080 and recover stale portrait indices by scanning displayed hero names.
- [x] Detect left tower panels across cyan and purple portrait cards without treating Glacial Trail's ice as a panel.
- [x] Read shifted cash with a left tower panel and Double Cash active; reject the repeated `$1,300` → `51,300` glyph artifact.
- [x] Keep a replay alive after its planned actions end; Tricky Tracks Hard reached round 80, showed victory, saved the medal, and was skipped afterward.
- [x] Execute canonical route ability actions instead of dropping them as unsupported.
- [x] Relay pause, stop, and stop-after controls directly to the guest across transient status-probe disconnects.
- [x] Recover round OCR from bounded monotonic full-HUD readings; observed `27/80` resynchronization in a live replay.
- [x] Classify new hero-picker failures as navigation bugs instead of gameplay defeats.
- [x] Add failure-category counts to the app diagnostics summary.

## Release and site refresh (2026-10-04)

- [x] Replace the README banner with a richer Bloons+ map and balloon composition.
- [x] Replace lifetime pricing with a monthly/annual subscription switch.
- [x] Make the download page resolve the newest published GitHub installer automatically, with a local metadata fallback.
- [x] Add more map environments and expand the public feature list.
- [x] Stop Glacial Trail emergency spending from pulling recorded actions into freeze windows.
- [x] Check Glacial Trail upgrade deferral offline: seven cycle, gating, checkpoint and actual retry-branch checks pass, plus 10 resume and 18 timing checks. Predict availability only with confirmed placement history and an unavailable exact-tier observation; live frozen-tower recognition remains unfinished.
- [ ] Observe Glacial Trail deferral only in a replay for a missing medal; never launch an owned mode to validate it.

## Settings cleanup (2026-10-05)

- [x] Remove the inert remember-queue toggle; queue persistence continues automatically.
- [x] Keep Appearance and VM actions visible; fold optional ISO, installation checks and backups away.
- [x] Move profile, hotkey, Monkey Knowledge and passive-learning readouts to Run logs.
- [x] Apply imported/reset themes immediately and clarify reset scope.

## Upgrade input safety (2026-10-05)

- [x] Reproduce unavailable-button hotkey fallback offline and prevent purchase input when the button is unavailable.
- [x] Retain exact-tier recovery, already-owned reconciliation and one visually justified button retry; log the unavailable reason.
- [x] Confirm One Two Tree Impoppable: victory summary and authoritative Hard.Impoppable medal value 1050191. Never replay this earned medal.
- [x] Deploy accumulated patches through Preview 19 at the replay boundary; guest controller reload verified and missing-medal sweep resumed.

## Ability timing (2026-10-06)

- [x] Move ability timer waits into the non-blocking execution gate and preserve deadlines across round transitions and unchanged checkpoint restores.
- [x] Verify 14 timing, 10 resume and eight converter checks offline; preserve original recordings.
- [x] Replace cursor-target waits with non-blocking scheduled continuation; keep move-only semantics and avoid repeated key input.
- [ ] Observe timed abilities only during gameplay for a missing medal; offline checks do not establish victory.

- Preview 16: 18 timing and 10 resume checks pass. Matching delayed cursor intent survives resume; actual gameplay verification awaits a missing-medal recording that uses cursor targeting.

## Import preservation (2026-10-06)

- [x] Reproduce full-import deletion of a repaired generator-tagged recording in a temporary fixture, then remove blanket regeneration/deletion. Existing bodies are deduplicated and changed candidates use separate names.
- [x] Reject validation output outside the newly created batch before cleanup. Nine importer checks pass; the full importer was not run on the real route library.

- Refreshed offline reports on 6 October: 893 recordings, 48 legacy timing review candidates; 508 of 1,204 map/mode pairs have eligible candidates across 86 maps, with 696 gaps and six maps lacking eligible routes. Coverage is not victory evidence.

## Source control semantics (2026-10-06)

- [x] Inspect Randy autoplayV2.py and play_collection_event.py at pinned commit 7c36862ffec1d64bb95ddabecf20c73cb54046fd without executing source. Start sends Space twice, automatic finish returns without input, Sanctuary uses manual controls and remains excluded.
- [x] Classify omitted explicit start/speed as lossy rather than a no-op; ten converter regressions pass. Existing legacy recordings still require review; classification is not faithful conversion or a route win.

## Status polling payload (2026-10-06)

- [x] Trace host UI polling payload: historical lastRun and route attempts account for roughly 330 KB per response. Add opt-in UI projection; preserve full API/history and all 2,000 log lines.
- [x] Verify pure projection and actual server handler offline. Current sample: 562,687 → 231,888 bytes (59% reduction); no claim of measured scroll latency or timeout recovery.
- [x] Verify UI projection on reloaded host and guest after One Two Tree CHIMPS finished. Both omit unused history and retain logs; host reports fresh VM status for the new replay.

## Confirmed replay boundary (2026-10-06)

- [x] One Two Tree CHIMPS: victory summary observed, authoritative Hard.Clicks value 1050185, controller logged clear confirmed. Never replay this earned medal.
- [x] Stop-after ended the sweep before another replay. Guest update through Preview 19 started only after running=false was confirmed.
- [x] Update completed without error; guest serves new app code and UI status view. Resume selected missing Skulltweak CHIMPS (save Clicks=1233), while earned One Two Tree CHIMPS remains Clicks=1050185.

- Host app reloaded only after setup job completion. Fresh host status: running=true, vm=true, statusStale=false, compact payload 135,519 bytes with 1,277 current log lines; independent guest replay continued at round 10 without fatal error. This proves status synchronization/API deployment, not visual layout or a Skulltweak victory.

## Settings polish (2026-10-06)

- [x] Replace the two-option theme dropdown with accessible Light/Dark preview cards. Keep selection synchronized after import and reset.
- [x] Separate reset from backup actions, shorten VM setup copy and remove the repeated Settings heading. Optional installation checks and ISO input remain collapsed.
- [x] JavaScript syntax and diff whitespace checked; dark layout inspected in the host browser. No replay was interrupted or started for this change.

## VM timestamp ages (2026-10-06)

- [x] Confirm nine-hour VM/host skew using live readAt and host UTC, without changing OS clocks.
- [x] Add a source-clock timestamp to guest status; relays retain it and stale responses cannot recalibrate it.
- [x] Calculate activity ages, run duration, profile freshness and result freshness against the source clock. Unknown time stays unknown instead of treating historical future-dated events as newly observed.
- [x] JavaScript syntax and whitespace checked. Native theme selection and status projection preserved.
- [ ] Confirm displayed ages and run time after deploying both host and guest at a healthy replay boundary.

## Pending healthy boundary (2026-10-06)

- Preview 21 is published and its installer includes Preview 20 Settings plus clock-aware activity. Guest/host reload is pending until Skulltweak CHIMPS finishes. Stop-after is confirmed enabled; resume the missing-medal sweep after successful deployment.
- Live Skulltweak CHIMPS upgrade evidence: heli1 at round 57 first read 3-0-2 with button unavailable. Existing exact-tier retry reselected, then confirmed 4-0-2 through panel pips at 00:34:02 in replay logs. This was recovered, not a permanently failed upgrade or evidence of freezing. No route or CHIMPS recording was edited.

## Glacial Trail upgrade availability (2026-10-06)

- [x] Research per-tower freeze cycle from https://bloons.fandom.com/wiki/Glacial_Trail : two frozen rounds every ten, relative to placement. Update map guidance to distinguish per-tower cycles from a global storm timer.
- [x] When a confirmed placement history predicts frozen rounds and the exact requested upgrade is visibly unavailable, retain its target ahead of dependent actions until predicted thaw. Then reselect and re-read tiers before any purchase. Other maps retain the bounded retry policy; unknown histories do not invent thaw times.
- [x] Persist the deferral in unresolved upgrade checkpoints and gate ownership probes without blocking screenshot/round processing. Original recordings unchanged.
- [x] Seven focused availability checks, 10 resume checks and 18 timing checks pass. This is prediction plus live availability reconciliation, not a visual freeze classifier or victory proof.

## Recovered upgrade failure reporting (2026-10-06)

- [x] Reproduce classification of a later defeat as upgrade-unconfirmed solely because a recovered retry warning remained in its log.
- [x] Reconcile same-run ambiguous upgrade events against later panel-tier-confirmed purchases on the same tower/path and target tier. Preserve unknown targets, later failures, cross-tower/path isolation and sold/replaced instances. Keep the legacy log fallback when evidence is absent.
- [x] Save exact planned upgrade targets in new action events and expose unresolved count in failure reports. Existing persistent history is not rewritten.
- [x] Focused failure-classification checks pass; Python action-ledger file compiles. Deployment is queued after the current replay.

- Closest upgrade gates: updated the offline branch fixture with the new scheduling dependencies; all eight upgrade-queue and 19 upgrade-observation checks pass. The initial fixture failure was missing injected helpers, not a live replay exception.

- Skulltweak CHIMPS earned: replay observed VICTORY_SUMMARY at 00:46:50 with VICTORY_CONFIRMED, and authoritative Hard.Clicks is 1050185. Never replay this medal. Waiting for the confirmed stop-after boundary before deploying Preview 23.

## Preview 23 deployment boundary (2026-10-06)

- [x] Skulltweak CHIMPS exit=0, controller clear confirmed, saved Hard.Clicks=1050185. Stop-after ended before another replay.
- [x] Guest Preview 23 update completed without error. Guest status now includes sourceNow; clock-aware app code is served. Host Electron reloaded only after the setup job finished.
- [x] Host UI visibly shows historical ages (Skulltweak 1–2 minutes, One Two Tree CHIMPS 27–28 minutes), a sane new run duration, and the correct new map. Missing-medal sweep resumed on Winter Park Hard; Skulltweak CHIMPS remains earned.
- [x] Follow-up UI evidence found Winter Park navigation displaying the previous Skulltweak checkpoint's 61/61 steps. Scope checkpoint progress and result badges to the current map/mode; syntax check passes. This small follow-up is pending the next healthy deployment boundary.

## Settings organization and dropdown focus (2026-10-06)

- [x] Move detected heroes, hotkeys and Monkey Knowledge from Run logs to Settings. Keep experimental observations in diagnostics.
- [x] Hide completed/inapplicable setup actions; distinguish local mode from missing VM setup. Add an accessible setup progress bar to Settings using existing job/check data.
- [x] Make profile readouts use theme colors and remove obsolete hidden hero-checklist styling.
- [x] Preserve dropdown focus when live options change; Home/End from the trigger focus the first/last enabled option.
- [x] JavaScript syntax and whitespace checked; dark Settings inspected in the host browser. Active Winter Park Hard replay remained running. Guest deployment queued at a healthy replay boundary.

## Save XP and public shared scripts (2026-10-06)

- [x] Calculate normal per-level progress from cumulative save XP with rank/threshold consistency guards. Share the existing level table with the scanner; reject missing/malformed/mismatched data.
- [x] Keep ordinary cumulative XP rate samples across rank-up while isolating profile switches and unconfirmed veteran rollover semantics.
- [x] Correct the overview counter to Upgrades unlocked; it counts acquired upgrade IDs, not towers awaiting XP.
- [x] Repair public loading of map guidance and issue-report redaction by moving browser-safe implementations into assets and retaining server require wrappers. Keep lib blocked by the static privacy guard.
- [x] Check all normal rank boundaries, cap threshold 180M, malformed save fields, rank-up rate and profile switch. Host visibly shows 493,535 XP remaining and issue-report dialog opens without publishing data.
- [ ] Confirm veteran XP remainder/rollover semantics against authoritative live data before displaying veteran ETA.

## Preview 26 healthy update boundary

- Winter Park Hard earned: replay observed VICTORY_SUMMARY; controller logged clear confirmed; authoritative WinterPark.difficult.Hard.modes.Standard=1049864. Never replay this medal. Stop-after ended before the next replay; guest update started only after running=false.

- [x] Preview 26 guest update completed; host reloaded after the update job ended. Guest served the new player XP module; authoritative guest status confirms the missing-medal sweep running again.

## Settings polish follow-up (2026-10-06)

- [x] Compact theme previews, consolidate advanced VM setup, hide VM-only advanced options in local mode, and clearly separate automatic profile diagnostics from preferences.
- [x] Improve dark surface/text contrast, align Boss preview cards, and retain explicit Coming soon status.
- [x] Correct label focus for enhanced selects, empty/disabled options feedback, small viewport menu height and removed-control cleanup.
- [x] Syntax/whitespace checks and host dark Settings/Boss visual review; End focuses Hard and Escape closes without selecting or launching gameplay.
- [ ] Deploy this UI batch to the VM after the active healthy replay ends; do not interrupt it.

## Save refresh ordering (2026-10-06)

- [x] Coalesce concurrent save reads from the five-second progress poll and ten-second save poll. Resolve the latest completed request after slow catalog/scanner requests so old profiles cannot roll back unlocks or reset hourly-rate samples.
- [x] Offline deferred-response checks prove request sharing, stale-consumer replacement, genuine backward-clock preservation, newer VM-unavailable precedence, and recovery after malformed JSON. Existing profile-rate regressions pass.
- [ ] Deploy with the pending Settings batch after the active healthy replay; check rates over a live sampling window. No new clear claimed; active run observed at round 45.

- Host browser follow-up: live save reads updated XP remaining to 385,105; after the minimum sampling window, XP/hr and MM/hr showed 0 for an unchanged save balance instead of remaining unknown. Positive multi-run rates and spending semantics are still unverified.

## Settings cleanup (2026-10-06)

- [x] Keep appearance and game connection as the primary settings. Remove legacy preference backup import/export controls and their handlers; keep reset behind a disclosure and confirmation.
- [x] Move automatically detected profile details to Run Logs; keep heroes, hotkeys and Monkey Knowledge live and read-only.
- [x] Hide the ISO override once setup has an ISO or an existing VM, and do not submit hidden stale paths. Show a working/error badge before a previously ready setup status.
- [x] Review dark Settings and installed-VM diagnostics in the host preview; the existing VM shows its checks without an ISO input. Active replay left untouched.
- [x] Settings batch deployed in Preview 30 at the confirmed Scrapyard replay boundary; guest serves the simplified Settings.

## Repeated abilities and candidate fidelity (2026-10-06)

- [x] Inspect BloonsPlayer's actual repeat/stop implementation. Unlike its README, repeats persist across rounds until cancelled; stopping a slot removes one occurrence. Source: src/player.py TAS_repeat_ability, TAS_stop_ability, TAS_stop_all_abilities, timer_hit.
- [x] Add canonical repeat/stop commands, parser and recorder roundtrip, contract validation, main-loop scheduler, current-hotkey checkpoint restore and ability-slot event logging. Keep input serialized; do not send during route actions, pending cursor targeting, held placements, speed toggles, pause or uncertain play-state reads.
- [x] Preserve BloonsPlayer numeric-key zero as slot 10 and seconds waits. Reject unmapped or malformed keys.
- [x] Add three separately named source candidates (Dark Dungeons Easy, Glacial Trail Easy, Muddy Puddles Hard). Both Python and JS route validators pass. No original recording overwritten and no validation-only game launched. No candidate victory claimed.
- [x] Eight scheduler/importer/runtime checks, 18 timing checks and four paid-hero rejection checks pass; syntax and publication guard pass.
- [x] Scrapyard CHIMPS earned: observed VICTORY_SUMMARY, controller clear confirmed, authoritative Scrapyard.difficult.Hard.modes.Clicks=1050185. Stop-after boundary confirmed running=false. Never replay this owned medal.
- [x] Preview 30 guest update completed without error at the confirmed Scrapyard boundary. Guest serves new Settings and all three ability-preserved candidates. Exact host Electron owner reloaded only while guest idle; authoritative guest status confirms missing-medal sweep running again.
- [x] Repeated abilities observed naturally during Dark Dungeons Easy at rounds 3–5 and 13; no validation-only replay launched.

- Pinned upstream revision 17d624879c5ad777e82594da34450e66b2d60756 confirms duplicate-entry repeat lists, per-slot cancellation and the one-second cycle. Six existing JS route-validation/failure gates also pass.
- New sweep naturally selected Dark Dungeons Easy for a missing medal using its ability-preserved source candidate; hero-picker logs show Etienne correctly read as Select. No validation-only run launched. Live repeating-input behavior and outcome remain to be observed.

## Covering hero/tower panel selection (2026-10-06)

- [x] Live Dark Dungeons Easy frame shows Etienne's right panel covering dart0 at native (1424,331). Repeated unchanged selections produced unselected upgrade observations.
- [x] Shared selection closes a detected covering panel with two centre clicks before the tower click, including retries and selling. Independent HUD anchors detect hero panels without tier pips. Preserve ordinary uncovered selection.
- [x] Captured-frame offline probe records two centre clicks followed by the intended tower; uncovered target records only the tower click. Three scale/ownership checks, 19 upgrade-observation and eight upgrade-queue checks pass. No test input sent to the game.
- [x] Live repeat scheduler observed naturally during Dark Dungeons missing-medal run at rounds 3,4,5; no exception observed in those logs. No victory claimed for that candidate yet.
- [x] Preview 31 installed after Dark Dungeons Easy finished and running=false was confirmed; update completed without error and authoritative guest status confirms the missing-medal sweep resumed. Live recovery by the new selection helper remains to be observed naturally.

- Dark Dungeons Easy clear recorded by the controller at 01:50; authoritative VM save independently reports DarkDungeons.difficult.Easy.modes.Standard=1049224. The controller requires observed victory plus saved medal before reporting a clear. This owned medal must never be replayed. Added a developer reference for timing, repeating abilities, checkpoints and panel selection.

## Ability binding prerequisites (2026-10-06)

- [x] Trace the gap: route ranking checked tower keys but ignored ability slots; helper.py replaces ability defaults whenever saved gameplay controls exist, so a missing key can remove a strategy's intended input.
- [x] Extract only issued one-shot/repeating slots, check saved bindings against the replay's supported key names, and count unavailable slots in candidate readiness. Cancellation and unused slots do not block. Empty/absent gameplay sections preserve replay defaults.
- [x] Identify required slots in sweep skip and direct-run diagnostics; subtract binding failures from the missing-upgrade count.
- [x] Focused command, slot 10, binding, defaults and alternative checks pass, as does the adjacent knowledge gate. No game or save file changed, no original recording modified.
- [x] Preview 32 published with the reviewed-source installer; publication guard reports no findings.
- [x] Preview 32 update completed after Spa Pits Deflation finished; guest running=false was confirmed before installing. Authoritative guest status confirms sweep resumed on missing Cubism Primary Only. No healthy replay interrupted and no validation-only replay.

- Spa Pits Deflation earned: VICTORY_CONFIRMED at round 60 (02:01:11), followed by victory screen; authoritative VM save SpaPits.difficult.Easy.modes.Deflation=1049545. Never replay this owned medal.

## Manual round-control source audit (2026-10-06)

- [x] Read pinned BloonsPlayer implementation including argument parsing, opening autostart preference, Space toggles and pause-setting controls. Add read-only inventory with source line numbers, conversion status and remaining omissions; three focused parser/semantics checks pass.
- [x] Audit 83 source scripts: 12 affected, 11 lossy conversions and one rejected race. Six have only a round-start omission. Preserve all recordings and keep these incomplete conversions excluded.
- [x] Implement observed round-start control with input ownership and checkpoint acknowledgement before restoring the six candidates. Explicit autostart and relative speed controls require further work; do not treat an automatic Space press as equivalent.

## Inferred source wait correction (2026-10-06)

- [x] Wider timing gate exposed two obsolete expectations. Pinned source implements TAS_delay but no wait handler; source scripts nevertheless use wait. Preserve supported delay and label nonzero wait interpretation for strategy review rather than claiming complete conversion.
- [x] Retain the Glacial Trail Easy candidate body with a review header/lossy filename. Mark its stale installed name lossy because installer updates preserve recordings. Original CHIMPS recordings unchanged.
- [x] Updated audit: 83 source files, 15 affected (14 lossy, one rejected), including six unregistered wait operations. Eleven importer, four audit, eight repeated-ability and ability-binding checks pass. Two complete repeating-ability candidates remain; no recordings regenerated or gameplay launched for validation.
- [x] Preview 33 published; packaged controller matches reviewed source and publication guard reports no findings.
- [x] Preview 33 update completed at the Cubism Primary Only terminal boundary; explicit guest idle preceded installation and authoritative guest confirms the resumed missing-medal sweep. No healthy run interrupted.
- [ ] Review intended Glacial Trail freezing/timing before restoring a complete candidate.

- Refreshed offline coverage after the source review: 86 catalog maps, 509 of 1,204 map/mode pairs covered, 695 gaps and five maps with no route. These are route-catalog counts, not victory proof. Remaining coverage is substantial; V1.0 is not complete.

- Cubism Primary Only earned: VICTORY_CONFIRMED at round 40 (02:09:55); authoritative VM save Cubism.difficult.Easy.modes.PrimaryOnly=1049225. Never replay this owned medal. Preview 33 updater finished and confirmed resumed sweep at 02:11.

## Observed startup control (2026-10-06)

- [x] Add start round fast/slow parser, recorder, action contract and legality support. Gate on confident play-state observation; persist intent before input, avoid competing automatic controls, and consume only after requested speed is observed.
- [x] Restore validated pending metadata with fresh source bindings; reject malformed deadlines and rebase a future clock without issuing input. Hold on failed checkpoint writes. Required Play/Fast Forward bindings are checked before launch.
- [x] Six offline state/input/recording/integration checks, 18 timing checks, eight repeat checks and 12 importer checks pass. Adjacent JS syntax/knowledge/binding gates pass. The captured-source startup behavior is adapted to observation rather than claimed literal timing equivalence.
- [x] Create six separately named observed-start candidates using source placements/upgrades: Balance CHIMPS, Quarry CHIMPS, Dark Castle Deflation, #Ouch Hard, Ravine Hard and Workshop Hard. Python parser and strict JS legality pass for all six. No original recording overwritten, no validation-only gameplay and no new candidate victory claim.
- [x] Preview 34 published and boundary updater completed successfully after Cubism Double HP MOABs; authoritative guest confirms the missing-medal sweep resumed. Observe the new control only when a missing medal naturally selects it.
- [ ] Explicit autostart settings, relative speed changes, multiple manual round starts and paid hero levels remain incomplete. Coverage remains 509/1,204 pairs (695 gaps); additional candidates improve alternatives but do not prove wins or resolve all coverage.

## Settings refinement (2026-10-06)

- [x] Group appearance and game connection into responsive cards; shorten labels, move connection refresh below installation details, and consolidate reset under Advanced. Keep existing setup, update, theme and reset element IDs and handlers.
- [x] Inspect Settings at desktop width in Light and Dark and at 390px in Light. Responsive cards and controls fit; actual screen-reader speech remains unverified.

- [x] Close the round-start pending-checkpoint window with strict action/index/speed validation; current source bindings still replace saved bindings. Eleven focused resume checks and six round-start checks pass.

- Cubism Magic Monkeys Only earned: VICTORY_CONFIRMED at round 80 (02:28:02), controller clear confirmation, and authoritative VM save Cubism.difficult.Hard.modes.MagicOnly=1049871. Never replay this owned medal. Preview 34 published and its boundary updater is live; deployment remains pending until Double HP MOABs ends.

## Tower and upgrade control prerequisites (2026-10-06)

- [x] Trace the unbound-path fallback in applyGameHotkeys: nonempty saved tower controls retained default path keys when a saved path was missing or unsupported.
- [x] Replace that fallback with None, preserving defaults only for absent/empty saved sections. Gate required placement/hero/path controls using the replay key whitelist; unused paths do not block.
- [x] Seven focused Python control checks and JS readiness checks pass; no recording or game/save file changed.
- [x] Publish Preview 35 and deploy after a healthy replay boundary. The active Cubism Double HP MOABs replay remains untouched.

- Preview 34 reached the terminal Cubism Double HP MOABs boundary at 02:46:17. Guest idle was confirmed before the updater began; source/API reconciliation continues after controller replacement. No healthy replay interrupted.

- Cubism Double HP MOABs earned: VICTORY_CONFIRMED at round 80 (02:45:58), controller clear confirmation, and authoritative VM save Cubism.difficult.Hard.modes.DoubleMoabHealth=1049865. Never replay this owned medal. Preview 34 update finished and resumed the missing-medal sweep without interrupting that replay.

- [x] Investigate Preview 34 immediate pass end: read-only candidate ranking found false missing Cold Snap and Bionic Boomerang names despite Metal Freeze and Bionc Boomerang in Profile.Save. UI already had scoped aliases; sweep did not.
- [x] Share one save-upgrade resolver between UI and backend, including qualified Buccaneer names. Actual Quad ABR and Infernal Hard candidates now rank missing=0/unknown=0 against the same save. Genuine missing tiers still block; no attempt history or game/save file changed.
- [x] Log missing upgrade names/path/tiers and mark incomplete passes distinctly from complete. Offline checks cover stopped, incomplete, unknown medal records and complete endings.

- Preview 35 published and guest update completed while idle on 6 October. Missing-medal sweep restarted on Quad Alternate Bloons Rounds with zero missing/unknown upgrade prerequisites; this confirms route selection now passes, not a victory. Existing saved medals and failure history remain intact.

- [x] Resolve save-name parity for TownCentre/Town Center and ThreeMinesAround/Three Mines 'Round using one exact browser/backend normalizer. A read-only current-VM check finds both records. Owned, missing and unknown medal tests plus sweep-pool checks pass. Ignore legacy OCR fragments absent from the navigation catalog without deleting saved configuration. Guest deployment pending.
- [x] Diagnose live Quad ABR cash stall: screenshot at round 16 showed $5,512 and 28 lives, while replay cash was 28. The alternate Sauda panel missed portrait-colour detection; the currency anchor scored .800 at the shifted HUD versus .144 at the normal HUD and was rejected by the .82 threshold. Accept >=.78 only with stronger >=.35 separation. Captured frame now resolves shifted HUD; 20 upgrade/HUD observation tests and panel-transition regression pass. New live cash reading remains pending a missing-medal replay after deployment; no strategy victory claimed.
- [x] Repair corrupted arrow/dash/bullet symbols in controller log messages. No route commands or original recordings modified.

- Preview 36 published on 6 October. Stop-after-replay is confirmed true in the guest; the current Tricky Tracks Medium replay remains running. Update/resume is queued at its terminal boundary.
- Offline follow-up on the recorded Quad JPEG: at a reconstructed 1920x1080 frame, the unchanged model reads 28 from the wrong HUD crop and 5512 from the shifted crop, matching the captured cash display. The raw 960px viewer image is too degraded for reliable direct digit OCR; do not claim native-frame accuracy from it.
- [x] Repair stale regression harnesses: normalize CRLF before extracting functions, allow PROJECT_ROOT declarations after imports in relocation checks, and test the actual live-source clock helpers instead of the removed activityTimestamp helper. All JavaScript test files and five HUD/placement regressions pass. This confirms the tested mechanisms, not every replay outcome.

## Relative speed controls (2026-10-06)

- [x] Add `change speed` grammar across parser, recorder, canonical action contract, legality validation, converter and required Play/Fast Forward preflight. Choose an absolute target from the observed initial state, serialize input, persist intent and await later-frame confirmation. A replay resume restores that same target with current bindings; it does not blindly toggle again.
- [x] Block automatic play/speed adjustment while an explicit control is unresolved, including a slow round start. Five relative-control checks, seven startup checks, eleven resume checks and fourteen importer checks pass.
- [x] Preserve two source-specific candidates separately: Monkey Meadow Deflation and Quad Hard. Full Python parser and strict JavaScript legality pass. Generator repeat/overwrite checks preserve original recordings and reject modified generated candidates. No candidate victory claimed; no owned medal launched for validation.
- [ ] Deploy relative speed support after the current Preview 36 update/resume batch. Explicit autostart, multiple manual starts and paid hero levels remain unfinished.

- [x] Finish Settings cleanup with a labelled page, distinct Appearance / Connection / Maintenance sections, a direct diagnostics link and main-PC update guidance. Keep setup actions and optional ISO details; automatic profile detection remains in diagnostics. No manual hero/XP/medal configuration added.
- Confirmed Tricky Tracks Medium on 6 October at 03:12:53: victory at round 60 and authoritative Medium/Standard=1049544. Preview 36 installed at the replay boundary; guest confirmed the missing-medal sweep resumed. Never replay this earned medal.

- Preview 37 published on 6 October with observed speed controls and Settings cleanup. Installer payload matches the current Settings and replay source byte-for-byte; publication guard reports no findings. VM deployment is queued for the next replay boundary.

### Explicit source cursor targets — 6 October

- [x] Preserve BTD6bot move_cursor as a move-only command with normalized source coordinates, full route grammar, recording, canonical action and serialized replay execution. Reject malformed, boolean and outside-playfield source coordinates.
- [x] Add one separate #Ouch Alternate Bloons Rounds cursor-preserved candidate. All 103 commands pass the complete Python parser and JS mode/legality validation. Original recordings unchanged; no victory claimed. Four offline cursor checks and 14 importer checks pass.
- [ ] Deploy cursor support in the next batch after Preview 37; observe it only during missing-medal gameplay. Manual rounds, autostart, positional special actions and source Sniper path regression remain unresolved conversion cases.

- Preview 38 published on 6 October from an isolated build directory, preserving the already queued Preview 37 installer. Packaged runtime files match source; publication guard reports no findings. Cursor support still awaits its own replay-boundary deployment.

### Automatic play input ownership — 6 October

- [x] Reproduce automatic Play/Fast Forward admission on a frame already used for a route action. Hold automatic toggles while a route action, held placement or prior toggle owns that frame. Seven round-control, five relative-speed and four cursor offline checks pass after the formerly failing regression. This addresses a real control race, not proof of all historical defeat causes.
- Confirmed Glacial Trail Primary Only at 03:26:49 on 6 October: observed victory at round 40 plus authoritative Easy/PrimaryOnly=1049225. Never replay the earned medal.
- Preview 37 installer completed at the replay boundary and the guest confirmed the resumed missing-medal sweep. Cursor support and the new input gate are queued together for the next batch.

- Preview 39 published on 6 October; its installer packages both cursor support and automatic input ownership. Packaged runtime matches source byte-for-byte. Boundary updater is live, waiting on the active replay with stop-after confirmed; no healthy run was interrupted. Guest deployment remains pending until that job completes.

### Signed Monkey Money rate — 6 October

- [x] Reproduce spending being clamped to zero in MM/hour. Preserve signed saved-balance changes, reject negative saved totals, and avoid negative-zero display. Label the statistic Net MM/hr with a spending/sampling explanation; document it in the account-progress wiki. Existing freshness, clock/source isolation and veteran-counter regressions pass alongside the new spending checks. Live sampling remains a separate check; no invented gross farming income is reported.

- Preview 40 published on 6 October from a separate build directory; the queued Preview 39 VM installer remains untouched. Packaged UI/replay matches source and publication guard reports no findings. Two authoritative VM save reads 59.788 seconds apart showed unchanged totals, consistent with zero XP/hr and Net MM/hr. Nonzero live gains and spending remain unverified.

### Advisory hero-picker layout memory — 6 October

- [x] Keep visually discovered page/card positions in the existing private last-hero.json after selection confirmation. Scope hints to exact resolution and slot geometry; require live title verification before reuse and fall back to a reset/full search on mismatch. Selection/ownership checks remain live.
- [x] Treat malformed non-object hero memory as empty and atomically replace the local hint file. No game saves or new public profile data are written. Five offline tests cover corrupt caches, changed layouts, invalid hints, confirmed persistence and wrong-hint fallback.
- [ ] Observe reduced picker searches during missing-medal gameplay after deployment. Current source OCR aliases and 1440p calibration still require live coverage.

- Preview 41 published on 6 October from a separate build directory. Packaged hero runtime matches source; private last-hero.json is excluded. The existing Preview 39 boundary updater remains live, waiting on Flooded Valley ABR (observed round 64, 12 lives); no clear or defeat is yet claimed for that replay. Hero hint and net-rate deployment remain pending a later batch.

### Positive evidence for ambiguous placements — 6 October

- [x] Require a newly selected 0-0-0 upgrade panel before confirming ordinary towers from visual changes when free placement or income masks cash. Clear an old panel first; send no purchase input. Missing or unchanged panels remain unverified and do not teach terrain refusals or trigger blind duplicate free placements. Heroes retain their separate observer.
- [x] Offline observations cover stale panels, fresh base panels, upgraded existing towers, missing frames and held placements. This proves panel observation behavior, not tower identity or a winning Infernal strategy.
- [ ] Deploy this observer at a healthy replay boundary after Preview 58. Continue only missing-medal gameplay; retain the Infernal ABR round-24 defeat in persistent failures.

### Authoritative medal display precedence — 6 October

- [x] Reproduce an older visual scan overwriting explicit missing CHIMPS/Impoppable medals from a fresh save when map keys differ in case or alias spelling. This is a synthetic regression, not a claim about the current account's Skulltweak medals.
- [x] Merge scan records first and authoritative save records last; order save records by localSaveReadAt. Invalid timestamps cannot give a scan priority over a save. Preserve exact alias normalization and missing/unknown distinctions.
- [x] Focused browser-helper regressions, map-save alias checks, sweep medal admission and JS syntax pass. Original recordings and game saves are unchanged.

- Confirmed Infernal Reverse on 6 October: replay reached VICTORY at 05:50:25 and the controller logged clear confirmed; the authoritative VM save subsequently returned Medium/Reverse=1049545. Never replay this earned medal. Preview 58 deployed at that boundary and the guest confirmed the missing-medal sweep resumed. Preview 60 is queued for its next replay boundary.

### Lightweight failure-log browsing — 6 October

- [x] Separate the failure index from full run evidence. The logs page requests a compact response without per-run fullLog, log, action, screenshot or observation arrays; the default diagnostics endpoint retains full evidence for explicit downloads.
- [x] Forward compact requests through the VM bridge and project responses from older guests too. Download fetches complete recent-run logs on demand with a longer bridge timeout; errors do not silently export the index as if it were full evidence.
- [x] Offline checks prove summary fields/counts remain, full-export contents remain unchanged, stored evidence is not mutated, and the synthetic large-log response shrinks by more than 50x. Live transfer/render measurement remains pending deployment.
- Measured against the live VM history: 614 total failures, 150 recent entries, 23,821,866-byte full response versus 89,893-byte compact projection (~265x smaller). Full logs remained present in the original response. This is a real data-volume measurement; browser rendering performance still awaits deployment.

### Glacial Trail Hard failure evidence — 6 October

- Persisted gameplay defeat at round 23 (2026-10-06T12:56:00.629Z), using the separate spike-target-preserved CHIMPS conversion as a Hard fallback. Druid 0-1-0 was panel-confirmed at round 22; its next upgrade was unselected shortly before DEFEAT. Hero was placed at round 3, unlike the source CHIMPS start. These observations warrant a freeze/timing audit; they do not establish freezing as the sole cause or justify blind changes to original CHIMPS recordings.
- Preview 60 applied after that replay ended; guest confirmed the resumed missing-medal sweep. Preview 61 is published and its boundary worker is live. Full failure evidence remains private under dist.

### Dedicated route priority — 6 October

- [x] Correct candidate ordering that placed recorded/converted CHIMPS reuse ahead of converted target-mode plans. Keep exact target-mode local wins first; otherwise prefer dedicated recordings, dedicated conversions and dedicated guides before CHIMPS/Hard fallbacks.
- [x] Glacial Trail Hard source plan preserves temporary Engineer/Dart opening and Sauda placement at round 6. The failed CHIMPS fallback placed Sauda at round 3. Do not claim this ordering change alone proves the round-23 loss is fixed; source placement timing is mechanically significant, but the unselected Druid upgrade still needs observation.
- [x] Focused ordering, fallback and authoritative medal gates pass. Actual available-combos enumeration now lists the dedicated Glacial Trail Hard route first. Original recordings and route hashes are unchanged; failed candidates remain persistently recorded.
- [ ] Deploy with the next boundary batch; continue only missing-medal gameplay. No validation-only games or earned-medal reruns.

- Dedicated Glacial Trail Hard replay subsequently reached round 34; Druid tiers 0-1-0, 0-2-0 and 0-3-0 were live panel-confirmed, passing the earlier round-23 failure point. This is progress evidence, not a claimed clear. Preview 62 is published; Preview 61's boundary worker still owns the reserved root payload, so Preview 62 remains isolated pending that deployment.

### Shared medal decoding — 6 October

- [x] Consolidate duplicated browser/server medal rules into one browser-safe data/catalogs/medal-progress.js contract. Preserve public Node export and UI wrapper, exact difficulty/mode mapping, Clicks vs SuperChimps, empirical completion threshold and null unknown values. No schema or saved-data change.
- [x] Run the same authoritative admission/alias tests before and after extraction. Shared-decoder coverage checks all 14 supported modes across 14 value schemas, browser/server parity and unchanged input records. Script-load order is checked before app initialization.
- [ ] Deploy with the next boundary batch. This removes one source of UI/sweep divergence; it does not prove every save field or route is correct.
