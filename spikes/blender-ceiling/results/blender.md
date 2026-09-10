# Object-count ceiling — Blender raw results

Produced by [`../blender_driver.py`](../blender_driver.py). Raw data for
[`../../../docs/research/kernels/blender.md`](../../../docs/research/kernels/blender.md)
§Measurements and for `problems.md` P-07. Do not edit by hand — re-run the driver.

**Run date:** 2026-09-10

## Environment

| Item | Value |
|---|---|
| blender | `5.0.0` |
| build hash | `a37564c4df7a` |
| build date | `2025-11-18 11:06:54` |
| platform | `Windows 10.0.26200 (AMD64)` |
| processor | `Intel64 Family 6 Model 183 Stepping 1, GenuineIntel` |
| repeats per incremental timing | 5 (median reported) |
| startup | `--factory-startup`, `--background` (no interface, no drawing) |

**Background mode draws nothing.** Every number below is therefore a *lower bound* on
what an interactive session costs: it excludes the viewport, the outliner and the draw
manager entirely. A ceiling measured here is a ceiling the interface has not yet been
added to.

## Results

Each box is 12 triangles. *Separate* is one mesh datablock and one object per box —
how an IFC importer maps elements. *Single* is the same boxes as disconnected shells
in one mesh, one object. *Incremental* is one `view_layer.update()` after moving a
single object, with everything else untouched: the cost of one drag.

| Objects | Variant | Datablocks (obj / mesh) | Triangles | Build ms | First full eval ms | Incremental ms | Memory |
|---|---|---|---|---|---|---|---|
| 1000 | separate | 1000 / 1000 | 12000 | 46.56 | 38.82 | **1.229** | 81 MB |
| 1000 | single | 1 / 1 | 12000 | 8.171 | 6.326 | **0.0051** | 3 MB |
| 10000 | separate | 10000 / 10000 | 120000 | 493.8 | 472.8 | **16.75** | 619 MB |
| 10000 | single | 1 / 1 | 120000 | 206.6 | 171.8 | **0.0129** | -25 MB |
| 100000 | separate | 100000 / 100000 | 1200000 | 2.675e+04 | 1.002e+04 | **295.3** | 6224 MB |
| 100000 | single | 1 / 1 | 1200000 | 3110 | 1972 | **0.0278** | -407 MB |

## Per-object overhead

The difference between the two variants at the same triangle count, divided by the
object count. Memory per object includes the object, its mesh datablock and the
depsgraph's evaluated copy.

| Objects | Δ build ms | Δ full eval ms | Δ incremental ms | Δ memory / object |
|---|---|---|---|---|
| 1000 | 38.39 | 32.5 | 1.224 | 78328 B |
| 10000 | 287.3 | 301 | 16.73 | 64352 B |
| 100000 | 2.364e+04 | 8048 | 295.2 | 66311 B |

An interactive editor has roughly 16 ms per frame. Which rows above fit inside that,
and which do not, is the whole of R-03's question for the part that is Blender's.

