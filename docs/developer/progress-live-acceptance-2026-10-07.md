# Live progress acceptance — 7 October 2026

This is scoped, read-only evidence from the current host dashboard and VM
controller. It does not certify every profile field, account or disconnected
state. No player balances, account identifiers, file paths or screenshots are
included here.

## Confirmed missing medal

Encrypted Magic Monkeys Only reached `VICTORY_CONFIRMED` at round 80. The
authoritative VM `Profile.Save` response changed from an unowned medal to owned
under the production shared decoder. The existing sweep then selected Cubism
Half Cash without a restart or user input. One victory and zero defeats were
recorded for this sweep at that observation. Encrypted's owned medal must never
be replayed for this account.

## Host dashboard and reload

The host and guest status APIs agreed on the running state and victory/defeat
counts, with a fresh VM relay rather than stale status. A background browser
inspection of the host dashboard displayed Cubism's advancing round and those
same counts. The Activity panel showed the new Encrypted medal and its age
advanced from four to five minutes. Reloading that dashboard retained the medal
history, one victory, zero defeats and the active map; the game was untouched.

The player source identified the VM profile save. Net MM/hour and XP/hour became
finite after the sampling window. Immediately after a fresh renderer reload,
both rates returned to unavailable while new samples accumulated, rather than
displaying an old session's rate. This confirms presence and reset behavior at
these observations; prior source-rate evidence covers actual XP and balance
changes. Spending, veteran rollover and disconnect behavior still need broader
live acceptance.

## Required hero and upgrades

The Monkey Meadow Hard chooser displayed Etienne and Engineer path requirements.
Etienne and all eleven displayed Engineer upgrades agreed with the authoritative
VM save's acquired entries. Only required paths and tiers appeared. The third
path's T1–T5 pills shared one actual rendered row, including XXXL Trap at T5.
The already-owned medal kept Run Selected disabled. The chooser was inspected
without launching a route, then returned to Overview and the temporary tab was
closed.

These are aggregate path requirements across the route's towers, not a claim
that one Engineer can have every listed path tier simultaneously. The check does
not establish every tower's catalog mapping, missing/unknown upgrade display,
narrow-view layout or renderer behavior during a disconnected VM. Those remain
P-01, P-04, P-05 and P-07 acceptance work in the active TODO.

## Host and guest route catalogs

A fresh comparison on 7 October at 02:31 UTC covered all map/mode pairs from
both controllers: 535 host pairs and 558 guest pairs. Each of the 23 guest-only
pairs has an exact-hash local victory receipt in the guest's catalog. All 23
target medals are already owned in the independently fetched authoritative
VM save, and all 23 route files match the host bytes and pass current target-mode
legality checks. They must not be played again to reconcile the catalogs.

For map/mode pairs present on both sides, 281 candidate entries differ in local
verification or candidate presence. All 281 are guest-verified and all target
medals are already owned; none has unreadable ownership. Four entries are
absent from the host's corresponding candidate list. The underlying endpoint
uses the controller's own verification history; the desktop catalog endpoint
does not relay guest history. Private account history must not be copied into
public source merely to make those counts equal.

An exhaustive byte comparison covered the 174 distinct files referenced by
these 281 entries, with no failed reads. Of those, 173 match exactly. The guest's
Rake Reverse file places Sauda before the first Tack Shooter, whereas the host
does the reverse. Apart from line-ending representation, the remaining command
sequence matches. The guest snapshot is retained privately for a deliberate
reconciliation; neither file was replaced during this audit.

This evidence rules out these catalog differences as a source of additional
missing-medal opportunities at this observation. It does not certify historical
verification receipts as saved-medal evidence, prove every route's strategy,
or complete restart/disconnect synchronization acceptance. The stopped sweep's
fresh Obyn/Psi picker failures are separate blockers; restarting without their
repair repeats navigation failures rather than earning medals.

## Live viewer backend

Four actual requests on 7 October at 02:36 UTC exercised the host's screen relay
and the guest's screen endpoint while the game was idle. Every response had
HTTP 200, `image/jpeg`, `Cache-Control: no-store` and a successfully decoded
960×540 frame of approximately 98 KB. Within each host/guest request pair, the
response bytes matched exactly. After a two-second interval, the second pair
contained different bytes, demonstrating a refreshed capture rather than a
permanently stale frame.

The two fresh host captures took 391 and 360 ms; their immediate guest cache
reads took 15 and 31 ms. These are individual observations, not throughput or
tail-latency estimates. The calls used the existing viewer endpoint and renewed
its application-owned request lease. No image was saved, no game/save file was
edited and no gameplay input was sent.

This establishes actual backend capture, response decoding, cache reuse and
host/guest transport at this observation. It does not establish renderer focus
handling, the ten-second publisher expiry during an active replay, suspended
browser behavior or sustained CPU/memory use. Those remain acceptance gates;
the earlier fourteen isolated renderer lifecycle checks emulate focus/page
events and must not be described as physical desktop validation.


## Hero search evidence retention

The terminal hero-picker screenshot could show Corvus even when the requested
hero was Psi: every OCR observation replaced the previous frame. That obscured
the earlier unreadable title, so the final screenshot could not diagnose it.

The approved picker investigation now retains up to 48 distinct OCR observations
per search. Each lossless PNG preserves the original title and Select-label pixels
at their original coordinates and blanks the rest of the frame, including account
and currency areas. Deduplication requires equal OCR metadata **and** equal image
bytes; two different unreadable cards must not collapse into one observation.
Encoded payloads are limited to 512 KiB each and supported images to 3840 × 2160.
There are no additional captures, clicks or selection decisions. Encoding failures
are warnings, not gameplay failures. A new search resets the collection.

On a failed search, `HERO_PICKER_SCAN` records identify each retained frame by
index, page, card position and observation time. The existing bounded private
failure-shot directory holds the images. The terminal full-frame evidence still
uses the existing `hero-picker` suffix. These images are diagnostics, not proof
that a hero is owned or selected; the ordinary title/button checks still apply.

Offline evidence: the missing earlier-frame regression and the distinct-image/
identical-OCR regression both failed before their fixes. All 16 focused hero tests
and the complete 419-test Python suite pass. Independent review found the OCR-only
deduplication weakness; its correction was reviewed with no remaining findings.
The diagnostic patch was hash-verified in the idle guest before one missing-medal
sweep attempt. Recognition and gameplay success remain unconfirmed at this point.


### Psi title repair

The instrumented missing-medal attempt supplied 32 masked picker observations.
The first image visibly reads **PSI**: the yellow letter fill merges into the
yellow ribbon under the warm-color mask. The full-width natural OCR also includes
the decorative ribbon tail and misreads the short name. The picker had reached
the correct card; accepting a guessed alias or assuming selection was unnecessary.

A narrow natural-color crop (reference 2560 × 1440: x=860, y=40, width=260,
height=95) now contributes a candidate only when its normalized text is exactly
`psi`. Partial names from longer titles are discarded. Select/Selected confirmation
is unchanged. The first 300-pixel-wide crop failed the scaled 960-pixel check;
the final width passes actual helper checks on all 32 retained images, with two
Psi readings and no false Psi matches among the other 30 observations. Resized
Psi frames at 960, 1920 and 2560 also pass. Resized frames are offline evidence,
not three independent live-resolution acceptance runs.

The new synthetic exact-name/fragment regression failed before implementation.
All 69 approved JavaScript test files pass; the unrelated pending ABR draft stays
excluded. Independent scoped review reported no actionable helper findings.
The helper was atomically installed with a rollback copy at a freshly confirmed
idle boundary and its hash verified. The missing-medal sweep was then resumed;
selection, gameplay and medal outcome still require live confirmation.


Live follow-up: the repaired helper verified the existing Psi layout hint, the
picker completed, and Three Mines 'Round Deflation entered gameplay at its normal
round-31 start. Psi's placement had cash confirmation; the replay continued through
its planned tower placements and upgrades. No saved-medal clear is claimed here.
The healthy replay stayed running while the installer was built.
