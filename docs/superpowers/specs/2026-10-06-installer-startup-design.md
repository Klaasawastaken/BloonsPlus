# BloonsPlus installer and startup design

Status: **written design for user review**. The native approach was approved in chat on 6 October 2026. Implementation is not yet approved by this document.

Source baseline: Preview 90, commit `b835fd9`. The [source audit](../../developer/installer-startup-audit.md) describes existing behavior and acceptance gaps. Roadmap tasks: I-08–I-11 and A-05–A-07; I-01–I-03 remain the installation acceptance gates.

## 1. Product outcome and constraints

One obvious installation action should lead through automatic checks, necessary setup, clear human actions and validated completion. The normal UI must be compact and friendly, while technical diagnostics remain accessible. Repeat launches should show a short original BloonsPlus identity moment and enter a usable dashboard without waiting for a remote VM.

Keep the native C# installer, current JavaScript controller and Python VM operations. Add no WebView2, installer framework or additional runtime. Preserve `/silent` and `/attempt:<id>`, the payload footer, exclusive installation ownership, pinned runtime checks, verified guest uploads and per-attempt receipts.

Preserve all user data, VM disks, original routes, SSH keys, ACLs and task privileges. Never edit BTD6/Steam saves or collect Steam credentials. Never interrupt a healthy replay to update. Game input remains owned by the replay engine; installation and intro presentation never send gameplay input.

Use official proportional BTD6 art and original BloonsPlus motion. Share the website's restrained blue/coral visual identity. Do not copy Opera/GX assets, animation sequences or sounds. Audio stays disabled for this release; no placeholder or unlicensed sound is shipped.

## 2. Components and ownership

### Native installer

Separate four responsibilities:

- **State model:** immutable snapshots and legal transitions, independent of WinForms.
- **Operation engine:** preflight, archive files, runtimes, shortcuts, retained installer and setup handoff. One installation owner controls mutation.
- **Windows operations adapter:** filesystem, process, download and elevation calls; real implementation remains testable through isolated paths and injected observations.
- **Presentation:** compact welcome, Options, current stage, details, human-action/error states and completion. The form renders snapshots and submits commands only.

Extract behavior incrementally from `installer-bootstrap.cs`, preserving compiled native tests. `make-installer.py` must compile/package all extracted sources and small embedded brand assets. No new runtime dependency is required to show the first installer screen.

### Environment setup

Keep `lib/vm-setup.js` and `vm/setup-vm.py` as the operators for Windows/VM/SSH/Steam work. Add a session-scoped coordinator over those existing operations. Native setup and app first-launch/Settings use the same coordinator and state contract; they do not implement separate VM creation logic.

After local app/runtime validation, the native installer can start or connect to the installed local controller for environment setup without opening a second dashboard. A setup-only controller mode must suppress pending gameplay dispatch and automatic replay resume. It may perform explicitly requested setup and show the VM for Steam sign-in. It must not start another port owner or take over an unrelated process.

A session has a random identifier, canonical application-owned receipt location and process identity. Reuse a live existing controller only after compatible protocol and ownership checks. Local setup commands are scoped to the session; bind only to loopback and do not expose session credentials in diagnostics. Observation timeout is not proof that a setup process died.

### App bootstrap and presentation

Keep process/bootstrap code separate from startup animation. The bootstrap starts/checks the local controller and loads the renderer; the renderer owns the short intro and shell-ready handoff. Existing VM software rendering remains enabled; the host retains acceleration.

App setup presentation remains available when setup is deferred, after a reboot, or when a component needs repair. It consumes the coordinator state, not a second set of setup assumptions.

## 3. State and command contract

Each snapshot includes:

- protocol version, session identifier, operation (`install`, `update`, `repair` or `resume`), sequence and observed timestamp;
- phase, current step, user-facing status and optional structured error;
- stage progress with a scope and measured numerator/denominator, or explicitly indeterminate;
- weighted completed work, current measurable work, and total planned weight;
- required human action, retry/cancel availability and retained checkpoint;
- redacted recent details and component readiness/freshness.

Phases are `idle`, `preflight`, `downloading`, `installing_dependency`, `enabling_feature`, `restart_required`, `configuring_vm`, `starting_vm`, `configuring_guest`, `configuring_ssh`, `deploying_bloonsplus`, `validating`, `finalizing`, `complete`, `recovering`, `failed` and `cancelled`. A human-action field distinguishes Steam sign-in, permission and retry without pretending they are active work.

Commands are Start, Retry, Cancel, Resume, Launch, Open VM, Restart Now and Restart Later. Reject stale-session commands and duplicate mutations. A cancelled or failed phase may resume only after fresh machine-state detection. `complete` is emitted only after the selected operation's acceptance checks succeed.

The default installation includes environment setup. When the user explicitly defers VM setup in Options, completion says **App installed — environment setup deferred**. It must not say automation is ready. Native `/silent` guest installation remains app/runtime-only to prevent nested VM provisioning.

## 4. Welcome, Options and installed actions

Initial compact screen: BloonsPlus mark, **Automate Bloons TD 6**, primary **Install BloonsPlus** and secondary **Options**. Do not display every backend step, ISO field or technical component card immediately.

Options expose installation location, desktop/Start menu shortcuts, launch on completion and environment setup/defer. Startup behavior must be explicit and off unless requested. Existing ISO and VM storage choices appear only where meaningful. Validate paths and drive capacity before mutation. Defaults work without opening Options.

An existing installation shows its actual installed version and health. Primary action is Launch when current and healthy, Update when a newer selected build exists, or Repair when unhealthy. Modify and Uninstall are secondary. Destructive actions require an explicit command and identify what will be removed; saves, Steam/game data and VM disks are not implicitly removed.

Preserve user choices across retries. Do not reset a healthy component or overwrite existing data merely because the user selects Repair.

## 5. Install and first-launch journey

1. Install responds immediately and begins lightweight preflight. Animation never gates work.
2. Validate Windows architecture/capabilities, target storage, required features/runtimes, existing installation/VM, network and permission needs. Distinguish unknown from absent.
3. Form an operation plan from actual machine state. Probe independent read-only components concurrently; keep dependent mutations sequential.
4. Install/verify local app and runtimes under exclusive ownership. Preserve existing app data and support interrupted file replacement.
5. Continue requested environment setup through the coordinator. Reuse existing resources; create/start only what is required.
6. Explain required UAC, reboot or Steam sign-in with one clear action. Keep original diagnostics under details. Open the VM for Steam/2FA rather than collecting credentials.
7. Validate local app/runtime, guest deployment, live bridge, selected Steam/game readiness and retained setup state.
8. Show deliberate completion and **Launch BloonsPlus**. Honour the user's explicit launch-after-install choice without pretending app start proves environment readiness.
9. Launch enters the short intro and then the dashboard. Deferred or remaining setup uses the same friendly setup presentation in the app.

Update and Repair share this flow. VM deployment waits for confirmed guest idleness; unknown status is not idle. If a healthy run is active, show **Waiting for this replay to finish** and continue observation without killing gameplay.

## 6. Honest progress

The engine calculates progress; UI animation only interpolates already-observed values. Stage weights represent planned work, not elapsed-time guesses. Final validation and finalization have reserved weight so completion cannot be reported early.

- Downloads and archive copying use actual byte counts where available.
- Unknown package installation, VM startup and service waits use an indeterminate current-stage indicator.
- Completed-stage milestones remain visible while an unknown stage runs; do not label them as a measured current-task percentage.
- Freeze the overall plan denominator within an attempt. If fresh preflight changes the plan, begin a clearly labelled recovery attempt rather than silently moving progress backwards.
- Reused healthy components earn completed weight only after their probe passes.
- A failed or waiting-human state stops the work animation. Completion is never shown solely because all commands were issued.

Time estimates require observed data. Do not invent a percentage from minutes waited or hold a bar at 99% while unbounded work continues.

## 7. Recovery, cancellation and elevation

Persist versioned session facts and durable stage boundaries with atomic writes. On reopen, compare receipts with actual machine state and live process identity; checkpoints alone do not prove completion or death.

Changed app files are staged and validated before replacement. Interrupted replacement must leave an identifiable repair state and recoverable preserved data. Only application-owned temporary paths may be cleaned. Never recursively delete a computed path without containment checks.

Track child process identity, creation time and ownership. A parent exit must not let a second installer repair an environment while an orphan package process is mutating it. Cancellation and retries must wait for safe ownership release or show a bounded recovery error.

- Preflight and downloads: cancellation stops owned work and retains safe partial downloads.
- File installation: stop at a safe verified file boundary and retain a repair checkpoint.
- Package installation: cancel only owned child work using the supported process boundary; validate the environment again before resuming.
- Windows feature/C++ installation: do not kill a shared Windows installer. Record the outstanding process/state and wait or explain required action.
- VM/SSH deployment: stop scheduling new work and retain the active owner's receipt. Do not shut down/delete a VM or kill gameplay to cancel setup.
- Replay wait: cancel the update request without stopping the replay.

Group elevation where compatible with ownership and Windows semantics. Explain why UAC is needed; declining it yields a recoverable state. Never restore task privileges, alter ACLs or repair SSH keys as a hidden fallback.

Restart required is persisted, with Now/Later choices. Reboot happens only through explicit Restart Now. On a later app/installer launch, Resume re-probes and continues; optional automatic startup must be an explicit user choice.

Use bounded retry/backoff for transient network, VM and SSH observations. Invalid artifacts, missing permissions or unhealthy persistent state require targeted repair/action rather than an endless retry loop. Verified resume requires a matching version/validator; range/size agreement alone is not publisher authenticity.

## 8. Diagnostics and privacy

Friendly primary text describes the failed component and next action. **Show details** reveals current operation, recent technical lines, download information and the original error. Provide keyboard-accessible Copy/Export, not an embedded raw terminal.

Redact account names, user paths, hostnames, addresses, credentials, keys, session identifiers and save content from shared exports. Local logs may retain necessary private diagnostics in application-owned storage. Sharing/export is explicit; installing, launching and viewing an error never upload diagnostics automatically.

Keep private runtime artifacts and bot source excluded from public source and installer payloads. Retain publication guards; do not claim they prove absence of every possible private datum.

## 9. Original app intro and readiness

Normal launches target 1–2 seconds; optional first launch targets 2–3 seconds. Use the existing BloonsPlus mark, brief restrained assembly/light treatment and a dissolve into the actual shell. No large video/GIF, new animation dependency or copyrighted sound.

Create one stable-sized app window with a theme-compatible background and preloaded small assets. Render cached shell/configuration and start lightweight checks concurrently with the intro. Do not wait for the intro before initializing the app.

Separate readiness:

- **Shell ready:** preferences/theme, navigation and initial controls are rendered; stale/missing live data is visibly labelled.
- **Service ready:** the local controller can answer its required APIs.
- **Environment ready:** VM, bridge and game prerequisites are healthy.

Only shell/local-service readiness affects entering the main app. VM absence or a slow profile request must not hide the shell. If local startup is delayed, transition to an honest loading/recovery screen with Retry and details. Never freeze an animation frame indefinitely.

Settings expose Full/Reduced/Off. Respect system reduced motion and use the lighter path in the software-rendered guest. Off shows no forced animation delay. Escape/Skip dismisses branding, while real readiness/error state remains visible. Reuse the same background/window throughout; avoid console windows, white flashes, resize jumps and blank intermediate frames.

## 10. Visual and accessibility system

Share source tokens for website/app/native colors, spacing, typography roles, radii and motion duration/easing. Native generated constants and web variables come from one small build-time source; no runtime token service.

Use rounded surfaces, readable contrast, subtle gradients/depth and short state transitions. Keep form size compact but let content grow/scroll for DPI and text scale rather than clipping. Render only controls for the current decision.

Keyboard focus must remain visible and move predictably after state changes. Status/progress/errors need accessible names and polite announcements. Do not announce every download byte. Reduced motion replaces sliding/assembly with simple fades or static states. Official art preserves aspect ratio at all scales; details remain readable in both themes.

## 11. Implementation slices and proof

1. Extract native state/operations without changing current behavior; verify ownership, silent receipts and runtime reuse.
2. Add durable operation/recovery/progress contracts and shared coordinator integration; verify duplicate requests, active replay waits, cancellation and interrupted ownership.
3. Replace native presentation with compact welcome/Options/details/actions/completion; inspect real native renders at multiple DPI levels.
4. Give first-launch/Settings setup the same state presentation and targeted recovery.
5. Add bootstrap/intro/settings/readiness; verify normal, first, delayed, failed, reduced and disabled launches.
6. Verify complete clean/update/repair/interruption journeys and package/publish a preview. Publish v1.0 only after the full production acceptance gates are met.

Offline tests and mock process observations establish contracts, not clean-machine success. Actual Windows checks must use isolated owned paths and never install into the current healthy VM mid-replay. Gameplay is launched only to earn missing medals; there is no route-validation phase for owned medals.

Acceptance must cover Windows without dependencies/VM, healthy existing installs, low storage, declined UAC, partial downloads, parent/child interruption, reboot later/resume, Steam/2FA, delayed bridge and active gameplay. UI acceptance covers high DPI/text scale, keyboard/screen reader, dark/light themes and weaker hardware. Release evidence must include exact packaged-source matches, guarded payload and honest limitations.

## Review decision

Confirm this written contract before the implementation plan. The plan will select inline execution and retain missing-medal gameplay in the background. Changes will be batched and deployed only between healthy replays.
