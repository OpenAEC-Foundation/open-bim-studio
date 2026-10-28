#!/usr/bin/env bash
# Builds and runs Open BIM Studio from this repository on a DynLex checkout.
#
#   ./build.sh generate                      the two generated import files (every other command runs it first)
#   ./build.sh app                           optimised editor (build/open-bim-studio)
#   ./build.sh dev                           unoptimised editor with debug info
#   ./build.sh dev-test NAME [NAME...]       editor and up to 3 headless checks in one compile
#   ./build.sh run-dev [ARGS...]             run the development build
#   ./build.sh run [ARGS...]                 run the editor (--example, FILE, --import ...)
#   ./build.sh kernel                        the kernel library build/kernel/libobskernel.a (also run by every other command)
#   ./build.sh test [NAME...]                headless tests (all when no name), BIM_JOBS at a time
#   ./build.sh bundle [NAME...]              the same tests compiled once as one program
#   ./build.sh probe NAME                    compile one manual tools/probes/ probe
#   ./build.sh run-probe NAME [ARGS...]      run an already compiled probe
#   ./build.sh installer OUT.sh              self-contained Linux installer
#   ./build.sh toolchain-info                the selected compiler, without building
#
# The compiler is the DynLex checkout named by DYNLEX_ROOT or .dynlex-root.local,
# built in place at build/dynlex; its own lib/ is found by the compiler itself.
# Programs compile from this repository's root: imports such as model/x.dl
# resolve here, lib/std.dl in the checkout, and a file under lib/ here shadows
# the checkout's (see lib/README.md). Nothing is staged or copied, except the
# prebuilt shaders into build/shaders, where the program reads them.
#
# BIM_BUILD_DIR (default build/) holds the outputs. BIM_PLATFORM (linux, the
# default, or windows) picks the window style module generated/platform.dl
# imports. BIM_JOBS (default 1) runs that many tests at once; the compiler
# needs several gigabytes per test, so raise it with the machine's memory.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
source "$here/toolchain.sh"
resolve_bim_toolchain "$here"
# Inspect the selected fork without invoking the compiler.
if [[ ${1:-app} == toolchain-info ]]; then
    show_bim_toolchain
    exit 0
fi
out=${BIM_BUILD_DIR:-$here/build}
dynlex="$root/build/dynlex"
cd "$here"

# The generated imports of ui/shell/main.dl: the OS's window style, and the
# self-test entry (a no-op unless dev-test writes the bundled checks).
write_platform() {
    mkdir -p generated
    printf 'import ui/shell/window_style_%s.dl\n' "${BIM_PLATFORM:-linux}" > generated/platform.dl
}
write_self_test_stub() {
    mkdir -p generated
    cat > generated/self_test.dl <<'STUB'
# Written by build.sh generate: the self-test entry of ui/shell/main.dl. The default does
# nothing; dev-test replaces it with the bundled headless checks.
function run bim app checks:
    execute:
        ignore 0
STUB
}
# The bundle of the named tests as the body of `run bim app checks`.
write_self_test_bundle() {
    mkdir -p generated
    python3 tools/bundle_tests.py make . generated/app_checks "$@"
    awk '
        /^print \(the string form of "=== / && !footer {
            print "function run bim app checks:"
            print "    execute:"
            footer = 1
        }
        { if (footer) print "        " $0; else print }
    ' generated/app_checks.dl > generated/self_test.dl
}
write_composition() {
    # The model record and the module dispatchers, from the MODULE manifests.
    python3 -B tools/compose_modules.py --root . --out generated > /dev/null
}
write_kernel_client() {
    # The kernel library's client, from its exposed functions (kernel/api/client.dl
    # is committed; this keeps it current, and git shows when it changed).
    python3 -B tools/kernel_client.py --exposed kernel/api/exposed.dl --out kernel/api/client.dl > /dev/null
}
generate() {
    write_platform
    write_self_test_stub
    write_composition
    write_kernel_client
    mkdir -p build/shaders "$out/shaders"
    cp viewer/shaders/*.spv build/shaders/
    if [ "$out/shaders" != "$here/build/shaders" ]; then cp viewer/shaders/*.spv "$out/shaders/"; fi
}
generate
command=${1:-app}
shift || true
if [ "$command" = generate ]; then
    echo "wrote generated/platform.dl, generated/self_test.dl, generated/model.dl and generated/compose.dl"
    exit 0
fi

if [ -f "$root/.cache/bootstrap/env.sh" ]; then
    # shellcheck disable=SC1091
    source "$root/.cache/bootstrap/env.sh" >/dev/null 2>&1 || true
fi
libs="$root/.cache/bootstrap/root/usr/lib/x86_64-linux-gnu"
if [ -d "$libs" ]; then
    export LIBRARY_PATH="$libs${LIBRARY_PATH:+:$LIBRARY_PATH}"
    export LD_LIBRARY_PATH="$libs${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi
# The platform shim (platform/obs_platform.c): the few C calls whose names
# differ between Linux and Windows, as the static library the program links
# ("obs_platform").
mkdir -p "$out/platform"
cc -std=c11 -O2 -fPIC -c platform/obs_platform.c -o "$out/platform/obs_platform.o"
ar rcs "$out/platform/libobs_platform.a" "$out/platform/obs_platform.o"
export LIBRARY_PATH="$out/platform${LIBRARY_PATH:+:$LIBRARY_PATH}"

# The kernel library (module split plan, phase E): kernel/api/exposed.dl
# compiled as a definition-only object into build/kernel/libobskernel.a,
# rebuilt when any kernel source is newer than the archive. Every program
# links it by the name "obskernel" through LIBRARY_PATH.
build_kernel_library() {
    mkdir -p "$out/kernel"
    archive="$out/kernel/libobskernel.a"
    if [ ! -f "$archive" ] || [ -n "$(find kernel -name '*.dl' -newer "$archive" -print -quit)" ]; then
        if ! "$dynlex" kernel/api/exposed.dl --emit-object --no-main -O2 -o "$out/kernel/obskernel.o" > "$out/kernel/obskernel.diag" 2>&1 || [ -s "$out/kernel/obskernel.diag" ]; then
            echo 'kernel library DIAG'; head -20 "$out/kernel/obskernel.diag"; exit 1
        fi
        ar rcs "$archive" "$out/kernel/obskernel.o"
        echo "kernel library: $archive"
    fi
    export LIBRARY_PATH="$out/kernel${LIBRARY_PATH:+:$LIBRARY_PATH}"
}
# Tests live in each module's tests/ directory; a name is looked up there.
test_source() {
    find . -path ./build -prune -o -path ./kernel/tests -prune -o -path ./kernel/reference -prune -o -path ./tools -prune -o -path ./generated -prune -o         -type f -path "*/tests/$1.dl" -print -quit
}
all_test_names() {
    find . -path ./build -prune -o -path ./kernel/tests -prune -o -path ./kernel/reference -prune -o -path ./tools -prune -o -path ./generated -prune -o         -type f -path "*/tests/*.expected.txt" -print | sed 's#.*/##; s#\.expected\.txt$##' | sort
}
# Compiles a test by name, runs it and compares with its expected output;
# prints one line and writes $out/tests/NAME.result (0 or 1).
run_one_test() {
    name=$1
    result=1
    source=$(test_source "$name")
    if [ -z "$source" ]; then echo "$name MISSING (no */tests/$name.dl)"; echo 1 > "$out/tests/$name.result"; return; fi
    if ! "$dynlex" "$source" -O0 -o "$out/tests/$name" > "$out/tests/$name.diag" 2>&1 || [ -s "$out/tests/$name.diag" ]; then
        echo "$name DIAG"; head -5 "$out/tests/$name.diag"
    elif ! (ulimit -c 0; stdbuf -oL "$out/tests/$name") > "$out/tests/$name.out" 2>&1; then
        echo "$name RUNTIME FAIL"; head -10 "$out/tests/$name.out"
    elif diff -q "$out/tests/$name.out" "${source%.dl}.expected.txt" > /dev/null; then
        echo "$name PASS"; result=0
    else
        echo "$name FAIL"; diff "$out/tests/$name.out" "${source%.dl}.expected.txt" | head -10 || true
    fi
    echo "$result" > "$out/tests/$name.result"
}
export -f run_one_test test_source
export dynlex out

if [ "$command" != kernel ]; then build_kernel_library; fi
case "$command" in
    app)
        "$dynlex" ui/shell/main.dl -O2 -o "$out/open-bim-studio"
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
            write_self_test_bundle "$@"
            if ! "$dynlex" ui/shell/main.dl "-O$dev_opt" "${debug_flags[@]}" -o "$out/open-bim-studio-dev" > "$out/tests/app.diag" 2>&1 || [ -s "$out/tests/app.diag" ]; then
                echo 'app DIAG'; head -20 "$out/tests/app.diag"; exit 1
            fi
            if ! (ulimit -c 0; "$out/open-bim-studio-dev" --self-test) > "$out/tests/app_checks.out" 2>&1; then
                echo 'app checks RUNTIME FAIL'; head -20 "$out/tests/app_checks.out"; exit 1
            fi
            python3 tools/bundle_tests.py split "$out/tests/app_checks.out" generated/app_checks.expected.txt "$out/tests/app_checks"
        else
            "$dynlex" ui/shell/main.dl "-O$dev_opt" "${debug_flags[@]}" -o "$out/open-bim-studio-dev"
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
            while IFS= read -r found; do names+=("$found"); done < <(all_test_names)
        fi
        mkdir -p "$out/tests"
        rm -f "$out"/tests/*.result
        jobs=${BIM_JOBS:-1}
        printf '%s\n' "${names[@]}" | xargs -P "$jobs" -I{} bash -c 'run_one_test "$1"' _ {}
        status=0
        for name in "${names[@]}"; do
            if [ "$(cat "$out/tests/$name.result" 2>/dev/null || echo 1)" != 0 ]; then status=1; fi
        done
        exit $status ;;
    bundle)
        # The tests (all when no name) bundled into one program: one compile
        # instead of one per test (tools/bundle_tests.py).
        names=("$@")
        if [ ${#names[@]} -eq 0 ]; then
            while IFS= read -r found; do names+=("$found"); done < <(all_test_names)
        fi
        mkdir -p "$out/tests"
        python3 tools/bundle_tests.py make . generated/bundle "${names[@]}"
        if ! "$dynlex" generated/bundle.dl -O0 -o "$out/tests/bundle" > "$out/tests/bundle.diag" 2>&1 || [ -s "$out/tests/bundle.diag" ]; then
            echo "bundle DIAG"; head -20 "$out/tests/bundle.diag"; exit 1
        fi
        runtime_status=0
        (ulimit -c 0; stdbuf -oL "$out/tests/bundle") > "$out/tests/bundle.out" 2>&1 || runtime_status=$?
        if [ "$runtime_status" -ne 0 ]; then
            echo "bundle RUNTIME FAIL (exit $runtime_status)"
        fi
        python3 tools/bundle_tests.py split "$out/tests/bundle.out" generated/bundle.expected.txt "$out/tests/bundled"
        exit "$runtime_status" ;;
    kernel)
        build_kernel_library
        ;;
    probe|run-probe)
        probe_name=${1:-}
        case "$probe_name" in
            ''|*[!a-zA-Z0-9_-]*) echo 'give a probe name using letters, digits, underscore or dash' >&2; exit 2 ;;
        esac
        shift
        probe_source="tools/probes/$probe_name.dl"
        probe_binary="$out/tools/$probe_name"
        if [ ! -f "$probe_source" ]; then
            echo "unknown probe $probe_name" >&2; exit 2
        fi
        if [ "$command" = probe ]; then
            mkdir -p "$out/tools"
            if ! "$dynlex" "$probe_source" -O0 -o "$probe_binary" > "$probe_binary.diag" 2>&1 || [ -s "$probe_binary.diag" ]; then
                echo "$probe_name DIAG"; head -20 "$probe_binary.diag"; exit 1
            fi
            echo "built $probe_binary"
        else
            if [ ! -x "$probe_binary" ]; then
                echo "compile first: build.sh probe $probe_name" >&2; exit 2
            fi
            exec "$probe_binary" "$@"
        fi ;;
    installer)
        bash installer/make-installer.sh "$out/open-bim-studio" "${1:?installer output path}" ;;
    *)
        echo "unknown command $command" >&2; exit 2 ;;
esac
