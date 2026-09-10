# Point cloud scale — Open3D raw results

Produced by [`../open3d_driver.py`](../open3d_driver.py) (`orchestrate`). Raw data for
[`../../../docs/research/kernels/pointclouds.md`](../../../docs/research/kernels/pointclouds.md)
§Measurements and for `problems.md` P-13 and P-05. Do not edit by hand — re-run the driver.

**Run date:** 2026-09-10
**Stages:** 15 planned, 15 completed, **0 failed** — no stage ran out of memory or hit its timeout.

## Environment

| Item | Value |
|---|---|
| open3d | `0.19.0` (wheel; matches source tag `v0.19.0`, commit `1e7b17438687a0b0c1e5a7187321ac7044afe275`) |
| numpy | `2.3.5` |
| psutil | `7.2.2` |
| python | `3.12.10` |
| platform | `Windows-11-10.0.26200-SP0` |
| processor | `Intel64 Family 6 Model 183 Stepping 1, GenuineIntel` |
| cpu | `Intel(R) Core(TM) i9-14900HX`, 32 logical processors |
| installed RAM | `34 049 179 648` bytes as the OS reports it — 32 GiB nominal, **34.0 GB** in the 10⁹-byte units used below |
| seed | `20260910` |
| cube extent | `100.0` m |

**Units.** Memory is reported in **GB = 10⁹ bytes** and bytes per point exactly. "Peak RSS" is
`psutil.Process().memory_info().peak_wset` — the OS's own peak working set for the stage's process,
so it cannot be missed between samples. "Bytes per point" is the RSS delta across the single
measured call divided by N; the baseline is taken *after* the source array for that representation
already exists, so it is the library's own allocation and not the input.

**Points.** Uniform random in a 100 m cube from `numpy.random.default_rng(20260910)`, generated in
2 000 000-point chunks into one preallocated `(N, 3)` array.

## Construction

`o3d.geometry.PointCloud(o3d.utility.Vector3dVector(a))` for *legacy*;
`o3d.t.geometry.PointCloud(o3d.core.Tensor(a, dtype))` for the tensor rows. The f32 cast of the
source array is done before the timer starts.

| N | Representation | Repeats | Median build (s) | Bytes/point | Peak RSS (GB) |
|---|---|---|---|---|---|
| 10⁷ | legacy `geometry::PointCloud` (f64) | 5 | 0.1333 | 24.086 | 1.073 |
| 10⁷ | tensor `t::geometry::PointCloud` f64 | 5 | 0.0630 | 24.078 | 0.833 |
| 10⁷ | tensor `t::geometry::PointCloud` f32 | 5 | 0.0231 | 12.089 | 0.473 |
| 10⁸ | legacy `geometry::PointCloud` (f64) | 1 | 1.7989 | 24.011 | 7.312 |
| 10⁸ | tensor `t::geometry::PointCloud` f64 | 1 | 0.5739 | 24.011 | 4.914 |
| 10⁸ | tensor `t::geometry::PointCloud` f32 | 1 | 0.2700 | 12.009 | 3.713 |

All five repeats, 10⁷ points, seconds:

- legacy: 0.11882, 0.13325, 0.13008, 0.14184, 0.14781
- tensor f64: 0.04374, 0.06305, 0.05993, 0.06952, 0.06373
- tensor f32: 0.01979, 0.02346, 0.02394, 0.02314, 0.02281

**All three representations hold 10⁸ points on this machine.** 24.011 bytes/point is
`3 × sizeof(double)` to five significant figures, so `Eigen::Vector3d` and the f64 tensor add no
per-point padding. The legacy row's higher *peak* (7.312 GB against the tensor's 4.914 GB for the
same bytes stored) is `Vector3dVector`'s intermediate copy; the tensor constructor has none.

## Octree

`o3d.geometry.Octree(max_depth=d).convert_from_point_cloud(cloud, size_expand=0.01)`. The source
numpy array is released before the baseline is taken, so bytes/point is the tree alone.

| N | `max_depth` | Repeats | Median build (s) | Bytes/point | Peak RSS (GB) | Root size (m) |
|---|---|---|---|---|---|---|
| 10⁶ | 8 | 3 | 3.072 | 466.555 | 1.006 | 100.99994 |
| 10⁷ | 6 | 3 | 16.515 | 91.234 | 1.867 | 100.99999 |
| 10⁷ | 8 | 1 | 35.929 | 220.892 | 2.562 | 100.99999 |
| 10⁸ | 8 | 1 | **324.383** | 102.910 | **13.131** | 100.99999 |

Repeats where more than one was run, seconds: 10⁶/d8 — 2.106, 3.625, 3.072; 10⁷/d6 — 18.320,
13.554, 16.515. The 10⁷/d8 and 10⁸/d8 rows are **single runs**; at 324 s a repeat was not run.

**The 10⁸ octree did not fail.** It built, in 13.131 GB of peak working set — **38.6 % of the
machine's 34.0 GB** — and 324.4 s on one of 32 cores. That is the P-13 result and it is not the one
the hypothesis predicted: on this machine the wall is *time and headroom*, not an allocation
failure. For comparison, the points themselves cost 4.914 GB, so **the index is 2.7× the data it
indexes**.

Bytes per point **falls** with N at fixed depth (466.6 → 220.9 → 102.9 at 10⁶ → 10⁷ → 10⁸) because
the tree saturates: at depth 8 there are at most 256³ ≈ 16.8 M leaves, so past ~10⁷ points the node
count stops growing and only the per-point index payload does. The floor that per-point payload is
approaching is `(max_depth + 1) × sizeof(size_t)` = 9 × 8 = **72 bytes/point**, because the point's
index is appended to every internal node on its root-to-leaf path as well as to its leaf.

**Extrapolation, stated as extrapolation.** At 102.9 bytes/point the same tree over 10⁹ points
would need ≈103 GB for the index plus 24 GB for the points. Nothing here measures that; it is
linear extrapolation from one data point at saturation, and clustered real-world data would give a
different node count at the same depth.

## Nearest neighbour

`o3d.geometry.KDTreeFlann(cloud)` — which is a **nanoflann** index over an `Eigen::MatrixXd` copy,
despite the class name — then 1 000 calls to `search_knn_vector_3d(q, 1)`.

| N | Repeats | Index build (s, median) | Query (µs, median of 1 000) | Bytes/point | Peak RSS (GB) | Verified |
|---|---|---|---|---|---|---|
| 10⁶ | 3 | 0.512 | 3.988 | 43.106 | 0.764 | 100 / 100 |
| 10⁷ | 3 | 8.721 | 4.861 | 42.580 | 1.579 | 100 / 100 |
| 10⁸ | 1 | 177.994 | 6.480 | 41.038 | 9.578 | 100 / 100 |

Index-build repeats, seconds: 10⁶ — 0.4830, 0.5120, 0.5176; 10⁷ — 8.2495, 8.7210, 8.9477.

**Verification.** For each N, the first 100 of the 1 000 query points were re-solved by a chunked
f64 brute-force scan over the entire cloud in numpy (100 000-point chunks, squared Euclidean
distance, `argmin`). The *point* returned by the index was compared with the point found by the
scan, coordinate for coordinate. **300 of 300 matched across the three sizes; 0 mismatches.** The
index also returned the identical *index*, not merely an equidistant point, in all 300 cases.
Largest nearest-neighbour distance among the verified queries: 1.183 m at 10⁶, 0.520 m at 10⁷,
0.211 m at 10⁸ — consistent with N^(-1/3) in a fixed cube, which is a second, weaker check that the
right cloud was searched.

**The index costs about 41–43 bytes per point on top of the cloud**, of which ≈24 is the
`Eigen::MatrixXd` duplicate of the coordinates and the remainder is nanoflann's own nodes.

## Precision

10⁷ points, the same cube, translated to (500000, 500000, 0) m in f64, stored as an f32 tensor and
as an f64 tensor, read back, and the offset subtracted again. The reference is the untranslated f64
array; the subtraction is exact in f64 at these magnitudes.

| Quantity | Value (m) |
|---|---|
| Max absolute error, **f32 storage at 500 km** | **0.015624999105895654** |
| RMS absolute error, f32 storage at 500 km | 0.0073669208225104685 |
| Max absolute error, f64 storage at 500 km | 2.9103830456733704e-11 |
| Max absolute error, f32 storage **at the origin** | 3.814696910353632e-06 |
| float32 ULP at 500 000 | 0.03125 |
| float64 ULP at 500 000 | 5.820766091346741e-11 |

Half the float32 ULP at 500 000 is 0.015625 m exactly, which is the worst case round-to-nearest
can produce. With 3 × 10⁷ coordinates the sample comes within 5.7 × 10⁻⁸ relative of it, so the
measured maximum is the theoretical bound for practical purposes. The f64 maximum is likewise half
the float64 ULP.

**Ratios, computed from the table above:**

- f32 at 500 km vs f32 at the origin: 0.0156249991 / 3.8146969e-06 = **4 096.0**, i.e. 2¹² — twelve
  binary exponents of range traded for twelve bits of resolution.
- f32 vs f64 at 500 km: 0.0156249991 / 2.9103830e-11 = **5.37 × 10⁸**.

## Raw output

The driver prints one JSON object per stage. `run.jsonl` from this session is not committed —
`python -u open3d_driver.py orchestrate > run.jsonl` reproduces it, and every number in the tables
above is transcribed from it.
