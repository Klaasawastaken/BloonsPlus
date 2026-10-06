# Bloons+ Preview 72

## Dropdown selection repair

- Refresh open menus when native option values change, even if their display labels stay the same.
- Rebuild row handlers when an option list is replaced with identical-looking nodes. Removed native options have an invalid index and must not be used to select a run.
- Ignore stale row clicks and refresh the current options instead of clearing the underlying selection.
- Preserve search, selected-row display, keyboard handling and native input/change events.

## Evidence

The focused refresh regression fails against Preview 71's dropdown code and passes after the repair. JavaScript syntax, Settings action checks and publication checks pass. This release does not claim new route clears.
