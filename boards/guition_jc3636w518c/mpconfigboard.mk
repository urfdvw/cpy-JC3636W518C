# This file is part of the CircuitPython project: https://circuitpython.org
# SPDX-License-Identifier: MIT

# 0x303A:0x8000 is Espressif's shared *test* PID. This is an unofficial,
# out-of-tree board; request a dedicated PID from
# https://github.com/espressif/usb-pids before upstreaming.
USB_VID = 0x303A
USB_PID = 0x8000
USB_MANUFACTURER = "Guition"
USB_PRODUCT = "JC3636W518C"

IDF_TARGET = esp32s3

# ESP32-S3R8: 8MB octal PSRAM in package, 16MB external quad flash
CIRCUITPY_ESP_FLASH_SIZE = 16MB
CIRCUITPY_ESP_FLASH_MODE = qio
CIRCUITPY_ESP_FLASH_FREQ = 80m

CIRCUITPY_ESP_PSRAM_SIZE = 8MB
CIRCUITPY_ESP_PSRAM_MODE = opi
CIRCUITPY_ESP_PSRAM_FREQ = 80m

OPTIMIZATION_FLAGS = -Os

# ST77916 display on a QSPI bus
CIRCUITPY_QSPIBUS = 1
CIRCUITPY_PARALLELDISPLAYBUS = 0

# No camera connector
CIRCUITPY_ESPCAMERA = 0

# TF card on 4-bit SDMMC
CIRCUITPY_SDIOIO = 1

# Display refresh buffer on the stack (same value as other ESP32-S3 QSPI boards)
CIRCUITPY_DISPLAY_AREA_BUFFER_SIZE = 8192
