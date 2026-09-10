# Manifold — a guaranteed-manifold mesh boolean, and what its guarantee costs

**Decision question:** Manifold is the fastest and most reliable open-source mesh boolean we have
measured. Can it be the boolean inside our kernel — and if not, which of its designs must ours
take, and which of its constraints must ours not inherit?

**Serves:** ADR-0004, ADR-0005, ADR-0006; kernel spec §4–§6, §12; R-16, R-17; `problems.md` P-09

**Status:** draft
**Author:** research programme, phase 2
**Last updated:** 2026-09-10

> This note measures the **standalone library at v3.5.3**.
> [`blender.md`](blender.md) already measured the same library **as embedded in Blender 5.0**,
> which bundles **v3.2.1** and feeds it float32 vertex positions. Where the two disagree, the
> difference is traced rather than asserted; nothing here contradicts that note.

---

## Summary

Manifold got every torture case it accepted numerically right on every setting, in **0.002–0.84 ms**
— 19× faster than Blender's exact solver on the twelve-opening wall and 64× faster than OCCT's
B-rep fuse on the same case, across three different harnesses (see §Evaluation) — and at 500 km from the origin on its float64 input path it held the
result to **3.3e-11 m**, passing R-17 outright. The cost is the contract in its name: it **refused**
the benchmark's T-junction operand with `Error::NotManifold` and an empty result, on both input
paths, and its default tolerance is keyed to the largest absolute coordinate, so the same geometry
gets a 5e-7 m epsilon at 500 km instead of 1e-12 m at the origin — and 0.0596 m if it arrived through
the float32 mesh type, which is the type the C++ `MeshGL` alias and most bindings default to.
It is a boolean to borrow from in detail and not a kernel to build on: it holds one representation,
it has no incremental evaluation, and its correctness contract admits slivers as in-spec output.

## What it is

Manifold is a C++17 library dedicated to booleans on oriented 2-manifold triangle meshes, written
by Emmett Lalish (`elalish`) with Zhen Li (`pca006132`) as the other principal maintainer. It is
Apache-2.0 (`LICENSE` at the tag) and has **no required dependencies**; TBB, Clipper2, nanobind and
Emscripten are all optional (`README.md` §Dependencies at the tag). The whole library is 23,598
lines of `.cpp` and `.h` under `src/` and `include/` at v3.5.3 (measured: `wc -l` over every file
matching `*.cpp` or `*.h` found recursively in those two directory trees) — small enough that one
person can read the whole boolean path.

Its boolean implements Julian Smith's algorithm; the maintainer states the goal in the README as
"guaranteed manifold output without caveats or edge cases", with reliability first and performance
second. The README is equally explicit about the price: "you'll get an error status if the imported
mesh isn't manifold", and repair is left to "automated repair tools that exist mostly for 3D
printing" (*claimed*, [README at the tag](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/README.md)).

It is widely embedded: OpenSCAD, Blender, Godot, BRL-CAD, trimesh and web-ifc all appear in the
README's user list. That matters for this programme in a specific way — **Blender's Manifold solver
and this library are the same code**, so [`blender.md`](blender.md) and this note measure one
artefact through two harnesses.

## What was read, and at which commit

| Area | Source, pinned |
|---|---|
| Public API, `Error` enum, tolerance accessors | [`include/manifold/manifold.h`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/include/manifold/manifold.h) |
| Cancellation and progress | [`include/manifold/common.h#L250-L299`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/include/manifold/common.h#L250-L299) |
| The boolean kernel cascade and symbolic perturbation | [`src/boolean3.cpp`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/boolean3.cpp), [`src/shared.h#L60-L96`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/shared.h#L60-L96) |
| Result assembly and tolerance propagation | [`src/boolean_result.cpp#L774-L782`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/boolean_result.cpp#L774-L782), [`#L828-L836`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/boolean_result.cpp#L828-L836) |
| Mesh ingest, manifoldness check, epsilon | [`src/impl.h#L471-L482`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/impl.h#L471-L482), [`src/impl.cpp#L682-L692`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/impl.cpp#L682-L692), [`src/shared.h#L28-L31`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/shared.h#L28-L31) |
| `kPrecision` | [`src/utils.h#L39`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/utils.h#L39) |
| Collider (LBVH) | [`src/collider.h`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/collider.h), design in [`docs/ParallelBVH.pdf`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/docs/ParallelBVH.pdf) |
| Threading policy | [`src/parallel.h#L34-L60`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/parallel.h#L34-L60) |
| Volume and area integrand | [`src/properties.cpp#L265-L294`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/properties.cpp#L265-L294) |
| Wheel build flags | [`pyproject.toml`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/pyproject.toml) |
| Correctness contract | [wiki: Manifold Library](https://github.com/elalish/manifold/wiki/Manifold-Library) (unversioned — see the caveat in §The contract) |

Measurements are in
[`spikes/boolean-torture/results/manifold.md`](../../../spikes/boolean-torture/results/manifold.md)
and
[`spikes/precision-set/results/manifold.md`](../../../spikes/precision-set/results/manifold.md),
produced by
[`spikes/boolean-torture/manifold_driver.py`](../../../spikes/boolean-torture/manifold_driver.py)
and
[`spikes/precision-set/manifold_driver.py`](../../../spikes/precision-set/manifold_driver.py)
against `manifold3d` 3.5.3 on an Intel Core i9-14900HX with 32 GB of RAM.

## Evaluation

| Criterion | Finding | Evidence type | Source / method |
|---|---|---|---|
| **License** | Apache-2.0. Permissive: code may be borrowed with attribution, not only ideas — the only candidate so far where that is true (OCCT is LGPL-2.1-with-exception, Blender GPL). | source | `LICENSE` at the tag |
| **Representations held natively** | **One**: an oriented 2-manifold triangle mesh with arbitrary vertex properties. Conversions exist outward — `Slice`/`Project` to 2D polygons, `Extrude`/`Revolve` back, `LevelSet` from an SDF to a mesh — but nothing else is *stored*. No B-rep, no point cloud, no volume. | source | `manifold.h` §Polygons, §Shapes |
| **Boolean robustness** | Measured on the torture set: **9 of 10 cases numerically correct and topologically valid on every one of four settings**, worst identity residual 3.55e-14. The tenth is not a wrong answer but a **refusal**: the T-junction operand is rejected as `NotManifold` on both the f32 and the f64 path. Algorithm class: floating-point predicates with **symbolic perturbation on exact equality**, not exact arithmetic. | measured + source | [`results/manifold.md`](../../../spikes/boolean-torture/results/manifold.md); `shared.h#L90-L96` |
| **Tolerance and precision model** | Two numbers per solid: `epsilon_`, derived as `kPrecision * Box::Scale()` with `kPrecision = 1e-12`, and `tolerance_`, the caller's promise, floored at epsilon. `Box::Scale()` is the **largest absolute coordinate**, so both scale with distance from the origin. Internal storage is `double` unconditionally; the *input* type chooses the precision — `Mesh`/`MeshGL` is float32, `Mesh64`/`MeshGL64` is float64, and a float32 ingest raises the floor to `FLT_EPSILON * Box::Scale()`. **A double path exists end to end**, which is the answer ADR-0006 needs. | measured + source | `impl.cpp#L682-L692`, `impl.h#L471-L482`, `utils.h#L39`; [`precision results`](../../../spikes/precision-set/results/manifold.md) |
| **Incremental evaluation** | **None.** `Manifold` is immutable and functional; operators build a deferred CSG tree that is evaluated once and discarded. There is no dependency graph, no handle to a leaf, and no way to re-evaluate one changed operand of a completed result. | inferred from source | `manifold.h` (every operator returns a new `Manifold`), `csg_tree.cpp` |
| **Threading model** | TBB throughout, chosen per call site by `autoPolicy(size)` with `kSeqThreshold = 1e4`, so small problems stay serial. The Python wheel is built `MANIFOLD_PAR=ON`. The maintainers treat run-to-run determinism as something to fix case by case, not as an invariant, and declined to reinstate a global deterministic mode. | source + tracker | `parallel.h#L34-L60`; `pyproject.toml`; [#1177](https://github.com/elalish/manifold/issues/1177) |
| **GPU path** | **None, by decision.** CUDA and OpenMP backends were removed in 2023; the v2.2.1 release notes record "Removed OMP and CUDA backends to focus on TBB" ([#525](https://github.com/elalish/manifold/pull/525), [#531](https://github.com/elalish/manifold/pull/531), closing [#524](https://github.com/elalish/manifold/issues/524)). Nothing reaches the GPU from this library; a caller uploads the exported triangles itself. | source + tracker | v2.2.1 release notes; PR #525 body |
| **IFC coverage** | Not applicable — no schema layer of any kind. | source | — |
| **Performance** | Measured, f64 path, median of 5, fresh operands per repeat: **0.002–0.84 ms** over the eighteen operations (nine accepted cases x union and intersection); the 0.002 ms floor is `disjoint`'s bounding-box early-out. Twelve-opening wall union **0.837 ms**, intersection 0.588 ms. For scale on the identical case: Blender's Manifold solver 1.76 / 1.33 ms, Blender's exact solver 15.95 / 15.90 ms, OCCT's `BRepAlgoAPI_Fuse` 53.97 / 49.24 ms single-threaded on a B-rep compound. | measured | [`results/manifold.md`](../../../spikes/boolean-torture/results/manifold.md), and the same tables for the other two candidates |
| **Embeddability** | Strong. No required dependencies, a plain **C ABI binding** (`bindings/c`, `MANIFOLD_CBIND`), a WASM build, and static linking as the wheel's default (`BUILD_SHARED_LIBS=OFF`). A DynLex FFI over the C header is the obvious integration and needs no subprocess and no file. | source | `bindings/c/include`, `pyproject.toml` |
| **2D derivation** | `Slice(height)` and `Project()` return polygons; `CrossSection` (Clipper2) does 2D booleans and offsets. **No hidden-line and no section hatching** — a section is a polygon set, not a drawing. | source | `manifold.h` §Polygons; `cross_section.h` |
| **Maturity** | 26 releases from v1.0.0 (2022-02) to v3.5.3 (2026-09), **nine of them in the last twelve months**. Two principal maintainers, so the bus factor is **2** and arguably 1 for the boolean itself. Downstream users include OpenSCAD, Blender, Godot and BRL-CAD, which is a real check on regressions. | source | `gh release list`; README §Users |
| **AI familiarity** | Small and heavily commented, with four design PDFs in `docs/`. One column, never a tiebreaker (R-09). | inferred | repository contents |

## How the boolean works, and why "exact" is the wrong word for it

Manifold does **not** use exact arithmetic. It evaluates the predicates of Julian Smith's boolean in
double precision and breaks ties symbolically at the point where two coordinates compare *exactly*
equal. The whole mechanism is three lines:

```
inline bool Shadows(double p, double q, double dir) {
  return p == q ? dir < 0 : p < q;
}
```

([`shared.h#L90-L96`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/shared.h#L90-L96);
the tie-break direction comes from the operands' own normals, and the sense is chosen per operation
— union expands both operands, difference and intersection contract the first — at
[`boolean3.cpp#L496-L505`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/boolean3.cpp#L496-L505).)

This is why the torture set's coplanar, shared-edge, touching-vertex and identical cases all come
out exactly right: those cases are built from coordinates that are *bit-identical*, so `p == q`
fires and the perturbation decides consistently. It is also precisely the limit the maintainers
name. On [#676](https://github.com/elalish/manifold/issues/676), where two identical cube pairs
behaved differently because one sat at `0.0999 * 51`, **`elalish` (OWNER)** answered "This is working as
intended" and explained that the library "uses the input float coordinates as though they are
exact". On [#1430](https://github.com/elalish/manifold/issues/1430) he calls symbolic perturbation
"more of a best-effort feature", and **`pca006132` (COLLABORATOR)** answers the report with "we don't
have a good way to fix it as of today".

**This distinction is load-bearing for our own design.** Blender's exact solver decides topology
with exact rational predicates and was still beaten on both correctness and speed by Manifold on our
set ([`blender.md`](blender.md) §Measurements). What Manifold shows is that *the cases a benchmark
built from exact coordinates exercises can be won without exact arithmetic* — and, in the same
breath through #676 and #1430, that the cases built from arithmetic on real coordinates cannot.
Our set is entirely of the first kind. That is a limit of the benchmark, and it is recorded here so
no ADR reads "Manifold is exact" out of the 9/10.

## The contract: manifoldness in, ε-valid out

Input must be an oriented 2-manifold: the wiki's *Manifoldness definition* requires that every
triangle edge "contain the same two vertices (by index) as exactly one other triangle edge", with
the start and end vertices swapped between them, and counter-clockwise winding seen from outside.
Output is only promised to be **ε-valid**: a mesh admits "a perturbation of the vertices (each by a
magnitude < ε)" that makes it non-overlapping
([wiki](https://github.com/elalish/manifold/wiki/Manifold-Library), linked from the README —
*claimed*; a GitHub wiki has no commit we can pin from the outside, so unlike every other citation
in this note this one may drift).

Two consequences are visible on the tracker and were **not** obvious to the reporters:

* Degenerate and sliver triangles are **in-spec output**, not defects. On
  [#1359](https://github.com/elalish/manifold/issues/1359) `pca006132` (COLLABORATOR) answers a
  report of degenerate triangles from coplanar faces with "Degenerate triangle is expected output",
  and points at the ε-valid definition. On
  [#1706](https://github.com/elalish/manifold/issues/1706) `elalish` (OWNER) writes that "slivers
  are very much expected to be produced by Smith's Boolean" and that `SimplifyTopology` is the
  intended, currently too conservative, cleanup.
* "Manifold" for this library means **manifold and correctly oriented**. A reversed-winding solid is
  not a negative volume to be subtracted; on [#1354](https://github.com/elalish/manifold/issues/1354)
  `pca006132` (COLLABORATOR) concludes it is "not a good idea to support negative volume meshes",
  and [#745](https://github.com/elalish/manifold/issues/745) remains open.

## Precision

### The tolerance is a function of where the project is

`Manifold::Impl::SetEpsilon` sets `epsilon_ = max(minEpsilon, kPrecision * bBox_.Scale())` with
`kPrecision = 1e-12`
([`impl.cpp#L682-L692`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/impl.cpp#L682-L692),
[`shared.h#L28-L31`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/shared.h#L28-L31),
[`utils.h#L39`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/utils.h#L39)),
and `Box::Scale()` is the **largest absolute coordinate**, not the diagonal
([`common.h`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/include/manifold/common.h)).
Measured, on the same unit box:

| Where the box sits | f64 tolerance | f32 tolerance |
|---|---|---|
| origin | 1e-12 m | 1.19e-07 m |
| 500 km out | 5.00e-07 m | **0.0596 m** |

*(measured, [`precision results`](../../../spikes/precision-set/results/manifold.md) §Storage.)*
Nothing about the building changed. A tolerance of 6 cm — wider than a brick joint — is decided by
the project's easting in a national grid. The f32 figure is the one Blender hits, because Blender
hands the library float32 positions.

### The boolean at 500 km

| Setting | Wall union V near / far | ΔV (relative) | Worst vertex deviation | R-17 |
|---|---|---|---|---|
| **f64** (`Mesh64`) | 12.6 / 12.5999999999 | −1.1e-11 | **3.3e-11 m** | **pass** (line 1e-6 m) |
| **f32** (`Mesh`) | 12.6000000179 / 12.7499997485 | +0.0119 | **0.0186 m** | **fail** (line 1e-4 m) |

*(measured, [`precision results`](../../../spikes/precision-set/results/manifold.md).)* The f32 row
reproduces Blender's number to the digit on volume — Blender's exact and Manifold solvers both
reported +0.15 m³ on this case — and differs on vertex deviation (0.0186 m here, 0.0348 m through
Blender), which is what different output triangulations of the same float32 grid look like. The
conclusion is the same one [`blender.md`](blender.md) drew and it is now shown to be independent of
Blender: **the loss is the storage type, not the algorithm.** Give the identical algorithm f64 input
and the error drops by a factor of 5.6e8.

### Local frames work — and this library shows why the frame origin must be f64

Carrying the 500 km in `Manifold.translate()` instead of in the vertex data leaves the **f32** result
byte-for-byte on the origin run: deviation **0 m**, volume 12.6000000179 against the origin's
12.6000000179. The float32 rounding happened at unit scale, and the move was applied in double.
On the f64 path the same probe changes nothing either way (3.3e-11 m, the same as the
offset-in-coordinates run), because f64 never needed rescuing.

The tolerance still rises: `Impl::Transform` re-derives epsilon from the **new** bounding box, so
`tol` goes 1.5e-12 → 5e-07 for the unit-scale cases (measured, transform probe). So a local frame
buys back the *geometry* and not the *tolerance*. That is exactly the half ADR-0006 has to be
explicit about, and it now has a second, independent measurement behind it.

### A warning about measuring volume at 500 km

`reference.signed_volume` sums `x0*(y1*z2 − z1*y2)` over raw coordinates. At 5e5 m each term is
~1e17 against a sum of ~12.6, and the sum loses **7.9e-05 m³** to cancellation on the wall case
*with no boolean and no library involved at all* — we measured it by shifting the origin result's own
vertices (measured, [`precision results`](../../../spikes/precision-set/results/manifold.md), last
probe). Manifold's own `Volume()` sums `dot(cross(v1 − v0, v2 − v0), v0) / 6` with Kahan
compensation ([`properties.cpp#L265-L294`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/properties.cpp#L265-L294))
and returns 12.5999999999 at the same place. The driver therefore reports far volumes on
back-translated vertices, and the probe exists so that choice is auditable. **Our kernel's mass
properties must use the differenced-and-compensated form; the naive divergence sum is unusable in a
national grid.**

## Known problems

### Issue-tracker survey

Twelve tickets on rejected input, precision, tolerance, boolean failure and non-determinism. Every
speaker's role is the `authorAssociation` the API reports: **OWNER** = `elalish`, **COLLABORATOR** =
`pca006132`, both maintainers; **CONTRIBUTOR** = has had a PR merged; **NONE** = outside reporter.

| # | Trigger | Traced cause, and by whom | State | Link |
|---|---|---|---|---|
| 1430 | coincident faces, axis-aligned and not | **Reporter's diagnosis, later endorsed.** `luisfonsivevo` (NONE) traced it to the perturbation using *vertex* normals, so both coincident verts perturb the same way. `pca006132` (COLLABORATOR) first, of the report: "we don't have a good way to fix it as of today" `elalish` (OWNER) then called the analysis sound and proposed a per-triangle variant | closed 2025-12 | [issue](https://github.com/elalish/manifold/issues/1430) |
| 1706 | near-coincident operands, 615 of 33,230 tris below 1e-9 area | **Maintainer, as designed.** `elalish` (OWNER): "slivers are very much expected to be produced by Smith's Boolean". The mechanism (`Kernel12` not coalescing near-duplicate verts) is the reporter's, `zmerlynn` (CONTRIBUTOR) | **open** 2026-05 | [issue](https://github.com/elalish/manifold/issues/1706) |
| 1714 | operands at very different scales | **Reporter only — no maintainer ever commented**, and `elalish` converted it to a discussion. `zmerlynn` (CONTRIBUTOR) traced a result `tolerance_` of 3.4e+26 on a ~50,000-unit output to `max(inP.tolerance_, inQ.tolerance_)`. We verified the line: [`boolean_result.cpp#L828-L836`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/boolean_result.cpp#L828-L836) does exactly that, and never re-derives from the output box | closed 2026-05 | [issue](https://github.com/elalish/manifold/issues/1714) |
| 1283 | v2.5.1 → v3: 0 → 968 degenerate tris | **Reporter's diagnosis.** `jonathanhogg` (CONTRIBUTOR) found ~1e-6 offsets from his own `sin`/`cos`; rounding coordinates to 19 fractional bits restored the old output. The maintainer sentence that matters for us is `elalish` (OWNER), on the input types: "you'll get float tolerance - only MeshGL64 gives double tolerance" | closed 2025-07 | [issue](https://github.com/elalish/manifold/issues/1283) |
| 676 | identical geometry at `0.0999*50` vs `0.0999*1` | **Maintainer, working as intended.** `elalish` (OWNER): "This is working as intended", because the coordinates are no longer bit-identical and perturbation cannot fire | closed 2023-12 | [issue](https://github.com/elalish/manifold/issues/676) |
| 1359 | union with several coplanar faces | **Maintainer, in-spec.** `pca006132` (COLLABORATOR): "Degenerate triangle is expected output", per the ε-valid definition | closed 2025-09 | [issue](https://github.com/elalish/manifold/issues/1359) |
| 1354 | union of a reversed-winding solid with a normal one | **Maintainer, out of scope.** `pca006132` (COLLABORATOR): "not a good idea to support negative volume meshes"; the underlying [#745](https://github.com/elalish/manifold/issues/745) is still open | closed 2025-09 | [issue](https://github.com/elalish/manifold/issues/1354) |
| 1177 | policy question raised from the Blender integration | **Maintainer, the definitive statement.** `pca006132` (COLLABORATOR): stable sorts, but with parallelism "we do have things that are racy and are not deterministic", and "It is pretty much impossible to get deterministic results across machines". `elalish` (OWNER) on restoring the removed flag: "I don't think we're bringing it back as an option" | closed 2025-03 | [issue](https://github.com/elalish/manifold/issues/1177) |
| 1233 | same input, different triangle order on arm64 vs x86-64 vs MSVC | **Maintainer.** `elalish` (OWNER): "the difference is circular reordering of some triangle indices"; `Trzeth` (CONTRIBUTOR) localised it to `GetMeshGLImpl`. Reported by `howardt` (CONTRIBUTOR), Blender's boolean author | closed 2025-04, fixed by PR #1234 | [issue](https://github.com/elalish/manifold/issues/1233) |
| 1320 | union of 19 mutually coplanar cubes, run to run | **Not traced in the ticket** — its only comment is `pca006132` (COLLABORATOR) saying he is away. Reported by `howardt` (CONTRIBUTOR) from a Blender bug report; PR #1321 "deterministic batch boolean" merged at the closing timestamp | closed 2025-08 | [issue](https://github.com/elalish/manifold/issues/1320) |
| 1348 | `MeshGL` with one vertex and no triangles → `NonFiniteVertex` | **Contributor.** `Trzeth` (CONTRIBUTOR): "A single point won't generate halfedges", and an empty halfedge set counts as manifold, so the code falls through to the wrong branch. Reported by `howardt` (CONTRIBUTOR); this is the upstream half of Blender's [#144698](https://projects.blender.org/blender/blender/issues/144698) | closed 2025-09, fixed by PR #1349 | [issue](https://github.com/elalish/manifold/issues/1348) |
| 1364 | watertight inputs, non-watertight output through trimesh | **Maintainer, and not a Manifold defect.** `pca006132` (COLLABORATOR) traced it to `trimesh.boolean` constructing `Trimesh(process=True)`, whose constructor "merges duplicated vertices and breaks manifoldness" | closed 2025-09 | [issue](https://github.com/elalish/manifold/issues/1364) |

### What the survey shows, and what it does not

Three things stand out, and one absence.

1. **`NotManifold` is rare on the tracker.** The dominant complaint is not "it refused my model" but
   "it accepted my model and gave me slivers, duplicate vertices or degenerate triangles" — which
   the maintainers classify as in-spec (1359, 1706, 1430). P-09 as written predicts the first
   failure. The tracker says the *second* is the common one in the field. Both are real; our own
   torture set produced the first, the field produces the second.
2. **Non-determinism is treated as a bug class, not an invariant.** It is fixed ticket by ticket
   (1233, 1320) and a global deterministic mode was deliberately not restored (1177). The one that
   reached us is Blender's [#143644](https://projects.blender.org/blender/blender/issues/143644),
   reproduced upstream by Blender's boolean author and fixed in the library — as
   [`blender.md`](blender.md) records.
3. **Not every ticket is a Manifold defect.** #1364 was traced to `trimesh`'s importer merging
   vertices, and #1283 to the reporter's own `sin`/`cos` arithmetic — two of twelve. Interchange and
   caller-side coordinate construction break manifoldness at least as often as the kernel does.

The absence: **no ticket in this survey reports a wrong volume from an accepted input.** Failures are
of quality (slivers), of contract (refusal), of tolerance bookkeeping, or of ordering. That is
consistent with everything we measured.

### The one we found ourselves

The T-junction. `near_degenerate_triangle` B is the reference set's cube whose top face is split by
a vertex lying *on* the edge v5→v6, so one halfedge has no twin. Manifold rejects it on **both**
input paths with `Error::NotManifold` and returns an **empty** Manifold; the union and the
intersection then propagate that status rather than returning anything
(measured, [`results/manifold.md`](../../../spikes/boolean-torture/results/manifold.md) Probe C).
The `Merge` helper the README offers for "slightly non-manifold meshes" reports that it changed the
mesh and the result is still `NotManifold` — merging coincident vertices does not weld a vertex to
the interior of an edge.

**Compare Blender.** Through Blender the same library, at v3.2.1, produced the warning "Cannot
execute, non-manifold inputs" **and the unmodified first operand**
([`blender.md`](blender.md) §The other two solvers). The library itself returns an empty result carrying a typed
status. The difference is entirely in the binding, and it is the single most important design point
in this note: *Manifold gets the refusal contract right, and its most prominent embedder throws that
away at the boundary.* Kernel spec §12 — every operation returns a result value, an invalid input is
reported, and healing is a separate call the caller makes — now has both a positive and a negative
example in one artefact.

## Measurements

- **Hardware:** Intel Core i9-14900HX, 32 GB RAM, Windows 11 Pro.
- **Versions:** `manifold3d` 3.5.3 (wheel, `MANIFOLD_PAR=ON`); source read at tag `v3.5.3`, commit
  `0edd9d54876f3135e431575214dd6d8a72866fee`. numpy 2.3.5 — imported only because the `manifold3d`
  wheel requires it for its typed-array constructors.
- **Benchmark:** `reference/boolean_torture_set.py` and `reference/precision_set.py`, verbatim.
- **Method:** fresh operands per setting and per repeat; validity checked by the driver on the
  *exported* triangles (closed, every directed edge used once with a matching opposite halfedge, no
  loose vertices, no triangle below 1e-14 m²) as well as by `status()` and `is_empty()`; volumes by
  `reference.signed_volume` over those triangles with `Manifold.volume()` recorded beside them;
  timing `time.perf_counter`, five repeats, median, with the `status()` call that forces the deferred
  CSG node inside the timed region.

### Boolean torture set (R-16)

| Setting | Valid (closed manifold) | Numerically correct | Worst identity residual |
|---|---|---|---|
| f64, default tolerance | 9 / 10 | 9 / 10 | 3.55e-14 |
| f64, tolerance = 1e-9 | 9 / 10 | 9 / 10 | 3.55e-14 |
| f64, tolerance = 1e-6 | **8 / 10** | 9 / 10 | 3.55e-14 |
| f32, default tolerance | 9 / 10 | 9 / 10 | 2.49e-14 |

R-16's pass line is *every* case valid with the identity within 1e-9 relative. **Manifold does not
pass, and the reason is the refusal, not an error.** On the nine cases it accepts it is numerically
correct at every setting, and topologically valid at every setting except the one where a raised
tolerance deleted an operand. Three details are worth carrying:

* **`tolerance = 1e-6` silently deletes the sliver.** The 1e-7 m slab becomes an empty Manifold with
  status `NoError`, and the intersection is empty where 1e-7 m³ was expected. The tolerance sweep
  (Probe B) puts the threshold between 1e-8 and 1e-7 on the f64 path and between 1e-7 and 1e-6 on
  the f32 path. A feature thinner than the tolerance disappears **without a distinguishable return
  value** — the one place where this library's own contract lapses.
* **The correctness threshold cannot see that deletion**, which is why the f64/1e-6 row still reads
  9/10 correct: an absolute floor of 1e-6 m³ cannot distinguish 0 from 1e-7 m³. The *validity*
  column catches it. This is why the two are counted separately.
* **`coplanar_faces`'s intersection is a non-empty zero-volume shell** of four triangles — closed,
  manifold, correctly wound, volume 0. Mathematically right; a caller that tests `is_empty()` to mean
  "no intersection" gets the wrong answer.

The twelve-shell cutting tool is a non-issue: Manifold accepts one mesh of twelve disconnected
closed shells as **one** `Manifold` and `decompose()` reports 12; union, intersection and difference
are all exact, with the difference at 3.6 m³ against the analytic 3.6 (Probe A).

Determinism: 10 runs of each of four case/operation pairs produced **1 signature each** (Probe D),
on a TBB-enabled build. That is the state at v3.5.3, after the fixes in #1233, #1320 and the one
Blender reported; it is not a guarantee the maintainers offer (#1177).

Cancellation: `ExecutionContext` cancels a deferred boolean tree and the result carries
`Error::Cancelled` with an empty mesh (Probe E). **This is the API `problems.md` P-15 found missing
in OCCT**, present and working in 23,598 lines.

### Precision set (R-17) — passes on f64, fails on f32

Worst vertex deviation over the whole set: **3.3e-11 m on `Mesh64`**, **0.0186 m on `Mesh`**. R-17's
pass line is 1e-6 m and its fail line 1e-4 m. The candidate therefore passes or fails on a choice
the *caller* makes at the boundary, not on anything in the algorithm — which is the cleanest
demonstration of ADR-0006's premise we have.

## Strengths

- **The only candidate so far whose boolean is never numerically wrong on a case it accepted.** Nine
  of ten cases exact on four settings, worst identity residual 3.55e-14. OCCT is 30/30 topologically
  valid but returned 0 where 1e-7 m³ was expected on the `sliver` intersection; Blender's exact solver
  silently deleted an operand on `touching_vertex`.
- **Refusal is a return value.** A typed `Error` enum with fifteen enumerators — `NoError` plus
  fourteen named failures — carried by an empty result and propagated through subsequent operations
  rather than lost.
- **A real double path.** `Mesh64`/`MeshGL64` end to end, and internal storage in `double`
  regardless.
- **Cancellation and progress that the boolean actually observes.** OCCT has the concept; a reporter
  measured that its face–face intersector does not poll it ([`occt.md`](occt.md) §Known problems,
  [#1385](https://github.com/Open-Cascade-SAS/OCCT/issues/1385)).
- **Apache-2.0 and dependency-free**, so borrowing *code* is legally and practically possible.
- **Small enough to read.** 23,598 lines with four design PDFs in the tree.
- **Fast**: 19× Blender's exact solver and 64× OCCT's single-threaded B-rep fuse on the twelve-opening
  wall — three different harnesses, so read the ratios as orders of magnitude, not as benchmarks.

## Weaknesses

- **One representation.** No B-rep, no point cloud, no stored implicit. Kernel spec §4's central bet
  is that a kernel must hold several; Manifold is a component of such a kernel, not the kernel.
- **No incremental evaluation of any kind.** Immutable values and a throwaway CSG tree.
- **Input must be a clean 2-manifold**, which real imported geometry frequently is not — and the
  supplied `Merge` repairs only coincident vertices, not T-junctions.
- **The tolerance is keyed to distance from the origin** by construction, on every path.
- **Tolerance propagates as `max` over the operands** and is never re-derived from the output box
  (#1714, verified in source).
- **Slivers and degenerate triangles are contract-conforming output**, so "the boolean succeeded"
  does not mean "the result is clean".
- **Determinism is a bug class, not an invariant** (#1177).
- **Bus factor 2.**
- **No GPU path**, by decision.

## Risks

- The refusal rate on *real* IFC-derived meshes is unmeasured. Our torture set contains one
  non-manifold operand and Manifold refused it; a building model contains thousands of T-junctions
  at wall/slab junctions. Adopting Manifold as the mesh boolean means owning a repair stage whose
  cost we have not measured. **This is the specific experiment that would settle "build on":** run
  Manifold over every solid in `reference/models/AC20-FZK-Haus.ifc` and count the refusals.
- Silent feature deletion at raised tolerance would be invisible in production. Any adoption must
  wrap `set_tolerance` in a check that the volume did not move.
- Determinism at v3.5.3 is measured, not promised; a library upgrade may reintroduce it, and there
  is no upstream test we could rely on.

## The twelve questions

1. **Re-evaluate one changed element without reprocessing the model?** No. Values are immutable and
   the CSG tree is per-expression. *(inferred from source.)*
2. **IFC round trip?** Not applicable; no schema layer.
3. **Driven in-process from DynLex?** Yes — a plain C ABI (`bindings/c`), no required dependencies,
   static linking by default. The best embeddability of any candidate so far. *(source.)*
4. **Threading model, and what is single-threaded by design?** TBB, chosen per call site by
   `autoPolicy(size)` against `kSeqThreshold = 1e4`; polygon triangulation is serial by design
   (README). *(source.)*
5. **What breaks first at scale?** **Unmeasured by us.** The library's own failure valve is
   `Error::ResultTooLarge`, raised when an intersection index set exceeds `INT_MAX`
   ([`boolean_result.cpp#L774-L782`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/boolean_result.cpp#L774-L782)).
   The one large-scale datum we have is second-hand and *memory*: Blender's
   [#158737](https://projects.blender.org/blender/blender/issues/158737) traced a 44× memory
   regression to a library-side async deallocation path, fixed in v3.5.2. That symbol is absent from
   v3.5.3's source (`grep free_async` over the tree returns nothing), consistent with the fix.
6. **Numeric precision, configurable?** `double` internally, always. Configurable at the boundary by
   mesh type (f32 vs f64) and at runtime by `set_tolerance`, floored at an epsilon derived from the
   bounding box. *(measured + source.)*
7. **Operate on a subset — one tile, one region?** Partly. `TrimByPlane`, `SplitByPlane` and
   `Decompose` carve a solid up, but there is no notion of a region of a larger model: the unit is
   the whole solid. *(source.)*
8. **Who maintains it, what if they stop?** Two people. Apache-2.0 and 23,598 readable lines make a
   fork survivable, and OpenSCAD, Blender, Godot and BRL-CAD all depend on it, so a fork would have
   company. *(source.)*
9. **Documented failure modes and their design cause?** §Known problems: twelve tickets, with the
   dominant class being ε-valid-but-ugly output that traces directly to the ε-valid contract, and the
   refusal class tracing to the manifoldness requirement. *(tracker + source.)*
10. **Representations held natively, and conversions?** One (triangle mesh); conversions outward to
    2D polygons and inward from an SDF. *(source.)*
11. **How does geometry reach the GPU?** It does not. The caller exports triangles and uploads them.
    *(source.)*
12. **What would we take, and what avoid?** §Verdict.

## Verdict

### Build on — **no, as a kernel; yes, as a candidate boolean component**

It cannot be the kernel: one representation, no incremental evaluation, no notion of a model. Kernel
spec §3–§4 asks for things this library deliberately does not do, and correctly does not do.

As *the mesh boolean inside* our kernel it is the strongest candidate measured, and the Apache-2.0
licence means the option is real. It is not taken here, for one reason that is a fact and one that
is a judgement. The fact: it refuses input our benchmark contains and buildings are full of, and the
repair cost is unmeasured (see §Risks for the experiment that would settle it). The judgement: a
boolean whose predicates are double-precision with symbolic tie-breaking is a different bet from
kernel spec §5's exact predicates, and adopting it would decide that bet by import rather than by
argument. **Recommendation: shortlist for M5's mesh path, behind the IFC refusal-rate measurement.**

### Borrow from — extensively, and *as code where it helps*

| What | Why | Where |
|---|---|---|
| **The typed `Error` enum, carried by an empty result and propagated through later operations** | Fifteen enumerators, fourteen of them named failures, instead of a bool. `Status()` on a chain still reports the failure that occurred in its middle. This is kernel spec §12's contract, already implemented | [`manifold.h#L124-L146`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/include/manifold/manifold.h#L124-L146). **P-09, P-01** |
| **`ExecutionContext`: cancel, cancelled, progress; permanent cancellation with `Error::Cancelled`** | The exact API P-15 found missing in OCCT, in a library 1/100th the size. Cancellation is checked between phases and inside parallel chunks | [`common.h#L250-L299`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/include/manifold/common.h#L250-L299), [`parallel.h#L396-L440`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/parallel.h#L396-L440). **P-15** |
| **The mass-property integrand: difference-then-cross, with Kahan compensation** | Measured: 12.5999999999 against a naive divergence sum's 12.5999143 on the same solid at 500 km. Cheap, and the difference is five orders of magnitude | [`properties.cpp#L265-L294`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/properties.cpp#L265-L294). **P-05** |
| **The LBVH collider: Morton codes, Karras radix tree, built and queried in parallel, with a sequential threshold** | The broad phase every boolean and every pick needs, in one header, with a written design document in the tree | [`collider.h`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/collider.h), [`docs/ParallelBVH.pdf`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/docs/ParallelBVH.pdf) |
| **`BatchBoolean` — an n-ary boolean with tree reordering, not a chain of pairwise calls** | A wall against twelve openings is one operation. Chaining twelve differences accumulates twelve tolerance maxima and twelve arrangements | [`csg_tree.cpp`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/csg_tree.cpp) |
| **A size-dependent execution policy (`autoPolicy`, `kSeqThreshold`) rather than a global parallel flag** | Directly answers the measured OCCT finding that a global parallel flag costs +8% when per-item work is small ([`occt.md`](occt.md) §Measurements). **Restates P-08** | [`parallel.h#L34-L60`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/parallel.h#L34-L60) |
| **Multi-component solids as one value, with `Decompose()` on demand** | Measured: twelve disconnected shells are one `Manifold`; the cutting tool needs no special case, and the OCCT driver's sew-into-a-compound step disappears | Probe A, [`results/manifold.md`](../../../spikes/boolean-torture/results/manifold.md) |
| **Symbolic perturbation on exact equality as the coplanar tie-break** | Three lines, and it wins every bit-identical-coordinate case on our set — *with* the maintainers' own caveat that it is best-effort and cannot survive arithmetic on the coordinates (#676, #1430) | [`shared.h#L90-L96`](https://github.com/elalish/manifold/blob/0edd9d54876f3135e431575214dd6d8a72866fee/src/shared.h#L90-L96) |

### Avoid — each one mapped to the design choice behind it

| Failure | Design choice it traces to | Our design's answer |
|---|---|---|
| **Real input is refused.** The T-junction operand → `NotManifold` + empty, both input paths; `Merge` does not repair it | The correctness proof assumes an oriented 2-manifold, and the ingest checks it before anything else (`impl.h#L471-L482`) | Validity is an explicit query and healing an explicit operation, not a precondition (spec §4, §12); the arrangement-based boolean tolerates non-manifold input where the literature allows. **P-09**, measured |
| **Tolerance keyed to `Box::Scale()` — the largest absolute coordinate** | Epsilon is derived from the bounding box so it scales with the model, which conflates *size* with *position*. At 500 km: 5e-7 m (f64), 0.0596 m (f32) | Tolerances are per-entity and explicit, and geometry lives in tile-local f64 frames so distance from a projection origin never enters a tolerance (spec §5, ADR-0006). **P-05**, measured |
| **float32 as the default mesh type.** `MeshGL`/`Mesh` is float32; `MeshGL64` exists but is not the default, and `elalish` (OWNER) confirms the consequence on #1283 | An interchange type designed for GPU upload doubles as the ingest type | f64 storage; f32 only in the camera-relative upload buffer (spec §5, ADR-0006). **P-05** |
| **Result tolerance is `max(inP, inQ)` and never re-derived from the output** | Tolerance is treated as an operand property carried forward, not a property of the result's own geometry | Tolerances grow but never shrink **and are reported per operation**, so a caller can see when a result's tolerance no longer matches its size (spec §5). **P-02**, source-verified, #1714 |
| **A raised tolerance deletes a thin feature and reports `NoError`** | `SetTolerance` above the current value runs `SimplifyTopology` as a side effect | A simplification that removes a shell is a *reported* fact with a changed result value, never a `NoError` (spec §12). **P-01/P-02**, measured |
| **Slivers and degenerate triangles are in-spec output** | The ε-valid contract promises manifoldness, not geometric cleanliness | Our contract states what the *geometry* guarantees, not only the topology; a result that needed cleanup says so (spec §4, §12) |
| **Determinism is a bug class, fixed case by case; a deterministic mode was removed and not restored (#1177)** | Parallel scheduling without a canonical merge order, with performance preferred | Determinism is an invariant with a test in the suite from the first boolean (spec §6). **P-16** |

### Corrections and additions this note makes to `problems.md`

- **P-09 → shown**, with the qualification the tracker forces: the refusal happens and we measured
  it, but the *field's* dominant complaint about this library is ε-valid-but-ugly output, not
  refusal. Both belong in the row.
- **P-09, on the refusal contract:** the standalone library returns an empty result carrying a typed
  status. Blender's message-plus-first-operand is the embedder's doing, not the library's. The
  design lesson `blender.md` drew survives, and gains a positive example.
- **P-05 → strengthened and generalised.** The float32 loss is now shown to be independent of
  Blender, and a second mechanism is added: a tolerance derived from the largest absolute coordinate
  degrades **even on the f64 path**. The local-frame mitigation is measured a second time and works.
- **P-03 gains a third data point.** "Exact boolean is correct but too slow" is a hypothesis about
  exact *arithmetic*. Manifold is neither: double predicates plus symbolic perturbation, correct on
  9/10 of our cases and 19× faster than Blender's exact solver. The row should say so — and say that
  the cases it wins are the ones built from bit-identical coordinates (#676).
- **P-15 gains its counter-example.** Cancellation and progress are not exotic; a 23.6k-line library
  ships them.
- **P-16 gains the upstream history**: the non-determinism `blender.md` traced downstream is one of
  several, fixed individually, with a global deterministic mode explicitly declined.

## Sources

- [Manifold](https://github.com/elalish/manifold), source read at tag `v3.5.3`, commit
  `0edd9d54876f3135e431575214dd6d8a72866fee`; package `manifold3d` 3.5.3 from PyPI, which is built
  from that tag with `MANIFOLD_PAR=ON`.
- [Manifold Library wiki](https://github.com/elalish/manifold/wiki/Manifold-Library) — the
  manifoldness and ε-valid definitions. Unpinnable; quoted as *claimed*.
- Issue tracker: [#676](https://github.com/elalish/manifold/issues/676),
  [#745](https://github.com/elalish/manifold/issues/745),
  [#1177](https://github.com/elalish/manifold/issues/1177),
  [#1233](https://github.com/elalish/manifold/issues/1233),
  [#1283](https://github.com/elalish/manifold/issues/1283),
  [#1320](https://github.com/elalish/manifold/issues/1320),
  [#1348](https://github.com/elalish/manifold/issues/1348),
  [#1354](https://github.com/elalish/manifold/issues/1354),
  [#1359](https://github.com/elalish/manifold/issues/1359),
  [#1364](https://github.com/elalish/manifold/issues/1364),
  [#1430](https://github.com/elalish/manifold/issues/1430),
  [#1706](https://github.com/elalish/manifold/issues/1706),
  [#1714](https://github.com/elalish/manifold/issues/1714).
  Speaker roles are the `authorAssociation` values returned by the GitHub issues API.
- [#524](https://github.com/elalish/manifold/issues/524) and PRs
  [#525](https://github.com/elalish/manifold/pull/525),
  [#531](https://github.com/elalish/manifold/pull/531) — the CUDA/OpenMP removal; the summary line
  "Removed OMP and CUDA backends to focus on TBB" is from the
  [v2.2.1 release notes](https://github.com/elalish/manifold/releases/tag/v2.2.1).
- Blender's bundled version: `MANIFOLD_VERSION v3.2.1` in
  `build_files/build_environment/cmake/versions.cmake` at Blender commit
  `a37564c4df7a9b604809e5192918400e46a0205f` (read via the GitHub mirror of the Blender repository
  at that commit; the canonical path is
  [projects.blender.org](https://projects.blender.org/blender/blender/src/commit/a37564c4df7a9b604809e5192918400e46a0205f/build_files/build_environment/cmake/versions.cmake)).
- Our measurements:
  [`spikes/boolean-torture/results/manifold.md`](../../../spikes/boolean-torture/results/manifold.md),
  [`spikes/precision-set/results/manifold.md`](../../../spikes/precision-set/results/manifold.md).
- Comparison numbers for the same benchmark:
  [`spikes/boolean-torture/results/blender.md`](../../../spikes/boolean-torture/results/blender.md),
  [`spikes/boolean-torture/results/occt.md`](../../../spikes/boolean-torture/results/occt.md),
  [`spikes/precision-set/results/blender.md`](../../../spikes/precision-set/results/blender.md),
  [`spikes/precision-set/results/occt.md`](../../../spikes/precision-set/results/occt.md).
