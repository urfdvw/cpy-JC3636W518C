# BLE keyboard host — debugging notes

Board: Guition JC3636W518C V2 (ESP32-S3). Tested on CircuitPython 10.3.2, then 11.0.0-alpha.2.
Target keyboard: Clicks "Power Keyboard" (advertises as `Power Keyboard-B49E-1`,
address d8:c3:e4:62:b4:9e, random static)

NOTE: upgrading to 11.0.0-alpha.2 wiped CIRCUITPY; code.py edits and this file were restored.

## Findings in code.py

1. **"Unknown system firmware error: 21" (fixed)**
   - On the ESP32 port, the iterator from `adapter.start_scan(timeout=5)` ends after
     ~0.25 s (as soon as its buffer is empty), not after `timeout`. Once exhausted,
     the same ScanResults object yields nothing more.
   - Restarting the scan in a tight loop makes NimBLE fail with error 21 after ~10–20 s.
   - Fix: sleep 0.3 s between scans, catch `_bleio.BluetoothError`, always
     `stop_scan()` in `finally`.
2. **ScanEntry flags are unreliable**: with active scan almost every entry reports
   `scan_response=True`. The keyboard name may only be in the scan response, so the
   name filter does not require `connectable`.
3. **Keyboard selection**: `TARGET_NAME_PREFIX = "Power Keyboard"`.
4. **Phone interference**: while the phone's Bluetooth was on, the board could not see
   the keyboard at all. With phone BT off it is found within seconds.
5. code.py checks `conn.connected` after connect() (10.3.x returns a dead object on timeout).

## Connection failure — diagnostics

On 10.3.2 (keyboard in pairing mode, touching the board, phone BT off):
- Keyboard advertises every ~45 ms, RSSI -66..-80 dBm (low TX power, see FCC below).
- connect() with 4/5/10/30 s timeouts, passive or active pre-scan, display released:
  ALL return connected=False after exactly the timeout.
- After most attempts the keyboard goes silent ~5–10 s, then advertises again ->
  it probably entered a link-layer connection the board never reported.
- Right after the timeout: adapter.connected=False, adapter.connections=().
- Other nearby peripherals connect, but slowly (2–5 s; normally <100 ms).
- No Python knobs: connection params hard-coded in firmware (scan 100/100 ms,
  interval 15–300 ms, latency 0, supervision 4 s); no disconnect reason exposed.

Source analysis (ports/espressif/common-hal/_bleio/Adapter.c, 10.3.2 vs main):
- 10.3.2 connect() only succeeds when the reply to the board's own ATT MTU exchange
  arrives; if ble_gattc_exchange_mtu() fails (peer already started MTU exchange) it
  waits to a software deadline and returns a bogus Connection for an empty slot.
- 10.3.2 also: no ble_gap_conn_cancel() on Ctrl-C; status reset after connect starts;
  sm_sc=0 (no LE Secure Connections).
- Fixed on main 2026-10-11 ("fix connect() timeout and Ctrl-C handling" #11559,
  "get MTU when the peer already exchanged it"), SC pairing #11340. First release with
  all of these: 11.0.0-alpha.2 (2026-10-21).

On 11.0.0-alpha.2 (2026-11-12):
- connect(addr, timeout=10) to the keyboard **never returns** (waited >70 s, had to Ctrl-C).
  11.0 has no software deadline. Its wait ends only when (a) BLE_GAP_EVENT_CONNECT
  arrives with an error/timeout status, or (b) after a successful CONNECT event, the
  board's ATT MTU exchange gets a reply (or the peer already exchanged MTU).
  So the hang is EITHER no CONNECT event at all, OR the link came up and the MTU
  reply never arrives (keyboard ignores it, or the keyboard disconnects and
  _mtu_reply ignores the now-invalid handle). Cannot tell which without
  CIRCUITPY_VERBOSE_BLE=1 logs.
- After Ctrl-C: adapter.connected=False, connections=().
- Same hang happened connecting to one other nearby device; another device connected
  (5.6 s, MTU 253). So connect() hanging is not keyboard-only.
- code.py therefore sits at "Connecting:" forever on 11.0.0-alpha.2.
- More logging needs a firmware build with CIRCUITPY_VERBOSE_BLE=1 (prints GAP events).

## Clicks Power Keyboard — hardware info

- Radio: BLE 5.4 only (no Classic). Chipset not published.
- Up to 9 pairing slots (April 2026 update). Name suffix `-1` appears to be the slot.
- Pairing mode for a new device: hold `123` + press `0`. Power + 1–9 switches slot;
  `sym` + `0` clears current slot. LED: pulsing blue = pairing, solid = paired.
- Pairing with Master's phone needed no code (phone only asked about contacts access)
  -> Just Works; passkey is NOT the cause. Our failure is before pairing anyway.
- Firmware: only V1.1.0 (2026-06-19) announced; no BT fixes/known issues published.
- 2300 mAh power bank, 5 W Qi/MagSafe/Qi2; 119.7 x 76.6 x 15.2 mm, 180 g.

FCC ID 2BVEP-CP1000 (model CP-1000), grants 2026-05-20, lab Aibo Standard Technology
(Shenzhen), report AB26040362FW01:
- BT 2402–2480 MHz, max conducted output 0.00177 W (~2.5 dBm) — low TX power.
- Second grant 0.114–0.149 MHz (likely the Qi coil; type not stated).
- Internal/external photos + manual confidential until 2026-11-16; block diagram,
  schematics, operational description confidential with no date.

Sources: clicks.tech/products/powerkeyboard, learn.clicks.tech, discover.clicks.tech,
cybernews.com review, fccid.io/2BVEP-CP1000, github.com/adafruit/circuitpython.

### 11.0.0-alpha.2 timeout test (2026-11-12) — narrows it down
- Control: connect() to a NON-EXISTENT address with timeout=1 -> raises
  "Failed to connect: timeout" after exactly 1.0 s. NimBLE's timeout path works.
- Keyboard with timeout=1 -> hangs (>20 s, Ctrl-C needed). So within 1 s NimBLE must have
  reported BLE_GAP_EVENT_CONNECT with status 0 (otherwise the 1 s timeout would fire),
  i.e. the controller sent CONNECT_IND and considers the link "created".
- Meanwhile the keyboard LED keeps pulsing (pairing) -> the keyboard never ends up in
  the connection. Most likely sequence: link created -> peripheral never syncs ->
  disconnect (probably HCI 0x3E "connection failed to be established") -> the pending
  MTU callback is dropped because the handle is already invalid -> 11.0 connect() waits
  forever. adapter.connected is False after Ctrl-C, consistent with this.
- So: (1) root problem = link establishment fails between this ESP32-S3 and the keyboard;
  (2) 11.0.0-alpha.2 has an extra bug: a disconnect during the MTU wait hangs connect().

### Source check (2026-11-12) — hang path VERIFIED in code
Read at the exact pinned versions: circuitpython tag 11.0.0-alpha.2 ->
adafruit/esp-idf 29d36039 -> espressif/esp-nimble 139cada0.
In this esp-nimble, a central connection does NOT report BLE_GAP_EVENT_CONNECT on the
HCI "LE Connection Complete". Sequence (ble_gap.c):
  1. LE Connection Complete (status 0): conn is created, conn->bhc_cb = _connect_event,
     and ble_gap_master_reset_state() — the connect() timeout timer is now gone.
  2. Host sends LE Read Remote Features -> on completion sends Read Remote Version ->
     only when THAT completes: ble_gap_event_connect_call(handle, 0) = CONNECT event.
  3. If the link fails with 0x3E (connection failed to be established), the feature/
     version completion handlers just return ("Reconnection will automatically happen").
  4. ble_hs_hci_evt.c disconnect handler: central + reason 0x3E ->
     BT_NIMBLE_ENABLE_CONN_REATTEMPT (default y on ESP32-S3, not overridden by
     CircuitPython, max 3) re-runs ble_gap_connect(); posts BLE_GAP_EVENT_REATTEMPT_COUNT.
  5. After the last reattempt fails: BLE_GAP_EVENT_DISCONNECT goes to _connect_event.
- CircuitPython's _connect_event handles ONLY BLE_GAP_EVENT_CONNECT; REATTEMPT_COUNT and
  DISCONNECT fall into "default" and are ignored, and no MTU exchange was ever started.
  => _connection_status is never written => 11.0 connect() loops forever (10.3.2: hits
  its software deadline and returns a dead Connection).
- Matches all observations: timeout=1 hangs (timer cancelled at step 1), ghost address
  times out normally (never reaches step 1), keyboard LED keeps pulsing, keyboard goes
  quiet ~5–10 s after an attempt on 10.3.2 (up to 4 attempts x 0x3E), adapter.connected
  False afterwards, some other devices also hang / connect slowly.
- So the real radio-level failure is: board sends CONNECT_IND, keyboard never answers
  in the new connection (0x3E), repeated 4x. WHY the keyboard does not follow is still
  unknown. CircuitPython bug to report: _connect_event should treat DISCONNECT (and
  ideally REATTEMPT_COUNT) during connect() as failure.

### Patched firmware result (2026-11-13) — CORRECTS the 0x3E guess
Firmware: 11.0.0-alpha.2 built from urfdvw/cpy-JC3636W518C with _connect_event
handling DISCONNECT during connect + CIRCUITPY_VERBOSE_BLE. code.py output per attempt:
  Connect event: 1            (1 = BLE_GAP_EVENT_DISCONNECT)
  Disconnected while connecting: reason 0x0213
  Failed: Unknown BLE error at common-hal/_bleio/Adapter.c:537: 0x0213
- connect() no longer hangs -> the hang root cause (ignored DISCONNECT) is CONFIRMED.
- 0x0213 = BLE_HS_ERR_HCI_BASE (0x200) + HCI 0x13 "Remote User Terminated Connection".
  So the link WAS established and the KEYBOARD actively terminated it, before NimBLE
  posted the CONNECT event (i.e. during the Read Remote Features/Version step).
  It is NOT 0x3E, and no REATTEMPT_COUNT events appeared.
- No other events (MTU, ENC_CHANGE, etc.) were seen before the disconnect.
- Open question: why does the keyboard drop the board within the first exchanges?
  Next data needed: time from connect() to the disconnect.
