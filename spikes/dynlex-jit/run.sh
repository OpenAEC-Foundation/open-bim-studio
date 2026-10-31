#!/usr/bin/env bash
# Builds the JIT shim against the compiler's own LLVM, compiles the editor
# stand-in, and runs it from the repository root (where script imports resolve).
set -euo pipefail
cd "$(dirname "$0")/../.."
root="${DYNLEX_ROOT:-$(cat .dynlex-root.local)}"
out=build/spikes/dynlex-jit
cmake -S spikes/dynlex-jit -B "$out" -G Ninja -DCMAKE_CXX_COMPILER="${CXX:-clang++-20}" \
    -DCMAKE_BUILD_TYPE=Release -DLLVM_DIR="$root/.cache/llvm-toolchain/native/install/lib/cmake/llvm" > /dev/null
ninja -C "$out" > /dev/null
LIBRARY_PATH="$out" "$root/build/dynlex" spikes/dynlex-jit/editor_host.dl -O1 -o "$out/editor_host"
DYNLEX="$root/build/dynlex" LD_LIBRARY_PATH="$out" "$out/editor_host"
