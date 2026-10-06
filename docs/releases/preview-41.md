# Bloons+ Preview 41

## Faster hero lookup with live verification

Visually discovered hero-card positions are remembered as advisory hints in the existing local-only selection memory. Hints match the exact client resolution and slot layout. The replay reads the hinted card's live title; a mismatch resets scrolling and uses the full search.

Select/Selected confirmation remains mandatory. Only successful selection saves a hint. Malformed cache shapes become empty memory, and updates replace the app's cache atomically. Game and profile saves remain untouched; selection memory remains excluded from Git and installers.

Five offline checks pass, including wrong-hint fallback and changed-layout rejection. Live 1080p/1440p coverage remains unfinished; no universal hero-picker or route-success claim is made.

Includes signed Net MM/hr, explicit cursor targeting and automatic play input ownership. V1.0 coverage and clean-install readiness remain incomplete.
