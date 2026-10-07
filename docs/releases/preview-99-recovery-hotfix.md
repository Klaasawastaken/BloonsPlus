# Bloons+ Preview 99 — Installer Recovery and Hero Picker Hotfix

## Additions

- Add a small native dependency observer that survives the installer window closing and records when its exact process group has finished.
- Add real process-interruption checks and hero-picker regressions for colored backgrounds, title colors and Select/Selected labels.

## Changes

- Allow setup recovery after the observed dependency group becomes empty. This confirms that work stopped, not that installation succeeded; normal dependency checks still run.
- Read hero selection from the button letters instead of treating green scenery as a Select or Selected button.
- Include magenta hero-title artwork in the existing OCR candidates and isolate the white Select letters from the button border.
- Keep Psi recognition marked unresolved: the captured Obyn and Ezili repairs do not prove every hero can be selected.
- Keep unknown process ownership blocked if the observer itself is lost. Clean Windows, reboot and physical accessibility acceptance remain open; this is still Preview 99.

## Removed

- Remove selection claims based solely on green-pixel density.
- Remove the permanent unknown state after an interrupted installer's retained observer confirms that its dependency group ended.
