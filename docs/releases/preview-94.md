# Bloons+ Preview 94

## VM setup repair

- Fix the newest installer being incorrectly rejected as an older build during **Steam + Bloons+ in the VM** setup. The app icon moved the native capability marker beyond the previous 256 KB scan limit.
- Inspect the bounded native executable before its appended app package. Package contents cannot supply that capability marker.
- Check the finished executable during packaging and retain the previous installer if the native capability is missing.
- Preserve the actual component error through the native setup engine, saved checkpoint, log and details panel. Failed setup no longer becomes an unexplained generic validation state.
- Open error details automatically and avoid repeated identical diagnostics.

## Recovery

Install this build over your existing Bloons+ installation, then continue the remaining setup steps. Completed components are retained. An active replay must finish before guest setup can proceed.

The compatibility fix was also applied to the affected host's installed setup script without restarting its running sweep. The installed executable now passes the corrected capability check.

## Verification limits

Regression checks cover the actual installer, markers after large icon resources, read boundaries, exclusion of the appended package, native error propagation and offscreen error rendering. This remains a preview; the complete clean Windows, UAC/reboot and physical accessibility acceptance gates remain open.

336 Python checks, ten SSH transport checks and the 56 existing JavaScript check files pass. The rebuilt installer is 246,836,142 bytes. Its 126 runtime source comparisons and all 1,683 inventory hashes match; both executables retain all seven original app-icon frames. Source and package publication guards report zero findings.
