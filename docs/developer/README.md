# Developer reference

- [Language map](../languages.md)
- [Build and GitHub setup](../../GITHUB_SETUP.md)
- [Implementation review](../../CODE_REVIEW_2026-10-03.md)
- Maintenance/import helpers are in `tools/`; run them from the repository root.
- The active engine and routes remain in `autobtd6/`.
- `data/tower-upgrades.json` is the attributed tower catalog used by the app and installer.

## Optional reference engines

Unused full source snapshots are excluded from the public repository and installer. Existing local copies are preserved. For maintenance imports, clone these into the corresponding ignored directory:

- `btd6bot/`: https://github.com/j-miet/BTD6bot
- `btd6autoplay/`: https://github.com/Jazzmoon/btd6_autoplay

Their original MIT notices are retained in `licenses/`. Existing imported routes retain provenance. Removing snapshots does not validate their converted strategies.
