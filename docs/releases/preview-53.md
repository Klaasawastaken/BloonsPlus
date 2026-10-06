# Bloons+ Preview 53

## Upgrade reliability

- Give upgrades added after a route ends an exact target path/tier, matching the safeguards already used for recorded upgrades.
- Preserve that target independently of other towers or later ledger changes, so panel checks, same-tier retries and resumable checkpoints can use it.
- Label surplus upgrade log paths as path_index, consistently using the internal zero-based index.
- Validate restored tower/history ledgers before replacing any state; damaged caches cannot partially restore purchase data.
- Include Preview 52’s nine additional offline-converted route candidates.

## Verification limits

The actual surplus planner previously returned no exact tier intent; the regression now passes. Two upgrade-intent checks, twenty panel-observation checks and five checkpoint checks pass. Four ledger validation checks and eleven resume checks pass; the current VM’s eighteen-tower snapshot is accepted read-only. Original recordings remain unchanged. These checks do not prove all upgrades or routes reliable in live gameplay. No validation-only game was launched; V1.0 remains incomplete.
