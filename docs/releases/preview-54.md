# Bloons+ Preview 54

## Window capture diagnostics

- Preserve the actual window-transition or too-small-client error instead of overwriting it with “window is minimized.”
- Include measured dimensions so logs distinguish a loading/dialog-sized window from a ready game client.
- Keep the existing bounded capture recovery and valid-window input behavior.
- Include Preview 53’s exact surplus upgrade intent, resume-ledger validation and route alternatives.

## Settings and dropdowns

- Simplify Help with direct run-log and existing redacted issue-report actions. Keep installation/reset details collapsed.
- Hide guest-only empty VM actions and disable setup/update until connection status arrives.
- Respect hidden option groups in custom dropdowns and close menus when the app is backgrounded.
- Preserve readable Settings error colours in light and dark themes.

## Verification limits

Four offline checks execute the actual client-rectangle function: non-game geometry, tiny valid-ratio geometry, zero-area clients and normal 1080p clients. This correction improves diagnostics; it does not prove every capture/VM startup issue solved. No game was launched for validation; V1.0 remains incomplete.
