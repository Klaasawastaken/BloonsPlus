# App and website update — 3 October 2026

## Website

- Replaced the redundant Docs page with a Features page describing the app’s available controls.
- Moved the installation, first replay and troubleshooting tutorial to Downloads.
- Kept old Docs and Guides URLs as redirects; the wiki remains the reference documentation.
- Updated navigation and added theme-aware scrollbars.

## Desktop app

- Applied the website’s coral and sage palette to light and dark modes.
- Reused the website balloon logo and rebuilt the Windows icon. Installer builds include this icon.
- Simplified the map selector and displayed only tower paths and tiers needed by its recording.
- Removed route generation, recording, import and export tools from the interface.
- Made the VM viewer inline. Frame requests stop when the window loses focus, the document is hidden or another app category is selected.
- Replaced the boss navigation mark with a dragon emoji.

## Setup recovery

- Reuse a responsive App Sandbox instead of starting another instance.
- Retry a stale shell once, using graceful window closure only when no VM worker is detected.
- Bound setup subprocess waits, report SSH and VM startup progress, and wait for a guest installer before launching its app.
- Wait for a real guest app connection after launch, with an actionable timeout instead of indefinite waiting.

## Replay repairs

- Recognize bottom-right placement confirmation buttons.
- Filter background artifacts in HUD OCR and reject implausible opening cash/round readings.
- Restrict movement-based relocation to maps that actually have moving placement terrain.
- Exclude structurally invalid routes and unverified CHIMPS conversions for incompatible modes.
- Existing CHIMPS recording files were not modified.

## Verification and limits

- JavaScript syntax checks, Python compilation and the publication pattern guard passed.
- Inspected the app’s requirement cards and live VM viewer in the browser.
- Setup recovery has not been exercised on the affected friend’s PC. No guarantee of every route winning is implied.
