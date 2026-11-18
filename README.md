# CircuitPython for the Guition JC3636W518C

Unofficial CircuitPython firmware for the Guition **JC3636W518C** ("Taiji Pi
S3"), a 1.8" round 360×360 touch display built around an ESP32-S3R8 (16 MB
flash, 8 MB PSRAM). The board also has a microSD slot, a PCM5100A headphone
DAC and a microphone.

With this firmware the display starts at boot as `board.DISPLAY`, every
on-board part has a `board` pin name, and the board appears as a `CIRCUITPY`
USB drive. Tested on hardware so far: the display, the USB drive and REPL,
and BLE: [`examples/keyboard host/`](examples/keyboard%20host/) is a working Bluetooth LE keyboard host.
Documentation is in [`docs/`](docs/README.md).

## Download

Firmware files are named `<board>-<CircuitPython version>.bin`. The current
build is based on CircuitPython `main` after **11.0.0-alpha.3**, plus the BLE
fix from [adafruit/circuitpython#11859](https://github.com/adafruit/circuitpython/pull/11859).
This is development code.

* **Releases:** the repository's Releases page, for tagged versions.
* **Latest build:** open the Actions tab, pick the most recent green
  "Build firmware" run, and download the board's zip from **Artifacts**.

### Which file?

Check the batch number printed on the PCB, next to the TF card slot
(e.g. `2628`), or on the label.

| Batch | Firmware |
|-------|----------|
| 2528 or lower (before July 2025) | `guition_jc3636w518c` |
| above 2528 (July 2025 and later) | `guition_jc3636w518c_v2` |

If you cannot find a batch number, see
[Identifying the revision](docs/usage.md#identifying-the-revision).

## Flashing

Flashing erases the factory firmware. To keep a copy, back it up first with
the command-line method below (`read_flash`).

### In the browser: esptool-js

Needs Chrome or Edge (WebSerial).

1. Open https://espressif.github.io/esptool-js/
2. Connect the board over USB-C and click **Connect**. Pick the port
   (`USB JTAG/serial debug unit`, ID `303a:1001`). If no port appears,
   unplug the board, hold **BOOT** while plugging it back in, then release.
   BOOT is the small side-push button on the PCB edge next to the 3.5 mm
   jack.
3. Click **Erase Flash** and wait for it to finish.
4. Under *Program*, set **Flash Address to `0x0`**. The page defaults to
   `0x1000`, which is wrong for the ESP32-S3: with it, the board boots to
   nothing, and neither a drive nor a serial port appears.
5. Choose the `.bin` file and click **Program**.
6. When it finishes, unplug and replug USB without holding BOOT. The board
   has no reset button.

The screen shows the CircuitPython console, and a `CIRCUITPY` drive appears.

### Command line: esptool

```sh
pip install esptool
# optional: back up the factory firmware (16 MB)
esptool.py --chip esp32s3 --port PORT read_flash 0 0x1000000 factory-backup.bin
esptool.py --chip esp32s3 --port PORT erase_flash
esptool.py --chip esp32s3 --port PORT write_flash -z 0x0 guition_jc3636w518c_v2-11.0.0-alpha.3-g6465d03.bin
```

`PORT` is e.g. `COM3` on Windows, `/dev/cu.usbmodem…` on macOS, or
`/dev/ttyACM0` on Linux. Unplug and replug when done.

## Next steps

* [docs/usage.md](docs/usage.md): libraries, examples, display, touch, audio, BLE
* [docs/hardware.md](docs/hardware.md): pin map, revisions, schematic notes
* [docs/development.md](docs/development.md): building the firmware yourself
