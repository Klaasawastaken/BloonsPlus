# Bloons+ Preview 56

## Honest failure-round evidence

- Timestamp accepted round readings separately from general game-state updates.
- Keep the last readable counter for diagnosis without treating unreadable frames or resumed checkpoints as new observations.
- Classify a loss stage only when new-format round evidence is no more than ten seconds old, comparing guest timestamps with each other.
- Label stale counters as last readable values; preserve historical records and observed defeat counts.

## Placement recovery and map guidance

- Include Preview 55’s live placement-confirmation discovery and Preview 54’s UI/capture diagnostics.
- Allow one stable new missing-medal attempt only for the two evidenced Infernal Reverse/ABR Heli cases. Keep unrelated exclusions and earned-medal skipping.
- Clarify Infernal’s narrow Heli/Farm edge strips and footprint reservation. Original routes, including CHIMPS, are unchanged.

## Verification limits

Focused offline runtime, freshness, loss classification, ledger and attempt-revision checks pass. These checks do not establish a winning Infernal strategy or every historical route repaired. No validation-only game was launched; V1.0 remains incomplete.
