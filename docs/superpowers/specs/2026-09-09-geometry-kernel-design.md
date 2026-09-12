# Geometry kernel — design

**Date:** 2026-09-09
**Status:** working hypothesis — reviewed 2026-09-09, **still not accepted after the research
programme closed on 2026-09-12**. Every fundamental choice below was to be substantiated by the
research programme in `../plans/2026-09-09-kernel-research-programme.md` before ADR-0004, 0005 and
0006 are accepted (see §15). The programme has now run, and it decided two of the three:

- **ADR-0005 (four equal representations) — accepted.** §4's representation model and its
  per-representation boolean dispatch are decided, with the exact-arrangement claim restated (see
  §4 below).
- **ADR-0006 (f64 local coordinates, exact predicates, explicit tolerance) — accepted.** §5's
  numerics are decided.
- **ADR-0004 (build our own kernel, in DynLex) — amended and still `proposed`**, because R-18
  failed (20k lines compile in 72.19 s against a 30 s budget, with a worsening exponent), R-19
  passes only with an explicit `-O` flag, the compiler cannot emit a GPU compute entry point at all,
  and one candidate — `cadkernel` — is a live conditional option for the B-rep arm rather than a
  disqualified one.

**Therefore ADR-0003 remains in force and no kernel code is written.** The §9 M0 repository restart
and the repository layout in §13 are blocked until ADR-0004 is accepted; the three conditions that
would accept it are in that ADR under "What must be true before this ADR is accepted".

**Amended 2026-09-12** in §1, §4, §5, §6, §8, §9, §10, §12 and §13 per
[`../../research/kernels/synthesis.md`](../../research/kernels/synthesis.md) §4, which lists every
amendment, what contradicted the original wording, and which amendments were recorded but **not**
applied.
**Scope:** the geometry kernel sub-project of the open-bim-studio restart. The UI library and the
IFC library are separate sub-projects and get their own specs; this document fixes only what
they need to know about the kernel.

---

## 1. Why this restart

The repository so far was a research repository built around ADR-0003 ("build on an existing
kernel"). That decision is reversed: the maintainer has decided to build a new geometry kernel,
written in DynLex, together with a UI library and an IFC library in the same language. The
research phase is over; this repository becomes a build repository.

> **Amended 2026-09-12 per [`synthesis.md`](../../research/kernels/synthesis.md) §4.** The paragraph
> above is the hypothesis this document records, not a decision in force. ADR-0003 is **not**
> reversed: ADR-0004 is still `proposed`, and the research phase closed by keeping it that way. Read
> §1 as "what this design assumes", and the Status block at the top for what is actually decided.

The product goal in `docs/vision/vision.md` stands: a BIM modeller with the semantics of a
professional authoring tool and the immediacy of a real-time 3D application. The structural
requirements in `docs/domain/capability-inventory.md` and `docs/domain/spatial-model.md` stand.
What changes is *how* the geometry layer is obtained.

The kernel's ambition, in the maintainer's words: the representational breadth of a B-rep
kernel such as OpenCascade (B-rep, mesh, point clouds, CSG), the speed of Blender, the numeric
accuracy of AutoCAD, and enough further representations that any shape can be made.

## 2. Decomposition of the whole effort

One monorepo, three libraries and later an application:

```
kernel/   geometry kernel                      — this spec
ui/       Vulkan-based UI and viewport library — later spec
ifc/      IFC/STEP read-write library           — later spec
app/      the BIM modeller itself               — later
```

The kernel comes first because both other libraries depend on it and because it carries the
largest unknowns (robustness of booleans, precision, performance).

## 3. Position and boundaries of the kernel

The kernel is a pure DynLex library. It owns geometry, topology, numerics, spatial indexing and
GPU-ready data layouts. It does **not** own a window, a swapchain, input, or any file format
other than its own and the two plain-text test formats (OBJ, PLY).

| Owns | Does not own |
|---|---|
| representations, conversions, modelling operations | Vulkan presentation (→ `ui/`) |
| exact predicates, tolerance model, coordinate frames | IFC/STEP (→ `ifc/`) |
| BVH, octree, tile grid, ray casting, picking | semantic BIM model, parameters, evaluation graph (→ `app/`) |
| vertex/index buffer layouts, camera-relative f32 conversion, compute kernels (SPIR-V) | shaders that draw, materials, UI |

"Read and write with Vulkan" is realised as: the kernel produces buffers in layouts that upload
without repacking, and it consumes buffers produced on the GPU (compute results, picking
readback) in the same layouts. The `ui/` library performs the actual uploads and draws.

## 4. Representations

Four representations are first-class and equal. No representation is "the source" from which
the others are derived; each is chosen per object by the caller.

| Representation | Data | Chosen for |
|---|---|---|
| **B-rep** | vertices, edges, coedges in loops, faces, shells, solids; per-face analytic surfaces (plane, cylinder, cone, sphere, torus) or NURBS surfaces; per-edge analytic curves (line, circle, ellipse) or NURBS curves; a tolerance per vertex, edge and face | exact dimensions, true curved faces, export to IFC geometry |
| **Mesh** | half-edge mesh with f64 positions; per-vertex, per-corner and per-face attributes (normals, UVs, material id, arbitrary named channels); polygonal faces, triangulation on demand | speed, free-form modelling, display |
| **Point cloud** | chunked structure-of-arrays: position (f64, local frame), colour, intensity, normal, classification; octree over chunks | scans, terrain, level-of-detail streaming |
| **Implicit (SDF)** | tree of signed-distance primitives and combinators (union, intersection, difference, smooth blends, offset, transform); evaluated on demand and sampled to a mesh | offsets, blends, organic shapes, cheap CSG previews |

### Conversions are explicit

There is no implicit conversion anywhere in the API. Each conversion is a named operation with
its own parameters and its own failure modes:

| From → to | Method | Parameters |
|---|---|---|
| B-rep → mesh | tessellation | linear deflection, angular deflection |
| mesh → B-rep | planar face recovery; non-planar regions become NURBS faces through fitting (M8) | coplanarity tolerance |
| implicit → mesh | dual contouring on an adaptive octree | cell size, feature angle |
| mesh → implicit | signed distance field from a closed mesh | grid resolution |
| curve → polyline, surface → mesh | sampling | deflection |
| point cloud → mesh | surface reconstruction; not in M0–M8, scheduled after M8 | — |

### CSG dispatches on representation

`boolean(A, B, operation)` is one operation with representation-specific implementations:

- B-rep × B-rep → B-rep boolean. Planar faces first (BIM geometry is mostly planar); curved
  faces in M8.
- mesh × mesh → exact mesh boolean: exact arrangement of the two triangle sets using exact
  predicates, then classification. This is the approach Blender adopted for its exact boolean, and
  it is the approach the design evidence points to — **not a measured winner**.
- implicit × implicit → a new implicit node; free.
- Mixed representations: the caller passes a conversion policy (which side converts, with which
  parameters). The kernel never picks one silently.

> **Amended 2026-09-12 per [`synthesis.md`](../../research/kernels/synthesis.md) §4.** The mesh
> boolean bullet used to say the exact arrangement "is the only known approach that is robust on
> arbitrary input". R-16 does not support that. The fifteen candidate × setting combinations split
> **11 FAIL / 3 neither-pass-nor-fail / 1 PASS** — the three that are neither are OCCT's three
> settings, valid on every case but with `sliver`'s residual between the pass and the fail line;
> **both** exact-arrangement implementations measured fail (Blender's Exact solver loses an
> operand on `touching_vertex`; CGAL's Epick corefinement refuses two cases); the single nominal
> pass uses neither exact predicates nor exact constructions; and the torture set is built from
> bit-identical coordinates, which is the input class a symbolic tie-break wins — so the set
> **cannot distinguish exactness from a tie-break at all**
> ([`spikes/boolean-torture/FINDINGS.md`](../../../spikes/boolean-torture/FINDINGS.md) §What this
> does not settle; `problems.md` P-03). The design stands; the claim about it does not. What settles
> it is R-16 run against our own kernel at M5, on a set extended with coordinates that are not
> bit-identical — `problems.md` N-01's mitigation.
>
> Also recorded and **not applied here**: cadkernel's per-node provenance
> (`Clean(SourceRef)` / `Dirty(SourceRef)` / `Synthesized`, with clean records reused byte-for-byte
> on lowering) belongs in this section and in the `ifc/` spec. It is an addition to the data model
> rather than a correction, and it waits for the spec revision that follows ADR-0004's acceptance
> ([`../../research/kernels/opencadstudio.md`](../../research/kernels/opencadstudio.md) §Borrow
> from 2).
>
> **Open question against the point-cloud row**, named rather than decided: the table says
> "position (f64, local frame)", and the research found a cheaper *storage* encoding that is
> position-independent by construction — `int32 × scale + f64 offset`, 12 bytes, ±2 147 km at 1 mm,
> which LAS and Potree both ship. Its cost is that the scale is chosen once per file, so a project
> mixing a 1 mm terrestrial scan with a 5 cm airborne survey either wastes range or loses the fine
> one. **Whether the scale is per tile, per cloud or per chunk is not decided**, here or in
> ADR-0006; it belongs with the `pointcloud` module at M6
> ([`../../research/kernels/pointclouds.md`](../../research/kernels/pointclouds.md) §Risks).

## 5. Numerics and precision

**All kernel coordinates are 64-bit floating point in a local frame.** This is stricter than
`spatial-model.md`, which proposed f32 local coordinates; that document is amended in M0 to f64
local coordinates with the tile architecture unchanged.

**Frames.** Every kernel object lives in a frame. A frame is a tile: a 64-bit origin in the
project's projected CRS plus a rotation. Geometry never stores world coordinates. Transforms
between frames are computed in f64 and are exact for translation by construction (origins are
chosen on a coarse grid). The kernel's `spatial` module owns the tile grid; the georeferencing
metadata (the `IfcMapConversion` equivalent) lives with the project in `app/` and `ifc/`.

**Two kinds of decisions, two kinds of arithmetic.**

- *Combinatorial* decisions — which side of a plane, do two segments cross, is a point inside a
  circle — use **exact adaptive-precision predicates** (`orient2d`, `orient3d`, `incircle`,
  `insphere`, and the segment/triangle intersection tests built on them). They are never wrong.
  The implementation follows Shewchuk's adaptive scheme: fast floating-point filter, exact
  expansion arithmetic only when the filter cannot decide.
- *Metric* decisions — are two points the same point, is a face planar — use an explicit
  **tolerance model**: a linear tolerance and an angular tolerance, with defaults of 1e-6 m and
  1e-9 rad, overridable per operation. B-rep entities carry their own tolerance, which an
  operation may grow but never shrink, as in tolerant B-rep modelling.

Construction of new geometry (intersection points, projected points) is floating point and is
rounded; the predicates make the *topology* consistent with whatever was constructed, which is
what keeps booleans from producing invalid shells.

**GPU precision.** Only the `gpu` module converts to 32-bit: positions are expressed relative to
the camera's tile in f64 on the CPU, then truncated to f32 for upload. GPU double precision is
never required.

> **Amended 2026-09-12 per [`synthesis.md`](../../research/kernels/synthesis.md) §4 — three
> corrections to §5, none of which changes a decision.**
>
> **1. The camera-relative conversion is per *tile*, not per vertex.** Read literally, the paragraph
> above implies re-uploading every visible vertex buffer whenever the camera crosses a tile
> boundary. Neither implementation that ships does that
> ([`../../research/renderers/gpu-paths.md`](../../research/renderers/gpu-paths.md) §The correction
> this note makes to spec §5). What the `gpu` module does instead:
>
> - vertex positions are stored and uploaded **in their own tile frame, f32, once**, into static
>   `DEVICE_LOCAL` buffers that are never repacked — a tile a few hundred metres across gives an f32
>   ULP of ≤ 6.1e-5 m;
> - the f64 subtraction is `own_tile_origin − camera_tile_origin`, a `dvec3` computed on the CPU
>   **once per visible tile per frame** and folded into the object's instance transform before
>   truncation to f32;
> - `ui/` must therefore expose a per-draw or per-instance f32 affine transform, not a collapsed MVP
>   push constant, or step two has nowhere to put its result. That is `ui/` work and it is the
>   second clause of M2's exit criterion (§9).
>
> This keeps the guarantee above — GPU double precision is never required — and removes the
> repacking it implied. The arrangement is what OCCT and Filament both ship, and cadkernel confirms
> it works with instancing on a modern explicit API
> ([`../../research/kernels/opencadstudio.md`](../../research/kernels/opencadstudio.md) §3). **It is
> not measured**: R-20 is the spike that would measure it, and it is open.
>
> **2. The tolerance defaults are disclosed against industry practice.** 1e-6 m **ties the loosest**
> of the compared defaults — exactly ACIS's `SPAresabs`, two orders looser than Parasolid's
> 1e-8-unit session precision, one order looser than OCCT's 1e-7 m `Precision::Confusion()` — and
> 1e-9 rad is **looser than either commercial kernel's** angular tolerance, by two orders against
> Parasolid and three against OCCT
> ([`../../research/kernels/commercial-brep-reference.md`](../../research/kernels/commercial-brep-reference.md)
> §Verdict). The numbers stand as *defaults*: every operation may override them and every B-rep
> entity carries its own. The alternative to measure against them at M1 is cadkernel's
> scale-and-position-derived formula, `extent·1e-8 + ε·coordinate_scale·64`, which is a default
> rather than a replacement for the per-entity tolerance.
>
> **3. A frame is a contract, and a contract nothing enforces decays.** The local frame here is
> translation-only and the tile origins sit on a coarse grid, so the transform is exact by
> construction. cadkernel documents the same invariant — lift into a local frame at every entry
> point, anchored at the midpoint of the bounding box — and the spike found `Frame` constructed at
> **no call site** in its B-rep path, so its far-field arithmetic is unmitigated f64
> ([`../../research/kernels/opencadstudio.md`](../../research/kernels/opencadstudio.md) §Precision).
> Our entry points assert the frame invariant rather than document it. Note also what a local frame
> does **not** fix: a tolerance derived from a bounding box still tracks the model's global position
> — measured on two independent kernels
> ([`spikes/precision-set/FINDINGS.md`](../../../spikes/precision-set/FINDINGS.md) §The local-frame
> mitigation, §The tolerance follows the model out to 500 km).

## 6. Performance strategy

Targets are in §10. The means:

1. **Data-oriented layout.** Every representation is structure-of-arrays with contiguous
   storage. Entities are addressed by *generational handles* (index + generation), not
   pointers, so deletion is O(1), handles stay stable across reallocation, and dangling
   references are detected rather than dereferenced.
2. **Spatial indexing everywhere.** BVH over B-rep faces and over mesh triangles, octree over
   point-cloud chunks, a tile grid over objects. Every query (ray, box, nearest) goes through
   an index.
3. **Parallelism.** A `parallel for` over independent work items — tessellation of many
   solids, normal computation, boolean of many pairs, octree build. Requires DynLex runtime
   threading (§8). Until it exists, the same code runs serially and correctly.
4. **GPU compute.** DynLex compiles to SPIR-V. Embarrassingly parallel work with large inputs
   (tessellation of instanced solids, normal generation, frustum and occlusion culling, point
   cloud LOD selection) is written as DynLex compute kernels in `gpu/` and dispatched by `ui/`.

   > **Amended 2026-09-12 per [`synthesis.md`](../../research/kernels/synthesis.md) §4.** The
   > compiler **cannot emit a compute entry point today**: the shader stage is a two-member enum,
   > the CLI accepts only `vertex` or `fragment`, and the runtime has zero `vkCmdDispatch`, zero
   > compute pipelines and zero storage buffers (`problems.md` **P-28**;
   > [`../../research/renderers/gpu-paths.md`](../../research/renderers/gpu-paths.md) §The gap list).
   > That is a language extension, and §8's table did not list it; it does now. **Until the
   > extension exists, every item above runs on CPU threads (§8's first row) and §10's targets are
   > checked against that, not against a GPU that cannot be dispatched to.** If the extension proves
   > too large to build, this item is rewritten rather than left standing — it is the second of
   > ADR-0004's three acceptance conditions.
5. **No per-entity heap objects, no hidden copies.** Operations take handles and write into
   caller-provided or kernel-owned arenas.

## 7. Module layout

Each module has one purpose, a public `.dl` surface, private files marked `local`, and its own
`tests/`. Dependencies point downward only.

```
kernel/
  core/        f64 vec2/vec3/vec4, mat3/mat4, quaternion, rigid transform, frame;
               tolerance model; exact predicates; generational handles; bbox; results
  curves/      line, circle, ellipse, polyline, B-spline/NURBS curve: evaluate, derivative,
               closest point, split, curve–curve intersection
  surfaces/    plane, cylinder, cone, sphere, torus, NURBS surface: evaluate, normal, closest
               point, surface–surface and curve–surface intersection
  brep/        topology (vertex/edge/coedge/loop/face/shell/solid), geometry attachment,
               Euler operators, validity check, healing
  mesh/        half-edge mesh, attributes, primitives, extrude/inset/subdivide/decimate,
               normals, triangulation, validity check
  pointcloud/  chunked SoA storage, octree, LOD, normal estimation, decimation
  implicit/    SDF node tree, evaluation, gradient, dual contouring
  csg/         boolean dispatch; exact mesh arrangement; B-rep boolean; conversion policy
  convert/     all cross-representation conversions of §4
  spatial/     BVH, octree, tile grid, ray cast, box query, nearest, pick
  ops/         extrude, revolve, sweep, loft, offset, shell, fillet/chamfer, planar section
               (any representation → 2D curves in the section plane), projection outline
  gpu/         vertex/index/instance buffer layouts, camera-relative f32 packing, compute
               kernels (SPIR-V) for tessellation, normals, culling
  io/          kernel binary format (versioned), OBJ and PLY read/write for tests
  benchmarks/  the measurements of §10
  tests/       cross-module tests and reference-model regressions
```

Dependency order: `core` ← `curves` ← `surfaces` ← {`brep`, `mesh`, `pointcloud`,
`implicit`} ← {`csg`, `convert`, `spatial`, `ops`} ← {`gpu`, `io`}.

## 8. Required DynLex extensions

DynLex is the maintainer's own language (`../dynlex`, pinned commit in
`metadata/DYNLEX_COMMIT`). Extending it is in scope. Each extension is a separate change in the
dynlex repository following its `AGENTS.md`, with its own tests, made when the milestone that
needs it starts.

**Amended 2026-09-12 per [`synthesis.md`](../../research/kernels/synthesis.md) §4:** the threading
row moves from M7 to **M6**, and four rows are added — the compute stage, two missing language
facilities, and the build flag. Every added row cites the evidence that found it.

| Extension | Needed by | Notes |
|---|---|---|
| Threads, a thread pool, atomics, a `parallel for` section intrinsic | **M6** *(was M7, amended 2026-09-12)* | `src/runtime` has no threading today. **Moved forward because the point-cloud octree build needs it at M6, not M7**: an in-core single-threaded build over 10⁸ points measured **324.4 s on one core of thirty-two**, against §10's 10 s target (`problems.md` **P-13**, **P-17**; [`../../research/kernels/pointclouds.md`](../../research/kernels/pointclouds.md) §Measurements). §6 item 3 already lists "octree build" among the `parallel for` targets; M7 remains the milestone that *measures* threading, not the one that introduces it |
| Aligned and memory-mapped allocation | M6 | point clouds exceed RAM; chunks are mapped from the kernel binary format. An index over mapped chunks must **address** them and never copy them — an index that duplicates the coordinates cancels this row (`problems.md` P-13, second root-cause term) |
| Verified SIMD codegen for f64 aggregates on CPU | M1 | `@intrinsic("vector", count, kind)` already builds typed LLVM vectors; measure, extend only if lacking. **Nothing in R-19 measured SIMD or parallel code**, so this row is unevidenced in both directions |
| **A SPIR-V `GLCompute` entry point** — with workgroup builtins, storage buffers, barriers and a memory model | **M7** *(added 2026-09-12)* | §6 item 4 and §7 `gpu/` assume compute kernels compiled from DynLex, and the compiler cannot emit one: `enum class ShaderStage { Fragment, Vertex }`, and the CLI accepts only `vertex` or `fragment` (`problems.md` **P-28**; [`../../research/renderers/gpu-paths.md`](../../research/renderers/gpu-paths.md) §The gap list). **This is not a CLI flag.** Until it exists that work runs on CPU threads |
| **Unsigned integers, or a logical right shift** | **M1** *(added 2026-09-12)* | `shift right` lowers to LLVM `ashr` and there is no unsigned integer type — confirmed at runtime, `(0 - 8) as a 64 bit integer >> 1` prints `-4`. Hash functions, bit-packed handles and PRNGs all want one; R-19's workload masked the sign-extended bits off by hand ([`../../../spikes/dynlex-performance/FINDINGS.md`](../../../spikes/dynlex-performance/FINDINGS.md) §Language facilities that were missing) |
| **Scientific-notation float literals** | **M1** *(added 2026-09-12)* | `1.0e-16`, `1.1102230246251565e-16` and `1e-16` are all rejected; a 53-digit plain decimal is accepted and parses exactly. A numerics module full of error bounds needs the notation (same source) |
| **An explicit `-O` flag in the kernel's build** — not a language extension, a build requirement | **M0** *(added 2026-09-12)* | The compiler's default emitted-code optimisation level is `-O0`, verified in-repo by comparing a no-flag build against an explicit `-O0` build after neutralising the linker's embedded timestamp. Unflagged, R-19's workloads run 9.09× / 6.78× / 21.14× slower than C++ and would fail the criterion; with `-O2` they are 1.12× / 1.23× / 1.01×. `scripts/build.sh` passes the flag, and any measurement that omits it is a false failure |

The kernel will be the largest DynLex program written. Compiler defects found along the way are
minimised, root-caused and fixed in dynlex per its procedure — never worked around in the
kernel. The kernel keeps the dynlex conventions: `.dl` files, `local` for private definitions,
result values with an error message instead of exceptions, tests with `expected.txt`.

> **Amended 2026-09-12 — an open blocker, named here because it gates M1.** R-18 measured the
> compiler on synthetic programs in this kernel's style and **failed**: 5 005 lines in 5.26 s,
> 20 059 lines in **72.19 s** against a 30 s pass line, and 50 011 lines in **1 146.72 s** — with the
> implied exponent worsening from 1.89 (5k→20k) to **3.03** (20k→50k). Memory is not the problem
> (2.8 GB peak at 50k on a 32 GB machine, near-linear) and neither is correctness (zero diagnostics
> at every size; every binary printed exactly the value an independent computation produced). §7's
> module layout plainly implies a program well past 50k lines.
>
> In the fail criterion's own words this is "a blocker to fix in dynlex before M1". Per the
> paragraph above it is fixed in dynlex — a minimal reproducer and a root cause, not a workaround
> here — and re-measured against the clean commit `metadata/DYNLEX_COMMIT` will pin, because the
> binary measured was built from a **dirty** tree whose six modified files are all in type
> inference, the phase the spike loads hardest. The cheapest useful follow-up the findings name:
> separate whether the cost scales with pattern count, call-site count or lines, and whether it is
> per-file or whole-program — the second question decides whether separate compilation rescues the
> developer loop even if whole-program compilation stays slow.
> ([`../../../spikes/dynlex-scale/FINDINGS.md`](../../../spikes/dynlex-scale/FINDINGS.md); this is
> the first of ADR-0004's three acceptance conditions.)

## 9. Milestones

Each milestone ends in tested, working code and a short `FINDINGS.md` note of what was
measured. Order is fixed; later milestones may not start before earlier ones pass their tests.

| M | Content | Exit criterion |
|---|---|---|
| **0** | Repository restart: move all research to `docs/archive/`; ADR-0004 (own kernel in DynLex, supersedes 0003), ADR-0005 (multi-representation), ADR-0006 (f64 local coordinates in tile frames); rewrite README, CLAUDE.md, CONTRIBUTING; `kernel/` skeleton; `scripts/build.sh` and `scripts/test.sh` that locate the pinned dynlex compiler | `scripts/test.sh` passes on an empty kernel |
| **1** | `core`: vectors, matrices, quaternions, transforms, frames, tolerance model, exact predicates, handles, bbox, BVH | predicate fuzz test agrees with an exact-rational reference on 10⁶ random and degenerate inputs |
| **2** | `mesh`, `gpu`, `io`: half-edge mesh, primitives, extrude, normals, triangulation, OBJ/PLY, buffer packing; a test program shows a kernel-built mesh through the existing DynLex graphics library | rotating extruded polygon on screen, driven only by kernel buffers; **and** *(added 2026-09-12)* the same kernel mesh drawn through a **`u32` index buffer and an instance-rate buffer** out of persistent `DEVICE_LOCAL` storage, not the per-frame transient arena |
| **3** | `curves`, `surfaces`: analytic and NURBS evaluation, intersections; `ops`: planar section of a mesh → 2D curves | section of a reference mesh matches golden curves within tolerance |
| **4** | `brep`: topology, primitives, extrude/revolve/sweep, validity, tessellation, planar section | a B-rep building block tessellates and sections; Euler characteristic checks pass |
| **5** | `csg`: exact mesh boolean; B-rep boolean on planar faces; `implicit`: SDF tree, dual contouring | volume conservation `V(A∪B) + V(A∩B) = V(A) + V(B)` within 1e-9 relative on a randomised suite; no invalid shells |
| **6** | `pointcloud`: chunked storage, octree, LOD, normals, PLY and binary import | 10⁸ points loaded and indexed; nearest-neighbour queries verified against brute force on samples |
| **7** | Performance: dynlex threading, parallel tessellation and booleans, GPU compute kernels, benchmark suite | §10 targets met and recorded |
| **8** | `ops`: offset, fillet/chamfer, loft, shell, healing; `convert`: mesh → B-rep; B-rep boolean on curved faces | fillet on a B-rep corner; round trip B-rep → mesh → B-rep on planar solids is identity |

> **Amended 2026-09-12 per [`synthesis.md`](../../research/kernels/synthesis.md) §4 — M2's second
> clause, and why it is worth a milestone.** The original criterion is reachable *today* through the
> DynLex graphics runtime's transient arena, which is exactly the trap: that arena is the only path
> to the GPU, it is reset every frame, it is 32 MiB, and at 36 bytes a vertex it holds **25 890
> twelve-triangle boxes** — so a 10⁵-box scene is a hard error, not a slow frame (`problems.md`
> **P-27**; [`../../research/renderers/gpu-paths.md`](../../research/renderers/gpu-paths.md) §The
> DynLex graphics runtime in detail). Without the second clause the gap surfaces at M7, after five
> milestones have been built on top of it. The runtime today has no index buffers, no
> instance-rate attributes, no caller-supplied vertex layout and no persistent device-local
> geometry buffer; all four are `ui/` work, and [R-20](../../risks.md) is the spike that measures
> the result.
>
> **M5's exit criterion carries the other unfinished business.** Volume conservation on a randomised
> suite is necessary and not sufficient: the boolean torture set that R-16 uses is built from
> bit-identical coordinates, and on that input class a symbolic tie-break is indistinguishable from
> an exact predicate. M5's run of R-16 against our own kernel must extend the set with coordinates
> that are not bit-identical, or it cannot tell which of the two it has built (`problems.md`
> **N-01**, **P-03**).

## 10. Performance targets (M7, 8 CPU cores, desktop GPU)

**Amended 2026-09-12 per [`synthesis.md`](../../research/kernels/synthesis.md) §4:** a *measured
reference* column is added, because §15 requires the targets to be "relative to something" and this
table had nothing to be relative to. **No target is lowered.** The references are what mature
kernels actually measured on this machine, in this programme's spikes; three of the five rows have
no reference at all, and saying so is the point.

| Measurement | Target | Measured reference (candidate, this programme's spikes) |
|---|---|---|
| Tessellate 10⁵ extruded solids (≈10 faces each) | < 1 s | **OCCT: 4.2–4.7 s for 10⁴ planar boxes** (120 000 triangles, 35–40 µs/triangle), ~250 ms to construct them. One tenth the solids at four to five times the target, on a kernel with 26 years of tuning. Parallel meshing made it **slower** here (+8% average over four paired deflections) because the per-item work is too small ([`spikes/tessellation/results/occt.md`](../../../spikes/tessellation/results/occt.md)) — *measured* |
| Exact boolean of two 10⁴-triangle meshes | < 50 ms | **No candidate was measured at this size.** The largest torture case is a wall with twelve openings: Manifold `Mesh64` **0.997 ms**, CGAL Epick **8.18 ms**, Blender Exact **17.80 ms**, OCCT **58.52 ms**, cadkernel **refused** (its constructor will not build the twelve-shell operand). Three harnesses, so these are orders of magnitude, not a benchmark ([`spikes/boolean-torture/FINDINGS.md`](../../../spikes/boolean-torture/FINDINGS.md)) — *measured, at the wrong size* |
| Ray pick in a scene of 10⁶ elements through the BVH | < 5 ms | **No reference.** No candidate was measured on picking. R-19's BVH *build* over 10⁶ boxes ran in 422 ms in DynLex against 344 ms in C++ `-O2`, which says something about the language and nothing about the query — *unknown* |
| Build octree over 10⁸ points | < 10 s | **Open3D: 324.4 s**, single-threaded on one core of thirty-two, peaking at 13.13 GB, with the index costing 102.910 bytes/point — **4.3× the 24.011 bytes/point of the data it indexes**. All 300 verified nearest-neighbour answers matched a brute-force scan, so that is the cost of a *working* index. This is the number that moved threading from M7 to M6 (§8) ([`spikes/pointcloud-scale/results/open3d.md`](../../../spikes/pointcloud-scale/results/open3d.md)) — *measured* |
| Planar section through 10⁵ solids | < 200 ms | **No reference.** No candidate was measured on sectioning; OCCT has `BRepAlgoAPI_Section` and `HLRBRep` and neither was run — *unknown* |

A miss is reported, not hidden; targets are revised only by editing this table with the
measured number beside the target. **The reference column is not a target and is never a licence to
lower one** — it records what the field costs today, so that a miss can be read as "worse than a
mature kernel" or "better", rather than as a bare number.

## 11. Testing

- **Unit tests per module** in the DynLex convention: a `.dl` program and `expected.txt`.
- **Golden numeric tests**: evaluations of curves, surfaces and intersections against values
  computed independently (closed-form or high-precision).
- **Property tests**: volume conservation for booleans, Euler characteristic for B-rep and mesh
  validity, round-trip identity for conversions where identity is expected.
- **Fuzzing**: predicates against an exact reference; boolean inputs with random and
  deliberately degenerate configurations (coplanar faces, shared edges, touching vertices).
- **Reference models** in `reference/` (binaries gitignored, acquisition documented) for
  regression on real geometry.
- **Benchmarks** in `kernel/benchmarks/`, run explicitly, results committed as tables.

## 12. Error handling

Kernel operations return a result value: the value on success, otherwise an error with a
message and, where useful, the offending handles. There are no exceptions, no aborts on user
input, and no silent repair of invalid geometry: an invalid input is reported, and healing is
an explicit operation the caller invokes.

Internal invariant violations (a handle generation mismatch, a half-edge without a twin after
an operation) abort with a message — these are kernel bugs and must surface immediately.

**Amended 2026-09-12 per [`synthesis.md`](../../research/kernels/synthesis.md) §4.** Two additions
and one open question.

**An error names the class of input that defeated the operation.** "Boolean failed" is unactionable:
the caller cannot recover a cause the kernel discarded, and neither can the user. Every refusal
carries a named variant — no closed-form intersection, coincident faces, an unrepresentable result,
a violated precondition — alongside the offending handles. cadkernel ships exactly this shape
(`Snag::{NoClosedForm, Coincident, CutRefused}`) and the research found it the sharper half of the
lesson the rest of §12 already states
([`../../research/kernels/opencadstudio.md`](../../research/kernels/opencadstudio.md) §Borrow from
1). The negative example is in the same note: a construction failure returned as a bare `None`
carries no machine-readable cause, and the reason has to be read out of the constructor's source.
The positive one is CGAL, which refuses the *operation* that cannot be represented and only that
one, recording the reason per operation.

**A long operation is cancellable and reports progress.** Operations that can run unboundedly — the
mesh arrangement, the B-rep boolean, dual contouring, the octree build — take a context object
carrying a cancel flag, poll it at phase boundaries and once per parallel chunk, and return a
**typed cancelled result** rather than throwing or running on. This closes half of `problems.md`
**P-15**, which three OCCT tickets describe from the other side: >10 GB consumed by a *single*
boolean, and 619 s of CPU against a 30 s deadline that could not fire because nothing inside
`IntTools_FaceFace::Perform` polls for a break. The design is borrowable and so is the code:
Manifold ships `ExecutionContext` with `Cancel()`, `Cancelled()` and `Progress()` under Apache-2.0,
polled between phases and once per parallel chunk, returning an empty result carrying
`Error::Cancelled` ([`../../research/kernels/manifold.md`](../../research/kernels/manifold.md)
§Measurements).

**Still open: a memory and time budget.** Cancellation lets a caller stop an operation it is
watching; it does not bound one that nobody is watching. The other half of P-15 — a declared ceiling
on intermediate memory or elapsed time, enforced from inside the operation — is **not** designed
here, and the research found no candidate that has one either. It is an open question against §6 and
this section, recorded rather than papered over.

## 13. Repository after M0

> **Amended 2026-09-12 per [`synthesis.md`](../../research/kernels/synthesis.md) §4.** This section
> describes the repository **after ADR-0004 is accepted**, which it is not. In particular "0003
> marked superseded by 0004" is a plan, not a state: ADR-0003 is `accepted` and **not** superseded,
> ADR-0005 and ADR-0006 are accepted, and ADR-0004 is `proposed` with three named conditions. M0
> does not start, and nothing under `docs/` moves to `docs/archive/`, until those conditions are
> met.

```
README.md, CLAUDE.md, CONTRIBUTING.md   rewritten for a build repository
PROMPTS.md                              unchanged (originating prompts only)
docs/vision/, docs/domain/, docs/ux/    kept; spatial-model.md amended (f64 local)
docs/architecture/decisions/            0001–0003 kept (0003 marked superseded by 0004); 0004, 0005, 0006 added
docs/archive/                           research/, layers.md, overview.md, roadmap.md,
                                        risks.md, BUILD-BRIEF.md — moved, unmodified
docs/superpowers/specs/                 this spec and later ones
kernel/  ui/  ifc/                      ui/ and ifc/ hold only a README stating their brief
scripts/  metadata/                     build/test entry points; DYNLEX_COMMIT pin
reference/  spikes/                     kept
```

Repository rules that continue: everything on disk is English; competing calculation software
is never named; BIM and 3D software may be named; no conversation transcripts anywhere.

## 14. Out of scope for the kernel

Semantic BIM objects, parameters and evaluation, drawings beyond planar sections and outlines,
IFC, rendering, materials, undo (a concern of `app/` built on kernel handles), multi-user.

## 15. Evidence required before acceptance

Each fundamental choice in this document maps to a research question. The choice is accepted,
amended or withdrawn on the evidence; the evidence lives in `docs/research/kernels/` and
`spikes/`, and the ADR's evidence table cites it by section.

**Amended 2026-09-12:** the programme has run. Every row below is answered, and the answers are
assembled in [`../../research/kernels/synthesis.md`](../../research/kernels/synthesis.md) — §1 for
the completed matrix, §2 for the per-candidate verdicts, §3 for what this spec takes from each
candidate, §4 for the rows where the evidence contradicted this document, and §5 for what is still
unmeasured. The Status block at the top of this file records which ADRs that accepted and which it
did not.

| Choice (section) | Research question | Where answered | Decision record |
|---|---|---|---|
| Build our own kernel rather than build on one (§1) | Can any candidate be built on without inheriting a disqualifying assumption — batch evaluation, float32 paths, single origin, licence? | every candidate note, verdict axis *build on*; `problems.md` P-05, P-06, P-14 | ADR-0004 |
| Write it in DynLex (§1, §8) | Does DynLex compile and run kernel-shaped code at native speed, and can it be extended where it falls short? | spikes `dynlex-performance/`, `dynlex-scale/` (R-18, R-19) | ADR-0004 |
| Four equal representations (§4) | Which representations do existing kernels hold, what do their conversions lose, and where does a single-representation design fail? | candidate notes question 10; `problems.md` P-09, P-11, P-12 | ADR-0005 |
| Explicit conversions, no silent conversion (§4) | Where do silent conversions cause loss or surprise in existing kernels? | candidate notes question 10; IfcOpenShell and web-ifc notes on IFC geometry mapping | ADR-0005 |
| CSG by representation; exact arrangement for meshes (§4) | Which boolean algorithms are robust on the torture set, at what cost? | spike `boolean-torture/` (R-16) across OCCT, Blender, Manifold, CGAL | ADR-0005 |
| f64 local coordinates in tile frames (§5) | What precision do existing kernels use, and what fails far from the origin? | spike `precision-set/` (R-17); candidate notes question 6 | ADR-0006 |
| Exact predicates for combinatorial decisions (§5) | Which kernel failures trace to floating-point topology decisions? | `problems.md` P-01, P-03; OCCT, Blender and CGAL notes | ADR-0006 |
| Explicit tolerance model, per entity for B-rep (§5) | How do tolerances accumulate in tolerant B-rep, and what does it cost users? | OCCT note; FreeCAD case study; `problems.md` P-02 | ADR-0006 |
| Data-oriented layout and generational handles (§6) | Which scale ceilings trace to per-object overhead? | `problems.md` P-07; Blender/Bonsai note; R-03 spike | ADR-0004 (design rationale) |
| Kernel-owned GPU buffer layouts, compute in SPIR-V (§3, §6) | How do existing kernels and engines move geometry to the GPU, and what does the DynLex runtime already provide? | `research/renderers/` GPU-paths note | ADR-0004 (design rationale) |
| Milestone order and performance targets (§9, §10) | What do the mature kernels measure on the benchmark set, so the targets are relative to something? | candidate measurements on the benchmark set | none — targets are recorded, not decided |
