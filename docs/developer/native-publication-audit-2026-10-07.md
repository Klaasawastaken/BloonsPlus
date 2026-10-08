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

The historical cleanup below removes the original helper from reachable public
branch/tag history and retires affected old downloads. Previously downloaded
copies, forks and hosting caches cannot be erased by that operation.

## Historical inventory and proposed cleanup

A read-only scan of 2,848 reachable text/native blobs (103,127,609 bytes) found
the known original helper and one historical diagnostics test. The test contains
an intentionally synthetic path and `secret-content` fixture, not a real key.
No other pattern findings were returned. Pattern scanning is not proof that
arbitrary personal text is absent.

The remote inventory contains 138 branch/tag tips after annotated-tag peeling
entries are excluded. The old helper is present at 122 tag tips. Of 136 public
releases, 121 correspond to those tags and hold 124 assets, including three
older checksum files. Fifteen newer releases use clean source snapshots.
Local retained installer archives independently confirm that Preview .22
contains the original helper and .23/.37 contain the repaired helper. Older
remote installers have not all been downloaded; the conservative retirement
scope is based on the affected release tags, not a claim of inspecting each
asset's compressed contents.

The proposed operation is to replace only the original helper blob throughout
public history, preserve every other source byte, retain release notes, and
retire the assets attached to those 121 affected releases. Newer clean release
downloads remain. Before publication, verify replacement history, tag coverage
and the exact remote-ref snapshot; retain a private recoverable backup. Force
updates change commit IDs and require collaborators to resynchronize clones.
Downloaded copies, forks and hosting caches cannot be erased by this operation.

**Completed on 8 October:** a privately retained Git bundle was verified before
the helper-only rewrite. Comparison covered 493 commits and 2,687 trees, preserving
all other source bytes, commit messages and tag annotations. Two commit signatures
were removed because their tree/parent changes invalidated them; original signed
objects remain in the private backup. An independent publisher review found no
critical or important issues.

Publication used an atomic push with exact per-ref leases. Fresh readback verified
all 139 branch/tag refs. Retirement addressed only the 124 approved asset IDs on
121 affected releases, after checking each name, size and digest. Final readback
verified all 137 release notes and preserved downloads on 16 newer releases,
including Preview .38. The local main pointer was synchronized only after proving
its latest tree identical; pending work was preserved. Exact IDs, inventories and
receipts stay private. Collaborators must resynchronize old clones before pushing.

## Checked artifact

Preview `v0.1.23-preview.99` has 422 passing Python tests and 71 passing approved JavaScript test files. Source and decompressed-payload publication guards report zero findings. The installer is 246,978,994 bytes with SHA-256 `3e068c9adad0850a90666180ba9021b0d9b7f74125ce36d01d18a83806d797d8`. Checks verified all 1,724 inventory hashes, 127 runtime source files, 1,245 unchanged data/route files, four package version identities, the exact appended payload and seven icon frames in each executable. The unapproved ABR draft is excluded. These checks do not establish clean Windows installation or resolve boot-file creation failures.

## Additional current-source coverage — 7 October

A read-only supplemental scan applies the existing privacy patterns to tracked
UTF-8 text outside the guard's current suffix list. It covers 1,122 files:
1,051 route recordings, 42 AutoHotkey files, ten SVGs, seven extensionless files,
six CommonJS fixtures, five stylesheets and one XML file. It returns one match
in the issue-report fixture, manually confirmed to be the deliberate synthetic
account path used to verify redaction. No new real personal-data match was found.
This is a point-in-time pattern audit; it does not expand the permanent guard,
cover arbitrary encodings/content, or resolve the historical helper finding.

The current .37 installer also reports `NotSigned` through Windows Authenticode.
Both Windows personal certificate stores have zero currently valid code-signing
certificates with a private key. No signing identity or certificate was changed.
