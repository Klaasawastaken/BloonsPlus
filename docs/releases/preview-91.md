# Bloons+ Preview 91

## A clearer install and first launch

- Compact native Windows installer with a single primary action and optional location, shortcut, launch and VM choices.
- Inspect an existing installation and offer Launch, Update or Repair. Preserve modified app data and routes during repair or selective uninstall.
- Retain installation ownership, dependency process-tree receipts and atomic app-file replacements across interruptions.
- Show measured download/copy progress when available, saved restart choices and friendly recovery details with explicit redacted Copy/Export.
- Share authenticated setup sessions between the native installer, first launch and Settings. Pause queued work without stopping a replay.
- Keep setup inline when a VM is absent. Updates wait for a fresh idle replay boundary.
- Add Full, Reduced and Off intro settings. Escape/Skip dismiss branding while service failures retain Retry/details.
- Preserve host acceleration and the guest's lighter rendering path. Use a stable themed window and bounded startup/recovery retries.

## Recovery fixes

- Resume an actively cancelled setup after its observed safe boundary.
- Save the boot identity before marking a remote restart requirement.
- Preserve Update intent through native handoff and Resume instead of accepting the old guest version as ready.
- Use the actual native observer constructor during read-only SSH recovery.
- Restore Continue after a previously healthy VM loses its connection.
- Serve the app shell while setup-only ownership persists; ordinary gameplay APIs and timers remain disabled there.
- Fix early status polling before its initialization guard.

## Verified scope

332 Python checks, ten SSH transport checks and 56 JavaScript check files pass. Actual native controls and the app renderer were inspected in isolated hidden windows. Package/source integrity and privacy guards are checked before publication.

This is a preview, not production 1.0 certification. Clean Windows setup, real UAC/reboot, Steam/2FA, physical DPI/screen readers and weak-hardware acceptance remain open. No game/save files or original CHIMPS recordings were changed. Healthy gameplay was not interrupted to apply the batch.

Unsigned previews may still show Windows SmartScreen. No certificate or security bypass is bundled.
