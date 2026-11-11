# SPDX-License-Identifier: MIT
# Play a 440 Hz tone through the PCM5100A DAC (3.5 mm headphone jack).
# There is no on-board speaker amplifier: use headphones or powered speakers.
import array
import math
import time

import audiobusio
import audiocore
import board
import digitalio

mute = digitalio.DigitalInOut(board.AUDIO_MUTE)
mute.switch_to_output(value=True)  # HIGH = un-muted

RATE = 16000
length = RATE // 440
wave = array.array("h", [int(math.sin(2 * math.pi * i / length) * 8000) for i in range(length)])
tone = audiocore.RawSample(wave, sample_rate=RATE)

i2s = audiobusio.I2SOut(board.I2S_BCLK, board.I2S_LRCLK, board.I2S_DOUT)
i2s.play(tone, loop=True)
time.sleep(2)
i2s.stop()
mute.value = False
