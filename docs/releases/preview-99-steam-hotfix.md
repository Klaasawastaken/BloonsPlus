# Bloons+ Preview 99 — Steam Readiness Hotfix

## Additions

- Add nine offline guest handoff checks for existing games, sign-in, missing games, unavailable status and Steam stopping during an update.

## Changes

- Reuse the existing guest Steam/game detector before and after VM app provisioning. Keep Steam's own sign-in and official installation flow for observed missing requirements.
- Avoid focusing Steam or opening the BTD6 install prompt when Steam is running, signed in and the game is installed. Show sign-in instructions without suggesting an installed game must be installed again.
- Reopen Steam when the fresh post-install check says it stopped, even if it was launched earlier. Unavailable or malformed observations remain unknown and defer to the setup panel; no game/save files are edited.
- Verify all 387 Python tests, 62 JavaScript check files, ten setup transport checks and six Steam cache checks. Keep clean-machine, UAC/reboot, physical accessibility and full 1.0 acceptance open.
- Check the 246,884,706-byte installer against 126 runtime source files and all 1,695 inventory hashes, with both seven-frame icons and staged/embedded release identities verified. Publication guards report zero private-data findings.
- Preserve the checked package identity, approved HUD recovery and existing gameplay safeguards. Keep runtime deployments batched after replays; this host provisioning repair does not require interrupting a healthy guest replay.

## Removed

- Remove unconditional Steam install/sign-in prompts from VM app provisioning.
