# Bring-up log

What was found while bringing CircuitPython up on this board, in order.
Kept for reference when the next board or firmware version shows something
unexpected.

## Pin map

* The first pin map came from public projects (ESPHome configs, xiaozhi-esp32,
  orbis-panel). Each pin appeared in at least two of them.
* It was then checked against the vendor schematic (`vendor/schematics/`)
  and the vendor demo's `pincfg.h`. Every pin matched.
* The schematic also showed several details that were not known before:
  - the CN2 header with GPIO38/39, and the CN4 line-out header;
  - the TE line is not connected, and UART0 is not broken out;
  - there is no reset button (RC power-on reset only);
  - XSMT is active high and the backlight MOSFET is active high.

## Flash size

* The schematic labels the flash BY25Q64 (8 MB), but the manual and every
  project say 16 MB.
* Measured with esptool-js (`Flash ID: 184068`): manufacturer `0x68` (Boya),
  capacity code `0x18` = 16 MB, so a BY25Q128. The 16 MB configuration is
  correct.
* ESP-IDF's QIO support list has no Boya entry, but its generic default entry
  (QE bit 1 via RDSR2/WRSR2) covers BY25Q parts.

## First flash: no drive, no serial port

* Symptom: after flashing with esptool-js, neither `CIRCUITPY` nor a serial
  port appeared.
* Cause: esptool-js defaults **Flash Address to `0x1000`** (right for the
  original ESP32, wrong for the ESP32-S3, which boots from `0x0`).
* Fix: erase and flash again at `0x0`. The screen then showed the
  CircuitPython console, and the drive appeared.
* Download mode was reachable throughout: the ROM's USB-Serial/JTAG shows up
  as `303a:1001` while BOOT is held during plug-in.

## Identifying the revision

* The board has no batch label on the case. The batch number is printed on the
  PCB next to the TF card slot: `2628` (year 26, week 28), next to `V1.3`.
* The panel back reads `20260714`, `H0185Y040X V0`, `BL-H0185Y014`, and
  `DJL18505C 26/06/10`.
* The batch is > 2528, so this is the new revision. The `_v2` build (V2
  panel table) works on it.
* Photos: `photos/batch2628-*.jpg`.

## Diagnostic builds used

During the no-USB investigation, two throw-away variants were built (not
kept in the repo). Recreate them if needed:

* **8 MB flash:** copy the `_v2` board directory and set
  `CIRCUITPY_ESP_FLASH_SIZE = 8MB`.
* **No display init:** copy the `_v2` board directory, and replace `board.c`
  with just `#include "supervisor/board.h"`. Use it to tell a display hang
  apart from other boot problems.

## Upgrade to CircuitPython 11.0.0-alpha.2

* The board code needed no changes: the `qspibus`, `busdisplay` and display
  allocation APIs are identical to 10.3.2.
* 11.x adds `audioi2sin`, which makes the I2S microphone on batch ≤ 2528
  boards usable. `examples/mic_level.py` handles both microphones.
* 11.x moves to ESP-IDF 6.1. Re-using the 10.3.2 checkout left ESP-IDF's
  nested submodules (mbedtls, lwip, Wi-Fi libs) at old commits, and CMake
  failed. `build.sh` now syncs them, and starts fresh build directories after
  a version change.

## Not yet tested on hardware

The 11.0.0-alpha.2 builds, touch, TF card, audio out, both microphones, Wi-Fi, BLE (including
`examples/ble_keyboard_host.py`), backlight dimming, the `identify_board.py`
heuristic, the original-revision build, and the other panel tables.
