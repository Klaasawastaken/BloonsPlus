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

## Shared first launch and startup — batch 5, 6 October

First-launch setup and Settings now observe and command the native installer's authenticated session. They retain the same sequence, queued replay wait and saved Restart Later choice. Pause cancels queued setup without stopping gameplay. Restart Now requires an explicit confirmation. Details preserve a bounded redacted error, while navigation stays available if the VM is missing. Explicit VM updates no longer disappear behind already-ready environment checks.

The original small-logo intro runs concurrently with the shell: Full uses 1.6 seconds, Reduced 1 second, and first launch 2.4 seconds; Off adds no branding timer. System reduced motion and software-rendered guests use Reduced. Escape/Skip dismiss branding only. Local-service readiness has an eight-second deadline and explicit Retry/details, independent of VM readiness. Initial and recovery-link navigation retries are bounded. An existing status-poll initialization error exposed by actual rendering is fixed.

Evidence: 39 focused native/guest/release Python checks, ten SSH transport checks and eleven JavaScript suites pass. A hidden isolated Electron window loaded the actual app assets with fake local APIs, blocked external requests, and exercised first/repeat launch preferences, Escape, inline missing-VM restart controls and persistent controller failure. Inspected light intro/shell and dark repeat artifacts are unclipped. The render recorded no uncaught application errors after the initialization fix; Electron still reports the existing development Content Security Policy warning. This does not certify physical focus/screen readers, weak hardware, a production controller launch, UAC/reboot, Steam/2FA or clean Windows installation. Current gameplay has not been reloaded. Spice Islands Hard Standard gained both victory and saved-medal confirmation.

## Final branch review and preview packaging — 6 October

One fresh reviewer found six concrete recovery defects. The fix pass adds regressions for active cancellation followed by Resume, remote restart boot receipts, selected Update intent, the actual optional-argument constructor used by SSH ownership observation, actionable recovery after a lost VM connection, and opening the shell while setup-only ownership persists. The setup-only process serves static assets and read-only setup status, while ordinary APIs and background gameplay timers remain suppressed. Its isolated real HTTP check accepts the shell and rejects gameplay POST.

All **332 Python checks, ten SSH transport checks and 56 JavaScript check files** pass after the fixes, including a fresh pre-publication run. Source and payload publication guards report zero findings. The final rebuilt installer is **246,809,855 bytes (235.4 MiB)**; 125 runtime sources and every one of its 1,669 inventory hashes match the source/package. Its executable and `BLPZIP01` footer are intact. These are preview gates. Actual clean Windows dependency/VM installation, UAC decline, physical reboot/resume, Steam/2FA, monitor DPI, screen readers and weak hardware remain open. The healthy missing-medal sweep is unchanged by these source checks. Keep the six-batch plan open until those acceptance gates are evidenced. Spice Islands Alternate Bloons Rounds subsequently gained both victory and saved-medal confirmation.

## Reported legacy-controller HTTP 404 — 6 October

The native install log places the repeated 404 in `SetupControllerClient.ConnectAsync`. The already-running host's `/api/setup/controller` returns 404, while the official setup download links return 200. A legacy app controller occupies the usual local app port; repeatedly retrying it cannot create the new setup endpoint.

The native client now launches its setup-only controller on a separate free loopback port for that exact legacy-404 case. It keeps the legacy listener and replay untouched. Before handoff it still checks protocol, installation digest, actual listening PID and executable. A private discovery receipt reconnects Resume to that same controller; it does not establish trust. Port-binding races or a wrong owner still fail verification before authenticated commands. Persisted outstanding setup work still requires the existing fresh ownership checks.

The regression first failed because this recovery path was absent, then passed with a real isolated legacy listener and owned controller: one read-only legacy probe, no legacy secret or mutation, one private controller and an authenticated reconnect without duplication. All 333 Python checks, ten SSH checks and 56 JavaScript check files pass. Rebuilt package: 246,828,802 bytes; 125 matching runtime sources, all 1,680 inventory hashes verified and seven exact original app-icon frames in both executables. This fixes the observed transport cause; actual clean-machine acceptance remains open.

## VM provisioning rejects the current installer — 6 October

The native screenshot showed “Setup needs attention” with empty details. The authenticated setup checkpoint identified `provision`: the current executable was incorrectly reported as too old to support isolated attempt receipts. Local app files and Python were already installed successfully.

Evidence: Preview 93's capability string occurs at byte 396,749. The VM helper scanned only the first 262,144 bytes, so the added icon resources caused a false negative. The repaired helper scans the bounded native stub in chunks, excludes the appended package using the validated footer extent, handles strings across read boundaries and caps inspection at 16 MiB. Packaging now checks the finished artifact before replacing the previous usable installer.

The native adapter previously discarded the structured component error and replaced the failed phase with generic validation. It now retains the actual error in the snapshot, result, log and automatically expanded details. Repeated identical detail lines are suppressed. Regression fixtures cover both defects; the actual installed executable passes the corrected helper. Only the host setup script was updated in place; no active replay, VM controller or game/save file was changed.

Preview 94 artifact checks: 336 Python checks, ten SSH checks, 56 existing JavaScript suites, 126 source comparisons, 1,683 inventory hashes and all seven icon frames pass. Installer size is 246,836,142 bytes. Clean-machine/UAC/reboot/physical acceptance remains open; this diagnosis does not claim complete guest provisioning while the missing-medal replay is active.

## Archive preparation and caught-failure rollback — 6 October

The installer previously committed each archive entry before inspecting later
entries. An isolated real ZIP fixture reproduced an unsafe later path leaving an
earlier installed file changed. A second fixture reproduced the first replacement
remaining changed after the second replacement failed.

The file operator now validates the complete path plan, rejects duplicate files
and file/directory collisions, stages all changes on the destination volume and
verifies recovery copies before replacement. Caught failures or cancellation roll
back attempted replacements in reverse order. A changed destination is preserved
and its verified prior copy retained. Staging files are cleaned after an observed
failure. Measured preparation/application work remains below completion until the
replacement pass finishes; unchanged files retain their modification time.

Both regressions passed RED to GREEN. The three archive checks cover eight
preparation/rollback scenarios plus locked-file and reuse behavior. The complete
341-check Python suite, ten SSH checks and 57 JavaScript suites pass. These are
isolated fixtures; no installed app, healthy guest replay or game/save file was
changed. Abrupt process termination/power-loss recovery still needs a persistent
package transaction. Retained copies are not automatically replayed on retry.
Clean-machine and physical acceptance remain open.

## Persistent package recovery — 6 October

A real child-process exit after replacement reproduced a mixed package that the
next installer could not recover. Setup now flushes a private journal before
staging and persists the complete prepared package intent before any replacement.
Verified old copies and staged files live in one contained directory on the
installation volume. Recovery runs under installation ownership before retained
data restoration or the next package preflight.

Preparing recovery removes owned staging without changing app files. Prepared
recovery restores prior hashes in reverse order and removes introduced files.
Committed recovery only finishes cleanup, keeping the new package. The journal
is removed last. Outside edits, missing or changed recovery copies and unsafe
paths retain the journal and data for repair. A final hash pass prevents silent
outside changes from being reported as a committed package. A pending journal
blocks healthy inventory, uninstall, runtime readiness and packaged app startup.

RED-to-GREEN fixtures cover process exits after each of three replacements,
pending inventory/startup guards, unknown journal artifacts and a silent outside
edit after the last replacement. Additional checks cover preparing exits,
committed cleanup interrupted by a real file lock, repeated recovery, conflict
resolution, oversized/unsafe journals and real directory junctions. Complete
verification: 346 Python checks, ten SSH checks and 58 JavaScript check files.

These are isolated filesystem/process fixtures. They do not prove physical
power-loss durability or clean-machine Windows/UAC/reboot/accessibility
acceptance. No healthy gameplay or game/save file was changed. Prior Preview 96
temporary copies without a journal are not automatically adopted as trusted
transaction data.

## Existing-guest update and production-tag selection — 6 October

The guest replay ended at an observed stop-after boundary. Bloonarius Prime
CHIMPS reported `VICTORY_CONFIRMED`; a separate read-only profile read found
Hard/Clicks=1050185, above the earned-medal threshold. `SuperChimps=2` is a
different internal field and is not the CHIMPS medal. The completed target must
remain skipped.

The host's remote update completed without a setup error. Read-only SSH hashes
for `replay.py`, `helper.py`, `automation.js`, `select-controls.js` and `server.js`
matched the Preview 98 payload. Guest status and game detection responded; the
host's Start Sweep request succeeded. Balance Hard began with an unearned saved
Standard value of 608. This proves an update on this existing machine, not clean
provisioning, physical accessibility or a post-update clear. Later source changes
are not part of the deployed Preview 98 package.

A separate production-release defect was reproduced in both host JavaScript and
the standalone Python VM helper: `v1.0.0` metadata ignored its named artifact and
selected an older generic installer. Both selectors now retain preview naming
and recognize the fixed stable directory `dist/v1.0.0`. Numeric tag validation,
fixed filename, missing-artifact fallback and size-mismatch rejection remain.
Both regressions passed RED to GREEN; the full 354-check Python suite and 60
JavaScript check files passed. Scoped read-only review found no regressions.
The unpublished route draft was excluded from JavaScript checks and publication.

## Live app requirements and dark surfaces — 6 October

The host app was inspected against its real VM API while Balance Hard continued.
Monkey Meadow's owned medal disabled Run Selected. Route requirements displayed
the saved Sauda/Etienne ownership and Engineer path unlocks; the Hard route's
required T5 appeared on the same row as T1–T4. No route was launched for this UI
inspection and no owned medal was replayed.

Dark checklist rows retained a white translucent background and border from the
light stylesheet. The actual label/value contrast was 2.06:1/3.88:1. Only dark
rows now use existing control-background and line tokens. A production-stylesheet
regression reproduced the contrast failure before the repair. Independent hidden
Chromium windows at actual 1,266 px and 606 px widths now measure 6.05:1/11.39:1,
retain T1–T5 on one row and preserve the light surface. The live host browser
also displayed the corrected opaque dark background and subdued border.

The first narrow fixture attempted to resize a hidden window without waiting for
Chromium's viewport change. An explicit width check rejected that evidence; the
replacement uses independently initialized windows and verifies the actual CSS
viewport. This test does not certify physical DPI, screen readers, all themes or
all requirement states. The older running host controller still reports its
known legacy setup API mismatch; backend activation remains a separate boundary
operation. The private screenshot is excluded from publication.

## Startup under delayed APIs — 7 October

`tests/test-startup-renderer.js` loads the actual application assets in separate
hidden Chromium windows behind an isolated loopback fixture. Profile reads stay
pending. The fixture permits only the fake setup-observation bootstrap; setup
commands and gameplay requests fail the check. External requests are blocked.

Four cases pass: Off on repeat launch, Full on first launch, software-rendered
guest mode, and a controller timeout followed by explicit Retry. The latter
three use Chromium's 4x CPU throttle. Navigation and the app shell are present
while the profile request is pending. Off hides branding immediately; the guest
selects reduced motion; the eight-second controller deadline exposes recovery
and a subsequent ready response resolves it.

The fixture initially stalled because it sent an Emulation command before
initializing a renderer. It also needed an explicit last-window lifecycle and
the actual setup-session observation contract. Those fixture defects were fixed;
no application or replay code changed. The final run observed shell initialization
at 105–481 ms and all four recovery assertions passed. Idle frame samples are
diagnostic only and do not establish animation performance or physical 60 FPS.
Clean-machine launch, weak physical hardware, Windows DPI and screen-reader
acceptance remain open. The active missing-medal replay was not interrupted.

## Native/coordinator recovery contract — 7 October

`tests/test_installer_protocol_integration.py` connects the compiled production
`SetupControllerClient` to the actual Node setup controller and session modules
through a private loopback listener. Native port, process and executable ownership
checks remain enabled. Only environment observations and operators are faked;
the fixture imports no VM or game operator and writes only inside its temporary
installation root.

The joint check covers waiting for a healthy replay, exactly one start after an
idle observation, measured download bytes, cancellation while work remains active,
resume after a terminal observation, native-client reconnect without duplicate
work, removal of stale byte progress, Restart Later persistence and release only
after fresh validated readiness. A separate negative check removes the replay
guard from an isolated source copy; native acceptance rejects it before continuing.
The production files are unchanged.

Both checks pass. The first negative-fixture attempt let an unhandled native
exception invoke Windows error handling; it timed out. The harness now catches
and reports assertion failures explicitly. This fixture repair changes no product
behavior. These checks close a cross-language protocol evidence gap, but do not
prove actual dependency installation, VM provisioning, UAC decline, physical reboot
recovery or clean-machine readiness. Those production gates remain open.

The complete Python suite subsequently passed 399 tests. Existing JavaScript
controller, session, setup-phase and source-selection-guard checks also passed;
the publication guard found no private-file findings. No installer binary or
runtime changed in this acceptance batch.

## Completed milestones during recovery — 7 October

The approved progress contract requires completed work to remain visible during
rechecks. A new native regression reproduced both local and environment progress
resetting when the same session retried an earlier stage. `ObserveMilestone` and
`ObserveEnvironmentWeight` overwrote the persisted total with the latest stage's
lower value.

Both methods now retain the greater completed milestone for the current session.
Unknown current-stage progress remains indeterminate, and readiness still requires
fresh validation. The final five units stay reserved; reopening retains completed
work, while a new operation after completion gets a new session and zero progress.
No VM, game, save, permission or scheduled-task behavior changed.

The local and environment cases failed before repair. Restoring only the old
environment update after repairing local milestones also reproduced its separate
failure; the final repair passes both cases. The complete suite passes 400 Python
tests and 65 approved JavaScript check files. Packaging and public release identity
are checked separately; this does not close clean-machine or physical reboot gates.

The prepared `v0.1.11-preview.99` installer contains 246,915,052 bytes. All 126
runtime source comparisons and 1,705 inventory hashes match; its appended payload
matches the checked archive byte for byte. Both executable icons contain the seven
exact application frames. Staged app/lock/inventory and native embedded package
resource versions agree. Source dependency metadata is unchanged, and publication
guards report zero findings.
The pending ABR draft is retained only in the worktree; packaging uses its committed
version. During preparation, public download metadata retained the previous release
until publication was independently confirmed. Native progress changes do not reload
the healthy guest.

The single installer asset is now published under `v0.1.11-preview.99`; GitHub's
uploaded size/state and digest match the archived build. Download fallback metadata
and the local Preview 99 selector were updated only after that confirmation. The
previous v0.1.10 archive is retained. These publication checks do not close the
remaining production acceptance gates.

## Native shared-details redaction — 7 October 2026

The approved diagnostics acceptance exposed quoted-field leaks in the native
redactor. JSON and Python field names prevented its old assignment pattern from
matching credentials; escaped quotes and truncated strings could also expose
remaining secret text. The production native helper now consumes those values
and removes account/player/session identifiers in structured fields.

The compiled regression failed before each repair, then passed ten complete-field
cases and three truncated-string cases. Complete-field cases retain map/round
context and are idempotent. Both native Copy and Export use `SharedDetails`, which
calls this helper. The app's separate shared-log helper remains unchanged pending
its design approval. Broader save-content and arbitrary-PII acceptance remain
open; this is not an exhaustive privacy certification.

Fresh verification passed 401 Python tests and all 65 approved JavaScript check
files. Three isolated Electron fixtures needed their usual renderer permission
outside the sandbox; they passed there without accessing the guest or game.
The prepared v0.1.12-preview.99 installer is 246,919,920 bytes. Its 126 runtime
comparisons, 1,707 inventory hashes, four staged identities, actual native embedded
identity and both seven-frame application icons pass. The prior installer archive
is retained, and the pending ABR draft was excluded from packaging.
