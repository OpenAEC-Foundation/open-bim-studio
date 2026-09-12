# `dynlex-scale`

**Question (R-18):** can the DynLex compiler build a kernel-sized program in a time a developer
can sit through? The kernel will be the largest DynLex program written, and compile time sits on
the inner loop of everyone working on it.

**Pass / fail** are fixed in [`../../docs/risks.md`](../../docs/risks.md) R-18, written before the
generator existed: pass is 20k lines under 30 s on the reference machine; fail is over 120 s, or
the compiler exhausting memory.

## What is generated

`generate.py` emits synthetic DynLex in the kernel's style. One *unit* is a point-like record —
a class with three 64-bit floating-point members — and the ten patterns a geometry kernel writes
over such a record:

| | | | |
|---|---|---|---|
| 1 construct | 2 add | 3 scale | 4 dot |
| 5 cross | 6 squared length | 7 compare (returns an ordering) | 8 min/max (componentwise, returns the squared diagonal) |
| 9 lerp | 10 a predicate returning a boolean | | |

Every pattern word carries the unit index (`a point u00042`, `the cross u00042 of …`), so no two
units collide and the compiler's pattern table grows with the program. A trailing `main` calls
every pattern of every unit exactly once and folds the results into one printed number, so
nothing can be dead-code eliminated.

The numeric constants in each unit come from a seeded PRNG — **default seed `20260909`** — so a
given (seed, line count) pair always produces byte-identical source. `generate.py` also
recomputes the number the program should print, in Python IEEE doubles, following the same
operation order; `run.py` compares that against what the compiled binary actually prints. So the
spike checks that the compiler produced a *correct* program, not only that it terminated.

## Running

```bash
python spikes/dynlex-scale/run.py --dynlex ../dynlex/build/dynlex.exe
```

It generates 5k, 20k and 50k line programs into `build/`, compiles each with `-o` five times
(once if the first compile exceeds 90 s), records wall time and the compiler's peak working set
via `psutil`, runs each binary, and writes
[`results/dynlex-scale.md`](results/dynlex-scale.md).

To produce one program by hand:

```bash
python spikes/dynlex-scale/generate.py --lines 20000 --out build/scale_20000.dl
```

Generated `.dl` files and binaries are **not committed** — the generator is deterministic, so
regenerate them with the same seed.

## Rules

Spike code is throwaway (see [`../README.md`](../README.md)). The generated programs are not a
proposal for how `kernel/` should be written; they are a load for the compiler that has the same
shape as kernel code.
