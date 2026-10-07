## Additions

- Installer checks available space for changed app files and recovery copies before staging them.
- Regression checks for insufficient space, exact capacity, unchanged-file reuse, and recovery after deployment exits.

## Changes

- Setup explains how much free space the app-file deployment needs before replacing installed files.
- Unchanged app files do not count as duplicate staging or recovery copies.

## Removed

- Starting a new app-file transaction when the observed free space cannot hold its planned staging and recovery data.
