# SPDX-License-Identifier: MIT
# Guition JC3636W518C demo: color rings, a label, and a dot that follows touch.
# Copy lib/cst816.py to CIRCUITPY/lib/ and this file to CIRCUITPY/code.py.
import board
import displayio
import terminalio
import vectorio

from cst816 import CST816

try:
    from adafruit_display_text import label
except ImportError:
    label = None

display = board.DISPLAY
display.rotation = 0          # 0/90/180/270, touch follows it below
display.brightness = 0.8      # PWM backlight on GPIO15

W, H = display.width, display.height
CX, CY = W // 2, H // 2

root = displayio.Group()
display.root_group = root

colors = (0xFF0000, 0xFF8000, 0xFFFF00, 0x00FF00, 0x0080FF, 0x8000FF)
for i, c in enumerate(colors):
    pal = displayio.Palette(1)
    pal[0] = c
    root.append(vectorio.Circle(pixel_shader=pal, radius=CX - i * 25, x=CX, y=CY))

bg = displayio.Palette(1)
bg[0] = 0x000000
root.append(vectorio.Circle(pixel_shader=bg, radius=CX - len(colors) * 25, x=CX, y=CY))

if label:
    title = label.Label(terminalio.FONT, text="JC3636W518C", color=0xFFFFFF,
                        scale=2, anchor_point=(0.5, 0.5), anchored_position=(CX, CY))
    root.append(title)

dot_pal = displayio.Palette(1)
dot_pal[0] = 0xFFFFFF
dot = vectorio.Circle(pixel_shader=dot_pal, radius=12, x=-50, y=-50)
root.append(dot)

touch = CST816(board.I2C(), reset_pin=board.TOUCH_RST, rotation=display.rotation)
print("Touch controller:", touch.chip_name)

while True:
    p = touch.touch
    if p:
        dot.x, dot.y = p
