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

## Clear evidence correction

The controller previously accepted a cached config medal plus a near-final OCR
round, without requiring observed victory or independently checking the save.
It could also erase that cache when round OCR lagged behind a real win. The replay
monitor now retains victory evidence only after entering gameplay. Clear reporting
requires that evidence, no observed defeat, and the authoritative earned medal.
Offline regressions cover stale victory menus, missing save data, conflicting
defeat evidence and a saved win despite unreadable round OCR. Deployment remains
batched for the end of a replay. Delayed game-save writes can still leave a result
unconfirmed until subsequent progress refresh; no clear is invented meanwhile.

## Failure-history preservation

Failure history now distinguishes a missing file from damaged JSON or access
errors. Damaged content is copied to a private timestamped .log backup before
the index is replaced; inability to preserve it aborts the write. Permission
errors no longer silently discard history. Regression cases cover truncated JSON,
incorrect shapes, missing files, denied reads and failed backups. New failures
also retain the route content hash captured at replay startup, engine version
and start time, so later source edits cannot obscure which recording failed.
Private backups remain excluded by Git's *.log rule and installer log exclusions.

## Cornfield placement dependency failure — 6 October

The converted BloonsPlayer no-harvest CHIMPS candidate, reused for Impoppable,
failed to place its Heli and Village. Native saved placement frames show red,
blocked footprints; this is stronger evidence than unchanged cash alone. Nearby
placement retries did not find a legal footprint. Recovery then skipped seven
Heli-dependent actions and five Village-dependent actions, so the recorded
defense was no longer the defense executed in game.

The final saved frame confirms a 2-0-5 Spike Factory, readable cash and an actual
defeat. It does not prove every planned tower upgrade was absent or that the
strategy itself loses when executed correctly. The immediate repair target is
legal placement and dependency-aware recovery, not an OCR-based cash rewrite.

Original CHIMPS recordings remain unchanged. A future corrected non-CHIMPS
candidate must preserve usable placement space or explicitly clear permitted
terrain, retain the required Heli/Village upgrade intent, and pass offline mode,
command and placement checks before eligibility. Exact footprint validity still
requires live evidence during missing-medal gameplay; no owned medal may be used
for testing. The sweep retained this failure and continued with another candidate.

The failure logs and native frames are retained only in private, ignored runtime
storage. No screenshots, credentials, machine paths or account data are included
in this audit. This entry is diagnosis evidence, not a completed route repair.

### Cornfield coordinate conversion check

Compared the five recorded Hero, Tack, Spike Factory, Heli and Village points
with `RatioFit` in the pinned [BloonsPlayer handler](https://github.com/piweiblen/BloonsPlayer/blob/17d624879c5ad777e82594da34450e66b2d60756/src/player.py).
At 1920×1080, every converted point agrees with the source geometry before
integer rounding. The offline comparison executes only the extracted coordinate
geometry, with an explicit screen size; it never initializes the source input
handler or sends game input.

This rules out a differing conversion formula for those five points. It does
not establish legal tower footprints, correct terrain state or placement parity
with the source game's version. Investigate blocked placement and dependency
recovery before changing the transform. Private coordinate results stay outside
the public repository.

### Later outcome and separate CHIMPS failure

Another candidate subsequently produced an Impoppable victory on Cornfield.
An independent read of the VM's Profile.Save confirmed the earned
Hard/Impoppable medal. The missing-medal sweep moved on; that owned medal must
never be rerun for validation.

The first subsequent CHIMPS attempt lost at round 14. Its logs retain Hero and
Tack placement failure frames and search diagnostics at the converted opening
points. Those warnings alone do not establish the final cause or legal replacement
coordinates. The persistent failure remains actionable, and the sweep continued
with another candidate. Original CHIMPS recordings remain unchanged.

## Repeat-ability implementation audit — 6 October

Repeat/stop-ability support already spans the BloonsPlayer importer, route parser,
recording writer, main replay dispatch and saved checkpoint restore. The scheduler
retains repeated slots as a multiset: cancelling a slot removes one entry, while
`stop all abilities` clears every entry. Restore rebinds slots through the current
key configuration rather than persisting arbitrary keys or clock values.

All eight checks in `tests/test_repeated_abilities.py` passed. They cover import
of key zero as slot ten, malformed commands, parser/writer round trips, duplicate
entries, cancellation, checkpoint validation and the actual runner dispatch/input
gate exercised with mocked frames and input. Repeated input is withheld while
placement, a route action or delayed targeting owns the input loop.

These checks prove those contracts offline. They do not establish cooldown
recognition, source-equivalent timing under every frame rate, or strategy victory.
R-01 remains open for source-command coverage; R-11 retains live timing evidence
from missing-medal gameplay only. No existing route or original CHIMPS recording
was modified by this audit.

### Selector and targeted-special checks

Four checks in `tests/test_selection_positions.py` and three in
`tests/test_targeted_special.py` also passed on 6 October. They verify persistent
source selection coordinates, invalid-coordinate rejection, full parser scaling
and recording round trips, resume/ledger selection positions, distinct special
targets, simulated key-then-target order and continued exclusion of unsupported
second-special commands. Temporary parser fixtures are isolated; no gameplay
input or original recording is changed.

This confirms existing support rather than completing every source dialect.
BloonsPlayer positional priority and non-Mortar positional targeting still carry
lossy markers; the separate EverythingMacro adapter rejects several coordinate
targeting actions. Ace centering and source-specific action semantics therefore
remain part of R-01's audit instead of being marked globally supported.

### Positional and keyword argument preservation

The BTD6bot adapter previously read `cpos` only as a keyword. The pinned Monkey
methods also accept it positionally: after the upgrade list, after target/special
coordinates, or as the first sell argument. Those valid calls could select the
original location instead of the moved tower. Keyword-only `set_upg` and
`set_target` calls also indexed an absent positional argument. Unknown arguments
and duplicate positional/keyword values could be silently ignored.

The adapter now binds the four known signatures before changing selection state.
An explicit `None` coordinate retains the source default rather than inventing a
target. Unknown, duplicate, excess and partial coordinate arguments are rejected;
unsupported Ace centering and second-special operations remain review cases.

Seven selector checks pass, including parser/scaling, recording and resume
coverage. The full offline Python suite passes 339 checks. A read-only comparison
of 252 locally available strategy files from the four source adapters found
identical conversion results before and after this fix. This proves preservation
of that source sample, not every possible source call or strategy victory. No
recording, game file or save was rewritten, and no gameplay was launched for this
check.

## Hero-picker failures — 6 October

The live sweep recorded pre-game navigation failures for Dark Castle Impoppable
with Obyn Greenfoot and Sanctuary Hard with Psi. Obyn's title was recognized,
but three Select attempts continued returning `select`, with a 0.489 green
fraction after the click. Psi's card produced unreadable title candidates during
the bounded search. Neither failure had a saved picker frame, so these logs alone
do not justify changing the selection threshold or accepting an uncertain hero.

Replay now retains one exact frame passed to hero OCR and saves it through the
existing failure-image retention on all three terminal picker branches. The
persistent error log includes the expected hero, observed and decision states,
button OCR candidates, target position, attempts, dimensions and frame age.
Missing and stale observations are labeled explicitly; no additional capture or
game input is performed by failure reporting. Non-object OCR responses are
rejected. Failure history also preserves full screenshot paths containing spaces.

Four isolated Python checks cover actual branch exits, exact image pixels,
malformed responses and freshness. The underlying Obyn/Psi recognition repair
remains open until the relevant frames establish the cause. No game/save file or
original CHIMPS route was modified by these diagnostics.

### Opening-loss retry allowance

Bloonarius Prime's CHIMPS recording lost at round 7 after cash-confirmed Boat and
Sub placements, with $72 left while the next $215 Dart placement waited. The saved
frame confirms both towers and zero lives. Comparing its Play-button crop with
the actual templates identifies slow speed; the double-arrow graphic alone is
not proof of fast speed. No placement/OCR failure is established by this frame,
and the original recording remains intact.

The sweep's timing classifier labeled this an instant loss and automatically
returned the same candidate to the pool. That contradicted the branch's stated
purpose of refunding bot-side failures. Opening timing now permits a refund only
when the persistent failure category establishes a placement or OCR failure.
Other strategy defeats retain their attempt and can move to another candidate;
the existing technical retry bound remains two. The actual sweep branch passes
regression checks for gameplay losses, uncertain evidence, corruption, unresolved
upgrades and bounded placement/OCR retries. This repair does not establish the
strategy's winning reliability, and the healthy ongoing replay is left untouched.

### Unbound Play alias — 6 October

The save-binding adapter assigned `round_start = None` for an unbound or
unsupported PlayFastForward binding, but retained the default `play = Space`.
Automatic speed/start input and manual income recovery use the latter alias,
so they could send a key the account had explicitly unbound. After clearing the
alias, the automatic branch also needed to reject `None` rather than pass it to
the keyboard sender.

Both aliases now follow the same decoded binding. The automatic branch preserves
bound-key behavior and reports a missing binding at most once every three seconds.
An absent gameplay section retains the known prior binding; an explicit section
with a missing or invalid Play entry does not invent one. The app's existing
hotkey report remains the place to resolve unsupported bindings. No game setting
or save is changed automatically.

Three focused checks execute the actual binding functions and automatic input
branch. They failed for the retained Space key and attempted `None` input before
the repair, then passed. Seven source-start and seven manual-cash checks also
pass, as does the complete 353-check Python suite. This establishes the input
contract offline; it does not prove an account with no Play binding can finish
a route. The healthy guest replay is not interrupted to deploy the change.

### Upgrade uncertainties across replacement towers — 6 October

The failure counter retained a retired tower's unresolved path as a null entry
under its route name. A later ambiguous purchase on a replacement reused that
same entry. Two distinct tower instances therefore appeared as one unresolved
purchase. Repeated replacements and multiple unresolved paths could further
undercount the evidence.

The counter now archives pending path counts at a sale or placement boundary,
then removes those entries from the active instance. Later panel confirmations
resolve only active purchases. A sale followed by placement does not count the
same retired uncertainty twice. Existing history remains unchanged.

Six added cases cover both boundaries, replacement confirmation, repeated
replacements and distinct paths. The new count assertion failed with 1 instead
of 2 before the repair. All 61 JavaScript check files pass afterward, excluding
the unpublished ABR draft; a scoped read-only review found no actionable issue.
This is diagnostic evidence, not proof that an upgrade was purchased or that
a strategy wins. It awaits the next safe deployment batch.

The live missing-medal sweep independently completed Balance Hard at round 80.
The read-only profile's Hard/Standard value is 1,049,864, above the earned bit
threshold, and the controller recorded the clear. It then continued to Balance
Magic Monkeys Only without a restart. The renewed offline coverage audit still
finds 526 eligible pairs out of 1,204 across 86 maps; 678 route gaps remain.

### Spike Factory source targeting — 6 October

The pinned BTD6bot targeting implementation uses Normal, Close, Smart, Set and
Automatic through bottom-path Tier 5. The old importer only accepted forward
Normal/Close/Smart transitions through Tier 4. It dropped Last Resort's reverse
Smart-to-Close change and Tier 5 Smart command, and Erosion's positional Set.

The importer now preserves the source's shortest forward/reverse sequence.
Reverse commands use the read-only profile's `ReverseChangeTargeting` binding;
missing or unsupported bindings block prerequisites rather than inventing a key.
Positional Set retains a separate tower selector and special-1 target click.
The pinned source has a concatenated-string typo in its Set guard. Smart and
Automatic positional Set calls remain lossy instead of receiving invented clicks.

Replay batching now leaves unbound retarget/special steps for the normal guarded
dispatch, and reselects a changed source coordinate on a fresh action. Recording,
scaling and resume retain reverse intent and the current saved key. Twelve focused
checks, the complete 362-check Python suite, ten setup-transport checks and all 61
JavaScript check files pass; the unrelated unpublished ABR draft is excluded.
A scoped read-only review found no actionable issue.

Separate Last Resort and Erosion CHIMPS candidates pass the complete Python
parser and JavaScript legality audit. No original recording was replaced. Offline
eligibility rises to 530/1,204 pairs; 674 gaps and Firing Range remain. These counts
do not prove victories, exact live targeting or account prerequisites. Deployment
is queued with the next release batch after the current replay finishes.

During this work, Balance Magic Monkeys Only's expanded tower shop covered the
round HUD while cash continued to rise. The controller reported the last valid
round, 36, while current round OCR returned -1. A private screenshot and log
excerpt preserve the evidence. End-of-actions HUD recovery requires further
investigation; no victory is inferred from income or a stale round.

### Magic Monkeys Only held placement — 6 October

Balance's dedicated Magic Monkeys Only route subsequently lost. Persistent
history retains repeated wizard `upgrade-unselected` observations; the sweep
continued to Rake Hard. The actual pre-defeat frame contains the placement close
anchor (template score 0.975) and purple shop cards covering more than half of
each of three sampled rows. The old observer required cyan cards and returned
false, allowing tower-selection clicks while placement remained active.

Held-placement recognition now accepts the evidenced purple cards alongside
cyan, while retaining the close-anchor and two-row requirements. A missing
anchor, one colored row and neutral cards remain negative. An input fixture
confirms cancellation precedes the requested tower selection at 1080p; scale
checks cover 960, 1920 and 2560 widths. Nine focused checks and the complete
365-check Python suite pass. A scoped read-only review found no actionable issue.
The captured private frame also qualifies with the new observer.

This change is published in v0.1.1-preview.99, separately from the first Preview
99 installer. After Rake Hard finished with victory and a saved medal, the shared
update completed; six installed guest file hashes match the hotfix payload. The
sweep resumed for missing Rake Alternate Bloons Rounds. This does not rewrite the
original route or prove that every upgrade failure is repaired. A future Magic
missing-medal outcome remains open. The private
account screenshot and full logs remain outside public code and packages.


### End-of-actions HUD recovery audit — 6 October

The Balance Magic failure also exposed a separate source gap: HUD recovery is
gated on the next action needing cash or being `await_round`. With no remaining
action, both flags are false, so an unreadable round counter does not enter the
existing close-panel recovery branch. With readable cash and a purchase queued,
the round counter can also remain stale. The log's income and old round are not
victory evidence. Recognition of the held Magic shop now prevents one observed
selection failure, but does not close this general R-13 gap.

A future repair must preserve pending placement and ability targeting intent,
use fresh overlay evidence, and keep ordinary completed-route gameplay running
until a real result. No additional centre-click behavior or round estimate was
introduced during the hotfix deployment.


### Approved finished-route HUD repair — 6 October

The approved bounded repair extends the existing unreadable-HUD branch only
when route actions are finished. The existing cash/pending-round behavior stays
in place. Recovery waits one second, captures a new frame, checks INGAME/focus/
pause/input ownership and requires the existing held-placement or panel observer
to positively identify a blocker. Unknown layouts receive no recovery clicks.
Pending route work and the immediately preceding action defer this recovery.

An observed orphan placement uses its close control; a confirmed panel receives
the requested two centre clicks. A second capture authorizes the second click
so a result screen cannot be clicked using older INGAME pixels. Issued recovery
input closes the iteration's automatic Play and repeated-ability gate. No round
is manufactured, no route is restarted and no victory is inferred.

The actual empty-queue recognition gate first failed offline. Eight focused
checks and the complete 373-check Python suite now pass. Review caught the
second-click stale-frame hazard; its new changed/missing-frame regression failed
before repair and passes afterward. A scoped re-review found no actionable issue.
The private Balance Magic frame cancels the orphan placement without a world
click in an injected-input fixture. Published as v0.1.2-preview.99 and installed only after Rake Reverse finished
with victory and its saved medal. Seven installed guest hashes match the published
payload, the app/game connection is ready and the sweep resumed for Quarry Magic
Monkeys Only. Future missing-medal gameplay must supply live recovery evidence.


### Rake Alternate Bloons Rounds failure — 6 October

The missing-medal attempt defeated at the last trusted round 30. Persistent
history classifies it as gameplay-defeat, with 1,920 cash and no unresolved
upgrade marker. Recorded Tack, Heli and Village purchases have panel-tier
confirmation. The mode's imported Hard opening therefore needs strategy review;
the evidence does not support blaming a missed upgrade. It reached a 0-1-0
Village but not its planned 0-2-0 camo upgrade before the loss. The sweep retained
the failure and continued to missing Reverse; the owned Hard medal stays skipped.

The [round-30 ABR reference](https://bloons.fandom.com/wiki/Round_30/ABR) lists
nine spaced camo leads. This supports checking combined camo/lead coverage and
ability timing as an explicit hypothesis. It does not identify the exact bloons
that leaked in this account's frame or prove a replacement opening. A dedicated
[Rake ABR guide](https://www.youtube.com/watch?v=VandVCZAPYc) was located, but its
full video could not be fetched in this check; no unseen placement/timing data
was copied or marked verified. Private failure evidence remains excluded.

The final pending action explicitly required 2,160 cash for the 0-2-0 Village,
against 1,920 available: a 240 shortfall. The route had already spent 3,670 on
Heli 2-0-3 before placing that Village at round 27. This gives a concrete
purchase-priority hypothesis: reserve early camo support before the costly
Heli upgrade. Any separate candidate must also confirm that the intended
lead-popping tower lies inside the Village's influence, including its radius
upgrade if required. Reordering the budget alone does not prove coverage or
victory; no replacement route was published from this audit.

### Firing Range source coverage clarification — 6 October

The pinned source includes `firing_rangeHardChimps.py` with Rosalia, coordinates,
upgrade order and round timing. Read-only re-conversion preserves 55 actions but
marks the second special as lossy. Earlier gap wording about no candidate does
not describe this current source. Exact `TowerSpecial2` binding, hero movement
and its positional click must be preserved before a separate complete candidate
can be eligible. No source plan was launched or original recording rewritten.

### Chutes Medium opening observation — 6 October

The missing-medal replay could not confirm its third Dart at the recorded point
after thirteen attempts. Cash remained unchanged and the held-placement observer
identified a pending placement. The placement recovery logged the problem,
skipped zero dependent actions and continued the existing game. Other tower and
hero placements succeeded, and later upgrades have panel-tier confirmation.

This is a placement incident, not confirmed defeat evidence. A later private
frame shows round 49/60, 150 lives and an owned 2-3-0 Desperado panel. The
original CHIMPS recording and its placement coordinates remain unchanged.
Chutes' alternating lanes and central statue obstacles are recorded in the
mechanics catalog, but they do not establish why that particular placement
failed. Review legal footprints and the live frame before proposing a separate
candidate; do not apply blind coordinate changes or infer victory from survival.

The replay subsequently reached `VICTORY_CONFIRMED` at round 60, and its saved
Medium/Standard medal changed from 768 to 1,049,544. Stop-after-replay ended the
controller before the next attempt, allowing the batched installer update.
This account now skips Chutes Medium permanently. The incident still warrants
placement review for other missing modes; this clear does not prove the original
CHIMPS strategy or its reused placement succeeds in every mode.

### Chutes fixed-terrain retry classification — 6 October

A read-only retrieval of the saved failed Dart screenshot shows a red, illegal
placement ghost at the recorded `(832, 620)` point on the track intersection.
This supplies positive placement-refusal evidence rather than relying on cash
alone. The account frame remains private and is excluded from publication.

The launcher interpreted Chutes' `phase-aware-route-required` catalog status as
changing placement terrain. That flag made the replay use the same coordinate
for every retry. Chutes alternates its active bloon lane; its tower surfaces do
not move. The approved correction uses `multi-lane-required`, retaining the
alternating-lane and statue instructions while restoring the existing bounded,
visually checked nearby placement retries. No recording coordinates were edited.

An offline regression executes the production filename parser and replay launch
policy for ordinary and boss-shaped filenames. It failed with the previous
classification and passes with the correction. Ten other catalog-driven map
guards and Geared/Sanctuary movement flags remain intact. The full 387 Python
checks and 63 JavaScript check files pass; two isolated Electron checks needed
sandbox escalation. A scoped independent review found no material issue.
Successful live Dart placement at a nearby point remains unverified. Deployment
completed only after the healthy Chutes Hard replay finished: eleven guest file
hashes match the published payload, and installed/running versions both report
`0.1.6-preview.99`. The missing-medal sweep resumed on Quiet Street Magic Monkeys
Only after fresh setup, idle and game-readiness checks.

Chutes Hard subsequently reached `VICTORY_CONFIRMED` at round 80. Its saved
Hard/Standard value changed from 816 to 1,049,864, and stop-after-replay saved the
clear before ending the sweep. It ran on the previously installed build; the new
placement correction did not interrupt that game and cannot receive credit for
its victory. The earned Hard medal is now permanently skipped.

## Firing Range second-special candidate — 6 October 2026

The pinned BTD6bot source places Rosalia and issues second-special target clicks
at rounds 11 and 16. Conversion previously omitted both commands, so no complete
Firing Range candidate was eligible. The approved extension preserves them as
`special2`, parsed into the existing selected-tower special action with slot 2.
Targets and selection positions remain independent; source clicks, waits,
abilities, placements and upgrade order remain intact.

The saved `TowerSpecial2` keyboard binding is mandatory. No key is guessed when
the profile is missing, the action is unbound or the binding is unsupported.
Both candidate ranking and direct starts enforce this condition. Recording and
resume retain the slot; recording distinguishes modifier keys and keypad events
from ordinary navigation keys that share a scan code.

The separate candidate passes the full Python parser: 57 executable lines,
57 recognized commands and 57 parsed actions. Ten focused checks and all
394 Python checks / 64 JavaScript check files pass. Scoped review exposed direct
start and recorder collision gaps; regression checks now cover both repairs.
Original recordings are unchanged. No local Firing Range victory is claimed.

Coverage increases to 535 of 1,204 map/mode pairs, with no map entirely lacking
an eligible candidate. Compatibility counts do not establish victories.

## Quiet Street Magic Monkeys Only — 6 October 2026

The healthy replay reached `VICTORY_CONFIRMED` at round 80. The sweep recorded
the clear, and the VM save-backed progress reports the completed Hard/MagicOnly
medal. The sweep continued to Downstream Magic Monkeys Only. The new
second-special code did not run during this clear; it receives no credit for
the result. Quiet Street's earned medal is permanently excluded.

## Flagged Hard source filenames — 6 October 2026

Rake's Alternate Bloons Rounds alias has the same executable strategy as its
Hard recording, including tower placement and upgrade order. The original file
ends in `#noMK.btd6`; the selection guard checks only a flag-free source filename,
so it does not compare these actions. This explains admission of the unchanged
alias, not every cause of the observed round-30 defeat.

A read-only audit of the current eligible catalog found 55 such map/mode
candidates across ten maps. It compares canonical executable actions against
unconverted Hard originals with the same map and resolution. Confirmed local
target wins and the explicitly supported Easy/Medium reuse are excluded from
this count. The bounded guard repair awaits approval. The audit changes no
recordings and supplies no new victory claim.

## Downstream Magic Monkeys Only — 6 October 2026

The replay reached `VICTORY_CONFIRMED` at round 80. Saved Hard/MagicOnly progress
changed from 657 before victory to 1,049,865 afterward. This clear ran on the
previously installed v0.1.6-preview.99 controller. The second-special batch did
not interrupt it and receives no credit for the result. The earned medal is
permanently skipped. Stop-after-replay retains the safe deployment boundary.

The shared update then completed with sixteen installed file hashes matching
the published v0.1.8-preview.99 payload. Inventory and running-controller
versions agree. Fifteen save-backed profile groups match between guest and host;
achievement values match with `steam-local-guest` and `steam-local-vm` labels,
without host fallback. These checks establish transport and artifact identity,
not every decoder's meaning or a live second-special victory. Fresh idle/setup
checks passed, and missing-medal gameplay resumed on Streambed Magic Monkeys Only.

## Streambed Magic Monkeys Only — 6 October 2026

The replay reached `VICTORY_CONFIRMED` at round 80; saved Hard/MagicOnly progress
reports 1,049,865 and the sweep recorded the clear before advancing to Spring
Spring Hard. Streambed's earned medal is permanently skipped.

## Spring Spring Hard and observations persistence — 7 October 2026

The replay logged `VICTORY_CONFIRMED` at round 80. The current VM save's
SpringSpring Hard/Standard record decodes to an owned medal using the production
decoder. The sweep recorded two victories and no defeats, then stopped on an
`EPERM` rename of its secondary `game-observations.json.tmp` file. This is a
post-victory persistence failure, not a strategy defeat. The earned Hard medal
must remain excluded when gameplay resumes. The bounded write-recovery design
awaits approval; no permission changes or game/save edits were made.

A read-only observer of the actual host VM profile relay captured 45 samples
over 461 seconds, including two XP changes and one Monkey Money change following
victory. Production rate calculations returned finite values after the sampling
window. Full account values and profile paths remain private. This evidence does
not establish actual veteran rollover, disconnect recovery or every decoder's
meaning. Offline rate checks additionally cover ordinary rank changes,
regressed XP and the fresh baseline required on entering veteran XP.

Live panel observations confirmed the first Wizard's bottom-path transition
from Tier 4 to Tier 5 and the second Wizard's top-path Tier 1, 2 and 3 purchases.
The round-40 log reported lost lives, with later observations at 88. Retain that
opening incident for strategy review, without replaying this account's owned
medal or inferring the exact initial lives from earlier noisy OCR. A clear does
not establish that the route's `noLL` filename still describes every run.

The [read-only transition observation](replay-transition-timing-2026-10-06.md)
records the subsequent 65-second interval to recognized gameplay. No recovery
click, wait or route was changed from this observation alone.

### Observations-file diagnosis — 7 October 2026

A read-only guest probe found Spring Spring's Hard medal absent from the main
observations file but present in the leftover temporary file. This is consistent
with a completed write followed by a failed replacement. Saved-profile progress
remains the authority for excluding the earned medal.

At observation time, all four installed BloonsPlus processes and the SSH query
process were elevated. Both observations files permitted non-mutating handles
with delete access and full sharing. The earlier metadata probe also found
neither file read-only and no applicable delete-deny rule. These present-time
checks do not reproduce the earlier rename failure or identify a competing
reader. No privilege, ACL, file content, scheduled task or gameplay was changed.
The bounded persistence repair still awaits approval; the sweep remains stopped
with two victories and zero defeats.

The repeated second-special approval was reconciled with the installed
implementation rather than producing another candidate. Fresh offline checks
passed all ten targeted-special Python tests and the JavaScript binding and
direct-start suites. Live Firing Range behavior remains unverified.

## Legacy BTD6bot admission audit — 7 October 2026

The read-only source audit compared 184 existing BTD6bot-labelled recordings
against their pinned source conversions. Of these, 177 have currently convertible
source and seven retain source omissions. Three recordings lack required moved
selectors and 26 lack required positional special commands; these groups overlap.
In total, 30 recordings have at least one of those findings.

A separate read-only invocation of the production catalog admission functions
found all 30 affected files excluded and none admitted. The invocation used the
actual route bodies, hashes, selection guard, legality rules and local verification
records. Requirement display construction was stubbed because this audit checks
catalog admission, not account unlocks or queue selection. No map-position sync,
gameplay operator or file writer was exposed to that invocation.

The seven omitted-command drafts comprise Ancient Portal's Dartling targeting,
five Ace-centering plans (Bloonarius Prime, Muddy Puddles, Peninsula, Rake and
Spice Islands), and Ravine's unavailable Spike Close transition. Existing
recordings remain unchanged. These results show that the known incomplete copies
are not current candidates; they do not establish exact command equivalence for
the other 177 recordings or certify any strategy victory. R-01 and R-04 remain
open for exact command comparison and unsupported dialects.

## Cubism Half Cash — 7 October 2026

The active missing-medal run progressed from round 61 through round 80 while
installer acceptance continued. It reported `VICTORY_CONFIRMED` for Cubism Half
Cash, followed by `clear confirmed`. A separate read-only VM profile request
decoded Cubism's Half Cash medal as owned through the production save decoder.
The sweep recorded two victories and zero defeats in this job, then automatically
navigated toward Skulltweak. No restart, deployment or manual gameplay input was
needed. Cubism Half Cash must remain skipped for this account.
