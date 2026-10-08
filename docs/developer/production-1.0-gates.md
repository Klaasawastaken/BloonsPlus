# Production 1.0 acceptance

Updated 8 October 2026. **Production 1.0 is not ready for publication.** This checklist separates implemented behavior, offline evidence and remaining acceptance work. The [active TODO](TODO.md) holds individual tasks; the [repair audit](route-repair-audit.md) holds incident evidence.

## Scope and standing rules

- Gameplay exists to earn the account's missing medals. Owned map/mode pairs are never rerun, including after all supported medals are earned.
- A clear requires both victory and a saved medal. Failed candidates retain persistent evidence; one failure must not block other eligible targets.
- Healthy replays finish before batched runtime deployment. Offline route checks do not justify validation-only gameplay.
- Original CHIMPS recordings remain intact. Game, save and Steam files are read only. Gameplay uses simulated input.
- Public source and installers exclude profiles, personal logs, screenshots, credentials, VM images and private Discord bot code.
- Milestone 100 is `v1.0.0`. Release notes contain only **Additions**, **Changes** and **Removed**. Publish one installer asset, without `SHA256SUMS.txt`.

## Required release gates — user scope, 8 October

The user narrowed 1.0 to the following four gates. Remaining app, website,
statistics and route-coverage improvements stay in the backlog; they do not
delay 1.0. Existing privacy and missing-medal safeguards still apply.

| Gate | Status | Required next evidence |
| --- | --- | --- |
| Finish the installer | Open | Clean installation through first launch, repair/retry and final packaged identities; retain the completed isolated native checks |
| Fix the main setup blocker | Open | Boot a separate clean guest after the boot-store repair, then complete actual setup; copied-store configuration alone is insufficient |
| Privacy cleanup | Historical cleanup complete; final artifact check remains | Recheck final source and decompressed installer; 139 public refs, 124 affected old assets, 137 retained notes and 16 clean downloads were verified after cleanup |
| Sweep fixes | Open | Resolve evidenced startup/reconnect/recovery blockers while preserving account ownership, attempts and failures; full route coverage or every medal is not required |

Full Odyssey support remains the first v1.2 priority after these gates and 1.0
publication. Release notes use only Additions, Changes and Removed.

## Existing evidence and remaining backlog

| Area | Evidence available | Remaining gate | TODO |
| --- | --- | --- | --- |
| Medal ownership | Save-source ownership/attempt buckets; 27 complete-loop offline scenarios now include same-path owner switches and safe legacy migration using a digest of explicit ownerID; fresh-save migration preflight passes; v0.1.22 is installed with verified hashes | Observe live prevention and real account switching. Synthetic scenarios do not certify all account changes | S-05–S-07 |
| Failure evidence | Complete 666-record archive audited privately against current saved ownership; 47 missing-target records match current route bytes across 17 combinations; retired tower uncertainties are separated | Legacy hash/version coverage is incomplete. Audit classifications and actual engine implementation; verify each required field and redaction at export boundaries | R-16–R-17 |
| Profile and statistics | Fifteen host/guest profile groups matched through the relay; thirteen populated-renderer checks pass for tiers/T5, heroes, medals, cadence, late-response precedence and synthetic MM/XP rates; all 390 catalog tier slots and 1,176 candidate tower slugs map; new-source explicit values and rate reset pass | Approved disconnect/source projection and two tower-name alias repairs pass the original renderer regressions. Live disconnect/account switching, broader decoder coverage and live rate semantics remain open | P-01–P-05 |
| Setup engine | Approved native redesign batches 1–5 implemented; actual published-package install and repair passed at a shorter isolated root, including pinned runtime imports, corrupted-file restoration and configuration preservation; real native/Node transport checks cover cancellation, resume, reconnect, restart deferral and validated release; actual published-archive selective removal preserved modified source and unlisted data/routes; exact installed Python/Pythonw guards cover missing controllers and work started during shutdown. A retained native observer now blocks while a descendant survives and permits recovery after observed natural exit; real observer-loss and failed-handshake checks pass; fresh-process recovery through actual deployment at staged/prepared/first-replacement boundaries preserves prior files and allows retry; real offline pip update failure and fresh-process retry preserve healthy packages/configuration and withhold a new success stamp until verified | Environment operators in the protocol fixture are faked. Losing the independent observer still leaves ownership unknown and safely blocks recovery. The approved transient checkpoint repair has deterministic error and actual Windows lock coverage; the observed deep-wheel path failure now passes actual native install/reuse/repair with pinned dependencies at a long custom root. Arbitrarily long application roots remain unproven alongside clean Windows, wider interruption recovery, permissions and complete dependency recovery | I-01–I-11 |
| App and configuration | Isolated real renderer checks cover dark requirements, dropdown keyboard behavior, post-install layout and actual startup; 28 full-app layout/name observations, 60 repaired intro label/persistence cases, 100 normal/hover contrast checks, 108 broader flat-background contrast observations and 14 emulated viewer request/lifecycle checks pass; 88 real-renderer report-dialog version, keyboard, layout, naming and redaction observations pass, with a failing non-modal negative control; seven real-file/synthetic-process viewer backend scenarios pass | The approved malformed-request publisher repair passes focused checks, including excessive JSON nesting; published in .38; full guest deployment remains. Gradient/opacity contrast remains outside the flat-background audit. Physical keyboard/screen-reader, high DPI, weak hardware, live viewer/lease behavior and complete clean first/repeat-launch acceptance remain open | A-01–A-08 |
| Website | Real BTD6 art, rebuilt pages and README; 18 keyboard/motion/landmark observations, atomic billing-price exposure, 60 secondary-text contrast checks and 68 complete content observations plus nine redirects pass. Mobile Escape focus and the Wiki table overflow are repaired; all 102 content observations at actual 100/200/400% zoom and 320 hover/focus contrast observations pass. All 17 content pages in both themes pass 2,646 normal-state rendered-background text observations, including map artwork; an invisible-text negative control is detected. All 68 fixed-viewport doubled-text cases pass with fallback fonts and actual web fonts (136 custom-font observations); the missing-font negative control fails as intended. Download metadata identifies .40; fresh live-page verification remains. Subscription controls pass 72 normal/hover/focus text observations including faded savings labels, with a 24-case low-opacity negative control | Finish remaining interactive-state and ancestor-opacity contrast, physical screen-reader and physical text-scaling acceptance | W-01–W-04 |
| Performance | Nonblocking waits, logical round clocks and lighter guest rendering implemented | Record navigation, loading, round-boundary, result and deployment timings; avoid claiming unmeasured throughput improvements | R-02, A-04, I-06 |
| Publication | Preview artifacts checked for source identity, inventory hashes, icons and private-file exclusion; helper diagnostic build paths removed. Approved historical cleanup is published and verified: 139 refs, 124 retired assets, 137 retained notes and 16 preserved clean downloads | Repeat source/payload checks for the final artifact and confirm the four scoped release gates | I-04, release policy |

Coverage was produced by `node tools/route-coverage-report.js` after adding eighteen separate Everything Macro conversions for Middle of the Road, One Two Tree and Town Center. They add ten eligible pairs, increasing coverage from 535 to 545. Subsequent missing-medal gameplay confirmed Middle of the Road Military Only, Primary Only and Deflation with both victory and fresh saved medals; the other conversions have no new local victory claim. The [source audit](upstream-route-batch-2026-10-07.md) records fidelity, opening budgets and exclusions. All 86 map names have explicit mechanics entries, which does not establish that every mechanic has a complete executable handling rule.

The next [four-candidate batch](complete-controls-route-batch-2026-10-07.md) extends catalog eligibility to 553 pairs, leaving 651 gaps. Its source-handler review restored Geared's implicit Heli targeting inputs. Bazaar subsequently earned its missing Hard and Impoppable medals with victories and fresh authoritative saved medals. The subsequent CHIMPS attempt lost at round 15; the full opening evidence is retained and its exact cause remains unresolved. The sweep continued automatically to another missing medal. These outcomes do not establish the other candidates' outcomes; all original recordings remain preserved.

Two separate clean Windows fixture builds failed at App Sandbox's boot-file
stage (`bcdboot` exit 183, `BcdOpenStore` status `c0000035`) before Bloons+ ran.
A fresh name did not repair the failure. Preview `v0.1.14-preview.99` preserves
this exact-VM, fresh-log diagnosis without repeating three image builds; it
does not close clean provisioning or resolve the boot-store issue. All 407
Python tests and 65 approved JavaScript checks pass. The published installer
has 126 matching runtime comparisons, 1,710 valid inventory hashes, matching
native/staged identities and both verified application icons.

On 8 October the approved elevated host copied-template probe passed all 11
configure/read-back operations with no error and unchanged source input. Every
BCDEdit operation used an explicit private store. A subsequent separate 64 GB
fixture applied the official Windows image and passed all 12 copied-store
operations. The original template remained unchanged. This proves disk creation,
not guest boot or complete installation. The corrected direct-HCS probe initially
stopped during construction with access denied. The user explicitly approved
Windows VM access grants for only the new private disk and two state files. All
three grants returned success; original and observed permissions were retained
privately and ownership was unchanged. HCS then created and started the fixture,
but it exited before a Windows guest connection was observed. Read-only offline
inspection found no startup logs, with kernel-file controls confirming the volume
was readable. Boot-store readback exposed host VHD references in the three device
entries. A reviewed, fixture-only repair uses explicit GPT disk/partition IDs and
checks all three entries before installation. After the user requested another
administrator prompt, the repair ran successfully: all three qualified device
references passed provider readback, the installed store matched the prepared
copy, and the disk detached. Two earlier private attempts are retained: embedded
WMI method dispatch failed, then an exact-path guard rejected the provider's NT
path prefix. The corrected guard accepts only that exact private path.

A subsequent bounded boot created and started the isolated fixture, but no guest
integration connection appeared within five minutes. Its handle closed
successfully. Read-only offline inspection then recovered fresh Windows setup
and system-event logs, proving startup reached specialization. Setup rejected
the copied BCD as a system store (`0xC0000098`), so complete guest setup and
production integration remain open. The disk detached after inspection. Existing
BTD6 VM, SSH and scheduled-task permissions were not changed.

The next private-copy diagnosis found a missing `System=1` marker in the root
Description key. Windows' offline hive API independently confirmed the missing
value. Its repaired output preserves all 165 key paths, including empty keys,
and every one of the 130 existing values; only the missing DWORD marker is added.
The output was reopened and compared exactly, and the original file hash stayed
unchanged. An independent byte-level reader also confirms the three root markers.
This file repair has not been applied to a guest or integrated into production.
Windows' explicit-store boot-entry verification now passes: both private copies
return success, their full entry listings match and the original inputs remain
unchanged. A fresh clean setup remains required. Earlier administrator prompts
were canceled; the final explicitly requested resend succeeded. Earlier
generic registry-loader experiments failed before the marker write and left no
temporary registry keys; that approach was retired.

The approved local app repair batch passes 48 actual-renderer map artwork checks,
88 report-dialog checks and four focused viewer publisher cases. Reports use the
observed controller version or `unknown`; malformed/deeply nested viewer requests
are ignored before frame processing. A six-run 4x CPU-throttled fixture measured
median Map navigation readiness of 1,078.7 ms with eager SVG and 433.2 ms with the
repair, preserving all visible artwork and scroll height. Preview .38 is published with checked source/payload identities, inventory,
icons and privacy guards. The viewer publisher repair was deployed at an idle
guest boundary after verifying that every other replay-source byte matched
(ignoring line endings); installed source and private backup matched their expected
hashes. No controller restart or gameplay was used. Physical performance/accessibility stay in the
backlog; complete clean first-launch belongs to the required installer gate.

A fresh 13-suite offline sweep/setup check passes startup-failure retention,
candidate fallback, account-bound ownership/history, ordering, outcome counts,
delayed medal confirmation and setup operation/session checks. The current guest
is idle after exhausting eligible untried targets. This is not permission to
reset attempts or replay owned medals, and does not prove complete live reconnect
or every route outcome. Current source and decompressed Preview .38 payload
publication guards each return zero findings.

The 8 October packaged acceptance continuation reproduced and repaired two
native handoff blockers: temporary checkpoint filenames exceeding the valid
destination's path budget, and null fresh-session operation flags. The reviewed
Preview .39 artifact passes actual native fresh install/repair, dependency
imports, preserved configuration and the installed controller's authenticated
observation-only native transport. All 437 Python tests and 85 approved
JavaScript suites pass; 1,749 inventory hashes, both icons and source/payload
privacy guards pass. [Detailed evidence](installer-native-acceptance-2026-10-06.md#packaged-install-repair-and-fresh-native-handoff--8-october).
The missing environment remains not ready; clean Windows guest boot and complete
first launch are still open. No existing VM or game was changed.

The same installed .39 assets also pass fresh/repeat hidden-renderer checks
against the actual packaged setup-only controller: missing-environment navigation,
intro preference persistence and an explicit Retry after a blocked readiness
request. No commands or gameplay ran. This adds real coordinator integration to
the renderer evidence; it does not close packaged main-process launch or clean
Windows acceptance. [Scope](installer-native-acceptance-2026-10-06.md#installed-assets-startup-preferences-and-connection-retry--8-october).

## Deferred route coverage and broader acceptance

On 8 October the user required sweep fixes for 1.0, while keeping complete route
coverage and all-route outcome work outside the release gates. The following
broader route work remains tracked; core sweep blockers belong to the required
gate above.
Existing owned-medal exclusions, account boundaries, failure retention and
read-only game/save rules remain mandatory. Keep eligible missing-medal gameplay
running when possible; an exhausted queue is not permission to reset attempts.

| Area | Evidence available | Deferred work | TODO |
| --- | --- | --- | --- |
| Route coverage | 86 maps; 553/1,204 eligible map/mode pairs; zero maps entirely without a candidate | 651 coverage gaps remain. A compatible candidate is not proof of victory or current balance compatibility | S-01–S-04, S-08 |
| Source fidelity | Manual controls, waits, selectors, targeting, repeated abilities and second-special commands have offline coverage; 132 existing import signatures match current conversions | Forty-five import signatures differ; nine differing files remain host-catalog candidates, including eight with omitted command context. Resolve admission and coordinate adaptations; support other dialects' paid hero levels and exact Ace centering | R-01–R-04 |
| Placements and upgrades | Visual selection and purchase checks, held-placement recovery and fixed Chutes policy have focused regressions | Observe remaining free/paid placement, hero selection, frozen/moving terrain and exact upgrade cases during missing-medal runs | R-05–R-11 |
| HUD and results | Cash/round guards and finished-route overlay recovery have offline checks; confirmed clears demonstrate some end-to-end paths | Finish representative 1080p/1440p, panel-side and Double Cash coverage; prove bounded recovery avoids stale-frame input | R-12–R-16 |

## Deferred capabilities

Experimental assistance, boss automation and Pro entitlements remain explicitly unfinished. Their drafts must not be presented as shipped capability or used to conceal missing core acceptance. The private community bot stays outside public packages.

On 7 October the user scheduled Quests, Races, Boss Rush and Boss Events for
**v1.2, after the required 1.0 work**. Full Odyssey support was added to that
roadmap on 8 October and is the first priority after 1.0, ahead of the other
v1.2 modes. This includes a dedicated Quests tab initially
marked **Coming soon**. Their individual tasks and outcome requirements are in
the active TODO's v1.2 section; they are not prerequisites for releasing 1.0.

## Release decision

Keep publishing bounded Preview 99 repairs while production gates remain open. Do not rename an incomplete build to 1.0, erase unresolved failures or manufacture validation evidence. Once all supported account medals are earned, stop gameplay entirely and complete remaining offline or installer/UI acceptance separately.


### Latest installer and existing guest acceptance — 8 October

Preview 99 [v0.1.40-preview.99](https://github.com/Klaasawastaken/BloonsPlus/releases/tag/v0.1.40-preview.99)
passes 438 Python checks, 85 approved JavaScript suites and actual isolated native
install/repair. The bounded map-table health repair avoids false repair warnings
when the app learns positions or discovers maps, while rejecting malformed data
and preserving hash checks elsewhere. Exact package identities, payload, icons
and current source/payload privacy checks pass.

The normal updater completed an existing idle guest update to .39 with unchanged
account identity, task principal, six persistent configuration/history files and
205 original CHIMPS files. This proves that update path, not clean provisioning.
The previously observed host helper mismatch initially kept environment validation false.
The installed .40 operator subsequently repaired that helper, and a fresh actual
packaged coordinator now reaches `complete` with `environmentValidated: true`.
Guest account/task/history and 205 original CHIMPS hashes remain unchanged. This
verifies the existing-environment ready path; clean guest boot remains open. Thirteen
focused offline sweep startup/recovery/medal suites pass; the live queue remains
exhausted, with attempts and earned medals preserved. The separate clean guest
boot repair still awaits the Windows administrator prompt that was canceled.
See the [native acceptance record](installer-native-acceptance-2026-10-06.md#existing-idle-guest-update-and-runtime-map-health--8-october).


Live download verification now passes for all four HTTP/HTTPS, root/www website
variants: each returns 200 with metadata matching the public `.40` release. The
[host helper repair record](installer-native-acceptance-2026-10-06.md#existing-host-helper-repair-and-packaged-ready-state--8-october)
records the bounded repair and actual coordinator observation.
