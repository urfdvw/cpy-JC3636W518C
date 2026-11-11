// This file is part of the CircuitPython project: https://circuitpython.org
// SPDX-License-Identifier: MIT
//
// Shared by guition_jc3636w518c and guition_jc3636w518c_v2.

#include "py/obj.h"
#include "py/mphal.h"
#include "shared-bindings/board/__init__.h"
#include "shared-bindings/microcontroller/Pin.h"
#include "shared-module/displayio/__init__.h"

static const mp_rom_map_elem_t board_module_globals_table[] = {
    CIRCUITPYTHON_BOARD_DICT_STANDARD_ITEMS

    // Buttons
    { MP_ROM_QSTR(MP_QSTR_BUTTON),     MP_ROM_PTR(&pin_GPIO0) },
    { MP_ROM_QSTR(MP_QSTR_BOOT),       MP_ROM_PTR(&pin_GPIO0) },

    // UART
    { MP_ROM_QSTR(MP_QSTR_TX),         MP_ROM_PTR(&pin_GPIO43) },
    { MP_ROM_QSTR(MP_QSTR_RX),         MP_ROM_PTR(&pin_GPIO44) },

    // I2C (CST816S touch, address 0x15)
    { MP_ROM_QSTR(MP_QSTR_SDA),        MP_ROM_PTR(&pin_GPIO7) },
    { MP_ROM_QSTR(MP_QSTR_SCL),        MP_ROM_PTR(&pin_GPIO8) },
    { MP_ROM_QSTR(MP_QSTR_TOUCH_SDA),  MP_ROM_PTR(&pin_GPIO7) },
    { MP_ROM_QSTR(MP_QSTR_TOUCH_SCL),  MP_ROM_PTR(&pin_GPIO8) },
    { MP_ROM_QSTR(MP_QSTR_TOUCH_RST),  MP_ROM_PTR(&pin_GPIO40) },
    { MP_ROM_QSTR(MP_QSTR_TOUCH_INT),  MP_ROM_PTR(&pin_GPIO41) },

    // ST77916 QSPI display (driven by board.DISPLAY)
    { MP_ROM_QSTR(MP_QSTR_LCD_CLK),       MP_ROM_PTR(&pin_GPIO9) },
    { MP_ROM_QSTR(MP_QSTR_LCD_CS),        MP_ROM_PTR(&pin_GPIO10) },
    { MP_ROM_QSTR(MP_QSTR_LCD_D0),        MP_ROM_PTR(&pin_GPIO11) },
    { MP_ROM_QSTR(MP_QSTR_LCD_D1),        MP_ROM_PTR(&pin_GPIO12) },
    { MP_ROM_QSTR(MP_QSTR_LCD_D2),        MP_ROM_PTR(&pin_GPIO13) },
    { MP_ROM_QSTR(MP_QSTR_LCD_D3),        MP_ROM_PTR(&pin_GPIO14) },
    { MP_ROM_QSTR(MP_QSTR_LCD_RESET),     MP_ROM_PTR(&pin_GPIO47) },
    { MP_ROM_QSTR(MP_QSTR_LCD_BACKLIGHT), MP_ROM_PTR(&pin_GPIO15) },

    // TF card, 4-bit SDMMC (use sdioio)
    { MP_ROM_QSTR(MP_QSTR_SD_CLK),     MP_ROM_PTR(&pin_GPIO3) },
    { MP_ROM_QSTR(MP_QSTR_SD_CMD),     MP_ROM_PTR(&pin_GPIO4) },
    { MP_ROM_QSTR(MP_QSTR_SD_D0),      MP_ROM_PTR(&pin_GPIO2) },
    { MP_ROM_QSTR(MP_QSTR_SD_D1),      MP_ROM_PTR(&pin_GPIO1) },
    { MP_ROM_QSTR(MP_QSTR_SD_D2),      MP_ROM_PTR(&pin_GPIO6) },
    { MP_ROM_QSTR(MP_QSTR_SD_D3),      MP_ROM_PTR(&pin_GPIO5) },

    // PCM5100A I2S DAC -> 3.5mm headphone jack (use audiobusio.I2SOut)
    { MP_ROM_QSTR(MP_QSTR_I2S_BCLK),   MP_ROM_PTR(&pin_GPIO18) },
    { MP_ROM_QSTR(MP_QSTR_I2S_LRCLK),  MP_ROM_PTR(&pin_GPIO16) },
    { MP_ROM_QSTR(MP_QSTR_I2S_WS),     MP_ROM_PTR(&pin_GPIO16) },
    { MP_ROM_QSTR(MP_QSTR_I2S_DOUT),   MP_ROM_PTR(&pin_GPIO17) },
    { MP_ROM_QSTR(MP_QSTR_I2S_MCLK),   MP_ROM_PTR(&pin_GPIO21) },
    // PCM5100A XSMT: drive HIGH to un-mute, LOW mutes.
    { MP_ROM_QSTR(MP_QSTR_AUDIO_MUTE), MP_ROM_PTR(&pin_GPIO48) },

    // Microphone
    #if JC3636W518_PANEL_V2
    // PDM microphone (use audiobusio.PDMIn(board.MIC_CLK, board.MIC_DATA))
    { MP_ROM_QSTR(MP_QSTR_MIC_CLK),    MP_ROM_PTR(&pin_GPIO45) },
    { MP_ROM_QSTR(MP_QSTR_MIC_DATA),   MP_ROM_PTR(&pin_GPIO46) },
    #else
    // Standard I2S MEMS microphone
    { MP_ROM_QSTR(MP_QSTR_MIC_SCK),    MP_ROM_PTR(&pin_GPIO42) },
    { MP_ROM_QSTR(MP_QSTR_MIC_WS),     MP_ROM_PTR(&pin_GPIO45) },
    { MP_ROM_QSTR(MP_QSTR_MIC_SD),     MP_ROM_PTR(&pin_GPIO46) },
    #endif

    // Raw GPIO names (Espressif convention)
    { MP_ROM_QSTR(MP_QSTR_IO0),     MP_ROM_PTR(&pin_GPIO0) },
    { MP_ROM_QSTR(MP_QSTR_IO1),     MP_ROM_PTR(&pin_GPIO1) },
    { MP_ROM_QSTR(MP_QSTR_IO2),     MP_ROM_PTR(&pin_GPIO2) },
    { MP_ROM_QSTR(MP_QSTR_IO3),     MP_ROM_PTR(&pin_GPIO3) },
    { MP_ROM_QSTR(MP_QSTR_IO4),     MP_ROM_PTR(&pin_GPIO4) },
    { MP_ROM_QSTR(MP_QSTR_IO5),     MP_ROM_PTR(&pin_GPIO5) },
    { MP_ROM_QSTR(MP_QSTR_IO6),     MP_ROM_PTR(&pin_GPIO6) },
    { MP_ROM_QSTR(MP_QSTR_IO7),     MP_ROM_PTR(&pin_GPIO7) },
    { MP_ROM_QSTR(MP_QSTR_IO8),     MP_ROM_PTR(&pin_GPIO8) },
    { MP_ROM_QSTR(MP_QSTR_IO9),     MP_ROM_PTR(&pin_GPIO9) },
    { MP_ROM_QSTR(MP_QSTR_IO10),    MP_ROM_PTR(&pin_GPIO10) },
    { MP_ROM_QSTR(MP_QSTR_IO11),    MP_ROM_PTR(&pin_GPIO11) },
    { MP_ROM_QSTR(MP_QSTR_IO12),    MP_ROM_PTR(&pin_GPIO12) },
    { MP_ROM_QSTR(MP_QSTR_IO13),    MP_ROM_PTR(&pin_GPIO13) },
    { MP_ROM_QSTR(MP_QSTR_IO14),    MP_ROM_PTR(&pin_GPIO14) },
    { MP_ROM_QSTR(MP_QSTR_IO15),    MP_ROM_PTR(&pin_GPIO15) },
    { MP_ROM_QSTR(MP_QSTR_IO16),    MP_ROM_PTR(&pin_GPIO16) },
    { MP_ROM_QSTR(MP_QSTR_IO17),    MP_ROM_PTR(&pin_GPIO17) },
    { MP_ROM_QSTR(MP_QSTR_IO18),    MP_ROM_PTR(&pin_GPIO18) },
    { MP_ROM_QSTR(MP_QSTR_IO21),    MP_ROM_PTR(&pin_GPIO21) },
    { MP_ROM_QSTR(MP_QSTR_IO38),    MP_ROM_PTR(&pin_GPIO38) },
    { MP_ROM_QSTR(MP_QSTR_IO39),    MP_ROM_PTR(&pin_GPIO39) },
    { MP_ROM_QSTR(MP_QSTR_IO40),    MP_ROM_PTR(&pin_GPIO40) },
    { MP_ROM_QSTR(MP_QSTR_IO41),    MP_ROM_PTR(&pin_GPIO41) },
    { MP_ROM_QSTR(MP_QSTR_IO42),    MP_ROM_PTR(&pin_GPIO42) },
    { MP_ROM_QSTR(MP_QSTR_IO43),    MP_ROM_PTR(&pin_GPIO43) },
    { MP_ROM_QSTR(MP_QSTR_IO44),    MP_ROM_PTR(&pin_GPIO44) },
    { MP_ROM_QSTR(MP_QSTR_IO45),    MP_ROM_PTR(&pin_GPIO45) },
    { MP_ROM_QSTR(MP_QSTR_IO46),    MP_ROM_PTR(&pin_GPIO46) },
    { MP_ROM_QSTR(MP_QSTR_IO47),    MP_ROM_PTR(&pin_GPIO47) },
    { MP_ROM_QSTR(MP_QSTR_IO48),    MP_ROM_PTR(&pin_GPIO48) },

    // Display (initialized in board_init)
    { MP_ROM_QSTR(MP_QSTR_DISPLAY), MP_ROM_PTR(&displays[0].display) },
};
MP_DEFINE_CONST_DICT(board_module_globals, board_module_globals_table);
