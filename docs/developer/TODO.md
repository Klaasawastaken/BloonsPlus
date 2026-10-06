# Bloons+ TODO

Updated **6 October 2026**. This is the readable, active task list. Technical notes, past failures and release evidence are preserved in the [history archive](history/roadmap-2026-10-06.md).

## At a glance

- **Current priority:** the installer and first-launch redesign, app polish, folders and the website alongside missing-medal gameplay.
- **Sweep:** running in the VM. Dark Castle Military Monkeys Only, Underground CHIMPS and Off the Coast Military Monkeys Only were confirmed by victory and saved medals. Cornfield Impoppable is the current replay. The previous Bloody Puddles interruption remains under investigation.
- **Development alongside gameplay:** installer/setup polish, app polish, folder organization and website redesign. Check the sweep every five minutes and diagnose meaningful failures.
- **Background work:** improve routes and placement from missing-medal gameplay evidence; retain failures and skip owned medals.
- **Latest release:** Preview 90 is published with native installer ownership and isolated VM setup tasks/results. The healthy VM replay retains its existing runtime; this batch was not deployed mid-run. Live cash-recovery evidence remains open.

## Work order

| Order | Area | Main outcome |
| --- | --- | --- |
| **1 — Recovery, then background** | [Replay reliability](#1-replay-reliability) | Restore the current run; diagnose evidenced failures between development tasks |
| **2 — Background** | [Routes and medals](#2-routes-and-medals) | Better candidates for missing medals; check the sweep every five minutes |
| **3 — Alongside gameplay** | [Installer and release](#4-installer-and-release) | Clear setup, repair and production acceptance checks |
| **4 — Alongside gameplay** | [App polish and files](#5-app-polish-and-files) | Smoother app, accessible controls and organized folders |
| **5 — Alongside gameplay** | [Website redesign](#6-website-redesign) | Clearer pages with varied official BTD6 artwork |
| **6 — Alongside gameplay** | [Progress and VM connection](#3-progress-and-vm-connection) | Accurate live progress, counters and connection status |
| **7 — Experimental** | [AI, bosses and Pro](#7-ai-bosses-and-pro) | Separate development after core reliability |

**How to read this list:** unchecked tasks remain open, including tasks awaiting live evidence. Checked tasks have recorded completion evidence. Task IDs stay stable when priorities change. A shipped fix does not prove every route wins.

### Immediate queue

1. **I-07 complete — Review the redesign:** the [source audit](installer-startup-audit.md) is complete; the native approach is approved. Review the [written design](../superpowers/specs/2026-10-06-installer-startup-design.md) before the implementation plan.
2. **I-08–I-11 / A-05–A-07 — Installer and first launch:** implement the simple install flow and branded startup in verified, recoverable batches.
3. **I-01 / I-03 / I-04 — Acceptance and releases:** check clean and interrupted setup, repair and release packaging.
4. **A-01 / A-03 / A-04 — App and files:** polish controls, accessibility, scrolling and folder organization.
5. **W-04 — Website:** finish responsive and accessibility checks for the refreshed pages.
6. **R-02 / R-15 — Recovery:** investigate game progression while replay input is paused or stopped; a paused controller does not prove a paused game.
7. **Background — R / S tasks:** check the missing-medal sweep every five minutes; diagnose failures and improve candidates without replaying owned medals.

The sweep earns missing medals alongside development. Deploy changes together after the current healthy replay finishes.

## Rules for every task

- Run gameplay **only to earn missing medals**. Never run an owned medal for validation, benchmarking or route testing.
- Confirm a clear with **both victory and the saved medal**. Once earned, never repeat that map/mode for this account.
- Keep coding while the sweep runs. Apply batches **after the current replay finishes**, then safely resume missing medals.
- Keep failed attempts across sweeps. Try suitable alternatives; one failed route must not block the other missing medals.
- Preserve original recordings, especially CHIMPS. Read game/save/Steam files without editing them; use simulated gameplay input.
- Keep private saves, logs, account details, credentials, VM images and private Discord bot code out of public code and installers.
- Stop the sweep when every supported obtainable medal is owned. There is no later gameplay validation phase.

## 1. Replay reliability

### Manual controls and route import

- [x] Preserve source `end_round` / `forward` commands, implicit first-round Play, logical branch order and skip-round-check consumption by empty iterations. Fifteen loop/import checks pass; eight separate candidates pass the full Python parser and JS legality checks.
- [ ] **R-01 — Finish source-command coverage.** Audit converted candidates for remaining moved selectors, positional specials and Ace centering; retain exclusions where exact source behavior is unsupported.
  - [x] Repeat/stop-ability commands are implemented through import, parser, recording, replay dispatch and checkpoint restore. Eight focused offline checks passed on 6 October, including duplicate slots, cancellation, rebound keys and the shared input gate. Live timing and victory remain separate evidence under R-11.
  - Selection-position suffixes and targeted-special commands already exist. Audit each source dialect and candidate before treating these as complete coverage; do not implement a second command system.
- [ ] **R-02 — Check manual controls and resume.** Observe them during missing-medal gameplay. Keep incomplete plans excluded.
- [ ] **R-03 — Support paid hero levels.** Preserve the source purchase before restoring routes that omitted it.
- [ ] **R-04 — Audit older imports.** Compare `source_btd6bot` and compatibility recordings with pinned source. Timing labels alone do not prove equivalence.

**Already implemented:** nonblocking waits, cursor and targeted-special commands, absolute Auto Start support, observed single/double Play receipts, logical round clocks and chronological source-loop traversal. Manual flow is now converted; some plans still need other commands and live outcome evidence.

### Hero, placement and upgrades

- [ ] **R-05 — Confirm hero selection.** Read the hero name and Select/Selected state at 1080p and 1440p. Check title recognition and picker searches during missing-medal runs.
- [ ] **R-06 — Confirm free placements.** Handle free Dart Monkey knowledge when cash does not change.
- [ ] **R-07 — Confirm paid placements.** Resolve unchanged or ambiguous cash observations, including Deflation cash.
- [ ] **R-08 — Confirm the intended upgrade.** Read the exact tower panel and path/tier state before retrying.
- [ ] **R-09 — Recover pending upgrades after resume.** Use remaining-action snapshots and ownership probes without buying the wrong tier. Live restart evidence remains open.
- [ ] **R-10 — Handle freezing.** Check frozen-tower deferral and Glacial Trail timing before restoring excluded candidates.
- [ ] **R-11 — Check abilities and targeting.** Observe timing and cursor targets during missing-medal gameplay; offline checks do not prove a win.

### HUD, recovery and failure evidence

- [ ] **R-12 — Improve cash reading.** Cover native 1080p/1440p, both panel sides and Double Cash. Reject sell prices and implausible readings.
- [ ] **R-13 — Improve round reading.** Cover panels, speed changes, effects and scaling. Bound stalled `await_round` actions.
- [ ] **R-14 — Continue until a real result.** Keep viable games running after route actions end. Individual clears worked; broader evidence remains open.
- [ ] **R-15 — Bound recovery attempts.** Cover placement, upgrades, navigation and stalled rounds. Preserve exact intent; avoid blind purchase retries.
- [ ] **R-16 — Save useful failure evidence.** Include frame, action, target, selected tower/hero, cash, round and freshness. Redact shared logs.
- [ ] **R-17 — Review past failures.** Investigate Hedge, Spa Pits, Cubism, Infernal, Glacial Trail and other remaining failures from their evidence. Retain cleared-map history; never replay owned medals.
  - Cornfield's converted no-harvest candidate has evidenced Heli/Village footprint failures and skipped dependent upgrades. The [failure audit](route-repair-audit.md) records the repair target; original CHIMPS recordings remain unchanged and the sweep continued with another candidate.

## 2. Routes and medals

### Candidate quality

- [ ] **S-01 — Check route requirements.** Cover mode restrictions, required paths, owned heroes/upgrades, game version and layout.
- [ ] **S-02 — Fill route gaps.** Generate strong candidates for missing map/mode combinations. Validate offline; a win requires victory plus saved medal.
- [ ] **S-03 — Handle map mechanics.** Cover moving platforms, freezing, changing layouts, obstacles, water and line of sight.
- [ ] **S-04 — Review incomplete conversions.** Include Sanctuary's moving-selector failure before restoring eligibility.

### Sweep behavior

- [ ] **S-05 — Reconcile saved medals.** Check after runs and restarts, resume partial sweeps and exclude owned or unreadable medals.
- [ ] **S-06 — Preserve outcomes and skip reasons.** Distinguish missing requirements, restrictions, known failures and no eligible candidate.
- [ ] **S-07 — Check map ordering.** Expert to Beginner, shuffled within categories, without repeating excluded candidates.
- [ ] **S-08 — Refresh coverage and architecture audit.** Complete before extending the production overhaul. Eligibility is not victory evidence.

**Offline coverage refreshed 6 October:** 526 of 1,204 map/mode pairs eligible; 678 gaps and three maps without eligible routes. Manual source schedules now require the target's starting round unless an exact-content target win exists. Eligibility does not establish winning strategies or account prerequisites.

## 3. Progress and VM connection

### Save data and statistics

- [ ] **P-01 — Check live VM save data.** Level, veteran rank, Monkey Money, heroes, Monkey Knowledge, tower XP and T1–T5 unlocks need source and freshness.
- [ ] **P-02 — Check veteran XP rollover.** Confirm its meaning before displaying veteran ETA.
- [ ] **P-03 — Reconcile achievements.** Compare progress with Steam unlocks; label unsupported counters accurately.
- [ ] **P-04 — Check MM/hour and XP/hour.** Handle spending, source changes and rank changes. Wait for enough valid samples.
- [ ] **P-05 — Check activity and run counters.** Keep ages, elapsed time and victory/defeat counts correct across reloads. Confirm clears from saves.

### Logs and connection

- [ ] **P-06 — Keep complete redacted logs.** Group failures by cause, including when stale game-state files remain.
- [ ] **P-07 — Check host/VM synchronization.** Cover updates and restarts; show the actual failed connection or setup step.

## 4. Installer and release

### Acceptance and existing safeguards

- [ ] **I-01 — Check a clean Windows setup.** No Python, Visual C++ runtime, App Sandbox or existing VM. Show progress and repair for each prerequisite.
- [ ] **I-02 — Check the complete VM setup.** Steam sign-in, game install/launch, SSH, bridge connection and remote updates. Never store Steam credentials.
  - Current VM update now uses a unique application staging folder and verifies size/hash before launch. Installed successfully; clean-machine and interrupted-install checks remain open.
  - Developer updates now select the published preview artifact before older generic builds, validate its metadata size and reject incomplete named artifacts. Launch and Steam actions resolve no installer unless provisioning needs one. Offline regression checks pass; the healthy guest replay was left untouched.
- [ ] **I-03 — Check partial-install repair.** Reuse healthy components without changing Steam or game data.
  - Installer now uses five named steps with measured percentages or a working indicator. Healthy unstamped Python environments pass version, dependency and runtime import probes before reuse. Offline progress/reuse checks pass; clean-machine repair evidence remains open.
  - Healthy environment reuse now happens before the 5 GB package-install space check. Repairs still check space before moving or rebuilding environments.
  - VM setup now reports explicit states and validates actions before advancing. Retry/failure/restart/sign-in and delayed update connection checks pass offline. Interrupted-process recovery and clean/interrupted setup acceptance remain open.
  - The native installer now holds an exclusive installation lock before file changes or result receipts. VM requests have unique tasks and receipts; setup waits for an owner and compares installer hashes before reusing an identical completed update. Real Windows cross-process, duplicate-result and PowerShell lock checks pass. Unsupported older installers are refused before staging. Recovery of orphaned package processes remains open.
- [ ] **I-04 — Check release packaging.** Installer, release notes and latest-download link. No separate `SHA256SUMS.txt` asset.
- [ ] **I-05 — Add trusted code signing when available.** Unsigned installers may still trigger SmartScreen.
- [ ] **I-06 — Meet production acceptance gates.** Complete the specification before publishing **v1.0.0**; previews do not establish production readiness.

**Latest published:** [Preview 90](https://github.com/Klaasawastaken/BloonsPlus/releases/tag/v0.1.0-preview.90), installer 246,311,732 bytes. Verified 314 Python checks, ten setup-transport checks, 50 JavaScript check files and 29 packaged-source comparisons; publication guard reported zero findings. Dark Castle Military Monkeys Only, Underground CHIMPS and Off the Coast Military Monkeys Only were confirmed by victory and saved medals. Clean-machine installation and live recovery evidence remain open.

### Installer redesign — requested 6 October

**Quality target:** the clarity and polish of a commercial Windows installer, with an original Bloons+ identity matching the website. Use official BTD6 art and crisp, proportional graphics. Do not copy Opera/GX assets, sounds or animation sequences.

- [x] **I-07 — Inspect before redesigning.** Read the current installer frontend/backend and application launch path. Map every dependency, VM, SSH and BTD6 stage; administrator requirements; measurable progress; safe concurrency; and interruption recovery. Record what loads before the dashboard is ready. Preserve working backend behavior.
  - [Source audit](installer-startup-audit.md) records the two-phase installation journey, current ownership boundaries, actual progress sources, UAC/restart behavior, safe concurrency and startup readiness gaps. Clean-machine and interrupted-install acceptance remain open; no product behavior changed in this audit.
- [ ] **I-08 — Build a compact, simple install flow.** Welcome with one clear **Install BloonsPlus** action and secondary **Options**. Transition through preparing, installing and validated completion with **Launch BloonsPlus**. Hide advanced choices until requested; avoid a long Next/Next wizard. Offer useful options such as shortcuts and launch behavior, without exposing internal commands as normal controls.
- [ ] **I-09 — Separate engine and presentation.** Keep installer state/operations, installer UI, app bootstrap, launch presentation and main UI distinct. Render real engine state. Each stage needs friendly status, technical details, progress behavior, bounded retry, cancellation and resume rules. Show measured stage/overall progress where meaningful and an indeterminate state where work cannot be measured. Never invent percentages, regress overall progress or declare completion before validation.
- [ ] **I-10 — Add smart preflight and targeted repair.** Check Windows version/architecture, storage, virtualization/features, runtimes, existing installation/VM, SSH, network, permissions and incomplete setup. Reuse healthy components; verify changes before advancing. Resume from actual machine state instead of rebuilding resources. Recognize installed versions and expose Launch, Update and Repair, with Modify/Uninstall secondary. Preserve app data, Steam, game data, VM disks, settings and keys.
- [ ] **I-11 — Polish recovery and diagnostics.** Use friendly error summaries with Try Again/Repair and expandable details; preserve original diagnostics and support redacted copy/export. Group required elevation with a clear reason. Treat restart required as a persisted state with explicit Now/Later choices and recovery after reboot. Use bounded backoff for transient downloads/VM/SSH failures, verify downloads and resume where safe. Keep heavy work off the UI thread.

**Design and motion:** compact visual/functional areas, excellent typography, rounded surfaces, restrained gradients/glow, subtle shadows and brief state transitions. Respond to clicks immediately; never delay setup for an animation. Avoid constant particles, large spinners or an exaggerated RGB style.

**State contract to audit:** idle, preflight, downloading, installing dependency, enabling feature, restart required, configuring/starting VM, configuring guest/SSH, deploying Bloons+, validating, finalizing, complete, recovering, failed and cancelled. Define retry, cancellation, resume and diagnostics for each rather than adding presentation-only labels.

**Acceptance journey:** open installer → clear install action → automatic checks/setup → honest progress → validated success → launch → short original intro → ready dashboard. Human sign-in, permission and restart steps remain explicit when required. Clean-machine and interrupted-install evidence are still required by I-01–I-03.

## 5. App polish and files

- [ ] **A-01 — Check app performance.** Scrolling and category changes should feel responsive.
  - Hidden card lists are deferred; unchanged medal data retains map cards. Overview and navigation counters remain live. Focused redraw/search/medal checks and browser search inspection pass; wider performance acceptance remains open.
- [ ] **A-02 — Check the inline VM viewer.** Capture only while visible/focused, including browser cache restoration. Lifecycle checks exist; broader live performance remains open.
- [ ] **A-03 — Finish accessibility checks.** Reduced motion and screen readers for Subscriptions, including price announcements.
- [ ] **A-04 — Organize folders.** Preserve runtime paths and exclude private/generated files.

### App startup and first launch — requested 6 October

- [ ] **A-05 — Build an original branded intro.** Use the Bloons+ logo and restrained tower/map motifs, with a seamless transition into the actual dashboard. Target roughly 1–2 seconds on normal launch; an optional richer first launch may take 2–3 seconds. Load configuration, cached UI and lightweight connections concurrently. If readiness takes longer, show a real loading state; never freeze the final animation frame.
- [ ] **A-06 — Keep launch fast and accessible.** Use small vector/native/GPU-friendly assets, not a large video or GIF. Preload required assets; avoid white flashes, window resizing, console windows, asset pop-in and a blank frame before the app. Support Full/Reduced/Off animation settings and reduced-motion preferences. Allow dismissal/recovery when startup fails. Keep sound off unless an appropriate original/licensed asset and user control exist.
- [ ] **A-07 — Match installer, intro and app.** Share website colors, typography, logo treatment, radii, spacing and motion curves. Animate button feedback, state changes, errors and completion without stalling work. Check high DPI, weaker hardware, keyboard/screen-reader use and first versus repeat launches. A color change plus loading GIF does not complete this redesign.

## 6. Website redesign

Requested **6 October**. Work alongside background missing-medal gameplay after recovering the current stalled controller.

- [x] **W-01 — Vary character artwork.** Four hero portraits (Quincy, Sauda, Benjamin and Gwendolin) and seven additional tower types distributed across pages; Engineer remains on the Wiki. README banner uses Wizard, Quincy, Alchemist and Sauda.
- [x] **W-02 — Rebuild Features.** Four practical workflow groups and a compact progress section, using varied official monkeys. Desktop/dark/narrow browser checks pass without broken images or horizontal overflow.
- [x] **W-03 — Streamline Home.** Three feature cards, clearer copy and corrected installation link. Retain the requested app-preview hero and floating card.
- [ ] **W-04 — Check artwork and layout.** Preserve proportions, attribution, responsiveness and accessibility. No AI-generated images.

## 7. AI, bosses and Pro

Start after core reliability. These are future work, not completed features.

- [ ] **E-01 — Develop experimental assistance.** Use redacted observations and route evidence before live strategy or placement decisions.
- [ ] **E-02 — Add executable boss routes.** Handle modifiers, restrictions, game versions and outcome checks first.
- [ ] **E-03 — Finalize Pro.** Decide features, pricing and entitlements before launch. Proposed additions are not shipped; checkout does not exist yet.

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
- [x] Preview 81 deployed while the guest was idle. Later host/guest checks confirmed resume; the initial two-second check was too early.
- [x] Preview 83 deployed between replays, including eight separate manual-flow candidates and the schedule-reuse guard.
- [x] Preview 82's waiting deployment stopped before installation so the schedule fix could join Preview 83. The healthy replay continued.
- [x] High Finance Reverse earned on 6 October: victory at round 60 plus authoritative saved medal. Never repeat the owned medal.
- [x] Underground CHIMPS earned on 6 October: victory plus authoritative saved medal. Never repeat the owned medal.
- [x] Preview 84 recovered the stalled Bloody Puddles Play receipt without restarting the map or sending an extra Play input. The run continues toward its missing Impoppable medal.

For exact checks, release history, confirmed medals and limitations, see the [evidence archive](history/roadmap-2026-10-06.md). Archive checkboxes and deployment notes are historical; use this list to choose the next task.
