# Bloons+ Preview 69

## Preserve routes after pre-game hero failures

- Classify the exact hero-not-found error as navigation failure.
- Record failed hero selection before gameplay without consuming a route attempt.
- Continue to the next map, leaving that route retryable in a later sweep.
- Preserve normal attempt handling once gameplay starts or a defeat is observed.

Actual sweep-branch fixtures, failure classification and authoritative medal admission checks pass. Includes Preview 68's full hero-name crop and bounded unchanged-card search. No route history or game save is erased, and no new victory is claimed.
