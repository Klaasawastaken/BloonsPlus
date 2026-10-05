# Bloons+ roadmap and repair list

Updated 5 October 2026. Checkboxes require evidence, not merely code. Preserve original CHIMPS recordings and BTD6 saves. Gameplay stays behind simulated input.

## Current repair pass

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
- [ ] Apply this batch to the guest at the next healthy replay boundary.
