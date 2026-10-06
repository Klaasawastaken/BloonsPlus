# Bloons+ Preview 55

## Live placement confirmation

- Stop treating a confirmation-mode flag from an earlier replay as the current game setting.
- Start each replay without that assumption and recognize confirmation from the live post-click green check.
- Preserve the existing placement-check click and purchase observation flow.
- Keep historical files intact and stop writing new confirmation flags.
- Include Preview 54’s Settings, dropdown, capture and placement diagnostics.

## Verification limits

Three offline checks execute the actual initialization/confirmation blocks with mocked input and filesystem operations. Eight nearby placement/HUD checks also pass. These checks prove stale flags no longer enable confirmation mode; they do not prove Infernal Heli placement or every historical defeat fixed. No validation-only game was launched. V1.0 remains incomplete.
