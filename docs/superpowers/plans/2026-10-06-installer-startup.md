# Native installer and startup implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the approved compact native installer, recoverable environment setup and short original app startup experience.

**Architecture:** Keep C#/.NET Framework, the existing JavaScript controller and Python VM operators. Extract setup ownership and state from WinForms, then give native installation and app first-launch one session-scoped setup contract. Presentation renders observed state; it never owns game input or delays actual work.

**Tech Stack:** C# compatible with the existing Framework 4 compiler, WinForms/GDI+, Node.js, Electron and vanilla browser JavaScript/CSS; existing Python VM scripts.

**Spec:** [Approved design](../specs/2026-10-06-installer-startup-design.md).

## Global constraints

- Preserve `/silent`, `/attempt:<id>`, `BLPZIP01`, exclusive installation ownership and attempt-specific receipts.
- Add no WebView2, installer framework, runtime service or animation dependency.
- Read game/Steam saves only; never store Steam credentials, alter SSH keys/ACLs/task privileges or interrupt a healthy replay.
- Normal intro: 1–2 seconds; optional first launch: 2–3 seconds. Full/Reduced/Off; no shipped sound.
- Default install includes environment setup. Explicit defer says **App installed — environment setup deferred**. Silent guest installation is app/runtime-only.
- No fake percentages. Freeze the plan denominator within an attempt; unknown work remains indeterminate; validation precedes completion.
- Official art retains proportions. Preserve guest software rendering and current host acceleration.
- Native tests use isolated temporary roots. No clean-install experiment may repair the active VM during its replay.
- Keep private runtime artifacts, session credentials and Discord bot source out of Git and installer payloads.

## Review focus

1. Parent installer exits while a package child still mutates the environment: a second owner must wait or report recoverable busy state.
2. A unrelated process owns the controller port: installer must refuse takeover and show recovery, not send setup commands to it.
3. UAC is declined or Windows requires a reboot: persist a truthful recoverable state and preserve the user's choices.
4. A stale session command arrives after Retry/Resume: reject it without starting a second operation or changing progress.
5. User opens the app with a missing/slow VM or reduced motion: render the usable shell promptly, with accurate service/setup status.

## Task 1 — Extract native ownership and operations without behavior changes

**Files:**
- Modify `installer/installer-bootstrap.cs`: retain executable entry point and form presentation.
- Create `installer/native/InstallerProgress.cs`: existing five-stage contract, unchanged initially.
- Create `installer/native/InstallerEngine.cs`: installation owner, receipts and operation ordering.
- Create `installer/native/WindowsInstallerOperations.cs`: current archive, runtime, process and shortcut operations.
- Modify `installer/make-installer.py`: compile sorted `installer/native/*.cs` with the bootstrap.
- Modify the existing native harnesses and builder tests to compile the same complete production source list.

**Interfaces:**
- `InstallerOptions`: canonical root, silent flag, attempt token, requested VM/ISO and launch/shortcut choices.
- `InstallerEngine(InstallerOptions options, WindowsInstallerOperations operations)`.
- `Task<InstallerResult> RunAsync(CancellationToken cancellation)`; emits `Action<InstallerProgress> ProgressChanged` and `Action<string> DetailAdded`.
- `InstallerResult`: local install readiness, exit/result receipt, restart/defer facts; it does not imply VM readiness.
- Form submits options and renders events via its existing UI-thread dispatch; operations never access WinForms controls.

- [x] Add harness assertions for engine construction with no form and no filesystem mutation; operation events must not require a window handle.
- [x] Run the harness; confirm it fails because the independent engine is missing.
- [x] Move one ownership boundary at a time. Preserve lock-before-receipt ordering, healthy-runtime probes, failure return codes and silent behavior.
- [x] Update harness imports/source locations without replacing behavior assertions with string presence checks. Keep real cross-process lock proof.
- [x] Run `python -m unittest discover -s tests -p 'test_installer_*.py' -v`, plus guest ownership and release-installer tests; all must pass.
- [x] Compile the production bootstrap with all native sources; inspect its payload footer/build test before committing.

## Task 2 — Durable state, progress and interruption recovery

**Files:**
- Create `installer/native/InstallSession.cs`, `InstallerSnapshot.cs` and `OwnedProcess.cs`.
- Modify native engine/operations from Task 1.
- Create `tests/test_installer_session.py` and `tests/test_installer_process_owner.py`.

**Interfaces:**
- `InstallerSnapshot`: protocol version, session ID, operation, sequence, UTC observation time, phase/step/status, measured stage numerator/denominator or indeterminate flag, frozen weighted plan, error/human action and available commands.
- `InstallSession.LoadOrCreate(root, operation)` and `SaveCheckpoint(snapshot)` use contained application-owned paths and atomic replacement.
- `OwnedProcess`: PID, creation time, executable identity and terminal observation; unknown process state is not completion.
- `InstallerEngine.CurrentSnapshot` plus `SnapshotChanged`; keep Task 1 compatibility while consumers migrate.

- [x] Write failing assertions for stale commands, changed retry plan denominator, validation-before-complete and restart-later persistence.
- [x] Write an isolated child-process fixture: parent interruption must not allow a second installer to mutate while the recorded owned child remains alive. Cover PID reuse and inaccessible process state.
- [x] Run those tests and observe the required failures.
- [x] Implement legal phase transitions from the spec. Stage archive changes on the same volume, verify before replacement and persist recoverable boundaries.
- [x] Keep shared Windows installers alive on observation timeout. Persist outstanding work; never treat disposing a parent `Process` as proof its descendants stopped.
- [x] Add bounded retries for transient observations; cancellation stops scheduling and retains active ownership until a safe boundary.
- [x] Run session, ownership, download, runtime and builder suites; commit with exact interruption limitations.

## Task 3 — Shared setup coordinator and setup-only controller

**Files:**
- Create `lib/setup-session.js` for session validation, snapshots/checkpoints and commands.
- Modify `lib/vm-setup.js` to expose existing observed steps to that coordinator.
- Modify `server.js` and `electron-main.js` for a setup-only mode and loopback session API.
- Create `installer/native/SetupControllerClient.cs`.
- Add `tests/test-setup-session.js` and `tests/test-setup-controller.js`.

**Interfaces:**
- JavaScript `createSetupSession({sessionId, operation, owner, options}, dependencies)` returns `observe()`, `command({sessionId, sequence, action})` and `snapshot()`.
- `observe()` reconciles `vmSetup.getStatus(true)`; `command()` calls existing operators only after fresh prerequisites/ownership checks.
- Session commands: Start/Retry/Cancel/Resume/Open VM/Restart Now/Restart Later; stale identity or sequence returns a conflict without mutation.
- API `GET /api/setup/session` and `POST /api/setup/session/command`; scoped session key via request header and application-owned private handoff, never logs.
- Native `SetupControllerClient`: launch/reuse a compatible owned controller, authenticate protocol/session, observe or submit commands asynchronously.
- Setup-only flag suppresses pending replay dispatch and automatic gameplay resume; it opens no dashboard and starts no competing port owner.

- [x] Write failing tests for a wrong protocol/owner on the port, invalid session key, stale retry, duplicate Start and controller-mode suppression of gameplay timers.
- [x] Test active and unknown replay states: deployment waits; Cancel stops only the requested update.
- [x] Implement the coordinator over current VM operations; do not duplicate VM creation, SSH provisioning or Steam logic.
- [x] Persist restart/action checkpoints and re-probe on Resume; expose Steam sign-in/2FA as a human action inside Steam.
- [x] Test explicit defer versus complete environment validation, delayed bridge and parent reopen. No guessed readiness from old timestamps.
- [x] Run all setup/bridge tests and native coordinator client tests with isolated fake services; commit.

## Task 4 — Compact native presentation and installed actions

**Files:**
- Modify `installer/installer-bootstrap.cs`; create `installer/native/InstallerView.cs` and small reusable painted controls only where native controls cannot meet the approved design.
- Add `data/config/brand-tokens.json`, generated native constants and web variables; keep one build-time token source.
- Modify builder asset embedding; reuse the existing logo and official art.
- Add `tests/test_installer_view.py` and token-generation checks.

**Interfaces:**
- `InstallerView.Render(InstallerSnapshot snapshot)` and `CommandRequested` render the Task 2/3 contracts.
- `Options`: location, desktop/Start menu shortcuts, launch choice and explicit environment defer; show ISO/storage only when relevant.
- `Show details`: bounded recent technical lines and explicit redacted Copy/Export; no automatic upload.
- Existing install: observed version/health determines Launch/Update/Repair; Modify/Uninstall are secondary explicit commands preserving user/VM/game data.

- [x] Add failing native view assertions: welcome shows one Install action and Options, hides pipeline/ISO/details; completion requires validated facts and exposes Launch.
- [x] Add tests for error/human-action/restart/deferred states and preserved Options after retry. Raw SSH commands must not replace the friendly main status.
- [x] Implement compact responsive layout, restrained gradients/shadows and immediate feedback; no animation blocks an operation.
- [x] Render actual native controls into isolated artifacts at 100%, 150% and 200% simulated text/layout scale; inspect proportions, clipped text and declared focus order in both themes. Actual Windows DPI/accessibility remains Task 6 acceptance.
- [x] Test details export redaction and unavailable progress as indeterminate. Verify no credentials/session key appear in exports.
- [x] Run baseline native and view suites and compile the complete installer: 39 Python checks, seven Node suites and a 226,816-byte native bootstrap. Batch 4 commit follows these checks.

## Task 5 — First-launch setup and original startup intro

**Files:**
- Modify `assets/app/setup-bar.js`, `assets/app/app.js`, `index.html`, app CSS and `electron-main.js`.
- Create `assets/app/startup.js` and `assets/app/startup.css` for presentation only.
- Add `tests/test-app-startup.js` and shared first-launch setup contract tests.

**Interfaces:**
- Renderer `startIntro({mode, firstLaunch, reducedMotion, shellReady, serviceReady})`; returns a dismiss/cleanup controller.
- Shell and local-service readiness are independent of VM/environment readiness. VM absence never hides navigation or setup recovery.
- Preferences use existing storage: Full/Reduced/Off. Off imposes no timer; Escape dismisses branding only. The user removed the Skip intro button on 6 October.
- Setup renderer consumes the same Task 3 snapshots and commands, rather than recreating setup state.

- [x] Write failing tests for immediate shell initialization during intro, disabled/reduced launch, delayed service and absent VM.
- [x] Test a persistent service failure: transition to Retry/details, not a frozen final animation or unlimited retries.
- [x] Implement 1–2 second normal and optional 2–3 second first intro with preloaded small assets; no video/GIF/audio/dependency.
- [x] Use one stable themed window; preserve host acceleration and guest software rendering. Avoid a white/blank flash, visible console or resize.
- [x] Verify model timing and keyboard dismissal, settings persistence, lighter guest rendering and first/repeat actual renderer launches in a hidden isolated Electron window. Physical focus/screen-reader and full clean launch acceptance remain Task 6.
- [x] Run startup, setup, viewer lifecycle and app-render suites; commit.

## Task 6 — End-to-end acceptance, packaging and release

**Files:**
- Update installer/startup audit, TODO, changelog and release notes with evidence and remaining limitations.
- Update installer builder/publication guards only where new sources/assets require packaging changes.

- [x] Exercise isolated native clean/update/repair/interruption fixtures, preserving app data and recording failures by component. Final branch: 332 Python checks, ten SSH transport checks and 56 JavaScript check files pass; six final-review recovery defects have regression coverage.
- [ ] Use a separate clean supported Windows environment for actual no-dependency setup; record UAC decline, reboot later/resume, Steam sign-in/2FA and delayed bridge. Do not repurpose the active gameplay VM.
- [ ] Finish keyboard/screen-reader, DPI/text-scale, theme and weak-hardware acceptance across installer, first launch and intro settings.
- [x] Verify packaged sources match this batch, footer/receipts/ownership remain compatible and publication guards exclude private artifacts. Preview 91 EXE: 246,809,855 bytes; 125 runtime sources and all 1,669 inventory hashes matched. Preview 93 rebuild: 246,833,668 bytes, 126 runtime comparisons and all 1,682 inventory hashes match. Source and payload privacy guards report zero findings.
- [x] Publish a preview only after its completed batch is verified. Preview 93 is published with the legacy-controller 404 fix and approved post-install presentation; uploaded installer size and digest match. Keep v1.0 blocked until the full production gates pass; docs or mocks alone cannot satisfy them.
- [ ] Deploy approved runtime changes only after the current healthy replay ends; resume missing medals and independently confirm new clears from saved medals.

## Review and execution record

Recommended execution is inline in this chat, using the existing workspace and keeping missing-medal gameplay in the background. The user approved the native installer scope and this plan, with inline execution, on 6 October. Tasks 1 and 2 are complete: 31 isolated installer/guest/release checks pass and the full production source list compiles. Task 2 covers atomic replacements, durable checkpoints, process-tree ownership, cancellation boundaries and required reboot receipts. Unknown orphan state remains blocked until an observed safe boundary or a confirmed OS reboot; completion is never inferred from it. Full environment and interruption acceptance remain open. Track task commits, red/green proof and rulings in this plan's ledger. A completed extraction or passing fixture does not complete the entire installer journey.

Self-review: all twelve design sections map to these six tasks. The five Review Focus cases have explicit test owners in Tasks 2, 3 and 5. Task 1 preserves legacy installation behavior while separating its engine and Windows operations from presentation.
