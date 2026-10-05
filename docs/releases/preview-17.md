# Bloons+ Preview 17

## Preserve repaired routes

- The full public-route importer no longer deletes existing generator-tagged recordings before converting sources.
- Existing strategy bodies are deduplicated; changed conversions receive separate candidate names.
- Validation cleanup is restricted to newly created files in the current batch.
- Nine offline importer checks pass, including repeated imports preserving a repaired fixture byte-for-byte and rejecting an out-of-batch validation result.

## Current coverage

Refreshed reports list 893 recordings and eligible candidates for 508 of 1,204 map/mode pairs across 86 maps. 696 pairs remain uncovered; 48 legacy timing headers still need source-semantics review. Candidate coverage does not establish victory.

No real recordings or game saves were rewritten. This is a preview, not production 1.0. Runtime behavior is unchanged from Preview 16; this release improves the source import workflow and updates coverage reports.

## Install

Download **BloonsPlusSetup.exe**. Close Bloons+ before updating and update the VM between replays.
