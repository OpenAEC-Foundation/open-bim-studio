# Geometry kernel — design

**Date:** 2026-09-09
**Status:** working hypothesis — reviewed 2026-09-09, **not accepted**. Every fundamental choice
below is to be substantiated by the research programme in
`../plans/2026-09-09-kernel-research-programme.md` before ADR-0004, 0005 and 0006 are accepted
(see §15). Until then ADR-0003 remains in force and no kernel code is written.
**Scope:** the geometry kernel sub-project of the open-bim-studio restart. The UI library and the
IFC library are separate sub-projects and get their own specs; this document fixes only what
they need to know about the kernel.

---

## 1. Why this restart

The repository so far was a research repository built around ADR-0003 ("build on an existing
kernel"). That decision is reversed: the maintainer has decided to build a new geometry kernel,
written in DynLex, together with a UI library and an IFC library in the same language. The
research phase is over; this repository becomes a build repository.

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
  predicates, then classification. This is the approach Blender adopted for its exact boolean
  and is the only known approach that is robust on arbitrary input.
- implicit × implicit → a new implicit node; free.
- Mixed representations: the caller passes a conversion policy (which side converts, with which
  parameters). The kernel never picks one silently.

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

| Extension | Needed by | Notes |
|---|---|---|
| Threads, a thread pool, atomics, a `parallel for` section intrinsic | M7 | `src/runtime` has no threading today |
| Aligned and memory-mapped allocation | M6 | point clouds exceed RAM; chunks are mapped from the kernel binary format |
| Verified SIMD codegen for f64 aggregates on CPU | M1 | `@intrinsic("vector", count, kind)` already builds typed LLVM vectors; measure, extend only if lacking |

The kernel will be the largest DynLex program written. Compiler defects found along the way are
minimised, root-caused and fixed in dynlex per its procedure — never worked around in the
kernel. The kernel keeps the dynlex conventions: `.dl` files, `local` for private definitions,
result values with an error message instead of exceptions, tests with `expected.txt`.

## 9. Milestones

Each milestone ends in tested, working code and a short `FINDINGS.md` note of what was
measured. Order is fixed; later milestones may not start before earlier ones pass their tests.

| M | Content | Exit criterion |
|---|---|---|
| **0** | Repository restart: move all research to `docs/archive/`; ADR-0004 (own kernel in DynLex, supersedes 0003), ADR-0005 (multi-representation), ADR-0006 (f64 local coordinates in tile frames); rewrite README, CLAUDE.md, CONTRIBUTING; `kernel/` skeleton; `scripts/build.sh` and `scripts/test.sh` that locate the pinned dynlex compiler | `scripts/test.sh` passes on an empty kernel |
| **1** | `core`: vectors, matrices, quaternions, transforms, frames, tolerance model, exact predicates, handles, bbox, BVH | predicate fuzz test agrees with an exact-rational reference on 10⁶ random and degenerate inputs |
| **2** | `mesh`, `gpu`, `io`: half-edge mesh, primitives, extrude, normals, triangulation, OBJ/PLY, buffer packing; a test program shows a kernel-built mesh through the existing DynLex graphics library | rotating extruded polygon on screen, driven only by kernel buffers |
| **3** | `curves`, `surfaces`: analytic and NURBS evaluation, intersections; `ops`: planar section of a mesh → 2D curves | section of a reference mesh matches golden curves within tolerance |
| **4** | `brep`: topology, primitives, extrude/revolve/sweep, validity, tessellation, planar section | a B-rep building block tessellates and sections; Euler characteristic checks pass |
| **5** | `csg`: exact mesh boolean; B-rep boolean on planar faces; `implicit`: SDF tree, dual contouring | volume conservation `V(A∪B) + V(A∩B) = V(A) + V(B)` within 1e-9 relative on a randomised suite; no invalid shells |
| **6** | `pointcloud`: chunked storage, octree, LOD, normals, PLY and binary import | 10⁸ points loaded and indexed; nearest-neighbour queries verified against brute force on samples |
| **7** | Performance: dynlex threading, parallel tessellation and booleans, GPU compute kernels, benchmark suite | §10 targets met and recorded |
| **8** | `ops`: offset, fillet/chamfer, loft, shell, healing; `convert`: mesh → B-rep; B-rep boolean on curved faces | fillet on a B-rep corner; round trip B-rep → mesh → B-rep on planar solids is identity |

## 10. Performance targets (M7, 8 CPU cores, desktop GPU)

| Measurement | Target |
|---|---|
| Tessellate 10⁵ extruded solids (≈10 faces each) | < 1 s |
| Exact boolean of two 10⁴-triangle meshes | < 50 ms |
| Ray pick in a scene of 10⁶ elements through the BVH | < 5 ms |
| Build octree over 10⁸ points | < 10 s |
| Planar section through 10⁵ solids | < 200 ms |

A miss is reported, not hidden; targets are revised only by editing this table with the
measured number beside the target.

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

## 13. Repository after M0

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
