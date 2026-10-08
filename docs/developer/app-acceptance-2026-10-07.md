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

## Appearance defects and completed repair

### Intro preference clipping

Visual inspection found that the Appearance row's flex layout compressed the intro
field. A focused repeat checked Full, Reduced and Off in both themes at both
supported sizes: **all 12 selected-label observations were clipped**.

At 1,080 pixels the Off trigger measured 36.31 pixels wide and its text span had
zero available pixels. At 1,440 pixels Reduced's text needed 46 pixels but received
35. Popup containment and accessible naming passed, but those checks alone did not
prove the selected value was readable.

The field's `min-width: 0` enhancement combines with the surrounding nonwrapping
Appearance row to permit this shrinkage. The approved startup/polish plan now
provides a responsive grid: the intro has a readable column and its explanation
sits below the controls. Narrow windows stack the fields; preference logic is unchanged.

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

The implemented repair separates action colors from decorative accent colors:
white on `#b5533d` is 4.919:1, invalid text `#a24b33` on its existing background
is 4.779:1, and unknown text `#556a73` on its existing background is 4.800:1.
The dark section label uses the existing muted token. The old blue primary
hover background also failed with dark text (2.338:1); hover now uses coral
colors appropriate to each theme.

### Repair verification

The approved startup plan's preferences and theme acceptance scope covers this
bounded CSS repair. No game, controller, account or save behavior changed.

- The permanent hidden-renderer regression passes **60** selected-label,
  persistence and geometry cases: Full/Reduced/Off, light/dark, 1,440 and 1,080
  pixel windows at 100/125/150/200% zoom, plus 550 and 420 pixel widths.
- All 20 menu openings retain their three choices inside the viewport. Native
  Escape closes the menu and restores focus. Reinstating the old flex rule in
  the isolated fixture reproduces clipping/layout failures.
- **100** computed-style contrast checks pass, including forced primary-button
  hover after transitions settle. The section label is checked against the
  theme's solid background; this does not certify every gradient pixel.
- The broader seven-section repeat passes all **28** layout/name cases with no
  unexpected mutations or renderer errors. Its **108** flat/composited-background
  contrast observations now have zero failures; the same 64 gradient/opacity
  observations remain excluded.
- All **73** approved JavaScript test files pass. Independent review found no
  remaining actionable issue in the CSS or renderer fixture. Its temporary
  profile is cleaned after Electron exits, and network access is restricted to
  synthetic local responses.

Physical DPI, assistive technology, real populated profiles and weak-hardware
acceptance remain separate open gates. The unrelated unapproved ABR draft is
excluded from this release.

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

## Viewer request lifecycle — follow-up at `fbc27aa`

An isolated actual Chromium renderer loaded the full app and its unmodified
viewer script. The fixture served a small synthetic PNG rather than reading the
VM screen. CDP emulated page focus; dispatched page-transition events exercised
the existing suspension/restoration handlers. No physical focus change, real
back/forward-cache restoration or live VM capture is claimed.

All **14 checks passed** in the complete repeat:

- Inactive categories and an unfocused window issued no capture requests.
- A focused Automation category decoded and displayed the PNG blob and refreshed
  at the existing two-second interval.
- Leaving the category stopped polling and aborted an in-flight request; losing
  focus also stopped requests.
- Page suspension cleared the image URL and stopped polling. Restoration resumed
  the viewer.
- HTTP failure displayed the inline unavailable state and then recovered without
  a page reload.
- A slow response was aborted at the bounded timeout, followed by recovery. At
  most one capture request was in flight throughout the checks.
- No real controller mutations were issued. Only the synthetic setup-session
  bootstrap was accepted by the fixture.

The first fixture checked the server's close event immediately after the browser
reported its timeout. The close event arrived asynchronously and produced a
false failure; the complete repeat waits for both observations. Product code was
unchanged.

This proves browser request, image and handler behavior under the stated
emulation. The replay's frame publisher uses a ten-second viewer lease, so these
checks do not prove that guest JPEG work stops immediately after focus is lost.
Physical lifecycle, actual capture latency and live resource usage remain A-02
acceptance work.

## Switching save sources — follow-up at `fbc27aa`

A separate full-app fixture started with one synthetic save containing an earned
Cubism Hard medal, Sniper XP and partial upgrades. It then read a different file
identity containing only a Logs record and Dart XP. Scanner responses were held
to isolate the independent save poller. No real account was switched.

The **nine checks completed: six passed and three failed**:

| Check | Result |
| --- | --- |
| Initial owned medal and XP | The first profile applied; its selected owned medal disabled the run control. |
| Same-source rate sample | The expected synthetic MM/hour and XP/hour appeared. |
| New source's explicit values | Rank, balance and Dart XP changed to the second profile. |
| New source's rate baseline | Both rates became unavailable rather than comparing different profiles. |
| New source's hero and upgrades | The new hero list and empty acquired-upgrade list replaced the former claims. |
| Mutations | No real controller mutation was issued. |
| Maps absent from the new save | **Failed:** the previous source's Cubism record retained its saved-source label and earned medal. |
| Tower XP absent from the new save | **Failed:** the previous source's numeric Sniper XP remained. |
| Reopening Maps | **Failed:** Cubism still displayed the previous source's earned Hard medal. |

The rate sampler tracks source/file identity, but the independent save merger
only overlays fields that the latest profile contains. It does not remove prior
map records or tower-XP claims when that identity changes. This is distinct from
temporary disconnection, where previously earned-medal protection should remain.
A bounded repair to separate those cases awaits approval. The fixture establishes
these renderer failures; it does not establish a replay of an owned medal or a
defect in the sweep's separate authoritative-save guard.

## Saved upgrade identifiers — follow-up at `fbc27aa`

Catalog presence and recognized tower slugs do not prove acquired-upgrade matching.
A read-only comparison of the current shared matcher against the 390 regular
path slots and the upstream [generated upgrade identifier source](https://github.com/gurrenm3/BTD-Mod-Helper/blob/master/BloonsTD6%20Mod%20Helper/Api/Enums/UpgradeType.cs)
found two unmatched display names: Mortar's **Shell Shock** and Skywarden's
**Storm Pulse**. The generated source uses `Shockwave` and `StormsPulse` in their
respective ordered tower upgrade groups. The downloaded source's SHA-256 was
`ac25698641ad3f116f2537ff5d954e0e0f73aba0691dfb7b78bc3b974e9dd457`.

The same two path gaps appeared when comparing frontend ownership matching with
the backend's contiguous upgrade-cap calculation against a readable guest save.
Other acquired identifiers outside the regular catalog include paragons or other
content and were not classified as missing regular tiers. No account balances,
paths, full profile or acquired-upgrade list is published here.

A two-alias repair is proposed, scoped to those towers and shared by the UI,
route preflight and optional upgrade caps. Approval and its regression checks
remain pending. The observed guest catalog has fifteen candidates requiring
Mortar top-path T3 or higher and none requiring Skywarden middle-path T1 or higher;
these are requirement counts, not evidence of ownership, admission or victories.
No mod was installed, no external source was executed, and no route or game/save
file was changed.

## Concurrent live observations

The missing-medal sweep stayed active during this work. Frozen Over Magic Monkeys
Only had completed all forty route actions by the observed round 58, continued
through round 70 and reached a round-80 victory. Its authoritative VM-save medal
was independently decoded as earned before reporting the clear. The job then
advanced to Double HP MOABs, with seven victories and zero defeats recorded.

During the viewer/source-switch follow-up, Double HP MOABs completed all forty
actions before the round-65 observation and continued to its round-80 victory.
The authoritative guest-save decoder independently confirmed that medal; the
job then started missing Half Cash with eight victories and zero defeats. No
runtime reload or validation-only gameplay was used.

Two observed transient game-state replacement warnings did not stop gameplay.
A later raw-JSON check showed the next map/mode's game state advancing from round
3 to 7; its timestamp was 1.122 seconds behind the VM controller's clock, and the
profile-read timestamp differed from that clock by three milliseconds. This is
recovery/freshness evidence for those observations, not a guarantee that every
persistence failure recovers. No private profile, screenshot or filesystem path
is included here.

## Still required

### Measured navigation and scrolling — 7 October

An isolated actual Electron renderer used the current app files and route
catalog, synthetic idle/profile APIs, and 2,000 synthetic log lines. Network
access was restricted to its fixture server. It measured all seven sections at
1440 × 900 with software rendering, both normally and with fourfold CPU
throttling. No gameplay, real save reads or controller mutations occurred.

The initial document load took 87.5 ms in this run. Navigation to Map Progress
took 123.2 ms normally and 433.5 ms under CPU throttling; that throttled visit
included a 330 ms main-thread task while rendering 86 map cards. Other section
visits took 7.5–39.1 ms normally and 32.3–109.8 ms throttled. These are measured
click-to-two-frame times, not promises for every computer or completed network
refresh.

After each section settled, 87 programmatic scroll-frame intervals were
measured. Their 95th percentile was 16.7–16.8 ms, with none above 50 ms. The
Boss Events section had no scrollable overflow, so its frame samples do not
prove scrolling. Physical wheel input, populated real profiles, live VM capture,
hardware acceleration and actual weak hardware remain separate acceptance
work. The map-navigation stall is a concrete performance target; this check
does not establish that all app scrolling feels smooth.

A separate cold-navigation CPU sample reproduced the slowdown under the same
fourfold throttle. It measured 822.4 ms with profiler overhead; 501.7 ms of
sampled self time was attributed to the native `scrollTo` call, followed by
324.6 ms in the browser's program frame. Those samples identify the synchronous
navigation/scroll boundary for deeper tracing. They do not distinguish every
layout, paint or compositor cost, and the instrumented value is not comparable
to the unprofiled navigation result as a performance regression.

### Map-card rendering investigation — 7 October

A follow-up used fresh hidden renderer windows, the same synthetic API fixture,
fourfold CPU throttling and three cold samples per variant. Moving the scroll
resets ahead of navigation shortened the synchronous handler but left first-frame
readiness near the baseline. It shifted work to browser rendering rather than
resolving the stall. A diagnostic variant that hid medal SVG artwork reduced
style-recalculation time substantially, identifying that artwork as a material
part of the cost. Hiding medals is not an acceptable product change.

An offscreen-card containment probe also improved initial readiness, but its
estimated card heights changed the document's scroll extent as cards rendered.
That probe is not ready to ship. No containment rule or reordered navigation
has been added to the app.

A separate lazy-artwork probe retained every map card, medal span, title, earned
state and filter, while attaching the decorative SVG artwork when its medal
entered the viewport's 200-pixel margin. In three fresh samples each:

| Observation | Current renderer | Fixture-only lazy artwork |
| --- | --- | --- |
| Median click-to-two-frame readiness | 729.4 ms | 327.5 ms |
| Visible medals with artwork at that observation | 84 of 84 | 84 of 84 |
| Document height before/after scrolling to the last card | 5,759 / 5,759 px | 5,759 / 5,759 px |
| Last card's medals with artwork after settling | 14 of 14 | 14 of 14 |
| Total attached map-medal SVGs after that jump | 1,204 | 400 |

All six samples used the current 86-card catalog and reported no fixture errors.
These timings are comparable within this probe, not directly with earlier runs
on a differently loaded host. The probe changes only its own hidden renderer;
the shipped app remains unchanged. The bounded production repair awaits design
approval and must cover observer cleanup, unavailable-observer fallback, filters,
data refresh, theme changes, scrolling and accessible labels before publication.
Physical hardware, live capture and screen-reader acceptance remain open.

During these checks, the repaired X Factor Alternate Bloons Rounds candidate
earned its missing medal. The controller observed its round-80 victory, and a
separate read of the actual guest save decoded that medal as earned. The sweep
then moved to Mesa Alternate Bloons Rounds with one victory and zero defeats.
No healthy replay was interrupted, and the newly owned X Factor medal must not
be replayed for validation.

- Apply approved repairs, then repeat their actual-renderer checks and the broader
  layout cases before publishing an app hotfix.
- Repair the evidenced unavailable-save requirements/hero failures and repeat
  the populated/stale/disconnected checks. Broader profile schemas, menu filtering
  and asynchronous option changes remain open.
- Repair the observed source-switch carry-over and resolve the two saved-name
  gaps before declaring map/tower progress complete.
- Inspect keyboard traversal and physical screen-reader use throughout the app,
  including report dialogs, errors and setup recovery.
- Complete high-DPI, weak-hardware, scrolling and physical/live viewer acceptance.
- Keep gameplay limited to missing medals; UI inspection never authorizes an owned
  medal replay or a validation-only game.


## Approved profile-display repair — 7 October 2026

The five previously observed failures were reproduced before editing: two disconnected ownership checks and three source-switch checks. The approved implementation now shares readable-save application between both pollers. It removes unscoped scanner medal and tower-XP claims before projecting authoritative save fields, so absent records cannot inherit another account's data on a later scan. Non-ownership artwork fields are preserved.

A temporary disconnect preserves the last readable map ownership for run protection, while hero, knowledge and tier requirements redraw as unknown and numeric tower XP clears. Network/parse failures invalidate availability as well as explicit unavailable responses. A newer failed read also supersedes an older readable response. Same-path account changes reset rate baselines using the opaque account identity; no account values are built into the app.

The shared matcher now recognizes Mortar **Shell Shock → Shockwave** and Skywarden **Storm Pulse → StormsPulse**, scoped to those towers. Browser matching and route readiness share the same catalog helper.

Independent review found a late-scanner/disconnect sequence that could revive another account's tower XP. A deterministic regression failed before the repair and passes after clearing unscoped XP in the unavailable branch. Same-path rate mixing also failed its negative control before the identity change. All 26 final actual-renderer checks (17 populated/disconnected and nine source-switch checks) and all 78 approved JavaScript suites pass. Publication guard reports zero findings. These synthetic checks do not certify a real account switch, every save identifier, or all live rate semantics.

## Issue-report keyboard and privacy acceptance — 7 October

The actual app renderer passes **80 observations** across Run Logs and Settings,
light/dark themes and 1,440 × 900 / 550 × 700 windows. Complete Chromium keyboard
events open the report, traverse its controls, close it with Escape or its Close
button, restore the launching control and preserve the current section. The
dialog stays within the window with no horizontal overflow. Accessibility-tree
reads expose its dialog title, description field, Close button and GitHub link.

Synthetic log and description values are absent from both the preview and the
constructed issue URL, while round/map context remains. No issue is submitted,
external page opened, real profile read or VM command issued by this fixture.
A plain native-dialog control independently reproduces Chromium's neutral BODY
focus boundary in hidden windows; underlying app controls must still reject
focus while the modal is open. This is Chromium keyboard/accessibility-tree
evidence, not physical keyboard or screen-reader certification.

An intentionally non-modal copy fails all eight modal-state and all eight
background-focus checks. Independent read-only review found no actionable
fixture issues. No production app behavior changed for this acceptance work.

The audit separately found a real report-context defect: the checked .37 payload
has package version `0.1.37-preview.99`, but its report body still hardcodes
`0.1.0`. A bounded repair using the existing local controller identity API has
been proposed for approval. The fixture above does not claim version accuracy.

Final verification passes all **81 approved JavaScript suites**, with the
unapproved ABR draft suite excluded. The source publication guard reports zero
findings; all 55 local links across the revised task/audit documents resolve.

## Viewer backend files and recovery — 7 October

Seven isolated scenarios now exercise the actual `lib/live-screen.js` module
with real temporary files and synthetic Node capture processes. They cover a
fresh replay frame, the one-second response-cache boundary and ten-second lease
renewal, eight simultaneous requests sharing one child, failed-child recovery,
missing-runtime recovery, and stale/future-dated frame rejection. All seven pass,
as do the existing freshness and frontend lifecycle checks. No game capture,
VM request or gameplay input is performed. Synthetic bytes do not verify JPEG
capture or Python process integration; earlier live relay evidence stays separate.

A separate extracted-function check found a request-data defect in
`publishViewerFrame`, called directly from the replay loop. A valid request
publishes and an expired request skips. JSON `null` and an array each raise an
uncaught `AttributeError`; a string expiry raises `TypeError`; a non-finite NaN
expiry is accepted and publishes. The current handler catches file/JSON errors
but does not validate the parsed shape or numeric expiry. These are isolated
reproductions, not evidence that a recorded defeat had this cause.

The bounded request-validation repair has been proposed for approval. No replay
behavior was changed or deployed during this audit. Actual active-replay lease
expiry and sustained live capture costs remain open acceptance work.


## Approved app repair batch — 8 October

The user approved the measured map-artwork change, report-version correction and
malformed viewer-request validation. These are local implementation results;
publishing and guest deployment are recorded separately.

Map cards retain every fixed-size medal span, title and earned/missing/unknown
state. Artwork near the viewport is populated immediately after one grouped
bounds read; offscreen cards are observed with a 200 px margin. Replacing cards
disconnects the previous observer, and stale callbacks are ignored. Environments
without IntersectionObserver use eager artwork. Forty-eight actual hidden-renderer
checks cover both themes, scrolling to the last card, stable scroll height/labels,
unchanged-data node retention, filtering, saved-medal changes, observer cleanup
and eager fallback. Before the repair, the new checks rejected eager SVG loading
and missing observer cleanup; after the repair all checks pass.

Three fresh samples per variant at 4x CPU throttle measured median two-frame Map
navigation readiness at 1,078.7 ms for the eager control and 433.2 ms for the
production repair. All six runs retained the same 5,759 px scroll height, all 84
visible medal artworks and all 14 artworks on the last card after scrolling.
An initial timing probe exposed delayed first-observer delivery; the immediate
nearby-card population above addresses that observed blank-artwork window.
Software-rendered, synthetic fixture timings are not a physical hardware claim.

Issue reports now request the current controller identity asynchronously when
opened. Protocol/version validation, unknown fallback, edits during loading,
request timeout and stale-response rejection have focused checks. The actual
renderer passes 88 observations, including the returned synthetic release version
in the GitHub issue body; the existing non-modal negative control still fails.
No issue is submitted during these checks.

The actual replay publisher is extracted without game imports for four Python
cases. Invalid JSON shapes, expiry values, non-finite numbers, unfinished JSON
and excessive nested arrays cause no frame work or publication. Valid leases
still publish; expired leases and an unfocused game skip processing. A nested
10,000-array fixture reproduced RecursionError on the project Python before the
added exception guard, then passed. Existing viewer lifecycle, freshness and
seven real-file/synthetic-process backend scenarios also pass. No live screenshot
or gameplay input was used.


### Preview .38 publication

Release v0.1.38-preview.99 is published with one 247,061,514-byte installer.
Its SHA-256 is `2032ee3d3e501394f60d1fadefcbe271cccb96203ba1fe29941590a2488266f9`.
The final artifact passes 128 runtime source comparisons, all 1,749 inventory
hashes, four package identities, the native embedded identity, exact appended
payload, both seven-frame application icons and source/payload privacy guards.
The unrelated route draft is excluded. All 436 Python cases pass. The broad
JavaScript run passed 83 of 84 suites; the remaining privacy fixture lacked the
new local request globals, was corrected and passed its focused rerun. The
original failure result is retained privately. No full guest update or
validation-only gameplay was performed. Required clean Windows and physical
acceptance gates remain open.
