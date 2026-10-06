# Bloons+ Preview 76

## Route conversion

- Preserve ordinary Engineer First/Last/Close/Strong targeting from the pinned BTD6bot source.
- Keep moving-platform selection coordinates attached to targeting commands.
- Preserve separate foam/trap targeting semantics instead of confusing them with the ordinary target cycle.
- Keep plans with manual-round or Ace-centering omissions excluded. Original recordings are unchanged.

## Round-reader repair

- Validate the complete counter before normal and fallback reads advance replay state.
- Reject numerators beyond the round total, totals from another game mode, padded digits and malformed counters.
- Use the selected mode limit when replaying a harder source recording on an easier mode. Keep bounded bare-digit reads available when the slash is temporarily unreadable.

## Included repairs

This installer also includes Preview 75's context-aware Settings controls and rejection of declared manual-round omissions.

## Verification limits

Four Engineer regressions cover all 16 transitions, moving selectors, unsupported targets and four actual source plans. Nearby Spike, selection-position and conversion-guard checks pass. Twelve round-structure, HUD and freshness checks also pass, including both actual reader statements and all 14 game modes. No new route victory is claimed. Route generation tooling is included in the source repository; gameplay remains on the existing replay runtime.
