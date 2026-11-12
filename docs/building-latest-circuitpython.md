# Building against the latest CircuitPython

The firmware is pinned to a CircuitPython release (`CP_VERSION`, currently
`11.0.0-alpha.2`). This page covers moving it to a newer release, or to
`main`, and what to check along the way.

History: 10.3.2 → 11.0.0-alpha.2 needed no change to the board code (the
`qspibus` and `busdisplay` APIs are unchanged). 11.x adds `audioi2sin`, and
moves to ESP-IDF 6.1.

## 1. Find the version

```sh
# newest release tags
git ls-remote --tags --refs https://github.com/adafruit/circuitpython \
  | sed 's|.*refs/tags/||' | sort -V | tail -10
```

Pick a stable tag (e.g. `10.4.0`), a pre-release (`10.4.0-beta.1`), or `main`
for the latest development code.

## 2. Check the APIs the board uses

The board code depends on two internal C APIs. They are not stable between
releases.

| What | File in CircuitPython | Used in |
|------|----------------------|---------|
| `common_hal_qspibus_qspibus_construct(...)` | `shared-bindings/qspibus/QSPIBus.h` | `boards/guition_jc3636w518c/board.c` |
| `common_hal_busdisplay_busdisplay_construct(...)` | `shared-bindings/busdisplay/BusDisplay.h` | same |
| `allocate_display_bus_or_raise()->qspi_bus` | `shared-module/displayio/__init__.h` | same |
| `CIRCUITPY_QSPIBUS` build flag | `ports/espressif/mpconfigport.mk` | `mpconfigboard.mk` |

The quickest check is to compare against the in-tree board that uses the
same path, and see what changed in it since the version we build against:

```sh
git clone --depth 200 https://github.com/adafruit/circuitpython cp-latest
cd cp-latest
git log --oneline -- ports/espressif/boards/waveshare_esp32_s3_amoled_241 \
                     shared-bindings/qspibus shared-bindings/busdisplay/BusDisplay.h
sed -n '/void common_hal_qspibus_qspibus_construct/,/);/p' shared-bindings/qspibus/QSPIBus.h
sed -n '/void common_hal_busdisplay_busdisplay_construct/,/);/p' shared-bindings/busdisplay/BusDisplay.h
```

If a signature changed, update the call in `board.c` the same way the
Waveshare board's `board.c` was updated.

## 3. Build

```sh
CP_VERSION=10.4.0 ./build.sh          # a release
CP_VERSION=main ./build.sh            # development head
```

`build.sh` re-uses `build/circuitpython` and checks out `CP_VERSION` in it.
It brings ESP-IDF's nested submodules to the matching commits, and removes a
board's build directory if it was configured by another version.
It then fetches that version's submodules, including its ESP-IDF, and runs
ESP-IDF's `install.sh` for any new toolchain versions. Output goes to
`dist/<board>-<version>.bin`; a branch build gets the commit added to the
version, e.g. `main-1a2b3c4`.

To start from a completely clean tree:

```sh
rm -rf build/circuitpython
```

Time and space: the first build of a new version downloads ESP-IDF and its
toolchain (several GB under `~/.espressif` and `build/`). CMake's configure
step takes a few minutes, and compiling another 5–10 minutes per board on 4
cores.

## 4. Known build problems

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Failed to download ... espidf.constraints.v6.0.txt` | `dl.espressif.com` blocked | `build.sh` falls back automatically. By hand: `python3 esp-idf/tools/idf_tools.py install-python-env --no-constraints` and `export IDF_PYTHON_CHECK_CONSTRAINTS=no` |
| `ModuleNotFoundError: minify_html` or `jsmin` during `make` | build dependencies installed into the system Python, not ESP-IDF's | install `requirements-dev.txt` after `source esp-idf/export.sh`, as `build.sh` does |
| `Failed building wheel for cpp-coveralls` | not needed for firmware builds | `build.sh` leaves it out |
| `export.sh` complains about missing tools after changing version | new ESP-IDF needs new tool versions | rerun `./esp-idf/install.sh esp32s3` (`build.sh` does this every run) |
| CMake: `Include directory .../mbedtls/tf-psa-crypto/extras is not a directory` | the re-used checkout changed version, but ESP-IDF's nested submodules stayed at the old commits | `git -C ports/espressif/esp-idf submodule update --recursive --depth 1` (`build.sh` does this) |
| pip retries `dl.espressif.com/pypi` on every package | ESP-IDF 6.1 adds Espressif's PyPI mirror as an extra index; blocked here | harmless but slow; packages still come from pypi.org |
| linker warning `LOAD segment with RWX permissions` | normal for ESP32 builds | ignore |

## 5. Check the result

Before flashing:

```sh
strings dist/guition_jc3636w518c_v2-*.bin | grep "Adafruit CircuitPython"
# -> Adafruit CircuitPython <version> on <date>; Guition JC3636W518C V2 with ESP32S3
strings dist/guition_jc3636w518c_v2-*.bin | grep -x -E "MIC_(CLK|SCK)"
# -> MIC_CLK for _v2, MIC_SCK for the original build
```

On the board (flash at `0x0`, see the top-level README):

1. The CircuitPython console appears on the round screen.
2. The `CIRCUITPY` drive and the serial REPL appear on the computer.
3. `examples/panel_test.py` shows clean color bars.
4. `examples/touch_test.py` prints coordinates that match where you touch.
5. Add the new version to the status table in [usage.md](usage.md) once it
   has been tested.

## 6. Make it the default

When a new version works:

1. Change the default `CP_VERSION` in `build.sh`.
2. Change `CP_VERSION` in `.github/workflows/build.yml`. The ESP-IDF cache
   key includes it, so CI downloads the new toolchain once.
3. Update the version mentioned in `README.md` and `docs/development.md`.
4. Optionally tag a release (`git tag v0.2.0 && git push origin v0.2.0`). CI
   then attaches the binaries to a GitHub Release.

## Upstream

`qspibus` first appeared in CircuitPython 10.2.0, so older releases cannot
build this board. Once this board is in CircuitPython itself (that needs a
dedicated USB PID, see [development.md](development.md#board-definition-notes)),
it will be built with every release and this page will no longer be needed.