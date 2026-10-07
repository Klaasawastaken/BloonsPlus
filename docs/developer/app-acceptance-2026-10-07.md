# App acceptance evidence — 7 October 2026

Source baseline: `a5f2d79`. This records an isolated actual Electron/Chromium
inspection of the existing app, not full accessibility or production acceptance.
The [production gates](production-1.0-gates.md) remain open.

## Isolation and scope

The fixture served the actual root `index.html`, app styles and scripts from a
temporary loopback origin. User data, session data and logs used a fresh temporary
directory. External requests were blocked. Synthetic controller responses included
idle run status, a protocol-correct completed setup session, two maps with recorded
route choices and an explicitly unavailable profile. No real game, controller,
save, account or setup operation was used.

The only POST was to the fixture's setup-session bootstrap response. All other
mutations were rejected. The app was rendered in a hidden offscreen window; this
does not establish physical display, screen-reader or weak-hardware behavior.

## Completed observations

| Check | Scope | Result |
| --- | --- | --- |
| App sections | Overview, Maps, Achievements, Automation, Boss events, Run logs and Settings; light/dark; 1,440×900 and 1,080×680 CSS-pixel viewports | All 28 cases had no document/main horizontal overflow or view element extending beyond the right edge. |
| Active navigation | Same 28 cases | Exactly one current navigation item, matching the visible section. |
| Button names | Actual Chromium accessibility trees for all 28 cases | No exposed button without an accessible name. This does not prove every name is useful or physical screen-reader interaction works. |
| Custom menus | Map, difficulty, variation and intro controls in both themes and sizes | All 16 visible-control openings stayed within the viewport. Native values and labels were present. Native Escape input closed each menu and restored focus to its trigger. Other keyboard behaviors have separate earlier evidence. |
| Required tiers | Synthetic route requiring Dart and Sniper paths | All 16 path-row observations retained their tier pills on one row, including T1–T5. Unknown profile data remained marked with `?`; this fixture does not prove populated-save upgrade mapping. |
| Local artwork | 360 visible image observations across the cases, including repeated map thumbnails | All observed images loaded. Boss art used `object-fit: contain`, with matching 200:220 natural and 220:242 displayed proportions in all four boss-page cases. |
| Renderer execution | All cases | No uncaught renderer error or unexpected mutation request. |
| Completed setup | Protocol phase `complete` plus all eight component observations ready | The first-launch configuration panel was hidden; Settings retained its ready status and component disclosure. |

The first menu probe programmatically clicked controls below the viewport. Its
out-of-bounds menu results were discarded as invalid user-interaction evidence.
Repeating after making each control visible and allowing its animation to finish
produced the menu results above. An initial setup fixture also used an unsupported
`ready` phase; that was corrected to `complete` before final acceptance. No product
code was changed to make either fixture pass.

## Confirmed remaining defects

### Intro preference clipping

Visual inspection found that the Appearance row's flex layout compressed the intro
field. A focused repeat checked Full, Reduced and Off in both themes at both
supported sizes: **all 12 selected-label observations were clipped**.

At 1,080 pixels the Off trigger measured 36.31 pixels wide and its text span had
zero available pixels. At 1,440 pixels Reduced's text needed 46 pixels but received
35. Popup containment and accessible naming passed, but those checks alone did not
prove the selected value was readable.

The field's `min-width: 0` enhancement combines with the surrounding nonwrapping
Appearance row to permit this shrinkage. A bounded responsive-grid repair has been
proposed: give the intro a readable column and move its explanation below the
controls while retaining the narrow-layout stack and preference behavior. Approval
is pending; the runtime is unchanged.

### Text contrast

Computed-style checks covered 108 normal/large text observations against actual
opaque or alpha-composited flat backgrounds. Sixty-four other observations were
excluded because gradients or opacity need different evidence. **Thirty-eight
observations failed**; they repeat three light-theme style problems across sizes:

| Style | Foreground / background | Contrast | Required |
| --- | --- | --- | --- |
| Primary action text | `#ffffff` / `#d36b50` | 3.507:1 | 4.5:1 |
| Invalid hero/tier pill | `#a94f36` / `#f9e4dc` | 4.447:1 | 4.5:1 |
| Unknown tier pill | `#596f79` / `#e6edf0` | 4.462:1 | 4.5:1 |

The dark Automation eyebrow uses `#5c6eaa`. Even against black it reaches only
4.266:1, so it cannot meet 4.5:1 against the observed darker background. Its exact
gradient-backed rendered ratio was not certified by the flat-background audit.

A bounded repair is proposed for those text styles and the dark section label.
Candidate light colors were checked mathematically: white on `#b5533d` is 4.919:1,
invalid text `#a24b33` on its existing background is 4.779:1, and unknown text
`#556a73` on its existing background is 4.800:1. These are design calculations,
not evidence that a repair has been implemented or rendered. Approval is pending.

## Populated-profile refresh — follow-up at `a7b2db6`

A separate actual-renderer fixture used the real bundled upgrade catalog and
synthetic VM profiles with partial Dart/Sniper unlocks, an owned Sauda, explicit
missing/earned Cubism medals and two sample balances/XP counters. A deliberately
newer scanner snapshot falsely reported Hard and CHIMPS as earned. Older scanner
responses were then held while the save poller read a newer profile independently.
All controller mutations remained rejected except synthetic session bootstrap.

The complete repeat recorded **13 passing checks and two failing checks**:

| Check | Result |
| --- | --- |
| Readable profile applied | Rank, Monkey Money and tower XP matched the synthetic profile. |
| Authoritative false medals | Saved missing Hard/CHIMPS overrode the newer false-positive scanner data, including the visible map card. |
| Required paths and T5 | Exact owned T1–T4 showed checks; unowned T5 showed a cross and the catalog upgrade name. |
| Owned hero | The required Sauda displayed a verified unlock from the synthetic save. |
| Idle missing-medal chooser | The missing selected medal could be selected while idle; no start request was sent. |
| Automatic refresh | Changed money and tower XP appeared after 8.710 seconds, within the ten-second save cadence, while scanner responses were held. |
| Newly earned medal | Saved Hard became owned and disabled the selected-run action immediately. CHIMPS remained missing. |
| New upgrade ownership | The added Dart T5 changed to a check without a page reload. |
| MM/XP rates | A synthetic 60-second sample interval with +400 MM and +1,200 XP produced 24,000 MM/hour and 72,000 XP/hour. This is arithmetic/UI evidence, not observed gameplay earnings. |
| Opening Maps again | The newly earned Hard medal appeared; CHIMPS remained missing. |
| Late scanner response | Releasing older requests did not restore the older balance, XP, medal or T5 state. |
| Disconnected money/rates | A synthetic VM-save HTTP 503 cleared availability, displayed money and both rates. |
| Disconnected tiers after explicit redraw | Recomputing route requirements changed every upgrade tier to unknown. |
| Disconnected requirements immediately | **Failed:** the save-unavailable path left the previously rendered hero and tier claims in place. |
| Disconnected hero after explicit redraw | **Failed:** cached hero ownership still displayed “Unlocked in game save” and a check. |

The initial fixture used an invalid top-level `await` expression for its final
disconnect call. That script error was corrected before the complete repeat; it
was not a product failure.

The unavailable-save handler clears `localProfile` and calls the general render,
but it does not immediately rebuild route requirements or invalidate the separate
cached `heroes` object. This explains the two independent stale-display failures.
A bounded repair is proposed: invalidate current hero/upgrade claims, redraw
requirements with explicit unknown states, and restore verified states only after
a readable save returns. Preserve cached earned-medal protection. Approval is
pending; no runtime behavior was changed.

A separate read-only catalog audit covered all **26 tower names and 390 T1–T5
path slots** in the frontend's merged bundled catalog. Every slot had a catalog
name. All **1,176 candidates across 535 host map/mode pairs** used requirement
tower slugs recognized by the frontend. This rules out missing catalog slots or
unmapped tower slugs in that snapshot; it does not prove every save identifier,
localized name, live ownership state or strategy is correct.

Both running host and guest catalog endpoints returned HTTP 200 with all 390
entries equal to the source's merged catalog. The Preview 99 hotfix installer
contains both catalog JSON files; their decoded contents and merged 390 entries
equal the source. All 26 tower-XP keys in the observed readable VM profile map to
frontend display names. No account values were retained in public evidence. These
checks establish transport, packaging and key-name coverage; they do not prove
every acquired-upgrade identifier or unlock value is interpreted correctly.

## Concurrent live observations

The missing-medal sweep stayed active during this work. Frozen Over Magic Monkeys
Only had completed all forty route actions by the observed round 58, continued
through round 70 and reached a round-80 victory. Its authoritative VM-save medal
was independently decoded as earned before reporting the clear. The job then
advanced to Double HP MOABs, with seven victories and zero defeats recorded.

Two observed transient game-state replacement warnings did not stop gameplay.
A later raw-JSON check showed the next map/mode's game state advancing from round
3 to 7; its timestamp was 1.122 seconds behind the VM controller's clock, and the
profile-read timestamp differed from that clock by three milliseconds. This is
recovery/freshness evidence for those observations, not a guarantee that every
persistence failure recovers. No private profile, screenshot or filesystem path
is included here.

## Still required

- Apply approved repairs, then repeat their actual-renderer checks and the broader
  layout cases before publishing an app hotfix.
- Repair the evidenced unavailable-save requirements/hero failures and repeat
  the populated/stale/disconnected checks. Broader profile schemas, menu filtering
  and asynchronous option changes remain open.
- Inspect keyboard traversal and physical screen-reader use throughout the app,
  including report dialogs, errors and setup recovery.
- Complete high-DPI, weak-hardware, scrolling and live viewer acceptance.
- Keep gameplay limited to missing medals; UI inspection never authorizes an owned
  medal replay or a validation-only game.
