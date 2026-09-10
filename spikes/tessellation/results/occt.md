# Tessellation on the 10k scale model — OCCT raw results

Produced by [`../occt_driver.py`](../occt_driver.py). Raw data for
[`../../../docs/research/kernels/occt.md`](../../../docs/research/kernels/occt.md)
§Measurements. Do not edit by hand — re-run the driver.

**Run date:** 2026-09-10
**Model:** `build/scale_10k.obj` — 10,000 unit boxes from `reference/generate_scale_models.py --count 10000`, parsed in 48 ms.

## Environment

| Item | Value |
|---|---|
| python | `3.12.10` |
| platform | `Windows 11 (AMD64)` |
| processor | `Intel64 Family 6 Model 183 Stepping 1, GenuineIntel` |
| cadquery-ocp | `8.0.1.0.0` |
| occt | `8.0.1 (bundled by cadquery-ocp 8.0.1.0.0)` |

## Results

*Linear deflection* is `BRepMesh_IncrementalMesh`'s `theLinDeflection`, in model units
(the boxes are 1 unit on a side). Angular deflection is 0.5 rad throughout and is
irrelevant here — the model is entirely planar, which is why the triangle count is
constant and the deflection changes only the time.

| Linear deflection | Mode | Done? | Build ms | Mesh ms | Triangles | µs / triangle |
|---|---|---|---|---|---|---|
| 1 | single | yes | 246 | 4218 | 120,000 | 35.2 |
| 1 | parallel | yes | 249 | 4634 | 120,000 | 38.6 |
| 0.1 | single | yes | 248 | 4488 | 120,000 | 37.4 |
| 0.1 | parallel | yes | 258 | 4649 | 120,000 | 38.7 |
| 0.01 | single | yes | 249 | 4523 | 120,000 | 37.7 |
| 0.01 | parallel | yes | 255 | 4587 | 120,000 | 38.2 |
| 0.001 | single | yes | 243 | 4606 | 120,000 | 38.4 |
| 0.001 | parallel | yes | 265 | 4724 | 120,000 | 39.4 |

## Control — does the parallel flag work at all?

`OSD_ThreadPool::DefaultPool()->NbThreads()` reports **32** on this machine. The rows
above show the parallel flag costing time rather than saving it on the box model; the rows
below use spheres, where one face is thousands of triangles, to separate "threading does not
work in this build" from "the per-face work is too small to pay for the parallel path".

| Model | Mode | Done? | Mesh ms | Triangles |
|---|---|---|---|---|
| 400 spheres, deflection 0.0005 | single | yes | 76245 | 12,881,600 |
| 400 spheres, deflection 0.0005 | parallel | yes | 7783 | 12,881,600 |
