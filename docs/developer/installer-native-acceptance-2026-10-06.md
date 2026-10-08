# Native package acceptance — 6 October 2026

## Purpose and isolation

Exercise the published v0.1.8-preview.99 package with the actual native installer
engine and Windows operations, including private Python dependency creation,
inventory validation and repair of an intentionally corrupted application file.
The harness disables shortcuts, app launch and environment/VM setup. It uses a
fresh application/data root and requires the host's existing C++ runtime rather
than installing a global dependency. No game or save input is involved.

This is existing-Windows package acceptance. It cannot prove clean Windows
provisioning, UAC/reboot handling, first-time Steam sign-in or accessibility.

## Observed failures

1. A deeply nested acceptance root exceeded the native Windows path limit during
   file deployment. The native engine returned a failure instead of completion.
   Keep long custom installation paths open as a separate acceptance case.
2. A fresh, normal-length isolated root failed while saving its session at the
   start of file deployment. The stack locates the failure in
   `InstallSession.AtomicWrite`, specifically `File.Replace`; package extraction
   and Python setup did not complete. The HRESULT was `0x80070497`, Windows error
   1175, “Unable to remove the file to be replaced.”

A separate read-only diagnostic exercised the same production atomic-write
method with temporary application-owned data: 1,000 writes in the workspace and
1,000 in a Windows temporary directory. The workspace case reproduced one
error 1175; a new attempt after 50 ms succeeded. The temporary-directory case
reported no failures. This establishes a transient replacement failure under
the observed workspace conditions; it does not establish which external reader
or service held the file, or that every installation encounters the problem.

3. A later attempt deployed the actual packaged files and entered native Python
   setup. Dependency installation then failed on a TensorFlow header whose
   complete filename was 262 characters. Windows long-path support was observed
   disabled. The isolated app root was 74 characters; the equivalent filename
   at the host's default installation root would be 247 characters. A read-only
   scan of 14,855 existing TensorFlow files identified that same header as the
   longest observed filename. This is evidence for custom-path validation,
   not evidence that the normal default path fails.

The next attempt used a root closer to the normal default length and passed the
real install and repair. The previous failures remain recorded. No registry
setting, production retry behavior or
game state was changed for these checks. Excluding private scratch roots from
Git was necessary to prevent generated sessions/environments from appearing as
untracked public-source candidates; it does not prove a cause for error 1175.

Microsoft documents that error 1175 retains the original filenames of the
replaced and replacement files. Errors 1176 and 1177 have different recovery
semantics and must not be treated as interchangeable.
[ReplaceFile documentation](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-replacefilea).

Long-path support depends on Windows configuration and the application's
opt-in; it cannot be inferred from Windows 11 alone.
[Windows path-limit documentation](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation).

## Acceptance status

- Native engine failure propagation and retained diagnostics were observed.
- Actual native installation and repair passed at the shorter isolated root,
  using the published package and unmodified native operations. The engine
  wrote successful completion and attempt receipts, and its session reached
  validated completion.
- Fresh native probes imported the installed image-processing, TensorFlow and
  keyboard dependencies with the pinned package checks. The published inventory
  was healthy. After deliberate corruption, repair restored the exact packaged
  `server.js`, retained an unlisted application configuration sentinel and reused
  the healthy private Python environment. No app, shortcut or VM was launched.
- The isolated probe supplies evidence for a bounded checkpoint/journal
  replacement repair; the design is awaiting approval. No production repair has
  been applied from this experiment.
- The active missing-medal replay was not interrupted. This test never launches
  an app, changes an existing VM, edits game data or creates user shortcuts.
- Keep private harness paths, logs and generated environments out of public
  source and installers. Only this account-free evidence summary is published.

## Native keyboard follow-up

The actual WinForms view passed forward and reverse selection at welcome, expanded
Options, busy download, expanded details and failed setup in both themes. The
checks use native `SelectNextControl`, verify wrapping and accessible names/roles,
and exclude hidden or disabled controls. During active work, Pause setup and
details remain reachable. The windows stay offscreen and receive no global
keyboard input. The full Python suite passed **395 tests** after adding this
coverage. This establishes the native control contract, not physical keyboard,
screen-reader, Windows DPI or high-contrast acceptance.

## Next checks

### Native accessibility follow-up — 7 October

The actual status label's accessibility name previously returned only “Setup
status”, hiding the visible installation or recovery text. The new regression
failed on this behavior before the repair. The label now exposes its friendly
current observation and sends an MSAA name-change event when that text changes.
An own-process event listener verified those events in both themes and verified
that progress-only observations do not repeat the status notification. Measured
and unknown progress descriptions match the visible caption. Failure status uses
the same friendly text as the view; completion still distinguishes environment
defer from readiness. No test sends desktop input or captures another process's
accessibility events.

All four native view tests and the complete suite of 396 Python tests passed,
alongside all 64 approved JavaScript check files. These prove the native control
contract, not physical screen-reader speech, announcement priority, Windows DPI,
or weak-hardware performance. Those production gates remain open.

### Text-only scaling follow-up — 7 October

The approved native acceptance work reproduced clipped footer text at 125%
text scaling and an undersized action button at 150%. A new test exercises the
actual native view while enlarging its fonts without enlarging the window.
The footer now uses its content's preferred height, its note wraps within the
window, and the action buttons size to their labels.

Checks pass for both themes, default and minimum window sizes, six setup states
and 100%, 125%, 150% and 200% text scaling. They compare visible text controls'
preferred heights with their actual bounds and verify primary-action containment.
Rendered native frames retain the official Engineer art. These are isolated
font-scaling fixtures, not proof of Windows text-scale settings, per-monitor
DPI changes, physical screen-reader behavior or every scroll interaction.

### Actual process-tree interruption — 7 October

The new `test_installer_process_tree_interruption.py` compiles the complete production native
source list and uses `OwnedProcess.Start` to launch a fixture parent inside its
Windows job. That parent starts a longer-lived descendant and exits. The live
installer observer reports running, rejects terminal completion and refuses a
second installation. After interruption of the fixture installer itself, the
descendant remains alive and the reopened installation lock remains blocked.
The descendant then finishes naturally and writes its own terminal marker.
Only the fixture's own processes and temporary directory are used.

This passes the concurrency safety requirement. It does **not** prove complete
interruption recovery: the reopened observer reports unknown both while the
descendant survives and after it finishes, and still blocks another installer.
The lost observer does not provide an observed empty job or terminal receipt.
This recovery limitation remains open; unavailable process state must never be
converted into permission to start competing dependency work.

The first private harness incorrectly requested an exit code from a process
attached through `GetProcessById`, causing an unhandled fixture exception and an
observation timeout. The corrected harness observes exit plus its own terminal
marker and catches fixture exceptions explicitly. No production repair was
made to obtain a passing result.

The sandbox also denied the exact Windows Management Instrumentation boot-time
query. A separate read-only probe outside the sandbox confirmed that the
production boot reader succeeds. Repeating the process-tree probe there retained
the same safety and unknown-recovery observations with a known boot identity.
This does not exercise an actual reboot or prove boot detection on another PC.

A further isolated probe queried the exact fixture job name with
`OpenJobObject(JOB_OBJECT_QUERY)` at each boundary. It succeeds before the fixture
installer is interrupted. After that installer exits, the same call returns
Windows error **2** while the fixture descendant is independently confirmed
alive. It also returns error 2 after the descendant's natural exit. Both reopened
observations remain unknown and block a second installer; no production source
was changed to obtain this result.

This rules out treating a missing job name as evidence of an empty process tree.
Microsoft's [job-object documentation](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)
describes job lifetime in terms of handles and associated processes. The actual
probe establishes that reopening this fixture's name is unavailable at both
distinct states. Recovery needs durable observation that distinguishes those
states; a filename-not-found exception, receipt deletion or the direct parent's
exit alone cannot provide it. The probe touches only its own fixture processes,
which finish or are identity-checked before cleanup. Installer interruption
recovery remains an open production gate.

The focused process-tree test passes, and the complete Python discovery run
passes **402 tests**. No installed app, VM, Steam or game data was changed.

### Published-package selective removal — 7 October

The actual Preview 99 diagnostics hotfix archive was extracted through the
unmodified native `ReadEmbeddedPackage` and `InstallAppFiles` operations into
a fresh application-owned fixture directory. Its observed release identity
matched `0.1.12-preview.99`, and all 1,707 inventoried files passed integrity
inspection before the fixture modified its own `server.js`.

Selective removal deleted 1,706 unchanged inventoried files, including the
installed executable. The deliberately modified source remained. Unlisted
fixture configuration, a fixture route, unlisted user data and an adjacent
unrelated sentinel remained unchanged. The resulting installation correctly
reported unhealthy; repeating removal deleted no retained data.

An inventory containing a valid app entry followed by an escaping path was
rejected before any app removal. An already-held installation lock also blocked
another owner before removal. The same guarded native call sequence used by the
installer's confirmed uninstall action was exercised, but its interactive dialog
was not clicked and no fixture application was launched. No dependency, Steam,
game or VM provisioning occurred. This verifies the selective file-removal
contract, not running-app interaction or a complete clean-machine uninstall.

An initial private assertion compared equivalent Windows paths with different
slash forms and falsely flagged the retained modified source. Canonicalizing
that assertion corrected the fixture; the production operations were unchanged.
Only account-free observations are published. The fixture and extracted files
were removed from their verified application-owned temporary directory.

### Fresh prerequisite resolution — 7 October

The current prerequisite URLs were read from the production installer/setup
sources and checked against their upstream services. All four returned HTTP 200:
the Microsoft C++ runtime, Steam installer, pinned App Sandbox 0.1.9 archive and
pinned Fido 1.70 script. This is point-in-time availability evidence, not a
guarantee of future service uptime or a diagnosis of an older installer.

All 47 exact Python pins in `requirements-installer.txt` have an available,
non-yanked Python 3.12-compatible wheel or source distribution. Their selected
artifact headers match the declared sizes. A Windows dependency-metadata check
found no missing runtime pin or incompatible pinned requirement. A subsequent
actual pip resolution used `--dry-run --ignore-installed --isolated` with a new
private cache on Windows CPython 3.12.14; it resolved exactly those 47 packages,
including TensorFlow, without changing the existing environment.

Six pins require source builds on this platform: MouseInfo, PyAutoGUI,
PyGetWindow, PyRect, PyScreeze and pytweening. Each built a wheel successfully in
the isolated audit using the pinned version and `pip wheel --no-deps`. This
exercises their build paths, not their game-input behavior. Download/build cache
files and raw tool output remain private and outside the installer.

The unmodified pinned Fido script was then run with the same command-line
selection as setup: Windows 11, latest release, Pro, English, x64, URL only.
It exited successfully and supplied a Microsoft-hosted ISO link whose HEAD
request returned HTTP 200 and a size above 8 GB. No ISO was downloaded, browser
or selection dialog opened, or Windows installation started. The temporary
signed URL is not included in source or reports.

The actual App Sandbox ZIP also passed CRC inspection and contains the expected
root executable, ISO patcher and `headless-api` directory. It was inspected in
memory without extraction or execution. No current 404 or dependency-resolution
failure was reproduced. This closes this download/resolution observation; it
does not resolve the earlier `bcdboot` fixture failure or establish clean Windows
installation, UAC/reboot, physical accessibility or complete VM provisioning.

### Remaining recovery checks

After the approved checkpoint repair, repeat these checks and add deterministic
bounded-retry and persistent-error coverage before changing product code.
Custom-path preflight also remains open: a successful shorter root does not
resolve the observed 262-character dependency path. Preserve the existing
atomicity, ownership and recovery rules.

Then finish the separate clean supported Windows, UAC/reboot, complete VM
provisioning and physical accessibility gates. Successful fixture checks or a
temporary-root install do not close those gates.

### Installed Python work during replacement — 7 October

The approved installer ownership contract now observes all four exact installed
Python and Pythonw paths in the private environment and bundled runtime. An
active interpreter blocks update, repair or uninstall before installed files
change. Python is observed only; the installer does not terminate it. Unrelated
interpreters, including a similarly named adjacent installation, remain outside
the guard. Unknown observations still block installation.

An actual native fixture first reproduced the missing-controller case: installed
Python survived, but replacement was allowed. A second fixture reproduced the
shutdown race: an exact fixture controller started Python while its idle status
was read, then exited while its child remained. Both now block file changes.
The second observation occurs after confirmed controller shutdown. The fixture
uses the production shutdown sequence with an isolated status reader, so it
never contacts the live controller on port 4173. It verifies that Python survives
and stops only its own exact executable in cleanup.

Independent review found the shutdown race, then confirmed its repair. This
closes the two observed interpreter-ownership gaps; it does not fence applications
independently launched during later installation stages, prove a clean-machine
installation or require any running VM to reload.

### Separate clean Windows attempts — 7 October

Two separate, fresh App Sandbox fixtures were requested with an existing Windows
11 ISO, 4 GB RAM, two CPU cores, a 64 GB disk and no GPU sharing. Capacity was
checked first. Neither fixture cloned the gameplay VM or copied game/profile
data. The active gameplay VM remained online and its missing-medal replay
continued during both attempts.

Both builds failed in App Sandbox before Windows became ready and before the
Bloons+ installer was copied or executed. The backend reported `bcdboot` exit
code **183**, removed each failed fixture from its VM list, and recorded
`BcdOpenStore` failures with status `c0000035`. The second build reached an
observed 94% before that failure. A fresh name did not resolve it. No host boot
store, registry hive, BitLocker setting, existing VM disk or daemon privilege
was changed to work around it. This is a failed clean-environment prerequisite,
not a clean-install pass or a Bloons+ installer crash.

The approved setup-diagnostics contract now retains this specific observed
failure instead of replacing it with a generic vanished-VM message and building
three images automatically. It reads at most 64 KiB of newly appended backend
log data, matches the exact requested VM, and exposes only the numeric boot-file
error. Old entries, unrelated VMs and replaced/truncated logs cannot supply the
diagnosis. Unknown disappearances keep their existing bounded retry behavior.
Four offline regressions cover those boundaries; the failure was reproduced
before the repair. The clean Windows, UAC/reboot and Steam/bridge gates remain
open, and the boot-store failure itself remains unresolved.

### Read-only boot-store follow-up — 7 October

A direct query of `BCD00000000` returned Windows access-denied code 5 in both
registry views. That result cannot be treated as evidence that the hive is
absent. A separate read of Windows' hive list showed it registered to the normal
EFI Microsoft boot store, outside App Sandbox's path. No boot-store path,
identifier or account detail is published. No hive was unloaded or changed.

The installed BCDBoot help lists `/offline`; both attempted builders had already
tried that option. Microsoft's [BCDBoot documentation](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/bcdboot-command-line-options-techref-di?view=windows-11)
describes it as offline boot-file servicing and documents that `/s` avoids
creating a firmware entry. This does not establish that either option repairs
the observed `BcdOpenStore` collision. The hive-list observation likewise does
not prove the full root cause. Further clean-VM work needs a safe, evidenced
provisioning path; another blind image build or changing this PC's boot store
would not close the acceptance gate.

### Upstream diagnosis check — 7 October

The current upstream `iso-patch.c` history was checked again. Its latest touching
commit, [`6d2e10f`](https://github.com/jamesstringer90/appsandbox/blob/6d2e10fd0bd6b67994b6ed3beccf5a8bc190590d/tools/iso-patch/iso-patch.c),
still invokes the host BCDBoot executable against the new image's Windows and
EFI volumes. It supplies `/s` and `/f UEFI`; no separate registry namespace or
new recovery path was added there. The upstream issue previously referenced in
a local comment, [issue 62](https://github.com/jamesstringer90/appsandbox/issues/62),
reports exit **193**, not the observed **183**, and does not establish a
same-name-remnant cause or a successful fix. That unsupported comment is removed;
runtime behavior is unchanged.

The retained failing log narrows the boundary further: template access and boot
file copying precede the failed creation/loading of the destination BCD store
under `BCD00000000`. Both `/offline` attempts reach the same `c0000035` load-key
failure. Thus changing locale or using another VM name has already failed to
address this boundary. This is evidence about the failing operation, not proof
of why Windows rejects it. No host hive, firmware setting or boot store was
changed, and no third full-image retry was launched. Clean provisioning remains
an open production gate requiring an independently isolated, evidenced repair.

### Offline boot-template investigation — 7 October

A private diagnostic compiled the existing `bcd_patch` implementation from the
locally installed App Sandbox macOS source, with only the Windows spelling of
`strcasecmp` adapted. It processed a read-only copy of the guest's generic
Windows BCD template: 28,672 input bytes became a 36,864-byte output file. Neither
file was installed as an active boot store. No host boot settings, firmware,
partition contents, game files or save files were changed.

An independent structural walk found valid base-block checksums, matching
sequence numbers, matching bin lengths and bounded cell sizes in both files.
The generated store contains eight bins and 551 cells. These are structural
observations, not proof that the guest can boot.

The unprivileged host's BCDEdit could not open either private file; its private
application-hive API also returned the same error for both the original and the
generated file. These results cannot distinguish a generator defect from the
validation environment. Read-only guest BCDEdit enumeration of the explicitly
named temporary files succeeded. A second generated file using observed guest
partition identifiers resolved its loader device and OS device to the intended
Windows partition and exposed `winload.efi` when queried by exact object ID.
No partition identifiers or temporary files are included in public packages.

The loader is labelled **OS Target Template** and omitted from ordinary all-object
enumeration, although the exact-object read succeeds. The initial hypothesis
that the object was absent was therefore rejected. Template-object identity,
loader cloning, x64 semantics, malformed-input handling and actual boot remain
unproven. The macOS builder is not being shipped as a Windows fallback.

The user approved an isolated prototype using Windows' own tools on a copied
per-image boot template, followed by a separate empty test VM. Every BCDEdit
operation must use an explicit private store path; the host boot configuration
and existing gameplay VM configuration remain outside this experiment.

The first copied-file experiment exposed a narrower prerequisite: cloning the
OS target template fails with “existing display order / Element not found” when
the source template has no display order. Initializing that order first allowed
all 11 configure/read-back operations to succeed: clone the loader, set its
device and OS device, set its loader path and system root, configure the copied
boot manager, select the default/order/timeout, then enumerate the store. The
input template's SHA-256 stayed unchanged. These operations affected only a
private disposable file, never an active boot store.

The initial host probe was canceled at Windows administrator consent. On
8 October the user explicitly requested the prompt again and accepted it.
All 11 host copied-store configure/read-back operations returned exit code zero;
the receipt records no error and the original template hash is unchanged.
Every command uses an explicit private `/store` path, and the probe refuses to
overwrite an existing output. Host boot configuration and the existing game VM
remain outside the probe. An actual separate-fixture boot is still required;
this is not yet a production fallback or a successful clean-install claim.

## Retained dependency observer — 7 October

The approved native ownership/recovery contract now uses a hidden transient mode
of the same installer executable to retain a query-only Windows job handle. It
handshakes before a dependency starts, waits until the launch attempt ends or its
exact parent exits, then records an atomic, exact-job empty observation. The
observer does not declare installation success; normal component checks remain
required. It adds no service or runtime and never kills a dependency.

The real process-tree interruption fixture first reproduced permanent unknown
ownership after the surviving descendant exited. With the observer, installation
remains blocked while that descendant lives and becomes idle for recovery after
its natural exit. Killing the observer as well leaves ownership unknown and
blocked. A failed startup handshake prevents the dependency from launching;
stale/malformed receipts cannot establish idle. All 48 installer checks and the
full 409-test Python suite pass. An independent reviewer found no actionable
findings. Clean-machine and broader interruption gates remain.

### Owner exit before dependency launch

An additional native fixture now pauses at the handshake-to-launch boundary.
It creates an isolated named job and the same pending receipt as production,
then invokes the unchanged production observer. While the exact owner remains
alive, six hundred milliseconds of repeated checks show no empty observation;
a second installer is blocked. After terminating only that fixture owner, the
observer records an empty job and recovery becomes idle. The receipt still has
neither a terminal-success claim nor a dependency exit code.

Two private source copies confirm the test detects broken behavior: permitting
empty observation before launch fails the pending-owner assertions; removing
owner-exit detection fails the eventual-idle assertion. Negative-control cleanup
signals only its own named launch event so a deliberately broken helper cannot
linger. The initial negative-control run exposed that fixture-cleanup omission;
it was corrected without changing production behavior.

This exercises the real observer and recovery reader at a deterministic boundary,
not a physical power interruption or a timed kill inside `OwnedProcess.Start`.
The final full Python suite passes 410 checks, including all 49 installer checks;
both private negative controls also fail for their expected behavior assertions.

### Boot identity in the prelaunch fixture

A later complete suite outside the restricted execution sandbox reproduced a
fixture defect: its receipt used `fixture-boot`, while the actual install lock
could read Windows' real boot identity. The deliberate mismatch correctly took
the installer's reboot-recovery branch and invalidated the fixture's expectation
that a second installer remain blocked. It was not a new installer ownership
failure.

The fixture now uses the production boot identity for both its receipt and
observer. The isolated check failed before this correction and passed afterward.
Both private negative controls still fail for their intended premature-empty and
missing-owner-exit assertions. Production ownership and reboot behavior were not
changed. This correction does not prove physical reboot acceptance.

### Transfer-manifest packaging boundary

The staged installer contained an untracked `.scp-list.txt` deployment manifest.
Inspection found a list of filenames, with no absolute paths or the checked
private-runtime filenames; no credential exposure was established. The manifest
has no role in an installed app.

The approved packaging cleanup now excludes it at the root and inside copied
directories. Private filename comparisons are case-insensitive, matching Windows
behavior. An independent publication guard rejects the manifest even if an
archive is assembled through another path. Synthetic regressions first reproduced
both the staging and guard gaps, then passed. They also retain the public license
and third-party notice paths. Independent review found no actionable issue in
this bounded packaging change.

The rebuilt `0.1.17-preview.99` artifact contains no transfer manifest. Its 127
runtime source comparisons, all 1,714 inventory hashes, four package identities,
native embedded inventory, both seven-frame executable icons and exact appended
ZIP payload pass inspection. License notices remain intact and the separately
pending route draft is excluded. This verifies the artifact, not a clean Windows
installation or resolution of the outstanding gameplay failures.

### Real HTTP download boundaries — 7 October

`tests/test-setup-download-http.js` exercises the unchanged setup downloader
against a real loopback HTTP server, including a socket closed during transfer.
It verifies exact-byte resume, refusal of an incorrect range, preserved completed
and partial files after HTTP 404 or a failed fresh retry, a fresh request after
416, replacement when a server ignores Range, and a chunked response with no
known total. A fifteen-second fixture watchdog closes sockets; cleanup removes
only the test's own temporary directory. The existing mocked range checks also
pass.

`tests/test_installer_download_http.py` compiles the unchanged native installer
sources and feeds actual `HttpWebResponse` streams into `CopyRuntimeDownload`.
It covers complete and chunked copies, truncated bodies, HTML responses,
oversized declared lengths, HTTP 404 and cancellation from the progress callback.
Oversized declarations must fail before any stream read or output write.
Cancellation must stop after the first read, leaving incomplete output.

Six isolated negative controls prove the assertions catch broken behavior:
truncating resumed output, ignoring HTTP 404, omitting the native length check,
omitting the executable-header check, removing the initial size bound, and
deferring cancellation until the final callback. An independent review found
the last two cases initially allowed false positives; the assertions were
strengthened, and all six controls now fail for their intended reasons. The
reviewed production-source fixtures pass, as does the existing native runtime
and controller guard check.

No product behavior changes, external downloads, installer execution, UAC
actions or gameplay inputs occur in these tests. They verify transfer handling
and the existing executable-header boundary, not publisher signatures, the real
Microsoft redirect/TLS path, complete installation, reboot recovery or clean
Windows acceptance. Those remain separate production gates.

After integrating these fixtures, the complete Python suite passed 423 tests
and all 72 approved JavaScript test files passed. The unpublished ABR draft
test remains excluded. No installer build or live runtime deployment was
performed for this test-only batch.

### Locked package rollback and fresh-process retry

`tests/test_installer_locked_rollback.py` compiles the unchanged production native
installer code and applies a three-file package in isolated temporary folders.
Each file position is held open with a real Windows sharing mode that permits
hash reads but denies replacement or deletion. Recovery restores the unlocked
files, reports incomplete rollback, and retains the journal and required backup
for the locked file. The fixture exits without unwinding the lock scope.

Separate processes then recover, repeat recovery, and install the next package.
The prior files are restored, the introduced file is removed, and unlisted user
data remains intact. Recovery clears the journal, staged/backup files and
transaction directory. A subsequent full package installation succeeds.

Two private negative controls demonstrate regression sensitivity: suppressing
the incomplete-rollback error fails the initial assertion; rejecting files that
were already restored fails recovery in the next process. Neither mutation was
applied to production source. Independent review found no important issue; its
suggested transaction-directory cleanup assertion was added.

All 420 Python checks passed before that additional assertion; the strengthened
focused fixture also passes. This closes a bounded file-lock recovery check,
not the entire I-03 gate. It does not simulate physical power loss, a reboot, or
interruption inside an individual filesystem operation. No installed app, VM,
Steam directory or game save is modified by this fixture.


### Process exit inside the production deployment pipeline

The new `test_installer_deployment_exit.py` compiles the unchanged production
native sources and executes `InstallAppFiles` on a three-file synthetic package.
The fixture process exits without unwinding at three deterministic boundaries:
after the first file is staged, after the prepared journal is durable, and after
the first real replacement returns. Unlike the earlier manually assembled
transaction fixture, these checkpoints are reached through the actual deployment
pipeline. No installed app, VM, game, save, shortcut or global dependency is used.

Before recovery, the parent verifies the expected journal phase and exact file
contents, including the mixed old/new state after the first replacement. Fresh
processes recover twice and then install the package successfully. Original and
unlisted user data are preserved, an uncommitted new file stays absent, and both
recovery and successful retry remove their transaction directories and journals.

Both private negative controls fail the intended original-content assertion:
removing recovery entirely, and skipping the prepared transaction's restoration.
These mutations were confined to temporary source copies. Independent review
found no blocker and requested the successful-retry staging cleanup assertion;
that strengthened focused check passes. All **53 native installer tests** and
the complete **427-test Python suite** pass.

This establishes recovery at these observed process boundaries. It does not
simulate physical power loss, a torn filesystem operation, a reboot, a killed
external dependency or every setup phase. The checkpoint-write retry, long
custom paths and clean-machine acceptance remain open.

### Current custom-path budget observation

A read-only scan of the Preview 30 payload finds its longest installed relative
filename is 136 characters. The observed TensorFlow runtime includes a filename
whose complete suffix below the install root is 201 characters, including
`resources\app\.venv`. With a 259-character full-path budget, the root plus
separator leaves only **57 characters** for that observed dependency path,
compared with 122 for the payload. Copying the bundled app successfully therefore
does not establish that its subsequently downloaded Python dependencies will fit.

This is measured evidence for a dependency-aware preflight design, not a newly
implemented path restriction. It does not certify every wheel, generated cache
file, long-path-enabled application or Windows configuration. No registry,
installation location or runtime setting was changed by the scan.

### App deployment capacity preflight — 7 October

The native file deployment now checks installation-drive free space before
creating a new staging transaction. It counts changed archive contents and the
existing files' rollback copies, plus a 16 MiB metadata/allocation allowance.
Files whose exact content already matches the archive need no extra copy.
Insufficient capacity reports the required free-space total and leaves the
installed app unchanged. Pending transaction recovery still runs first.

The compiled production deployment fixture rejects a one-byte shortfall before
creating transaction state, accepts the exact threshold, and reuses unchanged
files without budgeting duplicate copies. Unlisted user data is preserved in all
three cases. All 54 native installer tests and the full 428-test Python suite
pass; independent review found no blocker. This is an app-file preflight;
the separate Python runtime space check remains, and dependency-wide capacity,
custom-path handling and clean-machine acceptance are still open. Concurrent
disk consumption can still cause an I/O failure; transaction recovery remains
necessary.

Preview `v0.1.31-preview.99` package checks pass: 247,033,650-byte installer,
127 runtime-source comparisons, all 1,738 inventory hashes, four version
identities, exact appended payload and seven exact icon frames for both the
installer and app. Publication scanning reports zero findings; the pending
Sunken Columns draft is excluded. No guest installation was performed for this
batch.

### Approved checkpoint replacement retry — 7 October

The user approved the bounded persistence design after returning. Session
checkpoint replacement now retries only Win32 sharing/lock errors 32/33 and
the observed error 1175. Four total attempts use 50/100/200 ms backoff, and a
retry requires both original filenames still to exist. Errors 1176/1177 and
permission error 5 propagate immediately; no delete-and-replace fallback or
permission change is used.

The compiled fixture covers successful and persistent failures for all six
codes, a disappearing replacement file, a real temporary Windows file lock,
a persistent lock, the prior receipt and temporary-file cleanup. All 55 native
installer tests pass, and independent review repeated the focused check without
finding a blocker. This repairs the evidenced transient boundary; it does not
claim recovery from every replacement error or complete clean-Windows setup.
The complete 429-test Python suite also passes, and publication scanning reports
zero findings.

Published as `v0.1.32-preview.99`: the 247,035,235-byte installer passes 127
runtime comparisons, all 1,739 inventory hashes, four version identities, exact
appended-payload verification and both seven-frame icon comparisons. Its single
GitHub asset matches the local size and digest. No guest update was performed
during the recovered healthy missing-medal replay.

### Approved deep Python package paths — 7 October

The native setup now uses extended Windows executable spelling only for pip's
install and force-reinstall operations. Venv creation, ensurepip, runtime checks
and app execution keep their normal paths. Ownership receipts normalize the two
spellings before comparing the executable, while retaining the existing PID,
creation-time and job-observer checks. No Windows registry setting is changed.

Before the repair, the compiled native fixture failed with WinError 206 while
installing a synthetic wheel whose header path exceeded 260 characters. The
process identity fixture separately rejected the extended executable spelling.
Both now pass, including healthy reuse, deliberately damaged-package repair,
concurrent-install rejection and the observer's natural exit. UNC spelling and
device-namespace rejection have lexical coverage; no network-share install is
claimed.

The actual production `ConfigurePython` method also completed fresh installation,
healthy reuse and force-reinstall after a deliberately removed dependency file,
using all pinned requirements in an isolated 88-character installation root.
The observed deepest TensorFlow header consequently had a 290-character path.
Normal-path runtime imports and `pip check` passed after installation and repair.
The complete **431-test Python suite** passes; independent review found no
actionable issue. No installed app, VM, game or save was changed by these checks.

This closes the observed deep-wheel failure at a custom root whose application
files and Python launcher still fit the existing path limits. It does not claim
arbitrarily long application roots, network-share installation, clean Windows,
physical reboot recovery or all installer acceptance gates.

Published as `v0.1.35-preview.99`: the 247,045,045-byte installer passes 128
source comparisons, all 1,745 inventory hashes, four version identities, exact
appended-payload verification and both seven-frame icon comparisons. Its sole
GitHub asset matches the local size and digest. No guest update was performed.

### Failed dependency update and fresh-process retry — 7 October

The new isolated check compiles the unchanged native sources and calls the actual
`ConfigurePython` operation in four separate processes. Real pip installs a tiny
local wheel into a temporary private environment. The requirements then add a
second wheel that is deliberately unavailable. Installation fails with the
specific missing-distribution diagnostic and the native dependency-failure
message; it does not certify the changed requirements as installed.

After providing that wheel, a fresh process succeeds and writes the new verified
requirements receipt. The original package's bytes and modification time, an
unlisted environment marker and application configuration remain unchanged.
No replacement environment is created. A fourth process reports healthy reuse.
All package sources are offline; inherited pip settings are removed and pip
configuration is disabled to prevent installation outside the fixture.

The focused check passes under Python 3.12. A private copy that prematurely
writes a successful requirements receipt fails the intended preservation
assertion. Independent review found no remaining blocking issue after isolating
pip settings and adding fixture-process-tree cleanup on timeout. No installed
app, VM, Steam, game, save or global Python environment is modified.

This verifies one real dependency-resolution failure and retry through the native
pipeline. It does not establish physical power-loss, arbitrary interrupted pip
transactions, external network recovery, clean Windows setup or reboot behavior.
No production installer behavior changed for this acceptance batch.

### Packaged install, repair and fresh native handoff — 8 October

The published Preview .38 package completed a fresh isolated installation and
repair through the actual native Windows operations. Python dependency imports
passed, the deliberately damaged controller file was restored, and unlisted
configuration remained unchanged. This used the existing host C++ runtime;
shortcuts, normal app launch and VM setup were disabled.

An observation-only connection from the native client to that installed
controller exposed two defects: a valid 239-character handoff destination
generated a 276-character temporary path, and a fresh checkpoint returned null
operation flags that the native client could not consume as booleans.

The checkpoint repair generates its temporary basename independently and fits it
within the remaining Windows path budget. CreateNew collisions have a 16-attempt
limit; cleanup applies only to a file created by this writer. Flush(true),
same-directory atomic replacement and the existing replacement retry policy are
retained. Regression checks cover a long destination name, a long directory with
`session.json`, a reduced basename budget, Unicode, locked replacement, collision
retry/exhaustion, original bytes and unrelated-file preservation. The original
failure and the additional reviewer-found layout both failed before their fixes.
Fresh setup snapshots now expose explicit false flags while preserving checkpoint
identity matching and sequence checks; their regression also failed before repair.

The final reviewed Preview .39 artifact passed a new actual native install and
repair, runtime imports, configuration preservation and inventory validation.
The installed packaged controller then passed the native authenticated loopback
connection and observation with a private fresh profile. Owner, executable, PID,
version and session identities matched; sequence advanced; all three operation
flags were false. A missing VM remained explicitly not ready, and no setup
operation, desktop window or gameplay was started. The exact fixture controller
exited afterward.

All **437 Python tests** and **85 approved JavaScript suites** pass. An earlier
broad Python run completed its assertions but failed when deleting a temporary
observer executable before its natural exit; the focused two-case rerun and final
full run passed. That first result is retained privately. Independent review
found no remaining critical or important finding in the two production repairs.

The .39 installer has 128 matching runtime-source comparisons, 1,749 valid
inventory hashes, four matching version identities, an exact embedded payload
and both seven-frame application icons. Source and payload publication guards
report zero findings. The unrelated pending ABR draft is excluded from the
artifact. These checks do not establish clean Windows/VM provisioning, physical
reboot recovery, arbitrary application path lengths or first-launch accessibility.

Published as [v0.1.39-preview.99](https://github.com/Klaasawastaken/BloonsPlus/releases/tag/v0.1.39-preview.99).
GitHub's sole installer asset matches the checked 247,064,282-byte artifact and
its local digest. Download metadata now points to this release. The production
1.0 gates remain open; no full guest update or gameplay occurred in this batch.

### Installed assets: startup, preferences and connection retry — 8 October

A new isolated profile loaded the unchanged .39 application assets from the
actual packaged setup-only controller. The hidden renderer used the matching
original Electron 33.4.11 runtime. A fresh launch exposed the shell, showed then
dismissed the default Full branding, kept Settings reachable and showed the observed missing
environment as actionable. The real coordinator remained idle with validation
false and explicit false operation flags. Changing the actual intro dropdown to
Off persisted; reopening the window retained the setting and omitted branding.

Temporarily blocking only the controller identity request exposed the actual
connection diagnostic and Retry button without disabling navigation. Restoring
that request and pressing Retry recovered readiness against the same controller.
All three scenarios pass, with no uncaught renderer error or prohibited mutation
request. Only reads and same-origin observation-session bootstrap were allowed;
no VM/setup commands or gameplay ran. The exact fixture processes exited.
Review strengthened cleanup so an error for one owned process cannot skip
the other; four isolated cleanup checks cover that case and bounded timeout
handling. The final actual integration run passes, and independent re-review
found no remaining important finding.

The first harness attempt incorrectly assumed packaged Electron accepts an
alternate main script. It ignored that argument and safely exited on the fixture
controller's occupied port in setup-only mode. A second fixture error used the
wrong Settings element ID. Both initial results remain private; the corrected
first/repeat and recovery checks pass. These observations cover installed assets
and the real setup coordinator, not the packaged main-process window launch,
clean Windows, physical accessibility or a fully provisioned guest.

### Existing idle guest update and runtime map health — 8 October

The normal authenticated updater applied the exact published .39 installer to
the existing idle VM and finished with a verified app connection. The guest
controller reports .39. The account identity, existing app task principal,
configuration and failure-history files, and all 205 existing CHIMPS file hashes
are unchanged. No gameplay was started, earned medals or attempt budgets reset,
or SSH/task privileges changed. This was an update of the existing environment,
not a clean Windows installation.

The installed inventory matches 1,748 of its 1,749 entries. The remaining file,
the runtime map table, is valid JSON with one added map and three updated tile
positions. The existing app intentionally synchronizes this file from its
catalog and learned coordinates. The original native inventory nevertheless
classifies that normal change as damaged installation data.

A synthetic native regression reproduced the false repair warning. The bounded
repair validates only that exact map table's structure, with a 2 MiB size limit,
2,000-row limit, bounded JSON depth, map identifiers, category/name fields and
integer page/tile positions. Other required files retain their SHA checks.
Missing or malformed map data remains unhealthy. Separate native checks accept
both the public defaults and the privately retained live table. Independent
review found a trailing-newline identifier gap; its regression failed before
strict whole-string anchors corrected it. Row-count and nesting limits also have
direct negative cases, and final review is clear.

The host's existing image helper differs from the packaged helper, so overall
environment validation remains false even though the guest update completed.
The normal packaged app process and controller are present; physical window
acceptance is not claimed from cross-session process observations. Clean guest
boot still depends on the prepared fixture-only repair whose administrator
prompt was canceled.


Final runtime-map health acceptance passes all **438 Python tests** and the
**85 approved JavaScript suites**. The native interruption fixture now waits
for its exact temporary observer executable to exit before deleting the test
directory; production process ownership and recovery rules are unchanged.
Independent read-only review found no remaining issues in the repair or its
regression fixtures.

The Preview 99 `.40` installer is **247,069,669 bytes**. All 128 runtime source
comparisons, 1,751 inventory hashes, four version identities, the embedded
installer identity, exact appended payload and both seven-frame icons pass.
Source and decompressed-payload privacy guards report zero findings. An actual
isolated native install and repair pass: pinned runtime imports work, a damaged
published file is restored and configuration is preserved. These checks did
not request VM setup, launch the app or create shortcuts; they do not prove
clean Windows provisioning. The separate guest boot gate remains open.


Published as [v0.1.40-preview.99](https://github.com/Klaasawastaken/BloonsPlus/releases/tag/v0.1.40-preview.99),
with one installer asset matching the tested size and digest. Website download
metadata points to .40. Production 1.0 remains gated on clean setup acceptance.


### Existing host helper repair and packaged ready state — 8 October

The exact installed `.40` package's existing setup operator repaired the
observed host image-helper mismatch. It retained a private backup and installed
the checked published helper. A bounded acceptance driver permitted only that
step; it refused other setup operations. Its first attempt stopped before any
mutation because the fresh relay had not connected yet. A separate attempt
waited for read-only connection observations, required every other setup step to
be ready, then completed the helper repair.

Fresh before/after guest reads prove that the account identity, existing app task,
six persistent configuration/history files and all 205 original CHIMPS hashes
are unchanged. Steam and BTD6 remain ready; no gameplay, guest update, VM restart,
boot-disk repair, credential change or ACL change occurred.

A fresh setup-only process from the installed `.40` package then observed the
actual environment through the normal authenticated coordinator. Every observed
step is ready; the coordinator reaches `complete` with
`environmentValidated: true`, without starting a setup operation. Its validated
release endpoint closes that exact owned observer normally. This resolves the
previous helper mismatch and verifies the existing-environment ready path. It
does **not** close clean Windows provisioning or physical app-window acceptance.

Fresh requests to all four HTTP/HTTPS, root/www website variants return 200 and
exactly match the published `.40` download metadata.

### Production boot recovery and final candidate — 8 October

The reviewed image helper now preserves normal App Sandbox image application,
staging and unattended configuration. Only `bcdboot` exit 183 enables recovery.
The fallback configures a copied guest template with explicit GPT references,
adds the missing system-store marker through Windows' offline registry API, and
verifies the result before writing the guest EFI files. Host boot stores and
live registry hives are not opened. Other failures retain their original
diagnostic and remain failures.

A real production-function check exposed one additional requirement: initialize
the copied template's display order before copying its loader. That regression
failed before the change and passes afterward. All four focused offline checks
pass, including partition guards, opaque values, empty keys and invalid-marker
rejection. The corrected function completed on the isolated guest disk; the
disk detached and its permissions remained unchanged.

The exact shipped native helper then built a fresh image from the official ISO
with 19 normal unattended/guest-resource files. All four ordinary boot-file
attempts returned 183; the production fallback returned success. Both disk and
ISO detached, and the source ISO remained unchanged. This proves real native
image creation and staging. Unattended boot completion remains a separate check.

The local **1.0.0 candidate**, not yet published, is **247,073,902 bytes**.
All 128 runtime comparisons, 1,752 inventory hashes, four version identities,
the embedded identity, exact appended payload, licenses and both seven-frame
icons pass. The pending route draft is excluded without modifying its working
copy. Actual native fresh install and repair pass with runtime imports,
configuration preservation and restored published files. That isolated install
did not launch a VM or the app. Current source/payload privacy checks pass;
private fixture disks, generated credentials and setup logs remain excluded.

The final installed 1.0 assets also pass the existing hidden-renderer first and
repeat startup checks against their actual packaged setup-only controller.
Fresh preferences show the intro, saved preferences survive reopening, and a
blocked readiness request retains a diagnostic and recovers through explicit
Retry. No VM operation, gameplay or desktop capture occurs. This proves installed
startup logic, not a physical window, accessibility or clean-guest app launch.

The first production-image boot used the fixture's retained firmware/runtime
state. HCS created and started it, but the bounded observation produced no
Windows startup or setup logs. A read-only collection confirmed that the Windows
volume and kernel file were readable; it did not confirm Windows startup.
The handle closed, the disk detached and existing permissions stayed unchanged.
This is a failed acceptance check, not a successful setup. A separate retry
uses fresh private state contents in the same approved files; its result remains
pending. No new file-access grants or existing BTD6 VM changes are involved.

The fresh-state retry **passed**. Actual Windows logs report BCD specialization
status `0x0` and specialization return `0`. Both `SetupComplete.cmd` and
`setup.cmd` record completion; the guest service records successful startup.
The scripts were generated through the normal upstream provisioning functions,
not a replacement setup flow. The fixture closed, the disk detached and all
three approved files retained their permissions and verified backups.

Together with real native installation/repair, installed-assets startup checks,
existing-environment validated readiness and final publication checks, this
closes the four user-scoped 1.0 blockers. It does not certify every clean-machine
combination or a single integrated fresh-guest Steam/BTD6/Bloons+ installation.
Physical-window/accessibility checks, those broader environment combinations and
complete route coverage remain recorded acceptance work; no gameplay was launched
for this installer verification.

Published as [Bloons+ 1.0](https://github.com/Klaasawastaken/BloonsPlus/releases/tag/v1.0.0)
with exactly one installer. Fresh GitHub readback confirms the artifact's size
and digest, stable release status and tag resolving to the checked source commit.
Website download metadata now identifies 1.0.
