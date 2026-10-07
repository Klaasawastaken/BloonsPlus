## Additions

- Account-aware medal history, including Ninja Kiwi account changes at the same Steam save location.
- Offline checks for account switches, missing identity and safe history migration.

## Changes

- Confirmed clears must belong to the account that started the run.
- Existing earned medals and failed attempts are preserved when history is linked to a verified account.
- An ambiguous history migration waits for a consistent save instead of replaying medals or guessing their owner.
- Account identifiers are hashed before leaving the read-only save decoder.

## Removed

- Shared medal and failure exclusions between different owners at the same save location.

This is a Preview 99 repair. Full 1.0 acceptance remains in progress.
