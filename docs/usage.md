# Using CircuitPython on the JC3636W518C

## Status

| Feature | How | Tested on hardware |
|---------|-----|--------------------|
| Display (`board.DISPLAY`, REPL on screen) | built-in, `qspibus` + `busdisplay` | yes (V2 build, batch 2628; 10.3.2 and `11.0.0-alpha.3-g6465d03`) |
| USB `CIRCUITPY` drive and serial REPL | built-in | yes (V2 build, batch 2628; 10.3.2 and `11.0.0-alpha.3-g6465d03`) |
| BLE central: scan, connect, pair, HID keyboard input | `_bleio`, see [`examples/keyboard host/`](#ble) | **yes** (V2 build `11.0.0-alpha.3-g6465d03`, Clicks Power Keyboard) |
| Backlight dimming | `board.DISPLAY.brightness` | not yet |
| Touch | `lib/cst816.py` | not yet |
| TF card | `sdioio` | not yet |
| Headphone / line out | `audiobusio.I2SOut` | not yet |
| Microphone, batch > 2528 (PDM) | `audiobusio.PDMIn` | not yet |
| Microphone, batch ≤ 2528 (I2S) | `audioi2sin.I2SIn` (CircuitPython 11+) | not yet |
| Wi-Fi | `wifi` | not yet |
| BLE peripheral role | `_bleio`, `adafruit_ble` | not yet |
| `guition_jc3636w518c` (original revision) build | — | not yet |

## Libraries

Copy these from `lib/` to `CIRCUITPY/lib/`:

* `cst816.py`: touch driver (coordinates, gestures, rotation).
* `jc3636w518_panels.py`: all known ST77916 init tables, plus
  `init_display()` to restart the screen with one of them.

Some examples use `adafruit_display_text` (`circup install adafruit_display_text`).
Without it they still run, but print text to the serial console only.

## Examples

Single-file examples: copy one to `CIRCUITPY/code.py`.

| File | What it does |
|------|--------------|
| `examples/code.py` | color rings, title, and a dot that follows your finger |
| `examples/panel_test.py` | color bars; tap the screen or press BOOT to try the next panel init table |
| `examples/identify_board.py` | tells the two hardware revisions apart by the microphone |
| `examples/touch_test.py` | prints touch coordinates and gestures |
| `examples/sd_card.py` | mounts the TF card at `/sd` and lists it |
| `examples/audio_tone.py` | 440 Hz tone on the headphone jack |
| `examples/mic_level.py` | microphone level meter (PDM or I2S, picked by board) |

Complete project, tested on hardware:

| Folder | What it does |
|--------|--------------|
| [`examples/keyboard host/`](../examples/keyboard%20host/) | BLE keyboard host with an on-screen terminal and a Python prompt you type on the keyboard (see [BLE](#ble)) |

## Display

* 360×360, RGB565. The panel is round, so keep content inside the circle:
  anything outside about 180 px from the center is cut off.
* `board.DISPLAY.rotation = 0 / 90 / 180 / 270` turns the picture. Pass the
  same value to `CST816(..., rotation=...)` so touch coordinates follow.
* `board.DISPLAY.brightness = 0.0 … 1.0` sets the PWM backlight.
* There is no reset button. Use `microcontroller.reset()` or replug USB.

### Panel init tables

Guition has shipped several panel glasses, and four different ST77916 init
tables are in circulation (details in [hardware.md](hardware.md#st77916-init-tables)).
The firmware has one built in: `V1` in the original build, `V2` in the `_v2`
build. If the screen is blank, tinted or flickers, run
`examples/panel_test.py` and tap through the tables. To use another table
permanently, put this at the top of `code.py`:

```python
import jc3636w518_panels as panels
display = panels.init_display(panels.BOE)   # or V1, V2, ESP_DEFAULT
```

After that, use the returned `display`, not `board.DISPLAY`.

## Touch

```python
import board
from cst816 import CST816

touch = CST816(board.I2C(), reset_pin=board.TOUCH_RST, rotation=board.DISPLAY.rotation)
print(touch.chip_name)
while True:
    if p := touch.touch:
        print(p)          # (x, y) in display pixels
```

The CST816 normally goes to sleep a few seconds after the last touch and then
stops answering on I2C. The driver turns auto-sleep off, and treats any I2C
error as "no touch".

## TF card

```python
import board, sdioio, storage
sd = sdioio.SDCard(clock=board.SD_CLK, command=board.SD_CMD,
                   data=[board.SD_D0, board.SD_D1, board.SD_D2, board.SD_D3],
                   frequency=25_000_000)
storage.mount(storage.VfsFat(sd), "/sd")
```

If a card misbehaves in 4-bit mode, use `data=[board.SD_D0]`.

## Audio

The PCM5100A DAC drives the 3.5 mm jack and the CN4 line-out header. There is
no speaker amplifier, so use headphones or powered speakers. Set
`board.AUDIO_MUTE` HIGH to un-mute, then play through
`audiobusio.I2SOut(board.I2S_BCLK, board.I2S_LRCLK, board.I2S_DOUT)`.
See `examples/audio_tone.py`.

## Microphone

* Batch > 2528 (`_v2` build): PDM microphone.
  `audiobusio.PDMIn(board.MIC_CLK, board.MIC_DATA, sample_rate=16000, bit_depth=16)`.
* Batch ≤ 2528: I2S MEMS microphone (MSM261S4030H0R, left channel).
  It needs CircuitPython 11 or newer:
  `audioi2sin.I2SIn(board.MIC_SCK, board.MIC_WS, board.MIC_SD, sample_rate=16000, bit_depth=32, output_bit_depth=16)`.

`examples/mic_level.py` picks the right one automatically.

## BLE

`_bleio` works as both peripheral and central. ESP32-S3 has no Classic
Bluetooth, so only Bluetooth LE devices can connect.

### Working example: BLE keyboard host

The folder [`examples/keyboard host/`](../examples/keyboard%20host/) holds a complete,
tested `CIRCUITPY` drive: `code.py` plus the libraries it needs in `lib/`.
It turns the board into a host for a Bluetooth LE keyboard:

1. it scans for a keyboard whose advertised name starts with
   `TARGET_NAME_PREFIX` (default `"Power Keyboard"`; change it for your
   keyboard);
2. it connects, pairs and bonds, then reconnects to the same keyboard later;
3. it subscribes to the key reports, using boot protocol when the keyboard
   supports it;
4. it shows an on-screen terminal, and runs a Python prompt (`>>>`, with
   `...` continuation for blocks) that you type on the keyboard. Results and
   errors appear on the round screen, and are echoed to the serial console.

To use it, copy the folder's contents (not the folder itself) to the root of
`CIRCUITPY`, put the keyboard in pairing mode, and reset the board.

Tested on: a batch-2628 board (V2 build) running firmware `11.0.0-alpha.3-g6465d03`, with a Clicks
"Power Keyboard" (BLE 5.4; to enter pairing mode, hold `123` and press `0`).

Requirements and tips:

* **Firmware with the `_bleio` connect fix.** On stock 11.0.0-alpha.2,
  `connect()` to this keyboard never returned. The fix is
  [adafruit/circuitpython#11859](https://github.com/adafruit/circuitpython/pull/11859),
  and this repository's builds include it by default (see
  [building-latest-circuitpython.md](building-latest-circuitpython.md#where-the-source-comes-from)).
* **Turn off your phone's Bluetooth** (or anything else paired with the
  keyboard) while connecting. With the phone's Bluetooth on, the board could
  not see the keyboard at all.
* **Scan restarts are throttled.** On the ESP32 port the scan iterator ends
  as soon as its buffer is empty (~0.25 s), not after `timeout`. Restarting it
  in a tight loop makes NimBLE fail with "system firmware error: 21". The
  example sleeps 0.3 s between scans and recovers from scan errors.
* CircuitPython pairs as "Just Works", so keyboards that require you to type a
  passkey will not pair.
* adafruit_ble's `HIDService` has no host side, so the example uses `_bleio`
  directly.
* To forget bonded keyboards, run `_bleio.adapter.erase_bonding()`.

The debugging history behind this example (connect hang, root cause, the PR)
is in [`examples/keyboard host/MEMORY.md`](../examples/keyboard%20host/MEMORY.md) and
[notes/bring-up-log.md](notes/bring-up-log.md#ble-keyboard-host).

## Identifying the revision

The batch number is printed on the PCB next to the TF card slot. The panel
date on the back of the screen also gives a hint. If neither is readable,
flash either build and run `examples/identify_board.py`. It reads GPIO45/46
as a PDM microphone, first while you stay quiet and then while you talk:

* the level rises with sound: PDM microphone, so batch > 2528 → `_v2` build;
* no signal or no response: I2S microphone, so batch ≤ 2528 → original build.

`examples/panel_test.py` then confirms which panel table looks right.

## GPIO

The only free GPIOs are 38 and 39, on the 2×2 1.27 mm header CN2
(`board.HEADER_IO38`, `board.HEADER_IO39`; 5 V and GND are on the same
header). Every other pin is used by an on-board part. See the pin map in
[hardware.md](hardware.md#pin-map).
