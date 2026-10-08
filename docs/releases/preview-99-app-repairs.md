## Additions

- Map artwork checks for scrolling, filtering, saved-medal updates and fallback rendering in both themes.
- Viewer request checks covering invalid expiry values, malformed JSON and excessive nesting.

## Changes

- Load nearby medal artwork immediately and defer offscreen SVG to reduce Maps navigation work.
- Include the observed controller version in issue reports, with an unknown fallback when it cannot be read.
- Ignore malformed viewer requests before frame processing so they cannot interrupt a replay.
- Prioritize full Odyssey support as the first v1.2 task after required 1.0 work.

## Removed

- The hardcoded issue-report version and unnecessary offscreen medal SVG construction.
