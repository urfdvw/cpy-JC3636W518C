# Vendor material (Guition / 晶彩智能)

Files from the download package that Guition gives to buyers, sorted by
category. They are kept unmodified, with the original file names, as the
primary reference for this board.

| Folder | Contents | Original location in the package |
|--------|----------|----------------------------------|
| `manual/` | `JC3636W518使用说明-CN.pdf` (Chinese user manual: specs, factory firmware usage, dimensions); `用户注意事项.txt` (user notes); `aida_remote_1.85.rslcd` (AIDA64 layout for the factory firmware) | `1-使用说明/`, `3-规格书/`, root |
| `schematics/` | `1_P1.pdf` (USB-C, TF card, microphone, headers CN2/CN4, 3.3 V DC-DC), `2_S3R8.pdf` (ESP32-S3R8, flash, BOOT button, net labels for every GPIO), `3_DAC.pdf` (PCM5100A, 3.5 mm jack, DAC LDO), `4_LCD.pdf` (22-pin panel FPC, backlight MOSFET), `5_QI.pdf` (Qi receiver, VBUS/5 V switch) | `6-原理图/` |
| `datasheets/` | `ESP32-S3R8_规格书.pdf`, `pcm5100a.pdf`, `1.85显示屏.png` (panel drawing) | `4-芯片手册/`, `3-规格书/` |
| `mechanical/` | `JC3636W518_V1.0结构图.DWG` (enclosure drawing), product renders `1-1.jpg`, `1-2.jpg` | `5-尺寸图/` |
| `display-init/` | `ST77916_BOE 1.8'' 360x360 initial code_V1.7_20231208.txt`, `Initialization code.txt` | separate demo download |
| `demo/ST77916_LVGL_DEMO/` | Arduino LVGL demo: `pincfg.h` (pin map), `scr_st77916.h` (display, touch and backlight setup, with an init table), `.ino`, `lv_conf.h`, `编译说明.txt` (build notes: Arduino-ESP32 ≥ 3.0.1, ESP32_Display_Panel 0.1.4, ESP32_IO_Expander 0.0.2, LVGL ≤ 8.4.0), screenshots of Arduino settings | separate demo download |
| `flashing/` | `烧录操作1–3.png`: screenshots of the Flash Download Tool steps | `9-烧录/Burn operation instructions/` |

## Not included

* `9-烧录/flash_download_tool_3.9.3/` (Espressif's Windows flashing tool, with
  leftover cache and logs from the vendor's production line) and
  `8-工具/` (serial and network tools, `.rar`). These are generic tools,
  available from Espressif.
* The demo's media files: more than 30 MB, not needed.
* The ESP32_Display_Panel v0.1.4 and ESP32_IO_Expander v0.0.2 libraries
  shipped with the demo: unmodified upstream copies.
* The factory firmware image. It is not in the package; back it up from the
  board with `esptool read_flash` before the first erase (see the top-level
  README).

## Notes on the content

* The schematic labels the flash BY25Q64 (8 MB). Real boards have 16 MB (see
  [../notes/bring-up-log.md](../notes/bring-up-log.md#flash-size)).
* `scr_st77916.h` contains an init table, but the demo does not use it (see
  [../notes/st77916-init-tables.md](../notes/st77916-init-tables.md)).
* `pincfg.h` sets `AUDIO_I2S_MCK_IO -1`: the demo does not drive MCLK,
  although GPIO21 is wired to the DAC.
