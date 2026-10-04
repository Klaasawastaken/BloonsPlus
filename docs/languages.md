# Language map

Bloons+ has two core application languages: **JavaScript and Python**. Windows installation adds C# and embedded PowerShell. AutoHotkey currently supplies replay keystrokes. Other languages mainly come from vendored reference projects.

## Active code

| Language | Concrete responsibility | Can it go? |
| --- | --- | --- |
| JavaScript | Electron entry point, assets/app/app.js, server.js, account readers, route management and VM/status bridge. | Keep. It already owns most product behavior. |
| Python | autobtd6/replay.py, image processing, OCR, replay decisions, input adapter, route utilities, vm/setup-vm.py and installer/make-installer.py. | Keep. Rewriting the replay into JS would be a large migration. |
| HTML and CSS | App markup, styling, calibration UI and this documentation site. | Keep. They do not add an independently installed runtime. |
| C# | installer/installer-bootstrap.cs: native bootstrapper, installer interface, dependency setup and shortcuts. | Replace only when another bootstrap can reliably start on a clean Windows machine. |
| PowerShell | Commands embedded in JS, Python, installer code and the VM launcher for Windows feature checks, elevation, process operations and guest setup. | Consolidate first. Removing scripts without replacements would break provisioning. |
| AutoHotkey | helper.py creates an AHK client and sendKey uses ahk.send with explicit key delay and press duration. | A small Python keyboard adapter can eventually replace this live dependency. Verify key codes, modifiers, focus and timing. |
| Batch/CMD | vm/setup-vm.cmd is a developer VM setup entry point. | Can move behind app setup once parity exists. |

## Reference code and data

- **Rust:** btd6autoplay/src belongs to the vendored reference engine. It is not the current replay engine or a required app runtime.
- **Additional AutoHotkey/Python scripts:** imported route/reference material. Inventory licenses and consumers before pruning it.
- **JSON:** catalogs, app configuration, account observations and strategy metadata.
- **YAML/TOML:** reference-engine configuration and package metadata.
- **.btd6:** recorded action scripts interpreted by the Python engine. They are strategy data with commands, not a separately installed language runtime.
- **Markdown/SVG:** documentation and illustrations. SVG assets do not require an image-generation dependency.
- **Native libraries:** Electron, TensorFlow and OpenCV contain native code internally. Their upstream C/C++ implementation is not another language maintained by this project. vm/iso-patch.exe is a checked-in binary, not editable source.

## Recommended consolidation order

1. **Keep JS + Python as the core.** Define who owns app state, replay execution and provisioning.
2. **Separate optional reference engines.** Exclude unused material from builds; preserve attribution and source history.
3. **Centralize Windows operations.** Route existing PowerShell calls through one documented adapter with consistent errors.
4. **Replace the live AutoHotkey sender.** Use the Python input layer, preserving timing, modifier handling and foreground behavior.
5. **Give provisioning one owner.** Keep Python or JS as the coordinator; avoid duplicating setup decisions across installer and app.
6. **Reconsider C# last.** An Electron installer interface still needs a bootstrap that works before dependencies are installed. Merely moving UI does not remove that requirement.

This documentation does not migrate any implementation. Each migration should preserve the current working behavior before removing the old path.

## Performance versus language count

Fewer languages simplify maintenance and packaging. They do not automatically improve replay speed. Capture frequency, repeated OCR, TensorFlow initialization, process startup, network polling and bundled dependencies are more direct optimization targets.

[Back to README](../README.md) · [Website](index.html) · [Setup guide](guide.html)
