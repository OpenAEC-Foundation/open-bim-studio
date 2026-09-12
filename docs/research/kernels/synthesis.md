# Synthesis — what the kernel research decided, and on what evidence

**Decision question: which kernels do we build on, borrow from, or build ourselves — and do
[ADR-0004](../../architecture/decisions/0004-build-our-own-kernel-in-dynlex.md),
[ADR-0005](../../architecture/decisions/0005-multi-representation-kernel.md) and
[ADR-0006](../../architecture/decisions/0006-f64-local-coordinates-in-tile-frames.md) survive
contact with the evidence?**

**Status:** written 2026-09-12, at the end of the kernel research programme. This is the output
[`README.md`](README.md) §Output of this directory names. It assembles the fourteen candidate
notes in this directory, [`../renderers/gpu-paths.md`](../renderers/gpu-paths.md),
[`problems.md`](problems.md) and the five cross-candidate `FINDINGS.md` files in
[`../../../spikes/`](../../../spikes/). **It adds no measurement and no verdict of its own**: every
number and every per-candidate verdict below is copied from a named section of a named file, and
the only new judgements here are the three ADR decisions in §6 and the spec amendments in §4,
both of which say which evidence rows carried them.

**Serves:** ADR-0004, ADR-0005, ADR-0006; the kernel spec
[`2026-09-09-geometry-kernel-design.md`](../../superpowers/specs/2026-09-09-geometry-kernel-design.md)
§15.

---

## How to read the evidence labels

Every cell in every table below carries one of four labels, used exactly as
[`README.md`](README.md) §Traceability defines them:

| Label | Short form | Means |
|---|---|---|
| **measured** | *(m)* | a number this repository produced, in a `spikes/*/FINDINGS.md` or a `spikes/*/results/` file |
| **source** | *(s)* | read directly from the candidate's source code at a pinned commit |
| **claimed** | *(c)* | stated by the project's documentation, its maintainers, or a third party, with a URL |
| **inferred** | *(i)* | a conclusion drawn in the note from source, structure or arithmetic, with the reasoning shown |
| **unknown** | *(?)* | not established — recorded, never skipped |

Where a note labels a finding with two of these (for example "measured + source"), the short form
carries both: *(m,s)*.

---

## 1. The completed matrix

One row per candidate, every cell labelled. The criteria and their weights are
[`README.md`](README.md) §Weighting matrix, unchanged. The matrix is split into three tables of the
same twenty-one rows purely so the cells stay readable; it is one matrix.

Rows are candidates, not notes: `truck-fornjot.md`, `libigl-openmesh.md`, `pointclouds.md` and
`implicit.md` each cover more than one candidate, and `opencadstudio.md`'s subject is **cadkernel**,
the MPL-2.0 geometry crate, not the GPL application above it.

### 1a — Licence, representations, boolean robustness, tolerance and precision

| Candidate (note) | License | Representations held natively | Boolean robustness (R-16) | Tolerance and precision model (R-17) |
|---|---|---|---|---|
| **OCCT** ([`occt.md`](occt.md)) | LGPL-2.1 + OCCT exception; links, does not permit source reuse *(c)* | **One** — B-rep; `Poly_Triangulation` is a cached tessellation, not modellable *(i)* | 30/30 case×setting valid *(m)*; 9/10 correct *(i)* — the OCCT driver reports no correct count of its own, and the FINDINGS prints that column as "9 *(inferred)*", derived from the driver's Δ annotations; `sliver` ∩ returns 0 where 1e-07 m³ expected. **Neither pass nor fail** under R-16's identity reading *(m)* | f64 throughout; per-entity tolerance, monotone via `UpdateTolerance` but settable down; three `constexpr` floors (1e-7 / 1e-12 / 1e-9). **PASS** R-17, 2.65e-10 m default, 3.61e-10 m at fuzzy=1e-5 *(m,s)* |
| **FreeCAD** ([`freecad-topological-naming.md`](freecad-topological-naming.md)) | LGPL-2.1-or-later *(c)* | OCCT's, unchanged — an application, never a build-on candidate *(s)* | not applicable — OCCT's *(?)* | OCCT's, plus a name-reconstruction layer above it *(s)* |
| **Truck** ([`truck-fornjot.md`](truck-fornjot.md)) | Apache-2.0 *(m)* | **One** — B-rep, NURBS; mesh is a converted-to crate *(s)* | shipped, **transversal only** by its own doc; panics on some coincident/tangent input. Not run *(s)* | f64; **one global `TOLERANCE = 1e-6`**, no per-entity value *(s)* |
| **Fornjot** ([`truck-fornjot.md`](truck-fornjot.md)) | 0BSD *(m)* | **One** — B-rep, lines and circles only, no NURBS *(s)* | **none shipped**; owner-confirmed representation gap blocks it *(s,c)* | f64; one process-wide `ValidationConfig.tolerance`, default 0.001 *(s)* |
| **cadkernel** ([`opencadstudio.md`](opencadstudio.md)) | **MPL-2.0** — file-level copyleft; links from a differently licensed product *(m)* | **One** — B-rep, five analytic surfaces + NURBS; mesh export-only; no point cloud; no implicit *(s)* | **FAIL** at all three settings — 7/10 valid+correct (6/10 at tol=1e-6). **Every failure a refusal, none a wrong answer**; identity residual exactly **0** on every case that ran, in the FINDINGS' own words "the only candidate whose residual is 0 at every setting; CGAL's f32-rounded row is also 0 on the cases it completed" — and, like Manifold's and CGAL's figures, cadkernel's excludes the three cases it refused *(m)* | **f64 throughout, zero f32**; tolerance derived `extent·1e-8 + ε·scale·64`, measured ×1.474 larger at 500 km; **no per-entity tolerance; no exact predicates** *(m,s)*. **PASS** R-17 at 0 m, on two cases where 0 m is arithmetic rather than evidence *(m)* |
| **Parasolid / ACIS** ([`commercial-brep-reference.md`](commercial-brep-reference.md)) | commercial; documentation-only reference *(c)* | B-rep *(c)* | not a candidate; not run *(?)* | Parasolid 1e-8-unit session precision, extent ratio ≈1e11; ACIS `SPAresabs` 1e-6, ratio ≈1e10; both tolerant-B-rep *(c)* |
| **Blender** ([`blender.md`](blender.md)) | **GPL** (3.0 project, 2.0-or-later on BMesh and the boolean) *(c)* | Two mesh forms (`Mesh` SoA, `BMesh` radial-loop) plus datablock types; no B-rep, no point cloud, no implicit *(i)* | **FAIL** on all three solvers — Exact 8/10 valid and loses an operand on `touching_vertex`; Fast 5/10 valid, wrong by 33–100%; embedded Manifold 10/10 but **the one nominal pass in the whole file, resting on a refusal the criterion cannot see** *(m)* | **float32 storage**, exact rationals inside the Exact solver, float32 out. **FAIL** R-17 on every solver: 0.0348 m (Exact), 0.0435 m (Manifold), 0.5 m (Fast); the float32 storage round trip alone costs **0.01375 m** over the wall's operands before any algorithm *(m)* |
| **Manifold** ([`manifold.md`](manifold.md)) | **Apache-2.0** — code may be borrowed, not only ideas *(s)* | **One** — oriented 2-manifold triangle mesh with properties *(s)* | **FAIL** at all four settings — `near_degenerate_triangle` refused `NotManifold`; 9/10 correct otherwise, worst residual 3.55e-14. **Neither exact predicates nor exact constructions**: doubles plus a tie-break that fires only on bit-identical coordinates *(m,s)* | Two numbers per solid, both derived from `Box::Scale()` = **largest absolute coordinate**, so tolerance tracks distance from the origin even on f64 (1e-11 → 5e-07 at 500 km). **PASS** R-17 on `Mesh64` at **3.29e-11 m**, the tightest measured; **FAIL** on `Mesh` (f32) at 0.0186 m *(m,s)* |
| **CGAL** ([`cgal.md`](cgal.md)) | **Split per package** — kernel and filtering LGPL, `corefinement.h` **GPL-3.0-or-later** *(s)* | Several, but not as one kernel: `Polyhedron_3`/`Surface_mesh`, `Nef_polyhedron_3`, `Point_set_3`, `Mesh_3` in separate packages *(s,i)* | **FAIL** on both settings — `shared_edge` ∪ and both `near_degenerate_triangle` booleans return `False`; 8/10 otherwise, worst residual **7.11e-15**, the tightest in the file *(m,s)* | **No tolerance at all.** Epick = double storage + exact filtered predicates. Measured: the exact predicate is right 4096/4096 where plain double is wrong **2164/4096**. **PASS** R-17 at 1.29e-10 m on f64; **FAIL** at 0.0348 m on f32-rounded input *with the exact predicates still on* *(m,s)* |
| **libigl** ([`libigl-openmesh.md`](libigl-openmesh.md)) | MPL2 own files; **GPL via the `CGAL::Polyhedron_3` dependency** in the boolean *(m)* | **None of its own** — free functions over caller-owned `Eigen` matrices *(i)* | not run — design-reference note. Algorithm class read from source: exact arrangement, five stages *(s)* | no tolerance: exact-rational identity throughout *(s)* |
| **OpenMesh** ([`libigl-openmesh.md`](libigl-openmesh.md)) | BSD-3-Clause *(m)* | **One** — half-edge polygon mesh *(i)* | ships no boolean *(s)* | no fixed tolerance; default `Point` is `Vec3f`, **float32** *(m)* |
| **PCL** ([`pointclouds.md`](pointclouds.md)) | BSD-3 *(c)* | point cloud only *(c)* | not applicable *(?)* | **float32 xyz, no tolerance model**, stated as a design limit by two MEMBERs *(c,s)*. **PCL itself was never run** — the 0.015625 m cost of f32 world storage at 500 km was measured on Open3D's f32 tensor, not on PCL, and is carried in that row *(?)* |
| **Open3D** ([`pointclouds.md`](pointclouds.md)) | MIT *(c)* | point cloud, triangle mesh, voxel grid, octree, RGBD *(c)* | not applicable *(?)* | f64 legacy, f32-or-f64 tensor, caller's choice; no tolerance model *(c)*. The only point-cloud precision measurement in the programme is this candidate's: **0.015625 m** on the f32 tensor at 500 km against 2.91e-11 m on the f64 tensor *(m)* |
| **PDAL** ([`pointclouds.md`](pointclouds.md)) | BSD *(c)* | point cloud only; a `Mesh` exists as a stage output *(c)* | not applicable *(?)* | **f64 XYZ by declared dimension type** — the right precision model of the four *(c)* |
| **Potree** ([`pointclouds.md`](pointclouds.md)) | BSD-2, both repositories *(c)* | point cloud only *(c)* | not applicable *(?)* | **int32 × scale + f64 offset** — a fixed quantum, ±2 147 km at 1 mm, independent of position in a national grid *(s)* |
| **OpenVDB** ([`implicit.md`](implicit.md)) | Apache-2.0 (one BSD-3 header) *(m)* | sparse voxel grids: level sets, fog volumes, point-data grids; no persistent mesh or B-rep *(m,i)* | not torture-set-testable — tree CSG cannot fail; the cost moves to meshing *(s)* | narrow band = `voxelSize × halfWidth` (default 3); **float32 value type and mesh output by default** *(s)* |
| **libfive** ([`implicit.md`](implicit.md)) | MPL-2.0 core + C API; GPL only in bindings and GUI *(m)* | function tree of implicit primitives and combinators *(m)* | same — tree CSG cannot fail; the mesher can (maintainer-confirmed self-intersections, #284) *(s,c)* | `min_feature`/`max_err` explicit knobs; float32 field eval, float64 QEF solve, **float32 C-API output** *(s)* |
| **IfcOpenShell** ([`ifcopenshell.md`](ifcopenshell.md)) | LGPL-3.0-or-later *(m)* | OCCT B-rep, CGAL polyhedra (two flavours), triangulated output; no point cloud, no implicit *(m,c)* | OCCT's, plus an IFC retry ladder; failure is frequently **silent** — 49 `Failed to convert` on one model *(m,c)* | One global `precision`, default 1e-05, **clamped at 1e-7 m** — the clamp message logged 3,654 times, once per element *(m,c)* |
| **web-ifc** ([`web-ifc.md`](web-ifc.md)) | MPL-2.0 *(m)* | triangle meshes only *(i)* | its own, tolerance-driven, no exact arithmetic; named as the weak point by a COLLABORATOR *(c,i)* | computation in `double`, **output in float32**; 12 loader settings plus `EPS_*` constants duplicated across three headers with two different values for the same names *(m)* |
| **xBIM** ([`xbim.md`](xbim.md)) | CDDL, unversioned, on both repositories *(c)* | OCCT B-rep plus a triangulated mesh; no point cloud, no implicit *(c)* | OCCT's, inherited through `Factories/BooleanFactory` *(i)* | doubles throughout; tolerance from `ModelFactor.Precision`; a MEMBER's *hedged* hypothesis that the default differs between model backends *(c)* |
| **DynLex graphics runtime** ([`../renderers/gpu-paths.md`](../renderers/gpu-paths.md)) | the project's own *(s)* | none — it is a submitter, not a kernel *(s)* | not applicable *(?)* | **no f64 anywhere** in the runtime; one interleaved 36-byte f32 vertex *(s)* |

### 1b — Incremental evaluation, threading, GPU path, IFC coverage

| Candidate | Incremental evaluation (R-01) | Threading model | GPU path | IFC coverage |
|---|---|---|---|---|
| **OCCT** | **Absent** — no evaluation graph; `BRepTools_History` covers one operation *(i)* | opt-in per operation, default off; measured **9.5×** on curved tessellation and **+8% slower** on 10k planar boxes *(m,s)* | only after `BRepMesh`; nothing returns from the GPU. Camera-relative rendering **is** implemented, f64 subtraction on the CPU, per Z-layer *(i,s)* | none natively *(i)* |
| **FreeCAD** | an application-level recompute over OCCT, with a name-reconstruction layer; measured to survive a dimension change and to break on split/merge/insert *(m,c)* | not evaluated *(?)* | not evaluated *(?)* | none *(?)* |
| **Truck** | **absent** — no dependency graph in any crate read *(i)* | `Arc<Mutex<_>>` throughout — safe, not parallel by design *(i)* | `truck-platform`/`truck-rendimpl`, wgpu; out of scope *(?)* | none *(s)* |
| **Fornjot** | **absent** — `Store` is append-only, no invalidation *(i)* | `Arc<RwLock<_>>`; same caveat *(i)* | wgpu; out of scope *(?)* | none *(s)* |
| **cadkernel** | **not in the kernel**; the application re-evaluates a whole body from its stored history record *(s)* | **single-threaded by design** — one match for `rayon`/`thread`/`par_iter`/`Mutex`/`Arc<` under `src/`, and it is a comment *(m)* | wgpu through `iced`; **f64 → (high f32, low f32) split on the CPU, differenced against the camera in WGSL, per-instance**, so the scheme survives instancing. Picking is CPU *(s)* | none in either crate *(s)* |
| **Parasolid / ACIS** | *(?)* | *(?)* | *(?)* | *(?)* |
| **Blender** | **present — the only candidate that has one** — and too coarse: per datablock component. Measured one-object move **16.3 ms at 10k objects, 332.1 ms at 100k**, ≈63–65 kB per object *(m,s)* | parallel by default and pervasive, TBB behind `threading::parallel_for`; measured non-determinism on the Fast solver *(m,s)* | full backend abstraction behind `VertBuf`/`IndexBuf`/`Batch`, 29 extractors; positions upload as f32. **No camera-relative rendering**, and the tracker says so *(i,c)* | none — IFC arrives only through an add-on *(i)* |
| **Manifold** | **none** — immutable, functional, deferred CSG tree evaluated once and discarded *(i)* | TBB throughout, `autoPolicy(size)` with `kSeqThreshold = 1e4` so small problems stay serial *(s,c)* | **none, by decision** — CUDA and OpenMP backends removed in 2023 *(s,c)* | not applicable *(s)* |
| **CGAL** | **none at kernel level**; worse, corefinement **modifies both operands in place** *(m,i)* | **unmeasured** — the corefinement API takes no concurrency tag *(i)* | **none** *(s)* | not applicable *(s)* |
| **libigl** | **none** — every call rebuilds the arrangement of the full combined input *(i)* | `igl::parallel_for` used once, for the final coordinate copy *(s)* | not applicable *(?)* | not applicable *(?)* |
| **OpenMesh** | local edits are local; **no dependency graph above them** *(i)* | not verified; no locking or atomics in the files read *(i, low confidence)* | not applicable *(?)* | not applicable *(?)* |
| **PCL** | **not applicable** — no parametric model *(i)* | octree build serial; parallelism opt-in via separate `*OMP` classes *(c)* | VTK visualisation module *(c)* | not applicable *(?)* |
| **Open3D** | not applicable; and the octree has **no incremental insert** — rebuild is the only API *(i)* | **octree build serial**, measured **324.4 s on one core of thirty-two** at 10⁸ points, in a library that parallelises normal estimation in the same directory *(m,s)* | tensor cloud can live on a CUDA device *(c)* | not applicable *(?)* |
| **PDAL** | not applicable *(i)* | streaming is pipelined; per-stage *(c)* | **none** — headless by design *(c)* | not applicable *(?)* |
| **Potree** | not applicable *(i)* | converter parallel (`std::execution::par_unseq`); viewer single-threaded JS *(c)* | **the whole point** — WebGL, screen-space LOD, per-frame point budget *(c)* | not applicable *(?)* |
| **OpenVDB** | **no** — grids rebuilt, not patched *(i)* | TBB throughout; not benchmarked *(s)* | NanoVDB — separate, static-topology, ray-tracing-oriented *(s)* | not applicable *(?)* |
| **libfive** | **no** — `Mesh::render` rebuilds the octree from the whole tree every call *(i)* | `BRepSettings::workers`, default 8 *(s)* | **none found** *(m, absence)* | not applicable *(?)* |
| **IfcOpenShell** | single-element evaluation **exists** and is cheap at the median (**1.63 / 2.06 ms**); **dependency tracking does not exist**, and there is no automatic invalidation — one cache has no erase, the other only a manual `remove(GlobalId)`. p95 **16.96 ms**, max **553.97 ms** *(m,c)* | `kernel_pool` of one `Converter` per thread, `num_threads` explicit; measured **3.1×** and **2.4×** on 32 processors *(m)* | none in-library; triangulated output the caller uploads *(i)* | parsing IFC2x3 TC1 … IFC4x3 Add2; **geometry IFC2x3 TC1 and IFC4 Add2 only** *(c)* |
| **web-ifc** | **none that works** — geometry is cached per geometry express id and `ResetCache` **is not exported by the shipped WASM module and throws**; the only working route is to re-open the model, **266.8 ms** on a 3,822-element file *(m)* | **single-threaded**; no worker use in the sources read *(i)* | built for it: interleaved `[x,y,z,nx,ny,nz]` **float32** read straight out of `HEAPF32` *(m)* | both benchmark schemas read correctly; breadth not otherwise measured *(m, partial)* |
| **xBIM** | **none**, and it is enforced at the storage contract — `IGeometryStore.BeginInit()` clears *(c,i)* | boolean union multithreaded; the whole-model context is the parallel unit *(c, partial)* | none in-library; output is `wexBIM`, "only documented by the code" *(c)* | IFC2x3 TC1, IFC4 Add2, IFC4x3 Add2 *(c,i)* |
| **DynLex graphics runtime** | not applicable *(s)* | **none** — `src/runtime` has no threading *(s)* | **no index buffer, no instancing, no storage buffer, no compute pipeline, no readback, no f64**; a 32 MiB per-frame transient arena holds **25 890 twelve-triangle boxes**, and 10⁵ boxes **cannot be drawn at all** *(s,i)* | not applicable *(s)* |

### 1c — Performance, embeddability, 2D derivation, maturity, AI familiarity

| Candidate | Performance (measured on our benchmark set unless stated) | Embeddability from DynLex | 2D derivation | Maturity | AI familiarity |
|---|---|---|---|---|---|
| **OCCT** | 10k planar boxes: **4.2–4.7 s** to tessellate; wall+12 openings **54.03–58.52 ms** ∪ across the three settings; every other torture pair 0.47–4.62 ms *(m)* | C++ handle-and-template API, **no C ABI**; a shim would be larger than for a Rust kernel *(i)* | substantial — `HLRBRep`/`HLRAlgo`, `BRepAlgoAPI_Section`; drawing-grade quality unknown *(c)* | 26 years, commercial maintainer, ~2 releases/year; **14 of 20 surveyed boolean/tolerance issues open** *(m, survey)* | high *(i)* |
| **FreeCAD** | element-map recompute measured on a dimension change *(m)* | not applicable *(?)* | application-level *(?)* | 1.0 shipped with the naming problem "not completely solved"; three of five cited issues filed after 1.0 *(c)* | high *(i)* |
| **Truck** | not measured *(?)* | pure Rust; **zero `extern "C" fn`, zero `#[no_mangle]`** *(m)* | `truck-drafting` exists; not evaluated *(i)* | single-maintainer (2 591:9), active, 36 open issues *(m)* | moderate *(i)* |
| **Fornjot** | not applicable — no boolean *(?)* | same: **zero C-callable surface** *(m)* | none found *(i)* | single-maintainer, **archived; the project shut down** *(m)* | moderate *(i)* |
| **cadkernel** | **0.740 – 50.748 ms** per boolean; `overlap_half` ∪ **32.256 ms** against OCCT 4.62, Blender-Exact 3.21, CGAL 0.380, Manifold 0.293 — **5–110×** the others, with no binding layer. Face pairing is O(n·m) with an AABB reject and no spatial index *(m,s)* | pure Rust rlib; **zero `extern "C"`, zero `#[no_mangle]`, zero `#[repr(C)]`, no `cdylib`** — the shim is ours to write and maintain *(m)* | `silhouette` and `tessellate_wireframe`; hidden line and section are the application's *(s)* | **34 days old** at the pinned commit, 336 commits, two contributors, **no tags, no crates.io release** *(m)* | **effectively zero public corpus** *(i)* |
| **Parasolid / ACIS** | *(?)* | *(?)* | *(?)* | decades of commercial use *(c)* | *(?)* |
| **Blender** | torture booleans (FINDINGS §Summary, per solver): Exact **0.47–18.26 ms** (wall ∪ 17.80), Fast 0.25–1.18, embedded Manifold 0.30–1.91; **35.3 s to build and 11.5 s to evaluate 100k objects, 6.2 GB** *(m)* | **effectively none** — internal static libraries, no stable ABI, no C API; `bpy` embeds the whole application *(i)* | Line Art produces stylised outlines, not dimensioned drawings *(c)* | very high; 12 of 20 surveyed boolean reports closed, the boolean's author answers *(m, survey)* | very high *(i)* |
| **Manifold** | per setting, over the accepted cases (FINDINGS §Summary): f64 default tol **0.003–0.997 ms**, f64 tol=1e-9 **0.002–1.000**, f64 tol=1e-6 **0.002–1.104**, f32 default tol **0.002–0.990**. Wall+12 openings ∪ **0.997 / 1.000 / 1.104 / 0.990 ms** on those four settings — the fastest measured *(m)* | **strong** — no required dependencies, a plain **C ABI binding**, WASM, static by default *(s,i)* | `Slice`/`Project` to polygons, `CrossSection` for 2D booleans; **no hidden line, no hatching** *(s)* | 26 releases since 2022, nine in the last year; **bus factor 2** *(s,i)* | small, heavily commented corpus *(i)* |
| **CGAL** | **0.010–8.183 ms** Epick on f64 input (0.012–6.627 on f32-rounded); wall+12 openings **8.183 ms** ∪. **Epeck and Nef unmeasured** *(m)* | **weak** — template API, no C ABI; Epeck needs GMP/MPFR, PMP needs Boost; a 25 MB SWIG wheel *(i)* | `Polygon_mesh_slicer`, 2D arrangements, Boolean set ops; no hidden line *(s)* | nearly three decades, consortium plus commercial maintainer, active release train *(s,i)* | very large *(i)* |
| **libigl** | not measured *(?)* | header-only core, but the boolean needs CGAL + GMP + MPFR *(i)* | not applicable *(?)* | active; `v2.6.3` dated 2026-08-31 *(i)* | high *(i)* |
| **OpenMesh** | not measured *(?)* | plain C++ library, in-process *(i)* | not applicable *(?)* | 21 years; last tag 2022-01-18 *(c,i)* | high *(i)* |
| **PCL** | **not measured** — no install attempted *(?)* | C++ library, **no C ABI** *(c, negative result)* | not applicable *(?)* | 2009–, active; the `outofcore` module self-describes as under development *(c)* | very high *(i)* |
| **Open3D** | 10⁸ f64 points = **2.40 GB** data; depth-8 octree **102.910 bytes/point, 4.3× the data**, peak 13.13 GB, **324.4 s**; kd-tree 9.58 GB, 178.0 s; all 300 verified NN answers matched brute force *(m)* | C++ with a maintained wheel, **no C ABI** *(c, negative result)* | not applicable *(?)* | 2018–, Intel ISL origin, 0.19.0 dated 2025-01 *(c)* | high *(i)* |
| **PDAL** | **not measured** — the wheel is a source build needing the native library *(?)* | **no C ABI**; but its unit of work is a **JSON pipeline**, drivable across a process boundary with no shim *(c, negative result + i)* | not applicable *(?)* | 2010s–, Hobu Inc., 2.10.2 dated 2026-06 *(c)* | moderate *(i)* |
| **Potree** | **not measured** *(?)* | not a library — a CLI converter and a JS viewer; **its format is the embeddable thing** *(i)* | not applicable *(?)* | one principal author; converter 2026-06, **viewer's last release 2023-12** *(c)* | moderate *(i)* |
| **OpenVDB** | **not measured** — no wheel exists for this platform *(?)* | C++ template library, TBB dependency, **no C ABI** *(m, absence)* | not traced *(?)* | active ASWF project, `v13.0.0` *(c)* | high *(i)* |
| **libfive** | **not measured** *(?)* | header-only core plus a genuine `extern "C"` ABI — **more directly embeddable than OpenVDB** *(m)* | 2D DC/simplex variants exist; not traced *(i)* | single-maintainer-led; **no semver release tags exist at all** *(c,i)* | moderate *(i)* |
| **IfcOpenShell** | full geometry 1.038 s / 9.013 s at 32 threads; **0.666 s / 0.687 s** with the hybrid kernel; parse 0.136 s / 2.231 s *(m)* | C++ with a SWIG binding; an FFI boundary to a C++ library; LGPL shapes how *(i)* | `ifcopenshell.draw` and a CURVES dimensionality exist; not examined *(?)* | the reference open-source IFC implementation; bus factor concentrated on one maintainer for the geometry core *(c,i)* | *(?)* |
| **web-ifc** | `OpenModel` 16.5 / 328.7 ms; `LoadAllGeometry` 85.3 / **296.6 ms** — **≈30×** faster than the OCCT path on the larger model *(m)* | WASM, embeddable in-process — but the model must fit the WASM heap; a COLLABORATOR names "a hard limit of 4GB" *(m,c)* | `GetAllCrossSections2D/3D` exist; not examined *(?)* | active, multiple COLLABORATORs; the REAL write path fixed at least four times *(c)* | *(?)* |
| **xBIM** | **unknown and unpublished** — asked directly, a MEMBER answered "too many variables" *(c)* | **not embeddable on any reasonable path** — managed .NET plus C++/CLI; in-process means hosting the CLR *(i)* | not examined *(?)* | actively maintained, but the stable geometry package is 5.1.820 and 6.x has been prerelease off a feature branch for years *(c,i)* | *(?)* |
| **DynLex graphics runtime** | **nothing measured** — the compiler is not built in the working copy that note used *(?)*; the 25 890-box arena ceiling is arithmetic *(i)* | it is the given, not a choice *(s)* | none *(s)* | the project's own *(s)* | *(?)* |

---

## 2. The verdict per candidate, on all three axes

One line per axis, as [`README.md`](README.md) §Three verdicts, not one requires. Each links the
note's own `§Verdict`; none of these verdicts is changed here.

| Candidate | Build on | Borrow from | Avoid |
|---|---|---|---|
| **OCCT** ([§Verdict](occt.md#verdict)) | **No** — no incremental evaluation, one representation where ADR-0005 wants four, and a C++ handle API with no C ABI. Boolean quality is *not* the reason *(i)* | **Substantially, as design; never as code** (LGPL) — the tolerance model, the interference taxonomy, categorised validity, stated preconditions | Tolerance-as-resolution-mechanism; destructive-by-default operations; healing by widening tolerance; one tessellation cached per face |
| **FreeCAD** ([§Verdict](freecad-topological-naming.md#verdict-avoid-axis-only)) | not scored — an application, never a candidate | not scored — LGPL source, read for study | **Avoid axis only**: derived-topology references as the primary mechanism; conflating handle stability with recompute identity; silent automatic repair; an unbounded history walk |
| **Truck** ([§Verdict](truck-fornjot.md#verdict)) | **No** — no C-callable surface at all *(m)* | the `Compressed*` exchange types as the shape of an `io/` boundary | one global tolerance constant; a boolean that panics instead of refusing (**P-29**) |
| **Fornjot** ([§Verdict](truck-fornjot.md#verdict)) | **No** — same absence, and the project is archived *(m)* | handle-carries-identity topology; topological objects holding no geometric data of their own; an unenforced precondition named in the type's own doc comment; a numeric type that cannot represent NaN once constructed | a single process-wide `ValidationConfig.tolerance` with no per-entity value (**P-02**); append-only storage that never frees; deferred-panic error handling |
| **cadkernel** ([§Verdict](opencadstudio.md#verdict)) | **Conditional shortlist for the B-rep arm — not recommend.** The condition was set before the driver ran and the numbers selected the second branch: it refuses three of ten cases, is 5–110× slower, single-threaded, one representation, no exact predicates, 34 days old, and the C ABI is ours to write *(m,s)* | the note's §Borrow from — pinned, seven items — of which: the typed refusal with a named cause; **provenance** (`Clean`/`Dirty`/`Synthesized`), the best idea in the note; itemised import loss; the scale-derived tolerance formula; `validate()` returning every flaw; the local-frame contract | classification by tolerance comparison with no exact predicates; letting the persistence format gate the modeller (**P-30**); filling a format's exact-geometry entities with tessellated f32 (**P-31**) |
| **Parasolid / ACIS** ([§Verdict](commercial-brep-reference.md#verdict)) — **this row is composed here**: the note's §Verdict compares its numbers with ADR-0006 and carries no *build on* / *borrow from* / *avoid* headings of its own, so the three cells below are the synthesis reading that verdict onto the common axes *(i)* | **No** — documentation-only reference, not a candidate | the documented meaning of "engineering accuracy": session precision, the extent ratio, Parasolid's vertex-precision propagation rule | a single global frame with fixed precision, which is what forces their extent ceiling |
| **Blender** ([§Verdict](blender.md#verdict)) | **No** — GPL; float32 storage (measured failure at 500 km); no embedding path. Three independent disqualifications *(c,m,i)* | **Substantially, as design; never as code** (GPL) — the exact-arrangement boolean's provenance, the depsgraph's per-component tagging | float32 vertex storage; per-datablock evaluation cost (**P-07**); a boolean that returns the first operand on refusal |
| **Manifold** ([§Verdict](manifold.md#verdict)) | **No as a kernel; yes as a candidate boolean component** — Apache-2.0 makes the option real, and it is **not taken**: it refuses input buildings are full of, and the repair cost is unmeasured *(m,s)* | **Extensively, and as code where it helps** — `ExecutionContext` cancel/progress; the ε-valid contract stated explicitly; `autoPolicy` | tolerance derived from the largest absolute coordinate; silent simplification that deletes a feature and reports `NoError` (**P-02**, **P-24**) |
| **CGAL** ([§Verdict](cgal.md#verdict)) | **No** — not as the kernel (146 packages, no model, no handles), and not as the boolean (**`corefinement.h` is GPL**) *(s)*. **One build-on question is left open, not answered no:** the note's §Build on keeps "linking Epick as an LGPL library for its predicates … a live option against writing Shewchuk's predicates ourselves", and does not close it | **the exact-predicate design, in detail, because ADR-0006 rests on it** — the filtered-predicate scheme, measured 4096/4096 against plain double's 2164 wrong | exact constructions rounded at the operation boundary without saying so; a precondition the binding does not expose; non-deterministic emission order |
| **libigl** ([§Verdict](libigl-openmesh.md#verdict)) | **No** — library scope; and the boolean's CGAL dependency is GPL *(m)* | **the five-stage arrangement pipeline as a pipeline shape** — the reference implementation of spec §4's sentence | rebuilding the whole arrangement on every call |
| **OpenMesh** ([§Verdict](libigl-openmesh.md#verdict)) | **No** — single representation, no index, no boolean *(i)* | the half-edge layout as a design reference | **plain-index handles with garbage-collection renumbering** — the opposite of spec §6's generational handles |
| **PCL** ([§Verdict](pointclouds.md#verdict)) | **No** — float32 is the disqualifying fact, not a preference *(c,s)* | nothing taken | array-of-structs storage with a padded fourth component |
| **Open3D** ([§Verdict](pointclouds.md#verdict)) | **No** — the measurement is the reason: 4.3× index overhead, 324.4 s single-core, no LAS/LAZ/E57, a 2.1 GB write ceiling *(m,c)* | nothing taken | an index that stores a point's identity once per level; an index that owns a private copy of the coordinates; a single-threaded index build (**P-13**, **P-17**) |
| **PDAL** ([§Verdict](pointclouds.md#verdict)) | **No as the module; genuinely yes as an ingest dependency — and this is the one to revisit.** It has the right precision model, the right formats and a real streaming story, and its JSON pipeline crosses a process boundary with no shim *(c,i)* | the chunked per-dimension table with a power-of-two block size (16 384); `Streamable` declared in a type | nothing |
| **Potree** ([§Verdict](pointclouds.md#verdict)) | **Not applicable** — a converter and a viewer *(i)* | **the partition LOD octree**, the level-assignment rule, the 22-byte node record with a paging hierarchy, int32 × scale + f64 offset, screen-pixel-radius LOD with two caps | a fixed-capacity accumulation buffer on a hot path (**P-19**); a budget that caps drawing but not residency (**P-18**) |
| **OpenVDB** ([§Verdict](implicit.md#verdict)) | **No** — library scope; C++-only, no C ABI *(m)*. **A narrower question is left open, not answered no:** the note's §Build on says OpenVDB "could plausibly sit behind the kernel's `implicit` module (spec §7)" given Apache-2.0 and a mature sparse tree, and whether a C++ shim is needed is "**not answered here**" | narrow-band level sets with a background sign convention | **dual-contouring vertices placed by averaging edge crossings with no feature term** — this is OpenVDB's `tools::volumeToMesh`, whose vertex is "the plain average of the cell's linear edge zero-crossings" (**P-21**); CSG that assumes rather than checks a shared transform (**P-22**); a closedness requirement enforced only by a doc comment (**P-23**) |
| **libfive** ([§Verdict](implicit.md#verdict)) | **No** — library scope; but it has a genuine C ABI *(m)* | a QEF/Hermite vertex solve when a sharper mesh is worth the cost — the note's reason for taking it is precisely that it is **closer to feature-preserving than OpenVDB's edge-average approach** | treating "dual contouring" as inherently feature-preserving: libfive's QEF variant is closer but **not intersection-free either** (maintainer-confirmed self-intersections, #284), so M5 must state which trade its own dual contouring makes (**P-21**); a subdivision-stop parameter scaled to the bounding region rather than to local feature size (#562) |
| **IfcOpenShell** ([§Verdict](ifcopenshell.md#verdict)) | **Yes for parsing and representation mapping; qualified yes for geometry, and no as the evaluation layer** — there is no disqualifying assumption, only a missing one: no dependency tracking, and a p95/max tail of 16.96 / 553.97 ms *(m,c)* | the schema-degrading georeference API; the hybrid per-element kernel routing; the pinned items in §Borrow from | silent conversion failure; a cache written on the assumption that the model is static |
| **web-ifc** ([§Verdict](web-ifc.md#verdict)) | **No** — float32 output by design, and no working invalidation. Two independent disqualifying assumptions, each measured *(m)* | the tape parser's paged, typed token store | float32 at the API boundary; `EPS_*` constants duplicated across headers with different values (**P-24**); eviction that clears the first chunk found, not the least recently used |
| **xBIM** ([§Verdict](xbim.md#verdict)) | **No** — C++/CLI and therefore Windows-only, and whole-model regeneration enforced at the storage contract *(i,c)* | three pinned items in §Borrow from | a storage contract that makes incremental evaluation impossible by construction |
| **DynLex graphics runtime** ([§Verdict](../renderers/gpu-paths.md#verdict)) | **It is the given** — the note prices the bill: eleven gaps, ten of them `ui/` work, one a language extension *(s,i)* | bevy's GPU preprocessing as `ui/`'s target architecture; OCCT's and Filament's CPU-side camera-relative subtraction | the fixed per-frame transient arena as the only path to the GPU (**P-27**); planning GPU compute against a toolchain with no compute stage (**P-28**) |

---

## 3. What the kernel spec takes from each candidate

The *borrow from* harvest, grouped by the spec section it lands in. Every row is a design the
research read at a pinned commit; the note named in the row carries the file and line citation.
Nothing here is code taken from a GPL or LGPL source — where the licence permits code reuse
(Apache-2.0, MPL-2.0, BSD, MIT) the row says so.

### Into spec §4 — representations, conversions, CSG dispatch

| Take | From | Licence of the source | Note section |
|---|---|---|---|
| **The five-stage arrangement pipeline** — resolve self-intersections → patch → extract cells → propagate winding numbers → classify by a caller-supplied keep function. This is the concrete shape of spec §4's one sentence about the mesh boolean | libigl | MPL2 for the shape; the shipped pipeline's CGAL dependency is GPL, so this is **design only** | [`libigl-openmesh.md`](libigl-openmesh.md) §Borrow from |
| **An LOD octree that is a partition, not a pyramid** — an accepted point is *moved* out of the child into the parent, so N points occupy N slots regardless of depth and a coarse level is a real subset | Potree | BSD-2 — code may be taken | [`pointclouds.md`](pointclouds.md) §Borrow from |
| **The level-assignment rule** — root spacing = extent/128, halving per level; a candidate joins a node if it is ≥ spacing from every point already there; children sorted by distance to centre | Potree | BSD-2 | [`pointclouds.md`](pointclouds.md) §Borrow from |
| **A chunk size that someone ships**: 16 384 points per per-dimension block | PDAL | BSD | [`pointclouds.md`](pointclouds.md) §Borrow from |
| **Narrow-band level sets with a background-value sign convention** — cheap inside/outside classification without storing distance everywhere | OpenVDB | Apache-2.0 | [`implicit.md`](implicit.md) §Borrow from |
| **A QEF / Hermite-data vertex solve** for dual contouring where a sharp corner matters (BIM offsets and fillets, M8) — taken **over OpenVDB's edge-average placement**, which is the design P-21 names, and taken together with its own price: libfive's variant is not self-intersection-free either (#284) | libfive | MPL-2.0 | [`implicit.md`](implicit.md) §Borrow from 2 |
| **Tessellation as a conversion producing a value**, several results per object, rather than a mutation of the source | OCCT (as the counter-example) | LGPL — design only | [`occt.md`](occt.md) §Avoid, **P-11** |
| **Refuse the operation that cannot be represented, and only that one**, with the reason recorded per operation | CGAL | GPL for the boolean — design only | [`cgal.md`](cgal.md) §Corrections, **P-09** |
| **The ε-valid contract stated explicitly** — what the boolean guarantees and what it does not | Manifold | Apache-2.0 | [`manifold.md`](manifold.md) §The contract |

### Into spec §5 — numerics, precision, tolerance, frames

| Take | From | Licence | Note section |
|---|---|---|---|
| **Per-entity tolerance stored on the entity and readable**, plus a whole-shape `MaxTolerance` query, plus an explicit per-operation tolerance parameter at the call site | OCCT | LGPL — design only | [`occt.md`](occt.md) §Borrow from |
| **Shewchuk-style filtered exact predicates** — floating filter first, exact expansion only when it cannot decide. Measured worth: the exact predicate was right 4096/4096 where plain double was wrong **2164/4096** | CGAL | LGPL for the kernel and filtering — design; the measurement is ours | [`cgal.md`](cgal.md) §The predicate is worth having |
| **`int32 × scale + f64 offset` as the *storage* encoding for scan data** — a fixed quantum, uniform over a file, independent of position in a national grid. f64 in the local frame remains the *computation* type | Potree, LAS via PDAL | BSD-2 / BSD | [`pointclouds.md`](pointclouds.md) §Borrow from |
| **The local frame as a stated contract**, translation-only, anchored at the midpoint of the bounding box — and the warning that goes with it: cadkernel documents this contract and the spike found `Frame` constructed at no call site in `src/brep/`, so **a contract nothing enforces is a contract that decays** | cadkernel | MPL-2.0 | [`opencadstudio.md`](opencadstudio.md) §Borrow from 6, §Precision |
| **A scale- and position-derived operation tolerance** — `extent·1e-8 + ε·coordinate_scale·64` — as a concrete alternative to a fixed 1e-6 m default, which is too loose for a 10 mm detail and too tight for a 200 m span | cadkernel | MPL-2.0 | [`opencadstudio.md`](opencadstudio.md) §Borrow from 4 |
| **The f64 camera-relative subtraction happens on the CPU at *tile* granularity**, folded into the instance transform, and only that transform is truncated to f32 — the arrangement OCCT and Filament both ship, and cadkernel independently confirms on a modern explicit API with instancing | OCCT, Filament, cadkernel | design | [`../renderers/gpu-paths.md`](../renderers/gpu-paths.md) §The correction this note makes to spec §5; [`opencadstudio.md`](opencadstudio.md) §3 |
| **The warning that a tolerance derived from a global bounding box tracks the global position** — Manifold's 1e-11 becomes 5e-07 at 500 km on the f64 path, and cadkernel's derived tolerance grows ×1.474. A caller-side local frame fixes the coordinates and leaves the tolerance following the world | Manifold, cadkernel | — | [`manifold.md`](manifold.md) §Precision; [`../../../spikes/precision-set/FINDINGS.md`](../../../spikes/precision-set/FINDINGS.md) |
| **The vertex-precision propagation rule** — a vertex's precision is at least the largest precision of any edge ending at it — as independent commercial confirmation that monotone tolerance growth is an invariant, not an OCCT artefact | Parasolid | documentation | [`commercial-brep-reference.md`](commercial-brep-reference.md) §Update to `problems.md` |

### Into spec §6 — performance strategy

| Take | From | Licence | Note section |
|---|---|---|---|
| **Generational typed handles in an arena** — spec §6's mechanism, independently arrived at by a shipping B-rep kernel | cadkernel | MPL-2.0 | [`opencadstudio.md`](opencadstudio.md) §1, Topology |
| **Threading as an opt-in flag with a measured threshold**, not a blanket default: 9.5× on curved tessellation and **+8% slower** on 10k planar boxes, from the same flag | OCCT | LGPL — design only | [`occt.md`](occt.md) §Borrow from |
| **A size-based execution policy** — `autoPolicy(size)` with a sequential threshold of 1e4 — as the mechanism that implements the row above | Manifold | Apache-2.0 | [`manifold.md`](manifold.md) §Evaluation |
| **Screen-pixel-radius LOD selection with two caps** — a total drawn-point budget enforced during a priority traversal, and a per-frame node-load cap | Potree | BSD-2 | [`pointclouds.md`](pointclouds.md) §Borrow from |
| **GPU preprocessing as `ui/`'s target architecture** — a compute pass expands per-object records into per-view instance records, culls, and writes indirect parameters that one multi-draw consumes | bevy | design | [`../renderers/gpu-paths.md`](../renderers/gpu-paths.md) §Borrow from |
| **Patch derived state, never rebuild it** — an entity-delta undo with a self-inverting record, and a per-edit render arena, in place of a whole-document clone per edit | Open CAD Studio (the application) | GPL — design only, and the figures are the author's *(c)* | [`opencadstudio.md`](opencadstudio.md) §Verdict (c) |

### Into spec §7 — module layout, `io/`, `gpu/`, `brep/`

| Take | From | Licence | Note section |
|---|---|---|---|
| **An explicit exchange format kept apart from the live editable graph** — index-addressed, structure-of-arrays, converted in both directions; editable and on-disk as two distinct types | Truck | Apache-2.0 | [`truck-fornjot.md`](truck-fornjot.md) §Borrow from 1 |
| **The buffer layout the five mature engines agree on** — interleaved f32 vertex attributes, a `u32` index buffer, and a separate instance-rate buffer carrying a 3×`vec4` transposed affine plus an element id | bevy, Filament, three.js, OCCT, Blender | design | [`../renderers/gpu-paths.md`](../renderers/gpu-paths.md) §The answer for the kernel's `gpu` module |
| **Categorised validity, not a boolean** — 37 named statuses rather than `false` | OCCT | LGPL — design only | [`occt.md`](occt.md) §Borrow from |
| **`validate()` returning every flaw, not the first**, over a named enum, run after a lift so a malformed file is reported where it was read | cadkernel | MPL-2.0 | [`opencadstudio.md`](opencadstudio.md) §Borrow from 5 |
| **The half-edge layout as a design reference** — and the explicit rejection of its handle scheme: plain indices with garbage-collection renumbering are the opposite of spec §6's generational handles | OpenMesh | BSD-3 | [`libigl-openmesh.md`](libigl-openmesh.md) §Borrow from, §Avoid |
| **The shared-vertex rule at tessellation boundaries** — use the stored topology vertex at a tessellated curve's endpoints instead of re-evaluating the curve there | Open CAD Studio | GPL — design only | [`opencadstudio.md`](opencadstudio.md) §Borrow from 7 |

### Into spec §12 — error handling

| Take | From | Licence | Note section |
|---|---|---|---|
| **A typed refusal that names which class of input defeated the operation.** "Boolean failed" is unactionable; the caller cannot recover a cause the kernel discarded | cadkernel (`Snag::{NoClosedForm, Coincident, CutRefused}`) | MPL-2.0 | [`opencadstudio.md`](opencadstudio.md) §Borrow from 1 |
| **Cancellation and progress as a context object** — a permanent cancel flag, an operation that returns a *typed cancelled result* instead of throwing, polled at phase boundaries and inside parallel chunks. A 23.6k-line library ships this and OCCT does not | Manifold | Apache-2.0 — code may be taken | [`manifold.md`](manifold.md) §Measurements; **P-15** |
| **Itemised loss on import** — `Loss { surfaces, curves, broken }` as record indices, returned by every format bridge instead of a success flag | cadkernel | MPL-2.0 | [`opencadstudio.md`](opencadstudio.md) §Borrow from 3 |
| **Stated argument preconditions, checked at the boundary**, with the operation rejecting violating input rather than producing something | OCCT | LGPL — design only | [`occt.md`](occt.md) §Borrow from |
| **A stage that declares in a *type* whether it can work chunk-wise**, checked when the pipeline is built, rather than a global mode that silently degrades | PDAL | BSD | [`pointclouds.md`](pointclouds.md) §Borrow from |

---

## 4. Where the evidence contradicts the spec, and the amendment for each

This is the section the rest of the file exists for. Each row names a spec section, what it says
today, what the evidence says, and the amendment. "Applied" means the spec was edited in the same
commit as this file, with an `Amended 2026-09-12` line at the place changed.

| Spec section | What it claims | What the evidence says | Amendment | Applied |
|---|---|---|---|---|
| **§5**, GPU precision | positions "are expressed relative to the camera's tile in f64 on the CPU, then truncated to f32 for upload" | Read literally this is a **per-vertex repack whenever the camera's tile changes**. Neither shipping implementation does that ([`../renderers/gpu-paths.md`](../renderers/gpu-paths.md) §The correction this note makes to spec §5; §Camera-relative rendering) | Vertices are stored and uploaded in their own tile frame, f32, once, into static `DEVICE_LOCAL` buffers; the f64 subtraction is `own_tile_origin − camera_tile_origin`, once per visible tile per frame, folded into the instance transform; `ui/` must expose a per-instance affine, not a collapsed MVP push constant | **yes** |
| **§6** item 4, **§7** `gpu/`, **§9** M7 | "DynLex compiles to SPIR-V… written as DynLex compute kernels in `gpu/`" | The compiler's shader stage is a **two-member enum**; `--shader-stage` accepts only `vertex\|fragment`; the runtime has zero `vkCmdDispatch`, zero compute pipelines, zero storage buffers (**P-28**, source) | §6 item 4 states that until the extension exists this work runs on CPU threads and §10's targets are checked against that; §8 gains the extension as a row | **yes** |
| **§8**, threading row | threading is "Needed by **M7**" | The point-cloud octree build needs it at **M6**: Open3D's single-threaded build costs **324.4 s** on one core of thirty-two at 10⁸ points, against a §10 target of 10 s (**P-13**, **P-17**, measured). Spec §6 already lists "octree build" among the `parallel for` targets | The threading row's "Needed by" becomes **M6**, with M7 remaining the milestone that *measures* it | **yes** |
| **§8**, extension table | lists threading, aligned/mapped allocation, SIMD | R-19 found two missing language facilities — **no unsigned integers or logical right shift** (`shift right` lowers to `ashr`), and **scientific-notation float literals are rejected** — and established that the compiler's **default emitted-code level is `-O0`**: unflagged, DynLex is 9.09× / 6.78× / 21.14× slower than C++ *(m)* | Three rows added: the two facilities, and the requirement that the kernel's build passes an explicit `-O` flag | **yes** |
| **§8**, preamble | "Compiler defects found along the way are minimised, root-caused and fixed in dynlex" | R-18 **failed**: 20k lines take **72.19 s** against a 30 s budget and 50k lines take **1146.72 s**, with the implied exponent worsening from 1.89 to **3.03**. This is a blocker to fix before M1 in the criterion's own words *(m)* | A paragraph under §8 naming R-18 as an open blocker with its own tracking issue, and stating that M1 may not start before it is remeasured against a clean compiler pin | **yes** |
| **§9** M2 | exit criterion is "rotating extruded polygon on screen, driven only by kernel buffers" | Reachable today through the transient arena, which is exactly the trap: the arena holds **25 890 twelve-triangle boxes** and 10⁵ boxes cannot be drawn at all (**P-27**, source + arithmetic). The gap would surface at M7 instead of M2 | A second clause: the same kernel mesh drawn through an **index buffer and an instance buffer**, against persistent device-local storage | **yes** |
| **§10** | five targets, no reference | "targets are relative to something" is §15's own requirement and the table has no such column. The measured references exist: OCCT 4.2–4.7 s to tessellate **10⁴** boxes against a target of <1 s for 10⁵; Open3D's octree at **324.4 s** against <10 s; the fastest measured boolean on the twelve-opening wall is 0.997 ms and no candidate was measured at 10⁴ triangles; pick and section have no measured reference at all | A **measured reference** column carrying each number and its source. **No target is lowered** — §10's own rule is that targets are revised only by editing the table with the measured number beside them, and that is what this does | **yes** |
| **§12** | result values, no exceptions, no silent repair | Half of **P-15** is unanswered: the spec defines no cancellation token, no progress report and no memory or time budget, and three OCCT tickets describe exactly that failure (>10 GB on one boolean; 619 s against a 30 s deadline with no `UserBreak()` polling). Manifold ships the answer under Apache-2.0. Separately, a refusal that does not name its cause is unactionable (cadkernel's `Snag`) | §12 gains both: a cancellation/progress contract with a typed cancelled result, and the rule that an error names the class of input that defeated the operation. The **memory/time budget remains an open question**, stated as one | **yes** |
| **§4**, CSG dispatch | the exact mesh arrangement "is the only known approach that is robust on arbitrary input" | **Not shown, and the torture set cannot show it.** The fifteen candidate×setting combinations split **11 FAIL / 3 neither-pass-nor-fail / 1 PASS**: OCCT's three settings are valid on all ten cases but leave `sliver`'s residual between the pass and fail lines, which the criterion does not name; Blender Exact, Blender Fast, Manifold's four settings, CGAL's two and cadkernel's three all **fail**; Blender's embedded Manifold solver is the single pass. The two exact-arrangement implementations measured both fail (Blender Exact loses an operand on `touching_vertex`; CGAL Epick refuses two cases); the single nominal pass is Blender's embedded Manifold solver, which uses **neither** exact predicates nor exact constructions and whose pass rests on a refusal that happens to equal the right answer. The set is built from bit-identical coordinates, **the exact input class a symbolic tie-break wins**, and [`problems.md`](problems.md) P-03 states in terms that no ADR may cite the 9/10 as evidence of exactness | The sentence is restated: the exact arrangement is the approach the design evidence points to and **not a measured winner**; the test that would settle it is R-16 run against our own kernel, with the set extended to coordinates that are not bit-identical (**N-01**) | **yes** |
| **§5**, tolerance defaults | 1e-6 m linear and 1e-9 rad "by default" | The linear default **ties the loosest** of the compared industry defaults (ACIS `SPAresabs` 1e-6, exactly; two orders looser than Parasolid's 1e-8-unit session precision; one order looser than OCCT's 1e-7 m). The angular default is **looser than either commercial kernel's**, by two orders against Parasolid and three against OCCT, and this is the one row with no close prior-art number *(c)* | A sentence recording both facts beside the numbers, and naming cadkernel's scale-derived formula as the alternative to test. **The numbers are not changed** — this is a disclosure, not a revision | **yes** |
| **§1** and **§13** | "The research phase is over; this repository becomes a build repository"; §13 plans for "0003 marked superseded by 0004" | **ADR-0004 is not accepted** (§6.3 below). ADR-0003 remains in force and no kernel code is written | Both places gain a line saying the M0 repository restart is blocked until ADR-0004 is accepted, and that §13's table describes the repository *after* that acceptance, not a plan in force | **yes** |
| **§4**, representations | no provenance on a representation | cadkernel carries `Clean(SourceRef)` / `Dirty(SourceRef)` / `Synthesized` on every node and reuses clean records byte-for-byte on lowering. The note calls it the best idea in it and proposes it for §4 and for `ifc/` | Recorded here as a proposed amendment. **Not applied** — it is an addition to the kernel's data model rather than a correction of a claim the evidence contradicts, and it belongs in the spec revision that follows ADR-0004's acceptance, together with the `ifc/` sub-project's own spec | no |
| **§4**, point cloud | "position (f64, local frame)" | The storage encoding is undecided: Potree's int32 quantum is uniform but chosen **once per file**, and a project mixing a 1 mm terrestrial scan with a 5 cm airborne survey either wastes range or loses the fine one. Whether the scale is per tile, per cloud or per chunk is explicitly **not decided** by [`pointclouds.md`](pointclouds.md) §Risks | Recorded as an open question against §4 and ADR-0006, named in ADR-0006's evidence table. **Not applied** — deciding it needs a measurement nobody has | no |

---

## 5. What remains unmeasured

Assembled from the "what this does not settle" sections of the five `FINDINGS.md` files and the
notes' §Risks. Nothing below is a reason not to decide; each is a reason a decision below is
conditional, and each names what would close it.

1. **Curved-surface booleans.** All ten torture cases are boxes. **P-12** is where OCCT's own
   tracker concentrates and the set contains none. cadkernel refuses NURBS×NURBS by design. Spec
   §9 puts curved B-rep booleans at M8; nothing measured says what they cost.
   ([`../../../spikes/boolean-torture/FINDINGS.md`](../../../spikes/boolean-torture/FINDINGS.md)
   §What this does not settle)
2. **Chained operations.** Every case is one union and one intersection on fresh operands. OCCT's
   own Probe A is the single exception, and what it shows is narrower than "tolerance compounds":
   over eight chained fuzzy fuses of boxes separated by 5e-6 m gaps the maximum entity tolerance
   rose **once**, to 5.1e-6 (≈ fuzzy/2 + `Confusion`), and then **plateaued — it did not compound**.
   What grew linearly is the *metric error*: 3.33e-6 m³ of excess volume per step, 2.67e-5 m³ after
   eight ([`occt.md`](occt.md) §Tolerance model, Probe A). Chained behaviour for Blender, Manifold,
   CGAL and cadkernel was not measured at all.
3. **Real IFC input through any boolean.** Ten synthetic pairs, none carrying the
   self-intersections, duplicated faces and inconsistent winding real files do. The two refusals
   that decided three candidates' verdicts suggest the **refusal rate on real input** is the number
   that matters, and it is unmeasured.
4. **R-01 at its own scale.** The larger benchmark model is **3,822 elements — 4% of the 100k the
   criterion names** — and neither library was measured with a dependency graph in front of it. A
   wall move in a real modeller re-evaluates the wall *and* its openings, junctions and 2D views;
   that fan-out is unmeasured.
   ([`../../../spikes/incremental-evaluation/FINDINGS.md`](../../../spikes/incremental-evaluation/FINDINGS.md))
5. **Tessellation at 500 km.** R-17's spike sentence names "each candidate's boolean **and
   tessellation**"; no driver tessellates at the far location, and curved geometry is absent from
   the precision set altogether. This is what keeps R-17 `in progress`.
6. **Exactness against a lucky tie-break.** The torture set is built from bit-identical
   coordinates and cannot distinguish exact predicates from a symbolic tie-break that fires only on
   bit-equality. Closing it means extending the set with coordinates that are not bit-identical.
7. **The implicit representation has no measurement anywhere.** No OpenVDB or libfive wheel exists
   for this platform, so every claim in [`implicit.md`](implicit.md) is *claimed* or *inferred* from
   source. ADR-0005's implicit row inherits that limit.
8. **Three of the four point-cloud candidates were never run**, and the one that was is an in-core
   library on uniform synthetic points — the friendly case for a fixed-depth octree, so every
   octree number is a **lower bound** for real scans. Nothing measures the chunked, memory-mapped,
   partition-LOD design we actually propose.
9. **xBIM, libigl, OpenMesh, Truck, Fornjot, PCL, PDAL, Potree and the commercial kernels were read,
   not run.** Each note says so in its own §What was read.
10. **The DynLex GPU path is argued from source reading and arithmetic** — R-20, open. The runtime as
    it ships cannot draw the target scene at all.
11. **Nothing parallel or SIMD was measured in DynLex**, and spec §6 rests on both. R-18's figures
    exclude LLVM optimisation time, come from a **dirty compiler pin in exactly the phase under
    test**, are single-file programs, and the 50k figure is one run.
12. **Our own kernel has not been measured on anything.** R-16 and R-17 exist to be run against it;
    both FINDINGS say so in as many words, and that is the point of this whole directory.

---

## 6. The decisions

The rule applied is [`README.md`](README.md) §The rule and §Traceability, literally: *an ADR whose
evidence table has an empty or unsupported cell stays `proposed`.* Where a claim the evidence does
not support could be restated into one it does, the claim is restated and the restatement is
recorded — silently narrowing a claim to make it pass would defeat the rule.

### 6.1 ADR-0006 — **accepted**

f64 local coordinates in tile frames, exact predicates for combinatorial decisions, an explicit
per-entity tolerance model.

**What carried it.** The precision set separates two populations with three orders of magnitude of
clear air and no candidate in between: **every f64 path passes** (Manifold `Mesh64` 3.29e-11 m,
CGAL Epick 1.29e-10 m, OCCT 2.65e-10 m default and 3.61e-10 m at fuzzy=1e-5, cadkernel 0 m on two
cases) and **every f32 path fails** (0.0186 m to 0.5 m). The separation appears *within* one
library — Manifold `Mesh64` against `Mesh` — and *within* one set of exact predicates — CGAL f64
against f32-rounded — not only across libraries, which is stronger evidence than a single failing
candidate would have been. The exact-predicate half gained a direct measurement it did not have
when the ADR was written: **2164 of 4096 plain-double answers wrong, 0 of 4096 for the exact
predicate**, against an exact-rational oracle ([`cgal.md`](cgal.md) §The predicate is worth having).
The tolerance half is measured on OCCT twice, and the two probes say different things, so neither is
generalised here. **Probe A** (eight chained fuzzy fuses of boxes separated by 5e-6 m gaps): the
maximum entity tolerance rose **once**, to 5.1e-6 — ≈ fuzzy/2 + `Confusion` — and then **plateaued;
it did not compound over the chain**. What grew linearly is the *excess volume*, 3.33e-6 m³ per step
to **2.67e-05 m³** after eight steps, because every bridged gap is counted as solid. **Probe B** (one
`BRepAlgoAPI_Fuse` on the `sliver` case under `SetFuzzyValue(1e-3)`, `SetNonDestructive` at its
default off): the largest tolerance on the **input** shapes rose from 1.525e-7 to **5.001e-4** — a
single operation degrading its own arguments, and on the clean `overlap_half` case nothing grew at
any fuzzy value. So tolerance is **inherited and never reported**, not measured here to be
cumulative; the never-shrinking half is independently documented as an invariant for a commercial
kernel ([`occt.md`](occt.md) §Tolerance model, Probes A and B).

**What is stated rather than hidden, in the ADR itself:** Option B's evidence is rewritten, because
`cgal.md` §Measurements cannot be cited for Nef's cost — nothing about Nef was measured here, and
CGAL's shipped boolean is a **third** position the ADR did not name (exact constructions held for
one operation, rounded at its boundary, **8.183 ms** on the twelve-opening wall union — FINDINGS
§Summary, CGAL Epick f64) with Manifold a **fourth** (double predicates plus a bit-equality
tie-break, **0.997 ms** on the same union at its default tolerance — FINDINGS §Summary, Manifold
f64 default tol), the two separated by roughly **8.2×** on that one case. The GPU row is *inferred*
from source reading, not measured, and R-20 is open. The point-cloud storage quantum is an open
question. The linear default ties the loosest industry default and the angular default is looser
than any of them. None of these unmakes the decision; all of them are in the ADR.

### 6.2 ADR-0005 — **accepted**

Four equal representations, explicit conversions, boolean dispatched per representation.

**What carried it.** Every candidate that holds one representation pays for it exactly where the
product needs strength, and each cost is measured or read from source: OCCT needs **4.2–4.7 s** to
tessellate 10⁴ planar boxes and has no implicit representation at all; Manifold cannot hold an exact
curved surface; CGAL's several representations live in separate packages under two licences and are
not one kernel; cadkernel's mesh is export-only. Per-representation dispatch is supported by the
refusal pattern rather than by preference: **each mesh boolean measured has a precondition that real
input violates** — Manifold's `NotManifold` on a T-junction, CGAL's two documented corefinement
preconditions, cadkernel's `faceted_solid` refusing both a T-junction and a twelve-shell tool — so a
single shared algorithm would inherit one precondition for every representation.

**This ADR holds under either outcome of ADR-0004**, which is why it can be accepted while ADR-0004
cannot. [`opencadstudio.md`](opencadstudio.md) §Verdict (a) states it directly: if the B-rep arm
were built on cadkernel, "the four-representation `boolean(A, B, op)` dispatch of §4 would be ours
with cadkernel filling one of its four arms". The decision is about the kernel's shape, not about
who writes each arm, and it does not contradict ADR-0003.

**What is stated rather than hidden:** the "exact arrangement is the robust mesh boolean" claim is
**restated, not ticked** — see §4 above; it is now a design choice whose proof is R-16 against our
own kernel. The implicit representation's row is *claimed and inferred only*, because no implicit
library could be run on this platform. The point-cloud row is measured for an in-core library and
*inferred* for the design we propose. **N-03** ("four representations, four sets of bugs") stands
as an accepted, milestone-gated cost: a representation that fails its milestone's exit criterion is
deleted, not carried.

### 6.3 ADR-0004 — **amended, and stays `proposed`**

Build our own geometry kernel, written in DynLex.

Two halves, and they come out differently.

**The geometry half is nearly shown, and the ADR's claim as written is too strong.** The claim has
to be enumerated rather than counted loosely, because §2 above scores twenty-one candidates and four
of them are not candidates for the kernel role at all: **FreeCAD** (not scored — an application),
**Parasolid / ACIS** (a documentation-only reference), **Potree** (not applicable — a converter and a
viewer) and the **DynLex graphics runtime** ("it is the given"). That leaves **seventeen candidates
evaluated for the kernel role**, and they fall out as follows, each verdict as its own note's
§Verdict words it:

- **Eleven are an unqualified no**, each for a reason the note records: **OCCT**, **Truck**,
  **Fornjot**, **Blender**, **libigl**, **OpenMesh**, **PCL**, **Open3D**, **libfive**, **web-ifc**,
  **xBIM** — GPL or a GPL-licensed boolean (Blender, libigl's shipped pipeline), float32 storage or
  float32 at the API boundary (Blender, PCL, web-ifc, OpenMesh's default), no invalidation mechanism
  (web-ifc, xBIM), no embeddable surface (Truck, Fornjot, OCCT, PCL, Open3D), an archived project
  (Fornjot), or library rather than kernel scope (libigl, OpenMesh, libfive).
- **Three are a no for the kernel and a yes for a role that is not the kernel:** **Manifold** ("no as
  a kernel; yes as a candidate boolean component" — recorded and **not taken**), **PDAL** ("no as the
  module; genuinely yes as an ingest dependency"), **IfcOpenShell** ("yes for parsing and
  representation mapping; qualified yes for geometry, and no as the evaluation layer").
- **Two carry a build-on question their note leaves open rather than closed:** **CGAL** — no as the
  kernel and no as the boolean, but "linking Epick as an LGPL library for its predicates … is a live
  option" the note does not close — and **OpenVDB** — no as a kernel, but "could plausibly sit behind
  the kernel's `implicit` module … not answered here".
- **One is cadkernel, and it is not a no.** It is a *conditional shortlist* for the B-rep arm —
  MPL-2.0, f64 throughout, generational typed handles, a typed refusal, an identity residual of
  exactly 0 on every case that ran — held back by cost and maturity rather than by an assumption the
  product cannot accept: 3 of 10 benchmark cases produce nothing, it is 5–110× slower than the other
  candidates, single-threaded, one representation, has no exact predicates, is 34 days old with no
  release, and its C ABI does not exist and would be ours to write and maintain.

So the row's claim is amended from "no candidate can be built on without a disqualifying assumption"
to what the evidence supports: **of the seventeen candidates evaluated for the kernel role, sixteen
cannot supply the kernel — eleven unqualified, three with a yes for another role, two with an open
build-on question that is narrower than the kernel — and one, cadkernel, is a live, priced option
for one of its four arms.**

**The language half is contradicted by its own spike, and that is what keeps the ADR proposed.**

- **R-18 failed.** 20k lines compile in **72.19 s** against a 30 s pass line, 50k lines in
  **1146.72 s**, with the implied exponent worsening from 1.89 to **3.03**. The spike's own verdict:
  "a blocker to fix in dynlex before M1", and "the ADR should not move to `Accepted` on this row
  until it is fixed and remeasured". The 20k figure sits between the pass and the fail line on the
  narrower reading; the findings apply the wider reading and say why. Memory is not the problem
  (2.8 GB at 50k) and neither is correctness (zero diagnostics, every binary matched an independent
  computation).
- **R-19 passed, conditionally.** 1.12× / 1.23× / 1.01× against C++ `-O2`, with bit-identical
  output — but only with an explicit `-O` flag; the compiler's default emitted-code level is `-O0`,
  where the same workloads are 9.09× / 6.78× / 21.14×.
- **P-28.** Spec §6 item 4, §7 `gpu/` and §9 M7 assume DynLex compute kernels, and the compiler
  cannot emit a compute entry point. That is a language extension the spec did not list.

**Therefore ADR-0004 stays `proposed`, with three named acceptance conditions** written into the
ADR: R-18 remeasured against a clean pinned compiler and passing its own criterion; the compute
stage either scheduled as a dynlex extension or spec §6 item 4 rewritten to CPU threads with §10
rechecked; and the `-O` requirement carried in the kernel's build, which spec §8 now states.

**Its Options section gains two options the research produced**, both concerning cadkernel, both
argued in the ADR with the evidence for and against: porting cadkernel from Rust to DynLex as the
content of the first kernel milestones — **the maintainer's proposal, 2026-09-11** — and building
on cadkernel behind a C-ABI shim.

### 6.4 ADR-0003 — **stays `accepted`, not superseded**

ADR-0003 named its own reconsideration trigger: "writing our own is reconsidered only if the
research shows that no candidate can meet a requirement we are unwilling to drop — and that
reconsideration requires a new ADR". The research has now produced that reconsideration, and the new
ADR is **not accepted**. ADR-0003 therefore remains in force, unchanged and not marked superseded.

Neither ADR-0005 nor ADR-0006 contradicts it. ADR-0006 constrains *which* kernel may be built on —
it rules out every float32 path measured — and ADR-0005 describes a shape whose arms may be built,
borrowed or bought independently.

### 6.5 The kernel spec — **stays a working hypothesis**

[`2026-09-09-geometry-kernel-design.md`](../../superpowers/specs/2026-09-09-geometry-kernel-design.md)
stays **not accepted**. §5's numerics and §4's representation model are now carried by accepted ADRs
(0006 and 0005); §1's premise — that we build the kernel ourselves, in DynLex — is not, and the
spec's own §0 rule stands: **until ADR-0004 is accepted, ADR-0003 remains in force and no kernel
code is written.** The M0 repository restart in §9 and §13 is blocked on the same condition.

---

## 7. Corrections

Inconsistencies found while assembling this file. Per the programme's rule, a note's measured
numbers and its verdict are **not** edited here; they are recorded for the final review to triage.

1. **[`manifold.md`](manifold.md) line 203** carries a forward reference that names §Known problems
   where §The contract is meant. Cosmetic; not corrected here.
2. **ADR-0005's evidence row "Explicit conversions avoid documented loss" pointed at
   `kernels/ifcopenshell.md` §IFC geometry mapping and `kernels/web-ifc.md` §IFC geometry mapping.
   Neither section exists**, and both notes answer the round-trip question in §The twelve questions
   with *"not measured"*. The row is repointed at the evidence that does exist — **P-10** (shown and
   narrower than the row originally claimed), **P-11**, **P-26** and **P-31** — and relabelled.
3. **ADR-0006's Option B cited `kernels/cgal.md` §Measurements for the cost of exact rational
   arithmetic.** That section measures the Epick corefinement path only; the wheel exposes no
   `Nef_polyhedron_3` and no Epeck mesh type, so **nothing about the exact-construction path was
   measured**. Corrected in the ADR, as [`cgal.md`](cgal.md) §Corrections asks.
4. **`docs/risks.md` R-17 quoted OCCT's worst deviation as 3.61e-10 m** without saying it is the
   fuzzy=1e-5 figure; the default-setting figure is 2.65e-10 m. Both are now given.
5. **`docs/risks.md` R-15 says the IFC2x3 georeferencing convention lives on `IfcSite`.**
   IfcOpenShell writes `ePSet_ProjectedCRS` and `ePSet_MapConversion` on the **`IfcProject`**
   ([`ifcopenshell.md`](ifcopenshell.md) §Georeferencing). Which placement real exporters use is a
   separate measurement; the discrepancy is now recorded in R-15 rather than only in the note.
6. **[`problems.md`](problems.md) P-08 was doubly contradicted** — by OCCT and IfcOpenShell in the
   row itself, and a third time by Manifold, which is TBB-parallel throughout with a size-based
   policy. The row is restated here (it is a file this task edits) rather than left as "single-
   threaded evaluation… seen in OCCT".
7. **The spike files' own cross-references are consistent**: [`cgal.md`](cgal.md) was re-synced to
   the 2026-09-11 run (7.11e-15, "roughly two times tighter", not four), and the precision and
   torture FINDINGS each scope their run-to-run sections to their own files.
8. **Four timing figures in §1c were the pre-re-run ones and have been replaced with the values at
   HEAD.** The 2026-09-11 re-run moved timings by roughly −15% to +25%
   ([`../../../spikes/boolean-torture/FINDINGS.md`](../../../spikes/boolean-torture/FINDINGS.md)
   §Run-to-run reproduction), and the FINDINGS §Summary table is the file of record. The drift is
   recorded here rather than corrected in any note, per the programme's rule:

   | Row (this file, §1c) | Superseded figure | Figure at HEAD | Source row |
   |---|---|---|---|
   | OCCT, wall+12 openings ∪ | 52–54 ms | **54.03–58.52 ms** | [`results/occt.md`](../../../spikes/boolean-torture/results/occt.md), the three `wall_with_openings` rows |
   | OCCT, all other torture pairs | 0.42–4.53 ms | **0.47–4.62 ms** | FINDINGS §Summary, the three OCCT rows' time ranges |
   | Blender Exact, torture range | 0.37–15.95 ms | **0.47–18.26 ms** (wall ∪ **17.80**) | FINDINGS §Summary, `Blender 5.0 / Exact`; §Blender 5.0.0, `wall_with_openings` |
   | CGAL Epick, torture range | 0.011–8.21 ms | **0.010–8.183 ms** (wall ∪ **8.183**) | FINDINGS §Summary, `CGAL 6.0.1 / Epick, f64 input` |

   The same two superseded figures — CGAL's 8.21 ms and Manifold's **0.837 ms**, both the wall
   union at the 2026-09-10 basis — had reached ADR-0006's Option B, where they framed the
   exactness/speed trade's positions 2 and 3; both are corrected there to the FINDINGS §Summary rows
   (8.183 ms and 0.997 ms, roughly 8.2× rather than the 9.8× the old pair implied). Spec §10's
   reference column already carried the HEAD figures and is unchanged.
9. **Four candidate notes still quote their pre-re-run timings, and are deliberately not edited.**
   The re-run regenerated the `results/` files; the notes above them were re-synced for *residuals*
   ([`cgal.md`](cgal.md), item 7) but not for *timings*. Recorded here, per the rule that a note's
   measured numbers are not edited by this file:

   | Note, row | Figure the note carries | Figure in the results file at HEAD |
   |---|---|---|
   | [`occt.md`](occt.md) §Evaluation, Performance | wall ∪ 52–54 ms, ∩ 48–49 ms; other pairs 0.42–4.53 ms | **54.03–58.52** / **50.21–51.20**; **0.47–4.62** |
   | [`blender.md`](blender.md) §Evaluation, Performance | Exact 0.37–15.95, Fast 0.23–1.19, Manifold 0.29–1.76 ms | **0.47–18.26** / **0.25–1.18** / **0.30–1.91** |
   | [`manifold.md`](manifold.md) §Evaluation, Performance | 0.002–0.84 ms; wall ∪ 0.837, ∩ 0.588 | **0.003–0.997** at default tol (0.002–1.104 across all four settings); wall ∪ **0.997**, ∩ **0.650** |
   | [`cgal.md`](cgal.md) §Summary, §Evaluation Performance, §Verdict | 0.011–8.21 ms; wall ∪ 8.21, ∩ 7.84; "9.8× Manifold's 0.837 ms" | **0.010–8.183**; wall ∪ **8.183**, ∩ **8.082**; **≈8.2×** Manifold's **0.997 ms** |

   None of these moves a verdict: the FINDINGS' own run-to-run section records that timings moved
   by roughly −15% to +25% and that "no validity verdict, no pass/fail verdict and no volume above
   the 1e-12 level moved". This file, ADR-0005, ADR-0006 and spec §10 now use the HEAD figures
   throughout; the notes are left for the final review to triage.

---

## Sources

This file cites no external source of its own. Every claim above points at one of:

- the fourteen candidate notes in this directory, and
  [`../renderers/gpu-paths.md`](../renderers/gpu-paths.md);
- [`problems.md`](problems.md), P-01 … P-31 and N-01 … N-04;
- [`../../../spikes/boolean-torture/FINDINGS.md`](../../../spikes/boolean-torture/FINDINGS.md)
  (R-16), [`../../../spikes/precision-set/FINDINGS.md`](../../../spikes/precision-set/FINDINGS.md)
  (R-17),
  [`../../../spikes/incremental-evaluation/FINDINGS.md`](../../../spikes/incremental-evaluation/FINDINGS.md)
  (R-01), [`../../../spikes/dynlex-scale/FINDINGS.md`](../../../spikes/dynlex-scale/FINDINGS.md)
  (R-18),
  [`../../../spikes/dynlex-performance/FINDINGS.md`](../../../spikes/dynlex-performance/FINDINGS.md)
  (R-19), and the per-candidate result files under
  [`../../../spikes/`](../../../spikes/) those five assemble;
- [`../../risks.md`](../../risks.md), for the pass/fail criteria quoted verbatim in each FINDINGS.
