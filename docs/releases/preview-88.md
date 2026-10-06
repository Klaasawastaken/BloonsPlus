# Bloons+ Preview 88

## VM updates use the published installer

- In a developer checkout, prefer the named installer for the published preview over an older generic build in `dist`.
- Validate its size against release metadata. Report an incomplete artifact rather than silently installing older code.
- Keep standard builds and installed-app layouts supported.
- Resolve the installer only when provisioning requires it. Steam installation and app launch can proceed independently of release-artifact availability.

## Reuse healthy Python installations

- Check the existing private Python environment before requiring the temporary disk space needed for package installation.
- Reuse requires Python 3.12 x64, exact pinned package versions, consistent dependencies and successful runtime imports.
- When repair is required, check disk space before moving or rebuilding the existing environment.

## Verification and limits

All 301 Python checks, ten VM setup transport checks and 49 JavaScript check files pass. Regression checks cover published-artifact precedence, truncated artifacts, invalid metadata, legacy layouts, independent launch actions and healthy-runtime reuse.

The installer is 246,302,496 bytes. Its payload passes 29 exact source comparisons, footer/length verification and the publication guard with zero findings. Clean-machine installation and interrupted-install acceptance remain open.

The missing-medal sweep continued during development. This batch does not change gameplay or original CHIMPS recordings. It is a preview, not production v1.0 or a guarantee that every route wins.
