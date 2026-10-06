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
