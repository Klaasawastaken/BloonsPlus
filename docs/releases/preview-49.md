# Bloons+ Preview 49

## Medal-first automation

- Removed the separate live route-verification run type.
- Removed its one-attempt-per-map branch and skip rules.
- The missing-medal sweep remains the completion workflow, continuing eligible modes without replaying earned medals.
- Simplified sweep status to display this workflow directly.

## Verification

Five existing offline sweep checks pass: authoritative medals, alternative candidates, Expert-first/resume ordering, outcome counts and delayed save confirmation. Actual backend calls reject both removed legacy sweep types before starting the runtime. No game was launched solely to validate a route.

Full route coverage, paid hero levels, explicit Auto Start control and clean-PC installation remain unfinished. This is a preview release.
