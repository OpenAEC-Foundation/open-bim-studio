# ADR-0005 — Four equal representations, explicit conversions, boolean dispatched per representation

**Status:** accepted
**Date:** 2026-09-09
**Decided:** 2026-09-12, on the evidence table below, assembled in
[`docs/research/kernels/synthesis.md`](../../research/kernels/synthesis.md) §6.2

## Context

**Amended 2026-09-12 per [`synthesis.md`](../../research/kernels/synthesis.md) §6.2: this ADR is
independent of ADR-0004's outcome.** It was written as though it followed from ADR-0004, and it does
not. It decides the kernel's *shape* — which representations are first class and how a boolean
reaches them — not who writes each arm. `kernels/opencadstudio.md` §Verdict (a) states the
independence directly for the one candidate that could supply an arm: if the B-rep arm were built on
cadkernel, "the four-representation `boolean(A, B, op)` dispatch of §4 would be ours with cadkernel
filling one of its four arms". The decision therefore holds whether the arms are written, borrowed
or linked, and it does not contradict ADR-0003, which is still in force.

ADR-0004 proposes that we build our own kernel. That decision alone does not fix its shape. The
kernel's ambition, stated in `docs/superpowers/specs/2026-09-09-geometry-kernel-design.md` §1, is
the representational breadth of a B-rep kernel, the speed of a mesh kernel, and enough further
representations that any shape can be made — B-rep, mesh, point cloud and implicit (SDF), spec
§4, with none of the four treated as the source from which the others are derived.

This shape is itself a hypothesis to substantiate, not a consequence of ADR-0004. A kernel could
instead pick one representation as canonical and treat the others as views on it, the way most
existing single-representation kernels do — and every one of them pays for that choice somewhere:
a B-rep kernel is slow at free-form mesh work, a mesh kernel cannot hold exact curved geometry, an
implicit kernel has no natural way to express a wall's exact face. `problems.md` P-11 and P-12
record two of these costs directly. The kernel spec's bet is that keeping the four representations
equal and making every conversion between them an explicit, named operation (spec §4) avoids the
silent loss that comes from picking one representation as canonical and forcing everything else
through it.

The boolean operation is the sharpest test of this bet, because it is the operation every
representation needs and the one where existing kernels fail most visibly (`problems.md` P-01,
P-09, P-12). The spec dispatches `boolean(A, B, operation)` per representation rather than
routing every boolean through one shared algorithm (spec §4, "CSG dispatches on representation").

## Decision

We hold four representations — B-rep, mesh, point cloud, implicit — as first-class and equal, with
no implicit conversion between them anywhere in the kernel's public API. Every conversion is a
named operation with its own parameters and failure modes (spec §4). CSG dispatches per
representation: B-rep × B-rep uses a B-rep boolean (planar faces first, curved in M8), mesh × mesh
uses an exact triangle arrangement, implicit × implicit is free (a new tree node), and mixed
representations require the caller to name a conversion policy — the kernel never picks one
silently (spec §4).

**Amended 2026-09-12 per [`synthesis.md`](../../research/kernels/synthesis.md) §4.** The
exact-arrangement mesh boolean is the approach this decision *chooses*; it is **not** a measured
winner, and the earlier wording ("the only known approach that is robust on arbitrary input")
overstated what the research found. Of the fifteen candidate × setting combinations in R-16,
**twelve fail outright**; both exact-arrangement implementations measured fail (Blender's Exact
solver loses an operand on `touching_vertex`; CGAL's Epick corefinement refuses two cases); and the
single nominal pass — Blender's embedded Manifold solver — uses **neither** exact predicates nor
exact constructions, and passes on a refusal that happens to equal the right answer. The torture set
is built from bit-identical coordinates, which is the exact input class a symbolic tie-break wins,
so **the set cannot distinguish an exact predicate from a bit-equality tie-break at all**
(`kernels/problems.md` P-03, which states that no ADR may cite the 9/10 as evidence that it can).
What settles the choice is R-16 run against our own kernel, on a set extended with coordinates that
are not bit-identical — `problems.md` N-01's mitigation, now named as that experiment.

## Options considered

### Option A — single canonical representation, others derived
The conventional design: pick B-rep (the CAD-industry default) or mesh (the fast-modelling
default) as canonical, and make the others views computed on demand. Simpler to implement and to
reason about — one boolean algorithm, one validity model. Rejected because every existing kernel
that makes this choice pays for it exactly where our product needs strength: a canonical-B-rep
design inherits OCCT-class tessellation and performance costs for free-form and mesh-heavy work
(`kernels/occt.md` §Weaknesses); a canonical-mesh design has no way to hold an exact curved
surface without either losing it or bolting on a second representation anyway
(`kernels/blender.md` §Weaknesses, `kernels/manifold.md` §Weaknesses). Choosing one canonical
representation now would silently re-decide the product's geometric ambition in spec §1.

### Option B — four representations, always converted through one shared intermediate
Keep the four representations but route every operation, including boolean, through a single
shared representation (for example, always meshing before any boolean). Attractive because it
needs only one boolean implementation. Rejected because it reintroduces exactly the silent-loss
problem the multi-representation design exists to avoid: converting an exact B-rep face to a mesh
before a boolean discards the analytic surface permanently, which is the documented IFC
round-trip loss in `kernels/ifcopenshell.md` and `kernels/web-ifc.md` §IFC geometry mapping and
`problems.md` P-10, P-11. It would also make every B-rep boolean pay a mesh boolean's tolerance
class even when the operation is between two planes, which the product cannot afford for its most
common case (BIM geometry is mostly planar, spec §4).

### Option C — four equal representations, explicit per-representation conversion and boolean — chosen
No representation is silently downgraded, and the cost of a conversion is visible at the call
site instead of hidden inside an operation. The chosen mesh boolean — exact arrangement of the
two triangle sets with exact predicates, then classification — is the same approach Blender
adopted for its exact boolean and is, per spec §4, the only known approach robust on arbitrary
input; this is also the design point `spikes/boolean-torture/FINDINGS.md` (R-16) is built to
confirm or refute before the ADR can leave `proposed`. Costs four representations' worth of bugs
(`problems.md` N-03) and a boolean implementation per representation instead of one, which is an
explicit, accepted trade rather than an oversight.

## Evidence

> Every claim the decision rests on, with where it is shown. An ADR with an empty cell in this
> table stays `proposed`. Evidence type is **measured** (a `spikes/*/FINDINGS.md`), **claimed**
> (documentation or a third party, with URL) or **inferred** (reasoning shown in the note).

| Claim | Where shown | Evidence type |
|---|---|---|
| Single-representation kernels pay for it on the other geometry classes, and every candidate measured holds exactly one: OCCT needs 4.2–4.7 s to tessellate 10⁴ planar boxes and has no implicit representation at all; Manifold holds one triangle mesh and cannot carry an exact curved surface; cadkernel's mesh is export-only | [`kernels/occt.md`](../../research/kernels/occt.md) §Evaluation (representations), §Weaknesses; [`kernels/manifold.md`](../../research/kernels/manifold.md) §Evaluation, §Weaknesses; [`kernels/opencadstudio.md`](../../research/kernels/opencadstudio.md) §1, One representation, not four | **measured** (the tessellation and boolean timings) + **source** (the representation inventories) |
| A mesh-only design has no way to hold an exact curved surface without bolting on a second representation, and a float32 mesh loses the question before any algorithm runs — 0.0138 m of storage error over the benchmark operands at 500 km | [`kernels/blender.md`](../../research/kernels/blender.md) §Precision — the float32 finding, §Weaknesses | **measured** |
| CGAL's several representations are not one kernel: separate packages, separate maintainers, two licences, no shared model or handle | [`kernels/cgal.md`](../../research/kernels/cgal.md) §Evaluation (representations), §Licence | **source** + **inferred** |
| Conversion loss between representations is real and is documented where it is looked for — but the IFC **geometry** round trip was not measured by this programme, and the rows this ADR originally cited for it do not exist | [`kernels/problems.md`](../../research/kernels/problems.md) P-10 (shown, and narrower than stated: 0.36% disagreement between two implementations, and the cause is mostly the **kernel**, not the schema reading), P-11 (partly shown), P-31 (an exporter filling a format's exact-geometry entity types with tessellated f32 data); [`kernels/ifcopenshell.md`](../../research/kernels/ifcopenshell.md) §The twelve questions Q2 and [`kernels/web-ifc.md`](../../research/kernels/web-ifc.md) §The twelve questions Q2, both of which say the geometry round trip is **not measured** | **measured** (P-10's disagreement rate, P-26's attribute corruption) + **source** (P-31) + **unknown** (the geometry round trip itself, stated as such) |
| A silent conversion is a real failure mode and not a hypothetical one: an attribute round trip that changes nothing corrupts the values it writes back | [`kernels/problems.md`](../../research/kernels/problems.md) P-26; [`kernels/web-ifc.md`](../../research/kernels/web-ifc.md) §The raw write path corrupts REALs | **measured** |
| Per-representation dispatch is necessary rather than preferred, because **every** mesh boolean measured has a precondition real input violates: Manifold refuses a T-junction with `NotManifold`, CGAL's corefinement documents two preconditions that the same operand violates, and cadkernel's `faceted_solid` refuses both that T-junction and a twelve-shell cutting tool | [`spikes/boolean-torture/FINDINGS.md`](../../../spikes/boolean-torture/FINDINGS.md) §Failures, traced causes; §Construction caveats (cadkernel); `kernels/problems.md` P-09 | **measured** |
| The exact triangle arrangement is the chosen mesh boolean — **not** a measured winner. Twelve of fifteen candidate × setting combinations fail R-16; both exact-arrangement implementations measured fail; the one nominal pass uses neither exact predicates nor exact constructions; and the set cannot distinguish exactness from a bit-equality tie-break | [`spikes/boolean-torture/FINDINGS.md`](../../../spikes/boolean-torture/FINDINGS.md) §Verdict against R-16, §What this does not settle; [`kernels/problems.md`](../../research/kernels/problems.md) P-03; [`kernels/libigl-openmesh.md`](../../research/kernels/libigl-openmesh.md) §The arrangement pipeline (the pipeline shape, read from source) | **measured** (the failures) + **inferred** (that the arrangement is nonetheless the right design); the claim that it *is* robust is **not shown** and is what N-01's experiment must establish |
| Implicit earns its place for the scope spec §4 gives it — level-set CSG is cheap and free of the intersection-graph problem — and it is **not** a substitute for B-rep or mesh on exact geometry: dual-contouring vertices placed by averaging edge crossings round a wall's corner off | [`kernels/implicit.md`](../../research/kernels/implicit.md) §Verdict, §Meshing; `kernels/problems.md` P-21 | **source** + **claimed**; **nothing in that note is measured** — no OpenVDB or libfive wheel exists for this platform, and the note says so |
| The point cloud earns its place, and its cost is the **index**, not the storage: 10⁸ f64 points are 2.40 GB, while a depth-8 in-core octree over them costs 102.910 bytes/point — 4.3× the data — peaks at 13.13 GB and takes 324.4 s on one core | [`kernels/pointclouds.md`](../../research/kernels/pointclouds.md) §The index, §Measurements; [`spikes/pointcloud-scale/results/open3d.md`](../../../spikes/pointcloud-scale/results/open3d.md); `kernels/problems.md` P-13, P-17 | **measured** (Open3D only — PCL, PDAL and Potree could not be installed or run) |
| The point-cloud design this ADR implies — chunked, memory-mapped, partition-LOD, where an accepted point is *moved* out of the child into the parent so N points occupy N slots — is read from a shipping converter's source and has **not** been measured | [`kernels/pointclouds.md`](../../research/kernels/pointclouds.md) §Borrow from (Potree, BSD-2), §Risks ("Nothing here measures the design we are actually proposing") | **source** + **inferred** |
| Four representations cost four validity models and four sets of bugs, and that cost is accepted with a gate rather than waved through | [`kernels/problems.md`](../../research/kernels/problems.md) N-03; spec §9 M4/M5/M6/M8 exit criteria | **inferred** |
| This decision survives either outcome of ADR-0004, because the dispatch is ours in both | [`kernels/opencadstudio.md`](../../research/kernels/opencadstudio.md) §Verdict (a), "What it commits us to" | **inferred** |

## Consequences

**What this makes easier:** any object can be modelled in whichever representation suits it —
exact walls in B-rep, organic components in mesh or implicit, scan data as point clouds — without
one representation's limitations leaking into the others. IFC export can read from the
representation that was authoritative for each object instead of reconstructing lost precision.

**What this makes harder:** four representations means four validity models, four sets of
operations to implement and test (`problems.md` N-03), and a conversion matrix that grows
quadratically in the number of representations rather than staying flat. Callers must understand
which representation is appropriate for a given operation instead of calling one universal API.

**What this commits us to:** a boolean implementation per representation (spec §4), each proven
against the torture set independently (R-16); a conversion module (`convert/`, spec §7) that is
exercised and tested as its own surface, not a side effect of other operations; and milestone
gating where B-rep booleans on planar faces land at M5 and curved-face booleans wait for M8 (spec
§9), so the representational breadth is delivered incrementally rather than all at once.

**What is accepted without being measured, stated so it cannot be forgotten (added 2026-09-12):**

1. **The implicit representation has no measurement anywhere.** No OpenVDB or libfive wheel exists
   for this platform, so its whole case is source reading and documentation. If the implicit module
   cannot earn its M5 exit criterion, N-03's rule applies and it is deleted rather than carried.
2. **The point-cloud design is inferred from Potree's source**, and the only point-cloud
   measurement we have is of an in-core library on uniform synthetic points — the friendly case, so
   every octree figure is a lower bound for real scans. The spike that would settle it is named in
   `kernels/pointclouds.md` §Risks: build the chunked octree over 10⁸ synthetic points with chunks
   mapped from a file and measure resident memory during a fly-through, **before M6, not after**.
3. **The mesh boolean's robustness is unproven**, for us and for every candidate measured. R-16
   against our own kernel is the experiment, and the torture set needs extending with coordinates
   that are not bit-identical before it can tell exactness from a tie-break.
4. **The IFC geometry round trip was never measured.** The conversion-loss row rests on the
   disagreement rate between implementations, an attribute-corruption measurement, and a source
   finding about an exporter — not on a round trip through our own conversions, which do not exist.

**What we would have to change to reverse it:** collapse to Option A or B above, which means
picking one representation as canonical, rewriting the conversion module as one-directional
derivation, and accepting whichever silent-loss failure mode that canonical representation's
existing kernel already documents.

## Sources

- [Kernel design spec](../../superpowers/specs/2026-09-09-geometry-kernel-design.md)
- [Known problems in geometry kernels](../../research/kernels/problems.md)
- [Kernel research synthesis](../../research/kernels/synthesis.md) — the assembled evidence and the
  decision record for this ADR
- [R-16 findings, boolean robustness across five candidates](../../../spikes/boolean-torture/FINDINGS.md)
