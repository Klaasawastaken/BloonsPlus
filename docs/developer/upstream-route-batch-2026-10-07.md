# Additional published routes — 7 October 2026

## Scope

Eighteen separate conversions cover Easy, Primary Only, Deflation, Medium, Military Only and Reverse on **Middle of the Road**, **One Two Tree** and **Town Center**. They use the existing Everything Macro converter and preserve their source modes. No original recording, CHIMPS route, retry history or saved medal is replaced.

The source is [BTD6 Everything Macro at commit 715790be2fbfac0f799ef75f324a5748f5a6473f](https://github.com/ThuyTran735/BTD6-Everything-Macro/tree/715790be2fbfac0f799ef75f324a5748f5a6473f/Maps/Beginner). The [provenance manifest](../../route-library/metadata/upstream-routes-2026-10-07.json) records exact source and converted-file hashes. Its [MIT notice](licenses/everythingmacro-LICENSE.txt) is retained. Source files were inspected as text, never executed as macros.

## Offline checks

- All 297 source actions are represented by 855 parsed replay instructions. Source row counts match completely; the selected scripts contain no nonzero delays, moved selection overrides or unsupported callbacks.
- Placement positions, round markers, top-to-bottom upgrade purchase order and explicit targeting changes match the pinned handlers. Source placement does not perform extra targeting clicks from the setup object's bookkeeping fields.
- The full Python replay parser accepts all 18 files, with one parsed action per non-comment instruction. The JavaScript legality checks accept all 18 target modes and tower crosspaths.
- Opening purchases fit the base budget using the bundled prices with Monkey Knowledge disabled: at most 630 for a normal opening and 19,790 for Deflation. This does not certify later-round affordability or current-version prices in every game setting.
- Existing normalized strategies were compared before emission; none of these target-mode sequences duplicates an existing recording.
- Current catalog coverage rises from 535 to **545 of 1,204 map/mode pairs**, leaving **659 gaps**. Coverage means eligibility, not victory.

The sweep must still read the current account, skip owned medals, honor prerequisites and retain failed attempts. New local clear credit requires both victory and an authoritative saved medal. These conversions are not declared locally successful in their metadata.

## Excluded sources and follow-up

- Tree Stump remains excluded from unattended play because its specific cash-reader failure has not been resolved with evidence.
- The new Sanctuary expert script contains moved upgrade and targeting positions. The current Everything Macro converter silently drops those arguments; it was not emitted. The bounded coordinate-preservation repair has been proposed for approval.
- Dark Dungeons and Glacial Trail expert scripts use an unrecognized `SpikeFactory` source alias and require further action-fidelity review.
- The changed Tricky Tracks conversion duplicates an existing sequence and is not another retry candidate.
- The new BTD6bot Ascent plan references a map absent from the current map catalog. Map identification and mechanics need separate work before admission.

None of these exclusions was bypassed to extend the sweep.

## Publication and deployment

Preview `v0.1.24-preview.99` contains this batch. The single installer is 247,002,213 bytes, with SHA-256 `fa361b0d06695d9456bb0c8287a308f3b1d54a2ce4da55eef9dc5118d9746510`. Checks verified 127 runtime source files, all eighteen new route hashes, 1,727 inventory hashes, four package identities, the exact appended ZIP payload and seven matching application icon frames in both executables. Source and decompressed-payload privacy scans reported zero findings. The unapproved ABR draft is excluded. GitHub returned the expected uploaded asset size and digest.

The eighteen route files, source manifest and license were installed through the existing VM connection at an idle boundary. All twenty destination hashes matched; the controller did not restart. Its base version remains `v0.1.22-preview.99`. A missing-medal run then reached round 12 on Middle of the Road Military Only with confirmed upgrades. This establishes that the new candidate is usable by the installed controller; it does not establish victory. Full clean-machine installation acceptance remains open.
