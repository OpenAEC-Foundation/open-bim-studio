# `dynlex-performance`

**Question (R-19):** does DynLex run kernel-shaped code at native speed, or does the language
cost enough to invalidate the performance targets the kernel design assumes?

**Pass / fail** are fixed in [`../../docs/risks.md`](../../docs/risks.md) R-19, written before any
workload ran: pass is DynLex within 1.5× of C++ on every workload; fail is over 3× on any.

## The three workloads

| File pair | Workload | Output compared |
|---|---|---|
| `tritri.dl` / `tritri.cpp` | Möller–Trumbore ray/triangle (1997) applied edge-wise, 10⁶ random triangle pairs in the unit cube | count of intersecting pairs |
| `bvh.dl` / `bvh.cpp` | top-down BVH build over 10⁶ random AABBs, median split on the node's longest axis, leaf size 4 | node count and the root box's six bounds |
| `orient3d.dl` / `orient3d.cpp` | plain f64 `orient3d` (the 4×4 determinant, non-adaptive, no filter) over 10⁷ random point quadruples | count of positive determinants |

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

## Rules

Spike code is throwaway (see [`../README.md`](../README.md)). Nothing here is a design proposal
for `kernel/`, and neither language's program may be tuned in a way the other is not.
