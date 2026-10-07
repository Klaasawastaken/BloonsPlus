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
