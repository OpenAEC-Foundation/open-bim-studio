# `pointcloud-scale`

**Question (P-13):** `problems.md` P-13 says "point clouds exceed memory — root cause: in-core
storage", and marks it a hypothesis. The kernel spec commits to chunked, memory-mapped point
storage with an octree from the first milestone (§4, §8) on the strength of that hypothesis.
**At what point count does an in-core point cloud library actually stop fitting on the reference
machine, and which part of it fails first — the storage, or the index over it?**

**The answer at 10⁸ points on this machine is "neither, and that is the finding":** nothing ran out
of memory, and what became unusable was the index *build time* (324 s single-threaded) and the
index's *share of RAM* (13.1 GB, 2.7× the points). The results file says so plainly rather than
reporting a failure that did not occur.

A second, cheaper question rides along (P-05, ADR-0006): **what does float32 storage cost a point
cloud placed 500 km from the origin**, measured rather than derived.

## What this spike measures, and what it does not

It measures **Open3D 0.19.0** only. PCL and PDAL are documented from source in
[`../../docs/research/kernels/pointclouds.md`](../../docs/research/kernels/pointclouds.md) and are
not measured here; there is no `results/pcl.md` or `results/pdal.md`, and the note says so rather
than implying the comparison is complete.

Open3D is the right single subject for this question because it offers **three** storage
representations of the same points in one process — the legacy `geometry::PointCloud`
(`std::vector<Eigen::Vector3d>`, f64), and the tensor `t::geometry::PointCloud` in f32 and f64 —
so the cost of a representation choice can be isolated from the cost of a library choice.

What it does **not** measure: disk-backed or memory-mapped storage (Open3D has none), streaming
(Open3D has none), LOD (Open3D has none), and the GPU path. Those are read from PDAL's and
Potree's source in the note, not measured.

The clouds are **synthetic**: uniform random points in a 100 m cube from a fixed seed. Real scan
data is spatially clustered, so an octree over it has a different node count for the same point
count. Every octree number here is therefore about the *uniform* case, which is the friendly one
for a fixed-depth tree, and is a lower bound on the node count for clustered data at the same
depth.

## Layout

```
open3d_driver.py       the driver; each stage runs in its own process
results/open3d.md      raw results, one table per stage
```

## How to run

```
python -m pip install open3d==0.19.0 psutil     # numpy arrives with open3d
cd spikes/pointcloud-scale
python -u open3d_driver.py orchestrate > run.jsonl
```

`orchestrate` runs the fixed `PLAN` at the bottom of the driver, one subprocess per stage, and
prints one JSON object per line. A stage that runs out of memory, crashes or exceeds its timeout
is recorded as `"failed": true` with the tail of its stderr — **for this question a stage that
dies is a result**, and losing it to a crashed orchestrator would lose the answer. `run.jsonl` is
not committed; `results/open3d.md` is transcribed from it.

Single stages can be run directly, which is how to reproduce one number:

```
python open3d_driver.py octree --n 10000000 --depth 8 --repeats 1
python open3d_driver.py precision --n 10000000
```

## What each stage does

| Stage | What it answers |
|---|---|
| `env` | interpreter, library and machine versions, recorded in the results file |
| `construct` | bytes per point and construction time for each of the three representations, at 10⁷ and 10⁸ |
| `octree` | `o3d.geometry.Octree.convert_from_point_cloud` build time and bytes per point at a stated `max_depth` |
| `nn` | `o3d.geometry.KDTreeFlann` index build, 1 000 single-nearest-neighbour queries, and a brute-force check of 100 of them |
| `precision` | the same 10⁷ points stored f32 and f64 at (500000, 500000, 0), compared against the exact local-frame coordinates |

**The nearest-neighbour answers are verified, not assumed.** 100 of the 1 000 query results are
recomputed with a chunked f64 brute-force scan in numpy over the whole cloud, and the *point*
returned by the index must equal the point found by the scan. A timing whose answers were never
checked measures nothing in particular.

**Memory is the OS's peak working set**, read from `psutil.Process().memory_info().peak_wset` —
the peak the kernel itself recorded, so no sampling thread can miss a spike. Each stage also
reports the RSS delta across the one call being measured, taken after the source array for that
representation already exists, so the delta is the library's own copy and not the input.
