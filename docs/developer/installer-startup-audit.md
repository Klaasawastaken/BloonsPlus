# Installer and startup audit

Inspected 6 October 2026 against source commit `b835fd9` (Preview 90). This is a source audit, not evidence of a clean-machine installation or approval of the redesign.

## Intended outcome

A new user should install BloonsPlus through one clear action, see honest progress, complete necessary Windows/Steam steps, and enter the app through a short original branded intro. Updates and repair must preserve user data and healthy components. Normal startup must stay fast, including when the VM is unavailable.

The installer, first-launch setup and app should share the website's visual language. Official BTD6 artwork must keep its proportions. Opera/GX is a quality reference; its assets, sounds and animation sequences must not be copied.

## Current ownership and entry points

| Component | Responsibility today | Important boundary |
| --- | --- | --- |
| `installer/make-installer.py` | Builds the native executable, embedded payload and footer; packages Electron, trimmed base Python and production Node dependencies. | Excludes private progress, logs, saves and development files. Python packages, App Sandbox, Windows ISO and Steam are downloaded later. |
| `installer/installer-bootstrap.cs` | WinForms UI, file installation, C++ runtime, private Python environment, shortcuts, setup intent and app launch. | UI and engine share one form. Installation work uses `Task.Run`; UI changes use `BeginInvoke`. |
| `electron-main.js` | Starts the local server, creates the app window and retries loading the controller URL. | Guest software rendering is deliberate; the host retains hardware acceleration. |
| `server.js` | Owns APIs and schedules installer-intent continuation, guarded replay resume and queued automation. | Only the server that owns the port starts the recurring work. A visual intro must not become the owner of setup or gameplay. |
| `lib/vm-setup.js` | Detects Windows/VM readiness and runs setup/update actions. | Persisted setup facts and current probes are distinct from the in-memory job state. |
| `vm/setup-vm.py` | Creates/starts the VM, waits for SSH, installs Steam and BloonsPlus, and launches guest tasks. | Per-attempt installer receipts and exclusive native installation ownership prevent competing updates. |
| `assets/app/setup-bar.js` | Displays setup state and dispatches actions from first launch and Settings. | Current presentation exposes an eight-step technical checklist. |
| `assets/app/app.js` | Renders the shell, restores preferences and loads progress, routes and live status. | Initial requests are independent; no unified shell-readiness event exists. |

## Actual installation journey

1. Native installer acquires the exclusive installation lock before global result receipts or file changes.
2. It checks whether its own installed controller is idle before closing that controller. It does not close BTD6.
3. It reads the embedded archive, backs up selected app data and installs changed files; identical entries are reused by size/hash.
4. It restores the preserved app data, checks/installs the C++ runtime, and verifies or repairs the private Python environment.
5. It creates the Start menu shortcut, retains an installer copy and records the chosen first-launch VM setup intent.
6. It starts the app, records native installation success and closes after a short delay.
7. The server continues requested VM setup. The app displays setup checks and required user actions.
8. VM setup advances through Virtual Machine Platform, App Sandbox, daemon, ISO, VM, provisioning, bridge and Steam/BTD6 checks.
9. Steam sign-in and authentication remain inside Steam. Runtime installation success is not full VM/Steam/game readiness.

## Progress, permissions and recovery

| Work | Available progress/evidence | Permission or recovery constraint |
| --- | --- | --- |
| Archive copy | Copied/reused bytes relative to embedded entry lengths. | Exclusive owner; changed destination files currently use direct writes. Interrupted replacement is not transactional rollback. |
| C++ runtime | Measured download bytes; runtime process and DLL probes. | Windows UAC. Exit 3010 is accepted but does not become a persisted native restart state. A timed-out runtime process is deliberately not killed. |
| Python environment | Compatibility, pinned-package checks, `pip check` and runtime import probes. Package installation is not reliably measurable as a percentage. | Private environment; healthy installations are reused before space checks. A killed parent can leave package children running: cross-restart ownership is still open. |
| Windows feature | Feature install state and active hypervisor probe. | Elevated DISM uses `/norestart`. Setup stops for a required reboot; it never reboots automatically. |
| App Sandbox | Download bytes and patched executable comparison. | Existing resources are reused. Daemon starts through UAC; display and API process are separate. Do not alter keys, ACLs or task privileges. |
| Windows ISO | Real download bytes; range/length validation and partial-file resume. | HTTP 416 falls back to a new full download. Length/range consistency alone is not trusted publisher identity. |
| VM creation/start | Actual daemon/VM state and bounded elapsed wait. | Do not turn elapsed time into a fabricated percentage or create a second VM after an observation timeout. |
| Guest provisioning | SSH readiness, verified installer upload, exclusive owner and attempt-specific terminal receipt. | Wait for existing ownership; clean/interrupted-machine evidence remains open. |
| Bridge | Fresh guest API readiness. | An earlier provisioned timestamp or process name is not proof of a current usable connection. |
| Steam/BTD6 | Guest sign-in/install probes; actual game availability is separate. | Human sign-in/2FA stays explicit. Never store credentials or edit Steam/game saves. |

Independent read-only preflight probes can run together. Preparation of small intro assets, cached UI and lightweight service checks can overlap app startup. File replacement, runtime repair, VM creation and guest deployment must retain their ownership and dependency order. Setup or update must wait until a healthy replay finishes.

## Startup timeline and gaps

- The main process synchronously loads `server.js` before `app.whenReady()` creates the window. Expensive imports can therefore delay the first visible window.
- The app window is immediately shown with a fixed light background. There is no intro, early persisted-theme bootstrap, or explicit renderer-ready handoff.
- Local URL loading has bounded retries but no final user-facing startup recovery screen.
- The renderer restores local preferences, renders the shell and starts separate connection/progress/achievement/route/status requests. Waiting for every remote request would delay usable startup unnecessarily.
- Server timers already continue installer intent and validated pending replays. These must remain independent from animation timing.
- An unavailable VM must produce a connection/setup state, not indefinitely hide the usable app shell.

## Redesign gaps to implement

- Compact welcome and progressive Options; the current installer displays VM/ISO controls and technical cards immediately.
- Separate installer operations from form presentation; keep the existing native silent/attempt command contract.
- Friendly primary status with expandable, redacted details. Current package output can replace the main status text.
- Engine-owned, weighted overall progress with explicit unknown work. Native progress resets per stage; app setup counts fresh readiness checks and can regress.
- Validated completion with an explicit Launch action. Current native success launches automatically and does not prove VM readiness.
- Installed version detection and targeted Launch/Update/Repair actions; useful location, shortcut, launch and startup Options.
- Persisted interruption/restart/cancellation semantics. Detect remaining work from actual machine state before resuming.
- Account for surviving child installers; do not assume releasing a parent lock proves their work is finished.
- Short original startup presentation, Full/Reduced/Off settings, loading/recovery transition and no white/blank flash.
- Shared visual tokens and high-DPI/accessibility checks. Preserve guest software rendering and use a lighter intro there.

## Recommended approach for design review

Retain the native C# installer and existing Python/JavaScript VM operations. Extract the installer state/operation boundary from the form, then build a compact native presentation over it. Give app first-launch setup the same friendly state model and visual language. Implement the app intro in its existing web renderer, with shell readiness separate from VM readiness.

This avoids another installer runtime and preserves the current silent guest installation protocol. A WebView2 installer would provide richer web styling but add deployment/runtime work. An Electron-based installer would reuse the app UI stack but require a larger bootstrap and duplicate-launch coordination before the app is installed.

The proposed order is engine/state and recovery contracts, compact installer flow, first-launch setup presentation, then app intro/continuity. Each batch needs focused offline evidence and later clean-machine acceptance; no animation or passing source check can establish the complete installation journey.

## Completion evidence still required

- Clean supported Windows PC without Python, C++ runtime, App Sandbox or VM.
- Existing healthy install, targeted repair, update and preserved app data.
- Interrupted download, file replacement, package installation and guest deployment; surviving-child ownership and reboot recovery.
- Declined UAC, restart later, Steam sign-in/2FA, delayed SSH/VM and unavailable service states.
- Truthful measured/indeterminate progress, bounded errors, keyboard focus, screen reader, high DPI and weak hardware.
- First/repeat launches with each animation setting and reduced motion; no console, flash, expensive asset pop-in or dependency on remote VM readiness.

The source audit completes TODO I-07. I-01–I-03, I-08–I-11 and A-05–A-07 remain open.

## Focused baseline checks

All 23 checks below passed on 6 October against the existing installer behavior.
They establish a baseline for the approved native architecture, not completion
of the redesign.

| Test file | Checks | Evidence scope |
| --- | ---: | --- |
| `tests/test_installer_ownership.py` | 2 | Native Windows cross-process exclusion, release, target isolation and duplicate receipt behavior. |
| `tests/test_installer_progress.py` | 3 | Healthy runtime reuse before repair/storage mutation and named progress/error states. |
| `tests/test_installer_controller_guard.py` | 1 | Compiled native controller ownership and runtime/payload guard behavior. |
| `tests/test_guest_installer_ownership.py` | 11 | Mocked guest staging, task/result isolation, waits and hash reuse, plus actual Windows file-lock semantics in temporary storage. |
| `tests/test_installer_atomic_output.py` | 3 | Builder preserves the last good artifact on copy/publish failures and publishes its footer correctly. |
| `tests/test_release_installer.py` | 3 | Published preview selection, invalid/incomplete metadata rejection and avoiding unnecessary artifact lookup. |

Tests use isolated fixtures and mocked setup operations. Their guest-install
messages are fixture output, not evidence that the running VM was updated.
Native harnesses compile and exercise the specified behavior; they do not run a
full installation. No game input, existing VM deployment or security settings
were changed.

Orphaned package-child recovery remains open. Atomic builder publication also
does not prove atomic replacement of installed application files. Keep both
requirements in the implementation and interruption acceptance plan.

## Approved native execution — batches 1–2, 6 October

The independent C# engine, Windows operations and progress model compile without WinForms references. The complete production entry point also compiles (122,368-byte verification bootstrap; no payload was installed). All **31** focused installer, guest-ownership and release checks pass.

Evidence includes a real parent-exit fixture, a live descendant after its direct parent exits, concurrent-installer refusal, PID identity mismatch, measured copy bytes, staged replacement interrupted before commit, retained prior content, stale-session rejection, cancellation boundaries, required reboot persistence and the real PowerShell-to-native ownership probe. Guest restart receipts now produce a concrete action instead of waiting to timeout.

Private Python dependencies start directly in a Windows job using `PROC_THREAD_ATTRIBUTE_JOB_LIST`; a timeout closes observation handles without killing shared Windows installers. Unobservable orphan state remains blocked. A confirmed changed OS boot identity can release old work for fresh repair, without claiming it succeeded. This does not prove clean-machine setup, actual UAC/reboot acceptance, shared controller coordination or the redesigned view; those remain later plan tasks.

Windows process-tree design reference: [Microsoft job objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects) and [creating a process directly in a job](https://devblogs.microsoft.com/oldnewthing/20230209-00/?p=107812). No privileges, SSH keys, active guest files or game data were changed.

## Shared setup coordination — batch 3, 6 October

The native installer now connects to the same observed VM operations through a scoped loopback session. Protocol, application owner digest, actual listening-port PID and executable identity are checked before reuse. Header authentication uses a contained private handoff; the app renderer can attach using a same-origin HttpOnly cookie. Neither credential appears in snapshots or packaged files.

Start, retry, resume and cancellation are serialized. Every deployment boundary rechecks guest ownership; an unavailable bridge can use a bounded read-only SSH process/native-journal probe. No key, ACL or task privilege changes are made. Reopened sessions retain outstanding work instead of resetting it to idle. Unknown work stays blocked until an authoritative observation or a confirmed changed host boot identity permits fresh checks. In particular, lost same-boot host ownership remains a recovery action, not permission to spawn another provisioner.

Setup-only startup suppresses gameplay timers and dashboard creation. Steam sign-in stays in Steam. The native flow keeps a local-ready result separate from environment readiness, reserves work for environment checks/finalization, and resumes the environment without copying validated local files again. Its small existing presentation remains transitional until batch 4.

Evidence: **32** installer/guest/release Python tests, **10** separate SSH transport tests and **seven** Node suites pass. The complete bootstrap compiles to **145,920 bytes**. Fake services and isolated process fixtures prove these contracts; no active host/guest service was reloaded and no full installation was performed. Actual clean Windows setup, real elevation/reboot, native DPI/accessibility and full first-launch acceptance remain open.

## Compact native presentation — batch 4, 6 October

The installer now uses a compact native welcome with one primary action and Options. Location, shortcuts, launch choice, VM defer and an existing ISO remain deliberate choices, preserved across reopen in private app-owned storage. Progress comes from observed byte counts when available; unknown work is indeterminate and human waits remain still. Closing active setup waits for its safe cancellation boundary.

Existing installations are inspected for package-file integrity and a real Python runtime probe. Their observed health and the embedded package fingerprint select Launch, Update or Repair. Apply options uses the same guarded engine. Explicit uninstall removes only unchanged inventoried app files; modified files, user configuration, routes, VM/game/save data and unlisted runtime files remain. No recursive removal or game-file edits are involved.

Light/dark tokens generate native and web colors from one source. The native view embeds proportionate official Engineer art and the existing app icon. Details are bounded; Copy/Export redact credentials, user paths, endpoints and identifiers. Exports never upload automatically. Stale command conflicts are re-observed with a three-attempt limit; transport failures do not cause blind retries.

Evidence: **39 Python checks and seven Node suites** passed; the complete production source list compiles to a **226,816-byte bootstrap**. Actual WinForms controls rendered in four states, both themes and simulated 100/150/200% text/layout scales. Welcome, dark Options and completion artifacts were inspected for clipping and proportions. These offscreen renders do not prove physical monitor DPI, screen-reader behavior, real UAC/reboot or clean-machine installation. The healthy sweep remained untouched; Sunken Columns Reverse gained both victory and saved-medal confirmation. Alternate Bloons Rounds lost at round 27 and remains in the persistent failure log.
