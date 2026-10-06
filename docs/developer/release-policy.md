# Release policy

Effective from the next release after Preview 96.

- Use the [release notes template](../releases/TEMPLATE.md) for every new release.
- Release notes have exactly three sections, in this order: **Additions**, **Changes**, **Removed**. Use “None.” for an empty section.
- Put fixes, compatibility changes and relevant limitations under **Changes**. Keep detailed verification evidence in developer documentation.
- Preserve previously published notes; this format applies to future releases.
- Milestone 100 is the full **Bloons+ 1.0** release, tagged `v1.0.0`, rather than `v0.1.0-preview.100`.
- Use Previews 97–99 for remaining preparation. Publish milestone 100 after the production acceptance gates are met; its number does not establish readiness.
- A repair within Preview 99 may increment the patch version, for example `v0.1.1-preview.99`, without claiming the full 1.0 milestone. Preserve the prior published artifact under `dist/releases/<tag>/` before replacing the current `dist/preview99/` selector copy.
- Keep the current release metadata and download links on the latest published release until a new release is successfully published.
- Keep isolated published installers at `dist/preview<N>/BloonsPlusSetup.exe` for previews and `dist/v<major>.<minor>.<patch>/BloonsPlusSetup.exe` for production releases. Both host setup and the standalone VM helper select that artifact before a generic build and reject a size mismatch. This directory convention does not publish or certify a release.
