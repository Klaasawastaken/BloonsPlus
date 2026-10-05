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

## Current local patch

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
- VM deployment is pending. No route is declared repaired or victorious solely
  because these offline regressions pass.
