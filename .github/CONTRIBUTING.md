# Contributing to BloonsPlus

Thanks for helping improve BloonsPlus. Useful contributions include reproducible bug reports, focused fixes, accessibility improvements, documentation and attributed route candidates.

## Start with the right place

- **Questions and setup help:** [Wiki](https://bloonsplus.com/wiki/) or [Discord](https://discord.gg/qxUGXqrXsY).
- **Bugs:** search [existing issues](https://github.com/Klaasawastaken/BloonsPlus/issues), then use the bug report form.
- **Features:** explain the problem and expected benefit in the feature request form before starting a large change.
- **Security vulnerabilities:** use the [private reporting process](SECURITY.md). Do not open a public issue with exploit details.

Follow our [Code of Conduct](CODE_OF_CONDUCT.md) in all project spaces.

## Local development

Follow the setup commands in the [README](../README.md#build-and-contribute). Use Windows and Python 3.12, install the pinned Python dependencies, and run `npm ci`. Copy the example configuration only for a fresh checkout; keep existing personal settings.

The [developer wiki](https://bloonsplus.com/wiki/development/), [route format](https://bloonsplus.com/wiki/route-format/) and [developer reference](../docs/developer/README.md) describe the runtime. Check the [active roadmap](../docs/developer/TODO.md) before duplicating work.

## Making a change

1. Fork the repository and create a focused branch.
2. Explain larger changes in an issue first. Keep unrelated refactors out of a bug fix.
3. Add or update focused offline checks where behavior changes. Record the exact commands and results in your PR.
4. Update user or developer documentation when the workflow changes.
5. Open a PR using the checklist. State what was verified and what still needs live evidence.

Use descriptive commits such as `fix(replay): preserve the intended upgrade after reconnect`. PRs should explain the problem, the change and any compatibility or migration impact. Maintainers may request changes or decline contributions outside the roadmap.

## Verification

Run relevant checks from the repository root in PowerShell. The complete Python suite is:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test*.py'
.\.venv\Scripts\python.exe tests/test-vm-setup-ssh.py
```

JavaScript checks are standalone files; run the relevant file with `node tests/test-name.js`. For a full pass:

```powershell
$checks = Get-ChildItem tests -Filter 'test*.js' | Sort-Object Name
foreach ($check in $checks) {
    node $check.FullName
    if ($LASTEXITCODE -ne 0) { throw "Failed: $($check.Name)" }
}
```

Before sharing source or a package, run `python tools/check-publication.py` with your environment's Python executable. Use `--payload dist/BloonsPlusPayload.zip` for the built payload. Review attachments yourself too; automated redaction and scanning have limits.

## Gameplay and route contributions

- Read game, Steam and save data without modifying it. Gameplay must use simulated mouse/keyboard input.
- Preserve original recordings, especially CHIMPS. Submit an improved route as a separate candidate with source attribution and requirements.
- Include map, variation, game version, hero, required tower paths, Monkey Knowledge assumptions and special map mechanics.
- Offline parsing, budgets and legality checks do not prove a win. Label a candidate honestly. A confirmed clear requires both victory and the saved medal.
- For the missing-medal sweep, skip owned map/mode pairs. Do not launch gameplay solely to validate an already-earned medal.
- Apply runtime updates after a healthy replay finishes. Do not interrupt gameplay just to deploy a patch.

## Privacy and licensing

Never commit saves, Steam credentials, SSH keys, VM disks, local checkpoints, personal screenshots, account identifiers or private Discord bot code. Share only the minimum redacted evidence needed to reproduce a problem.

BloonsPlus-owned code uses [PolyForm Noncommercial 1.0.0](../LICENSE.md). Contributions you own are submitted under that license unless another arrangement is explicitly agreed before merging. Only submit material you have the right to contribute. Preserve imported licenses, copyrights and route provenance; official BTD6 art is not relicensed by BloonsPlus. See [third-party scope](THIRD_PARTY.md).
