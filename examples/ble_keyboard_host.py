# SPDX-License-Identifier: MIT
"""
BLE keyboard host (HID over GATT central) for the Guition JC3636W518C.

The board scans for a Bluetooth LE keyboard, pairs with it, subscribes to its
key reports and shows what you type on the round screen (and on the serial
console).

Usage
  1. Copy this file to CIRCUITPY/code.py. For on-screen text also install
     adafruit_display_text (``circup install adafruit_display_text``);
     without it the text only goes to the serial console.
  2. Put the keyboard into pairing mode.
  3. The board pairs and bonds with the first keyboard it finds. After
     that it reconnects to the same keyboard when it wakes up.

Notes
  * BLE keyboards only. ESP32-S3 has no Classic Bluetooth, so older
    Bluetooth 2.x/3.x keyboards cannot connect.
  * CircuitPython pairs as "Just Works" (no passkey). Keyboards that insist
    on typing a passkey will not pair.
  * adafruit_ble's HIDService has no central (host) side, so this uses the
    low-level _bleio module directly.
  * Run ``_bleio.adapter.erase_bonding()`` in the REPL to forget bonded keyboards.
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
CX = display.width // 2
CY = display.height // 2
MAX_COLS = 20       # characters per line inside the round screen
MAX_LINES = 8

if label:
    root = displayio.Group()
    status = label.Label(terminalio.FONT, text="", color=0x00C0FF,
                         anchor_point=(0.5, 0.5), anchored_position=(CX, 50))
    typed = label.Label(terminalio.FONT, text="", color=0xFFFFFF, scale=2,
                        line_spacing=1.0, anchor_point=(0.5, 0.5),
                        anchored_position=(CX, CY + 10))
    root.append(status)
    root.append(typed)
    display.root_group = root
else:
    status = typed = None

text_buffer = ""


def show_status(msg):
    print("[status]", msg)
    if status:
        status.text = msg


def wrap(text):
    lines = []
    for para in text.split("\n"):
        while len(para) > MAX_COLS:
            lines.append(para[:MAX_COLS])
            para = para[MAX_COLS:]
        lines.append(para)
    return "\n".join(lines[-MAX_LINES:])


def type_char(ch):
    global text_buffer
    if ch == "\b":
        text_buffer = text_buffer[:-1]
        print("\b \b", end="")
    else:
        text_buffer += ch
        print(ch, end="")
    text_buffer = text_buffer[-400:]
    if typed:
        typed.text = wrap(text_buffer)


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
        for entry in adapter.start_scan(timeout=5, active=True, minimum_rssi=-90):
            if not entry.connectable:
                continue
            is_kbd, name = adv_info(entry)
            if is_kbd or (known_address is not None and entry.address == known_address):
                adapter.stop_scan()
                return entry.address, name or str(entry.address)
        adapter.stop_scan()


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
    pressed = set()
    while conn.connected:
        for pb in buffers:
            n = pb.readinto(buf)
            if n:
                handle_report(buf[:n])
        time.sleep(0.005)

    show_status("Disconnected")
    time.sleep(1)
