# Replay failure audit

## Fresh catalog check — 5 October 2026

The current selector reports 508 selectable map/mode pairs out of 1,204 across
86 maps; 696 pairs have no eligible candidate. These are route availability
counts, not victories or a claim that every candidate meets live requirements.
All 931 active recording files pass the complete-command grammar check. The
validator now rejects unknown commands and trailing garbage rather than letting
the Python reader silently skip them. Existing route availability is preserved.

The semantic audit additionally identified 44 converted aliases containing towers
forbidden by their restricted mode (362 invalid placements across Primary Only,
Military Only and Magic Monkeys Only). Their exact contents were moved to
`route-library/unsupported-conversions/restricted-class-aliases/`, with per-line
reasons. File hashes were checked before and after moving. No CHIMPS recordings
were moved. The active folder now has 887 recordings; selectable coverage remains
508 pairs because these aliases were already rejected. These gaps still require
valid strategies; quarantining an invalid recording does not repair that mode.

This audit covers an archive of 584 failure records and a recent diagnostic
window of 150 records. A failure record is an attempt, not necessarily a distinct
route or a confirmed engine defect. The recent window contains:

| Recorded category | Attempts |
| --- | ---: |
| Gameplay defeat | 60 |
| Upgrade unconfirmed | 43 |
| Navigation bug | 26 |
| Insufficient data | 20 |
| Placement bug | 1 |

These counts describe diagnostic classifications. They do not establish that
every defeat has the same cause or that every historical route is repaired.
Private logs, screenshots, account data, and local machine details are omitted.

## Supported engine findings

- Repeated Skates CHIMPS attempts issued the first Heli top-path upgrade without
  a confirmed purchase, then consumed the next planned tier. Its larger observed
  spend was consistent with buying the earlier, missed tier. The evidence supports
  an upgrade sequence falling behind, but cash alone cannot establish the tower's
  actual tier.
- Replay currently consumes an ambiguous upgrade and proceeds. Selecting a tower
  and sending a key does not by itself prove that the selected tier changed.
- Both unchanged and rising cash can hide a purchase when income arrives during
  input. Retrying on unchanged cash alone can buy the next tier. A retry requires
  evidence that the intended path remained unchanged after selecting the tower.
- A positive cash drop proves spending only when the cash reading is reliable;
  it does not identify the purchased tier. Intended and observed tier information
  must remain distinct in the run ledger.
- Upgrade checkpoints advance when input is issued, before confirmation. A
  restart can therefore resume beyond an unresolved purchase.
- Surplus selection rejected legal first and second crosspath tiers after another
  path reached tier three, while allowing attempts to open a third path. The new
  pure legality helper checks all three paths and has focused offline regressions.

## Repair and verification boundary

Engine changes should preserve the recorded placements, timing, targeting, and
upgrade sequence in original CHIMPS recordings. Upgrade observation and recovery
belong in the replay engine; this audit does not rewrite recordings or game saves.

Tier legality is covered by offline tests. Upgrade confirmation, OCR, selection,
navigation, and placement fixes need their own focused evidence. Recorded defeat
and insufficient-data categories remain unresolved until their cause is established.
An offline fix is not a verified route win. Historical attempts require a private
attempt-by-attempt ledger linking each cause to a fix and subsequent validation;
aggregate counts alone do not satisfy that requirement.

## Initial patch evidence

- Surplus crosspath legality: five offline tests pass, including all main/secondary
  path permutations and rejection of invalid or third-path upgrades.
- Failure association: map, mode and attempt start/end times must match before
  reading old game-state evidence. Explicitly interrupted runs have their own
  category. A missing observed defeat now yields an unconfirmed outcome.
- Cash crop: the currency symbol is excluded and room is reserved for more digits.
  Removed the six-digit Deflation rewrite that forced the final digit to zero.
  Padded leading-zero readings require two agreeing alternate OCR masks.
- Local saved-frame checks recover the visible 40,000 balance after excluding
  the dollar glyph. Compressed viewer images still have digit ambiguity; resized
  previews are not equivalent to fresh native-resolution captures.
- A private, ignored repair backlog groups all 584 archived attempts into 204
  map/mode/route combinations. Only the latest 150 attempts have detailed evidence
  in this snapshot. Remaining combinations are explicitly awaiting evidence review.
- These patches were subsequently deployed. No route is declared repaired or victorious solely
  because these offline regressions pass.

## Native-frame follow-up

The initial Tinkerton CHIMPS attempt ended at round 28. Its native failure frame
shows the Village at 0-1-0, while the log issued its top-path upgrade before the
middle-path purchase. This confirms a missed upgrade, not merely ambiguous cash.

The new observer reads the panel's fifteen tier pips, rejects partial/noncontiguous
patterns, waits one second after input, and retries once through the available
upgrade button only when all observed tiers stayed unchanged on the same panel side.
Five offline regressions cover both sides, T5, successful/no-retry input, a supported
button retry, unavailable/unknown panels, and tier-ledger reconciliation with income.
The native Village frame reads 0-1-0; a left Dart panel reads 0-0-0; three screenshots
without ordinary tower panels return unknown. Input duration increased from 30 to
120 ms. Live verification is still required, especially on moving or obscured towers.

## Follow-up: selection retries and capped crosspaths

Two further faults were isolated from live attempts and the replay control flow:

- The missed-upgrade retry queue was placed inside the confirmed-purchase branch,
  making it unreachable. Commit `be72474` moves it to failed confirmation. Tests
  execute that actual branch and cover bounded retries and exact intended tiers.
- Native Heli 2-0-3 panels dim unused capped-crosspath pips to BGR 59,110,151.
  The reader rejected those selected panels as unreadable. Commit `8855121`
  recognizes the observed empty-pip state, retaining contiguous-tier and legal-path
  checks. Two native captures now return 2-0-3, and a no-panel control stays unknown.

The attempt with the retry-queue fix progressed past round 60 but ended in defeat
before receiving the capped-crosspath fix. This is not a confirmed route success.
The subsequent Workshop Hard run reached victory at round 80; the authoritative VM
save then reported Standard medal value 1049864. Its Heli upgrade initially stayed
at 3-0-2 at round 55, then the queued retry confirmed 4-0-2. A later 2-0-4 → 2-0-5
purchase also confirmed through the panel reader. This validates those observed
cases, not all routes or moving-map selection.

Unconfirmed upgrades now capture a native frame before the panel closes and retain
the observation in the run ledger. JSON sidecars survive subsequent failures;
image rotation keeps the newest 60 image files. A retained record's screenshot may
therefore be unavailable after rotation. These are private runtime artifacts.

Current offline verification: 29 Python tests pass, including actual reconciliation
control flow, metadata retention, and panel fixtures at 1080p and 1440p. The five
JavaScript regression scripts also passed during this repair pass. These checks
do not establish all-route reliability, full live resolution support, or production readiness.

The observer does not identify a tower by name. Correct selection still depends on
the recorded/tracked position; checkpoint recovery remains a separate open issue.
Unresolved checkpoint entries now refresh their tracked position and observation
on retries, rather than retaining the first failed attempt's coordinates. Resume
still needs to consume and reconcile those entries before this work is complete.
Checkpoint offsets now use original instruction indices instead of remaining queue
length. Duplicate retries and supplemental actions can no longer shift that offset.
Thirty Python regressions pass after this change; full resume reconciliation is still open.

## Ravine Hard follow-up

The 2560x1440 route, scaled to the live 1920x1080 client, lost at round 14.
After Benjamin placement, the next Dart upgrade waited for 110 cash while OCR
reported 100 for several rounds, then 6 and 0 without a planned purchase. This is
consistent with a wrong HUD crop reading lives, but requires frame evidence before
changing the layout detector. Retrieval of the logged failure frame returned file
not found. The sweep selected another candidate for the same still-missing medal;
no Ravine clear is claimed. Original recordings remain unchanged.

The subsequent `ravine#hard#1920x1080#converted#source_randyhodges.btd6`
attempt did reach victory at round 80. Its authoritative VM Standard medal changed
from 752 to 1049864. That is a confirmed Hard clear, not verification of the first
candidate or other modes. During this run, map-colour-based right-panel detection
flickered and delayed round tracking around rounds 51–62. A native frame read
62/80 with all three tested OCR thresholds; the complete tier panel was recognized
as right-side Ace 2-0-4. The new HUD fix prioritizes that panel evidence. It was
prepared after this run began, so live validation of the fix remains pending.

The first updated live run reproduced an unreadable panel on the first Heli input;
the next action visibly bought tier 1 instead of tier 2. The follow-up patch now
reselects twice before sending any upgrade input. If the panel is still unreadable,
no upgrade key is sent. Unselected/unchanged actions are retried ahead of dependent
steps, at most twice. A remembered expected tier prevents a delayed successful
purchase from turning the retry into an unintended higher-tier purchase. Eight
observer regressions pass. The sweep engine revision changes so failures recorded
against the older input engine can be retried without editing CHIMPS recordings.

## X Factor Hard follow-up

The `x_factor#hard#2560x1440#noLL.btd6` run reached the victory screens.
The authoritative VM save's `XFactor` Hard Standard medal changed from 624 to
1049864. The controller recorded `x_factor - hard clear confirmed` and stopped
before the next replay as requested. This confirms this clear only.

Cash and round HUD anchor fixes from `3014616` were built after this replay
started. Deployment completed between games; the X Factor victory does not
constitute live verification of those newer fixes. Native 1440p and interrupted
upgrade recovery validation remain outstanding.
The next selected target was X Factor Alternate Bloons Rounds, absent from the
fresh authoritative save, and it reached round 3. Hard Standard was skipped.
All 41 Python regression tests passed after deployment.

## Ambiguous upgrade confirmation follow-up

The reconciliation branch still treated an `unknown` panel observation as a
confirmed upgrade whenever cash fell. A regression using the actual branch
reproduced the false progress write. Upgrade confirmation now requires observed
tiers; cash evidence remains available for placement handling. Unknown upgrades
retain the existing uncertainty/checkpoint handling without a blind purchase
retry. All 43 Python tests pass, including the reproduced case and confirmation
despite rising cash when panel tiers are known. Guest deployment remains pending
until the active missing-medal replay ends.

## Large life-loss recovery

X Factor ABR logs showed readings 41, 15 and 9 repeatedly rejected against a
stale accepted value of 82 before the actual defeat screen. The old filter reset
its pending evidence on every large drop, making recovery impossible. It now
requires two additional OCR masks to agree and three nonincreasing readings for
large drops; normal small drops retain their two-reading confirmation. Single
glitches and disagreeing masks do not confirm a loss. Five regressions exercise
the actual replay branch, including emergency activation after sustained loss.
All 48 Python tests pass. This repairs life tracking, not proof that the ABR
strategy can win; guest deployment and live validation remain pending.

## Missing failure screenshots: clock rollback

The new X Factor ABR failure image could not be retrieved despite a successful
write. Inspection found older retained images dated several hours ahead of the
active guest clock. Rotation by modification time therefore deleted the new
capture immediately. The regression reproduces this with future-dated files.
Rotation now protects images written by the current call and expires older
future-dated payloads before normally dated images. It does not alter timestamps
or structured failure records. All 48 Python regressions pass; deployment is
queued behind the active Mesa Hard run.

## Round crop retained across panel transitions

A native Mesa frame showed 56/80 with a left Engineer panel while replay remained
at round 44 and returned unreadable round values. The per-frame layout code reset
the base crop only when no left panel was open. Switching from right to left
therefore retained the previous right-panel round coordinates. A regression of
the actual layout branch reproduced this exact transition. Base coordinates are
now refreshed on every frame before applying offsets. All 49 Python tests pass;
live validation is pending deployment after Mesa finishes.

Route syntax validation also now requires coordinates for placements/removals,
an upgrade path, numeric round/cash thresholds and supported speed values.
Missing fields previously passed the generic grammar but failed in the Python
parser. The expanded syntax regression passes; all 887 active recordings pass
the new syntax checks. No original route was modified.

Unreadable upgrade results now get at most two rechecks before dependent steps
when the exact intended tier vector is present. The existing observer reselects,
reads ownership and sends no purchase when that target is already owned.
Unknown results without an exact target still do not authorize a blind retry.
The actual reconciliation-branch regression passes; the suite now has 50 tests.
Guest validation remains pending. A later native Mesa frame showed round 69/80
and 100 lives despite the old round tracker remaining at 44.

## Mesa Hard result and watchdog recovery

The old round-only watchdog killed the controller while Mesa was still playing
successfully. The game itself continued from round 78 to a visible victory at
80; the authoritative Standard medal changed from 768 to 1049864. This is a
confirmed clear despite the controller's earlier interrupted result.

The watchdog now treats three bounded consecutive cash increases as activity,
without changing its reported round or claiming victory. Flat or oscillating
readings still time out and the overall duration limit still applies. Regressions
cover these cases and paused-time accounting. The stale HUD crop fix remains the
primary round repair; activity tracking avoids abandoning viable games when OCR
is temporarily unavailable.

## Supplemental upgrade checkpoint provenance

After deployment, auto-resume reported an unresolved upgrade absent from the
recorded route. The previous checkpoint was replaced by the next run, so its
exact entry is unavailable. A matching source-level failure is reproducible:
an unchanged surplus upgrade retry gains an exact tier target, but saving that
intent discarded its optional/supplemental origin. Resume then incorrectly
required a matching recorded instruction. Checkpoints now preserve that origin;
resume leaves supplemental purchases to the existing live surplus planner.
Unmatched ordinary route intent still fails validation. Both regressions and all
52 Python tests pass. This patch is source-only pending between-run deployment.

## X Factor ABR candidate repair

The failed ABR candidate copied Hard's opening and used a bottom-crosspath
Sniper without early camo coverage. The revised candidate opens with the existing
Engineer placement, then the same recorded Sniper position with Night Vision
Goggles and Full Metal Jacket before the hero and expensive Engineer progression.
Its later Sniper crosspath uses Shrapnel instead of faster firing. The local
price catalog gives 1,300 base cash for Engineer + 1-1-0 Sniper before difficulty
and knowledge adjustments; timing and survival must still be observed live.
The camo/lead combination is documented at
https://bloons.fandom.com/wiki/Night_Vision_Goggles_%28BTD6%29 .
Schema and crosspath validation pass. Original Hard and CHIMPS recordings are
unchanged. No live success is claimed for this candidate.

Mesa ABR subsequently lost at round 27 with 447 cash. The retained native failure
frame was successfully retrieved (clock-safe retention works in this case) and
shows camo bloons leaking, zero lives, and an unupgraded Heli. The route's Sniper
had the same bottom crosspath. Its ABR candidate now gets the same early 1-1-0
Sniper coverage and later Shrapnel using its existing map position. Both revised
candidates pass syntax and crosspath validation; both still need live attempts.
The updated life filter recorded 53 to 10 at round 27, instead of permanently
rejecting that sustained large loss. Round 27 in the log matches the frame.

## Checkpoint input refresh — 5 October 2026

Restored actions now use the current parsed recording for keys, prices and tier
intent. Only validated recovery coordinates and retry counts survive from the
saved queue. This prevents old checkpoints from retaining obsolete input settings
or sending malformed coordinates. Ten focused resume recovery tests pass,
including current-price/key restoration and rejection of non-finite coordinates.
Live interrupted-game validation and deployment remain pending.

The recovery patch was packaged and installed successfully in the idle guest on
5 October. The authoritative guest save remained readable (90 map records).
A missing-medal sweep was then requested; no owned-medal test was launched.

## Candidate fallback repair

The sweep previously discarded candidates with unknown (but not known locked)
requirements whenever any fully checked candidate existed, even after every
fully checked candidate exhausted its attempts. A regression reproduced this
premature skip. Selection now prioritizes fully checked candidates and then
considers the remaining eligible candidates. Known missing prerequisites remain
excluded. Focused fallback and Expert-first order tests pass. This engine change
is queued for a later between-run deployment, not a mid-game restart.

## Authoritative medal prelaunch check

Removed the startup path that continued without a readable save. The sweep now
waits and retries the save read every 15 seconds without game input. Immediately
before launching each selected replay it re-reads the map's saved medal: an owned
medal is skipped, unknown progress waits without consuming an attempt, and only
confirmed missing progress permits launch. Focused checks cover unavailable,
absent and malformed map records plus missing and earned Hard medals. Candidate
fallback regressions still pass. These source changes await the next batched
between-run deployment; the active healthy replay was not interrupted.
