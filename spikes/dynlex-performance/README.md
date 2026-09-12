# `dynlex-performance`

**Question (R-19):** does DynLex run kernel-shaped code at native speed, or does the language
cost enough to invalidate the performance targets the kernel design assumes?

**Pass / fail** are fixed in [`../../docs/risks.md`](../../docs/risks.md) R-19, written before any
workload ran: pass is DynLex within 1.5× of C++ on every workload; fail is over 3× on any.

## The three workloads (plus one diagnostic)

The pass/fail criterion in `../../docs/risks.md` R-19 is decided on three workloads. Each one's
timed region is stated explicitly here because for two of the three it is **not** the arithmetic
alone — the clock starts before generation, so the PRNG draws are inside the measured time
(finding I1 of the review; also recorded in `results/dynlex-performance.md` under *Timed region,
per workload*):

| File pair | Workload | Timed region | Output compared |
|---|---|---|---|
| `tritri.dl` / `tritri.cpp` | Möller–Trumbore ray/triangle (1997) applied edge-wise, 10⁶ random triangle pairs in the unit cube | generation (6 random points per pair) **+** the edge-wise test | count of intersecting pairs |
| `bvh.dl` / `bvh.cpp` | top-down BVH build over 10⁶ random AABBs, median split on the node's longest axis, leaf size 4 | the build only — generation is **outside** the timed region | node count and the root box's six bounds |
| `orient3d.dl` / `orient3d.cpp` | plain f64 `orient3d` (the 4×4 determinant, non-adaptive, no filter) over 10⁷ random point quadruples | generation (4 random points per quadruple) **+** the determinant | count of positive determinants |

A fourth pair, `prng_only.dl` / `prng_only.cpp`, was added for finding I1. It draws the identical
4 sample points (12 doubles) per iteration as `orient3d`, 10⁷ times, and does nothing else in its
timed region. It carries **no pass/fail weight of its own** — R-19's criterion is unchanged and is
still decided on the three workloads above — but `orient3d − prng_only`, measured in the same
interleaved round as `orient3d` (see *Running*, below), gives a *derived* estimate of how much of
orient3d's time is the determinant rather than the PRNG. See `FINDINGS.md` §I1 for the number and
whether it was resolvable above this measurement's noise floor.

`common.dl` and `common.hpp` are the shared prelude: output formatting, the clock, and a
xorshift64\* generator seeded identically in both languages. Both preludes are written
line-for-line against each other so the two programs draw the **same** doubles in the same order.

Each program prints its answers, then the running sum of every random number it drew, then the
final generator state, then the elapsed milliseconds of its timed region. The harness compares
everything except the last line. The input checksum is there so that an accidental agreement on
the answer with different inputs cannot pass as a match.

`empty.dl` / `empty.cpp` are the process start-up baseline for the external wall-time cross-check.
`clock_calibration.dl` measures the tick rate of the `clock()` the workloads time themselves with,
rather than assuming `CLOCKS_PER_SEC` is 1000.

## Running

```bash
python spikes/dynlex-performance/harness.py --dynlex ../dynlex/build/dynlex.exe
```

from this directory (the path is resolved relative to the invocation, so an absolute path is
safest). The harness builds every binary into `build/`, runs each five times, takes the median,
and writes [`results/dynlex-performance.md`](results/dynlex-performance.md). Binaries are not
committed.

The three binaries of a workload are run **round-robin, one each per round**, not five-of-one
then five-of-the-next. This machine's absolute times move by tens of per cent with background
load; interleaving puts that drift on both languages equally instead of on whichever ran first.

DynLex is built at **both** `-O2` and `-O0`: `-O0` is what the compiler emits when no
optimisation flag is given, and the difference between the two is one of this spike's findings.
C++ is `clang++ -O2 -std=c++17`.

**"No flag means `-O0`" is checked, not just asserted (finding M2).** The harness also compiles
`orient3d.dl` with no optimisation flag at all and compares the resulting binary against the
explicit `-O0` build: byte for byte (raw md5), and again after zeroing the linker's embedded PE
build timestamp (`lld` was observed to duplicate that 4-byte timestamp elsewhere in the image, so
a build made a few seconds apart never matches on the raw md5 even when the code is identical).
See *Default build check* in `results/dynlex-performance.md` for both md5 pairs and the neutralised
byte offsets. `dynlex --help`, verbatim, for reference:

```
Usage:
  dynlex <file.dl> [compiler options]
  dynlex <source...>
  dynlex -- <source...>

Compiler options:
  --emit-llvm | --emit-wasm | --emit-spirv
  --emit-completions line:column  --dump-purity
  --shader-stage=vertex|fragment  -O0|-O1|-O2|-O3|-Os|-Oz|-Ofast
  -ffast-math|-fno-fast-math  -ffp-contract=fast|off
  -march=native|<cpu>  -mcpu=<cpu>  -mtune=<cpu>  -mattr=<features>
  -fvectorize|-fno-vectorize  -fslp-vectorize|-fno-slp-vectorize
  -funroll-loops|-fno-unroll-loops
  -o <output>  -g|--debug
  --lsp [--port PORT]  --stdio  --dap  --lsp-trace[=PATH]
  --version  --help
```

No flag among these sets an optimisation level, so its absence falls through to the compiler's own
default — measured as `-O0`, not asserted.

## Rules

Spike code is throwaway (see [`../README.md`](../README.md)). Nothing here is a design proposal
for `kernel/`, and neither language's program may be tuned in a way the other is not.
