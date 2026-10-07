# Native publication audit — 7 October 2026

## Finding and repair

The bundled, unsigned App Sandbox image helper contained a local build directory in three native strings. The previous publication guard inspected text files only, so it missed these strings in the executable and its compressed installer payload.

The repair retains the filenames `iso-patch.pdb`, `ext4.c` and `squashfs.c`, clears their directory prefixes and pads the original string storage with null bytes. The two C filenames are diagnostic `__FILE__` values used by the upstream logging macros. The PDB string is in the PE CodeView RSDS record. Executable instructions, imports, resources, entry point, section sizes and file length are unchanged. This is a publication repair, not a boot-failure repair.

| Evidence | Result |
| --- | --- |
| Original helper SHA-256 | `77631254159f5b7d297b6ceee099e7ef4436dbe46977a0fda0814d706f9d6933` |
| Repaired helper SHA-256 | `e13a9e982e86f5b67693daf77697087233824512c87c988e9ede3f6a6ba39a0c` |
| File length | 387,584 bytes before and after |
| Changed bytes | 272, confined to three diagnostic strings |
| PE certificate directory / checksum | Both zero before and after; no signature was invalidated |
| Original string storage, decimal offsets, exclusive end | `[345744, 345830)`, `[347280, 347370)`, `[351524, 351622)` |

The private original was retained outside publication inputs for byte comparison. No local directory or account name is reproduced here. PE layout was checked against the [Microsoft PE format specification](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format).

## Prevention and attribution

The source and payload publication checks now scan `.exe`, `.dll` and `.pyd` files for the existing credential, account and personal-path patterns. Checks cover narrow strings and both byte alignments of UTF-16 little-endian strings. Reports contain only the artifact name and finding category. Synthetic regressions reproduced the previously missed paths, then passed with binary scanning enabled. This remains a pattern guard, not a guarantee of detecting arbitrary private information.

The exact upstream App Sandbox MIT notice is retained beside the helper in `vm/licenses/AppSandbox-MIT.txt` and required by the packager. The third-party index identifies its source and modifications. Setup wording now describes boot diagnostics instead of claiming the unresolved App Sandbox boot failure is fixed.

Earlier public commits and release artifacts can still contain the old helper. This repair changes future source and installers; it does not rewrite repository history or remove previously downloaded copies.

## Checked artifact

Preview `v0.1.23-preview.99` has 422 passing Python tests and 71 passing approved JavaScript test files. Source and decompressed-payload publication guards report zero findings. The installer is 246,978,994 bytes with SHA-256 `3e068c9adad0850a90666180ba9021b0d9b7f74125ce36d01d18a83806d797d8`. Checks verified all 1,724 inventory hashes, 127 runtime source files, 1,245 unchanged data/route files, four package version identities, the exact appended payload and seven icon frames in each executable. The unapproved ABR draft is excluded. These checks do not establish clean Windows installation or resolve boot-file creation failures.
