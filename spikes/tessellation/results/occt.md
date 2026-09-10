# Tessellation on the 10k scale model — OCCT raw results

Produced by [`../occt_driver.py`](../occt_driver.py). Raw data for
[`../../../docs/research/kernels/occt.md`](../../../docs/research/kernels/occt.md)
§Measurements. Do not edit by hand — re-run the driver.

**Run date:** 2026-09-10
**Model:** `build/scale_10k.obj` — 10,000 unit boxes from `reference/generate_scale_models.py --count 10000`, parsed in 49 ms.

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
| 1 | single | yes | 243 | 4171 | 120,000 | 34.8 |
| 1 | parallel | yes | 255 | 4732 | 120,000 | 39.4 |
| 0.1 | single | yes | 260 | 4489 | 120,000 | 37.4 |
| 0.1 | parallel | yes | 252 | 4856 | 120,000 | 40.5 |
| 0.01 | single | yes | 255 | 4453 | 120,000 | 37.1 |
| 0.01 | parallel | yes | 258 | 4899 | 120,000 | 40.8 |
| 0.001 | single | yes | 253 | 4741 | 120,000 | 39.5 |
| 0.001 | parallel | yes | 259 | 4804 | 120,000 | 40.0 |

## Control — does the parallel flag work at all?

`OSD_ThreadPool::DefaultPool()->NbThreads()` reports **32** on this machine. The rows
above show the parallel flag costing time rather than saving it on the box model; the rows
below use spheres, where one face is thousands of triangles, to separate "threading does not
work in this build" from "the per-face work is too small to pay for the parallel path".

| Model | Mode | Done? | Mesh ms | Triangles |
|---|---|---|---|---|
| 400 spheres, deflection 0.0005 | single | yes | 77431 | 12,881,600 |
| 400 spheres, deflection 0.0005 | parallel | yes | 8149 | 12,881,600 |

## Probe — is re-meshing an already-meshed shape a no-op?

`BRepMesh` caches a `Poly_Triangulation` on each face, so one shape cannot hold two
qualities at once. This probe uses the first 2,000 boxes of the model: it meshes them
coarse, meshes the **same** shape again at a finer deflection, and compares against a
**rebuilt** compound meshed at the fine deflection. Rows 4–6 repeat the question on a single
sphere, because a planar face meshes to the same two triangles at every deflection and so
cannot show whether the cache was replaced. *Nodes* is the node count of the first face's
cached triangulation.

| Step | Mesh ms | Triangles | Nodes (first face) | Note |
|---|---|---|---|---|
| 1. mesh fresh compound at 1 | 901 | 24,000 | 4 | - |
| 2. mesh the **same** shape again at 0.001 | 894 | 24,000 | 4 | first face's triangulation unchanged: yes |
| 3. mesh a **rebuilt** compound at 0.001 | 914 | 24,000 | 4 | - |
| 4. one sphere, meshed at 0.1 | 0.9 | 306 | 168 | - |
| 5. the **same** sphere, meshed again at 0.001 | 32.2 | 10,108 | 5106 | cached triangulation **replaced** |
| 6. the same sphere, back to 0.1 | 0.2 | 10,108 | 5106 | **fine mesh kept — a coarser request is ignored** |
