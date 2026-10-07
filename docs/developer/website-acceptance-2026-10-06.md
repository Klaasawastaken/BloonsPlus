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
