# Production 1.0 acceptance

Updated 7 October 2026. **Production 1.0 is not ready for publication.** This checklist separates implemented behavior, offline evidence and remaining acceptance work. The [active TODO](TODO.md) holds individual tasks; the [repair audit](route-repair-audit.md) holds incident evidence.

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
| Medal ownership | Save-source ownership/attempt buckets; 27 complete-loop offline scenarios now include same-path owner switches and safe legacy migration using a digest of explicit ownerID; fresh-save migration preflight passes; v0.1.22 is installed with verified hashes | Observe live prevention and real account switching. Synthetic scenarios do not certify all account changes | S-05–S-07 |
| Route coverage | 86 maps; 553/1,204 eligible map/mode pairs; zero maps entirely without a candidate | 651 coverage gaps remain. A compatible candidate is not proof of victory or current balance compatibility | S-01–S-04, S-08 |
| Source fidelity | Manual controls, waits, selectors, targeting, repeated abilities and second-special commands have offline coverage; 132 existing import signatures match current conversions | Forty-five import signatures differ; nine differing files remain host-catalog candidates, including eight with omitted command context. Resolve admission and coordinate adaptations; support other dialects' paid hero levels and exact Ace centering | R-01–R-04 |
| Placements and upgrades | Visual selection and purchase checks, held-placement recovery and fixed Chutes policy have focused regressions | Observe remaining free/paid placement, hero selection, frozen/moving terrain and exact upgrade cases during missing-medal runs | R-05–R-11 |
| HUD and results | Cash/round guards and finished-route overlay recovery have offline checks; confirmed clears demonstrate some end-to-end paths | Finish representative 1080p/1440p, panel-side and Double Cash coverage; prove bounded recovery avoids stale-frame input | R-12–R-16 |
| Failure evidence | Complete 666-record archive audited privately against current saved ownership; 47 missing-target records match current route bytes across 17 combinations; retired tower uncertainties are separated | Legacy hash/version coverage is incomplete. Audit classifications and actual engine implementation; verify each required field and redaction at export boundaries | R-16–R-17 |
| Profile and statistics | Fifteen host/guest profile groups matched through the relay; thirteen populated-renderer checks pass for tiers/T5, heroes, medals, cadence, late-response precedence and synthetic MM/XP rates; all 390 catalog tier slots and 1,176 candidate tower slugs map; new-source explicit values and rate reset pass | Disconnected requirements retain old marks; cached hero ownership remains green after redraw. Source changes retain absent map/XP claims. Mortar and Skywarden each have a saved-name gap. Bounded repairs await approval; broader decoder and live rate semantics remain open | P-01–P-05 |
| Setup engine | Approved native redesign batches 1–5 implemented; actual published-package install and repair passed at a shorter isolated root, including pinned runtime imports, corrupted-file restoration and configuration preservation; real native/Node transport checks cover cancellation, resume, reconnect, restart deferral and validated release; actual published-archive selective removal preserved modified source and unlisted data/routes; exact installed Python/Pythonw guards cover missing controllers and work started during shutdown. A retained native observer now blocks while a descendant survives and permits recovery after observed natural exit; real observer-loss and failed-handshake checks pass | Environment operators in the protocol fixture are faked. Losing the independent observer still leaves ownership unknown and safely blocks recovery. Earlier acceptance attempts exposed a transient session-write failure and long-path failure. Those repairs remain open, alongside clean Windows, wider interruption recovery, permissions and complete dependency recovery | I-01–I-11 |
| App and configuration | Isolated real renderer checks cover dark requirements, dropdown keyboard behavior, post-install layout and actual startup; 28 full-app layout/name observations, 16 visible-menu checks and 14 emulated viewer request/lifecycle checks pass | Intro preference labels clip in all 12 focused cases; light action/tier contrast and dark eyebrow contrast need approved repairs. Physical keyboard/screen-reader, high DPI, weak hardware, live viewer/lease behavior and complete clean first/repeat-launch acceptance remain open | A-01–A-08 |
| Website | Real BTD6 art, rebuilt pages and README; 18 actual keyboard/motion/landmark observations and exact atomic billing-price exposure have an evidence record | Light contrast and mobile-menu Escape focus repairs await approval; finish broader accessibility and artwork acceptance | W-01–W-04 |
| Performance | Nonblocking waits, logical round clocks and lighter guest rendering implemented | Record navigation, loading, round-boundary, result and deployment timings; avoid claiming unmeasured throughput improvements | R-02, A-04, I-06 |
| Publication | Preview artifacts checked for source identity, inventory hashes, icons and private-file exclusion; native helper build paths removed and binary privacy scans added | Historical commits/installers still contain the original helper. Plan separately scoped cleanup; repeat all checks for the final artifact and confirm clean-machine gates before 1.0 | I-04, release policy |

Coverage was produced by `node tools/route-coverage-report.js` after adding eighteen separate Everything Macro conversions for Middle of the Road, One Two Tree and Town Center. They add ten eligible pairs, increasing coverage from 535 to 545. Subsequent missing-medal gameplay confirmed Middle of the Road Military Only, Primary Only and Deflation with both victory and fresh saved medals; the other conversions have no new local victory claim. The [source audit](upstream-route-batch-2026-10-07.md) records fidelity, opening budgets and exclusions. All 86 map names have explicit mechanics entries, which does not establish that every mechanic has a complete executable handling rule.

The next [four-candidate batch](complete-controls-route-batch-2026-10-07.md) extends catalog eligibility to 553 pairs, leaving 651 gaps. Its source-handler review restored Geared's implicit Heli targeting inputs. These candidates have no local victory claim and preserve all original recordings.

Two separate clean Windows fixture builds failed at App Sandbox's boot-file
stage (`bcdboot` exit 183, `BcdOpenStore` status `c0000035`) before Bloons+ ran.
A fresh name did not repair the failure. Preview `v0.1.14-preview.99` preserves
this exact-VM, fresh-log diagnosis without repeating three image builds; it
does not close clean provisioning or resolve the boot-store issue. All 407
Python tests and 65 approved JavaScript checks pass. The published installer
has 126 matching runtime comparisons, 1,710 valid inventory hashes, matching
native/staged identities and both verified application icons.

## Deferred capabilities

Experimental assistance, boss automation and Pro entitlements remain explicitly unfinished. Their drafts must not be presented as shipped capability or used to conceal missing core acceptance. The private community bot stays outside public packages.

On 7 October the user scheduled Quests, Races, Boss Rush and Boss Events for
**v1.2, after the required 1.0 work**. This includes a dedicated Quests tab initially
marked **Coming soon**. Their individual tasks and outcome requirements are in
the active TODO's v1.2 section; they are not prerequisites for releasing 1.0.

## Release decision

Keep publishing bounded Preview 99 repairs while production gates remain open. Do not rename an incomplete build to 1.0, erase unresolved failures or manufacture validation evidence. Once all supported account medals are earned, stop gameplay entirely and complete remaining offline or installer/UI acceptance separately.
