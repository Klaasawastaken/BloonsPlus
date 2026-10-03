# Backend modules

The local API in `server.js` loads these modules. `PROJECT_ROOT` deliberately points to the app root so existing player settings, progress, Python environment and route locations survive the move.

- **Automation:** `automation.js`, `engine-lock.js`, `replay-monitor.js`, `route-validation.js`.
- **Progress:** `btd6-save-progress.js`, `steam-progress.js`, `scanner.js`, tower and achievement helpers.
- **VM:** `vm-bridge.js`, `vm-setup.js`, `live-screen.js`.
- **Game input and capture:** `input.js`, `capture.js`, `ocr.js`, `pixels.js`.
- **Experimental:** boss route generation and strategy assistance; these are not guaranteed winning engines.

Public functions remain CommonJS exports. Maintenance scripts are in `tools/`; browser code remains separate at the app root.
