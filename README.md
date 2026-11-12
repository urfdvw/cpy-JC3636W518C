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
* Wi-Fi, BLE, USB CIRCUITPY drive, and every unused GPIO as `board.IOxx`.

The I2S microphone on older boards has no CircuitPython driver, because
CircuitPython has no I2S input class yet.

## Which firmware?

Read the batch number on the board's label.

| Label batch | Firmware |
|-------------|----------|
| ≤ 2528 (made before July 2025) | `guition_jc3636w518c` |
| > 2528 (July 2025 and later)   | `guition_jc3636w518c_v2` |

The two builds differ only in the panel init table and the microphone pins.
If the screen stays dark, try the other build.

## Flashing

Hold **BOOT**, plug in USB-C, then release. Then run:

```sh
pip install esptool
esptool.py --chip esp32s3 --port /dev/ttyACM0 erase_flash
esptool.py --chip esp32s3 --port /dev/ttyACM0 write_flash -z 0x0 guition_jc3636w518c-10.3.2.bin
```

Press reset. A `CIRCUITPY` drive appears. Copy `lib/cst816.py` to
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
examples/                       display+touch demo, touch, SD, audio, mic
docs/hardware.md                hardware reference
```

## Notes

* The USB PID is Espressif's shared test PID `0x303A:0x8000`. Request a
  dedicated one at https://github.com/espressif/usb-pids before submitting
  this board upstream.
* Both variants compile cleanly against CircuitPython 10.3.2, but the
  firmware has not yet been tested on real hardware. Pins and init
  tables come from the vendor package, as used by the projects listed in
  `docs/hardware.md`.
