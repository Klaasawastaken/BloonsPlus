# Bloons+ Preview 95

## Clearer startup diagnostics

Startup connection details now distinguish a missing setup API, other HTTP
failures, an incompatible protocol, malformed JSON and an unreachable controller.
When an older running controller lacks the setup API, the message explains that
the current replay should finish before reopening Bloons+ to load its update.
The actual VM status, live viewer and run controls remain independent of that
startup warning. Setup ownership and protocol checks remain enforced.

The revised message was observed in the live host interface alongside the
running missing-medal sweep. This was a renderer refresh, not a controller or
game restart.

## Safer developer route conversion

The BTD6bot importer preserves positional `cpos` coordinates and keyword
`set_upg` / `set_target` arguments. It rejects unknown, duplicate, excess and
partial coordinate arguments before changing tower selection state. Explicit
`None` coordinate defaults are kept distinct from target coordinates.

A read-only comparison of 252 existing source strategy inputs found identical
conversion results before and after the repair. Existing recordings, including
original CHIMPS, were not regenerated. This tooling fix does not prove additional
routes win; paid hero levels and unsupported source commands remain on the
roadmap. The unpublished Sunken Columns ABR draft is excluded from this release.

## Verification and limits

The complete offline Python suite passes 339 checks. Focused app startup and
Electron bootstrap checks pass, including distinct failure diagnostics and
retained startup deadlines. This release also includes Preview 94's native
installer compatibility and visible-error repairs.

This remains an unsigned preview. Clean Windows installation, complete VM setup,
UAC/reboot recovery, physical accessibility and remaining gameplay evidence are
still required before v1.0.0. Install over the existing app and let a healthy
replay finish before applying a guest update.
