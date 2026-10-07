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

## Deployed-site spot checks

The browser reached the clean HTTPS [production domain](https://www.bloonsplus.com/)
and the Features, About, Wiki, Contributors, Subscriptions and Download pages on
6 October. The refreshed Home hero and Features layout are deployed. The primary
categories checked identify their own navigation item.

Loaded artwork includes Wizard and Quincy on Features, Sauda on About, Benjamin
on Contributors and Gwendolin on Subscriptions. Character images use
`object-fit: contain`; initial offscreen lazy images were rechecked after loading
rather than treated as broken downloads. This is a sample, not a complete artwork
or accessibility audit of the deployed site.

The deployed [Download page](https://www.bloonsplus.com/download/) resolves its
installer and release-notes links to Preview 90. Its displayed 234.9 MB size
matches the local release metadata of 246,311,732 bytes. The installer was not
downloaded or executed for this website check.

### Latest-release follow-up

A later browser observation on 6 October reached the same deployed HTTPS Download
page. Its installer link and release-notes link both resolved to
**v0.1.0-preview.94**. The rendered release label matched that tag and displayed
**235.4 MB**, consistent with the 246,836,142-byte release asset under the site's
current binary-size formatting. No horizontal overflow was observed at the
checked desktop viewport. This replaces Preview 90 as the latest-download
evidence; the earlier page observations remain historical. No installer was
executed by this browser check.

After Preview 95 publication and its metadata push, a fresh background browser
tab reached the deployed Download page. The resolved installer URL, notes URL
and rendered version label all identified **v0.1.0-preview.95**. The page displayed
**235.4 MB**, matching the binary-size formatting of its 246,840,323-byte asset.
The checked desktop viewport had no horizontal overflow. Preview 95 is now the
latest-download evidence; the observations above record earlier releases.

## Secondary-text readability defect and repair

After Preview 98 publication, the deployed HTTPS Download page resolved both
installer and release-note links to **v0.1.0-preview.98**. Its rendered label
and **235.4 MB** size matched the published 246,861,800-byte installer. This is
the current download evidence; previous observations remain historical. This
read-only browser check did not execute the installer.

The rendered light theme uses `--muted: #708177` for secondary text, including
11–17 pixel paragraphs and billing notes. Its contrast is **3.79:1** against
the `#f5f6f1` page background and **4.12:1** against white. Both combinations
fall below the **4.5:1** normal-text target in
[W3C's contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).

The authorized website polish now changes the light-theme secondary-text token
to `#56685e`. Computed contrast against the five main light surfaces is
4.84–5.94:1. Dark-theme colors, artwork and layout are retained. Translucent/gradient surfaces and accent-colored
small text require separate rendered checks; this token calculation does not
prove every text/background combination passes.

## Remaining acceptance

### Keyboard, motion and accessible price follow-up — 7 October

Actual production HTML, CSS and JavaScript were loaded behind an isolated static
server in hidden Chromium windows. External requests were blocked. Nine main
pages were checked at verified 1,280 px and 390 px CSS viewports, for 18 page
observations. Chromium focus emulation let keyboard input reach only those own
windows, without changing the user's foreground window.
The fixture uses the documented [DevTools Emulation API](https://chromedevtools.github.io/devtools-protocol/tot/Emulation/)
for focus, viewport and media preferences; these are simulated browser conditions.

- First Tab exposes the skip link, and Enter followed by Tab bypasses the header.
- Each page exposes one main landmark and no unnamed button in Chromium's
  accessibility tree.
- Changing the reduced-motion preference removes motion readiness, hides the
  reading indicator and leaves no running document animation in these checks.
- The mobile menu opens with Enter, lets Tab enter its links, and closes with
  Escape while updating its expanded state.
- On Subscriptions, keyboard selection changes Monthly to Annual and back.
  The annual price and period appear together inside the same atomic, polite
  live region in the actual accessibility tree. This proves the exposed
  announcement contract, not speech from a physical screen reader.

**New focus defect:** Escape closes the mobile navigation while a link has
focus, but focus falls back to the page body. A narrower repair would return
focus to the menu button for that keyboard dismissal. This was repaired in the follow-up below. Escape restores focus only when the
menu was open; pointer dismissal and Escape with a closed menu do not take focus.

The fixture first rejected evidence from an unfocused hidden window and a
390 px window whose real CSS viewport was wider. Explicit Chromium focus and
viewport emulation resolved those fixture issues before these observations
were accepted. No production website behavior changed in this audit. The
checks do not cover every Wiki article, every interactive state, physical
screen-reader speech, text zoom or all text/background contrast combinations.

### Latest release — 7 October

A fresh background browser tab reached the deployed HTTPS Download page. Its
installer link, release-notes link and rendered version all identify
**v0.1.10-preview.99**. The displayed **235.5 MB** matches the binary formatting
of the published 246,907,811-byte asset. No desktop horizontal overflow was
observed. The temporary tab was closed without downloading or executing the
installer. This is the latest download evidence; prior observations above are
historical.

- The evidenced secondary-text contrast, mobile Escape focus and table overflow
  repairs are verified below; broader states remain in scope for acceptance.
- Measure other text, controls and focus indicators on actual rendered surfaces.
- Complete keyboard traversal, focus restoration and skip-link checks across
  articles and longer pages, including zoom and text scaling.
- Check screen-reader announcements and dynamic navigation focus.
- Observe real reduced-motion changes; the current focused reading-progress test
  covers its mocked contract only.
- Inspect lower-page lazy artwork and README/banner composition at relevant sizes.
- Complete deployed-page interaction and accessibility coverage; the HTTPS,
  artwork, navigation and latest-download spot checks above are only a sample.

## Complete local page and artwork sweep — 7 October 2026

Source baseline: `dc858f1`. An isolated actual Chromium fixture examined all
17 current content pages at 1,280 px and 390 px CSS widths in both light and dark
themes: 68 content observations. It also followed all nine legacy HTML redirects
to their canonical destinations. No VM or gameplay command was issued.

- All 212 local image observations loaded successfully after real page scrolling,
  including below-fold lazy images. External avatar requests were blocked in eight
  observations; their availability is not claimed.
- All 64 character-image observations, comprising 14 distinct images, used
  `object-fit: contain` or retained their natural proportions within the measured
  tolerance. This checks computed boxes and fitting, not pixel-level cropping.
- Thirteen locally hosted tower PNGs are byte-identical to their originals in the
  app's existing tower-icon catalog. Existing artwork attribution remains in
  `docs/assets/game/README.md`; this does not establish an independent asset license.
- All content observations exposed one main landmark and one H1, with no missing
  local request or main-content fragment target.
- All 32 Wiki-article observations selected exactly their own sidebar entry.
  There are eight current articles; Wiki home is a separate content page. The
  repository's 26 HTML files include nine redirects, not 26 Wiki articles.

**New reproducible layout defect:** VM Connection's setup-state table expands to
620 px on the 390 px phone viewport in both themes. Its right edge is at 638 px,
so the entire page scrolls horizontally. The table lacks the existing
`.wiki-table-scroll` wrapper and inherits the site's mobile table minimum width.
The other 66 content observations remained within the viewport.

The implemented repair uses the existing scroll wrapper, labelled by its native
caption, with keyboard focus and a visible outline. The caption, column headings,
row headings and content remain intact. The original audit failed explicitly for
the two overflowing observations; the repaired repeat is recorded below.

W-04 remains open until the outstanding checks and defects are resolved.


## Website polish verification — 7 October 2026

This batch implements the existing website polish request with three bounded
repairs. It adds no page content, artwork, gameplay behavior or account data.

- The permanent isolated renderer regression passes **12 page/theme/viewport
  cases** across Home, Subscriptions and VM Connection, and **60 secondary-text
  contrast observations** against the five solid theme surfaces. The original
  light token failed all five surfaces; the replacement passes each one.
- Native Chromium Enter/Tab/Escape input opens the phone menu, enters its links,
  restores its toggle on Escape, then reaches visible main content with Tab.
  Reverse traversal returns to the toggle. Escape while closed and pointer
  dismissal preserve the current focus.
- VM Connection retains both column headers and all eight row headers. Its
  caption labels the scroll region, Right Arrow scrolls the table, and Tab exits
  the region. Both phone theme cases now keep the document inside the viewport.
- The broader **18** main-page keyboard/motion checks pass, including a stronger
  assertion that Escape restores the actual toggle, skip links, landmarks,
  reduced motion and atomic annual/monthly price exposure.
- The complete **68** content-page/theme/width observations and **9** legacy
  redirects pass with no missing local requests or layout failures. This is a
  repeat of the complete artwork audit above, not a claim about external avatars.
- All **74** approved JavaScript test files pass.
- Independent review found no actionable defect in the scoped product change
  or regression fixture. Its own temporary profile is removed after Electron
  exits; external network traffic is blocked.

The first new fixture omitted Chromium's Enter character event and incorrectly
assumed the theme toggle followed the menu button. Those fixture errors were
corrected to the existing proven input sequence and actual DOM order before
accepting the results. Product code was not changed to accommodate them.

These checks do not certify gradients, every accent-colored text state, physical
screen readers or all zoom combinations. W-04 remains open for those checks.


### Publication of this repair

Preview `v0.1.28-preview.99` is published with one 247,025,830-byte installer.
Package verification confirms all four version identities, 127 runtime source
comparisons, 1,735 inventory hashes, exact appended payload, both seven-frame
application icons and zero privacy findings. The unapproved ABR draft is excluded.
The deployed VM Connection HTML matches the repaired source; deployed CSS and
JavaScript match after normalizing Git's line endings. This HTTP content check
complements the local actual-renderer checks; it is not a physical browser audit.


## Wider zoom acceptance — 7 October 2026

A fresh isolated Chromium run at source `5f20c40` used a 1,280 × 960 window
and actual browser zoom factors of 100%, 200% and 400%. The measured CSS viewport
widths were 1,280, 640 and 320 pixels respectively; every observation asserted
that actual width and the selected theme before accepting its results.

All 17 content pages in both themes passed at all three zoom levels: **102
content observations**, plus **nine** canonical legacy redirects. There were
no document-wide horizontal overflows, missing local requests, missing main
fragments or heading/landmark mismatches. Every observed local image loaded
following real page scrolling. Character art retained its fitting/proportions,
and all 48 Wiki article observations selected exactly the current article.
The named table region can scroll internally; document-wide overflow is the
reflow condition checked here.

No production code change was needed for this repeat. This extends the earlier
1,280/390-pixel layout evidence; it does not establish physical display scaling,
screen-reader speech, standalone text-only scaling, useful alternative-text
wording, or every gradient/accent/interaction contrast combination. W-04 remains
open for those remaining acceptance checks.


## Link hover and keyboard focus — 7 October 2026

The remaining interaction audit found that hovered navigation/footer links and
focus outlines reused the light decorative coral `#ef987e`. Its contrast against
the five solid light surfaces ranged from **1.811:1 to 2.219:1**, below both the
normal-text 4.5:1 target and the tested focus-indicator 3:1 target. The actual
renderer reproduced **160 failing light-theme contrast observations**.

The bounded CSS repair retains the decorative accent, artwork and layout. Hover
text now uses `--link-ink: #934b38` (5.187–6.356:1 on those surfaces); focus uses
`--focus: #8b523b` (5.089–6.235:1). Dark mode retains its existing `#f5aa8b` for
both. The shared navigation/text-link/footer hover rules and all three existing
focus-outline rules use the new tokens; outline sizes and offsets are unchanged.

The permanent hidden-renderer regression now covers Home, Subscriptions,
VM Connection and Download in both themes at 1,280 and 390 pixels:

- **16** page cases and **80** secondary-text surface checks pass.
- **320** interaction contrast observations pass. Chromium forces actual hover
  and focus-visible states on existing navigation/footer links, theme controls,
  annual billing controls and Download FAQ summaries after transitions settle.
  Foreground/outline colors are measured against the five solid theme surfaces.
- The preceding menu traversal, focus preservation, table scrolling and viewport
  checks continue to pass. All **18** broader keyboard/motion/landmark checks pass.
- All **74** approved JavaScript test files pass. Independent review found no
  actionable defect and repeated the focused renderer check successfully.

An initial fixture additionally required computed outlines of at least two
pixels; Chromium reported 1.6 for declared two-pixel outlines on this display.
That unrelated size assertion was removed. The test now requires a visible,
nonzero outline and the stated contrast, and makes no physical focus-area or
DPI-compliance claim. Gradient/image backgrounds, other accent-text states and
physical assistive technology still require their separate acceptance evidence.


## Expanded heading spacing — 7 October 2026

A text-spacing stress check reproduced Contributors horizontal overflow at a
390-pixel CSS viewport in both themes. With line height 1.5, letter spacing
0.12em, word spacing 0.16em and paragraph-bottom spacing 2em, the heading's
minimum-content width pushed Benjamin's right edge to 394.61 pixels. The
shared Contributors/Subscriptions heading rule now allows long words to wrap
with `overflow-wrap: anywhere`; image dimensions and proportions are unchanged.

The permanent isolated renderer checks both pages at 1,280 and 390 pixels, both
themes, and normal/expanded spacing: **16 cases**. The corrected baseline failed
only the two expanded-spacing Contributors phone cases; all 16 pass after the
CSS change. Checks assert actual theme/viewport, applied spacing, document
horizontal reflow, heading horizontal bounds, loaded art and natural proportions.
Independent review repeated the focused check and found no actionable defect.
All **75** approved JavaScript test files pass.

An initial assertion incorrectly treated glyph ascent beyond the normal line
box as vertical clipping; it was removed before accepting the failing baseline.
The test makes no comprehensive vertical-clipping or accessibility-conformance
claim. The broader exploratory spacing audit did not complete and is not counted
as acceptance. Physical screen readers, standalone text scaling and gradient
contrast remain open gates. No guest update or gameplay input was needed.

## Rendered-background contrast investigation — 7 October

An isolated browser probe sampled Home, Features, Subscriptions and Download in
both themes at a 1,280-pixel viewport. It captured each page before and after
hiding text fill, then compared computed foreground colors with the rendered
background at changed text pixels. This includes gradient and artwork pixels
that the earlier flat-color audit excluded. No desktop or VM capture was used.

The probe produced 776 text observations and 42 low-contrast candidates. These
are investigation results, not 42 confirmed accessibility defects: brand marks,
decorative symbols and antialiased/shadow boundaries require separate review.
Candidates include the homepage map-preview caption and Routes chip, small
Coming Soon labels and light-theme journey numbers. Elements with ancestor
opacity and hidden content were excluded. No CSS fix or comprehensive contrast
conformance is claimed from this probe. Retain the character artwork and hero
concept while reviewing the text treatment.


### Packaged repair

The `v0.1.30-preview.99` artifact has 247,030,250 bytes. Verification confirms
four matching version identities, 127 runtime source comparisons, 1,737 inventory
hashes, the exact appended payload and seven exact frames in both application
icons. Publication scans report zero findings; the pending route draft is
excluded. This is artifact verification, not a clean-machine installation claim.

## Rendered-background contrast repair — 7 October 2026

The follow-up fixes the evidenced faint preview labels, feature symbols, step
numbers and coming-soon badges with existing theme tokens. The homepage map
caption now has a darker background beneath its white text; the Routes chip also
has a darker backing. Official artwork, proportions and the hero concept remain.

The permanent isolated Electron fixture covers Home, Features, Subscriptions,
Download, About, Contributors, Wiki and Getting Started in both themes at a
1,280-pixel viewport: **16 cases and 1,270 text observations pass**. It samples
actual rendered backgrounds, including map artwork, and applies 4.5:1 for small
text and 3:1 for large text. External requests are blocked; no desktop or VM
capture is used. All **79 approved JavaScript suites pass**.

Review exposed a false negative in the first checker: detecting glyphs from the
original foreground alone could skip invisible text. Independent black/white
glyph masks now locate text regardless of its original color. A deliberately
invisible label must fail at 1:1, and visible text without a measurable glyph
mask fails instead of silently disappearing. Captures use stable scrollbar
geometry. Each page must expose its main heading. Independent follow-up review
found no further actionable issue.

This is normal-state evidence for these eight pages, not complete accessibility
certification. Non-rendered content, off-page rectangles, partially transparent
ancestors, screen-reader-only text and logo marks are outside this measurement.
Physical assistive technology, standalone text scaling and other pages/states
remain separate acceptance work.

### Preview .36 publication

Published as `v0.1.36-preview.99`: one 247,046,810-byte installer. The uploaded
asset digest matches the checked local build. Verification covers 128 runtime
source comparisons, 1,746 inventory hashes, four version identities, the exact
appended payload and seven exact frames in each application icon. The packaged
website stylesheet matches this repair; publication scans report zero findings.
The unrelated pending route draft is excluded. This does not establish a clean
Windows installation or complete production 1.0 acceptance.

## Enlarged text at fixed viewport — 7 October 2026

The new isolated renderer captures every element's computed font size before
doubling it. Browser zoom stays at one, and the viewport remains 1,280 or 390 CSS
pixels. This covers all 17 content pages in both themes: **68 cases**. The
unmodified stylesheet failed 12 document-overflow and 14 heading-containment
observations. Home, Download and four Wiki pages overflowed the mobile document;
Account Progress also had a heading outside its column.

Long headings now allow word wrapping, the homepage grid text item can shrink,
and its metadata row can wrap. The corrected 68 cases pass. The change does not
set smaller fonts, hide overflow or change artwork dimensions. Independent
read-only review found no actionable regression.

External fonts are blocked, so these checks exercise fallback fonts. They prove
document and heading bounds under injected text sizing, not physical Windows
text scaling, every production font/browser combination, every clipping case
or complete screen-reader accessibility. Existing zoom, artwork, spacing and
contrast checks remain separate evidence.

All **80 approved JavaScript suites pass** after this repair, including the
earlier artwork/layout, expanded spacing and rendered-background checks.
