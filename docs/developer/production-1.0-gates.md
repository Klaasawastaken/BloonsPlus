# Production 1.0 acceptance

Updated 6 October 2026. **Production 1.0 is not ready for publication.** This checklist separates implemented behavior, offline evidence and remaining acceptance work. The [active TODO](TODO.md) holds individual tasks; the [repair audit](route-repair-audit.md) holds incident evidence.

## Scope and standing rules

- Gameplay exists to earn the account's missing medals. Owned map/mode pairs are never rerun, including after all supported medals are earned.
- A clear requires both victory and a saved medal. Failed candidates retain persistent evidence; one failure must not block other eligible targets.
- Healthy replays finish before batched runtime deployment. Offline route checks do not justify validation-only gameplay.
- Original CHIMPS recordings remain intact. Game, save and Steam files are read only. Gameplay uses simulated input.
- Public source and installers exclude profiles, personal logs, screenshots, credentials, VM images and private Discord bot code.
- Milestone 100 is `v1.0.0`. Release notes contain only **Additions**, **Changes** and **Removed**. Publish one installer asset, without `SHA256SUMS.txt`.

## Acceptance matrix

| Area | Evidence available | Remaining gate | TODO |
| --- | --- | --- | --- |
| Medal ownership | Save-backed selection, persistent attempts and observed victory/save reconciliation; several missing medals earned | Verify unreadable/stale saves, profile changes and delayed saves cannot cause owned medals to replay | S-05–S-07 |
| Route coverage | 86 maps; 535/1,204 eligible map/mode pairs; zero maps entirely without a candidate | 669 coverage gaps remain. A compatible candidate is not proof of victory or current balance compatibility | S-01–S-04, S-08 |
| Source fidelity | Manual controls, waits, selectors, targeting, repeated abilities and second-special commands have offline coverage | Audit older imports; support other dialects' paid hero levels and exact Ace centering before admitting affected candidates | R-01–R-04 |
| Placements and upgrades | Visual selection and purchase checks, held-placement recovery and fixed Chutes policy have focused regressions | Observe remaining free/paid placement, hero selection, frozen/moving terrain and exact upgrade cases during missing-medal runs | R-05–R-11 |
| HUD and results | Cash/round guards and finished-route overlay recovery have offline checks; confirmed clears demonstrate some end-to-end paths | Finish representative 1080p/1440p, panel-side and Double Cash coverage; prove bounded recovery avoids stale-frame input | R-12–R-16 |
| Failure evidence | Persistent route failures and screenshot/action context exist; retired tower uncertainties are separated | Audit older incidents and classifications; verify each required field and redaction at export boundaries | R-16–R-17 |
| Profile and statistics | Fifteen host/guest profile groups were equal through the actual relay; achievement-source repair has endpoint/UI regressions | Decoder semantics, UI freshness, disconnect handling and MM/XP rate behavior need broader acceptance | P-01–P-05 |
| Setup engine | Approved native redesign batches 1–5 implemented; shared controller/session checks, resume and installer compilation pass offline | Clean Windows install, interruption, repair, update, permissions and dependency recovery need end-to-end acceptance | I-01–I-11 |
| App and configuration | Isolated real renderer checks cover dark requirements, dropdown keyboard behavior and post-install layout/motion | Physical keyboard/screen-reader, high DPI, weak hardware and first/repeat-launch acceptance remain open | A-01–A-08 |
| Website | Real BTD6 art, rebuilt pages and README; responsive spot checks have an evidence record | Finish contrast, accessibility and artwork acceptance; retain the requested hero composition and community banner rules | W-01–W-04 |
| Performance | Nonblocking waits, logical round clocks and lighter guest rendering implemented | Record navigation, loading, round-boundary, result and deployment timings; avoid claiming unmeasured throughput improvements | R-02, A-04, I-06 |
| Publication | Preview artifacts checked for source identity, inventory hashes, icons and private-file exclusion | Repeat every check for the final artifact and confirm clean-machine gates before changing the release to 1.0 | I-04, release policy |

Coverage was produced by `node tools/route-coverage-report.js` after adding the separate Firing Range candidate. Its five compatible targets account for the increase from 530 to 535; they have no new local victory claim. All 86 map names have explicit mechanics entries, which does not establish that every mechanic has a complete executable handling rule.

## Deferred capabilities

Experimental assistance, boss automation and Pro entitlements remain explicitly unfinished. Their drafts must not be presented as shipped capability or used to conceal missing core acceptance. The private community bot stays outside public packages.

## Release decision

Keep publishing bounded Preview 99 repairs while production gates remain open. Do not rename an incomplete build to 1.0, erase unresolved failures or manufacture validation evidence. Once all supported account medals are earned, stop gameplay entirely and complete remaining offline or installer/UI acceptance separately.
