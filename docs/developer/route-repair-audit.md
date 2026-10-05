# Replay failure audit

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

The first updated live run reproduced an unreadable panel on the first Heli input;
the next action visibly bought tier 1 instead of tier 2. The follow-up patch now
reselects twice before sending any upgrade input. If the panel is still unreadable,
no upgrade key is sent. Unselected/unchanged actions are retried ahead of dependent
steps, at most twice. A remembered expected tier prevents a delayed successful
purchase from turning the retry into an unintended higher-tier purchase. Eight
observer regressions pass. The sweep engine revision changes so failures recorded
against the older input engine can be retried without editing CHIMPS recordings.
