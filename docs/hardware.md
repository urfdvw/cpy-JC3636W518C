# Guition JC3636W518C hardware reference

Also sold as "Taiji Pi S3" (太极小派). The trailing **C** marks the capacitive-touch
version; JC3636W518**N** is the same board without touch.

No official English datasheet is published. The vendor ships a download package
to buyers (schematics, a Chinese user manual, datasheets, flashing tools).
Everything below has been checked against the vendor schematic (sheets
`1_P1`, `2_S3R8`, `3_DAC`, `4_LCD`, `5_QI`) and the vendor manual, and
agrees with the public projects listed under [Sources](#sources).

## Summary

| Block        | Part                                   | Notes |
|--------------|----------------------------------------|-------|
| SoC          | ESP32-S3R8 (dual-core LX7, 240 MHz)    | Wi-Fi 2.4 GHz + BLE 5 |
| PSRAM        | 8 MB octal (in package)                | uses GPIO33–37 internally |
| Flash        | 16 MB quad SPI                          | see note on flash size below |
| Display      | 1.8" (some listings: 1.85") round IPS, 360×360, ST77916 | 4-wire QSPI, RGB565, colors inverted |
| Backlight    | GPIO15                                 | active high, PWM-dimmable |
| Touch        | CST816S (or CST816T/D) at I2C 0x15     | single point + gestures |
| Audio out    | PCM5100A I2S DAC                       | 3.5 mm jack (PJ-342C) + line-out header CN4, no speaker amplifier |
| Microphone   | batch ≤ 2528: MSM261S4030H0R I2S MEMS (L/R tied low = left slot); batch > 2528: PDM | see revisions |
| Storage      | microSD (TF) on SDMMC                  | |
| Power        | 5 V from USB-C or Qi wireless receiver | Qi has no GPIO; no battery or battery sense |
| USB          | ESP32-S3 native USB (GPIO19/20)        | USB-C |
| Button       | BOOT on GPIO0                          | active low, external pull-up |
| Header CN2   | 2×2, 1.27 mm pitch                     | 1: 5V, 2: GPIO39, 3: GND, 4: GPIO38 |
| Header CN4   | 2×2, 1.27 mm pitch                     | 1: LINE_OUT_R, 2: LINE_OUT_L, 3/4: GND |

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
| 38 | Header CN2 pin 4 | `IO38`, `HEADER_IO38` |
| 39 | Header CN2 pin 2 | `IO39`, `HEADER_IO39` |
| 43/44 | UART0 TX/RX (chip pins only, not on a connector) | `TX`, `RX` |
| 45 | Mic WS (≤ 2528) / PDM CLK (> 2528) | `MIC_WS` / `MIC_CLK` |
| 46 | Mic SD (≤ 2528) / PDM DATA (> 2528) | `MIC_SD` / `MIC_DATA` |
| 47 | LCD RST | `LCD_RESET` |
| 48 | DAC XSMT (mute): HIGH = sound on | `AUDIO_MUTE` |

GPIO38 and GPIO39 are the only free GPIOs; they go to the small CN2 header
together with 5 V and GND. The panel's TE (tearing) line is not connected to
the ESP32-S3.

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

### ST77916 init tables

Four different vendor init tables for this panel are in circulation:

| Name | Origin | Used by |
|------|--------|---------|
| `V1` | vendor demo `scr_st77916.h` (= xiaozhi V1) | `guition_jc3636w518c` firmware |
| `V2` | xiaozhi-esp32 `taiji-pi-s3`, batch > 2528 | `guition_jc3636w518c_v2` firmware |
| `ESP_DEFAULT` | Espressif `esp_lcd_st77916` default (ESP32_Display_Panel v0.1.4) | what the vendor Arduino demo really runs: its own `configVendorCommands()` call is commented out |
| `BOE` | vendor file `ST77916_BOE 1.8'' 360x360 initial code_V1.7_20231208.txt` | none of the firmware here (the vendor's `Initialization code.txt` differs by one gamma byte) |

All four are in `lib/jc3636w518_panels.py`. `examples/panel_test.py` cycles
through them with a screen tap or the BOOT button, so you can see which one suits your glass.
To use a different table permanently, call
`jc3636w518_panels.init_display(...)` at the top of `code.py`.

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
* **Flash size.** The schematic's flash symbol is labelled BY25Q64 (8 MB),
  but the manual says 16 MB, and a batch-2628 board reads JEDEC ID
  `0x684018`: a Boya BY25Q128, 16 MB. The firmware is built for 16 MB. If
  a board ever reports `0x684017` (8 MB) with `esptool flash_id`, rebuild with
  `CIRCUITPY_ESP_FLASH_SIZE = 8MB`. Boya parts use ESP-IDF's generic QIO
  enable, so QIO mode is fine.
* **TF card.** The schematic shows all four data lines wired, with pull-ups on
  a resistor network. If 4-bit mode gives trouble with a card, use
  `data=[board.SD_D0]` (1-bit).
* **Backlight.** GPIO15 drives the gate of a low-side N-MOSFET (AO8400A), so
  the backlight is active high and can be PWM-dimmed.
* **Audio.** The PCM5100A is hardware-configured (FMT low = I2S, no control
  bus). XSMT (GPIO48) is the soft-mute input: HIGH plays, LOW mutes. The
  output feeds both the 3.5 mm jack and the CN4 header. CircuitPython 10.x has no I2S
  *input* class, so the I2S microphone on batch ≤ 2528 boards cannot be used
  from Python. The PDM microphone on batch > 2528 boards works with
  `audiobusio.PDMIn`.

## Sources

* Vendor demo `ST77916_LVGL_DEMO` (`pincfg.h`, `scr_st77916.h`) and bundled ESP32_Display_Panel v0.1.4 (identical to upstream).
* Vendor download package: schematic sheets `1_P1`, `2_S3R8`, `3_DAC`, `4_LCD`, `5_QI`;
  `JC3636W518使用说明-CN.pdf` (manual: ESP32-S3R8, 8 MB PSRAM, 16 MB flash, ST77916, CST816).

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
