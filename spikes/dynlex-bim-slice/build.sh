#!/usr/bin/env bash
# Builds and runs the BIM slice from this spike's overlay on a DynLex checkout.
#
#   DYNLEX_ROOT=/path/to/dynlex-cadkernel ./build.sh app        optimised editor (build/bim-slice)
#   DYNLEX_ROOT=... ./build.sh dev                               unoptimised editor with debug info
#   DYNLEX_ROOT=... ./build.sh run [ARGS...]                     run the editor (--example, FILE, --import ...)
#   DYNLEX_ROOT=... ./build.sh test [NAME...]                    headless tests (all when no name)
#   DYNLEX_ROOT=... ./build.sh installer OUT.sh                  self-contained installer
#
# DYNLEX_ROOT is a DynLex checkout with a built compiler at build/dynlex (the
# cadkernel fork). The tree is assembled in build/tree: the checkout's lib/,
# this overlay, the public JSON parse patch and the prebuilt shaders. Nothing
# in the checkout is changed.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
root=${DYNLEX_ROOT:?set DYNLEX_ROOT to a DynLex checkout with a built compiler}
tree=$here/build/tree
mkdir -p "$tree/build/shaders"
rsync -a --delete "$root/lib/" "$tree/lib/"
rsync -a "$here/overlay/" "$tree/"
if ! grep -q "the JSON document parsed from" "$tree/lib/json.dl"; then
    (cd "$tree" && patch -p1 -s < "$here/patches/lib-json-public-parse.patch")
fi
cp "$here"/shaders/*.spv "$tree/build/shaders/"
# The fallback font and its licence, which the installer also ships.
mkdir -p "$tree/tests/games/fonts"
cp "$root/tests/games/fonts/LiberationMono-Regular.ttf" "$root/tests/games/fonts/LICENSE-LiberationFonts" "$tree/tests/games/fonts/"
ln -sfn "$root/build/dynlex" "$tree/build/dynlex"
if [ -f "$root/.cache/bootstrap/env.sh" ]; then
    # shellcheck disable=SC1091
    source "$root/.cache/bootstrap/env.sh" >/dev/null 2>&1 || true
fi
libs="$root/.cache/bootstrap/root/usr/lib/x86_64-linux-gnu"
if [ -d "$libs" ]; then
    export LIBRARY_PATH="$libs${LIBRARY_PATH:+:$LIBRARY_PATH}"
    export LD_LIBRARY_PATH="$libs${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi
cd "$tree"
command=${1:-app}
shift || true
case "$command" in
    app)
        build/dynlex examples/bim-slice/main.dl -O2 -o "$here/build/bim-slice"
        echo "built $here/build/bim-slice" ;;
    dev)
        build/dynlex examples/bim-slice/main.dl -O0 -g -o "$here/build/bim-slice-dev"
        echo "built $here/build/bim-slice-dev" ;;
    run)
        exec "$here/build/bim-slice" "$@" ;;
    test)
        names=("$@")
        if [ ${#names[@]} -eq 0 ]; then
            for expected in examples/bim-slice/tests/*.expected.txt; do
                names+=("$(basename "$expected" .expected.txt)")
            done
        fi
        mkdir -p "$here/build/tests"
        status=0
        for name in "${names[@]}"; do
            if ! build/dynlex "examples/bim-slice/tests/$name.dl" -O0 -o "$here/build/tests/$name" > "$here/build/tests/$name.diag" 2>&1 || [ -s "$here/build/tests/$name.diag" ]; then
                echo "$name DIAG"; head -5 "$here/build/tests/$name.diag"; status=1; continue
            fi
            "$here/build/tests/$name" > "$here/build/tests/$name.out" 2>&1 || true
            if diff -q "$here/build/tests/$name.out" "examples/bim-slice/tests/$name.expected.txt" > /dev/null; then
                echo "$name PASS"
            else
                echo "$name FAIL"; diff "$here/build/tests/$name.out" "examples/bim-slice/tests/$name.expected.txt" | head -10; status=1
            fi
        done
        exit $status ;;
    installer)
        bash examples/bim-slice/installer/make-installer.sh "$here/build/bim-slice" "${1:?installer output path}" ;;
    *)
        echo "unknown command $command" >&2; exit 2 ;;
esac
