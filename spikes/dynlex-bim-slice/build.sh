#!/usr/bin/env bash
# Builds and runs Open BIM Studio (the BIM slice) from this spike's overlay on a DynLex checkout.
#
#   DYNLEX_ROOT=/path/to/dynlex-cadkernel ./build.sh app        optimised editor (build/open-bim-studio)
#   DYNLEX_ROOT=... ./build.sh dev                               unoptimised editor with debug info
#   DYNLEX_ROOT=... ./build.sh run-dev [ARGS...]                  run the independent development build
#   DYNLEX_ROOT=... ./build.sh run [ARGS...]                     run the editor (--example, FILE, --import ...)
#   DYNLEX_ROOT=... ./build.sh test [NAME...]                    headless tests (all when no name)
#   DYNLEX_ROOT=... ./build.sh installer OUT.sh                  self-contained installer
#
# BIM_BUILD_DIR (default build/) is where the tree and the outputs go, so two
# builds can run side by side.
#
# DYNLEX_ROOT is a DynLex checkout with a built compiler at build/dynlex (the
# cadkernel fork). The tree is assembled in build/tree: the checkout's lib/,
# this overlay, the public JSON parse patch and the prebuilt shaders. Nothing
# in the checkout is changed.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
root=${DYNLEX_ROOT:?set DYNLEX_ROOT to a DynLex checkout with a built compiler}
out=${BIM_BUILD_DIR:-$here/build}
tree=$out/tree
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
        build/dynlex examples/bim-slice/main.dl -O2 -o "$out/open-bim-studio"
        echo "built $out/open-bim-studio" ;;
    dev)
        debug_flags=()
        if [ "${BIM_DEBUG:-1}" != 0 ]; then debug_flags+=(-g); fi
        build/dynlex examples/bim-slice/main.dl -O0 "${debug_flags[@]}" -o "$out/open-bim-studio-dev"
        echo "built $out/open-bim-studio-dev" ;;
    run)
        exec "$out/open-bim-studio" "$@" ;;
    run-dev)
        # The current native entry point expects at least one argument.
        if [ "$#" -eq 0 ]; then set -- --example; fi
        exec "$out/open-bim-studio-dev" "$@" ;;
    test)
        names=("$@")
        if [ ${#names[@]} -eq 0 ]; then
            for expected in examples/bim-slice/tests/*.expected.txt; do
                names+=("$(basename "$expected" .expected.txt)")
            done
        fi
        mkdir -p "$out/tests"
        status=0
        for name in "${names[@]}"; do
            if ! build/dynlex "examples/bim-slice/tests/$name.dl" -O0 -o "$out/tests/$name" > "$out/tests/$name.diag" 2>&1 || [ -s "$out/tests/$name.diag" ]; then
                echo "$name DIAG"; head -5 "$out/tests/$name.diag"; status=1; continue
            fi
            if ! (ulimit -c 0; stdbuf -oL "$out/tests/$name") > "$out/tests/$name.out" 2>&1; then
                echo "$name RUNTIME FAIL"; head -10 "$out/tests/$name.out"; status=1; continue
            fi
            if diff -q "$out/tests/$name.out" "examples/bim-slice/tests/$name.expected.txt" > /dev/null; then
                echo "$name PASS"
            else
                echo "$name FAIL"; diff "$out/tests/$name.out" "examples/bim-slice/tests/$name.expected.txt" | head -10 || true
                status=1
            fi
        done
        exit $status ;;
    installer)
        bash examples/bim-slice/installer/make-installer.sh "$out/open-bim-studio" "${1:?installer output path}" ;;
    *)
        echo "unknown command $command" >&2; exit 2 ;;
esac
