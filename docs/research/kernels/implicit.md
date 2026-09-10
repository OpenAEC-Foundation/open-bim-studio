# OpenVDB and libfive — the implicit representation, dual contouring, and SDF-from-mesh

**Decision question:** Kernel spec §4 proposes implicit (SDF) as the fourth first-class
representation — "a tree of signed-distance primitives and combinators… evaluated on demand and
sampled to a mesh," chosen for "offsets, blends, organic shapes, cheap CSG previews" — and spec §9
schedules its SDF tree and dual contouring for M5. ADR-0005's evidence table has an empty cell for
"Implicit representation earns its place," pointed at this file's §Verdict. The question answered
here: **does an implicit representation earn a place in the kernel, what does meshing (dual
contouring on an adaptive octree) cost, and what does converting a closed mesh to an SDF require?**

**Serves:** ADR-0005 (evidence row "Implicit representation earns its place"); kernel spec §4
(implicit representation, conversions), §9 (M5); `problems.md` — adds to P-05, adds P-21, P-22,
P-23.

**Status:** draft
**Author:** research programme, phase 2
**Last updated:** 2026-09-10

> Source-and-literature note; no spike ran (§Measurements) — the brief's optional cheap path (a
> `pyopenvdb`/`openvdb` wheel) was checked and does not exist for this platform, so every
> performance claim below is **claimed** or **inferred** from source, never **measured**.

---

## Summary

An implicit representation earns the place spec §4 already gives it, for a narrower job than the
other three: OpenVDB's CSG on level sets is genuinely free (`min`/`max` of two grids) and its
dual-contouring-style mesher is fast by construction, but its vertex placement — the mean of linear
edge zero-crossings, not a Hermite/QEF fit — rounds off sharp corners by design, confirming the
spec's own framing (offsets, blends, organic shapes, previews — not exact geometry). libfive's dual
contouring does fit Hermite data via a QEF solve and can hit a sharp corner in principle — its own
maintainer nonetheless confirms self-intersections in its recommended solver, and says its two
intersection-free alternatives buy that by admitting zero-area triangles and zero-volume cracks.
Mesh→SDF conversion in OpenVDB requires a closed surface but enforces this only in a doc comment;
CSG on level sets requires the two grids to share a transform and checks neither that nor the
narrow-band assumptions. Both gaps are new `problems.md` rows (P-22, P-23), alongside a
sharp-feature-rounding row (P-21) and an addition to P-05 on float32 mesh output.

## What was read, and at which commit

| Library | Pinned at | Commit |
|---|---|---|
| OpenVDB | tag `v13.0.0` (latest release) | [`7c03e1f0…`](https://github.com/AcademySoftwareFoundation/openvdb/tree/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38) |
| libfive | `master`, pinned by hash — no semver release tags exist (`git ls-remote --tags` returns only `last-chance`, `rip-dmc`) | [`c9e97343…`](https://github.com/libfive/libfive/tree/c9e97343e0af998cd1696e85583eccba95532b96), dated 2025-11-12 |

Both cloned shallow into the scratchpad, never into the repository, confirmed by `git rev-parse
HEAD` / `git log -1 --format='%H %ci'` after clone.

Areas read: OpenVDB — `openvdb.h` (grid typedefs), `tree/Tree.h` (`Tree4`), `Types.h`
(`LEVEL_SET_HALF_WIDTH`), `tools/LevelSetSphere.h`, `tools/Composite.h` (CSG), `tools/
VolumeToMesh.h`, `tools/MeshToVolume.h`, `tools/SignedFloodFill.h`, `math/Transform.h`, `LICENSE`,
`doc/changes.txt`, `doc/nanovdb/FAQ.md`. libfive — `include/libfive/tree/tree.hpp`, `include/
libfive/eval/{interval,eval_array}.hpp`, `src/render/brep/dc/` and `mesh.cpp`, `include/libfive/
render/brep/settings.hpp`, `include/libfive.h`, licence headers across `libfive/`, `libfive/bind/
guile/`, `studio/`. Full paths are given inline with each citation below.

## OpenVDB

### The sparse tree and default grid

`FloatGrid`'s tree is a four-level tree (root, two internal levels, leaf) with branching factors
5-4-3, defined by `Tree4` and instantiated as `FloatTree`/`DoubleTree`:

```cpp
template<typename T, Index N1=5, Index N2=4, Index N3=3>
struct Tree4 { using Type = Tree<RootNode<InternalNode<InternalNode<LeafNode<T, N3>, N2>, N1>>>; };
using DoubleGrid = Grid<tree::Tree4<double, 5, 4, 3>::Type>;
using FloatGrid  = Grid<tree::Tree4<float,  5, 4, 3>::Type>;
```
— [`tree/Tree.h#L1123-L1127`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/openvdb/openvdb/tree/Tree.h#L1123-L1127)
(comment there calls this "the standard tree configuration"),
[`openvdb.h#L54-L76`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/openvdb/openvdb/openvdb.h#L54-L76).
`DoubleGrid` is a real, usable type, but every factory and cookbook example read here defaults to
`FloatGrid`.

### Level sets and the narrow band

A level set's active voxels form a narrow band around the isosurface; inactive voxels carry a
constant background (`±background`). Default half-width is three voxels —
`static const Real LEVEL_SET_HALF_WIDTH = 3;`
([`Types.h#L528`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/openvdb/openvdb/Types.h#L528)),
the default `halfWidth` throughout `tools/LevelSetSphere.h`
([`#L53`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/openvdb/openvdb/tools/LevelSetSphere.h#L53)).
So the background value is `voxelSize × halfWidth` in world units — precision budget is a function
of voxel size, not a fixed tolerance, the same class of point P-05 already tracks.

### CSG on level sets — and what it does not check

`csgUnion`/`csgIntersection`/`csgDifference` each call `composite::validateLevelSet`, whose entire
check is the background value's **sign**, nothing else:

```cpp
if (!(tree.background() > zero)) { /* throw ValueError */ }
if (!(-tree.background() < zero)) { /* throw ValueError */ }
```
— [`Composite.h#L719-L736`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/openvdb/openvdb/tools/Composite.h#L719-L736).
The operation then runs a `tree::DynamicNodeManager` purely in **index space**
([`Composite.h#L884-L930`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/openvdb/openvdb/tools/Composite.h#L884-L930)):
no line in this file reads or compares `a.transform()` and `b.transform()` — coordinate `(i,j,k)`
in tree A is assumed to mean the same world point as `(i,j,k)` in tree B. The library's own
cookbook confirms this is by design: `DualGridSampler` "checks if the source and target grids are
aligned (that is, they have the same transform)," implying the ordinary CSG path does not, and
`resampleToMatch` is offered as the tool to align two grids *before* an operation that needs it —
*claimed*, [`doc/examplecode.txt#L790-L794`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/doc/examplecode.txt#L790-L794).
New — `problems.md` P-22.

### Meshing — `tools::volumeToMesh`

Dual-contouring-like, not marching-cubes: one candidate vertex per sign-changing cell, quads by
default, with an explicit non-manifold guard (`isNonManifold`,
[`VolumeToMesh.h#L803-L810`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/openvdb/openvdb/tools/VolumeToMesh.h#L803-L810)).
**The vertex position is the plain average of the cell's linear edge zero-crossings — not a
Hermite/QEF fit:**

```cpp
/// @brief Computes the average cell point for a given edge group.
inline Vec3d computePoint(const std::array<double, 8>& values, const unsigned char signs,
    const unsigned char edgeGroup, const double iso) {
    Vec3d avg(0.0, 0.0, 0.0); int samples = 0;
    if (sEdgeGroupTable[signs][1] == edgeGroup) { avg[0] += evalZeroCrossing(values[0], values[1], iso); ++samples; }
    // … seven more edges, same pattern, then avg /= samples
```
— [`VolumeToMesh.h#L1010-L1024`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/openvdb/openvdb/tools/VolumeToMesh.h#L1010-L1024) —
no gradient, no normal, no error-minimizing solve. Adaptivity is a separate, later pass:
`MergeVoxelRegions`/`isMergeable` compares gradients only to decide whether a merge is *safe*, never
to move a vertex toward a sharper feature
([`#L975-L1006`, `#L2054-L2119`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/openvdb/openvdb/tools/VolumeToMesh.h#L975-L2119));
the `[0,1]` `adaptivity` parameter is that merge threshold
([`#L64-L79`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/openvdb/openvdb/tools/VolumeToMesh.h#L64-L79)),
not a feature-preservation knob. This note found no citation to the DC paper inside the OpenVDB
source itself; "dual contouring" is a third-party, claimed description of the algorithm shape
(one dual vertex per crossed cell), consistent with what the source shows.

### Mesh → volume — `tools::meshToVolume`

The file's own header states the requirement narrower than "manifold": "The signed distance field
conversion requires a closed surface but not necessarily a manifold surface… independent of mesh
surface normals / polygon orientation" — *claimed*,
[`MeshToVolume.h#L9-L11`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/openvdb/openvdb/tools/MeshToVolume.h#L9-L11).
"Closed" is enforced nowhere in this file as a runtime check. The mechanism that depends on it,
sign propagation, states its precondition only as a warning: "@warning This method should only be
used on closed, narrow-band level sets"
([`SignedFloodFill.h#L54`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/openvdb/openvdb/tools/SignedFloodFill.h#L54)),
called unconditionally from the signed path at
[`MeshToVolume.h#L3503-L3509`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/openvdb/openvdb/tools/MeshToVolume.h#L3503-L3509).
`UNSIGNED_DISTANCE_FIELD` is an opt-in escape that "does not require a closed watertight mesh"
([`#L65-L68`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/openvdb/openvdb/tools/MeshToVolume.h#L65-L68))
but produces an unsigned field the CSG tools above reject (they require `background() > 0` and
`-background() < 0`). New — `problems.md` P-23.

### Precision, transform, threading, licence, NanoVDB

- **Value type:** `float` by default; `DoubleGrid` exists but was not the default anywhere read.
- **Mesh interchange type is float32 regardless of grid type:** `VolumeToMesh`'s output is
  `PointList = std::unique_ptr<Vec3s[]>`
  ([`VolumeToMesh.h#L161`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/openvdb/openvdb/tools/VolumeToMesh.h#L161)),
  `Vec3s = Vec3<float>`
  ([`math/Vec3.h#L664`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/openvdb/openvdb/math/Vec3.h#L664)) —
  meshing a `DoubleGrid` still returns float32 vertices, *inferred* from the type, not run.
- **Transform is always double:** `Vec3d indexToWorld/worldToIndex`
  ([`math/Transform.h#L108-L111`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/openvdb/openvdb/math/Transform.h#L108-L111)),
  independent of grid value type — the frame origin can be f64, but the meshed geometry inside it
  cannot (§Connecting to existing evidence).
- **Threading:** TBB throughout — `Composite.h`, `VolumeToMesh.h`, `MeshToVolume.h` all include
  `tbb/parallel_for.h`/`parallel_reduce.h`/`task_arena.h` and drive `DynamicNodeManager` or
  explicit ranges over leaf/node arrays. Not benchmarked here.
- **Licence:** Apache-2.0, verified against
  [`LICENSE`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/openvdb/openvdb/LICENSE)
  and the SPDX header of 89 of 90 headers under `tools/`, `tree/`, `math/` — *measured*, `grep -rl
  "SPDX-License-Identifier" tools/*.h tree/*.h math/*.h`. The exception is `math/Half.h`, BSD-3-
  Clause ([`#L2`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/openvdb/openvdb/math/Half.h#L2)),
  inherited from Imath. Relicensed from MPL-2.0 at v12.0.0 (2024-10-31) — *claimed*,
  [`doc/changes.txt#L349-L356`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/doc/changes.txt#L349-L356).
  **Correction against the task brief:** the brief describes this as "Apache-2.0 with LLVM
  exception." No such clause was found in `LICENSE` at the pinned tag or in any header read — the
  SPDX identifier is the bare string `Apache-2.0`.
- **NanoVDB**, one paragraph per brief: a GPU-friendly, header-only, **static-topology** companion
  — "while values can be modified in a NanoVDB grid its tree topology cannot" — *claimed*,
  [`doc/nanovdb/FAQ.md`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/doc/nanovdb/FAQ.md).
  Targets ray-tracing/random-access GPU workloads, converted from an OpenVDB grid; not a drop-in
  for the kernel's own `gpu` buffer-packing path (spec §6).

### Known issues, OpenVDB

| # | Issue | Reporter (assoc.) | State | What it shows |
|---|---|---|---|---|
| [#242](https://github.com/AcademySoftwareFoundation/openvdb/issues/242) | Open-surface `volumeToMesh` "creates self intersecting triangles in all cases" | `Danock22` (NONE) | open since 2018, no reply | Third-party, unconfirmed, but consistent with §Mesh → volume: closedness is documented, not checked |
| [#903](https://github.com/AcademySoftwareFoundation/openvdb/issues/903) | Two spheres separated by a small exact gap flip sign inside the gap well before voxel size approaches gap width | `UlysseV` (NONE) | open, maintainer replied | **Maintainer-confirmed** (`jmlait`, CONTRIBUTOR): "we do not treat the mesh as ground-truth… when it comes from an artist, it often isn't manifold, watertight, non-self-intersecting" — intentional smoothing assumes imperfect input and produces the wrong sign near close features |
| [#1992](https://github.com/AcademySoftwareFoundation/openvdb/issues/1992) | `resampleToMatch` "is not translation invariant for level-sets" — the tool required to align grids before cross-transform CSG measurably degrades after a pure translation | `andrewerf` (NONE) | open, no reply | Weakens "just resample first" as a complete answer to the missing transform check in §CSG on level sets |
| [#1354](https://github.com/AcademySoftwareFoundation/openvdb/issues/1354) | CSG on a grid built from a point cloud "does not work" | `SimonNgj` (NONE) | closed by workaround, not by a fix | Tangled with an unrelated type-cast bug in the reporter's own code — flagged as suggestive, **not** cited as confirmation of the transform gap |

## libfive

### The function tree and C API

`Tree` is a reference-counted, immutable wrapper over a `TreeData` variant, deliberately not a
`shared_ptr`/`intrusive_ptr` because the C API needs to release a pointer without decrementing a
refcount ([`tree.hpp#L33-L46`](https://github.com/libfive/libfive/blob/c9e97343e0af998cd1696e85583eccba95532b96/libfive/include/libfive/tree/tree.hpp#L33-L46)).
That C API is real and current — `extern "C"` from `libfive.h`
([`#L15`](https://github.com/libfive/libfive/blob/c9e97343e0af998cd1696e85583eccba95532b96/libfive/include/libfive.h#L15)),
exposing tree constructors and meshing entry points `libfive_tree_render_mesh`/
`libfive_tree_save_mesh(es)`
([`#L187-L222`, `#L356-L404`](https://github.com/libfive/libfive/blob/c9e97343e0af998cd1696e85583eccba95532b96/libfive/include/libfive.h#L187-L404)).
`libfive_mesh.verts` is `libfive_vec3*`, and `libfive_vec3 = {float x, y, z}`
([`#L46`, `#L99-L104`](https://github.com/libfive/libfive/blob/c9e97343e0af998cd1696e85583eccba95532b96/libfive/include/libfive.h#L46)) —
**answering the brief's question**: unlike OpenVDB (C++ template headers only — *measured*, `grep
-rl 'extern "C"' openvdb/openvdb/` found only two internal files unrelated to a public API),
libfive has a genuine C ABI a DynLex FFI could call without a C++ shim, but every value crossing it
is float32.

### Evaluators

Interval (subdivision pruning), array (bulk sampling), and feature/derivative (gradients, used by
the vertex solve below) evaluators sit over the tree. Interval and array are both float32:
`Interval(float lower, float upper)` wrapping `boost::numeric::interval<float>`
([`eval/interval.hpp#L20-L31`](https://github.com/libfive/libfive/blob/c9e97343e0af998cd1696e85583eccba95532b96/libfive/include/libfive/eval/interval.hpp#L20-L31));
`Eigen::Array<float, Eigen::Dynamic, N, Eigen::RowMajor> v;`, `N = 256`
([`eval/eval_array.hpp#L73`](https://github.com/libfive/libfive/blob/c9e97343e0af998cd1696e85583eccba95532b96/libfive/include/libfive/eval/eval_array.hpp#L73)).
Double appears only inside the octree's vertex solve (next section) — field evaluation, the part
that runs per-sample across the whole octree, is float32 throughout.

### Meshing — dual and manifold dual contouring

`BRepSettings::alg` selects `DUAL_CONTOURING` (default), `ISO_SIMPLEX`, or `HYBRID`
([`settings.hpp#L20-L37`](https://github.com/libfive/libfive/blob/c9e97343e0af998cd1696e85583eccba95532b96/libfive/include/libfive/render/brep/settings.hpp#L20-L37)).
Octree subdivision: `min_feature`, "subdivided until the smallest region edge is below
`min_feature` in size" (default `0.1`); cell merging: `max_err`, "if very small, only linear
regions are merged" (default `1e-8`)
([`#L44-L53`](https://github.com/libfive/libfive/blob/c9e97343e0af998cd1696e85583eccba95532b96/libfive/include/libfive/render/brep/settings.hpp#L44-L53)).
`Mesh::render` dispatches on `alg` to one of three worker-pool/mesher pairs
([`mesh.cpp#L35-L90`](https://github.com/libfive/libfive/blob/c9e97343e0af998cd1696e85583eccba95532b96/libfive/src/render/brep/mesh.cpp#L35-L90)).

The DC vertex is a **QEF solve** (SVD pseudo-inverse over accumulated gradient data), in **double**
even though the field data that built it is float32:

```cpp
Eigen::SelfAdjointEigenSolver<Eigen::Matrix<double, N, N>> es(this->leaf->AtA);
// … truncate near-singular eigenvalues, pseudo-invert …
Vec v = AtAp * (this->leaf->AtB - (this->leaf->AtA * center)) + center;   // returns the QEF error
```
— [`dc/dc_tree.inl#L740-L809`](https://github.com/libfive/libfive/blob/c9e97343e0af998cd1696e85583eccba95532b96/libfive/src/render/brep/dc/dc_tree.inl#L740-L809).
The manifold-preserving collapse criterion cites Ju et al. in a code comment ("the sign in the
middle of a coarse edge/face/cube must agree with the sign of at least one of its endpoints/
corners… [Ju et al, 2002]") —
[`dc/dc_tree3.cpp#L20-L27`](https://github.com/libfive/libfive/blob/c9e97343e0af998cd1696e85583eccba95532b96/libfive/src/render/brep/dc/dc_tree3.cpp#L20-L27),
re-checked before coarser collapse at
[`dc_tree.inl#L640-L661`](https://github.com/libfive/libfive/blob/c9e97343e0af998cd1696e85583eccba95532b96/libfive/src/render/brep/dc/dc_tree.inl#L640-L661),
implemented via `manifold_tables.cpp` — this is the library's version of Schaefer/Ju/Warren's
Manifold Dual Contouring (2007), the octree topology-preservation half of that paper; guaranteed
crack-free adaptive simplification is not separately verified here.

### Precision and licence, per directory — measured

Field evaluation float32, vertex solve float64 internally, truncated to float32 at the C API
boundary — the same "more precise internally, float32 on output" pattern OpenVDB shows. No
evaluator-wide double-precision switch was found in `eval/`.

| Directory | Licence | Evidence |
|---|---|---|
| `libfive/` (core kernel, C API) | MPL-2.0 | 192 of 197 files matched — *measured*, `grep -rl "Mozilla Public" libfive/ \| wc -l` |
| `libfive/bind/guile/` | GPL (2+) | Exactly the 5 `.scm` files here — *measured*, `grep -rl "GNU General Public" libfive/` |
| `studio/` (GUI) | GPL-2.0-or-later | 60 files, 0 MPL — *measured*, header e.g. [`studio/src/app.cpp#L1-L8`](https://github.com/libfive/libfive/blob/c9e97343e0af998cd1696e85583eccba95532b96/studio/src/app.cpp#L1-L8) |

The core kernel and its C API — everything a build-on decision would link — is MPL-2.0; only the
optional Guile layer and the GUI are GPL, and neither is required to use the kernel or C API.

### Known issues, libfive

| # | Issue | Reporter (assoc.) | State | What it shows |
|---|---|---|---|---|
| [#284](https://github.com/libfive/libfive/issues/284) | "Mesh Quality" — exported meshes have intersecting triangles (DC) or wrinkles/lost sharp features (ISO/hybrid) | NONE | open, maintainer replied | **Maintainer-confirmed** (`mkeeter`, MEMBER, project author): "DC will have self-intersections… Iso and hybrid both have wrinkles and issues preserving sharp features… may have zero-area triangles and other questionable geometry (e.g. zero-volume cracks) to keep the triangle graph manifold." No configuration is simultaneously intersection-free, crack-free and feature-preserving |
| [#562](https://github.com/libfive/libfive/issues/562) | "Feature resolution is unexpectedly impacted by the size of the bounding box" — the same `min_feature` yields very different subdivision depth depending on bounding-box size, not feature size | CONTRIBUTOR | open, maintainer replied, unresolved | **Maintainer-confirmed** (`mkeeter`): traced to `Region::withResolution`'s `(upper-lower).minCoeff()`; two contributors agree resolution should be per-unit; a fourth reporter (NONE) reproduces it independently via third-party Unity bindings |

### Measurements

None. The brief's optional cheap-measurement path (a `pyopenvdb`/`openvdb` Python wheel) was
checked against Python 3.12.10 on this machine: `pip index versions pyopenvdb` and `pip index
versions openvdb` both report **no matching distribution** — *measured*, the check itself. No
wheel exists for this platform, so the spike was skipped per the brief's instruction; every
timing/triangle-count claim above is either read from source (labelled) or absent.

## The papers

- Ju, Losasso, Schaefer, Warren, **"Dual Contouring of Hermite Data,"** SIGGRAPH 2002 — the method
  libfive's DC vertex solve implements and cites in source (§Meshing above). *Claimed*, from
  third-party summaries, not the paper text itself: contours Hermite-tagged edges (position +
  normal) without explicit feature detection, via a QEF, simplified by an octree.
- Schaefer, Ju, Warren, **"Manifold Dual Contouring,"** IEEE TVCG 13(3), 2007. DOI:
  [10.1109/TVCG.2007.1012](https://doi.org/10.1109/TVCG.2007.1012). *Claimed*: extends DC to
  guarantee a manifold mesh under adaptive simplification via a topology-preserving
  vertex-clustering rule — the rule libfive's `manifold_tables.cpp` implements and attributes to
  "[Ju et al, 2002]" in its own comments (§Meshing; the in-source attribution and this paper's
  authorship differ, reported as read rather than reconciled).
- Museth, **"VDB: High-Resolution Sparse Volumes with Dynamic Topology,"** ACM TOG 32(3), 2013.
  DOI: [10.1145/2487228.2487235](https://doi.org/10.1145/2487228.2487235). *Claimed*: the paper
  behind OpenVDB's tree design (§The sparse tree). Only a scanned/encoded PDF was obtainable, not
  machine-readable by the tools available, so this note does not quote its meshing section — the
  meshing description above is read entirely from current source, not the paper.
- Lorensen, Cline, **"Marching Cubes,"** SIGGRAPH 1987 — contrast only, not read: MC places one
  vertex per cell *edge*; DC places one vertex *inside* each crossed cell (the dual of the MC
  grid), which is why DC-family meshers emit quads and, in the QEF variant, can recover a sharp
  interior feature an edge-vertex scheme cannot.
- Quilez, **"distfunctions"**, an informal web page, not a paper:
  <https://iquilezles.org/articles/distfunctions/>. *Claimed*, cited only because spec §4 names
  "smooth blends" among the implicit combinators and this page is the commonly-cited source for
  smooth-min/-max formulas — not verified against either library's source in this note.

## Connecting to existing evidence

**Booleans (manifold.md, cgal.md).** Both measure mesh booleans that must resolve an intersection
graph; implicit CSG has none — `min`/`max` on two level sets is O(voxels), which is the sense in
which spec §4's "implicit × implicit → a new implicit node; free" (ADR-0005 Decision) is literally
true at the tree level. But the *meshed* output is an ordinary mesh with no special validity
guarantee, needing the same closed/manifold/volume-conserving checks those notes already require.
OpenVDB's `isNonManifold` guard (§Meshing) prevents one artefact (a merge creating a non-manifold
vertex) but says nothing about self-intersection, which `computePoint` averaging can itself produce
once adaptivity merges cells unevenly. "Free" describes the CSG step, not the round trip through a
mesh.

**Float32 precision (P-05: blender.md, manifold.md, pointclouds.md).** The implicit representation
reproduces the same two-layer pattern those notes measured for float32 storage at distance from a
frame origin — OpenVDB's mesh interchange type (`Vec3s`) and libfive's C API type (`libfive_vec3`)
are both float32 regardless of internal precision, while both libraries' *transforms* (OpenVDB) or
*internal solves* (libfive's QEF) are double. See the P-05 addition in `problems.md`, sourced from
§Precision, transform… (OpenVDB) and §Precision and licence… (libfive), both *inferred* from type
declarations, not measured with a spike.

## Evaluation

Criteria from [`README.md`](README.md). Both are libraries, not layered kernels; rows not
applicable to a design-reference library say why.

| Criterion | OpenVDB | libfive | Evidence type |
|---|---|---|---|
| **License** | Apache-2.0, whole library bar one BSD-3 header | MPL-2.0 core + C API; GPL only in Guile bindings and the GUI | measured |
| **Representations held natively** | Sparse voxel grids: level sets, fog volumes, point-data/attribute grids. No persistent B-rep or mesh — meshing is a one-shot conversion | Function tree of implicit primitives/combinators (the representation itself); no persistent voxel grid, no B-rep | measured/inferred |
| **Boolean robustness** | Not torture-set-testable — no triangle arrangement to fail on; cost moves to meshing (§Meshing) | Same: tree-level CSG cannot itself fail; the mesher can (maintainer-confirmed self-intersections, #284) | source, not applicable |
| **Tolerance and precision model** | Narrow band = `voxelSize × halfWidth` (default 3); float32 value type and mesh output by default | `min_feature`/`max_err` explicit knobs; float32 field eval, float64 QEF solve, float32 C-API output | measured (source) |
| **Incremental evaluation** | **No** — grids rebuilt, not patched, by any tool read; no dependency graph found | **No** — `Mesh::render` rebuilds the octree from the whole `Tree`/`Region` every call; no cited caching across calls | inferred |
| **Threading model** | TBB throughout (`parallel_for`, `DynamicNodeManager`); not benchmarked | `BRepSettings::workers` (default 8) drives a worker-pool build; not benchmarked | source |
| **GPU path** | NanoVDB — separate, static-topology, GPU-resident, ray-tracing-oriented; not the kernel's own buffer-packing path | None found — Studio's GL shaders rasterize CPU-meshed triangles only, no raymarching shader in the files read | measured (presence/absence) |
| **IFC coverage** | Not applicable | Not applicable | not applicable |
| **Performance** | Not measured — no spike (§Measurements) | Not measured — no spike | not applicable |
| **Embeddability** | C++ header/template library, TBB dependency, no C ABI | Header-only core plus a genuine `extern "C"` ABI — more directly embeddable via FFI | measured |
| **2D derivation** | Not traced in this note | 2D DC/simplex variants exist (`dc_tree2.cpp`, `simplex_tree2.cpp`) — noted, not traced | inferred (listing only) |
| **Maturity** | Active ASWF project; `v13.0.0` a current release tag | Single-maintainer-led; no semver release tags exist at all — a signal read as such, not asserted from code | claimed/inferred |
| **AI familiarity** | High: long public history, ASWF project. One column, never a tiebreaker (R-09) | Moderate: smaller public corpus than OpenVDB or CGAL | inferred |

## The twelve questions

1. Re-evaluate one changed element? No for both — §Evaluation, Incremental evaluation.
2. IFC round trip? Not applicable.
3. Driven in-process from DynLex? OpenVDB: C++ only, no C ABI found — would need a C++ shim.
   libfive: yes directly, `libfive.h` is `extern "C"`.
4. Threading model? §Evaluation — TBB (OpenVDB) vs. a fixed worker pool (libfive); neither
   benchmarked.
5. What breaks first at scale? Not measured for either. Inferred: OpenVDB's sparse-tree memory is
   bounded by active voxel count in the narrow band, not the bounding volume (Museth 2013,
   claimed, not re-derived); libfive's octree depth is bounded by `min_feature` relative to the
   *bounding box's* smallest axis, not local feature size (#562).
6. Numeric precision, configurable? OpenVDB: `FloatGrid` default, `DoubleGrid` available but mesh
   output stays float32 regardless. libfive: float32 evaluators fixed, double only inside the QEF
   solve, float32 at the C API boundary — no evaluator-wide double switch found.
7. Operate on a subset — one tile, one region? OpenVDB: yes natively, the sparse tree only
   allocates active regions. libfive: `Mesh::render` takes an explicit `Region<3>`, but every call
   still walks the whole function tree fresh.
8. Who maintains it? §Evaluation, Maturity.
9. Documented failure modes, with issue links? §Known issues, OpenVDB and libfive.
10. Representations held natively? §Evaluation.
11. GPU path? §Evaluation, GPU path.
12. What would we take, what would we avoid? §Verdict, below.

## Verdict

### Does an implicit representation earn a place? — Yes, for the scope spec §4 already gives it

Level-set CSG is genuinely cheap and free of the intersection-graph problem that makes mesh and
B-rep booleans hard (§Connecting to existing evidence) — a real capability none of the kernel's
other three representations offers as directly, and why spec §4 lists implicit for "offsets,
blends, organic shapes, cheap CSG previews." It is not a substitute for B-rep or mesh on exact
geometry: OpenVDB's dual-vertex placement is an unweighted average of edge crossings with no
feature term (§Meshing), rounding a wall's corner rather than preserving it, and libfive's
feature-preserving QEF variant is the one its own maintainer confirms produces self-intersections
(#284). Spec §4's own framing — implicit for organic shapes and previews, B-rep for "exact
dimensions, true curved faces" — is confirmed by source, not merely restated.

### What does meshing cost? — Claimed complexity only; no measurement

No spike ran (§Measurements). From source: OpenVDB's cost is dominated by active (near-surface)
voxel count, since the sparse tree never allocates the interior/exterior bulk — *claimed*,
following from the narrow-band design, not independently measured. libfive's cost is dominated by
octree depth, set by `min_feature` relative to the *whole bounding region's* smallest axis rather
than local feature size (#562) — a caller-visible performance footgun surfaced as `problems.md`
material below, not as a number, because no number was produced.

### What does SDF-from-mesh require? — A closed mesh, checked by comment only

OpenVDB's own header states the requirement ("requires a closed surface… independent of… polygon
orientation") but enforces nothing at the call site; the sign-propagation step it depends on
carries only a doc-comment warning (`SignedFloodFill.h`). Two issues — one third-party and
unconfirmed (#242), one maintainer-confirmed (#903, "we do not treat the mesh as ground-truth") —
show the consequence: an open or near-self-touching input can silently misclassify inside/outside.
Our own conversion (spec §4: "mesh → implicit: signed distance field from a closed mesh") already
names the precondition in the operation's name; this note's finding is that naming it is not the
same as checking it, and OpenVDB is the demonstration.

### Build on

**No, library scope for both — same answer as `libigl-openmesh.md`, for a different reason.**
Neither is a multi-representation kernel; each is a single-representation library (`README.md`
Category C). OpenVDB could plausibly sit behind the kernel's `implicit` module (spec §7) given its
Apache-2.0 licence and mature sparse tree, **but** it is C++-only with no C ABI (§The function tree
and C API) — if DynLex's FFI needs a C boundary (not settled here; a DynLex-extension question, not
a library-choice one), OpenVDB could not be called without a C++ shim, while libfive's genuine
`extern "C"` surface could. Not answered here.

### Borrow from

1. **Narrow-band level set with a background-value sign convention** (§Level sets) — cheap
   inside/outside classification without storing distance everywhere; matches spec §4's "tree of
   signed-distance primitives… sampled to a mesh." Source: [`Types.h#L528`](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/openvdb/openvdb/Types.h#L528).
2. **A QEF/Hermite-data vertex solve, when a sharper mesh is worth the cost** (§Meshing, libfive)
   — worth taking over OpenVDB's edge-average approach because BIM offsets/fillets (spec M8) may
   need a corner an averaged vertex loses; the trade (sharpness vs. maintainer-confirmed
   self-intersections, #284) must be taken with it. Source: [`dc_tree.inl#L740-L809`](https://github.com/libfive/libfive/blob/c9e97343e0af998cd1696e85583eccba95532b96/libfive/src/render/brep/dc/dc_tree.inl#L740-L809).
3. **The Manifold Dual Contouring collapse criterion** (sign-agreement at coarse edge/face/cube
   midpoints against a corner) as the octree merge-safety check for spec §9's M5. Source:
   [`dc_tree3.cpp#L20-L27`](https://github.com/libfive/libfive/blob/c9e97343e0af998cd1696e85583eccba95532b96/libfive/src/render/brep/dc/dc_tree3.cpp#L20-L27);
   DOI [10.1109/TVCG.2007.1012](https://doi.org/10.1109/TVCG.2007.1012).
4. **`min_feature` (subdivision stop) and `max_err` (merge tolerance) as two independent knobs**
   for spec §4's "cell size, feature angle" — but **`min_feature` must scale to feature size, not
   bounding-region size**, per #562's maintainer-confirmed defect. Source: [`settings.hpp#L44-L53`](https://github.com/libfive/libfive/blob/c9e97343e0af998cd1696e85583eccba95532b96/libfive/include/libfive/render/brep/settings.hpp#L44-L53).
5. **A real C ABI as the embeddability target**, modelled on `libfive.h`, if DynLex's FFI needs one
   for the `implicit` module — cheaper to bind than OpenVDB's template-heavy C++ API. Source:
   [`libfive.h#L15`](https://github.com/libfive/libfive/blob/c9e97343e0af998cd1696e85583eccba95532b96/libfive/include/libfive.h#L15).

### Avoid

- **CSG that assumes, rather than checks, a shared transform between two operands** (§CSG on level
  sets). Spec §12's result-value error model should make the implicit CSG's precondition — same
  frame, comparable narrow-band width — an explicit, checked contract, not documentation. New:
  `problems.md` P-22.
- **A closedness requirement enforced only by a doc comment** (§Mesh → volume). Our mesh →
  implicit conversion (spec §4) must carry the validation result in the operation's result value
  (spec §12), the same posture P-01/P-09 already take toward mesh booleans on non-manifold input.
  New: `problems.md` P-23.
- **Treating "dual contouring" as inherently feature-preserving.** OpenVDB's variant is not
  (averaged edge crossings, §Meshing); libfive's QEF variant is closer but not
  intersection-free either (#284). Spec §9's M5 must state which trade-off its own dual contouring
  makes, rather than inheriting the term's reputation without re-deriving which property survived
  the implementation. New: `problems.md` P-21.
- **A subdivision-stop parameter scaled to the wrong quantity** — libfive's `min_feature` measured
  against the bounding region's smallest axis, not local feature size (#562).

## Sources

- [OpenVDB, tag `v13.0.0`](https://github.com/AcademySoftwareFoundation/openvdb/tree/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38)
- [libfive, `master` at the pinned commit](https://github.com/libfive/libfive/tree/c9e97343e0af998cd1696e85583eccba95532b96)
- Ju, Losasso, Schaefer, Warren, "Dual Contouring of Hermite Data," SIGGRAPH 2002 —
  [ACM DL](https://dl.acm.org/doi/10.1145/566654.566586)
- Schaefer, Ju, Warren, "Manifold Dual Contouring," IEEE TVCG 13(3), 2007. DOI:
  [10.1109/TVCG.2007.1012](https://doi.org/10.1109/TVCG.2007.1012)
- Museth, "VDB: High-Resolution Sparse Volumes with Dynamic Topology," ACM TOG 32(3), 2013. DOI:
  [10.1145/2487228.2487235](https://doi.org/10.1145/2487228.2487235)
- Lorensen, Cline, "Marching Cubes," SIGGRAPH 1987 — cited for contrast only, not read
- Quilez, "distfunctions" — <https://iquilezles.org/articles/distfunctions/> — cited for the
  smooth-min/-max combinators spec §4 names, not verified against either library's source
- [OpenVDB #242](https://github.com/AcademySoftwareFoundation/openvdb/issues/242), [#903](https://github.com/AcademySoftwareFoundation/openvdb/issues/903), [#1992](https://github.com/AcademySoftwareFoundation/openvdb/issues/1992), [#1354](https://github.com/AcademySoftwareFoundation/openvdb/issues/1354)
- [libfive #284](https://github.com/libfive/libfive/issues/284), [#562](https://github.com/libfive/libfive/issues/562)
- [`libigl-openmesh.md`](libigl-openmesh.md) — closest sibling note in shape (design-reference, no
  torture-set measurement); its two-library table and "library, not kernel" verdict pattern
  followed here
- [`manifold.md`](manifold.md), [`cgal.md`](cgal.md) — booleans, cited in §Connecting to existing
  evidence rather than repeated
- [`blender.md`](blender.md), [`pointclouds.md`](pointclouds.md) — float32 precision at distance
  from origin, cited in §Connecting to existing evidence and the `problems.md` P-05 addition
- [`problems.md`](problems.md) — P-05 (addition), P-21, P-22, P-23 (new)
