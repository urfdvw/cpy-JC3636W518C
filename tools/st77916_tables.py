#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Collect, compare and convert the ST77916 init tables for the JC3636W518C.

Sources (the first two must be downloaded separately):
  --xiaozhi   xiaozhi-esp32 main/boards/taiji-pi-s3/taiji_pi_s3.cc
              (git clone https://github.com/78/xiaozhi-esp32)
  --esp-lib   ESP32_Display_Panel v0.1.4 src/lcd/base/esp_lcd_st77916.c
              (git clone --branch v0.1.4 https://github.com/esp-arduino-libs/ESP32_Display_Panel)
  vendor files under docs/vendor/ (found automatically)

Usage:
  tools/st77916_tables.py --xiaozhi X --esp-lib Y compare [A,B ...]
  tools/st77916_tables.py --xiaozhi X --esp-lib Y python   > lib/jc3636w518_panels.py
  tools/st77916_tables.py --xiaozhi X --esp-lib Y c V1|V2  # body for board.c

"compare" without arguments lists the tables and which ones are identical;
with "A,B" pairs it prints a diff. Delays and the INVON/SLPOUT/DISPON tail
are ignored when comparing.
"""

import argparse
import difflib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
VENDOR = ROOT / "docs" / "vendor"

_C_ENTRY = re.compile(
    r"^\s*(//)?\s*\{(0x[0-9A-Fa-f]{2}),\s*\(uint8_t\s*\[\]\)\{([^}]*)\},\s*(\d+),\s*(\d+)\}",
    re.M,
)
NO_DATA = (0x21, 0x11, 0x29)
# Sent after every vendor table: COLMOD 16 bit, MADCTL 0, INVON, SLPOUT, DISPON.
TAIL = [(0x3A, (0x55,), 0), (0x36, (0x00,), 0), (0x21, (), 0), (0x11, (), 120), (0x29, (), 20)]


def c_table(text):
    """Parse esp_lcd style {cmd, (uint8_t[]){...}, len, delay} entries (skips // lines)."""
    out = []
    for m in _C_ENTRY.finditer(text):
        if m[1]:
            continue
        n = int(m[4])
        data = tuple(int(x, 16) for x in m[3].split(",") if x.strip())[:n]
        out.append((int(m[2], 16), data, int(m[5])))
    return out


def send_set_table(text):
    """Parse the vendor 'send 0xNN / set 0xNN / delay_ms N' format."""
    out = []
    for line in text.splitlines():
        p = line.split()
        if not p:
            continue
        if p[0] == "send":
            out.append([int(p[1], 16), [], 0])
        elif p[0] == "set":
            out[-1][1].append(int(p[1], 16))
        elif p[0] == "delay_ms":
            out[-1][2] = int(p[1])
    return [(c, tuple(d), dl) for c, d, dl in out]


def between(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i)]


def load(args):
    tables = {}
    if args.xiaozhi:
        body = between(pathlib.Path(args.xiaozhi).read_text(), "lcd_init_cmds[] = {", "};")
        v1, v2 = body.split("#else")
        tables["V1"] = c_table(v1)
        tables["V2"] = c_table(v2)
    if args.esp_lib:
        src = pathlib.Path(args.esp_lib).read_text()
        tables["ESP_DEFAULT"] = c_table(between(src, "vendor_specific_init_default[]", "};"))
    demo = VENDOR / "demo" / "ST77916_LVGL_DEMO" / "scr_st77916.h"
    tables["VENDOR_DEMO"] = c_table(between(demo.read_text(), "lcd_init_cmd[]", "};"))
    tables["VENDOR_INIT_CODE"] = c_table((VENDOR / "display-init" / "Initialization code.txt").read_text())
    boe = next((VENDOR / "display-init").glob("ST77916_BOE*.txt"))
    tables["BOE"] = send_set_table(boe.read_text())
    return tables


def normalized(table):
    return [(c, () if c in NO_DATA else d) for c, d, _ in table]


def pack(table):
    """displayio init sequence: cmd, len | 0x80 if delay, data..., delay_ms."""
    while table and table[-1][0] in NO_DATA:
        table = table[:-1]
    out = bytearray()
    for c, d, dl in list(table) + TAIL:
        if c in NO_DATA:
            d = ()
        out += bytes((c, len(d) | (0x80 if dl else 0))) + bytes(d)
        if dl:
            out.append(min(dl, 255))
    return bytes(out)


def cmd_compare(tables, pairs):
    for name, t in tables.items():
        print(f"{name:18s} {len(t):4d} commands, starts {t[0][0]:02X} {bytes(t[0][1]).hex()}")
    names = list(tables)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if normalized(tables[a]) == normalized(tables[b]):
                print(f"identical: {a} == {b}")
    for pair in pairs:
        a, b = pair.split(",")
        fmt = lambda t: [f"{c:02X} " + " ".join(f"{x:02X}" for x in d) for c, d in normalized(t)]
        print(f"\n--- {a}\n+++ {b}")
        for line in difflib.unified_diff(fmt(tables[a]), fmt(tables[b]), lineterm="", n=0):
            if not line.startswith(("---", "+++")):
                print(line)


PY_TABLES = [
    ("V1", "V1", "Original glass (batch <= 2528). Same as the vendor demo's scr_st77916.h table; built into the guition_jc3636w518c firmware."),
    ("V2", "V2", "New glass (batch > 2528), from xiaozhi-esp32's taiji-pi-s3 board; built into the guition_jc3636w518c_v2 firmware."),
    ("ESP_DEFAULT", "ESP_DEFAULT", "Espressif esp_lcd_st77916 default table. The vendor Arduino demo actually runs this one (its own table is commented out)."),
    ("BOE", "BOE", "Vendor file 'ST77916_BOE 1.8'' 360x360 initial code_V1.7_20231208'."),
]


def cmd_python(tables):
    print((ROOT / "tools" / "panels_header.py.txt").read_text(), end="")
    for name, key, doc in PY_TABLES:
        h = pack(tables[key]).hex()
        print(f"# {doc}\n{name} = (")
        for i in range(0, len(h), 64):
            print('    b"' + "".join("\\x" + h[j:j + 2] for j in range(i, min(i + 64, len(h)), 2)) + '"')
        print(")\n")
    print("PANELS = {" + ", ".join(f'"{n}": {n}' for n, _, _ in PY_TABLES) + "}")
    print((ROOT / "tools" / "panels_footer.py.txt").read_text(), end="")


def cmd_c(tables, name):
    t = list(tables[name])
    while t and t[-1][0] in NO_DATA:
        t.pop()
    for c, d, dl in t:
        bs = [c, len(d) | (0x80 if dl else 0), *d] + ([min(dl, 255)] if dl else [])
        print("    " + ", ".join(f"0x{b:02X}" for b in bs) + ",")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xiaozhi")
    ap.add_argument("--esp-lib")
    ap.add_argument("command", choices=["compare", "python", "c"])
    ap.add_argument("rest", nargs="*")
    args = ap.parse_args()
    tables = load(args)
    if args.command == "compare":
        cmd_compare(tables, args.rest)
    elif args.command == "python":
        cmd_python(tables)
    else:
        cmd_c(tables, args.rest[0])


if __name__ == "__main__":
    sys.exit(main())
