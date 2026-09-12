# FINDINGS — R-19, DynLex runtime performance against C++

## The question, restated

Does DynLex run kernel-shaped code — triangle/triangle intersection, a BVH build, an f64
`orient3d` loop — at native speed, or does the language cost enough to invalidate the
performance targets in
[`../../docs/superpowers/specs/2026-09-09-geometry-kernel-design.md`](../../docs/superpowers/specs/2026-09-09-geometry-kernel-design.md)
§10, which assume native-speed code?

The pass/fail criteria were written before any workload ran and are quoted verbatim from
[`../../docs/risks.md`](../../docs/risks.md) R-19:

> - **Spike:** `spikes/dynlex-performance/` — triangle–triangle intersection over 10⁶ random
>   pairs, BVH build over 10⁶ boxes, and an f64 orient3d loop, each in DynLex and C++ -O2.
> - **Pass:** DynLex within 1.5× of C++ on every workload.
> - **Fail:** over 3× on any — a codegen issue to root-cause in dynlex before M1.

Every number below is copied from a named row of
[`results/dynlex-performance.md`](results/dynlex-performance.md). The original three workloads were
measured on 2026-09-11; the results file was regenerated on 2026-09-12 (fix round 1, findings I1,
M2, M4) to add the `prng_only` diagnostic, the timestamp-neutralised default-build check, and the
joint orient3d/prng_only interleaving the derived ratio in finding I1 depends on. All numbers below
are from that regeneration, on the same machine.

## Hardware, OS and versions

*Measured.* Recorded from `Get-CimInstance` and each tool's own `--version`.

| | |
|---|---|
| CPU | `Intel(R) Core(TM) i9-14900HX` (32 logical processors) |
| RAM | 32 GB |
| OS | Windows 11 Pro, `10.0.26200` |
| DynLex | `dynlex.exe --version` → `0.0.3`, binary built 2026-09-09 |
| DynLex commit | `7cacbc97f0cc2fdbe72bdbd310129bbc2da228cd` (`master`) **plus uncommitted compiler edits — see the caveat below** |
| C++ | `clang++` 19.1.1, target `x86_64-w64-windows-gnu` (WinLibs POSIX UCRT LLVM build) |
| Python (harness) | 3.12.10 |

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
**7cacbc9 plus those uncommitted edits as they stood at build time**, not 7cacbc9 itself. All the
edits are in type inference and none touch codegen, so the runtime numbers are unlikely to move;
that is an inference, not a measurement. When `metadata/DYNLEX_COMMIT` is created at M0 it must
pin a clean commit, and these numbers should be reproduced against it.

## Which reference model was used

**None.** [`../README.md`](../README.md) asks which model from `../../reference/` a spike used;
this spike uses no model. Its inputs are synthetic: uniform random points and boxes from a
xorshift64\* generator seeded with 88172645463325252, generated identically in both languages. The
question is about code generation, not about geometry that occurs in buildings. That the inputs
are unrealistic is a limitation recorded under *What this does not settle*.

## Method

Three workloads decide R-19's pass/fail criterion, each written twice — once in DynLex, once in
C++ — over a shared prelude (`common.dl` / `common.hpp`) written line-for-line against itself. A
fourth, diagnostic-only workload (`prng_only`) was added afterwards for finding I1; it carries no
pass/fail weight of its own and is described separately below.

**Timed region, disclosed for all three (finding I1).** Each workload's `started .. finished`
window is stated explicitly here, because for two of the three it is *not* the arithmetic alone —
the same table is in `results/dynlex-performance.md` under *Timed region, per workload*:

1. **Triangle/triangle**, 10⁶ pairs of random triangles in the unit cube. The test is
   **Möller–Trumbore ray/triangle (1997) applied edge-wise** — the six edges of the two triangles
   taken as segments against the opposite triangle, with the ray parameter constrained to [0, 1].
   It is *not* the full Möller 1997 tri-tri overlap test and it does not detect coplanar overlap.
   Both languages run exactly this test. Output: the count of intersecting pairs. **Timed region:
   generation (six random points per pair) together with the edge-wise test — not the test alone.**
2. **BVH build**, 10⁶ random AABBs (uniform centres in the unit cube, half-extents up to 0.01).
   Top-down, median split on the longest axis of the node's own bounding box, leaf size 4. The
   median is found by a Hoare-partition quickselect whose pivot is the centroid of the middle
   element of the range — deterministic, so the tree is identical in both languages. Output: node
   count and the root box's six bounds. **Timed region: the build only; generation is outside it —
   the one workload of the three where the disclosure was already made.**
3. **orient3d**, 10⁷ random point quadruples. The plain 4×4 determinant in Shewchuk's
   translated-to-`d` form, non-adaptive, no error bound and no exact fallback. Output: the count
   of positive determinants. **Timed region: generation (four random points per quadruple)
   together with the determinant — not the determinant alone.** Roughly half of the reported time
   is generation, not arithmetic — see *PRNG-only baseline* under Results.

**PRNG-only baseline (`prng_only.dl` / `prng_only.cpp`), added for finding I1.** Draws the
identical 4 sample points (12 doubles) per iteration as orient3d, 10⁷ times, and does nothing
else in its timed region — no arithmetic on the draws beyond the generator itself. Its only
purpose is to be subtracted from orient3d's time to estimate the determinant-only share; it has no
pass/fail criterion of its own. Measured the same way as the other three (five runs, median), and
— because the subtraction only means something if both sides are free of independent drift —
interleaved in the *same* round-robin as orient3d's three binaries rather than in a separate
measurement pass. See *Results* below for the derived figure and whether it was resolvable.

**Same inputs, verified not assumed.** Both preludes implement the same xorshift64\* (Marsaglia
xorshift64, Vigna's 2685821657736338717 multiplier), seeded with the same constant, drawing
doubles as `(bits >> 11) * 2⁻⁵³`. Each program prints, alongside its answer, the running sum of
every random number it drew and the final generator state. The harness compares all of those
between the languages, so an accidental agreement on the answer with different inputs cannot pass
as a match.

**Timing.** Each program times its own region with libc `clock()`. Both languages call libc
`clock()`, and the external wall-time cross-check confirms they measure the same thing.
`CLOCKS_PER_SEC` is 1000 on this toolchain — not assumed but
measured, by `clock_calibration.dl`: a fixed-result loop timed by `clock()` and by an external
stopwatch at once. The *Clock calibration* table's ten rows read between 793.4 and 1006.8 ticks
per second, and the readings converge on 1000 from below as the runs settle (1005.0 and 1006.8 for
`-O2`; 1000.9 and 1000.6 for `-O0`). The low readings are the external stopwatch running longer
than the tick count, which is what a descheduled process looks like — so `clock()` here is closer
to process CPU time than to wall time. That does not affect the comparison: it is the same
function, on the same runtime, in both languages, and the ratios are what R-19 asks about. As a
further cross-check the harness measures whole-process wall time with `time.perf_counter` and
subtracts an empty-program baseline; the *Cross-check* table agrees with the internal clock
throughout.

**Flags.** C++ is `clang++ -O2 -std=c++17`, as R-19 specifies. DynLex is built twice:

- `-O2`, the like-for-like comparison;
- **with no optimisation flag at all**, which the task brief called "the default optimised
  build". It is not optimised: `ParseContext::Options::optimizationLevel` defaults to `0`
  (`src/cpp/compiler/parseContext.h:115`), so an unflagged `dynlex file.dl -o out` emits `-O0`
  code. The dynlex README's "the normal build is optimized" describes how the *compiler* is
  built, not what it emits. Both figures are reported.

Neither side passes `-ffast-math`, `-march=native` or LTO. DynLex defaults to
`-ffp-contract=off`; clang's C++ default is `-ffp-contract=on`, and it was left at its default
because the outputs came out bit-identical anyway, which is the stronger evidence.

Five runs per binary, the three binaries of a workload interleaved round-robin; the median is
reported.

## Results

From *Workload timings* in [`results/dynlex-performance.md`](results/dynlex-performance.md). The
first three rows decide R-19; the fourth (`prng_only`) is the diagnostic added for finding I1 and
carries no pass/fail weight of its own:

| Workload | DynLex `-O2` | C++ `-O2` | ratio | DynLex unflagged (`-O0`) | ratio | outputs equal? |
|---|---:|---:|---:|---:|---:|---|
| Triangle/triangle, 10⁶ pairs | 87 ms | 78 ms | **1.12×** | 709 ms | 9.09× | yes |
| BVH build, 10⁶ boxes | 422 ms | 344 ms | **1.23×** | 2331 ms | 6.78× | yes |
| orient3d f64, 10⁷ quadruples | 155 ms | 153 ms | **1.01×** | 3235 ms | 21.14× | yes |
| PRNG-only baseline, 1.2×10⁸ doubles (diagnostic, finding I1) | 146 ms | 145 ms | 1.01× | 2957 ms | 20.39× | yes |

**Every output is bit-identical between the two languages**, at both DynLex optimisation levels:
279981 intersecting pairs; 524287 BVH nodes with a root box of
`[-0.0099878586160846734, -0.0098409882633637286, -0.0099019173479688079]` to
`[1.0098144316894508, 1.0099266545715151, 1.009858090198223]`; 5002121 positive determinants.
The input checksums and final generator states match too — see *Output equality* in the results
file.

**On the orient3d tie, and what finding I1 says about it.** The five runs were DynLex 155, 153,
160, 155, 149 ms against C++ 151, 154, 151, 153, 155 ms — the distributions overlap almost
completely, and 1.01× reads as a tie. But orient3d's timed region is generation **and** the
determinant, not the determinant alone (see *Timed region, disclosed for all three* above), so
**this 1.01× is a mixed PRNG+determinant figure**, not evidence about the determinant in
isolation. `prng_only` isolates the generation share: 146 ms (DynLex) / 145 ms (C++) — almost the
whole of orient3d's 155/153 ms. Subtracting, measured in the same interleaved round so machine-load
drift cancels rather than leaking into the subtraction (see *Derived* in the results file):

| | DynLex `-O2` | C++ `-O2` |
|---|---:|---:|
| orient3d (generation + determinant) | 155 ms | 153 ms |
| prng_only (generation only) | 146 ms | 145 ms |
| **derived: determinant only** | 9 ms | 8 ms |

**Derived determinant-only ratio: 1.12×** (9/8) — *derived*, not a direct measurement, and it does
not exceed the 1.5× line. It rests on a 9 ms and an 8 ms figure at a 1 ms clock, so it carries much
more relative noise than the whole-workload figures above; five repeated regenerations of this
subtraction during this fix round gave 11/9 (1.22×), −17/25 (unusable — negative on one side), 12/−2
(unusable), 17/0 (unusable), 6/6 (1.00×) and finally 9/8 (1.12×, the one committed here). Three of
those six could not be resolved to a ratio at all, because `orient3d − prng_only` came out zero or
negative on one side — a physical impossibility, since orient3d strictly does more work than
prng_only per iteration, and therefore read as the determinant's absolute cost (roughly 5–15 ms
out of a ~150 ms total) sitting at or below this measurement's noise floor rather than as evidence
the determinant costs nothing. **In every regeneration that did resolve, the derived ratio stayed
under 1.5×** (1.00×, 1.12×, 1.22×), so nothing here contradicts the pass verdict below — but the
number should be read as "small and consistent with parity," not as a precise 1.12×.

**On run-to-run variance generally.** This machine's absolute times move by tens of per cent with
background load — the same `clock_calibration.dl` loop's `-O2` runs were timed between 0.21 s and
0.27 s in the committed results file (see *Clock calibration* there). That is why the three
binaries of each workload (six for orient3d/prng_only together, see above) are run **round-robin,
one each per round** rather than five-of-one-then-five-of-the-next: drift then falls on both
languages equally instead of being attributed to whichever ran first. The whole-workload ratios
are consequently much more stable than the absolute milliseconds, even though the derived
determinant-only subtraction above is not. *Observed, not recorded:* the harness was regenerated
several times during this spike and again during this fix round as it was being written, at
absolute times varying by about 30%, and no whole-workload ratio left the range 1.0–1.3 in any of
them. Only the final regeneration is the committed results file; the others are not evidence you
can check, and are mentioned only because the stability of the whole-workload ratios against
unstable absolute times — contrasted with the instability of the small derived subtraction above —
is itself part of the finding.

## Verdict

**Pass**, against the criterion quoted verbatim above — *"DynLex within 1.5× of C++ on every
workload"* — but only when DynLex is given `-O2` explicitly, and evaluated on the criterion's own
literal terms (whole-workload timings, not the derived determinant-only subtraction). 1.12×, 1.23×
and 1.01×; the worst is 1.23×. Nothing is near the *"over 3× on any"* fail line. **The orient3d
1.01× is a mixed PRNG+determinant figure** (finding I1) — most of that workload's time is
generation, not the determinant — and the *derived*, noise-sensitive determinant-only ratio is
~1.0–1.2× across the regenerations that resolved it, which does not exceed 1.5× and does not change
this verdict.

**With no optimisation flag DynLex would fail the criterion on all three workloads** (9.09×,
6.78×, 21.14×), well past the fail line. This is not a codegen defect; it is the documented
meaning of `-O0`. It matters only because the phrase "the default optimised build" is wrong about
this compiler, and any future measurement that omits the flag will produce a false failure.
**The kernel's build must pass an explicit `-O` flag.** This is now checkable in-repo, not only
asserted: see *Default build check* in the results file, where a no-flag build of `orient3d.dl` is
compiled, run, and compared against the explicit `-O0` build. The raw md5s differ — `lld` embeds a
PE COFF build timestamp that differs by a couple of seconds between the two compiles, duplicated at
one further offset in the image — but after zeroing every span that matches that timestamp, the two
binaries are md5-identical, which is stronger evidence of "no flag emits `-O0`" than the timing
argument above ever was.

## What this means for ADR-0004

This fills the evidence row *"DynLex runs kernel-shaped code within 1.5× of C++ -O2"* with
**measured** evidence: 1.23× worst case across three workloads, with bit-identical results. On
this evidence the language is not the obstacle to the §10 performance targets.

## Language facilities that were missing

Recorded here because §8 of the kernel design spec keeps the list of required DynLex extensions,
and because a missing facility is an R-19-relevant finding in its own right. None of these
blocked a workload; each was expressed another way, identically in both languages, and each
substitution is noted in the source.

| Missing | What happened | How the workload was written instead |
|---|---|---|
| **Unsigned integers / a logical right shift** | `shift right` lowers to LLVM `ashr` (`src/cpp/compiler/codegen/codegenIntrinsics.cpp:340`); confirmed at runtime — `(0 - 8) as a 64 bit integer >> 1` prints `-4`. There is no unsigned integer type. xorshift64\* needs a logical shift. | `value logically shifted right by n` in `common.dl` masks the sign-extended bits off: `(value >> n) & ((1 << (64 - n)) - 1)`. The sequence is bit-identical to the C++ `uint64_t` version, verified against an independent Python reference. Signed wrapping multiply reproduces the unsigned multiply exactly. |
| **Scientific-notation float literals** | `1.0e-16`, `1.1102230246251565e-16` and `1e-16` are all rejected. The first two give `Error: This pattern couldn't be resolved`; `1e-16` gives the more confusing `No overload matches call 'print real 1e'`, so the lexer takes `1e` as a token. A 53-digit plain decimal *is* accepted and parses exactly. | `the unit scale` is `(1.0 / 9007199254740992.0)` — 2⁻⁵³ as an exact division of two exactly representable doubles. The C++ side is written the same way rather than as `0x1.0p-53`. |

Two further language properties — not defects, but they cost time and are worth writing down for
whoever writes the kernel: **variable names are single tokens** (`set rng state to 5` is a
pattern-resolution error; `set rngstate to 5` compiles), and **integer literals default to 32
bits**, so a 64-bit context needs `as a 64 bit integer` on the literal. The diagnostic for the
latter is good: `No overload matches call 'the fib of 30' for argument types [a 32-bit integer]`.

**No compiler crash, hang, wrong-code bug or internal error was seen in this spike.** Every
diagnostic encountered was a genuine error in the `.dl` source. The one warning class the
workloads triggered — `Expression 'set leftchild to -1 as a 64 bit integer' has multiple valid
operand groupings` — is correct, both groupings are equivalent here, and it was silenced by
writing `(0 - 1)`.

## What this does not settle

- **Three workloads are not a kernel.** All three are flat, branch-light, cache-friendly f64
  arithmetic over small records — the part of a kernel most likely to compile well. Nothing here
  exercises the boolean pipeline, tolerance handling, string or error paths, or deep data
  structures with pointer chasing.
- **Nothing here is parallel or SIMD.** §6 of the kernel design rests on `parallel for` and on
  SIMD codegen for f64 aggregates, neither of which exists or was measured. §8 lists them as
  extensions; this spike says nothing about whether they will land at native speed.
- **The inputs are synthetic and uniform.** Real BVH inputs are clustered and real triangle pairs
  are mostly far apart or nearly coplanar. Branch-prediction behaviour on real data may differ,
  and it may differ *unequally* between the two compilers.
- **One machine, one session, one C++ compiler.** A different C++ compiler, or
  `-O3`/`-march=native`/LTO — all of which the dynlex repository's own collatz benchmark explored
  — would move the baseline.
- **The compiler pin is dirty.** See the caveat above.
- **The BVH workload stores and loads whole node records the same way in both languages** rather
  than the way each language would naturally express it. That is deliberate — it is what keeps
  the comparison like-for-like — but it means neither figure is the best that language could do.
- **This says nothing about R-18.** Compile time at kernel scale is a different measurement; see
  [`../dynlex-scale/FINDINGS.md`](../dynlex-scale/FINDINGS.md).
