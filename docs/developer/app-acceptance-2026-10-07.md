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

## Still required

- Apply approved repairs, then repeat their actual-renderer checks and the broader
  layout cases before publishing an app hotfix.
- Check populated, stale and disconnected profile states, menu filtering and
  asynchronous option changes in the full app.
- Inspect keyboard traversal and physical screen-reader use throughout the app,
  including report dialogs, errors and setup recovery.
- Complete high-DPI, weak-hardware, scrolling and live viewer acceptance.
- Keep gameplay limited to missing medals; UI inspection never authorizes an owned
  medal replay or a validation-only game.
