# SPDX-License-Identifier: MIT
# Print touch coordinates and gestures to the serial console.
import time
import board
import cst816

touch = cst816.CST816(board.I2C(), reset_pin=board.TOUCH_RST)
print("Chip:", touch.chip_name, "FW:", touch.firmware_version)

names = {
    cst816.GESTURE_SWIPE_UP: "swipe up",
    cst816.GESTURE_SWIPE_DOWN: "swipe down",
    cst816.GESTURE_SWIPE_LEFT: "swipe left",
    cst816.GESTURE_SWIPE_RIGHT: "swipe right",
    cst816.GESTURE_SINGLE_CLICK: "click",
    cst816.GESTURE_DOUBLE_CLICK: "double click",
    cst816.GESTURE_LONG_PRESS: "long press",
}
last = None
while True:
    p = touch.touch
    g = touch.gesture
    if p and p != last:
        print("touch", p)
    if g in names:
        print("gesture:", names[g])
    last = p
    time.sleep(0.02)
