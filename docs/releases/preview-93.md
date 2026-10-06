# Bloons+ Preview 93

## Post-install configuration

- Replace the busy setup strip with a branded welcome, official Engineer Monkey art and three observed configuration stages.
- Keep one next-step action visible. Expand component checks, diagnostics and an optional existing Windows image path when needed.
- Retain the existing shared setup engine, Steam sign-in, restart confirmation, pause, retry and VM controls. Missing components do not block app navigation.
- Use proportional artwork, themed cards and short entrance animations. Reduced motion disables those animations; no extra runtime or media download is added.
- Remove the **Skip intro** button. Branding still finishes automatically; startup preferences, keyboard dismissal and independent controller recovery remain available.

## Included installer fix

Preview 92's legacy-controller compatibility fix and community policies remain included. Native setup can use a verified separate setup controller when an older listener returns HTTP 404. The older listener and its healthy gameplay stay untouched.

## Verification

333 Python checks, ten SSH transport checks and 56 JavaScript check files pass. The actual renderer was checked in light, dark and compact layouts without horizontal overflow. Artwork proportions, visible restart controls, progress semantics and reduced motion were checked. An isolated 60-frame sample had a median interval of 16.7 ms; this is not a guarantee for other hardware.

This remains a preview. Clean Windows setup, real UAC/reboot, physical accessibility and weak-hardware acceptance remain open. The active missing-medal sweep was not interrupted to install these changes.
