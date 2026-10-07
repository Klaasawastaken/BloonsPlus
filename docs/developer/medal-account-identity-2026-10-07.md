# Medal history and account identity

## Approved repair

Runs and confirmed-medal history must belong to the save/account that started
them. A later regressed save must not cause an earned medal to be replayed, and
a source change must not receive clear credit.

The existing implementation separated Steam save paths. It did not distinguish
two Ninja Kiwi owners using the same path. A synthetic full-loop check reproduced
that second owner incorrectly inheriting the first owner's medals.

## Implementation

- The read-only decoder hashes the save's explicit `ownerID` with a dedicated
  namespace. It returns the digest, never the raw owner value. Empty, malformed
  or unavailable identities cannot enable path-only gameplay in the new decoder.
- Sweep identity combines the normalized save path with that opaque owner
  digest. Existing launch and confirmation checks therefore detect same-path
  account changes too.
- Upgrade from the old path-only ledger requires every old positive medal to
  exist in the fresh save. A mismatch is ambiguous: it may be a regressed save
  or another account. The bot waits for a consistent source rather than silently
  attaching those medals to an owner or replaying them.
- A successful migration keeps the old ledger, copies its confirmed positives
  and failed attempts, and records the association using opaque keys. Existing
  newer attempt records take precedence. Later owners get independent attempt
  buckets, including when an older global attempt ledger still exists.
- Game files, saves and original routes are never changed by this repair.

## Evidence

The actual guest schema contains a nonempty string `ownerID`. A read-only
preflight checked every positive in the legacy history against the fresh save;
all matched. Only counts and validity flags were retained by the audit, with no
owner values or profile exported. This establishes migration readiness on that
snapshot, not a live account-switch experiment.

The field is also described by the independent
[BTD6 save converter's format investigation](https://github.com/lbrooney/BTD6-Save-Converter/blob/main/REVERSE_ENGINEERING.md).
Mutable header metadata and wallet identifiers are not used as account identity.

`tests/test-save-account-identity.js` exercises the real decoder projection with
synthetic owners, stable hashes, distinct owners and invalid inputs.
`tests/test-sweep-medal-lifecycle.js` now covers 27 complete-loop scenarios,
including same-path owner changes before launch and after victory, positive
history regression, retained failed attempts, ambiguous migration, and a later
owner encountering an old global failure ledger. The latter first failed in
independent review, then passed after explicit per-owner bucket initialization.

All 71 approved JavaScript test files and 420 Python checks passed during this
repair. No gameplay was launched for validation. Real account switching and
broader clean-machine acceptance remain separate production gates.
