# Guition JC3636W518C hardware reference

Also sold as "Taiji Pi S3" (太极小派). The trailing **C** marks the capacitive-touch
version; JC3636W518**N** is the same board without touch.

No official English datasheet is published. The vendor ships a download package
(schematics, `pincfg.h`, Arduino/ESP-IDF demos) to buyers. The tables below are
put together from public projects that use that package, listed under
[Sources](#sources). Each pin was checked in at least two of them, except
where a note says otherwise.

## Summary

| Block        | Part                                   | Notes |
|--------------|----------------------------------------|-------|
| SoC          | ESP32-S3R8 (dual-core LX7, 240 MHz)    | Wi-Fi 2.4 GHz + BLE 5 |
| PSRAM        | 8 MB octal (in package)                | uses GPIO33–37 internally |
| Flash        | 16 MB quad SPI                          | |
| Display      | 1.8" (some listings: 1.85") round IPS, 360×360, ST77916 | 4-wire QSPI, RGB565, colors inverted |
| Backlight    | GPIO15                                 | active high, PWM-dimmable |
| Touch        | CST816S (or CST816T/D) at I2C 0x15     | single point + gestures |
| Audio out    | PCM5100A I2S DAC                       | 3.5 mm headphone jack only, no speaker amplifier |
| Microphone   | batch ≤ 2528: I2S MEMS; batch > 2528: PDM | see revisions |
| Storage      | microSD (TF) on SDMMC                  | |
| Charging     | Qi wireless receiver                   | not connected to any GPIO |
| USB          | ESP32-S3 native USB (GPIO19/20)        | USB-C |
| Button       | BOOT on GPIO0                          | active low |

## Pin map

| GPIO | Function | CircuitPython `board.` name |
|------|----------|-----------------------------|
| 0  | BOOT button | `BUTTON`, `BOOT` |
| 1  | SD D1 | `SD_D1` |
| 2  | SD D0 | `SD_D0` |
| 3  | SD CLK | `SD_CLK` |
| 4  | SD CMD | `SD_CMD` |
| 5  | SD D3 | `SD_D3` |
| 6  | SD D2 | `SD_D2` |
| 7  | I2C SDA (touch) | `SDA`, `TOUCH_SDA` |
| 8  | I2C SCL (touch) | `SCL`, `TOUCH_SCL` |
| 9  | LCD QSPI CLK | `LCD_CLK` |
| 10 | LCD CS | `LCD_CS` |
| 11 | LCD D0 | `LCD_D0` |
| 12 | LCD D1 | `LCD_D1` |
| 13 | LCD D2 | `LCD_D2` |
| 14 | LCD D3 | `LCD_D3` |
| 15 | LCD backlight | `LCD_BACKLIGHT` (owned by `board.DISPLAY`) |
| 16 | DAC I2S LRCLK/WS | `I2S_LRCLK`, `I2S_WS` |
| 17 | DAC I2S DOUT | `I2S_DOUT` |
| 18 | DAC I2S BCLK | `I2S_BCLK` |
| 19/20 | USB D−/D+ | — |
| 21 | DAC I2S MCLK | `I2S_MCLK` |
| 40 | Touch RST | `TOUCH_RST` |
| 41 | Touch INT | `TOUCH_INT` |
| 42 | Mic I2S SCK (batch ≤ 2528 only) | `MIC_SCK` |
| 43/44 | UART TX/RX | `TX`, `RX` |
| 45 | Mic WS (≤ 2528) / PDM CLK (> 2528) | `MIC_WS` / `MIC_CLK` |
| 46 | Mic SD (≤ 2528) / PDM DATA (> 2528) | `MIC_SD` / `MIC_DATA` |
| 47 | LCD RST | `LCD_RESET` |
| 48 | DAC XSMT (mute): HIGH = sound on | `AUDIO_MUTE` |

GPIO38 and GPIO39 are not used by any on-board part (also exposed as `IO38`/`IO39`).
No public source shows whether they reach a connector.

## Hardware revisions

The printed batch number on the label tells them apart. From July 2025
(batch > 2528) Guition changed the microphone, because the old one was
discontinued, and the panel glass, which needs a different ST77916 init table.

| | batch ≤ 2528 | batch > 2528 |
|-|--------------|--------------|
| Microphone | I2S: SCK 42, WS 45, SD 46 | PDM: CLK 45, DATA 46 |
| Panel init | vendor "V1" table | vendor "V2" table |
| Firmware here | `guition_jc3636w518c` | `guition_jc3636w518c_v2` |

If the screen stays black or looks wrong with one build, flash the other.

## Details and caveats

* **Display.** The ST77916 is driven by CircuitPython's `qspibus` with
  0x02 command and 0x32 pixel-write framing at 40 MHz. The init sequence is
  the vendor table, followed by COLMOD 0x55, MADCTL 0x00, INVON, SLPOUT and
  DISPON. With MADCTL 0x00, the CST816 coordinates match the picture without
  any transform. Turn both together with `display.rotation`, and pass the
  same value to the touch driver.
* **Touch.** The CST816 goes to sleep after a few seconds without a touch.
  While asleep it does not acknowledge on I2C. `lib/cst816.py` writes
  register 0xFE = 1 to turn auto-sleep off, and treats I2C errors as
  "no touch".
* **TF card.** The vendor `pincfg.h` and schematic show a 4-bit bus. One
  ESPHome config uses it in 1-bit mode (D0/CLK/CMD only). If 4-bit fails, use
  `data=[board.SD_D0]`.
* **Audio.** The PCM5100A has no control interface. XSMT (GPIO48) must be
  HIGH, as the vendor firmware sets it. CircuitPython 10.x has no I2S
  *input* class, so the I2S microphone on batch ≤ 2528 boards cannot be used
  from Python. The PDM microphone on batch > 2528 boards works with
  `audiobusio.PDMIn`.

## Sources

* xiaozhi-esp32, board `taiji-pi-s3` (pins, both panel init tables, revision notes):
  https://github.com/78/xiaozhi-esp32/tree/main/main/boards/taiji-pi-s3
* orbis-panel `main/bsp_board.h` (from vendor `pincfg.h` + schematic `4_LCD.pdf`; SD 4-bit, PCM5100A, batch table):
  https://github.com/xiao-si-qi/orbis-panel
* ESPHome reference config by clowrey (display, touch, audio, mute):
  https://github.com/clowrey/esphome-guition-360x360-jc3636w518
* ESPHome device file by patrick3399 (memory, DAC, TF card, mic):
  https://github.com/patrick3399/esphome_components/blob/main/devices/guition/jc3636w518.yaml
* ESPHome `mipi_spi` models `JC3636W518` / `JC3636W518V2`:
  https://github.com/esphome/esphome/blob/dev/esphome/components/mipi_spi/models/jc.py
* Home Assistant community thread (cited by the above; not reachable from the build environment):
  https://community.home-assistant.io/t/guition-1-8-360x360-esp32-s3-jc3636w518-smart-display/750515
