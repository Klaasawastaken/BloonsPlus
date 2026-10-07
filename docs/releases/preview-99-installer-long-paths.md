## Additions

- Offline native installer checks for deep dependency paths, package repair and process ownership.

## Changes

- Install Python packages through extended Windows paths so deep wheel contents can be written when the app's own folder and launcher fit normal Windows path limits.
- Preserve exact process ownership across normal and extended executable spellings, including PID and creation-time checks.
- Keep Python environment creation, normal runtime launches and healthy-environment reuse unchanged.

## Removed

- Nothing. Windows registry settings, application data, saved medals and route failure history are preserved.
