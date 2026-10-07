# Shared diagnostic export — 7 October 2026

The approved installer/startup privacy contract requires account and credential
fields to be removed from shared diagnostics. The app's shared filter is used by
setup/startup details and the report UI. Its original assignment expression
missed quoted JSON/Python keys, including passwords and account identifiers.

The regression first failed against the production filter. The repair recognizes
quoted keys, consumes escaped quotes and truncated values, and includes session,
refresh-token and setup-key fields already covered by the native contract.
Incomplete credential blocks are redacted through the end of the input.

Independent review identified two additional gaps, both reproduced before their
repairs: the generic assignment rule consumed only `Bearer` or `Basic` in plain
Authorization headers, exposing the token; escaped LF/CRLF line continuations
escaped the quoted-value matcher. Complete header credentials are now processed
as complete field values, and escape matching includes line terminators. A later
combined case caught standalone token filtering changing escaped quoted values;
quoted fields now run before that filtering, with combined regression cases.

`tests/test-support-report-redaction.js` exercises 83 synthetic structured/header
cases, five truncated/block cases, useful map/round context and repeat-redaction
stability. It also loads the browser export and executes the actual app report
handlers with a local DOM stand-in: visible preview, encoded GitHub draft body
and downloaded text all omit the synthetic sensitive values. No network request,
real secret, game input or save modification is involved.

This demonstrates the specified field and export boundaries. It does not claim
that a pattern filter can identify every personal detail in arbitrary prose or
unrecognized structured objects. User review and explicit sharing remain required;
no automatic upload was introduced. Complete failure-field and physical browser
accessibility acceptance remain separate work.
