# Bloons+ Preview 58

## Dropdown keyboard fixes

- Enter in map search selects the visible selected option or first available match through the existing input/change handler.
- Escape closes a dropdown without also navigating to Overview; open dialogs retain their own Escape behaviour.
- Refresh open option groups when their labels change.

## Clearer run admission

- Run selected starts disabled and stays disabled without a route, with stale controller state, during an active job, or for a known owned medal.
- Use the same exact normalized map/save lookup as the Maps page, fixing false unknown medal displays for route names containing underscores.
- Label unavailable medal evidence as Waiting for game save.

## Placement evidence fix

- Reject clipped screen-edge regions as no-cash placement evidence. Infernal ABR falsely accepted a Heli at x=13, then repeatedly failed to select it for upgrades.
- An actual-function regression reproduced the false acceptance before the fix. Six HUD/placement, three held-placement and three confirmation-mode checks now pass. This does not establish a winning Infernal route or reset its failed attempt.

## Confirmed missing medal

Bloody Puddles Reverse reached victory at round 60 and its Reverse medal is present in the authoritative VM save. The sweep skips it from now on. The Preview 56 VM update completed between replays and the missing-medal sweep resumed.

## Verification limits

Browser checks confirmed Enter selection and Escape focus/page behaviour. JavaScript syntax, existing map-alias and authoritative medal-gate checks pass. The installer retains Preview 57's Settings and separate route candidates. No validation-only gameplay was started; the current healthy replay is not interrupted. V1.0 remains incomplete.
