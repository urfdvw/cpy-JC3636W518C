# SPDX-License-Identifier: MIT
# Microphone level meter for the V2 board (PDM microphone, batch > 2528).
# The original board (batch <= 2528) has a standard I2S MEMS microphone on
# MIC_SCK/MIC_WS/MIC_SD; CircuitPython has no I2S input class yet, so it is
# not usable from Python on that variant.
import array
import math
import time

import audiobusio
import board

mic = audiobusio.PDMIn(board.MIC_CLK, board.MIC_DATA, sample_rate=16000, bit_depth=16)
buf = array.array("H", [0] * 320)

while True:
    mic.record(buf, len(buf))
    mean = sum(buf) / len(buf)
    rms = math.sqrt(sum((s - mean) ** 2 for s in buf) / len(buf))
    print((rms,))
    time.sleep(0.05)
