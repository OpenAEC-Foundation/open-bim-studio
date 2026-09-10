# Known problems in geometry kernels, and where they come from

**Decision question: which failure modes of existing kernels are consequences of their design,
and how does our design avoid each one — or knowingly accept it?**

**Status:** seeded 2026-09-09 from phase 1 findings and general knowledge — **every row is a
hypothesis until a candidate note supplies evidence.** Rows without evidence are marked as such.
**Serves:** ADR-0004, ADR-0005, ADR-0006; kernel spec §4–§6.

---

## How to read this table

One row per problem. A problem is something that is observed to go wrong for users — a boolean
that produces a broken shell, a reference that breaks after an edit, a model that stops being
interactive. The **root cause** column names the design choice the problem traces back to, not
the symptom. The **evidence** column points at the candidate note section or issue that shows
it; until it does, the row's status is `hypothesis`.

The last column is the reason this file exists: what the kernel spec does about it, with the
spec section, so the design decision is traceable back to the problem it answers.

| # | Problem | Root cause (hypothesised or shown) | Seen in | Evidence | Status | Our design's answer |
|---|---|---|---|---|---|---|
| P-01 | Boolean produces an invalid shell or fails on coplanar / touching input | Floating-point predicates with tolerance-based topology decisions; the topology is decided on rounded values, so it can contradict itself | OCCT, Blender's former Carve boolean | [`occt.md`](occt.md) §Known problems, §Measurements | partly shown | Exact predicates decide topology; constructed points are rounded but never decide (spec §5) |
| P-02 | Boolean succeeds but the result is slightly wrong (slivers, gaps, misplaced vertices) | Tolerance growth: each operation may widen entity tolerances, and downstream operations inherit the looser value | OCCT tolerant B-rep | [`occt.md`](occt.md) §Tolerance model (measured: a fuse raised its *inputs*' tolerance 1.5e-7 → 5.0e-4; glued gaps added 3.3e-6 m³ per operation, linearly) | shown | Tolerances are explicit, per operation and per entity, grow but never shrink, and are reported (spec §5) |
| P-03 | Exact boolean is correct but too slow or memory-hungry for interactive use | Exact rational arithmetic on every construction, not only on predicates | CGAL Nef polyhedra | — | hypothesis | Exact arithmetic only in predicates, adaptive with a floating filter (spec §5) |
| P-04 | References break after an edit (dimensions, openings, features point at the wrong or a vanished face) | Topological naming: references store names for the *output* of a computation | FreeCAD on OCCT; all history-based CAD | phase 1 prior-art notes | shown (phase 1) | Out of kernel scope: references point at semantic entities in `app/`; the kernel offers stable generational handles and never renumbers (spec §6, R-13) |
| P-05 | Precision loss far from the origin; geometry vibrates or snaps | Single global origin, float32 storage or GPU float32 with world coordinates | Real-time engines; float32 viewers | phase 1 spatial-model note | shown (phase 1) | f64 in tile-local frames, camera-relative f32 only at upload (spec §5, ADR-0006) |
| P-06 | Whole model re-evaluates after one change | Batch conversion architecture; no dependency tracking below the model level | Most IFC tooling; viewers | — | hypothesis (R-01) | Kernel operations are per-object and handle-addressed; the evaluation graph lives in `app/` (spec §3) |
| P-07 | Viewport stops being interactive around 10⁴–10⁵ objects | Per-object heap allocation and per-object draw calls; object model overhead | Blender via Bonsai (R-03 unresolved whether Blender or Bonsai) | phase 1 hosts note | hypothesis | Structure-of-arrays, generational handles, instancing-first GPU layouts (spec §6) |
| P-08 | Single-threaded evaluation | Global state, non-reentrant kernels, locks around shared caches | OCCT (partially), IFC parsers | **Not shown for OCCT** — [`occt.md`](occt.md) §Measurements: parallelism is opt-in and off by default but it works (9.5× measured on curved tessellation); no thread-safety defect found on the tracker. The measured OCCT problem is the opposite one: the same flag costs +8% on average (+1.3% to +13.5% over four paired deflections) when per-item work is too small. Restate the row, or carry it on the IFC parsers alone | hypothesis | No global state; `parallel for` over independent handles; DynLex threading added when needed (spec §6, §8) |
| P-09 | Mesh boolean requires manifold, self-intersection-free input and rejects real models | The algorithm's correctness proof assumes it | Manifold | — | hypothesis | Mesh validity check is explicit; healing is an explicit operation; arrangement-based boolean tolerates non-manifold input where the literature allows (spec §4, §12) |
| P-10 | IFC geometry interpreted differently by different implementations | Schema ambiguity (swept solids, boolean clipping results, units, placements) | IfcOpenShell vs web-ifc vs xBIM | — | hypothesis | Out of kernel scope: `ifc/` maps representations explicitly; disagreements recorded per entity type |
| P-11 | Tessellation quality vs. speed: chords too coarse for drawings, too fine for the viewport | One tessellation per shape, one parameter set | OCCT, IFC viewers | [`occt.md`](occt.md) §Measurements — the *architectural* half holds (OCCT caches one `Poly_Triangulation` per face; measured, a finer request replaces it at full cost and a coarser request is silently ignored); the *cost* half does not on planar geometry (four decades of deflection changed the time 14% and the triangle count not at all). It is a curved-geometry problem | partly shown | Tessellation is a conversion with explicit deflection parameters; multiple results per object are allowed (spec §4) |
| P-12 | Curved-surface booleans fail where planar ones succeed | Surface–surface intersection is numerically hard; marching produces gaps | OCCT | [`occt.md`](occt.md) §Known problems — seven OCCT issues and two FreeCAD issues with `curved-intersection` as the trigger, against zero curved failures we measured ourselves (the torture set is entirely planar, so it cannot show this) | partly shown | Planar B-rep booleans first (M5), curved in M8 after measurement; mesh path as the fallback the caller chooses (spec §9) |
| P-13 | Point clouds exceed memory | In-core storage | PCL (in-core by default) | — | hypothesis | Chunked, memory-mapped storage with an octree from the first milestone that holds points (spec §4, §8) |
| P-14 | Licence blocks embedding or later open-sourcing | Copyleft on the kernel | some candidates | — | hypothesis | Not a concern for an own kernel; a concern for anything borrowed as code rather than as design (R-11) |
| P-15 | A single modelling operation consumes unbounded memory or runs unbounded time, and the caller cannot cancel it or find out how far it got | The operation owns the whole computation: intermediate structures grow with the intersection graph and have no ceiling, and the inner loops poll no cancellation flag, so a deadline outside the call cannot be enforced from inside it | OCCT | [`occt.md`](occt.md) §Known problems — [#724](https://github.com/Open-Cascade-SAS/OCCT/issues/724) and [#800](https://github.com/Open-Cascade-SAS/OCCT/issues/800) report >10 GB on a *single* boolean, the second with a maintainer confirming the defect and no fast solution; [#1385](https://github.com/Open-Cascade-SAS/OCCT/issues/1385) reports 619 s of CPU against a 30 s deadline that could not fire, the reporter finding no `UserBreak()` polling inside `IntTools_FaceFace::Perform`. All three are reporter diagnoses | partly shown | **Half answered, and the gap is recorded rather than papered over.** Work is per-object over independent generational handles (spec §3, §6), and operations return a result value with a message instead of aborting on user input (spec §12), so a runaway operation is contained to one object. The spec does **not** yet define a cancellation token, a progress report, or a memory/time budget for a long operation; adding one is an open question against spec §6 and §12 |

## Problems we may be about to create

Honesty in the other direction. Building our own kernel does not remove problems; it chooses
which ones we own.

| # | Problem | Why we would have it | Mitigation | Status |
|---|---|---|---|---|
| N-01 | Our booleans fail on inputs the mature kernels handle, because they have twenty years of fixes we do not | Every kernel's boolean is a long tail of special cases | The boolean torture set in `reference/`; exact arrangement instead of special cases; measure against OCCT and Blender on the same cases | open |
| N-02 | Compiler defects on the kernel's critical path | The kernel is the largest DynLex program | Defects are fixed in dynlex, never worked around; pinned commit; the smoke test runs on every build | open |
| N-03 | Four representations, four sets of bugs | Breadth | Each representation earns its place by a milestone with an exit criterion; a representation nobody needs is deleted | open |
| N-04 | Performance targets missed because DynLex lacks threading or SIMD codegen | Language maturity | Measured at M1 and M7; targets are recorded with the measured number, never quietly relaxed | open |

## Sources

Populated by the candidate notes. This file has no sources of its own, which is the point: it is
an index of evidence, not evidence.

- [`occt.md`](occt.md) — P-01, P-02, P-08, P-11, P-12, P-15. Source read at OCCT tag `V8_0_1`, commit
  `b8f597c677811d1f9f4d8a97f5ae2825c0353a42`; measurements in
  [`spikes/boolean-torture/results/occt.md`](../../../spikes/boolean-torture/results/occt.md),
  [`spikes/precision-set/results/occt.md`](../../../spikes/precision-set/results/occt.md),
  [`spikes/tessellation/results/occt.md`](../../../spikes/tessellation/results/occt.md).
