# Development

## Building locally

Linux, with Python 3, git, cmake and ninja. The first run downloads the
ESP-IDF toolchain (several GB).

```sh
./build.sh                       # both variants -> dist/
./build.sh guition_jc3636w518c   # one variant
CP_VERSION=main ./build.sh       # build against another CircuitPython ref
```

`build.sh`:

1. clones CircuitPython into `build/circuitpython` (default tag
   `11.0.0-alpha.2`; `qspibus` needs 10.2.0 or newer, and `audioi2sin`, used
   by the I2S microphone, needs 11);
2. fetches the espressif port's submodules;
3. copies `boards/*` into `ports/espressif/boards/`;
4. runs ESP-IDF's `install.sh`, and installs CircuitPython's Python build
   dependencies into ESP-IDF's Python environment;
5. runs `make BOARD=…` and copies `firmware.bin` (and `.uf2`) to `dist/`.

ESP-IDF's installer downloads a constraints file from `dl.espressif.com`.
If that host is blocked, `build.sh` installs the Python environment without
it, and sets `IDF_PYTHON_CHECK_CONSTRAINTS=no`.

To build against a newer CircuitPython, see
[building-latest-circuitpython.md](building-latest-circuitpython.md).

## CI and releases

`.github/workflows/build.yml` builds both variants on every push and pull
request, and uploads each `.bin` as an artifact. Pushing a tag that starts
with `v` (e.g. `v0.1.0`) also creates a GitHub Release with the binaries
attached.

## Repository layout

```
boards/guition_jc3636w518c/
    board.c                  display bring-up, shared by both variants
    pins.c                   board.* pin names, shared by both variants
    jc3636w518_common.h      settings shared by both variants
    mpconfigboard.h/.mk      original-revision config (JC3636W518_PANEL_V2 = 0)
    sdkconfig
boards/guition_jc3636w518c_v2/
    board.c, pins.c          #include the shared files above
    mpconfigboard.h/.mk      V2 config (JC3636W518_PANEL_V2 = 1)
    sdkconfig
lib/                         CircuitPython libraries for the board
examples/                    example code.py files
tools/st77916_tables.py      collects/compares/converts the panel init tables
tools/panels_*.py.txt        header/footer used to generate lib/jc3636w518_panels.py
docs/                        guides, notes, vendor material, photos
build.sh                     local build script
```

## Board definition notes

* **Shared sources.** The two variants differ only in
  `JC3636W518_PANEL_V2`, which selects the panel init table in `board.c` and
  the microphone pin names in `pins.c`. The v2 directory includes the shared
  files with relative `#include`s, so both board directories must sit side
  by side in `ports/espressif/boards/`.
* **Display.** `board_init()` builds a `qspibus.QSPIBus` at 40 MHz (the
  vendor demo uses 50 MHz) and a `busdisplay.BusDisplay`. The ST77916 uses
  the standard QSPI framing that `qspibus` sends: opcode 0x02 for commands,
  0x32 for pixel data. The init sequence is the vendor table followed by
  COLMOD 0x55, MADCTL 0x00, INVON, SLPOUT (120 ms) and DISPON. MADCTL 0x00 is
  the orientation that the CST816's raw coordinates match.
* **Init tables.** The tables in `board.c` and `lib/jc3636w518_panels.py` are
  generated from the vendor code by `tools/st77916_tables.py`, in displayio's
  format (`cmd, len | 0x80 if delay, data…, delay_ms`). The V1 and V2 tables
  in both files are identical byte for byte. See
  [notes/st77916-init-tables.md](notes/st77916-init-tables.md).
* **Flash.** The firmware uses 16 MB in QIO mode at 80 MHz. The measured part
  is a Boya BY25Q128 (`0x684018`).
* **USB PID.** The firmware uses Espressif's shared test PID `0x303A:0x8000`.
  Before submitting the board to CircuitPython upstream, request a dedicated
  PID at https://github.com/espressif/usb-pids.
