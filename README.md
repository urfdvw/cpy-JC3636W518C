# CircuitPython for the Guition JC3636W518C

Unofficial CircuitPython board definition for the Guition **JC3636W518C**
("Taiji Pi S3"). The board has an ESP32-S3R8, 16 MB flash and 8 MB PSRAM, a
round 360×360 ST77916 QSPI display, CST816S touch, a microSD slot, a
PCM5100A headphone DAC and a microphone.

Full pinout, revision differences and sources: [docs/hardware.md](docs/hardware.md).

## What works

* `board.DISPLAY`: the ST77916 starts at boot through `qspibus`, and the REPL
  appears on screen. `display.brightness` dims the PWM backlight.
* Touch through `lib/cst816.py` (coordinates, gestures).
* TF card through `sdioio` (4-bit).
* Headphone output through `audiobusio.I2SOut`.
* PDM microphone through `audiobusio.PDMIn` (V2 boards only).
* The two free GPIOs, 38 and 39, on the small CN2 header (`board.IO38`, `board.IO39`).
* Wi-Fi, BLE (`_bleio`; `examples/ble_keyboard_host.py` connects a BLE
  keyboard), USB CIRCUITPY drive, and every unused GPIO as `board.IOxx`.

The I2S microphone on older boards has no CircuitPython driver, because
CircuitPython has no I2S input class yet.

## Which firmware?

Read the batch number on the board's label.

| Label batch | Firmware |
|-------------|----------|
| ≤ 2528 (made before July 2025) | `guition_jc3636w518c` |
| > 2528 (July 2025 and later)   | `guition_jc3636w518c_v2` |

No label? Flash either build, copy `examples/identify_board.py` to
`code.py` and follow the prompts on the serial console. It tests whether the
microphone is the newer PDM type.

The two builds differ only in the panel init table and the microphone pins.
If the screen stays dark or the colors look wrong, run `examples/panel_test.py`.
It switches between all four known vendor init tables at runtime when you
tap the screen or press BOOT, without reflashing.

## Flashing

Hold **BOOT**, plug in USB-C, then release. Then run:

```sh
pip install esptool
esptool.py --chip esp32s3 --port /dev/ttyACM0 erase_flash
esptool.py --chip esp32s3 --port /dev/ttyACM0 write_flash -z 0x0 guition_jc3636w518c-10.3.2.bin
```

Browser alternative: https://espressif.github.io/esptool-js/ (Chrome/Edge).
**Change Flash Address from its default `0x1000` to `0x0`.** With `0x1000`
the ESP32-S3 finds no bootloader, and neither a drive nor a serial port
appears.

There is no reset button: unplug and replug USB (without holding BOOT).
A `CIRCUITPY` drive appears. Copy `lib/cst816.py` to
`CIRCUITPY/lib/` and an example from `examples/` to `CIRCUITPY/code.py`.
The demo uses `adafruit_display_text` when it is installed:
`circup install adafruit_display_text`.

## Building

GitHub Actions (`.github/workflows/build.yml`) builds both variants on every
push and uploads the `.bin` files as artifacts. Pushing a `v*` tag also
publishes them as a release.

Local build (Linux; downloads the ESP-IDF toolchain on first run):

```sh
./build.sh                       # both variants -> dist/
./build.sh guition_jc3636w518c   # one variant
CP_VERSION=main ./build.sh       # build against another CircuitPython ref
```

The script clones CircuitPython (default tag `10.3.2`, a stable release
that includes `qspibus`), copies `boards/*` into `ports/espressif/boards/`,
and runs `make`.

## Layout

```
boards/guition_jc3636w518c/     board.c (shared), pins.c (shared), common header, V1 config
boards/guition_jc3636w518c_v2/  V2 config; includes the shared sources
lib/cst816.py                   touch driver
lib/jc3636w518_panels.py        all known ST77916 init tables + runtime display re-init
examples/                       display+touch demo, panel test, revision check, touch, SD, audio, mic, BLE keyboard host
docs/hardware.md                hardware reference
```

## Notes

* The USB PID is Espressif's shared test PID `0x303A:0x8000`. Request a
  dedicated one at https://github.com/espressif/usb-pids before submitting
  this board upstream.
* Tested so far: `guition_jc3636w518c_v2` boots and shows the REPL on a
  batch-2628 board (panel `H0185Y040X V0`, flash Boya BY25Q128). The
  original-revision build has not been tested on hardware yet. The pins have been
  checked against the vendor schematic. The panel init tables come from
  vendor-derived code (xiaozhi-esp32).
