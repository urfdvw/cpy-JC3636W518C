# SPDX-License-Identifier: MIT
# Tell the two JC3636W518C hardware revisions apart when the batch label is
# missing. Works on either firmware build.
#
# The newer revision (batch > 2528) has a PDM microphone: CLK on GPIO45,
# DATA on GPIO46. The older one has an I2S microphone, which also needs a bit
# clock on GPIO42, so it stays silent when driven as a PDM mic.
#
# The script records about 2 s of quiet, then asks you to talk, clap or
# tap near the mic for about 2 s, and compares the two levels.
import array
import math
import time

import audiobusio
import board

SAMPLES = 1600  # 0.1 s at 16 kHz


def level(mic, seconds):
    buf = array.array("H", [0] * SAMPLES)
    total = 0.0
    n = int(seconds * 10)
    for _ in range(n):
        mic.record(buf, len(buf))
        mean = sum(buf) / len(buf)
        total += math.sqrt(sum((s - mean) ** 2 for s in buf) / len(buf))
    return total / n


mic = audiobusio.PDMIn(board.IO45, board.IO46, sample_rate=16000, bit_depth=16)
time.sleep(0.3)
level(mic, 0.3)  # discard start-up transient

print("Stay quiet...")
quiet = level(mic, 2)
print("Now talk, clap or tap near the board...")
time.sleep(0.5)
loud = level(mic, 2)
mic.deinit()

ratio = loud / quiet if quiet else float("inf")
print("quiet RMS = %.1f  loud RMS = %.1f  ratio = %.1f" % (quiet, loud, ratio))
if quiet < 1 and loud < 1:
    print("No signal at all -> I2S microphone -> OLD revision (batch <= 2528).")
    print("Use firmware guition_jc3636w518c.")
elif ratio > 3:
    print("PDM microphone responds -> NEW revision (batch > 2528).")
    print("Use firmware guition_jc3636w518c_v2.")
else:
    print("Inconclusive (constant noise but no response to sound).")
    print("Most likely the I2S microphone with a floating data line -> OLD revision.")
    print("Repeat with louder sound to be sure.")
