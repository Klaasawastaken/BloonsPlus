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

## Next checks

After the approved checkpoint repair, repeat these checks and add deterministic
bounded-retry and persistent-error coverage before changing product code.
Custom-path preflight also remains open: a successful shorter root does not
resolve the observed 262-character dependency path. Preserve the existing
atomicity, ownership and recovery rules.

Then finish the separate clean supported Windows, UAC/reboot, complete VM
provisioning and physical accessibility gates. Successful fixture checks or a
temporary-root install do not close those gates.
