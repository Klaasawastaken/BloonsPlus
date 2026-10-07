## Additions

- Publication checks for embedded credentials and personal paths in native executables and libraries, including UTF-16 strings.
- The upstream App Sandbox MIT notice beside the bundled VM image helper, with a packaging requirement to keep it present.

## Changes

- Native publication reports identify the affected file without echoing private content.
- VM setup describes the image helper's diagnostic role accurately. The clean-VM boot-file failure remains under investigation.

## Removed

- Local build-directory paths from the bundled image helper's diagnostic and debugger strings. Executable code remains unchanged.
