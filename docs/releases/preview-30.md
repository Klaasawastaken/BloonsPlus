# Bloons+ Preview 30

## Keep imported ability controls

Repeated ability commands now run in the same input-owning loop as the route. They preserve explicit slot cancellation and stop-all commands, use detected game hotkeys, and survive a checkpoint resume. Scheduling waits while another route action owns input or the playing state is uncertain; it does not catch up with a burst of missed keypresses.

BloonsPlayer numeric key `0` is mapped to the tenth ability. Its seconds waits are preserved instead of omitted. Unknown keys remain rejected. The conversion follows the upstream implementation's persistent repeats and single-slot cancellation.

Three new source candidates retain these commands: Dark Dungeons Easy, Glacial Trail Easy, and Muddy Puddles Hard. They passed both route parsers offline; this is not a claim of local victory. Original recordings, including CHIMPS, are unchanged.

Includes the Settings and progress-refresh improvements from recent previews. Scrapyard CHIMPS was earned by the existing sweep and confirmed in the game save; updates waited until that replay finished.

Scheduler, input ownership, parser/recorder, resume, import and existing timing checks pass. In-game repeat observation will happen only while earning missing medals. V1.0 remains in development.
