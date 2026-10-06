# Bloons+ Preview 79

## Replay controls

- Add `play once` as a distinct command from requesting fast or slow speed.
- Save intent before input and require an observed transition before the next command.
- Restore pending intent with the current key binding; do not blindly repeat a key after restart.
- Preserve input ownership and stop automatic startup from competing with a planned single Play.
- Preserve the source runner's initial-on Auto Start setting and subsequent toggle sequence.

## Hero title reading

- Read yellow/orange and violet lettering with separate masks alongside the existing cyan reader.
- Keep live title and Select/Selected verification required. No inferred hero choice or new unreadable-text aliases.
- An existing Admiral Brickell capture reproduced erased lettering before the fix; its corrected OCR candidate passes the actual hero matcher. Gwendolin/Psi live confirmation remains pending.

## Checks and remaining work

105 focused Python checks passed. JavaScript checks cover title color masks and route admission. The single-Play runtime and resume checks use simulated input only; no validation-only game runs were launched.

Full source logical-round and `end_round` conversion remains in development. Incomplete manual routes remain excluded, and original recordings including CHIMPS are unchanged. This release continues the missing-medal sweep workflow; it is not the finished V1.0 release.
