# Bloons+ Preview 33

## Separate supported timing from inferred source commands

A pinned-source audit found that BloonsPlayer implements `delay`, but does not register `wait` as a command. Bloons+ had interpreted both as seconds waits and described a Glacial Trail Easy conversion as complete.

Supported `delay` commands still preserve their seconds. Scripts containing an inferred nonzero `wait` remain review drafts. The Glacial Trail candidate keeps its recorded placement and upgrade body, with an explicit review label; the prior installed filename is also treated as a draft because updates preserve user recordings. Original CHIMPS recordings are unchanged.

The audit now covers 83 source scripts, identifying 15 with round/speed/autostart controls or unregistered waits. Eleven importer tests, four audit checks, eight repeated-ability checks and the ability-binding gate pass offline. No route was launched for validation. Manual control execution and the inferred Glacial Trail strategy still require work; V1.0 remains in development.
