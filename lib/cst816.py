# SPDX-License-Identifier: MIT
"""
Minimal CircuitPython driver for the Hynitron CST816S/T/D capacitive touch
controller used on the Guition JC3636W518C.

    import board
    from cst816 import CST816

    touch = CST816(board.I2C(), reset_pin=board.TOUCH_RST,
                   rotation=board.DISPLAY.rotation)
    while True:
        p = touch.touch
        if p:
            print(p)  # (x, y)

Coordinates are in display pixels (0..359) and follow ``rotation`` so they
line up with what displayio draws when ``board.DISPLAY.rotation`` is set to
the same value.
"""

import time

try:
    import digitalio
except ImportError:  # pragma: no cover
    digitalio = None

_ADDR = 0x15

_REG_GESTURE = 0x01
_REG_FINGERS = 0x02
_REG_CHIP_ID = 0xA7
_REG_FW_VERSION = 0xA9
_REG_DIS_AUTO_SLEEP = 0xFE

GESTURE_NONE = 0x00
GESTURE_SWIPE_UP = 0x01
GESTURE_SWIPE_DOWN = 0x02
GESTURE_SWIPE_LEFT = 0x03
GESTURE_SWIPE_RIGHT = 0x04
GESTURE_SINGLE_CLICK = 0x05
GESTURE_DOUBLE_CLICK = 0x0B
GESTURE_LONG_PRESS = 0x0C

CHIP_NAMES = {0xB4: "CST816S", 0xB5: "CST816T", 0xB6: "CST816D", 0xB7: "CST820"}


class CST816:
    """CST816 touch controller.

    :param i2c: an initialized ``busio.I2C`` (``board.I2C()`` on this board)
    :param reset_pin: optional ``board.TOUCH_RST``; pulsed low at start-up
    :param int width: panel width in pixels
    :param int height: panel height in pixels
    :param int rotation: 0, 90, 180 or 270, same meaning as displayio
    :param bool keep_awake: stop the chip from auto-sleeping. While asleep it
        does not answer on I2C until touched.
    """

    def __init__(self, i2c, *, reset_pin=None, address=_ADDR, width=360,
                 height=360, rotation=0, keep_awake=True):
        self._i2c = i2c
        self._addr = address
        self.width = width
        self.height = height
        self.rotation = rotation
        self._buf = bytearray(6)
        self._rst = None
        if reset_pin is not None and digitalio is not None:
            self._rst = digitalio.DigitalInOut(reset_pin)
            self._rst.switch_to_output(value=True)
            self.reset()
        if keep_awake:
            try:
                self._write(_REG_DIS_AUTO_SLEEP, 0x01)
            except OSError:
                pass

    def reset(self):
        """Hardware reset through TOUCH_RST (needs ``reset_pin``)."""
        if self._rst is None:
            return
        self._rst.value = False
        time.sleep(0.01)
        self._rst.value = True
        time.sleep(0.06)

    def _lock(self):
        while not self._i2c.try_lock():
            pass

    def _write(self, reg, value):
        self._lock()
        try:
            self._i2c.writeto(self._addr, bytes((reg, value)))
        finally:
            self._i2c.unlock()

    def _read(self, reg, buf):
        self._lock()
        try:
            self._i2c.writeto_then_readfrom(self._addr, bytes((reg,)), buf)
        finally:
            self._i2c.unlock()
        return buf

    @property
    def chip_id(self):
        """Chip ID byte (0xB4 = CST816S, 0xB5 = CST816T, 0xB6 = CST816D)."""
        return self._read(_REG_CHIP_ID, bytearray(1))[0]

    @property
    def chip_name(self):
        cid = self.chip_id
        return CHIP_NAMES.get(cid, "unknown (0x%02X)" % cid)

    @property
    def firmware_version(self):
        return self._read(_REG_FW_VERSION, bytearray(1))[0]

    def _raw(self):
        """(gesture, fingers, x, y) straight from the chip, or None on I2C error."""
        try:
            b = self._read(_REG_GESTURE, self._buf)
        except OSError:
            return None  # chip asleep / busy
        x = ((b[2] & 0x0F) << 8) | b[3]
        y = ((b[4] & 0x0F) << 8) | b[5]
        return b[0], b[1] & 0x0F, x, y

    def _rotate(self, x, y):
        w, h = self.width, self.height
        r = self.rotation % 360
        if r == 90:
            return y, w - 1 - x
        if r == 180:
            return w - 1 - x, h - 1 - y
        if r == 270:
            return h - 1 - y, x
        return x, y

    @property
    def touched(self):
        """True while a finger is on the screen."""
        raw = self._raw()
        return bool(raw and raw[1])

    @property
    def touch(self):
        """``(x, y)`` of the current touch in display coordinates, or None."""
        raw = self._raw()
        if not raw or not raw[1]:
            return None
        return self._rotate(raw[2], raw[3])

    @property
    def gesture(self):
        """Last gesture code reported by the chip (see GESTURE_* constants)."""
        raw = self._raw()
        return raw[0] if raw else GESTURE_NONE
