# Replay transition observation — 6 October 2026

One read-only observer followed an existing missing-medal replay and its next
target. It started no validation game, sent no input and changed no settings.
The observer polled fresh VM status every ten seconds and retained selected log
events privately. Durations below use timestamps printed by the same VM process
clock, rather than comparing host and guest clocks.

## Observed transition

Streambed Magic Monkeys Only reached `VICTORY_CONFIRMED` at 14:43:20. Its saved
medal was independently confirmed before the next game. Spring Spring Hard
reached `screen INGAME` at 14:44:25. The elapsed transition was **65 seconds**.

| Segment | Logged interval | Duration |
| --- | --- | --- |
| Victory through return-home cleanup and replay exit | 14:43:20–14:43:46 | 26 s |
| Replay exit through the next process's first recognized home screen | 14:43:46–14:43:49 | 3 s |
| Home through hero-selection state | 14:43:49–14:43:50 | 1 s |
| Select the required Striker Jones hero | 14:43:50–14:44:00 | 10 s |
| Hero completion through map-navigation state | 14:44:00–14:44:04 | 4 s |
| Map navigation through recognized gameplay | 14:44:04–14:44:25 | 21 s |

During cleanup, the log changed from Victory to Unknown, then
`QUIT_GAME_CONFIRM`, then the main menu. The existing replay branch cancels
that confirmation. This is a target for fresh-frame navigation investigation;
the event sequence alone does not identify every misclassified frame or prove
which click first caused the delay. Do not reduce waits or change coordinates
without the relevant screen evidence.

## Limits and next work

This is one observed transition, not a benchmark or a representative average.
The ten-second polling interval limits the precision of untimestamped selection
and saved-medal events. Individual reconciliation and next-target computation
latency cannot be inferred from those events. Neither is included in the table
as an independently measured operation.

Capture fresh evidence for the result-screen transition before changing its
recovery behavior. Separate recognition, intentional input delay, process
startup, loading and target selection in later timings. Preserve saved-medal
reconciliation, input ownership and healthy-run boundaries. Continue observing
only gameplay needed for missing medals.
