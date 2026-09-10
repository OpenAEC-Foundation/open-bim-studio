# OCCT — Open CASCADE Technology

**Decision question:** OCCT is the B-rep kernel under FreeCAD and IfcOpenShell, and — as
[`README.md`](README.md) puts it — "the richest source of documented boolean and tolerance
problems". Can we build the product's kernel on it — and if not,
which of its designs must our own kernel take, and which of its failure modes must it not repeat?

**Serves:** ADR-0004, ADR-0005, ADR-0006

**Status:** draft
**Author:** research programme, phase 2
**Last updated:** 2026-09-10

---

## Summary

OCCT is a mature, LGPL-with-linking-exception tolerant B-rep kernel whose boolean survived every
case of our torture set as a *valid* shape and got nine of ten *right* — but the tenth failed
silently, and the mechanism behind that silence is the design: topology is decided by comparing
distances against per-entity tolerances, so geometry below the tolerance disappears without an
error and `BRepCheck_Analyzer` still says the result is valid. It is not a candidate to build on,
for reasons that have nothing to do with boolean quality: it has no incremental evaluation, no
mesh or implicit representation to speak of, and it needs 4.4 s to tessellate 10k planar boxes.
It is the single most valuable candidate to *borrow* from, because its tolerance model, its
argument preconditions and its 38-category shape check are twenty years of accumulated knowledge
about what actually goes wrong.

## What it is

Open CASCADE Technology is a C++ modelling library, open-sourced in 1999 from Matra Datavision's
CAS.CADE. It is the geometry kernel under FreeCAD, IfcOpenShell's default kernel, KiCad's 3D
export, and a long tail of engineering software. It is maintained by Open Cascade SAS
commercially, with the open repository on GitHub; the project migrated its issue tracking from a
Mantis instance to GitHub Issues, and migrated tickets carry their legacy Mantis id.

Its data model is a *tolerant* boundary representation. A shape is a hierarchy of
vertices, edges, wires, faces, shells, solids (`TopoDS`), each topological entity referring to
geometry (`Geom`, `Geom2d`) and — this is the part that matters — each vertex, edge and face
carrying its **own tolerance value**. Two entities are "the same" if they are within the sum of
their tolerances. There is no exact predicate anywhere in the topology decisions; there is a
tolerance and a comparison.

OCCT holds one representation natively. `Poly_Triangulation` exists but is a *tessellation cached
on a face*, produced by `BRepMesh` from the B-rep and not a representation you can model in.
`BRepLib_PointCloudShape` samples points from a shape; `AIS_PointCloud` displays them. Neither is
a point-cloud representation with operations. There is no implicit / SDF representation at all.

**Maturity:** claimed by the project — LGPL 2.1 with an exception permitting object-code
distribution of header-derived material under terms of your choice, or a commercial licence
([`README.md`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/README.md),
[`OCCT_LGPL_EXCEPTION.txt`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/OCCT_LGPL_EXCEPTION.txt)).
Release cadence is roughly two minor releases a year; 7.9.x and 8.0.x both shipped within the
year before this note.

## What was read, and at which commit

Everything below is pinned to **tag `V8_0_1`, commit
[`b8f597c677811d1f9f4d8a97f5ae2825c0353a42`](https://github.com/Open-Cascade-SAS/OCCT/tree/b8f597c677811d1f9f4d8a97f5ae2825c0353a42)**
— the OCCT version bundled by the `cadquery-ocp` build that produced the measurements. Obtained
with `git clone --depth 1 --branch V8_0_1 https://github.com/Open-Cascade-SAS/OCCT`, hash
confirmed with `git rev-parse HEAD`.

Note that 8.0 reorganised the source tree: the packages the older documentation calls `src/BOPAlgo/`
and `src/BRepMesh/` now live under `src/ModelingAlgorithms/<toolkit>/<package>/`. The paths below
are the real paths at this commit.

| What | Path at the pinned commit |
|---|---|
| Boolean algorithm options (fuzzy, parallel, OBB, non-destructive) | [`src/ModelingAlgorithms/TKBO/BOPAlgo/BOPAlgo_Options.hxx`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingAlgorithms/TKBO/BOPAlgo/BOPAlgo_Options.hxx), [`.cxx`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingAlgorithms/TKBO/BOPAlgo/BOPAlgo_Options.cxx) |
| The rest of the boolean machinery (pave filler, builder, alerts) | [`src/ModelingAlgorithms/TKBO/BOPAlgo/`](https://github.com/Open-Cascade-SAS/OCCT/tree/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingAlgorithms/TKBO/BOPAlgo), [`BOPTools/`](https://github.com/Open-Cascade-SAS/OCCT/tree/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingAlgorithms/TKBO/BOPTools), [`IntTools/`](https://github.com/Open-Cascade-SAS/OCCT/tree/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingAlgorithms/TKBO/IntTools) |
| Public boolean API | [`src/ModelingAlgorithms/TKBO/BRepAlgoAPI/`](https://github.com/Open-Cascade-SAS/OCCT/tree/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingAlgorithms/TKBO/BRepAlgoAPI) |
| Validity checking | [`src/ModelingAlgorithms/TKTopAlgo/BRepCheck/`](https://github.com/Open-Cascade-SAS/OCCT/tree/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingAlgorithms/TKTopAlgo/BRepCheck) |
| Healing | [`src/ModelingAlgorithms/TKShHealing/ShapeFix/`](https://github.com/Open-Cascade-SAS/OCCT/tree/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingAlgorithms/TKShHealing/ShapeFix) |
| Per-entity tolerance access and storage | [`src/ModelingData/TKBRep/BRep/BRep_Tool.hxx`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingData/TKBRep/BRep/BRep_Tool.hxx), [`BRep_TVertex.lxx`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingData/TKBRep/BRep/BRep_TVertex.lxx) |
| Tolerance constants | [`src/FoundationClasses/TKernel/Precision/Precision.hxx`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/FoundationClasses/TKernel/Precision/Precision.hxx) |
| Tessellation and its parameters | [`src/ModelingAlgorithms/TKMesh/BRepMesh/`](https://github.com/Open-Cascade-SAS/OCCT/tree/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingAlgorithms/TKMesh/BRepMesh), [`IMeshTools/IMeshTools_Parameters.hxx`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingAlgorithms/TKMesh/IMeshTools/IMeshTools_Parameters.hxx) |
| Surface–surface intersection | [`src/ModelingAlgorithms/TKGeomAlgo/IntPatch/`](https://github.com/Open-Cascade-SAS/OCCT/tree/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingAlgorithms/TKGeomAlgo/IntPatch) (92 files), [`GeomInt/`](https://github.com/Open-Cascade-SAS/OCCT/tree/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingAlgorithms/TKGeomAlgo/GeomInt) (61 files) |
| Per-operation history | [`src/ModelingData/TKBRep/BRepTools/BRepTools_History.hxx`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingData/TKBRep/BRepTools/BRepTools_History.hxx) |
| Boolean Operations specification (3562 lines) | [`dox/specification/boolean_operations/boolean_operations.md`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/dox/specification/boolean_operations/boolean_operations.md) |
| Shape Healing user guide | [`dox/user_guides/shape_healing/shape_healing.md`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/dox/user_guides/shape_healing/shape_healing.md) |

## Evaluation

Scored against every criterion in [`README.md`](README.md).

| Criterion | Finding | Evidence type | Source / method |
|---|---|---|---|
| **License** | LGPL 2.1 plus an OCCT-specific exception allowing object-code distribution of header-derived material under terms of your choice; commercial licence available as an alternative. Permits linking and shipping; **borrowing source into a differently-licensed kernel is not permitted** — designs and algorithms may be reimplemented, code may not be copied (R-11). | claimed | [`README.md`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/README.md#L5-L11), [`OCCT_LGPL_EXCEPTION.txt`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/OCCT_LGPL_EXCEPTION.txt) |
| **Representations held natively** | **One.** B-rep (`TopoDS` + `Geom`). `Poly_Triangulation` is a tessellation cached on a face, produced by `BRepMesh` and not modellable. `BRepLib_PointCloudShape` samples points *from* a shape; `AIS_PointCloud` is a display object. No implicit / SDF representation exists. Conversions are therefore one-directional: B-rep → mesh (`BRepMesh`), B-rep → points (`BRepLib_PointCloudShape`). Mesh → B-rep exists only as `BRepBuilderAPI_Sewing` over per-triangle faces, which is what our drivers use and which produces one face per triangle. | inferred from the source tree at the pinned commit | package listing above; [`Poly_Triangulation.hxx`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/FoundationClasses/TKMath/Poly/Poly_Triangulation.hxx) |
| **Boolean robustness** | 30 of 30 case×setting combinations produced results `BRepCheck_Analyzer` calls valid, and 9 of 10 cases were numerically exact (identity residual ≤1.4e-14 absolute). The tenth — `sliver`, a 1e-7 m slab — returned an **empty intersection with no error**. Against R-16's threshold: 9 cases pass (identity ≤8e-16 relative), `sliver` is between the pass line (1e-9 relative) and the fail line (1e-6 relative) at 3.3e-8 relative. Algorithm class: **tolerant, not exact** — see §Tolerance model. | measured | [`spikes/boolean-torture/results/occt.md`](../../../spikes/boolean-torture/results/occt.md) |
| **Tolerance and precision model** | f64 throughout. Per-entity tolerances stored on vertex, edge and face; grown by `UpdateTolerance` (monotone) but settable downward by `Tolerance(T)`. Three global constants (`Confusion` 1e-7, `Angular` 1e-12, `Intersection` 1e-9) are `constexpr` and act as hard floors that no API can go below. Not float32 anywhere in the modelling path. See §Tolerance model. | measured + source | §Tolerance model below |
| **Incremental evaluation** | **Absent.** There is no evaluation graph, no dependency tracking and no parametric model in the kernel; `TopoDS_Shape` is a value with no history. `BRepTools_History` records generated / modified / removed relations for **one operation's** inputs and outputs only. Rebuilding a changed element means re-running the operations that produced it, which the caller must have recorded itself. This is what FreeCAD builds on top and where its topological-naming problem lives (R-13). | inferred from source; no evidence of the contrary found | [`BRepTools_History.hxx`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingData/TKBRep/BRepTools/BRepTools_History.hxx#L27-L41) |
| **Threading model** | Opt-in and per-operation. `BOPAlgo_Options::SetRunParallel(bool)` defaults to **false**; there is also a process-global `SetParallelMode`. `BRepMesh_IncrementalMesh` takes an `isInParallel` flag, also default false. The default thread pool reports 32 threads on the test machine. Measured: the mesh parallel flag gives **9.8×** on curved faces and **−8%** (i.e. slower) on 10k planar boxes. No documentation statement bounding BOP's thread safety was found. | measured + source | [`BOPAlgo_Options.hxx#L104-L118`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingAlgorithms/TKBO/BOPAlgo/BOPAlgo_Options.hxx#L104-L118); [`spikes/tessellation/results/occt.md`](../../../spikes/tessellation/results/occt.md) |
| **GPU path** | Out of scope for this note beyond the kernel seam: geometry reaches the GPU only after `BRepMesh` has produced a `Poly_Triangulation` per face, so the tessellation cost below *is* the GPU-upload cost. OCCT's own visualisation layer (`TKV3d`, `TKOpenGl`) is evaluated in [`../renderers/`](../renderers/). Nothing comes back from the GPU into the kernel. | inferred | package structure; §Measurements |
| **IFC coverage** | None natively. IFC reaches OCCT through IfcOpenShell, evaluated separately. OCCT's own exchange formats are STEP, IGES, glTF, OBJ, STL (`src/DataExchange/`). | inferred | source tree |
| **Performance** | 10k planar boxes: 4.2–4.7 s to tessellate (120,000 triangles, ~37 µs/triangle), ~250 ms to construct. Wall with 12 openings: 52 ms union, 49 ms intersection. Simple two-box boolean: 0.6–4.6 ms. 100k / 1M not run — the 10k number already answers the question this note needed. | measured | [`spikes/tessellation/results/occt.md`](../../../spikes/tessellation/results/occt.md), [`spikes/boolean-torture/results/occt.md`](../../../spikes/boolean-torture/results/occt.md) |
| **Embeddability** | C++ library; Python bindings (`OCP`/`cadquery-ocp`, `pythonocc`) are mature enough that this whole note's measurements ran through them. In-process use from DynLex would require a C ABI shim over a large C++ template-and-handle API — no C API exists. WASM builds exist in the wild but were not evaluated here. | inferred; the Python path is measured (it ran) | this note's drivers |
| **2D derivation** | Present and substantial: `HLRBRep` / `HLRAlgo` for hidden-line removal, section via `BRepAlgoAPI_Section`. Not measured. Unknown whether the quality is drawing-grade. | claimed (package exists) | source tree |
| **Maturity** | 26 years open-source, commercial maintainer, ~2 releases/year. Issue-tracker health is the concern: of ~20 boolean/tolerance issues surveyed, 13 are open, 3 closed with a merged fix and a stated cause, 1 closed as not-reproducible-on-latest with the reporter disputing it, 1 closed within 8 minutes with no comment. Several open tickets carry maintainer replies of the form "not planned for closest releases" or "not yet analyzed". | measured (survey; see §Known problems) | §Known problems |
| **AI familiarity** | High — 26 years of public code, a 3562-line boolean specification, and heavy downstream use. Recorded as one column and not used as a tiebreaker (R-09). | inferred | — |

## Tolerance model

This is the section ADR-0006 cites, so it states the mechanism rather than summarising it.

### The constants

Three `constexpr` values in
[`Precision.hxx`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/FoundationClasses/TKernel/Precision/Precision.hxx)
underpin everything:

| Constant | Value | Line | Meaning |
|---|---|---|---|
| `Precision::Confusion()` | `1.e-7` | [L165](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/FoundationClasses/TKernel/Precision/Precision.hxx#L165) | two points are the same point |
| `Precision::Angular()` | `1.e-12` | [L123](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/FoundationClasses/TKernel/Precision/Precision.hxx#L123) | two directions are parallel |
| `Precision::Intersection()` | `Confusion() * 0.01` = 1e-9 | [L220](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/FoundationClasses/TKernel/Precision/Precision.hxx#L220) | intersection computations |

They are dimensional: 1e-7 **metres** if the model is in metres, 1e-7 mm if in millimetres. OCCT
has no unit system, so the same constant means a different physical distance in a millimetre
model than in a metre model — a 1000× difference in effective precision decided by nothing more
than the units the file happened to use.

**They are floors, not defaults.** Measured: every API that accepts a tolerance clamps upward to
`Confusion()`.

- `BOPAlgo_Options::SetFuzzyValue` is literally `myFuzzyValue = std::max(theFuzz, Precision::Confusion())`
  ([`BOPAlgo_Options.cxx#L105-L108`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingAlgorithms/TKBO/BOPAlgo/BOPAlgo_Options.cxx#L105-L108)),
  and the default fuzzy value is `Confusion()` itself ([L53](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingAlgorithms/TKBO/BOPAlgo/BOPAlgo_Options.cxx#L53)).
- `BRepBuilderAPI_Sewing::Init` does the same: `myTolerance = std::max(tolerance, Precision::Confusion())`
  ([`BRepBuilderAPI_Sewing.cxx#L2105-L2122`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingAlgorithms/TKTopAlgo/BRepBuilderAPI/BRepBuilderAPI_Sewing.cxx#L2105-L2122)).
  **Measured:** asking for a sewing tolerance of 1e-8, 1e-9 or 1e-12 produced byte-identical
  results to 1e-7.
- `BRepPrim_GWedge::IsDegeneratedShape()` rejects any box extent `<= Precision::Confusion()`
  ([L1134-L1138](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingAlgorithms/TKPrim/BRepPrim/BRepPrim_GWedge.cxx#L1134-L1138)).
  **Measured:** `BRepPrimAPI_MakeBox(p, 1, 1, 1e-7)` throws `Standard_DomainError`; at `1.0001e-7`
  it succeeds. OCCT cannot represent a solid thinner than 0.1 µm, at any setting.

The answer to question 6 ("what precision does it use internally, and can it be configured?") is
therefore: f64 storage, and **no** — precision is a compile-time constant of the library, tunable
only upward per operation.

### Per-entity tolerance, and how it grows

Each `TopoDS` entity stores its own tolerance. Read with
[`BRep_Tool::Tolerance`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingData/TKBRep/BRep/BRep_Tool.hxx#L87)
for faces, [L256](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingData/TKBRep/BRep/BRep_Tool.hxx#L256)
edges, [L345](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingData/TKBRep/BRep/BRep_Tool.hxx#L345)
vertices, with a whole-shape [`MaxTolerance`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingData/TKBRep/BRep/BRep_Tool.hxx#L379).
The storage is a single double per entity, and growth is monotone:

```cpp
inline void BRep_TVertex::UpdateTolerance(const double T)
{
  if (T > myTolerance)
    myTolerance = T;
}
```

— [`BRep_TVertex.lxx#L33-L37`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingData/TKBRep/BRep/BRep_TVertex.lxx#L33-L37).
Note that the neighbouring plain setter `Tolerance(T)`
([L26-L29](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingData/TKBRep/BRep/BRep_TVertex.lxx#L26-L29))
*can* shrink it, and healing uses it. So "grows but never shrinks" is the convention of the
update path, not an invariant of the data structure.

The boolean specification defines tolerance growth as the *mechanism by which interferences are
resolved*, not as a side effect. For a vertex/vertex interference the result is a new vertex whose
point and tolerance are "the center and the radius of the sphere enclosing the tolerance spheres of
the source vertices"
([boolean_operations.md#L163-L165](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/dox/specification/boolean_operations/boolean_operations.md#L163-L165)).
For a vertex/edge interference, `Tol(Vi) = Max(Tol(Vi), D + Tol(Ej))`
([L173](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/dox/specification/boolean_operations/boolean_operations.md#L173));
for vertex/face, the same with `Tol(Fj)`
([L183](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/dox/specification/boolean_operations/boolean_operations.md#L183)).
Edge/edge and face/face produce new vertices by the same enclosing-sphere rule
([L205-L207](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/dox/specification/boolean_operations/boolean_operations.md#L205-L207),
[L247](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/dox/specification/boolean_operations/boolean_operations.md#L247)).

Growth is applied to the **inputs**, not only the outputs. `SetNonDestructive` is off by default,
and the user guide says enabling it "prevents the input arguments from any modification such as
tolerance increase, addition of the P-Curves on edges"
([L2811](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/dox/specification/boolean_operations/boolean_operations.md#L2811))
— which states the default behaviour by describing what turning it off prevents.

**Measured** ([Probe B](../../../spikes/boolean-torture/results/occt.md)): on the `sliver` case
with `SetFuzzyValue(1e-3)`, the largest tolerance on the **input** shapes rose from 1.525e-7 to
**5.001e-4** after a single `BRepAlgoAPI_Fuse`. The operands were mutated in place by an operation
that returned a new shape. On the clean `overlap_half` case, nothing grew at any fuzzy value —
growth happens only where an interference actually had to be resolved, which is worth stating
because it means the failure mode is data-dependent and will not show up in a smoke test.

**Measured** ([Probe A](../../../spikes/boolean-torture/results/occt.md)): chaining eight fuzzy
fuses of boxes separated by 5e-6 gaps raised the maximum entity tolerance once, to 5.1e-6
(≈ fuzzy/2 + `Confusion`), and then it **plateaued** — it did not compound over the chain. This
partially contradicts the hypothesis in `problems.md` P-02 as originally written: tolerance is
inherited, but in this scenario it is not cumulative. What *is* cumulative is the metric error:
the excess volume grew linearly, 3.33e-6 m³ per step, to 2.67e-5 m³ after eight steps, because
each gap the tolerance bridged was counted as solid. **A boolean that "works" here returns a solid
that is measurably bigger than the sum of its inputs, with no warning.**

### Healing works by raising tolerance too

`ShapeFix_Shape` takes a basic precision, a minimum and a **maximum allowed tolerance**, and the
guide is explicit that "the maximum tolerance value limits the increasing tolerance for fixing a
problem such as fix of not connected and self-intersected wires. If a value larger than the maximum
allowed tolerance is necessary for correcting a detected problem the problem can not be fixed"
([shape_healing.md#L132-L144](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/dox/user_guides/shape_healing/shape_healing.md#L132-L144)).
Healing in a tolerant B-rep is: widen tolerances until the contradiction disappears. That is a
coherent design, and it is why tolerance in a long-lived model only goes one way.

## Known problems

This section supplies the evidence for [`problems.md`](problems.md) P-01, P-02, P-08, P-11 and P-12.

### The documentation is itself a failure catalogue

Unusually and to OCCT's credit, the boolean specification has a chapter called **Algorithm
Limitations**
([§10, L2443](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/dox/specification/boolean_operations/boolean_operations.md#L2443))
that names the trigger classes directly: "self-interfered arguments, inappropriate or ungrounded
values of the argument tolerances, adverse mutual position of the arguments, tangency". The
statements that matter for our design:

1. **Validity is necessary but not sufficient.** "The fact that the argument is a valid shape (in
   terms of *BRepCheck_Analyzer*) is a necessary but insufficient requirement to produce a valid
   result of the Algorithms"
   ([L2477](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/dox/specification/boolean_operations/boolean_operations.md#L2477)).
   The guide then gives worked examples of shapes that pass `BRepCheck_Analyzer` and still cannot
   be boolean arguments: a self-interfered revolution face, an edge whose two vertices interfere
   because their tolerances are 0.5 and they are 0.698 apart, a solid with a vertex of tolerance
   50 ([L2481-L2548](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/dox/specification/boolean_operations/boolean_operations.md#L2481-L2548)).
   It even explains why the checker is unreliable: it samples 23 points along an edge, so splitting
   a valid edge can produce an invalid one, "thus the Analyzer gives a wrong result".
2. **Acquired self-interference is declared out of scope, not a bug.** "The cases when a
   non-self-interfered argument (or its sub-shapes) become interfered due to the intersections with
   other arguments (or their sub-shapes) are considered as limitations for the Algorithms"
   ([L2659](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/dox/specification/boolean_operations/boolean_operations.md#L2659)).
   This is the `BOPAlgo_AlertAcquiredSelfIntersection` that appears in issue #1173 below.
3. **Micro-fragmentation is specified behaviour.** Two nearly-coincident edges with `Tol=1e-7` and
   a maximum deflection of 1e-6 produce three new vertices and eight new edges rather than a common
   block, and the guide says "This is correct due to the source data"
   ([L2611-L2627](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/dox/specification/boolean_operations/boolean_operations.md#L2611-L2629)).
4. **Parametrisation is a scale limit.** Past roughly a 1e6 scale factor, p-curve angles on
   cylinders and cones become indistinguishable in double precision and "can cause failure of some
   BP sub-algorithms, such as building faces from a set of edges or building solids from a set of
   faces"
   ([L2529-L2556](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/dox/specification/boolean_operations/boolean_operations.md#L2526-L2556)).
5. **The preconditions are strict.** Arguments must be valid, non-self-interfered, and have
   geometry of continuity not less than C1
   ([L409-L426](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/dox/specification/boolean_operations/boolean_operations.md#L409-L426)).

### Issue-tracker survey

Twenty reports collected from OCCT's own GitHub tracker (primary) and downstream projects
(secondary), classified by trigger and by how far the cause was actually traced. **Distinguish
carefully:** most OCCT tickets carry a reporter's diagnosis, not a maintainer's. Only the three
marked *fixed* have a merged PR naming the cause.

| # | Trigger | Traced cause | State | Link |
|---|---|---|---|---|
| 1288 | self-intersection | **Fixed.** `Geom_BSplineCurve::PeriodicNormalization()` rewritten to O(1) and "protected against rounding error for large numbers" (PR #1329) | closed 2026-07 | [issue](https://github.com/Open-Cascade-SAS/OCCT/issues/1288) |
| 783 | degenerate | **Fixed.** Null `Geom2d_Curve` dereferenced in `BOPAlgo_PaveFiller::FillPaves` via `ProcessDE`; PR #860 skips edges without geometry | closed 2025-11 | [issue](https://github.com/Open-Cascade-SAS/OCCT/issues/783) |
| 544 | other (periodic p-curve origin) | **Fixed.** `RelocatePCurvesToNewUorigin()` could loop forever on an edge absent from the map; PR #557, regression test `bug_gh544` | closed 2025-05 | [issue](https://github.com/Open-Cascade-SAS/OCCT/issues/544) |
| 800 | coplanar + tolerance | Reporter localised a >10 GB spike to `BOPAlgo_PaveFiller::MakeBlocks` on operands sharing coplanar faces; **maintainer confirmed** "bug related to precision and splitting… multiple reports related to that peace of code", no fast solution | closed 2025-11 | [issue](https://github.com/Open-Cascade-SAS/OCCT/issues/800) |
| 1456 | tolerance-growth + coplanar | Reporter traces a SIGSEGV to an unchecked `BRep_Tool::CurveOnSurface` null return in `BOPTools_AlgoTools3D::DoSplitSEAMOnFace`, reached from `BuildSplitFaces`; trigger is two congruent solids where **one operand carries a loosened (~1e-3) tolerance "as is common after a round trip through an exchange format"**. Maintainer response: acknowledgement only | open 2026-08 | [issue](https://github.com/Open-Cascade-SAS/OCCT/issues/1456) |
| 1193 | coplanar | Reporter: `ShapeUpgrade_UnifySameDomain` merges faces across a wedge–wedge boundary and **introduces** self-intersections into a shape that passed `bopargcheck` after the fuse; count scales with wedge count. Closed as not reproducible on the current IR; reporter disputes | closed 2026-04 | [issue](https://github.com/Open-Cascade-SAS/OCCT/issues/1193) |
| 1173 | self-intersection (acquired) | `BOPAlgo_AlertAcquiredSelfIntersection` emitted twice; section returns 14 edges and 0 faces. Maintainer: "That issue is not yet analyzed" | open 2026-03 | [issue](https://github.com/Open-Cascade-SAS/OCCT/issues/1173) |
| 1385 | self-intersection + tangent | Reporter's stack sampling puts ~80% of runtime in `NCollection_BaseSequence::Find` from `Intf_TangentZone::GetPoint`, and finds no `UserBreak()` polling inside `IntTools_FaceFace::Perform`, so a 30 s deadline could not fire against 619 s of CPU. No maintainer response | open 2026-07 | [issue](https://github.com/Open-Cascade-SAS/OCCT/issues/1385) |
| 1360 | curved-intersection | Traced in the report: `IntTools_SurfaceRangeLocalizeData::SetFrame` returns early leaving indices at 0, so `GetUParamInFrame(1)` reads unallocated memory from `IntTools_BeanFaceIntersector::BuildBox`. **The crash occurs inside fuzzy mode.** Labelled "Not validated" | open 2026-07 (migrated Mantis 33090) | [issue](https://github.com/Open-Cascade-SAS/OCCT/issues/1360) |
| 1496 | tangent | `BRepAlgoAPI_Common` returns empty or negative for two geometrically identical swept solids while `IsDone()` is true; fails when the operands are independently constructed, succeeds when they are the same in-memory shape. Closed 8 minutes after opening, no comment | closed 2026-08 | [issue](https://github.com/Open-Cascade-SAS/OCCT/issues/1496) |
| 724 | curved-intersection | >10 GB for a boolean between two faces; reporter localises to face–face intersection and reports it worse than 7.6.x. Maintainer acknowledged only | open 2025-09 | [issue](https://github.com/Open-Cascade-SAS/OCCT/issues/724) |
| 344 | curved-intersection | 0.035 mm discontinuity in a section on a 100 mm bounding box; a commenter attributes it to a missing short intersection curve. **`ShapeFix` reported as producing wrong results on this input** | open 2025-02 | [issue](https://github.com/Open-Cascade-SAS/OCCT/issues/344) |
| 485 | curved-intersection | `BRepAlgoAPI_Common` returns an empty compound for two visually intersecting faces. Not traced. Maintainer: "not planned for closest releases" | open 2025-04 | [issue](https://github.com/Open-Cascade-SAS/OCCT/issues/485) |
| 245 | coplanar (shared edge) | Cut misbehaves when argument and tool share an edge; a third-party commenter blames revolution×sphere intersection at singular points. Workaround: rotate or offset to remove the shared edge | open 2025-01 | [issue](https://github.com/Open-Cascade-SAS/OCCT/issues/245) |
| 1041 | coplanar / tangent | Fuse of N rotated copies meeting on shared faces collapses surface area; reporter contributed failing unit tests. Not traced | open 2026-02 | [issue](https://github.com/Open-Cascade-SAS/OCCT/issues/1041) |
| 1124 | other (API path) | The same input gives wrong sections through `BRepAlgoAPI` and correct ones through `bopsection`. Not traced | open 2026-02 | [issue](https://github.com/Open-Cascade-SAS/OCCT/issues/1124) |
| 1534 | other (periodic parametrisation) | Reporter measures adjacent p-curves on a periodic root face differing by exactly 9×2π in U while the 3D vertices coincide; self-declared novice diagnosis, no maintainer comment. Moving the cutter by 0.0005 mm fixes it | open 2026-09 | [issue](https://github.com/Open-Cascade-SAS/OCCT/issues/1534) |
| 303 | curved-intersection | Double-cone draft face × cylinder: intersection is multiple mostly-disconnected curves and "the portion that we want is often not found" | open 2025-01 (Mantis 32857) | [issue](https://github.com/Open-Cascade-SAS/OCCT/issues/303) |
| 275 | curved-intersection | Surface intersection produces a strange result. Not traced | open 2025-01 | [issue](https://github.com/Open-Cascade-SAS/OCCT/issues/275) |
| 905 | other | `BOPAlgo_MakerVolume` returns 1 solid with artefact edges instead of 2. Not traced | open 2025-12 | [issue](https://github.com/Open-Cascade-SAS/OCCT/issues/905) |

Secondary, from downstream consumers — useful because they show what the failures look like on
**building** geometry rather than on mechanical parts:

| Project | Trigger | What it shows | Link |
|---|---|---|---|
| IfcOpenShell #7815 | tangent / degenerate | `BRepAlgoAPI_Cut` reports `IsDone` on a complete no-op — a void does not void — and the no-op passes every post-boolean validity check, so no retry fires. Reported that raising fuzziness **up to 1 cm** does not recover it; the CGAL kernel cuts correctly. Diagnosis is by a non-maintainer contributor: treat as claimed | [issue](https://github.com/IfcOpenShell/IfcOpenShell/issues/7815) |
| IfcOpenShell #6867 | coplanar | Mitred walls with half-space cuts: a coincident duplicate face lands on two topologically distinct edges at the same location, defeating the manifoldness check. Non-maintainer diagnosis: claimed | [issue](https://github.com/IfcOpenShell/IfcOpenShell/issues/6867) |
| IfcOpenShell #821 | policy | When an OCCT boolean cannot complete, IfcOpenShell substitutes the **unclipped first operand** and logs it. A wall with no opening, silently | [issue](https://github.com/IfcOpenShell/IfcOpenShell/issues/821) |
| IfcOpenShell #992 | coplanar | **Control case.** Maintainer states the failure "is actually fully caused by IfcOpenShell. There are boolean operands that share an edge" — not every downstream boolean failure is OCCT's | [issue](https://github.com/IfcOpenShell/IfcOpenShell/issues/992) |
| FreeCAD #25169 | curved-intersection | `Part: Boolean Common` empty result on two spline extrusions; labelled `3rd party: OCC` and `Confirmed` by FreeCAD. Extending one extrusion to full overlap makes it succeed | [issue](https://github.com/FreeCAD/FreeCAD/issues/25169) |
| FreeCAD #24115 | curved-intersection | `part.section` returns incomplete and wrong results roughly 1 in 100 attempts; labelled `3rd party: OCC` | [issue](https://github.com/FreeCAD/FreeCAD/issues/24115) |

### What the survey does *not* show

Three honest negatives, because they change how the "borrow" list is written:

- **No OCCT issue was found in which `SetFuzzyValue` rescued a failing boolean.** Only two or three
  fuzzy-related tickets exist on the whole tracker, and the substantial one (#1360) is a crash
  *inside* fuzzy mode. The strongest real-world evidence for fuzzy as a strategy is downstream:
  IfcOpenShell's [`boolean_utils.cpp`](https://github.com/IfcOpenShell/IfcOpenShell/blob/master/src/ifcgeom/kernels/opencascade/boolean_utils.cpp)
  starts at `precision/100` and retries at ×10 per attempt up to `precision*10000`, a four-decade
  sweep — and #7815 is a case where the whole ladder still fails.
- **No boolean thread-safety defect was found.** A search for `RunParallel` on the tracker returns
  zero issues. The one concurrency investigation (#1179) turned out to be a missing null guard in
  `ShapeUpgrade_FaceDivide::Perform()`, fixed in PR #1203, not a threading bug. The absence is the
  finding; nothing was substituted for it.
- **The legacy Mantis tracker is gone.** `tracker.dev.opencascade.org` does not resolve, and the
  `Mantis-Archive` GitHub Pages URLs that OCCT's own migrated issues link to return 404. Anything
  older than the GitHub migration is only reachable through the migrated tickets. That is a
  traceability warning for anyone who wants to re-derive this section later.
- **The trigger distribution above must not be read as a frequency distribution.** Searching for
  "coplanar" returns 3 tickets and "tangent" returns 5, yet several of the coplanar-triggered
  reports above (#800, #245, #1041, #1456) never use the word. The catalogue is a sample of
  failure *mechanisms*, not a measurement of their incidence.

### The one we found ourselves

`sliver` — a 1 m × 1 m × 1e-7 m slab inside a unit cube — is the clearest single demonstration of
the design's failure mode, and it needed no issue tracker:

1. The slab **cannot be constructed** by `BRepPrimAPI_MakeBox` at all (`Standard_DomainError`,
   because 1e-7 ≤ `Confusion()`), and when sewn from triangles it comes out with volume 3.33e-8
   instead of 1e-7 — a factor of 3 — while `BRepCheck_Analyzer` calls it **valid** and its own
   entity tolerance (1.525e-7) already exceeds its thickness.
2. `BRepAlgoAPI_Common` between the cube and the slab returns an **empty result**, at every fuzzy
   setting tried. `IsDone()` is true. No error, no warning, no alert.
3. The union is correct (the slab is inside the cube), so the volume identity residual — 3.33e-8 —
   is the only externally visible sign that anything was lost.

This is P-01 and P-02 in one case: a tolerance-based topology decision discarded geometry, and the
kernel's own validity check could not see it, because a tolerance-based validity check cannot
detect the loss of something smaller than the tolerance.

## Measurements

**Hardware:** Intel Core i9-14900HX (32 threads), 32 GB RAM, Windows 11 Pro 10.0.26200.
**Versions:** Python 3.12.10; `cadquery-ocp` 8.0.1.0.0, which bundles **OCCT 8.0.1** (the same
release as source tag `V8_0_1`, commit `b8f597c6`). Installed with
`pip install cadquery-ocp==8.0.1.0.0`. `Precision::Confusion` = 1e-7, `Angular` = 1e-12,
`Intersection` = 1e-9, confirmed at runtime.
**Benchmark models:** [`reference/boolean_torture_set.py`](../../../reference/boolean_torture_set.py)
(10 cases), [`reference/precision_set.py`](../../../reference/precision_set.py) (3 cases),
and the 10k synthetic scale model from
[`reference/generate_scale_models.py`](../../../reference/generate_scale_models.py).

**Method.** Three drivers, all committed:
[`spikes/boolean-torture/occt_driver.py`](../../../spikes/boolean-torture/occt_driver.py),
[`spikes/precision-set/occt_driver.py`](../../../spikes/precision-set/occt_driver.py),
[`spikes/tessellation/occt_driver.py`](../../../spikes/tessellation/occt_driver.py). Raw output is
in each spike's `results/occt.md`; those files are the reproducible record, this section is the
summary.

The construction method is part of the measurement and is stated here because it affects the
numbers: each benchmark triangle becomes a planar face
(`BRepBuilderAPI_MakePolygon` closed → `BRepBuilderAPI_MakeFace`), the faces are sewn
(`BRepBuilderAPI_Sewing` at `Precision::Confusion()`), and each resulting shell becomes a solid
(`BRepBuilderAPI_MakeSolid` + `BRepLib::OrientClosedSolid`). Where sewing yields several disjoint
shells — the `wall_with_openings` tool is twelve separate opening boxes — the operand is a
**compound of twelve solids**, not one solid with twelve shells: the latter is what a naive
translation produces and `BRepCheck_Analyzer` rejects it, which is itself worth knowing.
Timings are the fastest of five runs with `SetRunParallel(false)`.

### Boolean torture set (R-16)

Full table: [`spikes/boolean-torture/results/occt.md`](../../../spikes/boolean-torture/results/occt.md).

| Result | Value |
|---|---|
| Case×setting combinations valid per `BRepCheck_Analyzer` | **30 / 30** (10 cases × {default, fuzzy 1e-5, fuzzy 1e-3}) |
| Cases numerically exact (identity residual ≤1.5e-14 absolute, ≤8e-16 relative) | **9 / 10** |
| Cases failing R-16's 1e-9 relative identity threshold | **1** — `sliver`, at 3.3e-8 relative (below the 1e-6 fail line, so neither pass nor fail) |
| Worst case time | `wall_with_openings`: 52 ms union, 49 ms intersection |
| Simple two-box boolean | 0.6–4.6 ms |

Two derived numbers worth writing down. A wall with twelve openings at ~50 ms means the
Schependomlaan benchmark model's 934 walls would cost roughly **47 seconds** of boolean time alone
if each carried a comparable opening count — *inferred*, by multiplication, not measured on that
model, and openings per wall there are far fewer, so treat it as an order-of-magnitude ceiling
rather than a prediction. And 50 ms is three frames at 60 Hz: re-cutting one wall during a drag
gesture is not free at OCCT's speed.

Fuzzy settings changed no result on this set except by raising the result's tolerance. That is the
important negative: **fuzzy did not fix anything here, it only made the answer vaguer.**

### Precision set (R-17) — passes

Full table: [`spikes/precision-set/results/occt.md`](../../../spikes/precision-set/results/occt.md).

| Result | Value |
|---|---|
| Worst vertex deviation, origin vs. 500 km, after translating back | **3.61e-10 m** |
| Worst relative volume deviation | 1.39e-10 (`wall_with_openings` intersection) |
| Simple cases (`overlap_half`, `coplanar_faces`) | 2.48e-16 m and 0 m — exact |
| R-17 threshold | pass below 1e-6 m → **PASS**, by four orders of magnitude |

The f64 ULP of 5e5 m is ≈1.1e-10 m, so 3.6e-10 m is about three ULP: OCCT's boolean is
translation-invariant at 500 km to within the representation itself. This is real evidence for
ADR-0006's *sufficiency* claim — f64 world coordinates survive 500 km. It is **not** evidence for
the *necessity* claim ("float32 local coordinates fail the precision set"), which no OCCT
measurement can supply because OCCT has no float32 path. That row of ADR-0006's evidence table
needs a different candidate.

### Tessellation on 10k elements

Full table: [`spikes/tessellation/results/occt.md`](../../../spikes/tessellation/results/occt.md).

| Linear deflection | Mode | Mesh time | Triangles |
|---|---|---|---|
| 1.0 | single | 4218 ms | 120,000 |
| 0.1 | single | 4488 ms | 120,000 |
| 0.01 | single | 4523 ms | 120,000 |
| 0.001 | single | 4606 ms | 120,000 |
| 0.001 | parallel | 4724 ms | 120,000 |
| 400 spheres, deflection 5e-4 | single | 76,245 ms | 12,881,600 |
| 400 spheres, deflection 5e-4 | **parallel** | **7,783 ms** | 12,881,600 |

Three findings:

1. **4.4 s to tessellate 10k boxes**, ~37 µs per triangle, plus 250 ms to construct them. For a
   model that is nothing but axis-aligned boxes this is a large number, and it is the number that
   would sit between a model change and a redraw if OCCT were the kernel.
2. **Deflection is nearly free to change on planar geometry** — the triangle count is constant and
   the time varies by 9% across four decades. So `problems.md` P-11's "quality vs. speed" tension
   is *not* general: on planar BIM geometry there is no tension, and holding two tessellations of a
   wall costs storage, not computation. The cost is real on curved geometry, where the sphere rows
   show 12.9 M triangles from 400 objects.
3. **The parallel flag is not a free win.** It costs 8% on the box model and gives 9.8× on the
   sphere model. The default thread pool has 32 threads, so this is not a build without threading —
   it is per-face work too small to amortise the parallel path. Any threading design that
   parallelises per-object without checking the per-object work will reproduce this.

## The twelve questions

1. **Re-evaluate a single changed element without reprocessing the model?** No. There is no
   evaluation graph in the kernel; `BRepTools_History` is per-operation only. The caller must own
   the dependency tracking, which is precisely the layer FreeCAD built and where its topological
   naming problem lives (R-13, P-04).
2. **IFC round trip?** Not applicable — OCCT has no IFC. Answered in the IfcOpenShell note.
3. **Driven in-process from DynLex without a subprocess or a file?** Only through a C++ ABI. There
   is no C API; every entry point is a C++ class with handle-based memory management. A binding
   layer would have to be written and maintained, and it would be large — the Python bindings that
   ran these measurements are machine-generated from the headers.
4. **Threading model, and what is single-threaded by design?** Opt-in parallelism per operation,
   off by default, both for booleans (`SetRunParallel`) and tessellation (`isInParallel`). Measured
   to work (9.8× on curved tessellation). Nothing found that is single-threaded *by design*; the
   defaults are conservative rather than the architecture being serial. No documented thread-safety
   bound for BOP, and no tracker evidence of a threading defect. **This partially refutes
   `problems.md` P-08 as written for OCCT** — see below.
5. **What breaks first at scale?** Evaluation time, well before memory: 4.4 s of tessellation for
   10k trivial solids. Two tracker reports (#724, #800) describe >10 GB memory on *single* boolean
   operations, so memory is a tail risk on hard inputs rather than a scaling limit on easy ones.
6. **Numeric precision internally, and configurable?** f64 everywhere in modelling. Not
   configurable downward: `Precision::Confusion()` is `constexpr 1.e-7` and every tolerance-taking
   API clamps up to it (measured three separate ways in §Tolerance model). Unit-relative, since
   OCCT has no unit system.
7. **Operate on a subset — one tile, one region?** Yes, trivially: shapes are independent values
   with no global registry, so a boolean on two solids touches nothing else. This is a genuine
   strength for R-14 and a direct consequence of having no evaluation graph — the same design
   choice that fails question 1 passes this one.
8. **Who maintains it, and what if they stop?** Open Cascade SAS, commercially, with LGPL source.
   If they stopped, the code would remain usable and forkable, but a 26-year C++ codebase with a
   3562-line specification for one algorithm is not a codebase a small team maintains. The tracker
   suggests the practical bus factor is already tight: 13 of 20 surveyed boolean issues open,
   several with "not yet analyzed" as the only maintainer response.
9. **Documented failure modes and the design choice behind each?** §Known problems. Every trigger
   class traces to the same root: topology is decided by comparing distances against tolerances,
   so the decision is made on rounded values and can contradict itself, and anything below the
   tolerance is invisible to both the algorithm and the validity checker.
10. **Representations held natively, and conversions?** One (B-rep), plus a derived tessellation
    cache. Conversions are one-directional out of B-rep. Nothing to borrow for ADR-0005's
    multi-representation design except the negative example.
11. **How does geometry reach the GPU and come back?** Through `BRepMesh` → `Poly_Triangulation`
    per face, so the 4.4 s above is the upload-preparation cost. Nothing comes back.
12. **What would we take, and what would we avoid?** §Verdict.

## Strengths

- The tolerance model is **explicit, per-entity and inspectable** at runtime. Whatever its
  consequences, it is not hidden: `BRep_Tool::Tolerance` on any entity tells you exactly how
  uncertain that entity is, and that is more than most kernels offer.
- The **specification is honest**. A 3562-line document with a chapter of admitted limitations and
  worked counter-examples of its own validity checker being wrong is unusual, and it is where
  most of the *avoid* column below comes from.
- **Argument preconditions are stated**, so a caller can check them: valid, non-self-interfered,
  C1 or better.
- **38 named failure categories** in `BRepCheck_Status` — not a boolean valid/invalid.
- **Passes the precision set** at 500 km with room to spare.
- **Independent shapes**: no global registry, so subset operation and R-14 are unproblematic.

## Weaknesses

- **No incremental evaluation** (question 1). This alone disqualifies *build on* against R-01.
- **Silent loss below tolerance** — the `sliver` result. An operation that returns a wrong answer
  with `IsDone() == true` and a valid result shape is the worst possible failure shape for a
  modeller, because there is nothing to catch.
- **Operations mutate their inputs by default** (measured: 1.5e-7 → 5.0e-4 on one fuse).
- **One representation.** ADR-0005 wants four; OCCT offers B-rep and a tessellation cache.
- **Tessellation is slow** — 4.4 s for 10k boxes.
- **`Confusion()` is a compile-time constant with no unit system**, so effective precision depends
  on the file's units.
- **Healing can make things worse** — #1193 shows `ShapeUpgrade_UnifySameDomain` introducing
  self-intersections into a shape that was clean; #344 reports `ShapeFix` producing wrong results.
- **C++-only embedding**, with a large handle-based API and no C ABI.

## Risks

If we built on OCCT, the risk that would not surface until too late is the **silent-wrongness
class**: booleans that succeed, validate, and are subtly wrong. The `sliver` case took a
purpose-built torture set to expose; IfcOpenShell #7815 is the same shape of failure on real
building geometry, and IfcOpenShell #821 shows the downstream consequence — a wall shipped with
its opening missing, logged and forgotten. A product whose output is construction documents cannot
have a geometry layer whose errors are invisible to its own validity check.

The second risk is the one this note cannot measure: **the long tail**. Nine of ten torture cases
exact is a good result, and it is also what twenty-six years of fixing special cases buys. Our own
kernel starts at zero on that tail (`problems.md` N-01), and no amount of design elegance
substitutes for it. This note is evidence against *build on*; it is not evidence that building our
own will go better, and it should not be cited as if it were.

## Verdict

### Build on — **no**

Not because of boolean quality, which is good, but because of three structural mismatches with the
product's requirements, in descending order of severity:

1. **No incremental evaluation** (R-01, the programme's critical risk). OCCT has no evaluation
   graph, so the entire dependency layer would be ours to build — which is what FreeCAD did, and
   R-13 records how that turned out.
2. **One representation** where ADR-0005 requires four as equals. Adopting OCCT means adopting
   canonical-B-rep, i.e. ADR-0005's rejected Option A.
3. **Embedding cost.** A C++ handle API with no C ABI, bound into DynLex, is the FFI seam ADR-0004
   Option B exists to avoid — and it would be a larger seam than a Rust or C++ kernel, not smaller.

The precision result and the boolean result do **not** support rejection; they are OCCT's strong
suit. The evidence row in [ADR-0004](../../architecture/decisions/0004-build-our-own-kernel-in-dynlex.md)
("No candidate can be built on without a disqualifying assumption") is answered from this note by
items 1 and 2 above, and the labelling matters: item 1 is *inferred* from the source (an absence
is hard to measure), item 2 is *inferred* from the package structure, item 3 is *inferred* from
the API shape.

### Borrow from — **substantially, as design; never as code**

The licence permits linking, not source reuse into a differently-licensed kernel (R-11). Everything
below is an idea to reimplement, with the citation that justifies it.

| Take | Why | Where it comes from |
|---|---|---|
| **Per-entity tolerance, stored on the entity and readable** | The alternative — a single global epsilon — makes it impossible to answer "how uncertain is *this* face?". Spec §5's per-entity tolerance is this idea. | [`BRep_Tool::Tolerance`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingData/TKBRep/BRep/BRep_Tool.hxx#L87-L345), [`BRep_TVertex.lxx#L33-L37`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingData/TKBRep/BRep/BRep_TVertex.lxx#L33-L37) |
| **A whole-shape `MaxTolerance` query** | One number that says how much a shape has degraded. Cheap to maintain, and it is the thing to show a user when a boolean "worked". | [`BRep_Tool::MaxTolerance`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingData/TKBRep/BRep/BRep_Tool.hxx#L379) |
| **An explicit per-operation tolerance parameter (the fuzzy value)** | Naming the tolerance at the call site instead of inheriting a global is right, even though the tracker shows fuzzy rarely rescues a failure. Take the *interface*, not the expectation. | [`BOPAlgo_Options::SetFuzzyValue`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingAlgorithms/TKBO/BOPAlgo/BOPAlgo_Options.cxx#L105-L108) |
| **Non-destructive as the *default*, not an option** | OCCT has the right mechanism (`SetNonDestructive`) and the wrong default. Measured: a fuse raised its inputs' tolerance by 3300×. Our operations never mutate their arguments. | [boolean_operations.md#L2808-L2816](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/dox/specification/boolean_operations/boolean_operations.md#L2808-L2816), [Probe B](../../../spikes/boolean-torture/results/occt.md) |
| **Categorised validity, not a boolean** | 38 named statuses (`BRepCheck_InvalidCurveOnSurface`, `BRepCheck_SelfIntersectingWire`, `BRepCheck_NotClosed`, …). A validity check that returns `false` is nearly useless; one that returns *which* invariant broke is a debugging tool. | [`BRepCheck_Status.hxx#L20-L58`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingAlgorithms/TKTopAlgo/BRepCheck/BRepCheck_Status.hxx#L20-L58) |
| **Stated argument preconditions, checked at the boundary** | "Valid, non-self-interfered, C1 or better" is a contract. Our boolean states its preconditions and *rejects* violating input rather than producing something. | [boolean_operations.md#L405-L426](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/dox/specification/boolean_operations/boolean_operations.md#L405-L426) |
| **The interference taxonomy** (V/V, V/E, V/F, E/E, E/F, F/F + the four solid cases) | A complete enumeration of what two B-rep entities can do to each other. Any B-rep boolean has to handle exactly these ten, and having them named is half the design. | [boolean_operations.md#L139-L276](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/dox/specification/boolean_operations/boolean_operations.md#L139-L276) |
| **Per-operation history as generated / modified / removed** | The right *shape* for an operation's output mapping — three relations, defined only for vertex, edge, face, solid. Feed it to a stable-handle layer instead of to a name-matching layer (P-04, R-13). | [`BRepTools_History.hxx#L27-L41`](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/src/ModelingData/TKBRep/BRepTools/BRepTools_History.hxx#L27-L41) |
| **Writing down the limitations** | The single most valuable thing in the whole codebase is the chapter that admits what does not work. Our kernel's spec gets the same chapter. | [boolean_operations.md#L2443-L2470](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/dox/specification/boolean_operations/boolean_operations.md#L2443-L2470) |
| **Threading as an opt-in flag with a measured threshold** | The measured 9.8× / −8% split says the flag is right and a blanket default is wrong. Parallelise on measured per-item work, not on item count. | [`spikes/tessellation/results/occt.md`](../../../spikes/tessellation/results/occt.md) |

### Avoid — each failure class mapped to the design choice behind it

| Failure class | Design choice it traces to | Evidence | Our design's answer |
|---|---|---|---|
| Geometry below tolerance vanishes silently, and the validity check cannot see it | Topology decided by distance-vs-tolerance comparison; validity itself defined in terms of the same tolerances | `sliver` (measured); IfcOpenShell [#7815](https://github.com/IfcOpenShell/IfcOpenShell/issues/7815) | Exact predicates decide topology; constructed points are rounded but never decide (spec §5). A predicate cannot "not see" a slab. **P-01** |
| Boolean succeeds and the result is metrically wrong | Tolerance *is* the resolution mechanism: interferences are resolved by growing tolerance spheres until they enclose the discrepancy | Probe A: +3.33e-6 m³ per glued 5e-6 gap, linear over 8 steps (measured); spec's `Tol(Vi)=Max(Tol(Vi), D+Tol(Ej))` | Tolerances explicit per operation and per entity, and **reported** — a growth is a returned fact, not a silent field update (spec §5). **P-02** |
| An operation degrades its own inputs | `SetNonDestructive` defaults to off | Probe B: 1.525e-7 → 5.001e-4 on the inputs (measured) | Operations are pure with respect to their arguments. Non-destructive is not an option. **P-02** |
| Healing introduces new defects | Healing is defined as widening tolerance until the contradiction disappears, with no invariant that it may not create a new one | OCCT [#1193](https://github.com/Open-Cascade-SAS/OCCT/issues/1193), [#344](https://github.com/Open-Cascade-SAS/OCCT/issues/344); shape_healing.md L132-L144 | Healing is an explicit, named operation with a validity check before and after; a heal that lowers validity is rejected (spec §4, §12). **P-02** |
| Curved-surface booleans fail where planar ones succeed | Surface–surface intersection by marching/approximation over 92 + 61 files of special cases; the spec says a wrong section makes a correct result impossible | OCCT [#724](https://github.com/Open-Cascade-SAS/OCCT/issues/724), [#485](https://github.com/Open-Cascade-SAS/OCCT/issues/485), [#344](https://github.com/Open-Cascade-SAS/OCCT/issues/344), [#275](https://github.com/Open-Cascade-SAS/OCCT/issues/275), [#303](https://github.com/Open-Cascade-SAS/OCCT/issues/303); FreeCAD [#25169](https://github.com/FreeCAD/FreeCAD/issues/25169), [#24115](https://github.com/FreeCAD/FreeCAD/issues/24115) | Planar B-rep booleans first (M5), curved only at M8 after measurement; the mesh path stays available as a caller-chosen fallback (spec §9). **P-12** |
| Loose tolerance from an exchange round trip crashes or breaks a later boolean | Tolerances are inherited from whatever produced the shape, with no re-derivation | OCCT [#1456](https://github.com/Open-Cascade-SAS/OCCT/issues/1456) (a ~1e-3 operand tolerance "as is common after a round trip") | Imported geometry's tolerance is set explicitly at the import boundary and recorded as provenance, never silently inherited (spec §5). **P-02** |
| One boolean consumes >10 GB, or runs for 619 s with no way to cancel | Unbounded intermediate structures; no cooperative cancellation inside the intersection loop | OCCT [#724](https://github.com/Open-Cascade-SAS/OCCT/issues/724), [#800](https://github.com/Open-Cascade-SAS/OCCT/issues/800), [#1385](https://github.com/Open-Cascade-SAS/OCCT/issues/1385) | Every long kernel operation takes a cancellation token and a budget, checked in the inner loop (spec §6, §8). |
| Tessellation quality is a per-shape property, so one quality serves everything | `Poly_Triangulation` is cached *on the face*; a second quality overwrites the first | `BRepMesh` caches on the face (source); measured: re-meshing a meshed shape is a no-op unless rebuilt | Tessellation is a conversion producing a value, not a mutation of the source; several results per object are allowed (spec §4). **P-11** — but note the measurement below tempers this. |

### Corrections this note makes to `problems.md`

Two rows were hypotheses that the evidence partly contradicts, and saying so is the point of the
file:

- **P-08 ("single-threaded evaluation … seen in OCCT (partially)")** is **not shown** for OCCT.
  Parallelism is opt-in and off by default, but it exists, it works (9.8× measured), and no
  threading defect or documented thread-safety bound was found. The real finding is different and
  more useful: *a parallel flag applied without regard to per-item work makes things slower*
  (−8% measured). The row should be restated in those terms rather than kept as "OCCT is
  single-threaded".
- **P-11 ("tessellation quality vs. speed")** is **partly shown**. The architectural half is real —
  one triangulation is cached per face, so a second quality displaces the first. The *cost* half is
  not: on planar geometry, four decades of deflection changed the time by 9% and the triangle count
  not at all. The tension P-11 describes is a curved-geometry problem, not a BIM-geometry problem.

## Sources

Primary, at commit `b8f597c677811d1f9f4d8a97f5ae2825c0353a42` (tag `V8_0_1`) — individual file and
line links are inline above:

- [OCCT repository at the pinned commit](https://github.com/Open-Cascade-SAS/OCCT/tree/b8f597c677811d1f9f4d8a97f5ae2825c0353a42)
- [Boolean Operations specification](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/dox/specification/boolean_operations/boolean_operations.md)
- [Shape Healing user guide](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/dox/user_guides/shape_healing/shape_healing.md)
- [Licence and exception](https://github.com/Open-Cascade-SAS/OCCT/blob/b8f597c677811d1f9f4d8a97f5ae2825c0353a42/OCCT_LGPL_EXCEPTION.txt)

Issue tracker — every ticket linked inline in §Known problems; the tracker root is
<https://github.com/Open-Cascade-SAS/OCCT/issues>. The legacy Mantis instance
(`tracker.dev.opencascade.org`) no longer resolves and its GitHub Pages archive returns 404, so
pre-migration tickets are reachable only through their migrated GitHub issues.

Downstream, labelled secondary throughout:
<https://github.com/IfcOpenShell/IfcOpenShell/issues>, <https://github.com/FreeCAD/FreeCAD/issues>,
and IfcOpenShell's fuzzy retry ladder in
[`src/ifcgeom/kernels/opencascade/boolean_utils.cpp`](https://github.com/IfcOpenShell/IfcOpenShell/blob/master/src/ifcgeom/kernels/opencascade/boolean_utils.cpp)
(linked at `master`, not a pinned commit — it is cited for the existence of the strategy, not for
a line number).

Measurements — the reproducible record, not a summary:

- [`spikes/boolean-torture/results/occt.md`](../../../spikes/boolean-torture/results/occt.md)
- [`spikes/precision-set/results/occt.md`](../../../spikes/precision-set/results/occt.md)
- [`spikes/tessellation/results/occt.md`](../../../spikes/tessellation/results/occt.md)
