# Bloons+ 0.1.0 Preview 7

A replay reliability update with a refreshed website and clearer route requirements.

## Replay and progress

- Recover a tower still held on the cursor even when round income increases cash. This addresses the observed unplaced-village failure that prevented subsequent upgrades.
- Preserve explicit timed waits without blocking screen observation; resume waits through checkpoints.
- Check active Monkey Knowledge when a route requires two Crossbow Masters. Reject impossible hero/path and tier-five combinations before launching.
- Add four separate timing-preserved route candidates and correct missing Sniper crosspaths in generated Beginner Hard guides. Original CHIMPS recordings remain unchanged.
- Improve direct replay preflight, persistent failure evidence, medal difficulty mapping and safe update boundaries.
- Reset MM/hour and XP/hour samples when the save source or clock changes.

## Installer and website

- Keep the previous usable installer if a rebuild fails, and improve partial-download validation and guest command diagnostics.
- Refresh Features, Subscriptions, Contributors and the wiki, using official BTD6 artwork with preserved proportions.
- Replace the README banner with official monkey artwork, simplify the homepage and keep Discord banners on Home, Features and Contributors.
- Resolve the newest published preview installer from the download page.

## Install

Download **BloonsPlusSetup.exe**. Internet access is required for setup dependencies. Let an active replay finish before updating the guest application.

## Verification and limitations

The new placement detector recognizes the captured failed-village frame and passes offline checks at 1080p and 1440p. Upgrade-observation regressions pass. These checks do not prove every route wins; new route candidates still require victory plus a saved medal before being considered confirmed. No owned medals were replayed for testing.

Clean Windows setup, signing and remaining live reliability work are still in progress. The installer is unsigned and Windows may show a SmartScreen warning. Pro is a planned offering, not an available purchase. Bloons+ is independent of Ninja Kiwi.
