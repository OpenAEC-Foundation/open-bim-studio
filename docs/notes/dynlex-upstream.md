# DynLex upstream: our pin against DynLex master

**Decision question:** should this repository move from its pinned DynLex commit to DynLex master,
and what must reach upstream first?

Compared on 31 October 2026 by reading both histories (`git fetch`, `git log`, `git diff`). Nothing
was compiled or run, so every statement about behaviour below is **read from source**, not
measured.

## The two lines

| | Commit | Date |
|---|---|---|
| Our pin, `codex/cadkernel-port` | `c2d32bea` | 2026-10-23 |
| `OpenAEC-Foundation/dynlex` master | `4fe542b2` | 2026-10-26 |
| Where they diverged | `332dac13` | 2026-09-09 |

Master has 54 commits the pin lacks; the pin has 64 that master lacks — the kernel port and the
Vulkan compute dispatch of DynLex PR #8.

## What is on master and not on the pin

- `--incremental` (`b9355ff7`): faster relinking; it does not reuse type inference, so it does not
  address R-18's inference cost.
- Compile speed and memory commits, not measured on this application.
- Memory-safety diagnostics (`b504363b`), which could trip `build.sh`'s strict diagnostic gate.
- A rewrite of parts of the standard library (`e7441b72`, `ba9476d8`), including `json.dl`.
- A `GLCompute` entry point (fixed workgroup of 64). Compute dispatch and float64 remain on the
  pin only.
- Not on master: a change of the default optimisation level (still `-O0`) or a module system, so
  [ADR-0008](../architecture/decisions/0008-compile-units-with-c-abi-seams.md) stays the route.

## Our patches against master

| Patch | Upstream? | Applies to master |
|---|---|---|
| Class-instantiation cache fix (`rollbackTrialJournal` does not erase `instantiationIndicesByRequest`) | no; the bug is still on master | yes |
| libm (#27) | no | yes |
| `windows-library-names` | no | yes |
| `windows-compiler-stack` | no | yes |
| `pattern-reference-index` | no | yes |
| `shader-extensions` | no | **conflicts**; `lib/shader.dl` was rewritten on master |
| `pattern-precedence-families` | probably replaced by `57dfc3f3` | — |
| numeric-literal half of `dynlex-compiler-local` | replaced by `329672b4` | — |
| `lib/json.dl` override | no PR | would shadow master's rewritten `json.dl` |

## Housekeeping found

- DynLex issue #13 (inference memory) is fixed but still open; issue #7 is stale.
- Windows CI builds the compiler from the Open-BIM-Studio-0.1 snapshot, not from `c2d32bea`.

## Decisions of 31 October 2026

Answered by the maintainer ([`open-questions.md`](../open-questions.md), round 1, H):

1. **Stay on the pin** until the cache fix, libm, the two Windows patches and `json.dl` are merged
   upstream; then move to master.
2. **Computer 2 offers the patches upstream**, in this order: the cache fix with a regression
   test; libm and the two Windows patches; `json.dl`; then the shader patch, redone against
   master's `lib/shader.dl`.
3. **Split DynLex PR #8:** the compiler and runtime parts (compute dispatch, float64) go to master;
   the kernel part (`lib/cadkernel`, `lib/bim`) is closed, because the kernel lives here
   ([ADR-0007](../architecture/decisions/0007-kernel-source-lives-in-this-repository.md)).
4. **Adopt `--incremental`** for `build.sh dev` and the tests after the move, once computer 2 has
   measured time, memory and the number of new diagnostics.
5. **One pin for both platforms:** Windows CI and Linux build from the same commit, named in one
   file that `build.sh` and CI both read.
6. **Close DynLex #13** with a comment naming both commits, and update #7 with what is done
   (`GLCompute`, the memory fix).

## Verdict

Stay on `c2d32bea`. Moving now would bring back the class-instantiation cache failure, because
only our local patch fixes it. The move becomes possible when the four patches in decision 1 are
merged upstream; the measurement in decision 4 then decides whether `--incremental` is adopted.
