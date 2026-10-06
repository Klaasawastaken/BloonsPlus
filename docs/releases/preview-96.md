# Bloons+ Preview 96

## Safer installer file replacement

Setup checks the complete archive path plan and prepares every changed app file
before replacing installed files. Unsafe paths, case-insensitive duplicate files
and file/directory conflicts are rejected before app contents change.

If preparation fails or is cancelled, the existing app files remain intact. A
caught failure or cancellation during replacement restores earlier replacements
from verified recovery copies and removes newly introduced files. If another
process changes a file, setup preserves that change and retains its recovery
copy instead of overwriting it during rollback.

The file step reports measured preparation and application work. It does not
report app files ready until replacements finish. Unchanged files are reused.

## Verification and limits

Regression fixtures first reproduced early replacement after a bad later archive
entry and missing rollback after a later replacement failure. Both now pass.
Coverage includes unsafe paths, duplicates, file/directory collisions, staging
cancellation, locked files, later failures, cancellation between replacements,
outside edits, retained copies, unchanged-file reuse and progress boundaries.

All 341 offline Python checks, ten isolated SSH transport checks and 57 current
JavaScript check files pass. One JavaScript check covers the unpublished Sunken
Columns ABR draft; that draft remains excluded from this release. Original
recordings, including CHIMPS, were not modified.

This remains an unsigned preview. The rollback handles caught errors and
cancellation; it does not yet provide a durable package transaction across an
abrupt process termination or power loss. Retained recovery copies are not
automatically reconciled on a later launch. Clean Windows setup, UAC/reboot,
full VM provisioning and physical accessibility acceptance remain open. Healthy
missing-medal gameplay was not interrupted or updated by these checks.

The installer is 246,846,108 bytes (235.4 MiB). The 126 runtime source comparisons,
all 1,685 package inventory hashes and seven original icon frames in each EXE
match. Source and payload publication guards report zero findings.
