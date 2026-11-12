# Using CircuitPython on the JC3636W518C

## Status

| Feature | How | Tested on hardware |
|---------|-----|--------------------|
| Display (`board.DISPLAY`, REPL on screen) | built-in, `qspibus` + `busdisplay` | yes (V2 build, batch 2628) |
| USB `CIRCUITPY` drive and serial REPL | built-in | yes (V2 build, batch 2628) |
| Backlight dimming | `board.DISPLAY.brightness` | not yet |
| Touch | `lib/cst816.py` | not yet |
| TF card | `sdioio` | not yet |
| Headphone / line out | `audiobusio.I2SOut` | not yet |
| Microphone, batch > 2528 (PDM) | `audiobusio.PDMIn` | not yet |
| Microphone, batch ≤ 2528 (I2S) | not possible: CircuitPython has no I2S input | — |
| Wi-Fi, BLE | `wifi`, `_bleio` | not yet |
| `guition_jc3636w518c` (original revision) build | — | not yet |

## Libraries

Copy these from `lib/` to `CIRCUITPY/lib/`:

* `cst816.py`: touch driver (coordinates, gestures, rotation).
* `jc3636w518_panels.py`: all known ST77916 init tables, plus
  `init_display()` to restart the screen with one of them.

Some examples use `adafruit_display_text` (`circup install adafruit_display_text`).
Without it they still run, but print text to the serial console only.

## Examples

Copy one to `CIRCUITPY/code.py`.

| File | What it does |
|------|--------------|
| `examples/code.py` | color rings, title, and a dot that follows your finger |
| `examples/panel_test.py` | color bars; tap the screen or press BOOT to try the next panel init table |
| `examples/identify_board.py` | tells the two hardware revisions apart by the microphone |
| `examples/touch_test.py` | prints touch coordinates and gestures |
| `examples/sd_card.py` | mounts the TF card at `/sd` and lists it |
| `examples/audio_tone.py` | 440 Hz tone on the headphone jack |
| `examples/mic_level.py` | microphone level meter (PDM, batch > 2528) |
| `examples/ble_keyboard_host.py` | connects a BLE keyboard and shows what you type |

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
* Batch ≤ 2528: I2S MEMS microphone (`MIC_SCK`, `MIC_WS`, `MIC_SD`). It can't
  be used from Python yet, because CircuitPython has no I2S input class.

## BLE

`_bleio` works as both peripheral and central. ESP32-S3 has no Classic
Bluetooth, so only Bluetooth LE devices can connect.

`examples/ble_keyboard_host.py` acts as a host for a BLE keyboard. It scans,
pairs and bonds, subscribes to key reports (boot protocol when the keyboard
supports it), and shows typed text on screen. Limitations:

* CircuitPython pairs as "Just Works", so keyboards that require you to type a
  passkey will not pair.
* adafruit_ble's `HIDService` has no host side, so the example uses `_bleio`
  directly.
* To forget bonded keyboards, run `_bleio.adapter.erase_bonding()`.

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
