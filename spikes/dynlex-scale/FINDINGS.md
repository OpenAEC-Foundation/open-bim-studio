# FINDINGS — R-18, DynLex compile time and memory at kernel scale

## The question, restated

The kernel will be the largest DynLex program written. Can the compiler build a kernel-sized
program in a time a developer can sit through, and within the memory of a development machine?

The pass/fail criteria were written before the generator existed and are quoted verbatim from
[`../../docs/risks.md`](../../docs/risks.md) R-18:

> - **Spike:** `spikes/dynlex-scale/` — generate synthetic DynLex programs of 5k, 20k and 50k
>   lines in the kernel's style (classes, patterns, intrinsics); measure compile time and memory.
> - **Pass:** 20k lines compile in under 30 s on the reference machine.
> - **Fail:** over 120 s, or the compiler exhausts memory — a blocker to fix in dynlex before M1.

Every number below is copied from a named row of
[`results/dynlex-scale.md`](results/dynlex-scale.md), produced in one session on one machine on
2026-09-11.

## Hardware, OS and versions

*Measured.* Recorded from `Get-CimInstance` and the compiler's own `--version`.

| | |
|---|---|
| CPU | `Intel(R) Core(TM) i9-14900HX` (32 logical processors) |
| RAM | 32 GB |
| OS | Windows 11 Pro, `10.0.26200` |
| DynLex | `dynlex.exe --version` → `0.0.3`; binary 73.9 MB, built 2026-09-09 |
| DynLex commit | `7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd` (`master`) **plus uncommitted compiler edits — see the caveat below** |
| Python (generator and runner) | 3.12.10, `psutil` 7.2.2 |

### Caveat on the compiler pin — read this before citing any number here

The `../dynlex` working tree was **not clean** when the compiler binary used here was built, and
the binary was not rebuilt for this spike. `git -C ../dynlex diff --stat` at the time of
measurement:

```
 .gitignore                                                    |  1 +
 lib/config.dl                                                 |  1 +
 src/cpp/compiler/type.h                                       | 11 +++++++++++
 .../compiler/type_inference/function_inference_intrinsics.inl | 10 +++++++++-
 src/cpp/compiler/type_inference/type_resolution.inl           |  8 ++++++--
 .../compiler/type_inference/type_resolution_diagnostics.inl   |  2 ++
 6 files changed, 30 insertions(+), 3 deletions(-)
```

plus untracked `tests/benchmarks/matrix_solver/`, `tests/required/unary_math_boolean_condition/`
and `tests/required/unary_math_invalid_operand/`. The measured compiler is therefore
**7cacbc9 plus those uncommitted edits as they stood at build time**, not 7cacbc9 itself.

This caveat matters more for R-18 than for R-19: **every one of the six modified files is in type
inference**, which is the phase this spike loads hardest. The numbers below could move in either
direction against a clean 7cacbc9. They must be reproduced once `metadata/DYNLEX_COMMIT` pins a
clean commit, and the scaling exponent re-derived, before anything is changed in dynlex on the
strength of them.

## Which reference model was used

**None.** [`../README.md`](../README.md) asks which model from `../../reference/` a spike used;
this spike uses no model. Its input is generated DynLex source. The size and shape of that source
are the independent variable.

## Method

`generate.py` emits synthetic DynLex in the kernel's style. One *unit* is a point-like record —
a class with three 64-bit floating-point members — plus the ten patterns a geometry kernel writes
over such a record: construct, add, scale, dot, cross, squared length, compare, componentwise
min/max, lerp, and a predicate returning a boolean. Every pattern word carries the unit index
(`a point u00042`, `the cross u00042 of …`), so no two units collide and the compiler's pattern
table grows with the program. A trailing `main` calls every pattern of every unit exactly once
and folds the results into one printed number, so nothing can be dead-code eliminated.

| Target | Lines | Units | Classes | Function patterns |
|---:|---:|---:|---:|---:|
| 5k | 5005 | 64 | 64 | 705 |
| 20k | 20059 | 257 | 257 | 2828 |
| 50k | 50011 | 641 | 641 | 7052 |

Lines and units are the results file's own columns; classes and function patterns follow from
them, because the generator emits exactly one class and eleven function patterns per unit (the
ten listed above plus the `report` that calls them), and the prelude adds one more.

Constants are drawn from a seeded PRNG — **seed `20260909`** — so a given (seed, line count)
pair produces byte-identical source. The generated `.dl` files are not committed; regenerate
them with `python generate.py --lines 20000 --seed 20260909 --out build/scale_20000.dl`.

**Correctness is checked, not assumed.** `generate.py` also recomputes the number the program
should print, in Python IEEE doubles, following the same operation order as the generated `the
report` patterns. `run.py` runs the compiled binary and compares. So this spike measures a
compiler producing a *correct* program, not merely one that terminates.

**Timing** is wall time around the `dynlex.exe <file> -o <out>` process, `time.perf_counter`.
Five runs, median; a program whose first compile exceeds 90 s is compiled once (the 50k program).
**Peak memory** is the compiler process's `peak_wset` from `psutil`, polled every 20 ms and
re-read after exit — the highest value over all runs is reported.

No optimisation flag is passed. The compiler's default emitted-code level is `-O0`
(`src/cpp/compiler/parseContext.h:115`), so these are *lower* bounds: a kernel build passing
`-O2`, which R-19 shows it must, will spend more time still in LLVM on top of these figures.

## Results

From *Summary* in [`results/dynlex-scale.md`](results/dynlex-scale.md):

| Lines | Units | Compile s (median) | Peak MB | Binary runs? | Output matches expected? |
|---:|---:|---:|---:|---|---|
| 5005 | 64 | **5.26** | 298 | yes | yes |
| 20059 | 257 | **72.19** | 1102 | yes | yes |
| 50011 | 641 | **1146.72** | 2843 | yes | yes |

The five 20k runs were 72.19, 70.19, 68.83, 87.05, 77.97 s. The 50k program was compiled once:
1146.72 s is **19 minutes 7 seconds**.

**Every program compiled cleanly — zero diagnostics at all three sizes — and every binary printed
exactly the value Python computed independently**: 3398.0544795872252, 14811.008943975516 and
38835.641248242602. No crash, no hang, no internal error, no wrong code.

### The shape of the curve

*Derived from the three measured rows above.*

| From → to | lines × | time × | implied exponent | memory × |
|---|---:|---:|---:|---:|
| 5005 → 20059 | 4.01 | 13.72 | **1.89** | 3.70 |
| 20059 → 50011 | 2.49 | 15.88 | **3.03** | 2.58 |
| 5005 → 50011 | 9.99 | 218.01 | **2.34** | 9.54 |

Compile time is **superlinear and the exponent is getting worse**, not better, as the program
grows: roughly quadratic over the first step and roughly cubic over the second. Memory, by
contrast, is close to linear in program size (9.54× for 9.99× the lines) and never came near
exhausting the machine — 2.8 GB peak of 32 GB.

An anchor at the small end, taken from the R-19 spike's compile log rather than from this one
and so labelled as such: `orient3d.dl` plus its 117-line prelude — 161 lines — compiles unflagged
in **0.37 s**. That point is *not* on the curve above and must not be fitted to it: thirty-one
times that source (5005 lines) costs only fourteen times the time, because at 161 lines almost
all of the 0.37 s is fixed process start-up plus `lib/std.dl`. The exponents come from the three
measured sizes, where the fixed cost is negligible.

**Extrapolation, not measurement.** At the locally observed exponent of ~3, a 100k-line kernel
would take on the order of two and a half hours, and a 200k-line one a day. Even at the gentler
overall exponent of 2.34, 100k lines is around 1.6 hours. The kernel design's module layout (§7)
plainly implies a program well past 50k lines.

## Verdict

**Does not pass.** The pass criterion quoted verbatim above is *"20k lines compile in under 30
s on the reference machine"*. The measurement is **72.19 s** — 2.41× over.

**Fails, on the reading that the fail criterion applies to the spike as written.** The fail
criterion is *"over 120 s, or the compiler exhausts memory"*. It names no program size, and the
spike sentence it belongs to covers 5k, 20k **and** 50k. The 50k program took **1146.72 s**, 9.6×
the fail threshold. On the narrower reading — that both lines are about the 20k program, since
the pass line names 20k — the 20k figure of 72.19 s sits between the two criteria and the result
is neither a pass nor a fail. **This document applies the first reading and records R-18 as
failed**, because the second reading would leave a 19-minute compile unrecorded as a problem, and
because the fail criterion's own consequence — *"a blocker to fix in dynlex before M1"* — is
exactly what the curve above calls for. If the maintainer prefers the narrow reading, the status
line in `docs/risks.md` should be changed to `in progress` and the criterion rewritten to say
which size it governs; the numbers do not change either way.

**Memory is not the problem.** The fail criterion's second clause — *"the compiler exhausts
memory"* — was not met at any size. 2.8 GB at 50k lines on a 32 GB machine, scaling roughly
linearly.

**Correctness is not the problem either.** Nothing about this result questions what the compiler
produces. It compiled 7052 patterns across 641 classes with no diagnostics and produced a binary
whose output matched an independent computation to the last digit. The defect is a performance
one, in compilation, and it is a *scaling* defect rather than a constant-factor one.

## What this means for ADR-0004

The evidence row *"DynLex compiles kernel-shaped code within the compile-time budget"* is filled
with **measured** evidence, and the evidence is **negative**: 72.19 s for 20k lines against a 30 s
budget, with a superlinear curve that gets steeper. This does not by itself overturn the decision
to build the kernel in DynLex — R-19 passes cleanly, and the compiler is the maintainer's own, so
this is a fixable defect in a tree we control rather than a third party's refusal. But it is a
**blocker to fix in dynlex before M1**, in the fail criterion's own words, and the ADR should not
move to `Accepted` on this row until it is fixed and remeasured.

The useful thing to hand the dynlex side is not the totals but the exponent: the cost is
superlinear in the number of patterns in scope, and the shape suggests pattern resolution or type
inference doing work proportional to the pattern table for each call site. This spike did not
profile the compiler and that sentence is a **hypothesis, not a measurement** — it follows only
from the exponent and from the fact that the generated program's distinguishing feature is a
pattern table that grows with it. Per dynlex's `AGENTS.md` the next step is a minimal reproducer
and a root cause, not a workaround here.

## What this does not settle

- **The compiler was not profiled.** This spike measures wall time and peak memory from outside
  the process. Which phase consumes the time is unknown; the guess above is a guess.
- **One shape of program.** Every unit is a small record with ten arithmetic patterns over it.
  A real kernel also has deep call graphs, long functions, generics-by-pattern, imports across
  many files and error paths. Whether compile time scales with *pattern count*, with *call-site
  count*, with *lines*, or with something else is not separated here — all three grow together in
  the generator. **Separating them is the single most useful follow-up**, and it is cheap: hold
  one constant while varying the others.
- **Single-file programs.** The kernel will be many `.dl` files behind imports. Whether the
  compiler's cost is per-file, per-module or whole-program — and therefore whether incremental or
  separate compilation could rescue the developer loop even if whole-program compilation stays
  slow — is untested and is the question that most changes what the fix has to be.
- **No `-O` flag was passed**, so these numbers exclude the LLVM optimisation time a real kernel
  build will add on top.
- **The 50k figure is a single run.** At 19 minutes it was not repeated. Its exponent is
  therefore derived from one sample and could move by tens of percent.
- **The compiler pin is dirty, and in exactly the phase under test.** See the caveat above.
- **This says nothing about runtime performance**, which passes — see
  [`../dynlex-performance/FINDINGS.md`](../dynlex-performance/FINDINGS.md).
