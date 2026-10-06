# Failure evidence and shared diagnostics audit

## Scope

This read-only audit compared the production failure writer, HTTP response mapping
and shared-log redactors with the production brief. It inspected only aggregate
field availability from the VM's last 150 failure responses. Account values, raw
logs, screenshot contents and profile identifiers are not reproduced here.

The VM reported 666 retained failures and returned its latest 150. These are
historical records, not 666 failures in the current sweep. The active sweep had
three victories and zero defeats during this observation.

## Writer and API boundaries

| Required context | Current evidence | Remaining work |
| --- | --- | --- |
| Timestamp, map, mode, route and category | Present in all 150 responses | Check semantic accuracy of older classifications |
| Route hash, engine version and start time | Writer stores these fields; the response mapping omits them | Preserve recorded values at the diagnostics API boundary; do not invent legacy values |
| Round freshness | Writer distinguishes fresh, stale and legacy reads; API drops the status and observed time | Retain freshness metadata in detailed diagnostics |
| Cash and last round | Nonempty in 95 and 97 responses respectively | Missing readings must remain unknown rather than guessed |
| Screenshot reference | Nonempty in 96 responses | A reference does not prove the rotated image still exists |
| Actions and observations | Nonempty in 90 and 105 responses respectively | The action projection retains only a subset of event fields; audit expected/actual state and recovery context |
| Notable and fuller output | Nonempty in 145 and 149 responses respectively | Fuller output is a bounded 4,000-line tail, not an unlimited full-run transcript |
| Hero, app/game versions and medal-afterward state | No dedicated fields in the current failure response | Structured context remains incomplete; logs alone do not satisfy every requirement |

No failure history, route, retry budget, save or gameplay state was changed by
this audit. Missing context remains an open production gate.

## Export redaction

Synthetic probes reproduced a gap in the app's shared-log redactor: quoted JSON
and Python field names bypass its assignment pattern. The issue preview and
downloaded log both use this function. Its bounded repair awaits the requested
design approval; it is not included in the native installer repair.

The approved installer plan separately requires redacted Copy/Export details.
Its native redactor had the same quoted-field gap. A real compiled native harness
failed before the repair. It now removes structured credential/account/session
values, consumes escaped quotes and removes incomplete quoted values through the
end of the diagnostic. Ten complete-field cases retain safe map/round context and
are idempotent; three truncated cases leave no synthetic credential prefix or
suffix. Existing raw-path, key-block, address and size-limit checks remain in the
native view suite.

These cases establish the tested formats, not exhaustive detection of arbitrary
personal information or complete save-content redaction. Local forensic records
remain private; exporting details still requires an explicit user action.
