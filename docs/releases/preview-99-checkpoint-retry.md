## Additions

- Regression coverage for temporary and persistent Windows checkpoint locks.

## Changes

- Installer checkpoint updates retry briefly when Windows reports a sharing or lock conflict, including the observed replacement error 1175.
- Retries remain bounded and preserve the prior valid checkpoint.

## Removed

- Immediate setup failure on the supported transient replacement errors when a subsequent bounded attempt succeeds.
