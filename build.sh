#!/usr/bin/env bash
# Build CircuitPython firmware for the Guition JC3636W518C.
#
#   ./build.sh                          # both variants, default source (below)
#   ./build.sh guition_jc3636w518c_v2   # one variant
#   CP_REF=main ./build.sh              # another branch of CP_REPO
#   CP_REPO=https://github.com/adafruit/circuitpython CP_REF=11.0.0-alpha.2 ./build.sh
#
# Environment:
#   CP_REPO     CircuitPython git repository to build from (default: urfdvw's fork)
#   CP_REF      branch, tag or commit in CP_REPO (default below)
#   CP_VERSION  version string the firmware reports. CircuitPython's build reads
#               this variable itself. Default: CP_REF for a release tag, else
#               "<newest upstream tag>-g<commit>" (like `git describe`).
#   CP_DIR      where to keep the CircuitPython checkout (default ./build/circuitpython)
#   JOBS        parallel make jobs (default: nproc)
#
# See docs/building-latest-circuitpython.md.
set -euo pipefail

# Default source: urfdvw/circuitpython, branch of adafruit/circuitpython PR #11859
# (espressif _bleio: connect() no longer hangs when the link fails early).
CP_REPO="${CP_REPO:-https://github.com/urfdvw/circuitpython}"
CP_REF="${CP_REF:-espressif-bleio-connect-disconnect}"
UPSTREAM=https://github.com/adafruit/circuitpython
HERE="$(cd "$(dirname "$0")" && pwd)"
CP_DIR="${CP_DIR:-$HERE/build/circuitpython}"
JOBS="${JOBS:-$(nproc)}"
BOARDS=("$@")
if [ ${#BOARDS[@]} -eq 0 ]; then
    BOARDS=(guition_jc3636w518c guition_jc3636w518c_v2)
fi

# 1. CircuitPython source at CP_REF (shallow; re-used between runs).
#    Submodule URLs in .gitmodules are absolute, so a fork works the same way.
if [ ! -d "$CP_DIR/.git" ]; then
    git init -q "$CP_DIR"
fi
git -C "$CP_DIR" fetch --depth 1 "$CP_REPO" "$CP_REF"
git -C "$CP_DIR" checkout -q --force FETCH_HEAD
cd "$CP_DIR"
SHA="$(git rev-parse --short HEAD)"

# Version string. A shallow clone has no tags for `git describe`, so set it here.
if [ -z "${CP_VERSION:-}" ]; then
    if [[ "$CP_REF" =~ ^[0-9]+\.[0-9]+\.[0-9]+ ]]; then
        CP_VERSION="$CP_REF"
    else
        base="$(git ls-remote --tags --refs "$UPSTREAM" | sed 's|.*refs/tags/||' \
                | grep -E '^[0-9]+\.[0-9]+\.[0-9]+' | sort -V | tail -1)"
        CP_VERSION="${base:-0.0.0}-g$SHA"
    fi
fi
export CP_VERSION
CP_LABEL="$CP_VERSION"
echo "Building $CP_REPO @ $CP_REF ($SHA) as CircuitPython $CP_VERSION"

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
