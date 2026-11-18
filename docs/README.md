# Documentation

Downloading and flashing are covered in the [top-level README](../README.md).

## Guides

| Page | Contents |
|------|----------|
| [usage.md](usage.md) | Feature status, libraries, examples, and how to use the display, touch, TF card, audio, microphone and BLE |
| [hardware.md](hardware.md) | Hardware reference: parts, pin map, revisions, schematic notes, sources |
| [development.md](development.md) | Building the firmware, CI and releases, repository layout, board definition notes |
| [building-latest-circuitpython.md](building-latest-circuitpython.md) | Moving to a newer CircuitPython release or `main`: API checks, build, known problems, verification |

## Notes

| Page | Contents |
|------|----------|
| [notes/st77916-init-tables.md](notes/st77916-init-tables.md) | The panel init tables found, how they differ, and which one the vendor demo really uses |
| [notes/bring-up-log.md](notes/bring-up-log.md) | What was found while bringing the board up: flash ID, the `0x1000` flashing pitfall, revision identification |

## Reference material

| Folder | Contents |
|--------|----------|
| [vendor/](vendor/README.md) | Guition's download package: manual, schematics, datasheets, mechanical drawing, display init code, Arduino demo |
| [`examples/keyboard host/`](../examples/keyboard%20host/) | Working BLE keyboard host example (complete `CIRCUITPY` contents) and its debugging notes, `MEMORY.md` |
| [photos/](photos/) | Photos of a batch-2628 board: PCB top side and the panel's back label |
