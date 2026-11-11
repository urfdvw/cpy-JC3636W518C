// This file is part of the CircuitPython project: https://circuitpython.org
// SPDX-License-Identifier: MIT
//
// Settings shared by guition_jc3636w518c and guition_jc3636w518c_v2.

#pragma once

// I2C bus: CST816S touch controller (address 0x15) only.
#define CIRCUITPY_BOARD_I2C         (1)
#define CIRCUITPY_BOARD_I2C_PIN     {{.scl = &pin_GPIO8, .sda = &pin_GPIO7}}

// No general-purpose SPI bus: display is QSPI, TF card is SDMMC.
#define CIRCUITPY_BOARD_SPI         (0)

// Default UART (USB-serial chip pads / header)
#define DEFAULT_UART_BUS_RX         (&pin_GPIO44)
#define DEFAULT_UART_BUS_TX         (&pin_GPIO43)

// ST77916 QSPI display, initialized in board_init()
#define CIRCUITPY_BOARD_DISPLAY     (1)
#define CIRCUITPY_LCD_CLK           (&pin_GPIO9)
#define CIRCUITPY_LCD_CS            (&pin_GPIO10)
#define CIRCUITPY_LCD_D0            (&pin_GPIO11)
#define CIRCUITPY_LCD_D1            (&pin_GPIO12)
#define CIRCUITPY_LCD_D2            (&pin_GPIO13)
#define CIRCUITPY_LCD_D3            (&pin_GPIO14)
#define CIRCUITPY_LCD_RESET         (&pin_GPIO47)
#define CIRCUITPY_LCD_BACKLIGHT     (&pin_GPIO15)
