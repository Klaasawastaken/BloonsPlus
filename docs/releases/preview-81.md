# Bloons+ Preview 81

## Recording controls

- Add a two-Play command with separately saved input phases.
- Observe the first speed transition before input two, then confirm the final transition on a later frame.
- Keep the source's 0.2-second minimum spacing, with a fresh foreground/game-screen check between inputs.
- Resume a saved phase without blindly repeating its earlier key; retain the action when the transition is ambiguous.
- Reject stale logical-clock receipts and retain queued intent when a checkpoint save fails.

## Source importer

- Traverse source round branches chronologically, preserving independent if chains and first-match elif behavior.
- Model round reassignment without inventing a wait for that reassigned HUD value.
- Reject unsupported source loop headers and backward control.

## Verification and limits

119 focused Python checks pass, including actual replay callback wiring. All 115 pinned source plans retain their previous conversion acceptance outcomes. Incomplete manual plans remain excluded pending full end-round and source-loop timing conversion. Original recordings and game saves are unchanged; this release does not claim new winning strategies.
