# SPDX-License-Identifier: MIT
# Microphone level meter. Works on both hardware revisions:
#   batch > 2528 (_v2 build):  PDM microphone   -> audiobusio.PDMIn
#   batch <= 2528:             I2S MEMS mic     -> audioi2sin.I2SIn (CircuitPython 11+)
# Prints a tuple per reading, so the Mu / Thonny plotter can graph it.
import array
import math
import time

import board

N = 320  # 20 ms at 16 kHz

if hasattr(board, "MIC_CLK"):
    import audiobusio

    mic = audiobusio.PDMIn(board.MIC_CLK, board.MIC_DATA, sample_rate=16000, bit_depth=16)
    buf = array.array("H", [0] * N)  # PDMIn gives unsigned samples
    print("PDM microphone")
else:
    import audioi2sin  # needs CircuitPython 11 or newer

    # MSM261S4030H0R: 24-bit data in 32-bit slots, L/R pin low = left channel.
    mic = audioi2sin.I2SIn(board.MIC_SCK, board.MIC_WS, board.MIC_SD,
                           sample_rate=16000, bit_depth=32, output_bit_depth=16, mono=True)
    buf = array.array("h", [0] * N)
    print("I2S microphone")

while True:
    mic.record(buf, len(buf))
    mean = sum(buf) / len(buf)
    rms = math.sqrt(sum((s - mean) ** 2 for s in buf) / len(buf))
    print((rms,))
    time.sleep(0.05)
