# Bloons+ Preview 92

## Installer compatibility fix

- Fix native setup failing with repeated HTTP 404 errors when an older local controller occupies the app port.
- Start a setup-only controller on a separate free loopback port. Verify its protocol, installation owner, actual listening process and executable before sending any setup secret or command.
- Retain a private discovery receipt so Resume reconnects to the same controller. The receipt never substitutes for ownership checks.
- Keep the older controller and healthy replay running. Existing setup ownership, unknown-state refusal and replay-boundary checks still apply.
- Both the installer and installed app contain the Bloons+ app icon, verified against all seven original icon frames.

## Community standards

- Add contribution guidance, a Code of Conduct, support and security policies, privacy-aware bug/feature forms and a pull request checklist under `.github`.
- Add the official, unmodified PolyForm Noncommercial 1.0.0 license for BloonsPlus-owned material, with its required copyright notice and explicit third-party exclusions. Imported licenses and official BTD6 artwork retain their terms.
- Link the community policies from the README and correct the retained-notice folder reference.

## Acceptance scope

333 Python checks, ten SSH transport checks and 56 JavaScript check files pass. The rebuilt installer is 246,828,802 bytes (235.4 MiB); 125 runtime sources and all 1,680 inventory hashes match. Source and payload privacy guards report zero findings. The legacy-port regression covers authenticated handoff and reconnect without replacing the old listener.

This remains a preview: clean Windows setup, real UAC/reboot, physical accessibility and weak-hardware acceptance remain open. The new post-install configuration presentation is planned separately; the native installer design stays intact.
