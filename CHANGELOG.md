# Changelog

## Unreleased — replay diagnostics and cash reading

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
