# Bloons+ Preview 15

## Ability timing

- Wait for round-relative ability timers in the replay execution gate, keeping screen reads and run controls active.
- Pin each pending ability deadline so a round transition cannot restart its wait.
- Preserve the deadline during checkpoint resume only when the recorded timer is unchanged; reject invalid deadlines.
- Log the scheduled deadline when sending the ability input.

## Verification limits

14 timing, 10 resume and eight converter checks pass offline. Existing recordings, including CHIMPS, are unchanged. These checks do not prove strategy victories. Cursor-target delays still use a blocking wait and remain unfinished.

## Install

Download **BloonsPlusSetup.exe**. Close Bloons+ before updating. Apply VM updates between replays from Settings on the main PC. This is a preview, not production 1.0.
