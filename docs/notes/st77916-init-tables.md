# ST77916 init tables: research notes

The ST77916 needs a long vendor-specific init sequence (gate timing, gamma,
power), which differs per panel glass. Six tables were collected for this
board. Compared with `tools/st77916_tables.py compare`, ignoring delays and
the trailing INVON/SLPOUT/DISPON, they reduce to four distinct ones.

| Table | Source | Commands | Starts with |
|-------|--------|----------|-------------|
| V1 | xiaozhi-esp32 `taiji-pi-s3`, `CONFIG_TAIJIPAI_I2S_TYPE_STD` branch | 216 | `F0 08` |
| VENDOR_DEMO | vendor `ST77916_LVGL_DEMO/scr_st77916.h` | 216 | `F0 08` — **identical to V1** |
| ESP_DEFAULT | Espressif `esp_lcd_st77916.c` default, ESP32_Display_Panel v0.1.4 | 216 | `F0 08` |
| V2 | xiaozhi-esp32 `taiji-pi-s3`, PDM branch (batch > 2528) | 184 | `F0 28` |
| BOE | vendor `ST77916_BOE 1.8'' 360x360 initial code_V1.7_20231208.txt` | 181 | `F0 28` |
| VENDOR_INIT_CODE | vendor `Initialization code.txt` | 181 | `F0 28` — BOE with one gamma byte changed |

## How they differ

* **V1 vs ESP_DEFAULT:** the same structure, with 31 commands changed. ESP_DEFAULT
  adds `B8 04`, and differs in `DD/DE` (VCOM), `E0/E2`, and the GIP timing block
  `80–BC` (`48`→`38`, and each start/end value one lower). It also differs in `C0/D0`.
* **BOE vs VENDOR_INIT_CODE:** only the last byte of the `E1` negative gamma
  (`2D` vs `24`).
* **V2 vs BOE:** both start the "28" family (`F0 28`, `F2 28`, `7C D1`, …), but V2
  adds `73 F0`, uses different power settings (`B0–B8`), drops `DD/DE`, and has
  completely different gamma (`E0/E1`) and GIP timing (`60–D9`).

## What the vendor demo actually runs

`ST77916_LVGL_DEMO.ino` builds the panel with ESP32_Display_Panel, but the line
`lcd->configVendorCommands(lcd_init_cmd, ...)` is commented out. So the demo
runs the library's built-in default (ESP_DEFAULT), not its own
`scr_st77916.h` table. The ESP32_Display_Panel and ESP32_IO_Expander copies
in the vendor package are unmodified upstream v0.1.4 / v0.0.2.

## Hardware results

| Board | Panel label | Table | Result |
|-------|-------------|-------|--------|
| PCB `V1.3`, batch `2628` | `H0185Y040X V0`, 2026-07-14 | V2 (built into `_v2` firmware) | boots; REPL visible on screen |

Add rows here as more boards and tables are tried with `examples/panel_test.py`.

## Orientation and touch

The vendor demo's `setRotation()` always applies the same swap/mirror to the
LCD and the touch panel, and rotation 0 uses no mirroring. The firmware
therefore sends MADCTL `0x00`, and the raw CST816 coordinates match the
picture. xiaozhi uses `mirror_x = mirror_y = true`, which is a 180° turn.
That only changes which edge counts as "up".

## Reproducing

```sh
git clone --depth 1 https://github.com/78/xiaozhi-esp32
git clone --depth 1 --branch v0.1.4 https://github.com/esp-arduino-libs/ESP32_Display_Panel
X=xiaozhi-esp32/main/boards/taiji-pi-s3/taiji_pi_s3.cc
E=ESP32_Display_Panel/src/lcd/base/esp_lcd_st77916.c
tools/st77916_tables.py --xiaozhi $X --esp-lib $E compare V1,ESP_DEFAULT V2,BOE
tools/st77916_tables.py --xiaozhi $X --esp-lib $E python > lib/jc3636w518_panels.py
tools/st77916_tables.py --xiaozhi $X --esp-lib $E c V2      # rows for board.c
```
