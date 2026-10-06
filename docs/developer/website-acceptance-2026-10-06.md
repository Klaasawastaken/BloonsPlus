# Website acceptance evidence — 6 October 2026

Source baseline: `811916f`. This is a focused browser and source audit, not a
claim that the website meets every accessibility requirement.

## Checks completed

| Check | Evidence | Result |
| --- | --- | --- |
| Phone and tablet reflow | Home, Features, About, Wiki, Contributors, Subscriptions, Download, Privacy and Terms at 390×844 and 768×844 | All 18 page observations stayed within the viewport width. |
| Main landmarks and names | Same 18 observations | One main landmark and one H1 per page; no missing image `alt` attribute or unnamed button detected. This does not prove every accessible name is useful. |
| Active primary category | Main navigation after each page load | Home, Features, About, Wiki, Contributors and Subscriptions each identified only their own category. Download and legal pages are outside that navigation. |
| Mobile menu | Features at 390 pixels | Open/close label and expanded state changed; Tab reached Home; Escape closed the menu. |
| Wiki search | Query `medals`, then clear | Account progress remained visible; clearing restored the article list. |
| Active wiki article | Navigate to Getting started | Getting started alone had `aria-current="page"` in the sidebar. Phone rendering showed its highlighted row. |
| Billing controls | Monthly to Annual | Pressed states changed together; annual price became $49.99 per year with its billing note. No checkout exists. |
| Narrow comparison | Subscriptions at 390 pixels | The table scrolled inside its named, keyboard-focusable region, rather than expanding the page. |
| Artwork above the fold | Main pages at both narrow widths | No broken loaded image observed. Features' Wizard and Quincy used `object-fit: contain`; their phone render preserved proportions. Lazy images below the fold were not counted as failed downloads. |
| Static local references | Parse all 26 HTML files and resolve local `href`/`src` targets and fragments | No missing target or unmatched static anchor found. External destinations were not checked by this scan. |
| Release download lookup | `node tests/test-site-releases.js` | Passed latest-preview selection, drafts, missing assets, download URL validation and offline fallback. |
| Reading progress | `node tests/test-site-progress.js` | Passed reduced-motion, visibility and single-pending-frame behavior with mocked browser state. |

Desktop screenshots of Home and Subscriptions and phone screenshots of Features,
Getting started in both themes, and Subscriptions were inspected. This visual
sample does not establish complete desktop coverage or all interactive states.

## Open readability defect

The rendered light theme uses `--muted: #708177` for secondary text, including
11–17 pixel paragraphs and billing notes. Its contrast is **3.79:1** against
the `#f5f6f1` page background and **4.12:1** against white. Both combinations
fall below the **4.5:1** normal-text target in
[W3C's contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).

Proposed narrow repair: change the light-theme secondary-text token to `#56685e`.
Computed contrast against the five main light surfaces is 4.84–5.94:1. Preserve
dark-theme colors, artwork and layout. The bounded design is awaiting review;
the CSS has not been changed. Translucent/gradient surfaces and accent-colored
small text require separate rendered checks; this token calculation does not
prove every text/background combination passes.

## Remaining acceptance

- Repair and recheck the evidenced secondary-text contrast issue.
- Measure other text, controls and focus indicators on actual rendered surfaces.
- Complete keyboard traversal, focus restoration and skip-link checks across
  articles and longer pages, including zoom and text scaling.
- Check screen-reader announcements and dynamic navigation focus.
- Observe real reduced-motion changes; the current focused reading-progress test
  covers its mocked contract only.
- Inspect lower-page lazy artwork and README/banner composition at relevant sizes.
- Verify deployed pages after publication; local preview evidence does not prove
  GitHub Pages or custom-domain behavior.

W-04 remains open until the outstanding checks and defects are resolved.
