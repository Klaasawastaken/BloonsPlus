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
