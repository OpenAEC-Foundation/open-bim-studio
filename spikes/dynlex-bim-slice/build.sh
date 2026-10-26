#!/usr/bin/env bash
# Builds and runs Open BIM Studio (the BIM slice) from this spike's overlay on a DynLex checkout.
#
#   DYNLEX_ROOT=/path/to/dynlex-cadkernel ./build.sh app        optimised editor (build/open-bim-studio)
#   DYNLEX_ROOT=... ./build.sh dev                               unoptimised editor with debug info
#   DYNLEX_ROOT=... ./build.sh dev-test NAME [NAME...]            editor and up to 3 headless checks in one compile
#   DYNLEX_ROOT=... ./build.sh run-dev [ARGS...]                  run the independent development build
#   DYNLEX_ROOT=... ./build.sh run [ARGS...]                     run the editor (--example, FILE, --import ...)
#   DYNLEX_ROOT=... ./build.sh test [NAME...]                    headless tests (all when no name)
#   DYNLEX_ROOT=... ./build.sh bundle [NAME...]                  the same tests compiled once as one program
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
# Fail before staging/type inference on known implicit-parameter name captures.
case "${1:-app}" in
    app|dev|dev-test|test|bundle)
        python3 "$here/tools/check_dynlex_locals.py" "$here/overlay/examples/bim-slice"
        ;;
esac
source "$here/toolchain.sh"
resolve_bim_toolchain "$here"
# Inspect the selected fork without staging files or invoking the compiler.
if [[ ${1:-app} == toolchain-info ]]; then
    show_bim_toolchain
    exit 0
fi
out=${BIM_BUILD_DIR:-$here/build}
tree=$out/tree
mkdir -p "$tree/build/shaders"
rsync -a --delete "$root/lib/" "$tree/lib/"
rsync -a "$here/overlay/" "$tree/"
# Headless fixture tests read the same review models shipped with the spike.
mkdir -p "$tree/examples/bim-slice/models"
rsync -a --delete "$here/examples/" "$tree/examples/bim-slice/models/"
if ! grep -q "the JSON document parsed from" "$tree/lib/json.dl"; then
    (cd "$tree" && patch -p1 -s < "$here/patches/lib-json-public-parse.patch")
fi
if ! grep -q "Bound storage by this encoded string" "$tree/lib/json.dl"; then
    (cd "$tree" && patch -p1 -s < "$here/patches/lib-json-bounded-string.patch")
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
# The platform shim (`examples/bim-slice/platform/obs_platform.c`): the few
# C calls whose names differ between Linux and Windows, as the static
# library the slice links ("obs_platform").
mkdir -p "$out/platform"
cc -std=c11 -O2 -fPIC -c "$tree/examples/bim-slice/platform/obs_platform.c" -o "$out/platform/obs_platform.o"
ar rcs "$out/platform/libobs_platform.a" "$out/platform/obs_platform.o"
export LIBRARY_PATH="$out/platform${LIBRARY_PATH:+:$LIBRARY_PATH}"
cd "$tree"
command=${1:-app}
shift || true
case "$command" in
    app)
        build/dynlex examples/bim-slice/main.dl -O2 -o "$out/open-bim-studio"
        echo "built $out/open-bim-studio" ;;
    dev|dev-test)
        dev_opt=${BIM_DEV_OPT_LEVEL:-0}
        case "$dev_opt" in
            0|1|2) ;;
            *) echo 'BIM_DEV_OPT_LEVEL must be 0, 1 or 2' >&2; exit 2 ;;
        esac
        debug_flags=()
        if [ "${BIM_DEBUG:-1}" != 0 ]; then debug_flags+=(-g); fi
        if [ "$command" = dev-test ]; then
            if [ "$#" -lt 1 ] || [ "$#" -gt 3 ]; then
                echo 'dev-test requires 1 to 3 explicit test names' >&2; exit 2
            fi
            mkdir -p "$out/tests"
            python3 "$here/tools/bundle_tests.py" make examples/bim-slice/tests app_checks "$@"
            # Keep test definitions dormant during normal app use. Only the
            # generated footer becomes a callable, editor-independent entry.
            awk '
                /^print \(the string form of "=== / && !footer {
                    print "function run bim app checks:"
                    print "    execute:"
                    footer = 1
                }
                { if (footer) print "        " $0; else print }
            ' examples/bim-slice/tests/app_checks.dl > examples/bim-slice/tests/app_checks.tmp
            mv examples/bim-slice/tests/app_checks.tmp examples/bim-slice/tests/app_checks.dl
            # Modify the staged copy only; run before any window/font/GPU setup.
            awk '
                BEGIN { print "import examples/bim-slice/tests/app_checks.dl" }
                /^set startedAt to / {
                    print "set appCheckArguments to the command line arguments"
                    print "if appCheckArguments\047 length > 0:"
                    print "    if (the argument at 0 in appCheckArguments) = (the string form of \"--self-test\"):"
                    print "        run bim app checks"
                    print "        @intrinsic(\"call\", \"libc\", \"exit\", nothing, 0)"
                }
                { print }
            ' examples/bim-slice/main.dl > examples/bim-slice/main.tmp
            mv examples/bim-slice/main.tmp examples/bim-slice/main.dl
            if ! build/dynlex examples/bim-slice/main.dl "-O$dev_opt" "${debug_flags[@]}" -o "$out/open-bim-studio-dev" > "$out/tests/app.diag" 2>&1 || [ -s "$out/tests/app.diag" ]; then
                echo 'app DIAG'; head -20 "$out/tests/app.diag"; exit 1
            fi
            if ! (ulimit -c 0; "$out/open-bim-studio-dev" --self-test) > "$out/tests/app_checks.out" 2>&1; then
                echo 'app checks RUNTIME FAIL'; head -20 "$out/tests/app_checks.out"; exit 1
            fi
            python3 "$here/tools/bundle_tests.py" split "$out/tests/app_checks.out" examples/bim-slice/tests/app_checks.expected.txt "$out/tests/app_checks"
        else
            build/dynlex examples/bim-slice/main.dl "-O$dev_opt" "${debug_flags[@]}" -o "$out/open-bim-studio-dev"
        fi
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
    bundle)
        # The tests (all when no name) bundled into one program: one compile
        # instead of one per test (tools/bundle_tests.py).
        names=("$@")
        if [ ${#names[@]} -eq 0 ]; then
            for expected in examples/bim-slice/tests/*.expected.txt; do
                names+=("$(basename "$expected" .expected.txt)")
            done
        fi
        mkdir -p "$out/tests"
        python3 "$here/tools/bundle_tests.py" make examples/bim-slice/tests bundle "${names[@]}"
        if ! build/dynlex examples/bim-slice/tests/bundle.dl -O0 -o "$out/tests/bundle" > "$out/tests/bundle.diag" 2>&1 || [ -s "$out/tests/bundle.diag" ]; then
            echo "bundle DIAG"; head -20 "$out/tests/bundle.diag"; exit 1
        fi
        runtime_status=0
        (ulimit -c 0; stdbuf -oL "$out/tests/bundle") > "$out/tests/bundle.out" 2>&1 || runtime_status=$?
        if [ "$runtime_status" -ne 0 ]; then
            echo "bundle RUNTIME FAIL (exit $runtime_status)"
        fi
        python3 "$here/tools/bundle_tests.py" split "$out/tests/bundle.out" examples/bim-slice/tests/bundle.expected.txt "$out/tests/bundled"
        exit "$runtime_status" ;;
    installer)
        bash examples/bim-slice/installer/make-installer.sh "$out/open-bim-studio" "${1:?installer output path}" ;;
    *)
        echo "unknown command $command" >&2; exit 2 ;;
esac
