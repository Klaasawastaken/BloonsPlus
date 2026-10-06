# Bloons+ roadmap

Updated **6 October 2026**. This is the active task list. Detailed implementation notes, past failures and release evidence are preserved in the [history archive](history/roadmap-2026-10-06.md).

## At a glance

| Priority | Area | What remains |
| --- | --- | --- |
| **Now** | Replay reliability | Finish manual controls, upgrade recovery and live HUD/hero evidence |
| **Next** | Routes and medals | Audit incomplete conversions, improve failed candidates, fill coverage gaps |
| **Next** | Progress and connection | Check live save data, counters, rates and host/VM synchronization |
| **Then** | Installer and release | Complete clean-install, repair and distribution checks |
| **Later** | App and website | Performance, accessibility, website redesign and repository cleanup |
| **Experimental** | AI, bosses and Pro | Separate development after core reliability |

**Status key:** unchecked means unfinished or awaiting evidence. A shipped patch does not prove every route works. Completed work is summarized below; its detailed evidence stays in the archive.

## Rules for every task

- Run gameplay **only to earn missing medals**. Never run an owned medal for validation, benchmarking or route testing.
- Confirm a clear with **both victory and the saved medal**. Once earned, never repeat that map/mode for this account.
- Keep coding while the sweep runs. Apply batches **after the current replay finishes**, then safely resume missing medals.
- Keep failed attempts across sweeps. Try suitable alternatives; one failed route must not block the other missing medals.
- Preserve original recordings, especially CHIMPS. Read game/save/Steam files without editing them; use simulated gameplay input.
- Keep private saves, logs, account details, credentials, VM images and private Discord bot code out of public code and installers.
- Stop the sweep when every supported obtainable medal is owned. There is no later gameplay validation phase.

## 1. Current work — replay reliability

### Manual controls and route import

- [x] Preserve source `end_round` / `forward` commands, implicit first-round Play, logical branch order and skip-round-check consumption by empty iterations. Fifteen loop/import checks pass; eight separate candidates pass the full Python parser and JS legality checks.
- [ ] Observe the integrated manual controls and resumable checkpoints during missing-medal gameplay. Keep plans with remaining omissions excluded; new candidates are not claimed winning.
- [ ] Add faithful paid hero-level purchases before restoring candidates that omitted them.
- [ ] Audit legacy `source_btd6bot` / compatibility recordings against pinned source. Timing-only omission labels are not evidence of equivalent behavior.
- [ ] Finish remaining dependent conversion cases: repeat-ability schedules, moved selectors, positional specials and Ace centering where required. Preserve already-supported commands.

**Already implemented:** nonblocking waits, cursor and targeted-special commands, absolute Auto Start support, observed single/double Play receipts, logical round clocks and chronological source-loop traversal. Manual flow is now converted; some plans still need other commands and live outcome evidence.

### Hero, placement and upgrades

- [ ] Confirm hero name and Select/Selected state at 1080p and 1440p; observe improved title recognition and reduced picker searches during missing-medal runs.
- [ ] Confirm free and paid placements when cash is unchanged, including free Dart Monkey knowledge and Deflation cash.
- [ ] Resolve ambiguous upgrades from the exact tower panel and path/tier state; retry only the intended purchase.
- [ ] Validate unresolved-upgrade checkpoint recovery without buying the wrong tier. Remaining-action snapshots and ownership probes are implemented; live restart evidence remains open.
- [ ] Verify frozen-tower deferral and Glacial Trail timing during missing-medal gameplay. Restore excluded candidates only after their timing is preserved.
- [ ] Observe timed abilities and cursor targeting during missing-medal gameplay; offline command checks alone do not prove a win.

### HUD, recovery and failure evidence

- [ ] Verify cash at native 1080p/1440p, both panel sides and Double Cash. Reject sell-price and implausible readings.
- [ ] Confirm round reads through panels, speed changes, effects and scaling; bound stalled `await_round` actions.
- [ ] Confirm viable games continue after the planned actions end until an actual result. This already worked on individual clears; broader evidence remains open.
- [ ] Check bounded recovery for failed placement, upgrades, navigation and stalled rounds; retain exact intent and avoid blind purchase retries.
- [ ] Keep failure evidence complete: frame, action, target, selected tower/hero, cash, round and freshness. Redact shared logs.
- [ ] Review the persistent failure backlog by its own evidence. Investigate Hedge, Spa Pits, Cubism, Infernal, Glacial Trail and other remaining failures; retain historical failures for maps already cleared and never replay their owned medals.

## 2. Routes and the missing-medal sweep

- [ ] Audit candidates against mode restrictions, required paths, owned heroes/upgrades, game version and map layout.
- [ ] Generate strong candidates for missing map/mode combinations. Validate offline; mark winning only after victory plus saved medal.
- [ ] Complete map-mechanics handling: moving platforms, freezing, changing layouts, obstacles, water and line of sight.
- [ ] Review the Sanctuary legacy moving-selector failure and other incomplete conversions before restoring eligibility.
- [ ] Confirm saved-medal reconciliation after runs and restarts, partial-sweep resume and exclusion of owned or unreadable medals.
- [ ] Confirm persistent per-route outcomes and clear skip reasons: requirements, restrictions, known failures or no eligible candidate.
- [ ] Confirm Expert-to-Beginner ordering, shuffled within categories, without repeating excluded candidates.
- [ ] Regenerate coverage and audit architecture before extending the production overhaul. Eligibility is not victory evidence.

**Last recorded offline coverage:** 532 of 1,204 map/mode pairs eligible; 672 gaps and three maps without eligible routes. Eligibility does not establish winning strategies or account prerequisites.

## 3. Progress, activity and host/VM connection

- [ ] Confirm live VM save fields: level, veteran rank, Monkey Money, owned heroes, Monkey Knowledge, tower XP and T1–T5 unlocks, with source and freshness.
- [ ] Confirm veteran XP rollover semantics before displaying veteran ETA.
- [ ] Reconcile achievement progress with Steam unlocks; label unsupported counters accurately.
- [ ] Check MM/hour and XP/hour over live save updates, spending, source changes and rank changes. Show no rate until enough valid samples exist.
- [ ] Confirm activity ages, elapsed run time and victory/defeat counters across host/guest reloads. Count clears only after save confirmation.
- [ ] Keep full redacted logs and group failures by actionable cause, even when stale game-state files remain.
- [ ] Confirm host/guest synchronization after updates and restarts; expose the actual failed connection/setup step.
- [x] Deploy Preview 81 while the guest is idle, then resume missing medals. Setup confirms installation; host and guest both report the sweep running. The worker's initial two-second resume check was too early; later authoritative checks confirmed success without starting another sweep.
- [ ] Apply Preview 82 at the next completed replay boundary. Stop-after is confirmed and the update worker is waiting; keep the current replay untouched and resume missing medals after installation.

## 4. Installer, updates and production release

- [ ] Verify a clean Windows setup without Python, Visual C++ runtime, App Sandbox or an existing VM. Show progress and a repair action for each prerequisite.
- [ ] Verify Steam sign-in, BTD6 install/launch, SSH provisioning, bridge connection and remote guest update without storing Steam credentials.
- [ ] Verify partial-install repair and reuse healthy components without changing existing Steam or game data.
- [ ] Check the next packaged installer, release notes and latest-download link. Do not add a separate `SHA256SUMS.txt` asset.
- [ ] Add trusted code signing when available; unsigned installers may still trigger SmartScreen.
- [ ] Meet the production specification's acceptance gates before publishing **v1.0.0**. Preview releases are not production readiness.

**Latest published:** [Preview 82](https://github.com/Klaasawastaken/BloonsPlus/releases/tag/v0.1.0-preview.82), installer 245,318,358 bytes. 134 focused checks and 23 packaged-source comparisons passed; publication guard reported zero findings. This does not establish clean-machine installation or winning routes.

## 5. App usability and repository cleanup

- [ ] Check scrolling and category-switch performance in the actual app.
- [ ] Confirm the inline VM viewer only captures while visible/focused, including browser cache restoration. Lifecycle checks exist; broader live performance remains open.
- [ ] Finish reduced-motion and screen-reader checks for Subscriptions, including its price announcement.
- [ ] Organize repository folders while preserving runtime paths and excluding private/generated files.

## 6. Deferred website redesign

Requested **6 October**. Start after current replay/control work and VM recovery are stable.

- [ ] Use different official BTD6 monkeys on **About us** and **Contributors**. Keep **Engineer Monkey on the Wiki**.
- [ ] Fully rebuild **Features** around what Bloons+ actually does, with clear groups and varied official BTD6 art.
- [ ] Partially redesign **Home**: streamline sections, reduce clutter and strengthen its BTD6 theme.
- [ ] Preserve artwork proportions, attribution, responsive layout and accessibility. Use no AI-generated images.

## 7. Later — experimental systems

- [ ] Develop experimental strategy/placement assistance with redacted observations and route-level evidence before live decisions.
- [ ] Add executable boss routes only after handling modifiers, restrictions, game versions and outcome checks.
- [ ] Finalize Pro features, pricing and entitlements before launch. Proposed additions are not shipped features; checkout does not exist yet.

## Completed milestones

- [x] Compact Settings, safer custom dropdowns and keyboard navigation.
- [x] HUD counter bounds and freshness checks; currency-crop and alternate-mask cash recovery.
- [x] Exact-tier upgrade observations, bounded retries and ownership reconciliation groundwork.
- [x] Placement-ghost recovery and restriction of tracking to moving-platform maps.
- [x] Shared saved-medal decoding, difficulty scoping and delayed-save confirmation window.
- [x] Smaller UI status payloads, activity clock normalization and rate-sample reset safeguards.
- [x] Atomic installer/download handling and bounded SSH commands with diagnostics.
- [x] Official-art README banner, monthly/annual plan selector and latest-release download lookup.
- [x] Source import/control groundwork described in section 1; original recordings preserved.
- [x] Preview 81 deployed while idle; Preview 82 published with eight separate manual-flow candidates and package/privacy checks.

For exact checks, release history, confirmed medals and limitations, see the [evidence archive](history/roadmap-2026-10-06.md). Archive checkboxes and deployment notes are historical; use this list to choose the next task.
