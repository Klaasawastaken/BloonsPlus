# Bloons+ Preview 16

## Non-blocking cursor targeting

- Split delayed ability targeting into key input and a scheduled cursor continuation.
- Keep screen reading and replay controls active during the cursor delay.
- Send the ability key once; preserve delayed move-only and immediate move-and-click recordings.
- Restore a pending cursor continuation only when its key, timing and target match the current recording, with a validated deadline.
- Avoid counting cursor continuation as a second ability use.

## Verification limits

18 timing and 10 resume checks pass offline. Original recordings are unchanged. Live cursor behavior remains to be observed during missing-medal gameplay; this is not a claim that every strategy wins.

## Install

Download **BloonsPlusSetup.exe**. Close Bloons+ before updating and update the VM between replays. This is a preview, not production 1.0.
