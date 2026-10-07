## Preview 99 package cleanup — 7 October 2026

### Additions

- Add the v1.2 roadmap for Quests, Races, Boss Rush and Boss Events after the required 1.0 work, including a future Quests Coming soon tab.
- Add staging and publication checks for local transfer manifests.

### Changes

- Match private installer filenames regardless of letter case.
- Use the real boot identity consistently in the isolated prelaunch interruption fixture; production ownership behavior is unchanged.
- Record the remaining pinned-source command and upgrade-semantic gaps without modifying original recordings.

### Removed

- Exclude the unnecessary local file-transfer manifest from newly built installers.

## Preview 99 Monkey Knowledge activation hotfix — 7 October 2026

### Additions

- Read per-point disabled knowledge from each user's save and show active/inactive purchased nodes.
- Add synthetic decoder, route, free-placement flag and app-label checks without personal stats.

### Changes

- Distinguish owned knowledge from active knowledge for route eligibility and free Dart/Glue assumptions.
- Preserve legacy saves and unknown malformed data. Game/save files remain read-only.

### Removed

- Remove the assumption that global enablement activates every owned knowledge point.

## Preview 99 installer recovery and hero picker hotfix — 7 October 2026

### Additions

- Add a small native dependency observer that survives the installer window closing and records when its exact process group has finished.
- Add real process-interruption checks and hero-picker regressions for colored backgrounds, title colors and Select/Selected labels.

### Changes

- Allow setup recovery after the observed dependency group becomes empty. This confirms that work stopped, not that installation succeeded; normal dependency checks still run.
- Read hero selection from the button letters instead of treating green scenery as a Select or Selected button.
- Include magenta hero-title artwork in the existing OCR candidates and isolate the white Select letters from the button border.
- Keep Psi recognition marked unresolved: the captured Obyn and Ezili repairs do not prove every hero can be selected.
- Keep unknown process ownership blocked if the observer itself is lost. Clean Windows, reboot and physical accessibility acceptance remain open; this is still Preview 99.

### Removed

- Remove selection claims based solely on green-pixel density.
- Remove the permanent unknown state after an interrupted installer's retained observer confirms that its dependency group ended.

## Preview 99 VM build diagnostics hotfix — 7 October 2026

### Additions

- Add exact-VM, fresh-log setup diagnostics with stale/unrelated/replaced-log regressions.

### Changes

- Preserve observed `bcdboot` error codes and stop repeating full Windows image builds after a confirmed boot-file failure.
- Verify 407 Python tests and 65 approved JavaScript check files. Two actual clean-environment attempts failed before Bloons+ ran; the underlying App Sandbox boot-store issue remains open.

### Removed

- Remove the generic vanished-VM error for this confirmed setup failure.

## Preview 99 installer diagnostics hotfix — 7 October 2026

### Additions

- Add compiled native structured-field and truncated-credential export checks and an aggregate failure-evidence audit.

### Changes

- Redact quoted credentials and account/session identifiers while preserving safe run context in the tested formats.
- Keep remaining app-log and structured failure-evidence gaps explicit; production acceptance remains incomplete.

### Removed

- Remove native shared-details leaks caused by quoted fields, escaped quotes and incomplete strings.

## Preview 99 installer progress hotfix — 7 October 2026

### Additions

- Add actual native/Node setup protocol acceptance and persisted milestone regressions.

### Changes

- Retain completed work across component rechecks and resume without inferring current-stage progress or readiness.
- Verify 400 Python tests and 65 approved JavaScript check files. Production clean-machine, physical reboot and accessibility gates remain open.

### Removed

- Remove recovery progress resets within the same setup operation.

## Preview 99 installer text scaling hotfix — 7 October 2026

### Additions

- Add actual native text-layout checks across both themes, four text sizes, default/minimum windows and six setup states.

### Changes

- Size the footer and action buttons to their content and wrap the installation note within the window.
- Verify 397 Python tests and 64 approved JavaScript check files. Actual Windows DPI/text scaling, screen-reader and clean-machine acceptance remain open.

### Removed

- Remove fixed footer heights that clipped enlarged text.

## Preview 99 installer accessibility hotfix — 7 October 2026

### Additions

- Add checks against actual WinForms accessibility objects and status-change events in the isolated native installer view.

### Changes

- Expose current friendly status and measured or unknown progress without repeating status announcements for progress-only updates.
- Verify 396 Python tests and 64 JavaScript check files. Physical screen-reader and clean-machine acceptance remain open.

### Removed

- Remove the accessible status name that concealed the current installer observation.

## Preview 99 second special hotfix — 6 October 2026

### Additions

- Add a complete, separate Firing Range CHIMPS candidate and offline second-special regressions.

### Changes

- Preserve second-special source inputs, saved keyboard bindings, independent targets/selectors and checkpoint intent.
- Enforce binding prerequisites during direct starts and distinguish ordinary keys from keypad shortcuts in recording.
- Keep original CHIMPS recordings and healthy missing-medal replays intact; live target behavior remains unverified.

### Removed

- Remove second-special omissions and duplicate recorder actions from the supported conversion path.

## Preview 99 achievement source hotfix — 6 October 2026

### Additions

- Add production endpoint and UI regressions for achievement cache source labels and older guest compatibility.

### Changes

- Distinguish guest-local cache, successful VM relay and genuine host fallback without changing completion values.
- Verify 387 Python checks and 64 JavaScript check files; activation remains batched between replays.

### Removed

- Remove the incorrect PC cache label for VM achievement data.

## Preview 99 Chutes placement hotfix — 6 October 2026

### Additions

- Add a production launch-policy regression for fixed Chutes terrain, other guarded maps and moving platforms.

### Changes

- Restore bounded visual placement retries on Chutes without changing recordings or alternating-lane coverage.
- Verify 387 Python checks and 63 JavaScript check files; live placement success and full production acceptance remain open.

### Removed

- Remove Chutes' incorrect changing-terrain classification.

## Preview 99 Steam readiness hotfix — 6 October 2026

### Additions

- Add nine offline guest Steam handoff and freshness checks.

### Changes

- Read the existing guest detector before and after provisioning; retain official Steam actions only for observed missing requirements.
- Reopen stopped Steam from fresh evidence, preserve unavailable status and avoid distracting healthy existing installations.
- Verify all 387 Python tests and 62 JavaScript check files; broader production acceptance remains open.

### Removed

- Remove unconditional BTD6 install prompts and misleading sign-in instructions after VM app updates.

## Preview 99 package identity hotfix — 6 October 2026

### Additions

- Add explicit stable/preview release identity input to the installer builder and offline staging/native label checks.

### Changes

- Stamp staged app, lock metadata and inventory consistently; preserve source metadata and dependency versions.
- Reject invalid build identities before replacing staging and retain development-build defaults.
- Verify 378 Python tests and 62 JavaScript check files; full production acceptance remains open.

### Removed

- Remove fixed development-version labels from explicitly tagged packages.

## Preview 99 setup status hotfix — 6 October 2026

### Additions

- Add offline setup attempt and active ownership regressions.

### Changes

- Scope step attempts to independent setup or VM update operations; preserve genuine retries and active ownership.
- Verify 62 JavaScript check files and all 373 Python tests. Keep clean-machine and physical accessibility acceptance open.

### Removed

- Remove misleading retry state inherited from earlier successful operations.

## Preview 99 HUD hotfix — 6 October 2026

### Additions

- Add eight offline finished-route HUD and input ownership checks.

### Changes

- Recover an observed blocking overlay after route actions finish, using fresh frames and existing safe clicks.
- Capture again before the second click; preserve pending controls and reject stale-frame automatic input.
- Verify all 373 Python tests and the private observed failure fixture. Live recovery remains unverified.

### Removed

- Remove the next-action dependency that prevented completed routes from reaching HUD recovery.

## Preview 99 hotfix — 6 October 2026

### Additions

- Add scale, negative and cancellation-order checks for Magic Monkeys Only placement.

### Changes

- Recognize purple shop cards alongside cyan while retaining the close-anchor and two-row gate.
- Verify the actual private failure frame, nine focused checks and all 365 Python tests.
- Keep live recovery and full production acceptance open; retain original recordings and persistent failure history.

### Removed

- Remove the cyan-only placement assumption in restricted Magic tower shops.

## Preview 99 — 6 October 2026

### Additions

- Add separate complete source candidates for Last Resort and Erosion CHIMPS.
- Preserve Spike Factory Tier 5, reverse targeting and supported Set clicks with saved bindings.
- Preflight targeting/special controls and cover selection, scaling, recording and resume offline.

### Changes

- Guard automatic Play and nested tower commands against unbound inputs.
- Retain unresolved upgrade counts across replaced tower instances.
- Improve dark requirement contrast and prepare installer selection for the v1.0.0 milestone.
- Verify 362 Python tests, 61 JavaScript check files and ten setup-transport tests.
- Verify the 235.4 MiB installer, all packaged runtime comparisons, inventory hashes and application icons. Retain clean-machine and live acceptance gates.

### Removed

- Remove incomplete forward-only Spike targeting conversion and white dark-mode requirement surfaces.

## Preview 98 — 6 October 2026

### Additions

- Preserve exact hero-picker failure frames, OCR inputs and freshness in local diagnostics.
- Check disabled fieldsets and stale dropdown rows in an isolated actual renderer.

### Changes

- Keep opening strategy defeats consumed; reserve bounded retries for evidenced placement/OCR failures.
- Honor inherited native disablement and refresh custom menus when fieldsets change.
- Preserve failure screenshot paths containing spaces; reject malformed hero OCR states.
- Keep recognition and production acceptance gates open until their required live evidence exists.
- Verify 350 Python checks, ten setup-transport checks and 61 JavaScript check files.

### Removed

- Remove dropdown selection through a stale menu after the native field or option becomes unavailable.

## Preview 97 — 6 October 2026

### Additions

- Add persistent package journals and recovery after installer process exits.
- Block packaged controller startup until interrupted app files are repaired.

### Changes

- Recover before retained-data restoration; preserve outside edits and resume partial rollback safely.
- Keep committed packages through cleanup interruptions; verify final hashes and reject unsafe recovery paths and linked destinations.
- Set milestone 100 to the full v1.0.0 release and standardize future notes to Additions, Changes and Removed.
- Verify 346 Python checks, ten SSH checks and 58 JavaScript files; retain physical power-loss and clean-machine production gates.

### Removed

- Replace the in-memory-only rollback and untracked sibling temporary files with persistent recovery.

## Preview 95 — 6 October 2026

- Preserve positional moved-tower selectors and keyword upgrade/target arguments in BTD6bot route imports.
- Reject unknown, duplicate, excess and partial coordinate arguments before changing selection state; leave existing recordings intact.
- Distinguish a missing setup API, HTTP failure, incompatible protocol, malformed response and unreachable controller in startup details.
- Explain that an older running controller should be reopened after the healthy replay finishes. Do not report that a working VM is offline or bypass setup ownership checks.
- Refresh the readable V1.0 checklist and release evidence. Clean-machine, UAC/reboot, physical accessibility and live recovery acceptance remain open.

## Preview 94 — 6 October 2026

- Fix false “older installer” rejection in VM provisioning after adding the app icon.
- Scan bounded native capability metadata before the appended package and enforce the check before publishing a new installer artifact.
- Preserve structured VM component errors in the native checkpoint, log and visible details; retain the failed phase for recovery.
- Keep active replays untouched when applying the host setup compatibility repair.

## Preview 93 — Post-install configuration

- Add a branded, compact post-install welcome with three observed stages, proportional official artwork and expandable checks/options.
- Preserve existing shared setup commands, restart confirmation and recovery. Navigation remains available while setup is incomplete.
- Remove the Skip intro button; preserve automatic dismissal and startup preferences.
- Verify actual light/dark/compact renders, reduced motion and progress semantics. Isolated timing supports the animation target; physical hardware acceptance remains open.

## Preview 92 — Legacy controller compatibility and community standards

- Recover native setup from an older controller's HTTP 404 using a separate authenticated, ownership-verified setup listener.
- Reconnect Resume to the same verified controller without replacing an older active listener.
- Add contributor/support/security policies, issue forms, a PR checklist and the official PolyForm Noncommercial 1.0.0 first-party license.
- Verify both EXEs contain all seven app-icon frames. Retain third-party terms.

## Preview 91 — Native setup and app startup

### A clearer install and first launch

- Compact native Windows installer with a single primary action and optional location, shortcut, launch and VM choices.
- Inspect an existing installation and offer Launch, Update or Repair. Preserve modified app data and routes during repair or selective uninstall.
- Retain installation ownership, dependency process-tree receipts and atomic app-file replacements across interruptions.
- Show measured download/copy progress when available, saved restart choices and friendly recovery details with explicit redacted Copy/Export.
- Share authenticated setup sessions between the native installer, first launch and Settings. Pause queued work without stopping a replay.
- Keep setup inline when a VM is absent. Updates wait for a fresh idle replay boundary.
- Add Full, Reduced and Off intro settings. Escape/Skip dismiss branding while service failures retain Retry/details.
- Preserve host acceleration and the guest's lighter rendering path. Use a stable themed window and bounded startup/recovery retries.

### Recovery fixes

- Resume an actively cancelled setup after its observed safe boundary.
- Save the boot identity before marking a remote restart requirement.
- Preserve Update intent through native handoff and Resume instead of accepting the old guest version as ready.
- Use the actual native observer constructor during read-only SSH recovery.
- Restore Continue after a previously healthy VM loses its connection.
- Serve the app shell while setup-only ownership persists; ordinary gameplay APIs and timers remain disabled there.
- Fix early status polling before its initialization guard.

### Verified scope

332 Python checks, ten SSH transport checks and 56 JavaScript check files pass. Actual native controls and the app renderer were inspected in isolated hidden windows. Package/source integrity and privacy guards are checked before publication.

This is a preview, not production 1.0 certification. Clean Windows setup, real UAC/reboot, Steam/2FA, physical DPI/screen readers and weak-hardware acceptance remain open. No game/save files or original CHIMPS recordings were changed. Healthy gameplay was not interrupted to apply the batch.

Unsigned previews may still show Windows SmartScreen. No certificate or security bypass is bundled.

## Preview 89 — Validated setup states and remote updates

- Show explicit VM setup states, including readiness checks, retries, restart requirements and failed steps.
- Validate each finished action before advancing; stop an unready step instead of reinstalling it in a loop.
- Keep Steam sign-in as a user step and verify app reconnection before reporting a VM update complete.
- Add light/dark state styling, setup-state documentation and flow/reconnection regressions.
- Verification: 301 Python checks, ten setup transport checks and 50 JavaScript check files. Clean/interrupted setup acceptance remains open.

## Preview 88 — Published VM installer and Python reuse

- Prefer the published preview installer in developer checkouts instead of an older generic build.
- Reject incomplete named artifacts, preserve standard/installed layouts and keep launch actions independent of installer lookup.
- Accept a healthy private Python environment before checking temporary package-install disk space; check space before repair mutations.
- Verification: 301 Python checks, ten setup-transport checks and 49 JavaScript check files. Clean-machine and interrupted-install acceptance remain open.

## Preview 87 — Installer steps and less background rendering

- Show named installation steps, measured file/download progress and a working indicator for tasks without a measurable percentage.
- Preserve the failed step and stop treating package output as 98% complete.
- Reuse healthy private Python environments without requiring an old receipt; retain version, dependency and import checks.
- Defer hidden app card lists and retain unchanged map cards while keeping overview/navigation counters live.
- Verification: 297 Python checks, ten setup-transport checks and focused UI/site checks. Clean-machine acceptance remains open.

## Preview 86 — Manual round recovery and character artwork

- Confirm a completed manual round when the paused HUD retains the same round number; do not repeat an issued Play input.
- Add bounded paused-income recovery while preserving queued purchases and saved Play receipts.
- Stage VM installers in unique app folders and verify size and SHA-256 before launch.
- Rebuild Features and simplify Home while retaining its app-preview hero and floating card.
- Add four BTD6 heroes and seven more monkey types; keep Ninja Monkey consistent in Discord banners and Engineer on the wiki.
- Refresh the README banner with existing game artwork and preserve natural character proportions.
- Verification: 295 replay checks, 10 VM setup checks, site behavior/layout checks and 27 exact payload comparisons. Publication guard reports zero findings. Live recovery and clean-machine acceptance remain open.

## Preview 77 — Pause evidence and simpler Settings

- Require full pause-menu labels before replay recovery sends Esc.
- Read Auto Start from its actual lime rail and cyan knob; leave ambiguous switch states unknown.
- Remove the queue-clearing preference reset and refresh setup status on Settings visits.
- Keep manual-round route support in development; no unsupported route admission or original recording edits.

## Preview 76 — Counter structure and Engineer targeting

- Validate round counter structure and selected-mode totals in normal and fallback OCR reads.
- Reject impossible/padded counters before they advance route actions.
- Preserve source Engineer standard targeting and moved selectors during conversion.
- Keep unrelated manual-round and Ace-centering omissions excluded; original recordings remain unchanged.

## Preview 75 — Relevant settings and manual-round safety

- Hide VM update controls before installation and unusable setup buttons during reboot-only steps.
- Preserve setup retries, advanced ISO override and support actions.
- Reject legacy conversions declaring omitted autostart/end-round controls; original recordings remain unchanged.
- Offline eligibility: 516/1,204 targets, 688 gaps. No new winning-route claim.

## Preview 51 — Same-tower placement fallback

- Read route coordinates as unverified hints for the same map and tower.
- Try bounded hints after local placement recovery fails, requiring positive live preview evidence.
- Keep CHIMPS and changing terrain on their existing recovery path.
- Allow one targeted fresh attempt for failed non-CHIMPS Infernal Heli routes; owned medals remain skipped.

## Preview 50 — Placement evidence and changing surfaces

- Keep placement memory separate for each tower and hero footprint.
- Stop seeding confirmed legal spots from merely planned actions in winning routes.
- Preserve legacy memory without using broad terrain-only buckets for tower decisions.
- Ignore phase-stale illegal-spot caches on changing maps; live confirmation still applies.
- Preserve older refusal observations without using another run's occupied layout as a permanent terrain ban.

## Preview 49 — One medal-completion workflow

- Remove the separate live route-verification run type and one-attempt-per-map branch.
- Keep the missing-medal sweep working through remaining eligible modes.
- Simplify the UI sweep status to match the completion workflow.

## Preview 48 — Replay binding validation and medal-first cleanup

- Reject unsupported saved modifiers instead of sending the bare upgrade key.
- Handle malformed saved binding objects without crashing startup.
- Align route readiness with keyboard/modifier support in the replay runner.
- Remove the obsolete achievement sweep backend that could replay owned modes.
- Show current replay victories and defeats instead of its stale recording count.

## Preview 47 — Settings connection cleanup

- Show Game Connection inside the guest and keep VM setup guidance on the main PC.
- Disable installation/update buttons while the controller reconnects.
- Label preference and queue reset consistently.

## Preview 46 — VM setup concurrency and repair state

- Share concurrent VM update requests with the existing setup job.
- Hold queued gameplay starts while setup/update runs.
- Preserve previous setup state when a write or replacement fails.

## Preview 45 — Held shop placement recovery

- Recognize ordinary shop-based placement when the nudge cancel button is absent.
- Cancel held placement before selecting an existing tower.
- Keep blocked tower actions queued until a fresh frame permits selection.

## Preview 44 — Checkpoint recovery validation

- Refuse malformed unresolved-upgrade collections and action metadata cleanly.
- Reject boolean offsets and duplicated recorded queue positions.
- Refresh route coverage and gap reports without launching validation games.

## Preview 43 — Owned upgrade limits for surplus spending

- Derive optional upgrade caps from the read-only profile at replay launch.
- Share upgrade-name aliases with preflight, including renamed and prefixed save names.
- Reject malformed snapshots without changing recorded route actions.

## Preview 42 — Settings and surplus upgrade limits

- Simplify Settings and consolidate troubleshooting controls.
- Enforce active tier-five limits before surplus upgrade purchases.
- Rate-limit income-driven upgrade waiting logs.

## Preview 41 — Verified hero-picker hints

- Remember visually confirmed card locations as resolution/layout-scoped hints.
- Verify hinted cards live and fall back to the full search on mismatch.
- Reject corrupt cache shapes and atomically save local selection memory.

## Preview 40 — Honest net Monkey Money rates

- Preserve negative balance changes instead of clamping spending to zero.
- Label Net MM/hr and explain the sampling/spending behavior in the app and wiki.
- Reject invalid negative save balances and suppress negative-zero display.

## Preview 39 — Serialize automatic play input

- Hold automatic Play/Fast Forward when the current screenshot predates an issued route action.
- Respect held placements and already-issued play input before toggling again.
- Preserve normal idle-frame controls and original recordings.

## Preview 38 — Preserve explicit cursor targets

- Add move-only route targets to parser, recorder, action ledger and replay.
- Preserve a separate #Ouch ABR candidate without changing original recordings.
- Reject malformed cursor arguments and retain unsupported-source restrictions.

## Preview 37 — Recorded speed controls and clearer Settings

- Preserve relative speed commands with observed state, serialized input and checkpoint-safe resume.
- Add two separate speed-preserved source candidates without replacing original recordings.
- Group Settings into appearance, connection and maintenance with direct diagnostics access.

## Preview 36 — Cash HUD and saved map identities

- Recognize the shifted cash HUD behind alternate hero panels.
- Share exact Town Centre and Three Mines Around save aliases between sweep and UI.
- Exclude orphaned legacy scan identifiers from the map pool.

## Preview 35 — Required tower and upgrade controls

- Check saved placement keys for required towers and heroes before starting a route.
- Check only the upgrade paths needed by each candidate, with explicit readiness reasons.
- Remove guessed default upgrade keys when the save marks a path unbound or unsupported.

- Share qualified and renamed save-upgrade identifiers between UI and sweep to remove false locked-tier skips.
- Name missing tiers in logs and report passes with remaining medals as incomplete.

## Preview 34 — Observe recorded round starts

- Add observed startup commands with input ownership, pre-input checkpoints and fresh-binding resume.
- Keep automatic round input from competing with pending startup; confirm speed before advancing.
- Add six source-position startup adaptations and check their required play binding.

- Admit narrowly validated pending round-start checkpoints on resume, keeping pending purchases refused.
- Simplify Settings cards and clarify required path tiers.

## Preview 33 — Review inferred source waits

- Preserve supported BloonsPlayer delays while flagging unregistered wait interpretations.
- Mark the affected Glacial Trail candidate for review, including its stale installed filename.
- Extend read-only source audits and correct the timing regression checks.

## Preview 32 — Check required ability bindings

- Extract one-shot and repeating ability slots from recorded routes.
- Check saved bindings against replay-supported keys before starting a strategy.
- Explain unavailable slots in sweep and direct-run diagnostics; continue with compatible alternatives.

## Preview 31 — Select towers behind covering panels

- Close detected covering hero/tower panels with two centre clicks before selection.
- Apply the same selection behavior to upgrade retries, targeting and selling.
- Reproduce the live covering-panel failure offline and retain existing upgrade gates.

## Preview 30 — Preserve repeating ability controls

- Add main-loop repeat/stop commands and current-hotkey checkpoint restoration.
- Serialize ability input with placement and targeting; avoid pause catch-up bursts.
- Preserve BloonsPlayer zero-key ability and seconds waits; add three offline-checked source candidates.
- Record ability slots and recurring use in the action ledger. Original CHIMPS recordings remain unchanged.

## Preview 29 — Simpler Settings

- Focus preferences on appearance and game connection; remove legacy backup controls.
- Keep detected profile diagnostics under Run Logs.
- Hide unnecessary ISO overrides and correct setup/update status badges.

## Preview 28 — Keep live save refreshes in order

- Share concurrent save reads between progress pollers.
- Prevent delayed consumers from reapplying older profiles or hiding newer VM-unavailable state.
- Preserve real clock corrections and retry after failed reads.

## Preview 27 — Compact Settings and themed controls

- Compact Appearance and keep automatic game-profile diagnostics separate from preferences.
- Consolidate advanced VM setup and hide irrelevant controls in local mode.
- Improve dark surfaces and Boss Events preview cards.
- Repair dropdown label focus, disabled-choice feedback and small-window sizing.

## Preview 26 — Save XP and shared browser scripts

- Read ordinary level progress from cumulative save XP and retain XP-rate samples through rank-up.
- Label the acquired-upgrade count correctly.
- Restore public map guidance and local log-redaction scripts without exposing server modules.

## Preview 25 — Clearer Settings and dropdown navigation

- Group detected game controls with Settings rather than run diagnostics.
- Hide completed setup actions, show local mode correctly, and display setup progress in Settings.
- Match profile readouts to the selected theme; preserve keyboard focus during dropdown updates and implement Home/End navigation.
- Keep active replays running while UI changes are prepared.

## Preview 24 — Scope live progress to the current run

- Show checkpoint steps only when its map and mode match the current replay.
- Keep a fresh previous victory from appearing as the result of a different active map/mode.
- Fix observed Winter Park navigation showing the completed Skulltweak checkpoint's 61/61 steps.
- JavaScript syntax and whitespace checks pass; guest deployment will be batched after a healthy replay.

## Preview 23 — Distinguish recovered upgrade retries

- Do not classify a later defeat as an unresolved upgrade failure when same-run panel-tier evidence proves recovery.
- Preserve uncertainty for unknown targets, reused tower instances and mismatched paths or insufficient tiers.
- Retain exact planned targets in action events and expose the unresolved count in failure reports.
- Keep prior history unchanged and retain legacy fallback when evidence is missing.

## Preview 22 — Retain upgrades through Glacial Trail thaw

- Predict per-tower thaw from confirmed placement history only after an unavailable exact-tier upgrade observation.
- Keep that planned tier ahead of dependent actions and re-read ownership at thaw; do not spam unavailable purchase buttons.
- Preserve deferred upgrades in resumable checkpoints and keep the main observation loop running.
- Seven availability, 10 resume and 18 timing checks pass. Live frozen-tower recognition and victory evidence remain pending.

## Preview 21 — VM clock-aware activity

- Retain the guest clock through status relays and ignore stale samples when calculating clock offset.
- Correct activity ages, run duration, profile freshness and result freshness when host and VM clocks differ.
- Report unknown time honestly before clock calibration; do not reset historical event ages on reload.
- Include the Preview 20 Settings redesign. Gameplay behavior is unchanged.

## Preview 20 — Cleaner Settings

- Replace the theme dropdown with Light/Dark preview cards and native keyboard-accessible radio controls.
- Separate preference reset from backup actions; keep optional setup details collapsed.
- Shorten VM setup descriptions and remove the repeated Settings heading.
- Preserve repair, VM update, backup and reset flows. No gameplay changes.

## Preview 13 — Round-relative strategy timing

## Preview 19 — Lighter status polling

- Add an opt-in UI status response without unused historical progress payloads; retain full logs and active state.
- Keep the full API and history unchanged; app polling uses the smaller view.
- Offline projection/handler checks pass; live sample measures 59% fewer response bytes. Visual performance verification remains pending.

## Preview 18 — Source flow audit

- Classify Randy explicit start/speed as omitted flow control rather than a source no-op.
- Confirm automatic finish sends no input; manual Sanctuary remains excluded.
- Ten offline importer checks pass. Existing recordings and runtime behavior are unchanged.

## Preview 17 — Preserve repaired imports

- Remove blanket deletion of existing imported recordings; retain repairs and original bytes.
- Restrict validation cleanup to the new import batch. Nine offline checks pass.
- Refresh reports: 893 recordings, 508/1,204 eligible map/mode pairs and 48 legacy timing review candidates. No new victory claim.

## Preview 16 — Non-blocking cursor targeting

- Schedule delayed ability cursor movement without blocking screen reads or repeating the ability key.
- Preserve existing move-only / move-and-click semantics and restore only matching cursor intent.
- 28 timing/resume checks pass offline; live missing-medal observation remains pending.

## Preview 15 — Non-blocking ability timers

- Gate timed abilities without blocking screen observation. Pin deadlines across round transitions.
- Restore unchanged ability deadlines from checkpoints and reject malformed values.
- 32 focused offline timing, resume and converter checks pass. Cursor-target waits remain unfinished.

## Preview 14 — Settings and unavailable upgrade safety

- Simplify Settings and move diagnostic readouts into Run logs. Remove the inert queue toggle.
- Apply imported/reset themes immediately.
- Prevent hotkey fallback on unavailable upgrade buttons; retain bounded exact-target recovery and explain the reason in logs.
- 19 upgrade observation and 10 resume checks pass offline. Freeze-specific recovery and live Settings visual checks remain pending.

- Add `round N after S seconds` to parsing, recording, canonical validation and the replay execution gate.
- Use one observed round-start timestamp for all scheduled actions; keep screen observation active during waits.
- Preserve explicit offsets during emergency wait release and log overdue/resumed timing recovery.
- Convert Everything Macro millisecond offsets into seconds and create separate Dark Castle Deflation and Tricky Tracks Impoppable candidates. Original recordings remain unchanged.
- Nine offline timing/recording tests and eight converter checks pass; both new candidates pass full Python parser and JavaScript legality checks. Live timing validation remains pending missing-medal gameplay.

## Preview 12 — Route timing audit

- Stop calling omitted BloonsPlayer timing, life, speed and manual-round controls harmless. Mark incomplete conversions explicitly.
- Flag Everything Macro round-relative delay loss; do not confuse a relative ability wait with an absolute round schedule.
- Add a read-only legacy timing audit: 891 recordings scanned; 48 source review candidates and four existing timing-preserved alternatives.
- Eight offline converter regressions pass. Original recordings remain untouched; no validation-only games launched.

## Preview 11 — Runtime setup recovery

- Bound the Microsoft C++ runtime request/read/download waits and show download progress.
- Reject oversized, truncated and non-executable runtime responses before launch.
- Stop waiting after 15 minutes for runtime installation and report the still-running process without terminating Windows installation.
- Compiled offline payload and ownership checks and installer atomic-output checks pass. Clean-machine installation remains a separate verification requirement.

## Preview 9 — App interface polish

- Reorganize Settings into appearance, VM setup and backups; expand profile and passive-learning diagnostics only when needed.
- Remove the unused XP target, redundant status rows and stale prototype notice from Settings.
- Add shared searchable dropdowns with keyboard navigation and theme-aware menus. Preserve selections and focused options during live updates.
- Repair dark control surfaces and contrast; restyle Boss Events with official tower art and clearly labelled planned features.
- Keep healthy replays running while changing the interface. No route validation games or original CHIMPS recording edits.

# Changelog

## Preview 36

- Repair shifted Sauda cash HUD detection, share exact map-save aliases, ignore obsolete OCR map IDs in sweep pools and restore readable log symbols. Focused offline checks pass; live validation is limited to missing-medal runs.


- Replace generated promotional art with official BTD6 tower/map compositions and preserve character proportions. Rebuild Subscriptions and Contributors, change Wiki artwork, and contain the mobile comparison table without page overflow. Keep planned billing and Pro status explicit.

## Website and README refresh — 5 October 2026

- Replace the README banner with BTD6-inspired jungle artwork and a linked website destination; add actual tower art and clearer preview/setup information.
- Refresh Features with named map thumbnails, distinct account-aware features and a compact Discord community card. Add varied tower art across About, Contributors, Wiki and Subscriptions.
- Add setup/update FAQs, canonical URLs, social previews and a public sitemap. Preserve clean URLs and redirect the retired route-tools article to route development.
- Select the newest published installer, including previews, with bounded network timeouts and validated GitHub asset links. Add offline release-lookup regression coverage.
- Keep Pro prices and example additions explicitly planned; no checkout or production-release claim.

- Reject solo routes with multiple active heroes or duplicate active tier-five upgrades on one tower path. Preserve selling/rebuying, different T5 paths and the non-CHIMPS Crossbow Master knowledge exception.

- Close stale installed Bloons+ Node controllers during installation only after an explicit idle response; preserve unrelated Node processes, Python replays and BTD6.
- Read ordinary CHIMPS medals from Hard/Clicks in the app and backend, based on observed victory/save evidence. SuperChimps no longer supplies that medal.
- Label known startup/window failures as technical failures and explicit focus/map-navigation errors as navigation failures instead of insufficient data.

- Classify defeat timing from the mode's opening round instead of a truncated observation tail, preventing late losses from receiving extra instant-failure retries.

- Keep persistent evidence for pre-game window, focus, startup and navigation failures, including recoverable relaunches. Their route attempt allowance remains unchanged.

- Block remote installation when guest replay status is missing or malformed; an update now requires an explicitly idle guest.

- Extend the stationary tower tracking repair to evidenced One Two Tree attempts while preserving unrelated failure exclusions and all saved-medal skip checks. Original routes remain unchanged.

## Unreleased — replay diagnostics and cash reading

- Separate moving tower platforms from dynamic covers, water and lane access. The Polyphemus failure log showed visual tracking relocating heli1 from its original position beside heli0, causing the wrong upgrade panel. Coordinate tracking now requires a moving-platform flag; original recordings remain unchanged. Only Polyphemus receives a new attempt revision for this evidenced fix, preserving unrelated failure exclusions and all owned-medal skips.

- Read each medal only from its matching difficulty. Ignore CHIMPS and other placeholders stored under unrelated difficulties, preventing JSON property order from hiding an earned medal. Backend and browser regressions reproduce the conflicting CHIMPS placeholder case.

- Preserve malformed saved medal values as unknown in both the app and sweep instead of treating them as unearned. Skip only the unreadable mode for the current pass without recording a route attempt; an unavailable whole profile still waits safely. Offline checks cover schema/value errors and UI parity.

- Recover HTTP 416 downloads with a fresh full request instead of declaring a same-size partial file complete. Size alone cannot identify cached content. Offline checks cover a stale large partial and preservation when the fresh request fails.

- Avoid scheduling website reading-progress animation frames while reduced motion is requested or the page is hidden. Coalesce scroll and resize updates into one pending frame, cancel it on preference/visibility changes and refresh when visible again. Public pages use a refreshed script cache version.

- Reconcile uncertain upgrade retries against visible tiers before waiting for their purchase cost again. Exact-intent panel mismatches can rejoin the bounded retry queue ahead of dependent actions; missing intent does not authorize retries. Offline checks execute the replay branch with zero cash and an already-owned target.

- Reselect the intended tower up to twice when a readable panel contradicts its planned upgrade tiers. A persistent mismatch never authorizes purchase input. Offline regressions reproduce the Polyphemus Heli mismatch; this is not a claim that the route now wins.
- Write game-state snapshots through unique temporary files with serialized writes, bounded Windows-lock retries and cleanup. Serialization failures preserve the previous snapshot rather than terminating gameplay. Exclude temporary files from Git and installers and reject them in publication checks.

- Count sweep victories only after the existing victory-plus-saved-medal confirmation, rather than immediately from a result-screen log. Defeats still update when observed, and repeated result lines do not double count. Offline regression also checks consecutive wins and preserves non-medal farming outcome behavior.
- Keep the first-observed activity timestamp stable when the VM clock is ahead; ages no longer reset to zero as the host clock approaches the original future time. Support numeric-string Unix timestamps and show unknown for malformed dates. Focused offline timestamp checks pass; existing saved timestamps are unchanged.
- Download missing Steam setup into an isolated temporary file and promote it only after length and executable-format checks. Reuse completed unchanged downloads via a local integrity receipt; replace incomplete legacy caches and clean up interrupted downloads. Existing installed Steam still bypasses this step. Six offline cache-recovery checks pass; no Steam or game installation was changed during testing.
- Prevent a partial HTTP range from being promoted to a completed installer or Windows ISO. Validate the complete Content-Range and Content-Length, retain a valid shorter chunk for resume, and roll back bytes outside the advertised range. Offline stream tests cover capped ranges, malformed offsets, unknown totals, mismatched bytes, full resumes and servers returning a fresh full file.
- Send VM setup PowerShell through UTF-16LE EncodedCommand so paths, quotes and shell metacharacters survive transport. Preserve guest stdout errors and SSH exit codes instead of empty command-failed messages. Bound ordinary remote commands to 60 seconds; Steam installation gets an explicit ten-minute allowance. Seven offline transport checks and a read-only existing-VM command pass; no credentials or permission changes involved.
- After an observed sweep victory, retry authoritative medal reads every two seconds for up to twenty seconds before deciding the clear is unconfirmed. Missing or contradictory victory evidence never starts this wait; explicit Stop ends it. Focused offline tests cover delayed writes, unavailable reads, timeout, defeat and cancellation. Guest deployment pending.
- Resume the live viewer when a browser restores the app from its Back/Forward cache. Suspend capture scheduling during page departure and clear revoked frame references. Offline lifecycle regressions cover focus, hidden categories/tabs, one in-flight request, abort and restoration; no gameplay input used. Deployment queued with the next runtime batch.
- Flag nine legacy conversions with omitted paid hero purchases in shared validation, excluding them from future sweep selection without modifying recordings. Coverage remains 508 map/mode pairs through alternative candidates; availability is not a claim that every route wins. Guest deployment is pending a later between-replay batch.
- Reject imported strategies that require paid hero levels instead of silently dropping those purchases as harmless. Four offline regressions cover both upgrade APIs, BloonsPlayer text conversion and ordinary tower upgrades. Existing recordings are unchanged; previously converted routes with dropped hero purchases still need individual review.
- Retain unresolved planned upgrades in checkpoint metadata until observed tiers prove those targets owned. Deduplicate repeated attempts without erasing other towers or higher pending tiers. Automatic resume reconciliation is still outstanding.
- Preserve the intended three-path tier vector on every parsed recorded upgrade. Already-owned target tiers (or higher) are recognized without another purchase; a missing prerequisite is no longer mistaken for the planned higher-tier upgrade. Resumable unresolved-action recovery remains unfinished.
- Exclude unverified, unchanged Hard-route aliases from unsupported variation reuse. Compare executable strategy content, so genuinely adapted candidates remain eligible. Dedicated #Ouch ABR candidates remain available; a renamed Hard recording no longer masquerades as one.
- Keep structured failure sidecars when rotating screenshots. Image retention remains capped at 60 files; JSON diagnostic records are no longer accidentally deleted by that cleanup.
- Recognize dimmed unused tier markers on capped crosspaths. Native Heli 2-0-3 frames were previously rejected as an unselected tower; they now decode correctly. Added left/right 1080p and 1440p regression coverage without changing original routes.
- Capture unsuccessful upgrade observations before the panel closes, with a local PNG and map/mode/round/cash/position/tier sidecar. Keep the observation in the run ledger for diagnosis. These private artifacts are excluded from publication.
- Fixed unreachable upgrade recovery: the retry queue was incorrectly inside the successful-purchase branch. Unselected and unchanged panel observations now retry before dependent actions, with bounded attempts and an exact target for unchanged tiers. Regression tests execute the replay branch itself.
- Extended key presses from 30 ms to 120 ms for VM input. Added ordinary-tower tier-pip observation on both panel sides, a one-second wait, and at most one button retry when the same tiers remain visible and the upgrade button is available. Confirmed visual tiers reconcile the run ledger even when income hides spending.
- Removed the blind retry on unchanged cash. Unknown or occluded panels do not authorize a second purchase.
- Verify selection before sending an upgrade key; reselect unreadable panels and keep confirmed missed actions ahead of their dependent upgrades. Bound retries and remember the intended tier to avoid purchasing an extra tier after a delayed response. Refresh the sweep engine revision so prior failures remain retryable after these engine fixes.
- Corrected ordinary-tower crosspath eligibility for surplus upgrades: legal T1/T2 crosspaths remain available beside a T3–T5 main path, and a third path cannot be opened.
- Cropped the currency symbol out of the cash reader and widened its digit area. Removed arithmetic that fabricated balances from suspicious OCR; invalid leading-zero readings now require agreement between two alternate masks.
- Matched failure evidence to the current map, mode and attempt time. Interrupted and unconfirmed runs are no longer automatically classified as gameplay defeats.
- Audited historical failure categories and created a private repair backlog. Original CHIMPS recordings are unchanged; unresolved upgrade confirmation and checkpoint issues remain documented.
- Replaced the README banner with original BTD6-inspired track, monkey, tack shooter, bloon and blimp artwork; retained the website link.
- Excluded local JPEG captures and debug JSON from Git. These changes have focused offline checks; live VM deployment and route victories are not yet verified.

## 2026-10-04 — Preview 4 site and diagnostics

- Added a Subscriptions comparison with Bloons+ Free forever and planned Bloons+ Pro pricing of $5.99/month or $40 lifetime. The target date is 31 October 2026; purchase and entitlement flows are not yet available.
- Added clearly labeled examples of possible Pro additions, game artwork to inner site pages, and reduced-motion-aware transitions between same-site pages.
- Replaced the sidebar Prestige estimate with XP/hour. MM/hour and XP/hour now use changing values from the read-only VM profile save over a rolling observation window instead of stale menu scans.
- Corrected new hero-picker failures to appear as navigation bugs in diagnostics and added a failure-category breakdown.
- Improved round-counter recovery when complete, valid HUD readings advance between captures. A live replay resynchronized to round 27/80; route victories remain individually unverified.
- Published a prioritized repair list in docs/developer/TODO.md. Original CHIMPS route recordings and BTD6 save files were not modified.

## 2026-10-04 — Replay reliability and product cleanup

- Restored strict Expert-to-Beginner sweep ordering: route confidence now only prioritizes maps inside their own category. Older saved queues are repaired without changing their within-category order; duplicate saved entries and unknown-category ordering are covered by regression checks.

- Excluded explicit user-pause time from navigation, round-stall and maximum-duration watchdogs. A focused test covers a twenty-minute pause, resume and a subsequent real active stall.

- Corrected strategy deduplication when a tower's identifier equals its type: Dart and Ninja placements now remain distinct. Added collision regression tests.
- Blocked static access to private community-bot source, backend/build folders and credential-like files; public UI and thumbnail assets remain available. Added focused path-access tests.

- Prevented the normal Play/nudge controls from being mistaken for a placement-confirm button, and blocked round starts while a placement is still pending. Original CHIMPS recordings remain unchanged.
- Fixed padded cash glyph detection. Round reading now preserves its last valid value and can recover after a long HUD obstruction using three repeated complete counter readings and elapsed-time checks.
- Replaced pause-producing Escape cleanup after upgrade retries with a right-click, and kept failed-placement screenshots for diagnosis.
- Removed the Easy/Medium exception for known locked upgrade requirements and deduplicated strategies that differ only in comments or tower identifiers.
- Added a regression check excluding the unverified CHIMPS-derived Spa Pits Alternate Bloons Rounds recording that lost at round 24 in the old guest controller.
- Reduced scrolling cost: native host GPU rendering, fewer per-card blur effects, bounded displayed logs and no overlapping automation-status requests.
- Applied the brand icon to staged application executables, installer windows and taskbar relaunch metadata; rebuilt the Discord banner.
- Rebuilt Features as six capability cards with clear feature lists; expanded the wiki with developer architecture, local setup, API reference, route syntax, validation and contribution guidance. Added grouped navigation and fixed the clipped background glow.
- Matched README to the product site. Moved 25 backend modules into lib/, maintenance reports into tools/ and project reference notes into docs/developer/, preserving existing runtime data paths.
- Excluded private community-bot source and regression tests from installer payloads; the publication guard rejects private project paths.
- Verification: three focused HUD/placement tests, strategy-identity tests, equivalent route catalogs before/after the backend move, JavaScript/Python syntax checks, app/API smoke checks and light/dark website inspection. These checks do not guarantee victory for every strategy.


## 2026-10-03 — Desktop, installer and VM repairs

- Consolidated map controls into compact Automation; removed Farm/Sweep panels and Tower Progress navigation, and set Boss Events to Coming Soon.
- Added save-backed hero and T1–T5 requirement checks using a bundled shared catalog.
- Added an on-demand live VM viewer, bounded polling, fullscreen preview and stale/error states. Temporary game frames are excluded from publication.
- Added redacted log previews/downloads and a GitHub issue draft, opened in the system browser.
- Preserved recorded action order by removing mid-route optional spending and action reshuffling; surplus upgrades remain available after planned actions finish.
- Repaired title/menu input timing and logged privilege mismatches instead of silently dropping clicks. A VM test reached actual gameplay and tower actions.
- Refreshed the installer layout, native-runtime probes, repair/retry behavior, recovery backups, logs and unchanged-file reuse.
- Added source and installer privacy guards; removed unused engine snapshots and moved maintenance scripts into tools with retained attribution.
- Fixed wiki current-article highlighting and theme initialization before paint; added brief cross-document transitions.
- Published unsigned Preview 3 with explicit verification limits and a checksum.


## 2026-10-03 — Motion and community polish

- Added a linked Discord community banner to the homepage and a shareable PNG asset.
- Added tower entrance animations, responsive card feedback and button arrow motion.
- Added a scroll progress indicator, updated through animation frames rather than polling.
- Preserved reduced-motion support and toned down the banner in dark mode.
- Fixed incorrectly encoded checkmarks and download labels.


## 2026-10-03 — Website and documentation refresh

- Added clean product URLs, Docs and a searchable wiki with seven reference articles.
- Removed language sections from the public setup guide; developer language notes remain separate.
- Added privacy and terms pages, footer links, the owner’s public GitHub avatar and Discord links.
- Added BTD6 map/tower artwork with attribution and concrete descriptions of replay actions.
- Redesigned README around setup, map runs, progress and diagnostics.
- Linked its main banner to bloonsplus.com and added a matching Discord banner.
- Reduced pale glows and increased surface contrast in the dark website theme.
- Checked JavaScript syntax, local links and loaded artwork; browser-checked Docs and wiki.

These changes do not certify route victories or clean-PC installer compatibility.
## Preview 78 — Auto Start recovery and Settings cleanup

- Wire absolute Auto Start commands into replay parsing, recording, input ownership and checkpoint recovery.
- Confirm the observed setting and close the menu before completing a command; preserve it when a checkpoint save fails.
- Recheck consumed Auto Start intent after resume and prevent automatic round control from competing with explicit manual settings.
- Validate resumed round counters against the selected mode's total.
- Simplify Settings maintenance controls and explain updates from the main PC to the VM.
- Keep incomplete source manual-round conversions excluded and original recordings unchanged.
## Preview 79 — Single Play control and colored hero titles

- Add an observed single-Play command across parser, recorder, replay ownership and resume recovery.
- Preserve pending input intent rather than sending another key without evidence, and keep automatic startup from competing with planned single Play.
- Preserve source Auto Start's initial-on baseline and toggle sequence during conversion.
- Read warm and violet hero-title fills alongside cyan; retain title verification instead of guessing hero identity.
- Keep source logical-round/end-round conversions gated; original recordings are unchanged.
## Preview 92 — Controller compatibility and community standards

- Recover native setup from an older controller's HTTP 404 by using a separate verified setup-only port; persist discovery for Resume without stopping the old controller or its replay.
- Preserve protocol, owner, executable and listening-process verification before authenticated handoff. Keep unknown setup ownership and replay safety checks.
- Add contribution, conduct, security and support policies, issue forms and a PR checklist in `.github`.
- Use the official PolyForm Noncommercial 1.0.0 text for BloonsPlus-owned material. Preserve third-party terms and required notices.
- Verify the installer and installed executable contain the original seven-frame Bloons+ icon.
- Keep the native installer design. The requested Opera-inspired styling applies to post-install configuration and remains a separate task.
