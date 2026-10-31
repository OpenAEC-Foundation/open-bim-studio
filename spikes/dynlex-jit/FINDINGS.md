# Findings: `dynlex-jit`

## Question

Can a DynLex script be compiled while the editor runs, loaded in-process and
run against the live BIM model, at interactive speed and without changes to
the compiler?

## Set-up

- AMD Ryzen 7 9700X (16 threads), 29 GB RAM, Linux 7.0.0-38, clang-20.
- Compiler: the DynLex checkout `~/dynlex-7` at `c2d32bea`. LLVM is the fork
  pinned in its `metadata/LLVM_TOOLCHAIN` (major 23). `libLLVMOrcJIT.a` is
  already part of that toolchain build.
- Model: built in code by `editor_host.dl` (one level, one wall type). No
  model from `reference/` was used.
- Method: `run.sh`, timings printed by the shim (`std::chrono`), compile
  sizes with `/usr/bin/time -f "%e s %M KB"`. Each was measured on a single
  run, with no repetitions, so treat the numbers as indications.

## Measured

| Step | Time | Peak RSS |
|---|---|---|
| Compile a script with only `lib/std.dl` (`--emit-object --no-main -O0`) | 0.03–0.04 s | 54 MB |
| The same with `lib/list.dl` (heap list, printing) | 0.06 s | — |
| Compile a script importing `generated/model.dl` (the full model record) | 2.39 s | 209 MB |
| Compile a script importing `bim/bim_model.dl` and calling `add bim wall typed` | 2.4–3.0 s (`-O0`/`-O1`) | 209 MB |
| ORC load of the object plus the call into the model | 0.2–0.4 ms | — |
| `libobsjit.so` with LLVM linked statically | 57 MB on disk | — |

End-to-end result: the first script added five walls to the host's model
(`walls before: 0`, `walls after: 5`). The second edited three of them in
place (height 3 → 4.5 m), and the host then read those changes back. Both
scripts ran in one process against one model, each in its own JITDylib.

A script's object needs only `realloc`, `free` and `abort` from libc (`nm`).
It brings its own instantiation of every DynLex function it uses. The shared
libc allocator is what makes it safe for a script to grow model lists that
the host later frees.

## What this means

**Measured:** the mechanism works with no compiler change. It uses
`--emit-object --no-main`, `exposed function` for a fixed C entry point, and
LLVM ORC from the toolchain the compiler already builds. Compile time, not
JIT time, sets the latency. That latency is about the cost of what the script
imports: tens of milliseconds for plain logic, about 2.5 s once the model
record is in scope.

**Not settled, and why:**

1. **Layout agreement.** A script is safe only when it was compiled from the
   same record sources as the running editor. A mismatch corrupts memory
   silently. A product version needs a fingerprint of `generated/model.dl`
   and the records, checked before the call.
2. **Undo, journal and caches.** The scripts write straight into the model
   and bypass the editor's transactions, the join index and scene caches.
   Going through the editor's functions means importing `ui/editor`, which
   compiles in minutes, not seconds (`build-times.md`: `test editor` 4–5 min).
   A plausible way round this is a small script API of `exposed function`s
   in the editor, the way `kernel/api/exposed.dl` does it for the kernel, so
   that scripts import only a generated client. That is not measured here.
3. **No isolation.** A faulty script crashes the editor. ORC can also run
   code out of process, but that was not tried.
4. **Distribution.** The shim calls the `dynlex` binary as a subprocess.
   The editor would have to ship the compiler and the `.dl` sources the
   scripts import, or link the compiler in as a library.
5. **Windows.** Untested. ORC supports COFF, but the shim, the subprocess
   call and symbol resolution need their own check.
6. **Memory.** The spike never removes a JITDylib, so every script run keeps
   its code loaded.

## Verdict

No pass/fail criterion was written before the run, so this is a provisional
verdict, not a pass. A JIT for DynLex scripts against the live model is
feasible and small: a 55-line shim and no compiler changes. The open work is
on the editor side: a stable script API with undo, a layout fingerprint and
shipping the compiler. That should be the next step, measured against a
criterion written in `docs/risks.md` first.
