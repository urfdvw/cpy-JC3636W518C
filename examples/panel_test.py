# SPDX-License-Identifier: MIT
# Try each ST77916 init table and find the one that suits your panel glass.
#
# Shows color bars, a white ring at the panel edge and the table name.
# Press BOOT to switch to the next table. The serial console prints the name.
# A good table gives clean red/green/blue/white bars, black corners and no
# flicker or tint.
#
# Needs lib/jc3636w518_panels.py on CIRCUITPY/lib.
import time

import board
import digitalio
import displayio
import terminalio
import vectorio

import jc3636w518_panels as panels

try:
    from adafruit_display_text import label
except ImportError:
    label = None

button = digitalio.DigitalInOut(board.BUTTON)
button.switch_to_input(pull=digitalio.Pull.UP)

COLORS = (0xFF0000, 0x00FF00, 0x0000FF, 0xFFFFFF, 0x808080, 0x000000)


def scene(name):
    g = displayio.Group()
    bar_w = 360 // len(COLORS)
    for i, c in enumerate(COLORS):
        pal = displayio.Palette(1)
        pal[0] = c
        g.append(vectorio.Rectangle(pixel_shader=pal, width=bar_w, height=360, x=i * bar_w, y=0))
    ring = displayio.Palette(1)
    ring[0] = 0xFFFFFF
    inner = displayio.Palette(1)
    inner[0] = 0x000000
    g.append(vectorio.Circle(pixel_shader=ring, radius=179, x=180, y=180))
    g.append(vectorio.Circle(pixel_shader=inner, radius=170, x=180, y=180))
    for i, c in enumerate(COLORS[:4]):
        pal = displayio.Palette(1)
        pal[0] = c
        g.append(vectorio.Rectangle(pixel_shader=pal, width=60, height=120, x=60 + i * 60, y=60))
    if label:
        g.append(label.Label(terminalio.FONT, text=name, color=0xFFFF00, scale=3,
                             anchor_point=(0.5, 0.5), anchored_position=(180, 250)))
    return g


names = list(panels.PANELS)
index = 0
while True:
    name = names[index]
    print("Panel table:", name)
    display = panels.init_display(panels.PANELS[name])
    display.root_group = scene(name)
    while button.value:  # wait for press
        time.sleep(0.02)
    while not button.value:  # wait for release
        time.sleep(0.02)
    index = (index + 1) % len(names)
