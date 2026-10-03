# Experimental AI test plan

The AI remains read-only until a route passes offline validation and a supervised in-game test.

## Data collected

- map, mode, resolution, and route source
- screenshot dimensions and normalized coordinates (`x`/`y` in 0..1)
- track polygons, water polygons, obstacles, and buildable regions
- tower placement, tower type, hero, upgrade path, round, cash before/after
- ability use, target mode, pause state, and observed failure reason

## Candidate pipeline

1. Import a verified or recorded route.
2. Normalize coordinates to the current game window.
3. Reject placements outside detected legal regions or inside obstacles.
4. Generate bounded variants by changing one placement or upgrade timing at a time.
5. Score coverage, cost, range overlap, round survival, and prior route confidence.
6. Export candidates for review; do not send input automatically.
7. Run one supervised candidate with a visible emergency stop.
8. Mark verified only after a victory and saved medal are both confirmed.

## Safety gates

- experimental controls default off
- no memory access or game-file modification
- no candidate can replace a verified route automatically
- stop on unreadable screen, unexpected menu, missing hero, failed purchase, or round stall
- every action and screenshot is logged with a timestamp

## Tomorrow's first test

Use Monkey Meadows on Easy with a short recorded route. Compare detected buildable regions and placements against the route, then test one candidate at a time with the live control switch still disabled until the reader agrees with the screenshot.
