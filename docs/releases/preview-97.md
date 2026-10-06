# Bloons+ Preview 97

## Additions

- Persistent installer file recovery across process exits. Setup saves a package journal before replacement and recovers unfinished work when setup resumes.
- App startup protection for interrupted packages. Reopen the installer and choose Continue setup or Repair before starting the local controller.

## Changes

- Recover prior app files before preparing another package or restoring retained app data. Interrupted preparation keeps the old package; interrupted cleanup after a recorded commit keeps the new package.
- Preserve files changed outside setup and retain their verified recovery copies until the conflict is resolved. Retry recovery safely without repeating completed restoration.
- Reject unsafe journal paths, duplicate destinations, linked paths and unknown recovery artifacts before changing app files.
- Verify final replacement hashes before recording a package commit. Pending recovery cannot be reported as healthy, launched, uninstalled or bypassed by a cached environment setup session.
- Target milestone 100 as the full `v1.0.0` release. Future notes use Additions, Changes and Removed.
- Verified 346 offline Python checks, ten isolated SSH checks and 58 JavaScript check files. These include an unpublished route draft check; that draft remains excluded from this installer. Original recordings remain intact.
- The 246,857,552-byte installer passes all 126 runtime source comparisons and 1,688 package inventory hashes. Both executables retain all seven original icon frames; source and payload publication guards report zero findings.
- This is an unsigned preview. Process-exit fixtures do not certify physical power-loss recovery, clean Windows setup, UAC/reboot, complete VM provisioning or physical accessibility. Those production acceptance gates remain open. Healthy missing-medal gameplay was not interrupted.

## Removed

- Replaced the in-memory-only package rollback and untracked sibling temporary files with one persistent transaction recovery flow.
