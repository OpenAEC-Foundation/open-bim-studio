# Point clouds — PCL, Open3D, PDAL and Potree

**Decision question:** The kernel spec commits the `pointcloud` module to chunked
structure-of-arrays storage with an octree, LOD streaming and memory-mapped chunks
([spec](../../superpowers/specs/2026-09-09-geometry-kernel-design.md) §4, §6, §8) — a design
proposed before any of it was measured. **Does an existing point cloud library already do this
well enough to be the module (build on), which parts of these four designs should ours copy
(borrow from), and which of their choices produce the failures `problems.md` P-13 and P-05
describe (avoid)?**

**Serves:** kernel spec §4 (point cloud representation: chunked SoA, octree, LOD), §6 (spatial
indexing, parallelism), §8 (memory-mapped allocation); [`problems.md`](problems.md) **P-13**
(root cause replaced) and **P-05** (measurement and a third storage option added);
[`../../domain/spatial-model.md`](../../domain/spatial-model.md) (tiles as a paging strategy)

**Note on the ADRs.**
[ADR-0005](../../architecture/decisions/0005-multi-representation-kernel.md)'s evidence table
carries four claims — about single-representation kernels, explicit conversions, the exact mesh
arrangement, and "Implicit representation earns its place" — and **none of them is about the
point cloud representation**.
[ADR-0006](../../architecture/decisions/0006-f64-local-coordinates-in-tile-frames.md)'s table
cites `spikes/precision-set/FINDINGS.md` for "float32 local coordinates fail the precision set",
which is a mesh measurement. **This note does not silently fill either gap.** It supplies the
point-cloud evidence both would need — §Precision for ADR-0006's claim, §Storage and §The index
for a point-cloud row ADR-0005 does not yet have — and whoever amends those ADRs should add the
rows explicitly rather than treat this paragraph as one.

**Status:** draft
**Author:** research programme, phase 2
**Last updated:** 2026-09-10

> **Four subjects, two kinds.** PCL, Open3D and PDAL are *libraries* that could conceivably be
> the kernel's point cloud module, and are scored for *build on*. Potree is not a library at all —
> it is a converter and a web viewer — and is present only as a **design reference** for the
> out-of-core octree, so its *build on* row says "not applicable" with a reason rather than being
> scored. Several criteria in the [README](README.md) matrix (boolean robustness, IFC coverage,
> 2D derivation, incremental evaluation of a parametric model) are about a *modelling kernel* and
> genuinely do not apply to a point cloud library; those rows say so and say why, rather than
> being silently dropped.
>
> **Only Open3D was measured.** PCL, PDAL and Potree are read from source at a pinned tag. There
> is no `spikes/pointcloud-scale/results/pcl.md` or `results/pdal.md`, and nothing below claims a
> measured comparison between libraries.

---

## Summary

The kernel spec's point cloud design is right about the two things that matter and can be made
much more specific by copying Potree's converter — but P-13's *stated* root cause turns out to
be wrong, and the measurement is what shows it. **Measured**, Open3D's in-core array of 10⁸
points costs 24.0 bytes per point and fits easily in 34.0 GB of RAM (4.91 GB peak); its depth-8
octree over the same points also fits, at 13.13 GB — but takes **324 s on one of thirty-two
cores** and is **2.7× the size of the data it indexes**. Nothing ran out of memory. So P-13's
root cause is not "in-core storage": it is *an in-core index whose cost is paid per point per
level*, and what it breaks first at 10⁸ is interactivity, not allocation. **Measured**, the same
10⁷ points stored as float32 at 500 km from the origin lose 0.015625 m — half a float32 ULP at
that magnitude, the worst case round-to-nearest allows — against 2.9 × 10⁻¹¹ m in f64, and a
factor of 4 096 worse than the same f32 storage at the origin; that settles the ADR-0006 storage
question for point clouds as firmly as [`blender.md`](blender.md) and [`manifold.md`](manifold.md)
settled it for meshes. **Read from source**, PCL stores xyz as `float data[4]` (16 bytes, 4 of
them padding, all single precision) and a PCL member states plainly on the tracker that the
library "is designed for float/single precision"; PDAL stores XYZ as `double` and already ships
both a row-major and a **per-dimension chunked** point table, which is the kernel spec's
structure-of-arrays with a block size to cite; and PotreeConverter's octree is a *partition* of
the point set — a point accepted into a parent is removed from its child — so an LOD hierarchy
over N points stores exactly N points, not a pyramid of copies. That last fact is the single
most valuable thing in this note.

## What was read, and at which commit

| Project | Pinned at | Commit | Obtained with |
|---|---|---|---|
| PCL | tag `pcl-1.15.1` (released 2025-08-26) | [`3346843ea6b97697a1577293aa9cdf236b5c7ffb`](https://github.com/PointCloudLibrary/pcl/tree/3346843ea6b97697a1577293aa9cdf236b5c7ffb) | `git clone --depth 1 --branch pcl-1.15.1`, confirmed with `git rev-parse HEAD` |
| Open3D | tag `v0.19.0` (released 2025-01-08) | [`1e7b17438687a0b0c1e5a7187321ac7044afe275`](https://github.com/isl-org/Open3D/tree/1e7b17438687a0b0c1e5a7187321ac7044afe275) | `git clone --depth 1 --branch v0.19.0`; the same version as the measured `open3d` 0.19.0 wheel |
| PDAL | tag `2.10.2` (released 2026-06-12) | [`27008f6241be44585c866a29dfc13bb16d678dab`](https://github.com/PDAL/PDAL/tree/27008f6241be44585c866a29dfc13bb16d678dab) | `git clone --depth 1 --branch 2.10.2` |
| Potree (viewer) | tag `1.8.2` (released 2023-12-12) | [`3013577379b5c8530ebca3cdc980f7585ae2320f`](https://github.com/potree/potree/tree/3013577379b5c8530ebca3cdc980f7585ae2320f) | `git clone --depth 1 --branch 1.8.2` |
| PotreeConverter | tag `2.1.3` (released 2026-06-22) | [`a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7`](https://github.com/potree/PotreeConverter/tree/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7) | `git clone --depth 1 --branch 2.1.3` |

Each tag is the project's latest GitHub release at time of writing, taken from
`gh api repos/<org>/<repo>/releases/latest`. Note the spread: PotreeConverter and PDAL are current
(2026), PCL and Open3D are a year old, and the Potree **viewer** has not had a release since
2023-12 — the converter and the viewer are maintained at very different rates, which matters for
the maturity row below.

**The papers were not read for this note.** PotreeConverter's README names two publications as the
basis of the design — Schütz's *Potree: Rendering Large Point Clouds in Web Browsers* (2016) and
Schütz, Ohrhallinger and Wimmer's *Fast Out-of-Core Octree Generation for Massive Point Clouds*
(2020) — and they are listed under Sources for provenance. **Every design statement below about
Potree comes from the source at the pinned tag**, not from the papers, so that no claim rests on a
paper this note did not open.

## Storage: what one point costs

This is the whole of P-13, and the four projects give four different answers.

### PCL — array of structs, float32, 16 bytes for a 12-byte payload

`pcl::PointCloud<PointT>` is a `std::vector` of the point struct:

- [`common/include/pcl/point_cloud.h#L395-L396`](https://github.com/PointCloudLibrary/pcl/blob/3346843ea6b97697a1577293aa9cdf236b5c7ffb/common/include/pcl/point_cloud.h#L395-L396) —
  `/** \brief The point data. */` on one line, then
  `std::vector<PointT, Eigen::aligned_allocator<PointT> > points;` on the next

The point struct itself is generated by a macro, and the macro is where the two design decisions
live — single precision, and a fourth padded component for SSE:

- [`common/include/pcl/impl/point_types.hpp#L211-L219`](https://github.com/PointCloudLibrary/pcl/blob/3346843ea6b97697a1577293aa9cdf236b5c7ffb/common/include/pcl/impl/point_types.hpp#L211-L219) —
  `PCL_ADD_UNION_POINT4D`, which expands to
  `union EIGEN_ALIGN16 { float data[4]; struct { float x; float y; float z; }; };` — reflowed onto
  one line here; in source it is a nine-line backslash-continued macro
- [`#L310-L315`](https://github.com/PointCloudLibrary/pcl/blob/3346843ea6b97697a1577293aa9cdf236b5c7ffb/common/include/pcl/impl/point_types.hpp#L310-L315) —
  `_PointXYZ` is exactly that macro and nothing else, with the in-source comment
  "This adds the members x,y,z which can also be accessed using the point (which is float[4])"

**Inferred** from those two: a `PointXYZ` occupies 16 bytes, of which 4 are padding and none are
double precision. Array-of-structs, not structure-of-arrays: an operation that touches only x pays
for y, z and the pad on every cache line.

### Open3D — two representations, and the choice is the caller's

Legacy `geometry::PointCloud` is an array of `Eigen::Vector3d` per attribute — already
structure-of-arrays *across* attributes, array-of-structs *within* a position:

- [`cpp/open3d/geometry/PointCloud.h#L462-L469`](https://github.com/isl-org/Open3D/blob/1e7b17438687a0b0c1e5a7187321ac7044afe275/cpp/open3d/geometry/PointCloud.h#L462-L469) —
  `std::vector<Eigen::Vector3d> points_; … normals_; … colors_;`

Tensor `t::geometry::PointCloud` replaces those vectors with a map of named tensors whose dtype
and device the caller picks:

- [`cpp/open3d/t/geometry/PointCloud.h#L741-L743`](https://github.com/isl-org/Open3D/blob/1e7b17438687a0b0c1e5a7187321ac7044afe275/cpp/open3d/t/geometry/PointCloud.h#L741-L743) —
  `core::Device device_ = core::Device("CPU:0"); TensorMap point_attr_;`

**Measured** (10⁸ points, [`spikes/pointcloud-scale/results/open3d.md`](../../../spikes/pointcloud-scale/results/open3d.md)
§Construction): 24.01 bytes/point for the legacy cloud, 24.01 for the f64 tensor, 12.01 for the
f32 tensor. The legacy vector matches `3 × sizeof(double)` exactly, so `Eigen::Vector3d` adds no
padding — the opposite of PCL's choice.

### PDAL — dimension-typed, XYZ in double, and a chunked column store already exists

PDAL's point storage is not a struct at all: a `PointLayout` is assembled from *dimensions*, each
with a declared type, and the default type of X, Y and Z is `double`:

- [`pdal/Dimension.json#L1-L12`](https://github.com/PDAL/PDAL/blob/27008f6241be44585c866a29dfc13bb16d678dab/pdal/Dimension.json#L1-L12) —
  `{ "name": "X", "type": "double", … }`, and Y and Z identically

Two in-memory tables implement that layout, and the difference between them is precisely the
row-versus-column decision the kernel spec §6 makes:

| Table | Layout | Block size | Source |
|---|---|---|---|
| `RowPointTable` (the default, `using PointTable = RowPointTable`) | one interleaved record per point, in 64 Ki-point blocks | `m_blockPtCnt = 65536` | [`pdal/PointTable.hpp#L144-L152`](https://github.com/PDAL/PDAL/blob/27008f6241be44585c866a29dfc13bb16d678dab/pdal/PointTable.hpp#L144-L152) |
| `ColumnPointTable` | one block list **per dimension**, in 16 Ki-point blocks | `m_blockPtCnt = 16384` | [`pdal/PointTable.hpp#L174-L186`](https://github.com/PDAL/PDAL/blob/27008f6241be44585c866a29dfc13bb16d678dab/pdal/PointTable.hpp#L174-L186) |

`ColumnPointTable`'s `MemBlocks m_blocks` is a `std::vector<std::vector<char *>>` — a list of
block lists, one per dimension. **That is the kernel spec §4 point cloud layout, already written
down, with a chunk size chosen by someone who ships it.** The kernel spec does not currently name
a chunk size; PDAL's two are 16 384 and 65 536 points, both powers of two "to facilitate fast div
and mod ops" (the source's own comment).

### Potree — int32 triples plus a per-file scale and offset

PotreeConverter stores each position as three `int32_t` and reconstructs a double from a per-file
scale and offset:

- [`Converter/src/indexer.cpp#L852-L857`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/src/indexer.cpp#L852-L857) —
  `int32_t* xyz = reinterpret_cast<int32_t*>(points->data_u8 + pointOffset); double x = (xyz[0] * scale.x) + offset.x;` and the same for y and z
- the same decode appears in the sampler, [`Converter/include/sampler_poisson.h#L96-L101`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/include/sampler_poisson.h#L96-L101)
- the scale and offset are written into `metadata.json`,
  [`Converter/src/indexer.cpp#L512-L513`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/src/indexer.cpp#L512-L513)

This is 12 bytes per position with **uniform** resolution across the whole file — at a scale of
0.001 m, an int32 spans ±2 147 km at exactly 1 mm everywhere, which no float of any width does.
It is the same scheme LAS uses, and PDAL's LAS reader decodes it the same way:

- [`io/LasReader.cpp#L750-L756`](https://github.com/PDAL/PDAL/blob/27008f6241be44585c866a29dfc13bb16d678dab/io/LasReader.cpp#L750-L756) —
  `int32_t xi, yi, zi; istream >> xi >> yi >> zi; … double x = xi * h.scale.x + h.offset.x;`

## The index, and why it is the thing that breaks

### Open3D's octree stores every index at every level

`Octree::ConvertFromPointCloud` inserts points one at a time, and each insertion appends the
point's index to **every internal node on the root-to-leaf path** as well as to the leaf:

- [`cpp/open3d/geometry/Octree.cpp#L564-L575`](https://github.com/isl-org/Open3D/blob/1e7b17438687a0b0c1e5a7187321ac7044afe275/cpp/open3d/geometry/Octree.cpp#L564-L575) —
  a plain serial `for (size_t idx = 0; idx < point_cloud.points_.size(); idx++)` calling
  `InsertPoint` with `OctreeInternalPointNode::GetUpdateFunction(idx)`
- [`#L131-L138`](https://github.com/isl-org/Open3D/blob/1e7b17438687a0b0c1e5a7187321ac7044afe275/cpp/open3d/geometry/Octree.cpp#L131-L138) —
  that internal-node update is `internal_point_node->indices_.push_back(idx);`
- [`cpp/open3d/geometry/Octree.h#L160-L162`](https://github.com/isl-org/Open3D/blob/1e7b17438687a0b0c1e5a7187321ac7044afe275/cpp/open3d/geometry/Octree.h#L160-L162) —
  `/// Indices of points associated with any children of this node` `std::vector<size_t> indices_;`
- [`#L237-L238`](https://github.com/isl-org/Open3D/blob/1e7b17438687a0b0c1e5a7187321ac7044afe275/cpp/open3d/geometry/Octree.h#L237-L238) —
  the leaf carries `std::vector<size_t> indices_` too

**Inferred** from those: a depth-*d* tree holds *(d + 1) × N* eight-byte indices, i.e. 72 bytes per
point of index payload alone at `max_depth=8`, before node objects, `shared_ptr` control blocks and
`std::vector` slack.

**Measured** ([results](../../../spikes/pointcloud-scale/results/open3d.md) §Octree):

| N | `max_depth` | Build (s) | Bytes/point | Peak RSS |
|---|---|---|---|---|
| 10⁶ | 8 | 3.07 | 466.6 | 1.01 GB |
| 10⁷ | 6 | 16.51 | 91.2 | 1.87 GB |
| 10⁷ | 8 | 35.93 | 220.9 | 2.56 GB |
| 10⁸ | 8 | **324.38** | 102.9 | **13.13 GB** |

Bytes per point *falls* with N at fixed depth because the tree saturates — at depth 8 there are at
most 256³ ≈ 16.8 M leaves, so past ~10⁷ points the node count stops growing and only the
per-point index payload does, approaching the 72 bytes/point floor the source predicts.

**This is the correction P-13 needs, and it goes the other way from the hypothesis.** Nothing ran
out of memory. 10⁸ points stored in 4.91 GB (f64) or 3.71 GB (f32); the depth-8 octree over them
built successfully in 13.13 GB — **38.6 % of this machine's 34.0 GB, and 2.7× the size of the
points it indexes** — in **324.4 s on one core of thirty-two**. The failure is not an allocation
error, it is that a single index build over a single cloud eats five and a half minutes and two
fifths of the machine, leaving nothing for a second cloud, a mesh, or the model the point cloud is
supposed to be measured against. Extrapolated linearly (and this is extrapolation, from one
saturated data point), 10⁹ points would need ≈103 GB for the index alone.

### Nearest-neighbour search costs a second full copy

Open3D's `KDTreeFlann` is — despite the name — a **nanoflann** index over an `Eigen::MatrixXd` it
owns:

- [`cpp/open3d/geometry/KDTreeFlann.h#L100-L106`](https://github.com/isl-org/Open3D/blob/1e7b17438687a0b0c1e5a7187321ac7044afe275/cpp/open3d/geometry/KDTreeFlann.h#L100-L106) —
  `using KDTree_t = nanoflann::KDTreeEigenMatrixAdaptor<const Eigen::MatrixXd, …>; Eigen::MatrixXd data_; std::unique_ptr<KDTree_t> nanoflann_index_;`

PCL's `KdTreeFLANN` — which really is FLANN — does the same thing in float32, allocating a fresh
`float[n × dim]`:

- [`kdtree/include/pcl/kdtree/kdtree_flann.h#L288-L293`](https://github.com/PointCloudLibrary/pcl/blob/3346843ea6b97697a1577293aa9cdf236b5c7ffb/kdtree/include/pcl/kdtree/kdtree_flann.h#L288-L293) —
  `std::shared_ptr<FLANNIndex> flann_index_;` and `/** \brief Internal pointer to data. … */ std::shared_ptr<float> cloud_;`
- [`kdtree/include/pcl/kdtree/impl/kdtree_flann.hpp#L440`](https://github.com/PointCloudLibrary/pcl/blob/3346843ea6b97697a1577293aa9cdf236b5c7ffb/kdtree/include/pcl/kdtree/impl/kdtree_flann.hpp#L440) —
  `cloud_.reset (new float[original_no_of_points * dim_], std::default_delete<float[]> ());`

**Measured** for Open3D's: 42.6 bytes/point of extra resident memory at 10⁷ points and 41.0 at
10⁸ — consistent with the 24 bytes/point `Eigen::MatrixXd` duplicate plus ≈17 bytes/point of
nanoflann nodes. The index built in **178.0 s** at 10⁸ points, and 1 000 single-nearest queries
then cost **6.48 µs each**. **All 100 verified queries returned the same point as a chunked f64
brute-force scan over the whole cloud, at every size — 0 mismatches out of 300 verifications
across the three sizes.**

**Both libraries therefore duplicate the cloud to index it.** For a kernel that intends to memory-
map chunks (spec §8), an index that demands its own private copy of the coordinates defeats the
mapping.

## Out-of-core: three answers and one non-answer

### PCL — an out-of-core module exists, and its own documentation qualifies it

`pcl_outofcore` is a directory-based octree on disk with per-node containers
([`outofcore/include/pcl/outofcore/octree_disk_container.h`](https://github.com/PointCloudLibrary/pcl/blob/3346843ea6b97697a1577293aa9cdf236b5c7ffb/outofcore/include/pcl/outofcore/octree_disk_container.h),
[`octree_ram_container.h`](https://github.com/PointCloudLibrary/pcl/blob/3346843ea6b97697a1577293aa9cdf236b5c7ffb/outofcore/include/pcl/outofcore/octree_ram_container.h)),
built and viewed with two command-line tools. Its module documentation states the status itself:

- [`outofcore/outofcore.doxy#L33-L36`](https://github.com/PointCloudLibrary/pcl/blob/3346843ea6b97697a1577293aa9cdf236b5c7ffb/outofcore/outofcore.doxy#L33-L36) —
  "Please note that this library is still under development, and that interested users should use
  the `PCLPointCloud2`-based insertion and query methods."

**Claimed**, by the module's own documentation, at a 2025 release tag. It is also an optional
subsystem, disabled when Boost.filesystem is absent
([`outofcore/CMakeLists.txt#L9-L15`](https://github.com/PointCloudLibrary/pcl/blob/3346843ea6b97697a1577293aa9cdf236b5c7ffb/outofcore/CMakeLists.txt#L9-L15)).

### PDAL — streaming, and it is a per-stage property, not a mode

A PDAL pipeline can execute in streaming mode, in which points flow through the stages in
fixed-capacity buffers instead of a full `PointView`:

- [`pdal/Streamable.hpp#L45-L47`](https://github.com/PDAL/PDAL/blob/27008f6241be44585c866a29dfc13bb16d678dab/pdal/Streamable.hpp#L45-L47) —
  `class PDAL_EXPORT Streamable : public virtual Stage`
- [`#L94`](https://github.com/PDAL/PDAL/blob/27008f6241be44585c866a29dfc13bb16d678dab/pdal/Streamable.hpp#L94) —
  `virtual bool processOne(PointRef& /*point*/) = 0;` — one point at a time, the reader returning
  false at end of input and a filter returning false to drop the point
- [`pdal/PointTable.hpp#L216-L272`](https://github.com/PDAL/PDAL/blob/27008f6241be44585c866a29dfc13bb16d678dab/pdal/PointTable.hpp#L216-L272) —
  `StreamPointTable` holds a fixed `m_capacity` and a per-point `m_skips` flag;
  [`#L276-L299`](https://github.com/PDAL/PDAL/blob/27008f6241be44585c866a29dfc13bb16d678dab/pdal/PointTable.hpp#L276-L299)
  is `FixedPointTable`, the concrete fixed-size buffer

**Counted**, with the rule stated so it can be re-run: of the header files under `io/` and
`filters/` at the pinned commit whose class declaration line matches
`class PDAL_EXPORT <Name> : public (Reader|Writer|Filter)`, there are **102**, and **41** of them
also list `public Streamable` on that same declaration line
(`grep -lE "class PDAL_EXPORT [A-Za-z0-9_]+ : public (Reader|Writer|Filter),? public Streamable" io/*.hpp filters/*.hpp | wc -l`).
The count is of *direct* declarations only — a stage inheriting `Streamable` through an
intermediate base would not be counted — so 41/102 is a lower bound on streamable stages and an
upper bound on the fraction that are not. The point stands either way: **streaming is a property
of each stage, and the majority of stages do not have it.** A maintainer says the consequence out
loud on the tracker; see [Known problems](#known-problems) row PDAL#1818.

### Potree — the converter is the out-of-core design, and it is a partition

`PotreeConverter` 2.x produces exactly three files — `metadata.json`, `hierarchy.bin`,
`octree.bin` ([`Converter/src/indexer.cpp#L1437`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/src/indexer.cpp#L1437),
[`#L1769`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/src/indexer.cpp#L1769),
[`Converter/include/HierarchyBuilder.h#L284-L287`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/include/HierarchyBuilder.h#L284-L287)) —
where 1.x produced one file per node. `metadata.json` carries version, point count, projection,
the first hierarchy chunk's descriptor, `offset`, `scale`, `spacing`, bounding box, encoding and
the attribute list
([`#L505-L518`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/src/indexer.cpp#L505-L518)).

`hierarchy.bin` is a flat array of fixed-size node records:

- [`Converter/src/indexer.cpp#L587`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/src/indexer.cpp#L587) —
  `constexpr int bytesPerNode = 1 + 1 + 4 + 8 + 8;`
- [`Converter/include/HierarchyBuilder.h#L49-L53`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/include/HierarchyBuilder.h#L49-L53) —
  the fields those 22 bytes hold: `numPoints`, `childMask`, `byteOffset`, `byteSize`, `type`
- [`#L102-L104`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/include/HierarchyBuilder.h#L102-L104) —
  the reader's byte offsets into a record, `numPoints` at +31, `byteOffset` at +35, `byteSize` at +43

The hierarchy is itself chunked so a viewer never loads all of it: nodes are grouped into subtrees
`hierarchyStepSize = 4` levels deep, and a node at the bottom of a chunk becomes a `PROXY` record
pointing at the next chunk
([`Converter/src/indexer.cpp#L19`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/src/indexer.cpp#L19),
[`#L559-L575`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/src/indexer.cpp#L559-L575)).
Nodes subdivide at `maxPointsPerChunk = 10'000`
([`Converter/include/indexer.h#L47`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/include/indexer.h#L47)).

**The level-assignment rule, read from source, and it is the part worth copying.** The spacing at
the root is one 128th of the bounding box's x extent, and halves per level:

- [`Converter/src/indexer.cpp#L1603`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/src/indexer.cpp#L1603) —
  `indexer.spacing = (chunks->max - chunks->min).x / 128.0;`
- [`Converter/include/sampler_poisson.h#L114`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/include/sampler_poisson.h#L114) —
  `double spacing = baseSpacing / pow(2.0, node->level());`

Sampling runs **bottom-up**. A node's children's points are sorted by distance to the node centre
([`#L182-L203`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/include/sampler_poisson.h#L182-L203))
and each is accepted into the parent only if it is at least `spacing` from every point already
accepted there
([`#L133-L180`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/include/sampler_poisson.h#L133-L180)).
Then — and this is the design decision — the rejected points, not a copy of everything, become the
child's new contents:

- [`Converter/include/sampler_poisson.h#L247-L280`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/include/sampler_poisson.h#L247-L280) —
  accepted points are written to the parent's `accepted` buffer, rejected ones to a `rejected`
  buffer, and then `child->points = rejected; child->numPoints = numRejected;`

**Inferred, and it is the headline:** every point is stored in exactly one node, so an LOD octree
over N points holds N points. A coarse level is a *thinned sample of the real points*, not a
derived summary — so there is no resampling error, no second copy, and `octree.bin` is the same
size as the input point set regardless of tree depth. Compare Open3D's octree, which stores every
index at every level.

Two honest qualifications, both from the same file. The acceptance test is Poisson-disk-*like*,
not exact: after 10 000 distance checks a candidate is accepted unconditionally
([`#L170-L176`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/include/sampler_poisson.h#L170-L176)),
and the accepted set lives in a **fixed** `thread_local vector<Point> dbgAccepted(1'000'000)`
([`#L112`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/include/sampler_poisson.h#L112))
written through `dbgAccepted[dbgNumAccepted] = point;` with no bounds check
([`#L213-L215`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/include/sampler_poisson.h#L213-L215)).
A user on the tracker names that exact line as the source of a slowdown on dense overlapping scans
(PotreeConverter#501 below), and a separate report is a segfault in this function
(PotreeConverter#550). **The layout is worth borrowing; this implementation of the sampler is
not.**

### The viewer's budget — a hard cap, not an eviction policy

Potree's viewer selects nodes by a screen-space priority and stops when a fixed budget is reached:

- [`src/Potree.js#L101`](https://github.com/potree/potree/blob/3013577379b5c8530ebca3cdc980f7585ae2320f/src/Potree.js#L101) —
  `export let pointBudget = 1 * 1000 * 1000;`
- [`src/Potree_update_visibility.js#L40`](https://github.com/potree/potree/blob/3013577379b5c8530ebca3cdc980f7585ae2320f/src/Potree_update_visibility.js#L40) —
  the traversal is a `BinaryHeap` keyed on `1 / x.weight`
- [`#L352-L392`](https://github.com/potree/potree/blob/3013577379b5c8530ebca3cdc980f7585ae2320f/src/Potree_update_visibility.js#L352-L392) —
  the weight of a child is its bounding sphere's **screen pixel radius** under a perspective
  camera; below `pointcloud.minimumNodePixelSize` the subtree is not even queued, and a node the
  camera is inside gets `Number.MAX_VALUE`
- [`#L179-L183`](https://github.com/potree/potree/blob/3013577379b5c8530ebca3cdc980f7585ae2320f/src/Potree_update_visibility.js#L179-L183)
  and [`#L282-L284`](https://github.com/potree/potree/blob/3013577379b5c8530ebca3cdc980f7585ae2320f/src/Potree_update_visibility.js#L282-L284) —
  a node is not visible if it would push `numVisiblePoints` past the budget, and the traversal
  `break`s outright at that point; the first three levels are exempt
  (`visible = visible || node.getLevel() <= 2`)
- [`#L406-L408`](https://github.com/potree/potree/blob/3013577379b5c8530ebca3cdc980f7585ae2320f/src/Potree_update_visibility.js#L406-L408) —
  at most `Potree.maxNodesLoading` (**4**, [`src/Potree.js#L104`](https://github.com/potree/potree/blob/3013577379b5c8530ebca3cdc980f7585ae2320f/src/Potree.js#L104))
  unloaded nodes are fetched per frame

**Inferred:** the budget is a *drawing* cap enforced during traversal, plus a per-frame *loading*
cap. No eviction of already-loaded geometry was found in these files, which is consistent with the
"crashes after some minutes" report below. Borrow the two caps; do not assume the memory question
is answered by them.

## Precision — the P-05 evidence

**Measured** ([results](../../../spikes/pointcloud-scale/results/open3d.md) §Precision), 10⁷ points
in a 100 m cube placed at (500000, 500000, 0) m and compared, after subtracting the offset again,
against the exact local-frame coordinates:

| Storage | Max absolute error | Note |
|---|---|---|
| f32 tensor at 500 km | **0.015625 m** | exactly half the float32 ULP at that magnitude (0.03125 m) |
| f64 tensor at 500 km | 2.91 × 10⁻¹¹ m | half the float64 ULP (5.82 × 10⁻¹¹ m) |
| f32 at the origin | 3.81 × 10⁻⁶ m | the same storage, the same points, 4 096× better |

The 0.03125 m figure is the same float32 ULP at 500 km that [`blender.md`](blender.md) §Precision
reports for meshes; this note adds the point cloud half of the same fact and the ratio that makes
it concrete — **moving a cloud from the origin to a national-grid coordinate costs 4 096× the
storage error, with no operation performed at all.** RMS error is 0.00737 m, so this is not a tail
effect: a typical point moves ~7 mm.

**Potree's answer is the one to copy, and it is not "use f64".** An int32 with a scale of 0.001 m
and a per-file offset gives *uniform* 1 mm resolution over ±2 147 km in 12 bytes per point, where
f32 gives 3.8 µm at the origin and 15.6 mm at 500 km in the same 12 bytes, and f64 gives uniform
sub-nanometre in 24. For a scan — whose own instrument noise is millimetres — a fixed quantum
matched to the instrument is a better use of 12 bytes than a floating exponent, and it makes the
error independent of where the project sits in a national grid, which is precisely what
[`problems.md`](problems.md) P-05's "our design's answer" column demands of tolerances.

PCL's position is the opposite one, stated by a maintainer; see PCL#4756 below.

## Formats, or: what these libraries can actually read

**Open3D reads none of the formats survey data arrives in.** The dispatch tables are literal and
short:

- [`cpp/open3d/io/PointCloudIO.cpp#L26-L34`](https://github.com/isl-org/Open3D/blob/1e7b17438687a0b0c1e5a7187321ac7044afe275/cpp/open3d/io/PointCloudIO.cpp#L26-L34) —
  legacy: `xyz`, `xyzn`, `xyzrgb`, `ply`, `pcd`, `pts`
- [`cpp/open3d/t/io/PointCloudIO.cpp#L29-L39`](https://github.com/isl-org/Open3D/blob/1e7b17438687a0b0c1e5a7187321ac7044afe275/cpp/open3d/t/io/PointCloudIO.cpp#L29-L39) —
  tensor: `npz`, `xyz`, `xyzd`, `xyzi`, `xyzn`, `xyzrgb`, `pcd`, `ply`, `pts`

A case-insensitive search of `cpp/open3d/io/` and `cpp/open3d/t/io/` for `las`, `laszip`,
`lazperf` or `e57` returns nothing at this commit. **No LAS, no LAZ, no E57.** The feature request
(Open3D#3321) was closed the day after it was filed with a `laspy` workaround from another user,
not a maintainer.

PDAL is the opposite: LAS and LAZ, COPC, EPT, and E57 as a plugin
([`io/LasReader.hpp`](https://github.com/PDAL/PDAL/blob/27008f6241be44585c866a29dfc13bb16d678dab/io/LasReader.hpp),
[`io/CopcReader.hpp`](https://github.com/PDAL/PDAL/blob/27008f6241be44585c866a29dfc13bb16d678dab/io/CopcReader.hpp),
[`io/EptReader.hpp#L63`](https://github.com/PDAL/PDAL/blob/27008f6241be44585c866a29dfc13bb16d678dab/io/EptReader.hpp#L63)
— `class PDAL_EXPORT EptReader : public Reader, public Streamable`,
[`plugins/e57/`](https://github.com/PDAL/PDAL/tree/27008f6241be44585c866a29dfc13bb16d678dab/plugins/e57)).
**For an ingest path this is not a close comparison.**

## Threading

| Operation | PCL | Open3D |
|---|---|---|
| Octree build | serial loop over points, [`octree/include/pcl/octree/impl/octree_pointcloud.hpp#L77-L88`](https://github.com/PointCloudLibrary/pcl/blob/3346843ea6b97697a1577293aa9cdf236b5c7ffb/octree/include/pcl/octree/impl/octree_pointcloud.hpp#L77-L88) | serial loop over points, [`Octree.cpp#L564-L575`](https://github.com/isl-org/Open3D/blob/1e7b17438687a0b0c1e5a7187321ac7044afe275/cpp/open3d/geometry/Octree.cpp#L564-L575) |
| Normal estimation | parallel, but only in a **separate class**, `NormalEstimationOMP` ([`features/include/pcl/features/normal_3d_omp.h#L81-L92`](https://github.com/PointCloudLibrary/pcl/blob/3346843ea6b97697a1577293aa9cdf236b5c7ffb/features/include/pcl/features/normal_3d_omp.h#L81-L92)) | parallel in the one class, `#pragma omp parallel for schedule(static)` ([`EstimateNormals.cpp#L301`](https://github.com/isl-org/Open3D/blob/1e7b17438687a0b0c1e5a7187321ac7044afe275/cpp/open3d/geometry/EstimateNormals.cpp#L301)) |

**The measured 35.93 s at 10⁷ points and 324.4 s at 10⁸ are one core of thirty-two.** Spec §6 already
lists "octree build" among the `parallel for` targets; this is the number that says why.

PotreeConverter, by contrast, is parallel by default. Counting with a rule: `grep -rn
'std::execution::par' Converter/` at the pinned tag returns **5** occurrences, spread across the
chunker, the indexer and the sampler, and the converter additionally ships its own
`ConcurrentWriter` and `Monitor` thread helpers. The sampler's own sort is
[`Converter/include/sampler_poisson.h#L182-L183`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/include/sampler_poisson.h#L182-L183),
`std::sort(parallel, points.begin(), points.end(), …)` with `auto parallel = std::execution::par_unseq;`.
**Inferred:** that, plus the partition layout, is why a converter written for this problem outruns a
general-purpose library's tree on the same points — neither half alone explains it, and this note
measures neither, so the comparison is not quantified.

## Licences

Every licence here is permissive, so — unlike [`cgal.md`](cgal.md) §Licence — the file-granularity
check that P-14 demands has a uniform answer, and code as well as design may be borrowed.

| Project | Licence | Read at |
|---|---|---|
| PCL | BSD-3-Clause | [`LICENSE.txt#L1-L8`](https://github.com/PointCloudLibrary/pcl/blob/3346843ea6b97697a1577293aa9cdf236b5c7ffb/LICENSE.txt#L1-L8) — "Software License Agreement (BSD License)", Willow Garage / Open Perception |
| Open3D | MIT | [`LICENSE#L1-L4`](https://github.com/isl-org/Open3D/blob/1e7b17438687a0b0c1e5a7187321ac7044afe275/LICENSE#L1-L4) — "The MIT License (MIT)" |
| PDAL | BSD | [`LICENSE.txt#L1-L5`](https://github.com/PDAL/PDAL/blob/27008f6241be44585c866a29dfc13bb16d678dab/LICENSE.txt#L1-L5) — "released under the terms of the BSD open source license", Hobu, Inc. |
| Potree (viewer) | BSD-2-Clause | [`LICENSE`](https://github.com/potree/potree/blob/3013577379b5c8530ebca3cdc980f7585ae2320f/LICENSE) — Copyright (c) 2011-2020, Markus Schütz |
| PotreeConverter | BSD-2-Clause | [`LICENSE#L1-L7`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/LICENSE#L1-L7) — Copyright 2020 Markus Schütz |

**Not checked, and the reason to check later:** all three C++ libraries vendor or link third-party
components under their own terms — PCL and Open3D pull in FLANN, nanoflann and Eigen; PDAL vendors
**lazperf** ([`CMakeLists.txt#L168`](https://github.com/PDAL/PDAL/blob/27008f6241be44585c866a29dfc13bb16d678dab/CMakeLists.txt#L168),
`add_subdirectory(vendor/lazperf)`) and its E57 plugin builds **libE57Format**
([`plugins/e57/CMakeLists.txt#L10`](https://github.com/PDAL/PDAL/blob/27008f6241be44585c866a29dfc13bb16d678dab/plugins/e57/CMakeLists.txt#L10)).
A decision to *link* any of these needs that second pass, at the granularity P-14 requires; a
decision to *read* them for design does not, which is all this note does.

## Measurements

- **Hardware:** Windows 11 Pro 10.0.26200; Intel Core i9-14900HX, 32 logical processors; 32 GB
  installed RAM (`Get-CimInstance Win32_ComputerSystem` reports 34 049 179 648 bytes)
- **Versions:** Python 3.12.10, `open3d` 0.19.0, `numpy` 2.3.5, `psutil` 7.2.2
- **Benchmark model:** none from `reference/` — this is the *synthetic scale test* of the README's
  benchmark set, extended to point counts, plus the *precision set* placement (500 km) applied to a
  point cloud instead of a solid
- **Method:** [`spikes/pointcloud-scale/`](../../../spikes/pointcloud-scale/); raw results in
  [`results/open3d.md`](../../../spikes/pointcloud-scale/results/open3d.md). Uniform random points
  in a 100 m cube, seed 20260910, generated in 2 Mi-point chunks into one preallocated array.
  Memory is the OS peak working set (`psutil.Process().memory_info().peak_wset`). Five repeats at
  10⁷ where the stage allowed it, fewer at 10⁸; every repeat is in the results file.

| Test | Result |
|---|---|
| Construction, 10⁷ / 10⁸ points, legacy f64 | 24.09 / 24.01 bytes per point; 0.133 s / 1.799 s |
| Construction, 10⁷ / 10⁸ points, tensor f64 | 24.08 / 24.01 bytes per point; 0.063 s / 0.574 s |
| Construction, 10⁷ / 10⁸ points, tensor f32 | 12.09 / 12.01 bytes per point; 0.023 s / 0.270 s |
| Peak RSS at 10⁸ points (source array + cloud) | 7.31 GB legacy, 4.91 GB tensor f64, 3.71 GB tensor f32 |
| `Octree(max_depth=8)`, 10⁶ / 10⁷ points | 3.07 s / 35.93 s; 466.6 / 220.9 bytes per point |
| `Octree(max_depth=6)`, 10⁷ points | 16.51 s; 91.2 bytes per point |
| `Octree(max_depth=8)`, 10⁸ points | **324.38 s; 102.9 bytes per point; 13.13 GB peak RSS — it fits, single-threaded, in 38.6 % of RAM.** The P-13 case, and it is a *time* result |
| `KDTreeFlann` build, 10⁶ / 10⁷ / 10⁸ points | 0.512 s / 8.72 s / 178.0 s; 43.1 / 42.6 / 41.0 bytes per point |
| Nearest-neighbour query, 10⁶ / 10⁷ / 10⁸ points | 3.99 / 4.86 / 6.48 µs per query |
| Nearest-neighbour correctness | 100 of 1 000 queries verified against a chunked f64 brute-force scan at each size; **300 of 300 returned the same point**, 0 mismatches |
| f32 storage error at (500000, 500000, 0), 10⁷ points | max 0.015625 m, RMS 0.00737 m |
| f64 storage error at the same offset | max 2.91 × 10⁻¹¹ m |
| f32 storage error at the origin, same points | max 3.81 × 10⁻⁶ m — a factor of 4 096 |

**The C-ABI rule, so the negative result is checkable.** `grep -rl 'extern "C"'` over PCL's
`*/include/` trees returns **9** files, every one of them vendored third-party code (`kiss_fft.h`,
`kiss_fftr.h`, `svm.h`, `cJSON.h`) or a macro header, not an API; over Open3D's `cpp/open3d/` it
returns **3** (`DLPack.h`, a CUDA utility and a Filament engine file); over PDAL's `pdal/`, `io/`
and `filters/` it returns **4**, of which the two in `pdal/` are the plugin loader
(`PluginHelper.hpp`, `PluginInfo.hpp`). **None of the three exposes its own functionality through a
C ABI.**

**PDAL was not measured.** `pip install pdal==3.5.5` in a clean virtual environment fails: the
PyPI distribution is a source build that needs the native PDAL library, and CMake reports
`By not providing "FindPDAL.cmake" in CMAKE_MODULE_PATH this project has asked CMake to find a
package configuration file provided by "PDAL", but CMake did not find one.` Every PDAL statement
in this note is therefore read from source, and none is labelled measured. **PCL was not measured
either, and no PCL install was attempted** — the reference machine has no PCL build, and the note
makes no claim about how easy one would be. Nothing about PCL below is labelled measured.

## Known problems

Ten tickets across the four projects. Roles are `author_association` as GitHub reports it on the
issue or on the comment quoted (`gh api repos/<org>/<repo>/issues/<n>` and `…/comments`); `NONE`
means the speaker is not a member, collaborator or contributor of that repository, so a `NONE`
diagnosis is a *report*, not a maintainer's confirmation.

| Ticket | State | What it shows | Root cause it traces to |
|---|---|---|---|
| [Open3D#6525](https://github.com/isl-org/Open3D/issues/6525) — "Unable to load UTM based objects correctly" (2023-12-06, `fratopa`, **NONE**) | **open**, and **no replies at all** in the 2 years 9 months since | Reporter: "the values are too big for the Float32 used by open3d. This manifests as a vague 'shimmering'… translating the mesh to be close to the centre stops the 'shimmering' But leaves the mesh distorted… the translation occurs already after the precision has been lost". Reporter diagnosis; our own measurement of the same mechanism is above | **P-05.** f32 storage of world coordinates, and a translate applied after the loss. Exactly the "the frame origin must be f64 even when the geometry inside it is f32" half [`blender.md`](blender.md) established |
| [Open3D#6043](https://github.com/isl-org/Open3D/issues/6043) — "Tensor API can't write .pcd files beyond 2.1 GB" (2023-03-30, `jpaulos`, **NONE**) | **open**, **no replies at all** | "fails with a 'MemoryError: std::bad_alloc' (the system is certainly not out of memory)… The threshold of writable point clouds is about 2.1 GB". A 2³¹-byte ceiling in the writer, on the API that is meant to be the scalable one | A 32-bit size in an IO path. Our 10⁸-point f64 cloud is 2.4 GB, i.e. **past this ceiling** |
| [Open3D#3321](https://github.com/isl-org/Open3D/issues/3321) — LAS/LAZ import/export request (2021-04-21, `weinacker`, **NONE**) | **closed** 2021-04-22 | Closed the next day; the only substantive reply is from `aweinmann` (**NONE**) suggesting `laspy`. Still absent at v0.19.0, confirmed in source above | Scope: Open3D is a 3D-perception library, not a geospatial one |
| [PCL#4756](https://github.com/PointCloudLibrary/pcl/issues/4756) — "Is all pcl point type's x y z base on float?" (2021-05-12, `OrdinaryChen`, **NONE**) | **closed** 2024-08-22 | `mvieth` (**MEMBER**): "All of PCL's native point types use float for x, y, and z. You can create your own point type with double precision, but only few functions and classes will work correctly with double precision since PCL is designed for float/single precision". A maintainer stating the design, not a user guessing | **P-05.** A whole-library commitment to single precision |
| [PCL#1010](https://github.com/PointCloudLibrary/pcl/issues/1010) — "KDTree with double precision" (2014-11-21, `kode9`, **NONE**) | **closed** 2020-06-14 by the stale bot | `taketwo` (**MEMBER**): "the code in PCL is not precision type agnostic. It is usually written with the implicit assumption that points' coordinates are encoded with floats… you will see that `float`s are hard-coded everywhere". Six years open, closed by inactivity | The same commitment, now load-bearing in the *index* — matching the `new float[…]` we read in `kdtree_flann.hpp` |
| [PDAL#1818](https://github.com/PDAL/PDAL/issues/1818) — "PDAL runs out of memory with big .asc files" (2018-02-25, `gabri94`, **NONE**) | **closed** 2018-03-14 | `abellgithub` (**CONTRIBUTOR**): "The chipper filter requires all points in memory to properly operate, so this pipeline won't work with streaming mode. I don't have much to recommend at this point other than to increase the swap on your system or find a system with adequate memory." | **Streaming is per stage.** One non-streamable filter in a pipeline reverts the whole pipeline to in-core |
| [PDAL#4193](https://github.com/PDAL/PDAL/issues/4193) — "Is there a bug with readers.las truncating precision on larger decimal values?" (2023-09-27, `DrewScatterday`, **NONE**) | **closed** 2024-03-06 | The reporter's own follow-up is the useful part: "I naively didn't know that las files are stored as 32 ints. Then at runtime they can be converted to their decimal values using the scale and offset values stored in the header", with `offset_x: 575410, scale_x: 0.001`. `abellgithub` (**CONTRIBUTOR**) declined to investigate without an isolated test case. No maintainer confirmation of a defect | The int32-scale-offset scheme is invisible until it is not: users hit its *quantum*, not a float's exponent. A design that hides its resolution surprises people |
| [PotreeConverter#501](https://github.com/potree/PotreeConverter/issues/501) — "Converting a large quantity and size of las files (1.2TB)" (2021-02-04, `Nogbit`, **NONE**) | **open** | Two independent third-party reports, both **NONE**: `smcavoy12` processed "about 60 billion points… with a 32gb RAM university computer lab workstation… I run out of disk space constantly, but never RAM"; `nikste` reports ">100gb" of RAM on ~6.5 billion points. `ditlef` (**NONE**) attributes the slowdown to "thread_local vector<Point> dbgAccepted(1'000'000)" — the exact fixed buffer we read in source | Out-of-core works for the *streaming* phases; the in-node sampler is the in-core part, and it is where both the memory and the speed reports land |
| [PotreeConverter#550](https://github.com/potree/PotreeConverter/issues/550) — "Segfault in SamplerPoisson::sample" (2022-01-16, `kannes`, **NONE**) | **open** | A crash named for the function whose fixed 1 Mi-entry buffer is written without a bounds check. The reporter then isolates it to that sampler: "Using '-m random' did not crash indeed!" — the other sampling method, on the same data, on a 64 GB Ryzen 5 3600X. `midnight-dev` (**CONTRIBUTOR**): "this isn't a simple problem to diagnose. I've tried to figure out what's breaking a couple times in the past without much luck. There's always a ton of points when it happens" | **Inferred, not established.** Nobody in the thread names the buffer; what is established is that the crash is in this sampler and not in `-m random`, and that a contributor has failed to diagnose it more than once. The unguarded fixed buffer we read in that function is a candidate, not a confirmed cause |
| [Potree#1002](https://github.com/potree/potree/issues/1002) — "Viewer crashing after some time on potree viewer 1.8" (2021-03-18, `Deca`, **NONE**) | **open** | Reporter's point budget is **41 637 198**, against the shipped default of 1 000 000. `mikepianka` (**CONTRIBUTOR**): "I assumed it was a memory leak somewhere, and then eventually the browser dumped the page". `midnight-dev` (**CONTRIBUTOR**) asks whether RAM or VRAM runs out first — nobody establishes which | The budget caps *drawing*, not *residency*. No eviction path was found in the source read above, and this is the user-visible consequence |

## Evaluation

Scored against the [README](README.md) matrix. Rows that are about a modelling kernel rather than a
point cloud library are marked **not applicable** with the reason, per that file's rule that
unknowns are recorded rather than skipped.

| Criterion | PCL | Open3D | PDAL | Potree | Evidence type | Source / method |
|---|---|---|---|---|---|---|
| **License** | BSD-3 | MIT | BSD | BSD-2 (both repos) | claimed | licence files at the pinned commits, §Licences |
| **Representations held natively** | point cloud only (plus `PolygonMesh` as a wrapper) | point cloud, triangle mesh, voxel grid, octree, RGBD | point cloud only; a `Mesh` exists as a stage output | point cloud only | claimed | headers at the pinned commits |
| **Boolean robustness** | **not applicable** — none of the four performs solid booleans; this is a B-rep/mesh criterion | — | — | — | — | — |
| **Tolerance and precision model** | float32 xyz, no tolerance model; explicitly stated as a design limit by a MEMBER | f64 legacy, f32-or-f64 tensor, caller's choice; no tolerance model | f64 XYZ by declared dimension type | int32 × scale + f64 offset — a *fixed quantum*, which is a stronger guarantee than either float | claimed (source) + measured (Open3D) | §Storage, §Precision, PCL#4756, PCL#1010 |
| **Incremental evaluation** | **not applicable** — none has a parametric model to re-evaluate. The nearest analogue, "can one changed chunk be re-indexed", is answered no for Open3D's octree (rebuild is the only API) | — | — | — | inferred | [`Octree.h`](https://github.com/isl-org/Open3D/blob/1e7b17438687a0b0c1e5a7187321ac7044afe275/cpp/open3d/geometry/Octree.h) exposes `ConvertFromPointCloud` and no incremental insert on a built tree |
| **Threading model** | octree build serial; parallelism is opt-in via separate `*OMP` classes | octree build serial; normals OpenMP-parallel | streaming is inherently pipelined; `filters.*` are per-stage | converter parallel (`std::execution::par_unseq`); viewer single-threaded JS with ≤4 concurrent node loads | claimed (source) + measured (35.93 s / 324.4 s single-core octree build at 10⁷ / 10⁸) | §Threading |
| **GPU path** | visualisation module (VTK) | tensor point cloud can live on a CUDA device; a rendering module exists | none — PDAL is headless by design | the whole point: WebGL, screen-space LOD, per-frame budget | claimed | §Out-of-core, `Device("CPU:0")` default in [`PointCloud.h#L742`](https://github.com/isl-org/Open3D/blob/1e7b17438687a0b0c1e5a7187321ac7044afe275/cpp/open3d/t/geometry/PointCloud.h#L742) |
| **IFC coverage** | **not applicable** — none reads IFC, and none should | — | — | — | — | — |
| **Performance** | not measured (no reliable Windows wheel) | measured at 10⁶/10⁷/10⁸ | not measured (wheel needs the native library) | not measured | measured for Open3D only | §Measurements |
| **Embeddability** | C++ library; **no C ABI for its own API** | C++ library with a maintained Python wheel; **no C ABI for its own API** | C++ library; **no C ABI for its own API** — the public header is `pdal/pdal.hpp`; `find . -iname 'pdal.h' -o -iname '*capi*'` returns nothing. What it has that the others do not is a **JSON pipeline description**, drivable over a subprocess or a file | not a library — a CLI converter and a JS viewer. Its *format* is the embeddable thing | claimed (source, negative result) | §Verdict, build on; rule below |
| **2D derivation** | **not applicable** — a point cloud has no section or hidden-line problem in the B-rep sense | — | — | — | — | — |
| **Maturity** | 2009–, wide use, active releases (1.15.1, 2025-08); the out-of-core module self-describes as under development | 2018–, corporate origin (Intel ISL), release 0.19.0 2025-01 | 2010s–, Hobu Inc., commercial support offered on the tracker, release 2.10.2 2026-06 | one principal author; converter released 2026-06, **viewer's last release 2023-12** | claimed | release tags, §What was read |
| **AI familiarity** | very high — the default answer to "point cloud library" for a decade | high | moderate, concentrated in the geospatial community | moderate | inferred; one column, never a tiebreaker (R-09) | — |

## The twelve questions

1. **Re-evaluate a single changed element without reprocessing the model?** Open3D: no — its
   `Octree` has no incremental insert after `ConvertFromPointCloud`; rebuilding 10⁷ points costs
   35.93 s (measured). PDAL: not applicable, it is a batch/streaming pipeline. Potree: the
   converter is a batch tool, but the *format* supports it — a node is a byte range in
   `octree.bin` with its own hierarchy record, so one node can be rewritten in principle
   (inferred).
2. **What happens to geometry on an IFC round trip?** Not applicable — none of the four reads IFC.
3. **Driven in-process from DynLex, without a subprocess or a file?** See *Build on* below. Short
   answer: **none of them, without work.** No C ABI is exposed by PCL, Open3D or PDAL at these
   tags — PDAL's public header is `pdal/pdal.hpp` and a search for `pdal.h` or a `capi` directory
   returns nothing. Each would need a C shim written and maintained by us. PDAL is nevertheless the
   least bad, because its unit of work is a **JSON pipeline** that can be handed across a process
   boundary without a shim at all; the others have no such surface.
4. **Threading model, and what is single-threaded by design?** §Threading. Octree construction is
   serial in both PCL and Open3D. The Potree *viewer* is single-threaded JavaScript that loads at
   most 4 nodes per frame; the Potree *converter* is parallel.
5. **What breaks first at scale — memory, load time, or evaluation time?** Measured, and the answer
   corrects the hypothesis twice over. Not storage: 10⁸ points store in 4.91 GB (f64) or 3.71 GB
   (f32) of 34.0 GB. And not, at 10⁸ on this machine, memory at all — **index build time is what
   breaks first**: 324.4 s single-threaded for the depth-8 octree and 178.0 s for the kd-tree,
   against 0.57 s to load the points. Memory is the *second* wall, not the first: the octree's
   13.13 GB is 38.6 % of the machine for one index over one cloud, so a second cloud, or 10⁹
   points, is where allocation actually fails.
6. **What numeric precision internally, and can it be configured?** PCL: float32, not configurable
   in practice (PCL#1010, a MEMBER: "`float`s are hard-coded everywhere"). Open3D: f64 legacy,
   f32-or-f64 tensor, configurable per cloud. PDAL: f64 XYZ by dimension type, configurable
   per dimension. Potree: int32 with a per-file scale and offset — configurable *quantum*, which is
   the third option and the one this note recommends borrowing.
7. **Operate on a subset — one tile, one region? (R-14)** PDAL yes, by construction (streaming
   plus `filters.crop`, plus EPT/COPC which are tiled formats). Potree yes, that *is* the format.
   Open3D and PCL: only by loading everything and slicing in memory, which is the failure mode.
8. **Who maintains it, and what if they stop?** PCL: a broad community, Open Perception; low bus
   factor risk, but the out-of-core module has been "under development" long enough to appear so
   at a 2025 tag. Open3D: Intel ISL origin plus community. PDAL: Hobu, Inc., which sells support
   for it (a link to commercial support appears on PDAL#4193) — a company, so a commercial rather
   than an abandonment risk. Potree: **one principal author**, and the viewer has not had a release
   since 2023-12. For a *design* reference that risk does not matter; for a dependency it would.
9. **Documented failure modes, with issue links, and the design choice each traces back to?**
   §Known problems, ten tickets.
10. **Which representations natively, and how does it convert?** Point clouds in all four. Open3D
    additionally holds meshes and voxel grids and converts between them; the point-cloud→mesh
    direction (Poisson reconstruction, ball pivoting) exists there and in PCL, and is scheduled
    *after* M8 in our spec §4 — nothing here changes that.
11. **How does geometry reach the GPU and come back?** Potree is the only one of the four that
    answers this seriously, and its answer is the borrow: pick nodes by screen-pixel radius, cap
    the total drawn points, cap the nodes loaded per frame. Open3D's tensor cloud can be allocated
    on a CUDA device, which is a different thing from a rendering path.
12. **What would we take, and what would we avoid?** §Verdict.

## Verdict

### Build on

**No, for all four — but for three different reasons, and one of them is close.**

**PCL — no, and float32 is the disqualifying fact, not a preference.** The README matrix says
"float32-only is disqualifying for *build on*", and PCL is float32-only by design: the macro that
defines every native point type emits `float x; float y; float z;`, and two members say on the
tracker that the assumption is baked in throughout. Our measured 0.015625 m error at 500 km is
what that costs on a national grid. A custom double point type is possible and, per `taketwo`,
mostly useless because the algorithms are not precision-agnostic.

**Open3D — no, and the measurement is the reason rather than the licence.** MIT, a maintained
wheel, f64 available, and the friendliest API of the four; but its depth-8 octree over 10⁸ points
costs 102.9 bytes per point — 2.7× the points themselves — and 324.4 s on one core, its kd-tree
duplicates the whole cloud to index it, it
reads none of LAS, LAZ or E57, and its scalable API cannot write past 2.1 GB (Open3D#6043). Those
are not gaps to fill — they are the parts we would have to replace, which is the whole module.

**PDAL — no as the module, but genuinely yes as an ingest dependency, and this is the one to
revisit.** It is the only one of the four with the right precision model (f64 XYZ), the right
formats (LAS, LAZ, COPC, EPT, E57), a real out-of-core story (streaming stages), a chunked
per-dimension table already written. It has **no C ABI**, so "in-process from DynLex" would need a
shim exactly as PCL and Open3D would — but it is the only one of the three whose whole unit of work
is a JSON pipeline, which can be driven across a process boundary with no shim at all, and that is a
real difference when the work is a one-off ingest rather than an interactive edit. What disqualifies it as the *module* is that it is a
processing pipeline, not a spatial data structure: it has no LOD, no viewer-facing octree, and no
notion of a resident, editable, GPU-bound cloud. **Recommended follow-up, not settled here:** an
explicit decision on whether `ifc/`-style ingest drives PDAL — as a linked C++ library behind our
own C shim, or as a subprocess given a JSON pipeline — rather than us writing LAS, LAZ and E57
readers ourselves. That decision needs a measurement this note does not have — see Risks.

**Potree — not applicable.** A CLI converter and a WebGL viewer. There is nothing to build on;
there is a great deal to copy.

### Borrow from

Each row names the file the design was read in, and — per P-14's sharpened rule — the licence of
that file, since all five are permissive enough that the *code* and not only the idea may be
taken.

| Borrow | Where it is, at the pinned commit | Licence of that file | Into |
|---|---|---|---|
| **An LOD octree that is a partition, not a pyramid.** Accepted points are *moved* out of the child into the parent (`child->points = rejected`), so N points occupy N slots regardless of depth, and a coarse level is a real subset of the real points | [`sampler_poisson.h#L247-L280`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/include/sampler_poisson.h#L247-L280) | BSD-2 | spec §4 `pointcloud`: the LOD rule, in place of an unspecified "LOD" |
| **The level-assignment rule**: root spacing = bbox extent / 128, halving per level; a candidate joins a node if it is ≥ spacing from every point already at that node; children sorted by distance to node centre first, so the coarse level is centre-weighted | [`indexer.cpp#L1603`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/src/indexer.cpp#L1603), [`sampler_poisson.h#L114`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/include/sampler_poisson.h#L114), [`#L133-L203`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/include/sampler_poisson.h#L133-L203) | BSD-2 | spec §4 |
| **A 22-byte fixed node record and a chunked hierarchy**: `type`, `childMask`, `numPoints`, `byteOffset`, `byteSize`; subtrees of 4 levels, with a `PROXY` record at a chunk boundary pointing at the next chunk, so the hierarchy itself pages | [`indexer.cpp#L587`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/src/indexer.cpp#L587), [`#L19`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/src/indexer.cpp#L19), [`HierarchyBuilder.h#L49-L53`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/include/HierarchyBuilder.h#L49-L53) | BSD-2 | spec §8: this is what a memory-mapped chunk index looks like when it works |
| **int32 × scale + f64 offset for stored positions** — a fixed quantum, uniform over the file, 12 bytes; ±2 147 km at 1 mm. Independent of where the project sits in a national grid, which is exactly what P-05 asks of a design | [`indexer.cpp#L852-L857`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/src/indexer.cpp#L852-L857); LAS's own version at [`LasReader.cpp#L750-L756`](https://github.com/PDAL/PDAL/blob/27008f6241be44585c866a29dfc13bb16d678dab/io/LasReader.cpp#L750-L756) | BSD-2 / BSD | spec §5 and ADR-0006 — as the **storage** encoding for scan data, with f64 in the local frame remaining the *computation* type |
| **A per-dimension chunked table with a power-of-two block size**, alongside a row-major one, so the layout is a decision and not an accident: 16 384 points per dimension block, 65 536 per row block | [`PointTable.hpp#L174-L186`](https://github.com/PDAL/PDAL/blob/27008f6241be44585c866a29dfc13bb16d678dab/pdal/PointTable.hpp#L174-L186), [`#L144-L152`](https://github.com/PDAL/PDAL/blob/27008f6241be44585c866a29dfc13bb16d678dab/pdal/PointTable.hpp#L144-L152) | BSD | spec §4/§6: a chunk size for "chunked structure-of-arrays", from someone who ships it |
| **A stage that declares whether it can stream, checked at pipeline build**, rather than a global "streaming mode" that silently degrades | [`Streamable.hpp#L45-L94`](https://github.com/PDAL/PDAL/blob/27008f6241be44585c866a29dfc13bb16d678dab/pdal/Streamable.hpp#L45-L94), [`PointTable.hpp#L216-L272`](https://github.com/PDAL/PDAL/blob/27008f6241be44585c866a29dfc13bb16d678dab/pdal/PointTable.hpp#L216-L272) | BSD | spec §12: an operation that cannot work chunk-wise must say so in a *type*, not in a log line |
| **Screen-pixel-radius LOD selection with two caps** — a total drawn-point budget enforced during a priority traversal, and a per-frame node-load cap | [`Potree_update_visibility.js#L352-L392`](https://github.com/potree/potree/blob/3013577379b5c8530ebca3cdc980f7585ae2320f/src/Potree_update_visibility.js#L352-L392), [`#L179-L183`](https://github.com/potree/potree/blob/3013577379b5c8530ebca3cdc980f7585ae2320f/src/Potree_update_visibility.js#L179-L183), [`Potree.js#L101-L104`](https://github.com/potree/potree/blob/3013577379b5c8530ebca3cdc980f7585ae2320f/src/Potree.js#L101-L104) | BSD-2 | spec §6 item 4 (GPU point cloud LOD selection) |

### Avoid

| Avoid | Evidence |
|---|---|
| **Array-of-structs point storage with a padded fourth component.** PCL's `float data[4]` pays 16 bytes for a 12-byte payload and forces every access to pull y, z and a pad into cache | [`point_types.hpp#L211-L219`](https://github.com/PointCloudLibrary/pcl/blob/3346843ea6b97697a1577293aa9cdf236b5c7ffb/common/include/pcl/impl/point_types.hpp#L211-L219). Spec §6 already says structure-of-arrays; this is the concrete thing it is avoiding |
| **float32 world coordinates.** Measured: 0.015625 m at 500 km, 4 096× the same storage's error at the origin, RMS 7 mm. Reported independently as visible shimmering | measured, §Precision; Open3D#6525; PCL#4756 and PCL#1010 for the library-wide version. **P-05** |
| **An index that stores a point's identity once per level.** Open3D's octree appends the point index to every internal node on the path — 72 bytes/point of payload at depth 8 before any object overhead, 102.9 bytes/point measured at saturation, and **2.7× the size of the points it indexes** | [`Octree.cpp#L131-L138`](https://github.com/isl-org/Open3D/blob/1e7b17438687a0b0c1e5a7187321ac7044afe275/cpp/open3d/geometry/Octree.cpp#L131-L138), [`Octree.h#L160-L162`](https://github.com/isl-org/Open3D/blob/1e7b17438687a0b0c1e5a7187321ac7044afe275/cpp/open3d/geometry/Octree.h#L160-L162); measured, §The index. **P-13, root cause corrected** |
| **An index that owns a private copy of the coordinates.** Both kd-tree implementations duplicate the cloud; a memory-mapped chunk store whose index re-materialises the same points in RAM has mapped nothing | [`KDTreeFlann.h#L100-L106`](https://github.com/isl-org/Open3D/blob/1e7b17438687a0b0c1e5a7187321ac7044afe275/cpp/open3d/geometry/KDTreeFlann.h#L100-L106), [`kdtree_flann.hpp#L440`](https://github.com/PointCloudLibrary/pcl/blob/3346843ea6b97697a1577293aa9cdf236b5c7ffb/kdtree/include/pcl/kdtree/impl/kdtree_flann.hpp#L440); measured 41–43 bytes/point on top. **Spec §8** |
| **A single-threaded index build.** 35.93 s at 10⁷ points and **324.4 s at 10⁸** on one of 32 cores, in a library that parallelises normal estimation in the same directory. This, not memory, is what actually broke first in the measurement | measured; [`Octree.cpp#L564-L575`](https://github.com/isl-org/Open3D/blob/1e7b17438687a0b0c1e5a7187321ac7044afe275/cpp/open3d/geometry/Octree.cpp#L564-L575) against [`EstimateNormals.cpp#L301`](https://github.com/isl-org/Open3D/blob/1e7b17438687a0b0c1e5a7187321ac7044afe275/cpp/open3d/geometry/EstimateNormals.cpp#L301) |
| **A fixed-size accumulation buffer with no bounds check on a hot path.** Potree's sampler writes into a `thread_local vector<Point>(1'000'000)` by index; two tracker reports (a slowdown attributed to that line by name, and a segfault in that function) | [`sampler_poisson.h#L112`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/include/sampler_poisson.h#L112), [`#L213-L215`](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/Converter/include/sampler_poisson.h#L213-L215); PotreeConverter#501, #550. **Borrow the layout, not this loop** |
| **A budget that caps drawing but not residency.** Potree's `pointBudget` stops the traversal; no eviction of loaded nodes was found, and the tracker carries "crashing after some time" with a 41.6 M budget | [`Potree_update_visibility.js#L282-L284`](https://github.com/potree/potree/blob/3013577379b5c8530ebca3cdc980f7585ae2320f/src/Potree_update_visibility.js#L282-L284); Potree#1002. Our `pointcloud` module needs an eviction policy stated alongside the budget, or it inherits this |
| **A 32-bit byte count anywhere in an IO path.** Open3D's tensor writer fails past 2.1 GB with `std::bad_alloc` on a machine with free memory; our 10⁸-point f64 cloud is already 2.4 GB | Open3D#6043 |

## Risks

**P-13 was not reproduced as written, and this note does not pretend otherwise.** The row predicted
that point clouds exceed memory; on this machine, at 10⁸ points, nothing did. Neither the cloud nor
the index nor the kd-tree raised a `MemoryError`. What the measurement found instead — an index
2.7× the size of its data, built in 324 s on one core — is a *worse* problem for an interactive
modeller and a *different* one for the row to record, so P-13's root cause and status are edited
rather than confirmed. A row that gets ticked by a measurement that did not actually happen is
worse than an open one.

**The measurement is one library on one machine with synthetic data, and each of those three is a
real limitation.** Uniform random points are the *friendly* case for a fixed-depth octree — real
scans are clustered, so the same point count produces deeper subtrees and a higher node count at
the same `max_depth`, and every octree number here is a lower bound for real data. A benchmark
scan in `reference/` would fix this; none exists yet.

**Nothing here measures the design we are actually proposing.** All of it measures what an in-core
library costs. The claim that a chunked, memory-mapped, partition-LOD octree does better is
*inferred from Potree's source and from third-party reports on its tracker*, not measured — and one
of those reports says the converter used >100 GB on 6.5 billion points. The spike that would settle
it is: build our chunked octree over 10⁸ synthetic points with chunks mapped from a file, and
measure resident memory during a camera fly-through. That belongs against spec §8 before M6, not
after.

**Nothing about calling PDAL from DynLex was demonstrated, and one claim here was wrong before it
was checked.** A draft of this note asserted
a PDAL C API on the strength of a filename that does not exist; there is none at tag `2.10.2`, and
the claim is withdrawn here rather than softened, with the grep that would have caught it recorded
above. What
remains is the weaker statement that a JSON pipeline is easier to drive across a boundary than a C++
class hierarchy, which is plausible and untested. If the ingest decision above is taken seriously,
the first step is a spike that actually reads a LAZ file through PDAL from our side of the
boundary — and that spike needs the native library built, which is the same obstacle that stopped
the wheel from installing here.

**The precision recommendation trades one problem for another.** An int32 quantum is uniform, but
it is *chosen once per file*: a project that mixes a 1 mm terrestrial scan with a 5 cm airborne
survey either wastes range or loses the fine one. Potree sets the scale per file and PDAL per LAS
header; our kernel would set it per tile, which is better but not free. Whoever writes ADR-0006's
point-cloud row must decide whether the scale is per tile, per cloud or per chunk, and that
decision is not made here.

## Sources

- PCL — [PointCloudLibrary/pcl](https://github.com/PointCloudLibrary/pcl/tree/3346843ea6b97697a1577293aa9cdf236b5c7ffb) at tag `pcl-1.15.1`
- Open3D — [isl-org/Open3D](https://github.com/isl-org/Open3D/tree/1e7b17438687a0b0c1e5a7187321ac7044afe275) at tag `v0.19.0`
- PDAL — [PDAL/PDAL](https://github.com/PDAL/PDAL/tree/27008f6241be44585c866a29dfc13bb16d678dab) at tag `2.10.2`
- Potree — [potree/potree](https://github.com/potree/potree/tree/3013577379b5c8530ebca3cdc980f7585ae2320f) at tag `1.8.2`
- PotreeConverter — [potree/PotreeConverter](https://github.com/potree/PotreeConverter/tree/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7) at tag `2.1.3`
- Tickets: [Open3D#6525](https://github.com/isl-org/Open3D/issues/6525), [#6043](https://github.com/isl-org/Open3D/issues/6043), [#3321](https://github.com/isl-org/Open3D/issues/3321); [PCL#4756](https://github.com/PointCloudLibrary/pcl/issues/4756), [#1010](https://github.com/PointCloudLibrary/pcl/issues/1010); [PDAL#1818](https://github.com/PDAL/PDAL/issues/1818), [#4193](https://github.com/PDAL/PDAL/issues/4193); [PotreeConverter#501](https://github.com/potree/PotreeConverter/issues/501), [#550](https://github.com/potree/PotreeConverter/issues/550); [Potree#1002](https://github.com/potree/potree/issues/1002)
- Measurements — [`spikes/pointcloud-scale/`](../../../spikes/pointcloud-scale/), results in [`results/open3d.md`](../../../spikes/pointcloud-scale/results/open3d.md)
- **Named but not read for this note** (listed for provenance only; no claim above rests on them):
  M. Schütz, *Potree: Rendering Large Point Clouds in Web Browsers*, master's thesis, TU Wien, 2016
  ([PDF](https://www.cg.tuwien.ac.at/research/publications/2016/SCHUETZ-2016-POT/SCHUETZ-2016-POT-thesis.pdf));
  M. Schütz, S. Ohrhallinger, M. Wimmer, *Fast Out-of-Core Octree Generation for Massive Point
  Clouds*, 2020
  ([page](https://www.cg.tuwien.ac.at/research/publications/2020/SCHUETZ-2020-MPC/)). Both are
  named as the basis of the design in
  [PotreeConverter's README](https://github.com/potree/PotreeConverter/blob/a70ef212198b0e5ae1d071713a0c8cbda8fcc9a7/README.md).
