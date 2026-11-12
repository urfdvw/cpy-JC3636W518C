#!/usr/bin/env bash
# Build CircuitPython firmware for the Guition JC3636W518C.
#
#   ./build.sh                          # both variants, default CircuitPython version
#   ./build.sh guition_jc3636w518c_v2   # one variant
#   CP_VERSION=10.4.0 ./build.sh        # another release tag
#   CP_VERSION=main ./build.sh          # latest development code
#
# Environment:
#   CP_VERSION  CircuitPython tag or branch to build against (default below)
#   CP_DIR      where to keep the CircuitPython checkout (default ./build/circuitpython)
#   JOBS        parallel make jobs (default: nproc)
#
# See docs/building-latest-circuitpython.md.
set -euo pipefail

CP_VERSION="${CP_VERSION:-11.0.0-alpha.2}"
HERE="$(cd "$(dirname "$0")" && pwd)"
CP_DIR="${CP_DIR:-$HERE/build/circuitpython}"
JOBS="${JOBS:-$(nproc)}"
BOARDS=("$@")
if [ ${#BOARDS[@]} -eq 0 ]; then
    BOARDS=(guition_jc3636w518c guition_jc3636w518c_v2)
fi

# 1. CircuitPython source at CP_VERSION (shallow; re-used between runs).
if [ ! -d "$CP_DIR/.git" ]; then
    git clone --depth 1 --branch "$CP_VERSION" https://github.com/adafruit/circuitpython "$CP_DIR"
else
    git -C "$CP_DIR" fetch --depth 1 origin "$CP_VERSION"
    git -C "$CP_DIR" checkout --force FETCH_HEAD
fi
cd "$CP_DIR"
if [[ "$CP_VERSION" =~ ^[0-9] ]]; then
    CP_LABEL="$CP_VERSION"                                       # release tag
else
    CP_LABEL="$CP_VERSION-$(git rev-parse --short HEAD)"         # branch: add commit
fi
echo "Building against CircuitPython $CP_LABEL"

# 2. Submodules needed by the espressif port (includes the matching ESP-IDF).
python3 tools/ci_fetch_deps.py espressif
# When an existing checkout switches version, ESP-IDF's own nested submodules
# (mbedtls, lwip, Wi-Fi/BT libs, ...) stay at the old commits. Move the ones
# that are already initialized to the commits this ESP-IDF expects.
git -C ports/espressif/esp-idf submodule update --recursive --depth 1

# 3. Drop the board definitions into the tree.
for d in "$HERE"/boards/*/; do
    rm -rf "ports/espressif/boards/$(basename "$d")"
    cp -r "$d" "ports/espressif/boards/"
done

# 4. ESP-IDF toolchain. install.sh is quick when everything is present, and
#    picks up new tool versions after a CircuitPython upgrade.
cd ports/espressif
export IDF_PYTHON_CHECK_CONSTRAINTS="${IDF_PYTHON_CHECK_CONSTRAINTS:-yes}"
if ! ./esp-idf/install.sh esp32s3; then
    # The constraints file comes from dl.espressif.com; fall back if it is unreachable.
    echo "install.sh failed; retrying the Python environment without constraints"
    python3 ./esp-idf/tools/idf_tools.py install-python-env --no-constraints
    export IDF_PYTHON_CHECK_CONSTRAINTS=no
fi
# shellcheck disable=SC1091
source ./esp-idf/export.sh >/dev/null

# 5. CircuitPython's build scripts run inside the ESP-IDF Python environment.
#    cpp-coveralls is only for coverage reports and fails to build on new Pythons.
grep -v -E '^cpp-coveralls' ../../requirements-dev.txt > "$CP_DIR/.req-build.txt"
python -m pip install --quiet -r "$CP_DIR/.req-build.txt"

# 6. Build.
mkdir -p "$HERE/dist"
for b in "${BOARDS[@]}"; do
    # A build directory configured by another CircuitPython version is not reusable.
    stamp="build-$b/.cp-version"
    if [ -d "build-$b" ] && [ "$(cat "$stamp" 2>/dev/null)" != "$(git rev-parse HEAD)" ]; then
        rm -rf "build-$b"
    fi
    make -j"$JOBS" BOARD="$b"
    git rev-parse HEAD > "$stamp"
    cp "build-$b/firmware.bin" "$HERE/dist/$b-$CP_LABEL.bin"
    if [ -f "build-$b/firmware.uf2" ]; then
        cp "build-$b/firmware.uf2" "$HERE/dist/$b-$CP_LABEL.uf2"
    fi
done
ls -l "$HERE/dist"
