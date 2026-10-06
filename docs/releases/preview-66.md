# Bloons+ Preview 66

## Give upgrade batches time to finish

- Slow an observed fast game before a batch of at least two affordable upgrades on an untimed route.
- Keep purchase input off the speed-toggle frame and respect the existing toggle cooldown.
- Keep recorded speed, manual starts, delays and timed/repeated abilities in control of their own timing.
- Resume normal route speed while waiting for cash or the next round.
- Log the pacing decision for later failure analysis.

Glacial Trail ABR exposed the issue: its round-39 setup took about 22 seconds, and round 40 began before the planned Spike Factory purchases. Pacing addresses that execution delay; it does not prove the strategy wins.

## Verification limits

Offline pacing cases, the actual replay input gate and nearby round-control checks pass. Python compilation and publication checks pass. Original recordings are unchanged. No missing-medal replay was interrupted or launched solely for testing.

Includes the Settings cleanup and route-report repair from Preview 65. Eligible route coverage remains 513/1,204 pairs, with 691 gaps; V1.0 is not complete.
