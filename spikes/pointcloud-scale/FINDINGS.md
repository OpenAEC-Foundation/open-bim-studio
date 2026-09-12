# FINDINGS — P-13 / P-17, where an in-core point cloud library stops fitting

This file adds no measurement. Every number below is copied from a named row of
[`results/open3d.md`](results/open3d.md), which is the reproducible record.

## The question, restated

[`../../docs/research/kernels/problems.md`](../../docs/research/kernels/problems.md) **P-13** said
"point clouds exceed memory — root cause: in-core storage", and marked it a hypothesis. The kernel
spec commits to chunked, memory-mapped point storage with an octree from the first milestone
(§4, §8) on the strength of it. **At what point count does an in-core point cloud library actually
stop fitting on the reference machine, and which part fails first — the storage, or the index over
it?** A second, cheaper question rides along (**P-05**, ADR-0006): **what does float32 storage cost
a point cloud placed 500 km from the origin**, measured rather than derived.

**There is no pass/fail criterion in [`../../docs/risks.md`](../../docs/risks.md) for this spike**
— it is not a risk-register gate. It feeds P-13, P-17 and P-05. The nearest thing to a threshold
is a *target*, not a criterion, in the kernel spec's §10 performance table, quoted verbatim:

> | Build octree over 10⁸ points | < 10 s |

That target is the reference this file measures against, and it is the spec's target rather than
a criterion written before the spike ran.

## Hardware, OS and versions

*Measured*, recorded by the driver ([`results/open3d.md`](results/open3d.md) §Environment):
Open3D `0.19.0` (wheel; matches source tag `v0.19.0`, commit
`1e7b17438687a0b0c1e5a7187321ac7044afe275`); numpy `2.3.5`; psutil `7.2.2`; Python `3.12.10`;
platform `Windows-11-10.0.26200-SP0`; Intel Core i9-14900HX (`Intel64 Family 6 Model 183 Stepping
1`), 32 logical processors; installed RAM `34 049 179 648` bytes — 32 GiB nominal, **34.0 GB** in
the 10⁹-byte units the results file uses. Seed `20260910`, cube extent `100.0` m. **Run date:**
2026-09-10. **Stages:** 15 planned, 15 completed, **0 failed**.

## Model and inputs

No file from [`../../reference/`](../../reference/). The clouds are **synthetic**: uniform random
points in a 100 m cube from `numpy.random.default_rng(20260910)`, generated in 2 000 000-point
chunks into one preallocated `(N, 3)` array, at N = 10⁶, 10⁷, 10⁸.

## Method

[`open3d_driver.py`](open3d_driver.py) in `orchestrate` mode, **one subprocess per stage** so a
stage that dies is still a recorded result rather than a lost orchestrator
([`README.md`](README.md) §How to run). Stages: `construct` (three representations — legacy
`geometry::PointCloud` f64, tensor `t::geometry::PointCloud` f64 and f32), `octree`
(`convert_from_point_cloud`, `size_expand=0.01`), `nn` (`KDTreeFlann` build, 1 000
single-nearest-neighbour queries), `precision` (10⁷ points at (500000, 500000, 0) stored f32 and
f64, read back, offset subtracted). Memory is the OS's own peak working set,
`psutil.Process().memory_info().peak_wset`; bytes/point is the RSS delta across the one measured
call, baseline taken after the source array exists, so it is the library's own allocation.
Nearest-neighbour answers are **verified, not assumed**: 100 of each 1 000 are recomputed by a
chunked f64 brute-force scan in numpy and compared point for point.

## The numbers

*Measured*, copied from [`results/open3d.md`](results/open3d.md).

**§Construction** — all three representations hold 10⁸ points:

| N | Representation | Median build (s) | Bytes/point | Peak RSS (GB) |
|---|---|---|---|---|
| 10⁸ | legacy `geometry::PointCloud` (f64) | 1.7989 | 24.011 | 7.312 |
| 10⁸ | tensor `t::geometry::PointCloud` f64 | 0.5739 | 24.011 | 4.914 |
| 10⁸ | tensor `t::geometry::PointCloud` f32 | 0.2700 | 12.009 | 3.713 |

**§Octree** — `max_depth = 8` throughout:

| N | Repeats | Median build (s) | Bytes/point | Peak RSS (GB) |
|---|---|---|---|---|
| 10⁶ | 3 | 3.072 | 466.555 | 1.006 |
| 10⁷ | 1 | 35.929 | 220.892 | 2.562 |
| 10⁸ | 1 | **324.383** | 102.910 | **13.131** |

(`10⁷` at `max_depth 6`, 3 repeats: 16.515 s, 91.234 bytes/point, 1.867 GB.)

**§Nearest neighbour** — `KDTreeFlann`, which is nanoflann over an `Eigen::MatrixXd` copy:

| N | Index build (s, median) | µs/query | Bytes/point | Peak RSS (GB) | Verified |
|---|---|---|---|---|---|
| 10⁶ | 0.512 | 3.988 | 43.106 | 0.764 | 100 / 100 |
| 10⁷ | 8.721 | 4.861 | 42.580 | 1.579 | 100 / 100 |
| 10⁸ | 177.994 | 6.480 | 41.038 | 9.578 | 100 / 100 |

**§Precision**, 10⁷ points at (500000, 500000, 0) m:

| Quantity | Value (m) |
|---|---|
| Max absolute error, **f32 storage at 500 km** | **0.015624999105895654** |
| Max absolute error, f64 storage at 500 km | 2.9103830456733704e-11 |
| Max absolute error, f32 storage **at the origin** | 3.814696910353632e-06 |
| float32 ULP at 500 000 | 0.03125 |

## Verdict

**Against the spec §10 reference ("Build octree over 10⁸ points < 10 s"): fail, by 32×.** The
build took **324.383 s** — *measured*, single-threaded on one of thirty-two logical processors.

**Against the question as asked, the finding is that nothing ran out of memory, and that is the
result.** *Measured*: all fifteen stages completed, 0 failed. Storage was never the binding term —
an f64 point costs **24.011 bytes**, so 10⁸ of them are 2.40 GB inside a 34.0 GB machine. What
became unusable was the **index**: 324.4 s to build, and **13.131 GB** of peak working set, 38.6 %
of the machine. *Measured*, on the fair like-for-like figure, **the index is 4.3× the data it
indexes** (102.910 / 24.011 = 4.29).

**P-13's stated root cause is therefore refuted and replaced** — *inferred* from the rows above:
the price is paid **per point per level**, because the point's index is appended to every internal
node on its root-to-leaf path as well as to its leaf, a floor of `(max_depth + 1) * sizeof(size_t)`
= 9 × 8 = **72 bytes/point** before any node object exists. A second, independent term: the
nearest-neighbour index **owns a private copy of the coordinates** — of its 41–43 bytes/point,
≈24 is the `Eigen::MatrixXd` duplicate — so a memory-mapped chunk store would be re-materialised
in RAM the moment it is indexed.

**P-17 holds as stated** — *measured*: the 10⁸ octree build ran on one core of thirty-two, in a
library that parallelises other work in the same codebase. This is the number that moved threading
from M7 to M6 in spec §8.

**P-05 / ADR-0006, the precision half** — *measured*: f32 storage at 500 km costs **0.015625 m**,
which is exactly half the float32 ULP at 500 000 and therefore the theoretical worst case of
round-to-nearest, reached to within 5.7 × 10⁻⁸ relative by 3 × 10⁷ coordinates. Against f32 at the
origin the ratio is **4 096 = 2¹²**; against f64 at 500 km it is **5.37 × 10⁸**.

## What this does not settle

- **Open3D 0.19.0 only.** PCL and PDAL are read from source in
  [`../../docs/research/kernels/pointclouds.md`](../../docs/research/kernels/pointclouds.md) and
  are **not measured here** — there is no `results/pcl.md` or `results/pdal.md`, and no PCL
  install was attempted. Nothing about PCL or PDAL may be labelled measured on this spike's
  strength.
- **Disk-backed and memory-mapped storage, streaming, LOD and the GPU path are unmeasured**,
  because Open3D has none of them ([`README.md`](README.md) §What this spike measures).
- **The clouds are uniform random.** Real scan data is spatially clustered, so an octree over it
  has a different node count at the same point count; every octree number here is about the
  *friendly* case and is a lower bound on node count for clustered data at the same depth.
- **The 10⁹ figure in the results file is linear extrapolation, and says so** — ≈103 GB of index
  plus 24 GB of points. Nothing here measures it.
- **Peak-RSS ambiguity on the multi-repeat rows** (10⁶ at depth 8, 10⁷ at depth 6, and the 10⁶ and
  10⁷ nearest-neighbour rows): repeats share one process, so `peak_wset` is a cumulative
  high-water mark rather than any single build's peak. The single-run 10⁸ rows carry no such
  ambiguity.
- **The query column is a batch mean**, not a median over individually timed queries; no per-query
  timing was collected.

## Where this lands

[`../../docs/research/kernels/pointclouds.md`](../../docs/research/kernels/pointclouds.md)
§Measurements; `problems.md` **P-13**, **P-17**, **P-05**; spec §8 (threading moved M7 → M6) and
§10 (the octree row).
