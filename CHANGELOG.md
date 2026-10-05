# Changelog

## Unreleased — replay diagnostics and cash reading

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
