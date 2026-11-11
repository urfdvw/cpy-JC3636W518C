// This file is part of the CircuitPython project: https://circuitpython.org
// SPDX-License-Identifier: MIT

#pragma once

#define MICROPY_HW_BOARD_NAME "Guition JC3636W518C V2"
#define MICROPY_HW_MCU_NAME   "ESP32S3"

// New panel glass + PDM microphone (label batch > 2528, from 2025-07).
#define JC3636W518_PANEL_V2 (1)

#include "../guition_jc3636w518c/jc3636w518_common.h"
