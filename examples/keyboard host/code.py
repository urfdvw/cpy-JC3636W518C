# SPDX-License-Identifier: MIT
"""
BLE keyboard host (HID over GATT central) for the Guition JC3636W518C.

Tested on a batch-2628 board (V2 build) with firmware 11.0.0-alpha.3-g6465d03
(CircuitPython main + adafruit/circuitpython#11859) and a Clicks "Power Keyboard".

What it does
  * Scans for a BLE keyboard whose name starts with TARGET_NAME_PREFIX,
    connects, pairs and bonds, then reconnects to it after a disconnect.
  * Subscribes to its key reports (boot protocol when supported).
  * Shows an on-screen terminal and runs a Python prompt (>>> / ...) that you
    type on the keyboard. Output also goes to the serial console.

Usage
  1. Copy this folder's contents (code.py, lib/, ...) to the root of CIRCUITPY.
  2. Set TARGET_NAME_PREFIX below to the start of your keyboard's name.
  3. Put the keyboard into pairing mode. Turn off Bluetooth on phones paired
     with it while the board connects.

Notes
  * BLE keyboards only. ESP32-S3 has no Classic Bluetooth.
  * CircuitPython pairs as "Just Works" (no passkey). Keyboards that insist
    on typing a passkey will not pair.
  * Needs firmware with the _bleio connect() fix (#11859): on stock
    11.0.0-alpha.2, connect() to this keyboard never returned.
  * adafruit_ble's HIDService has no central (host) side, so this uses the
    low-level _bleio module directly.
  * Run ``_bleio.adapter.erase_bonding()`` in the REPL to forget bonded keyboards.
  * Debugging history: MEMORY.md in this folder.
"""

import time

import _bleio
import board
import displayio
import terminalio

try:
    from adafruit_display_text import label
except ImportError:
    label = None

# ---------------------------------------------------------------------------
# GATT UUIDs (Bluetooth SIG assigned numbers)
# ---------------------------------------------------------------------------
UUID_HID_SERVICE = _bleio.UUID(0x1812)
UUID_PROTOCOL_MODE = _bleio.UUID(0x2A4E)
UUID_REPORT = _bleio.UUID(0x2A4D)
UUID_BOOT_KBD_INPUT = _bleio.UUID(0x2A22)
UUID_REPORT_REFERENCE = _bleio.UUID(0x2908)

APPEARANCE_KEYBOARD = 0x03C1
TARGET_NAME_PREFIX = "Power Keyboard"  # only connect to keyboards named like this
REPORT_TYPE_INPUT = 1

# ---------------------------------------------------------------------------
# HID usage -> character, US layout: (normal, shifted)
# ---------------------------------------------------------------------------
KEYMAP = {}
for i, (a, b) in enumerate(zip("abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ")):
    KEYMAP[0x04 + i] = (a, b)
for i, (a, b) in enumerate(zip("1234567890", "!@#$%^&*()")):
    KEYMAP[0x1E + i] = (a, b)
KEYMAP.update({
    0x28: ("\n", "\n"),   # Enter
    0x2B: ("\t", "\t"),   # Tab
    0x2C: (" ", " "),     # Space
    0x2D: ("-", "_"), 0x2E: ("=", "+"), 0x2F: ("[", "{"), 0x30: ("]", "}"),
    0x31: ("\\", "|"), 0x33: (";", ":"), 0x34: ("'", '"'), 0x35: ("`", "~"),
    0x36: (",", "<"), 0x37: (".", ">"), 0x38: ("/", "?"),
    0x58: ("\n", "\n"),   # Keypad Enter
})
KEY_BACKSPACE = 0x2A
KEY_CAPS_LOCK = 0x39
MOD_SHIFT = 0x02 | 0x20  # left / right shift bits

# ---------------------------------------------------------------------------
# Screen
# ---------------------------------------------------------------------------
display = board.DISPLAY
display.brightness = 0.8
# Our own on-screen terminal. Only text written through out() shows here, so the
# firmware's BLE debug prints (CIRCUITPY_VERBOSE_BLE) stay on the serial console.
_font = terminalio.FONT
_fw, _fh = _font.get_bounding_box()[:2]
TERM_SCALE = 2
_side = int(display.width * 0.72)          # square that fits inside the round screen
TERM_COLS = _side // (_fw * TERM_SCALE)
TERM_ROWS = _side // (_fh * TERM_SCALE)
_pal = displayio.Palette(2)
_pal[0] = 0x000000
_pal[1] = 0xFFFFFF
_grid = displayio.TileGrid(_font.bitmap, pixel_shader=_pal, width=TERM_COLS,
                           height=TERM_ROWS, tile_width=_fw, tile_height=_fh,
                           default_tile=_font.get_glyph(32).tile_index)
term = terminalio.Terminal(_grid, _font)
_screen = displayio.Group(scale=TERM_SCALE,
                          x=(display.width - TERM_COLS * _fw * TERM_SCALE) // 2,
                          y=(display.height - TERM_ROWS * _fh * TERM_SCALE) // 2)
_screen.append(_grid)
display.root_group = _screen
status = typed = None


def out(s):
    """Write text to the on-screen terminal and the serial console."""
    if not s:
        return
    term.write(s.replace("\r\n", "\n").replace("\n", "\r\n").encode())
    print(s, end="")


class _Out:
    def write(self, s):
        out(s if isinstance(s, str) else str(s, "utf-8"))
        return len(s)


OUT = _Out()


def kprint(*args, sep=" ", end="\n"):
    out(sep.join(str(x) for x in args) + end)

def show_status(msg):
    out("[status] " + msg + "\n")


# ---------------------------------------------------------------------------
# Keyboard REPL (an emulated >>> prompt; the real REPL cannot take BLE input)
# ---------------------------------------------------------------------------
import traceback

repl_ns = {"__name__": "__kbd__", "print": kprint}
repl_line = ""      # line being typed
repl_block = []     # lines of an unfinished multi-line block


def repl_prompt():
    out("... " if repl_block else ">>> ")


def repl_run(src):
    try:
        try:
            code = compile(src, "<kbd>", "eval")
        except SyntaxError:
            exec(compile(src, "<kbd>", "exec"), repl_ns)
        else:
            result = eval(code, repl_ns)
            if result is not None:
                out(repr(result) + "\n")
                repl_ns["_"] = result
    except Exception as e:  # show errors like the real REPL, keep running
        traceback.print_exception(e, file=OUT)


def repl_enter():
    global repl_line
    line = repl_line
    repl_line = ""
    out("\n")
    if repl_block:
        if line.strip():
            repl_block.append(line)
        else:               # blank line ends the block
            src = "\n".join(repl_block)
            repl_block.clear()
            repl_run(src)
    elif line.rstrip().endswith(":"):
        repl_block.append(line)
    elif line.strip():
        repl_run(line)
    repl_prompt()


def type_char(ch):
    global repl_line
    if ch == "\n":
        repl_enter()
    elif ch == "\b":
        if repl_line:
            repl_line = repl_line[:-1]
            out("\b \b")
    elif ch == "\t":
        repl_line += "    "
        out("    ")
    else:
        repl_line += ch
        out(ch)



# ---------------------------------------------------------------------------
# Advertisement parsing
# ---------------------------------------------------------------------------
def parse_adv(data):
    """Yield (ad_type, payload) from raw advertisement bytes."""
    i = 0
    while i < len(data):
        length = data[i]
        if length == 0 or i + 1 + length > len(data):
            break
        yield data[i + 1], data[i + 2:i + 1 + length]
        i += 1 + length


def adv_info(entry):
    """Return (is_keyboard, name) for a ScanEntry."""
    is_kbd = False
    name = None
    for ad_type, payload in parse_adv(entry.advertisement_bytes):
        if ad_type in (0x02, 0x03):  # 16-bit service UUID list
            for j in range(0, len(payload) - 1, 2):
                if payload[j] | (payload[j + 1] << 8) == 0x1812:
                    is_kbd = True
        elif ad_type == 0x19 and len(payload) >= 2:  # Appearance
            if payload[0] | (payload[1] << 8) == APPEARANCE_KEYBOARD:
                is_kbd = True
        elif ad_type in (0x08, 0x09):  # short / complete local name
            try:
                name = str(payload, "utf-8")
            except Exception:
                pass
    return is_kbd, name


def find_keyboard(known_address=None):
    """Scan until a connectable BLE keyboard (or the bonded one) shows up."""
    adapter = _bleio.adapter
    while True:
        # On the ESP32 port the scan iterator ends as soon as its buffer is
        # empty (~0.25 s), not after `timeout`. Restarting the scan in a tight
        # loop eventually makes NimBLE fail ("system firmware error: 21"), so
        # throttle restarts and recover from scan errors instead of crashing.
        try:
            for entry in adapter.start_scan(timeout=5, active=True, minimum_rssi=-90):
                # The name often arrives in the scan response, so don't
                # filter on entry.connectable here.
                _, name = adv_info(entry)
                if (name and name.startswith(TARGET_NAME_PREFIX)) or (
                    known_address is not None and entry.address == known_address
                ):
                    return entry.address, name or str(entry.address)
        except _bleio.BluetoothError as e:
            print("[scan] error, retrying:", e)
            time.sleep(1)
        finally:
            try:
                adapter.stop_scan()
            except Exception:
                pass
        time.sleep(0.3)


# ---------------------------------------------------------------------------
# HID over GATT
# ---------------------------------------------------------------------------
def report_reference(characteristic):
    """(report_id, report_type) from the Report Reference descriptor, or None."""
    for d in characteristic.descriptors:
        if d.uuid == UUID_REPORT_REFERENCE:
            v = d.value
            if len(v) >= 2:
                return v[0], v[1]
    return None


def subscribe(connection):
    """Discover the HID service and return a list of PacketBuffers for key reports."""
    services = connection.discover_remote_services((UUID_HID_SERVICE,))
    if not services:
        raise RuntimeError("no HID service")
    chars = services[0].characteristics

    protocol_mode = None
    boot_input = None
    report_inputs = []
    for ch in chars:
        if ch.uuid == UUID_PROTOCOL_MODE:
            protocol_mode = ch
        elif ch.uuid == UUID_BOOT_KBD_INPUT:
            boot_input = ch
        elif ch.uuid == UUID_REPORT and ch.properties & _bleio.Characteristic.NOTIFY:
            ref = report_reference(ch)
            if ref is None or ref[1] == REPORT_TYPE_INPUT:
                report_inputs.append(ch)

    # Boot protocol has a fixed 8-byte layout: [modifiers, 0, key1..key6].
    if boot_input is not None and protocol_mode is not None:
        try:
            protocol_mode.value = b"\x00"  # 0 = Boot Protocol
            print("Using boot protocol")
            return [_bleio.PacketBuffer(boot_input, buffer_size=8, max_packet_size=64)]
        except Exception as e:  # some keyboards refuse; fall back to report mode
            print("Boot protocol not accepted:", e)

    # Report protocol: subscribe to every input report, keyboard reports are
    # picked out by their 8-byte length in handle_report().
    print("Using report protocol,", len(report_inputs), "input reports")
    return [_bleio.PacketBuffer(ch, buffer_size=8, max_packet_size=64)
            for ch in report_inputs]


pressed = set()
caps_lock = False


def handle_report(data):
    """Turn an 8-byte keyboard report into typed characters (new key-downs only)."""
    global pressed, caps_lock
    if len(data) != 8:
        return  # not a keyboard report (consumer keys, mouse, ...)
    modifiers = data[0]
    keys = set(k for k in data[2:8] if k > 3)  # 0 = none, 1-3 = error codes
    shift = bool(modifiers & MOD_SHIFT)
    for k in keys - pressed:
        if k == KEY_CAPS_LOCK:
            caps_lock = not caps_lock
        elif k == KEY_BACKSPACE:
            type_char("\b")
        elif k in KEYMAP:
            normal, shifted = KEYMAP[k]
            upper = shift ^ (caps_lock and normal.isalpha())
            type_char(shifted if upper else normal)
    pressed = keys


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
_bleio.adapter.enabled = True
known = None
buf = bytearray(64)

while True:
    show_status("Searching for keyboard...")
    address, name = find_keyboard(known)
    show_status("Connecting: " + name)
    conn = None
    try:
        conn = _bleio.adapter.connect(address, timeout=10)
        # On 10.3.x connect() can return after the timeout without a link.
        if conn is None or not conn.connected:
            raise RuntimeError("connect timed out")
        show_status("Pairing: " + name)
        conn.pair(bond=True)
        buffers = subscribe(conn)
        if not buffers:
            raise RuntimeError("no keyboard input reports")
    except Exception as e:
        show_status("Failed: " + str(e))
        if conn is not None and conn.connected:
            conn.disconnect()
        time.sleep(2)
        continue

    known = address
    show_status("Connected: " + name)
    repl_line = ""
    repl_block.clear()
    repl_prompt()
    pressed = set()
    while conn.connected:
        for pb in buffers:
            n = pb.readinto(buf)
            if n:
                handle_report(buf[:n])
        time.sleep(0.005)

    show_status("Disconnected")
    time.sleep(1)
