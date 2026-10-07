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
