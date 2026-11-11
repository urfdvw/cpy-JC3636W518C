#!/usr/bin/env bash
# Build CircuitPython firmware for the Guition JC3636W518C.
#
#   ./build.sh                     # both variants
#   ./build.sh guition_jc3636w518c # one variant
#
# Environment:
#   CP_VERSION  CircuitPython git tag/branch to build against (default below)
#   CP_DIR      where to keep the CircuitPython checkout (default ./build/circuitpython)
#   JOBS        parallel make jobs (default: nproc)
set -euo pipefail

CP_VERSION="${CP_VERSION:-10.3.2}"
HERE="$(cd "$(dirname "$0")" && pwd)"
CP_DIR="${CP_DIR:-$HERE/build/circuitpython}"
JOBS="${JOBS:-$(nproc)}"
BOARDS=("$@")
if [ ${#BOARDS[@]} -eq 0 ]; then
    BOARDS=(guition_jc3636w518c guition_jc3636w518c_v2)
fi

if [ ! -d "$CP_DIR/.git" ]; then
    git clone --depth 1 --branch "$CP_VERSION" https://github.com/adafruit/circuitpython "$CP_DIR"
fi

cd "$CP_DIR"
python3 tools/ci_fetch_deps.py espressif

# Drop the board definitions into the CircuitPython tree.
for d in "$HERE"/boards/*/; do
    rm -rf "ports/espressif/boards/$(basename "$d")"
    cp -r "$d" "ports/espressif/boards/"
done

cd ports/espressif
if [ ! -d "$HOME/.espressif" ] || ! ls "$HOME"/.espressif/tools/xtensa-esp-elf* >/dev/null 2>&1; then
    ./esp-idf/install.sh esp32s3
fi
# shellcheck disable=SC1091
source ./esp-idf/export.sh >/dev/null
# CircuitPython's build scripts run inside the ESP-IDF Python environment.
# cpp-coveralls is only used for coverage reports and fails to build on new Pythons.
grep -v -E '^cpp-coveralls' ../../requirements-dev.txt > "$CP_DIR/.req-build.txt"
python -m pip install --quiet -r "$CP_DIR/.req-build.txt"

mkdir -p "$HERE/dist"
for b in "${BOARDS[@]}"; do
    make -j"$JOBS" BOARD="$b"
    cp "build-$b/firmware.bin" "$HERE/dist/$b-$CP_VERSION.bin"
    [ -f "build-$b/firmware.uf2" ] && cp "build-$b/firmware.uf2" "$HERE/dist/$b-$CP_VERSION.uf2"
done
ls -l "$HERE/dist"
