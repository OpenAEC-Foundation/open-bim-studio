# ADR-0006 — f64 local coordinates in tile frames, exact predicates for topology

**Status:** accepted
**Date:** 2026-09-09
**Decided:** 2026-09-12, on the evidence table below, assembled in
[`docs/research/kernels/synthesis.md`](../../research/kernels/synthesis.md) §6.1

## Context

**Amended 2026-09-12 per [`synthesis.md`](../../research/kernels/synthesis.md) §6.4: this ADR is
independent of ADR-0004's outcome.** The Context below — "Building our own kernel (ADR-0004)
removes that constraint" — reads as though this decision followed from ADR-0004, and it does not.
This decision does not say who writes the kernel; it constrains *which* kernel may be built on —
in the synthesis' words, "ADR-0006 constrains *which* kernel may be built on — it rules out every
float32 path measured". A candidate whose coordinates are float32 fails the
precision requirement whether we write it, link it or buy it (`kernels/pointclouds.md`,
`kernels/blender.md`, `kernels/web-ifc.md`), and every f64 candidate satisfies the storage half
without our writing a line. ADR-0004 is therefore not a premise of this ADR, and this ADR does not
contradict ADR-0003, which is still in force.

`docs/domain/spatial-model.md`, written during phase 1, proposed f32 local coordinates within a
tiled coordinate architecture: a 64-bit origin per tile in the project's projected CRS, with
geometry stored relative to that origin in 32-bit floating point. That proposal targeted a kernel
built on an existing library and a GPU-first rendering path, where f32 is the natural storage
class because it is what the GPU consumes directly.

Building our own kernel (ADR-0004) removes that constraint: the kernel's own precision no longer
has to match the GPU's. `docs/superpowers/specs/2026-09-09-geometry-kernel-design.md` §5 proposes
amending `spatial-model.md` in M0 to f64 local coordinates, with the tile architecture itself
unchanged, and pairs this with a stricter rule: combinatorial decisions (which side of a plane,
do two segments cross) use exact adaptive-precision predicates, never plain floating-point
comparison, while metric decisions (are two points the same point) use an explicit, per-entity
tolerance model that grows but never shrinks. GPU precision is kept out of this decision entirely:
only the `gpu` module truncates to f32, and only after positions are made camera-relative in f64
on the CPU (spec §5).

This is three coupled claims, not one: that f32 local coordinates would fail a precision
requirement the product actually has, that floating-point topology decisions are a real,
attributable source of boolean failures elsewhere, and that exact-everywhere is not affordable
either. `problems.md` P-01, P-02 and P-03 name these as hypotheses pending candidate evidence, and
the evidence table below is where that evidence lands before this ADR can leave `proposed`.

## Decision

All kernel coordinates are 64-bit floating point in a local (tile) frame. Every kernel object
lives in a frame: a 64-bit origin in the project's projected CRS plus a rotation, with transforms
between frames computed in f64 and exact for translation by construction. Combinatorial
(topological) decisions use exact adaptive-precision predicates (`orient2d`, `orient3d`,
`incircle`, `insphere`, and intersection tests built on them), following Shewchuk's adaptive
scheme — a floating-point filter first, exact expansion arithmetic only when the filter cannot
decide. Metric decisions use an explicit tolerance model — 1e-6 m linear, 1e-9 rad angular by
default, overridable per operation — with B-rep entities carrying their own tolerance that an
operation may grow but never shrink. GPU precision is truncated to f32 only inside the `gpu`
module, after camera-relative conversion in f64 on the CPU (spec §5).

**Amended 2026-09-12 per [`synthesis.md`](../../research/kernels/synthesis.md) §4.** Two
clarifications the evidence forces, neither of which changes the decision:

- The camera-relative conversion happens at **tile** granularity, not per vertex: vertex buffers
  are stored and uploaded once in their own tile frame, and the f64 subtraction
  `own_tile_origin − camera_tile_origin` is folded into the object's instance transform before
  truncation. Read per-vertex, the original wording implied re-uploading every visible vertex
  buffer at a tile crossing, which neither shipping implementation does
  (`research/renderers/gpu-paths.md` §The correction this note makes to spec §5).
- The defaults 1e-6 m and 1e-9 rad are **disclosed** against industry practice rather than
  presented as a middle: the linear default ties the loosest of the compared defaults and the
  angular default is looser than either commercial kernel's
  (`kernels/commercial-brep-reference.md` §Verdict). They stand as defaults — every operation may
  override them and every B-rep entity carries its own — and the scale-derived alternative in the
  evidence table is the thing to measure against them at M1.

## Options considered

### Option A — f32 local coordinates in tile frames (the spatial-model.md proposal)
What phase 1 proposed, on the reasoning that f32 is sufficient once tiling removes the
large-coordinate problem, and that it matches GPU storage directly with no conversion step.
Rejected as insufficient on its own: tiling controls the *magnitude* of coordinates within a tile
but not the *precision* needed for exact combinatorial decisions or for booleans on fine
architectural detail, and f32's roughly 7 decimal digits of precision is the documented failure
mode this ADR exists to avoid (`spikes/precision-set/FINDINGS.md`, R-17). Kept only as the GPU
upload format, where it belongs (spec §5).

### Option B — exact rational arithmetic everywhere
Every coordinate and every construction in exact rational (or exact algebraic) arithmetic, the
CGAL Nef-polyhedra approach. Removes floating-point error as a category entirely.

**Rejected — and the evidence for rejecting it is weaker than this ADR first claimed, so it is
restated here rather than left as written.** The original text cited `kernels/cgal.md`
§Measurements for the cost. That section cannot carry the claim: the CGAL wheel measured exposes no
`Nef_polyhedron_3` and no Epeck mesh type, so **nothing about the exact-construction path was
measured here at all** (`kernels/cgal.md` §Corrections; `problems.md` P-03, status *partly shown*).
What is shown is the *mechanism*, in source — a Nef vertex **is** a complete 2D sphere map, over
seven separately allocated doubly-linked item lists, on coordinates the class documentation requires
to be exact ℤ or ℚ — and the *direction*, attested by CGAL contributors on their own tracker:
50.498 s to build one `Nef_polyhedron_3` from a single mesh, and "~1 minute" for a
Surface_mesh-to-Nef conversion of a "relatively simple checkerboard model". Mechanism plus
third-party attestation, not our measurement.

The research also found that the trade this option frames as binary **has four positions, not two**,
and the two it omits are the ones that actually ship (`problems.md` P-03):

1. exact constructions *stored* — Nef, the option above;
2. **exact constructions held for the duration of one operation and rounded at its boundary** —
   what CGAL's shipped corefinement does, measured at **8.183 ms** on the twelve-opening wall union
   (`spikes/boolean-torture/FINDINGS.md` §Summary, CGAL 6.0.1 Epick f64 input), with a
   maintainer naming the price of that seam: output that "contains self-intersections created when
   the exact intersection points are rounded to double";
3. **double predicates with a symbolic tie-break that fires only on bit-identical coordinates** —
   Manifold, numerically correct on 9 of our 10 cases at **0.997 ms** on the same wall union at its
   default tolerance (`spikes/boolean-torture/FINDINGS.md` §Summary, Manifold 3.5.3 f64 default tol;
   the other three settings give 1.000 / 1.104 / 0.990 ms). Position 2 is therefore roughly **8.2×**
   position 3 on this one case. *(The 8.21 ms and 0.837 ms this ADR previously carried were the
   2026-09-10 basis figures, superseded by the 2026-09-11 re-run — see
   `kernels/synthesis.md` §Corrections item 8.)*;
4. exact *predicates* over floating-point constructions — Option C, chosen.

Option B is rejected on positions 1 and 2 together: the stored-exact path's cost is attested but
unmeasured by us, and the hold-then-round path shows that the seam does not disappear, it only moves
to the rounding step — which is precisely why Option C makes the rounding explicit and keeps the
*decisions* exact. The product's performance targets (spec §10) assume construction stays in
floating point.

### Option C — f64 local coordinates, exact predicates for topology, explicit tolerance for metric decisions — chosen
f64 gives roughly 15–16 decimal digits, enough headroom within a tile-sized region for both
architectural detail and the precision set's 500 km test case (spec §5). Restricting exactness to
predicates rather than all construction keeps performance within reach, following the same
floating-filter design CGAL itself uses for predicates specifically. The explicit,
never-shrinking tolerance model is a direct, named answer to the tolerance-growth failure mode
documented for tolerant B-rep (`kernels/occt.md` §Tolerance model, `problems.md` P-02): tolerances
still grow, but every growth is visible and attributable instead of silently inherited.

## Evidence

> Every claim the decision rests on, with where it is shown. An ADR with an empty cell in this
> table stays `proposed`. Evidence type is **measured** (a `spikes/*/FINDINGS.md`), **claimed**
> (documentation or a third party, with URL) or **inferred** (reasoning shown in the note).

| Claim | Where shown | Evidence type |
|---|---|---|
| float32 local coordinates fail the precision set, and f64 local coordinates pass it — 0.0186–0.5 m against 3.3e-11–3.6e-10 m, two populations with three orders of magnitude between them and no candidate in between | [`spikes/precision-set/FINDINGS.md`](../../../spikes/precision-set/FINDINGS.md) (R-17) §Summary, §Verdict against R-17 | **measured** |
| The separation is not an artefact of comparing different libraries: it appears inside one library (Manifold `Mesh64` 3.29e-11 m against `Mesh` 0.0186 m) and inside one set of exact predicates (CGAL Epick f64 1.29e-10 m against f32-rounded 0.0348 m) | [`spikes/precision-set/FINDINGS.md`](../../../spikes/precision-set/FINDINGS.md) §Summary, the two-population reading | **measured** |
| The local-frame mitigation this ADR proposes was measured on every candidate rather than assumed, and it rescues the case that matters: on Blender's twelve-opening wall, carrying the offset in the `location` instead of in the vertices takes a **0.0348 m** error to **0 m**. Two qualifications the FINDINGS states and this row must not drop: **the roll-up sentence is labelled *inferred* there**, and the per-candidate results are not uniformly 0 m — Blender's **Fast** solver still deviates **0.5 m** on `overlap_half` ∩ (a result already invalid in both frames, so the frame changes an error term, not a verdict), and Manifold's wall reaches **3.29e-11 m / 2.60e-11 m** at f64, not 0 | [`spikes/precision-set/FINDINGS.md`](../../../spikes/precision-set/FINDINGS.md) §The local-frame mitigation, measured (the per-candidate table and its closing *inferred* paragraph) | **measured** (each candidate's cell) + **inferred** (the roll-up "works on every candidate measured", which is the FINDINGS' own label) |
| Floating-point topology decisions cause invalid booleans | [`spikes/boolean-torture/FINDINGS.md`](../../../spikes/boolean-torture/FINDINGS.md) §Failures (Blender Fast: wrong volumes 33–100% with `double_threshold` deciding topology on rounded values); `kernels/problems.md` P-01; `kernels/occt.md` §Known problems; `kernels/blender.md` §Carve history | **measured** (the torture rows) + **claimed** (the trackers) |
| An exact predicate is worth having, directly: 2164 of 4096 plain-double answers wrong against an exact-rational oracle, 0 of 4096 for the filtered exact predicate | [`kernels/cgal.md`](../../research/kernels/cgal.md) §The predicate is worth having: measured, 2164 wrong answers out of 4096 | **measured** |
| Exact predicates keep the *combinatorics* right on rounded coordinates and cannot keep the *geometry* right — which is why this ADR pairs them with f64 storage rather than treating them as a substitute for it | [`kernels/cgal.md`](../../research/kernels/cgal.md) §f32-rounded input, with the exact predicates still on; [`spikes/precision-set/FINDINGS.md`](../../../spikes/precision-set/FINDINGS.md) §Summary | **measured** |
| Exact rational *constructions* are costly — mechanism in source, magnitude attested by third parties, **measured by nobody here**; and the trade has four positions, not two (see Option B) | [`kernels/cgal.md`](../../research/kernels/cgal.md) §What P-03 asks; `kernels/problems.md` P-03; [`kernels/manifold.md`](../../research/kernels/manifold.md) §How the boolean works | **inferred** (source) + **claimed** (CGAL tracker); *not measured — recorded as the gap it is* |
| In a tolerant B-rep, tolerance is **inherited and unreported**, and the metric error it buys accumulates — but the two probes measure different quantities and neither shows tolerance compounding. **Probe A** (eight chained `BRepAlgoAPI_Fuse` operations on boxes separated by 5e-6 m gaps, `SetFuzzyValue(1e-5)`): the maximum entity tolerance rose **once**, to 5.1e-6 ≈ fuzzy/2 + `Precision::Confusion()`, and then **plateaued — it did not compound over the chain**; what grew linearly is the *excess volume*, 3.33e-6 m³ per step to **2.67e-05 m³** after eight, because each bridged gap is counted as solid. **Probe B** (one fuse on the `sliver` case, `SetFuzzyValue(1e-3)`, `SetNonDestructive` left at its default **off**): the largest tolerance on the operation's own **input** shapes rose 1.525e-7 → **5.001e-4**; on the clean `overlap_half` case nothing grew at any fuzzy value, so the failure mode is data-dependent. The "never shrinks" half is a property of the update path (`UpdateTolerance`), not of the data structure — the neighbouring `Tolerance(T)` setter can shrink it and healing uses it | [`kernels/occt.md`](../../research/kernels/occt.md) §Tolerance model (Probe A and Probe B, quoted with their settings); [`spikes/boolean-torture/results/occt.md`](../../../spikes/boolean-torture/results/occt.md) Probe A, Probe B | **measured** (both probes, each with its stated fuzzy value) + **source** (`UpdateTolerance` / `Tolerance(T)`) |
| The same growth pattern is an independently documented invariant in a commercial kernel, not an OCCT artefact — a vertex's precision is at least the largest precision of any edge ending at it | [`kernels/commercial-brep-reference.md`](../../research/kernels/commercial-brep-reference.md) §Parasolid, §Update to `problems.md` | **claimed** (vendor documentation) |
| A reference that breaks after an edit is a *different* problem from tolerance growth, and a handle scheme does not touch it — which is why this ADR decides tolerance and leaves identity to the application layer | [`kernels/freecad-topological-naming.md`](../../research/kernels/freecad-topological-naming.md) §When the reference breaks (the four failure classes, read from `ElementMap.cpp` at the pinned tag), §Evidence (five dated GitHub issues, three filed after FreeCAD 1.0 shipped, plus the 1.0 release notes' own "not completely solved"), §Verdict item 2 | **claimed** (the five issues and the release notes) + **inferred** (the failure classes, derived in the note from the source mechanism). **Explicitly not measured:** the note's §Measurements probe covers a **topology-preserving** edit — the `MappedName` came back byte-identical — and the note says in terms that it "is **not** a measurement of any of the four failure classes above"; its output is `spikes/topological-naming/results/freecad.txt`, not a `FINDINGS.md` or a `results/` measurement this table may cite as measured |
| A tolerance derived from a global bounding box tracks the model's global position even on an f64 path — Manifold 1e-11 → 5e-07 at 500 km, cadkernel's derived tolerance ×1.474 — so a local frame fixes coordinates and does **not** fix tolerances | [`spikes/precision-set/FINDINGS.md`](../../../spikes/precision-set/FINDINGS.md) §Manifold (the `tol` column), §The tolerance follows the model out to 500 km | **measured** |
| Camera-relative f32 is sufficient on the GPU, and the f64 subtraction belongs on the CPU at **tile** granularity rather than per vertex | [`research/renderers/gpu-paths.md`](../../research/renderers/gpu-paths.md) §Camera-relative rendering, §The correction this note makes to spec §5; [`kernels/opencadstudio.md`](../../research/kernels/opencadstudio.md) §3 (the two-float scheme confirmed with instancing on a modern explicit API) | **inferred** (arithmetic and source reading across OCCT, Filament and cadkernel) — **not measured**; R-20 is the spike that would measure it |
| Point-cloud storage is where f64-everywhere is *not* obviously right: float32 world coordinates cost 0.015625 m at 500 km (measured), and an `int32 × scale + f64 offset` quantum is 12 bytes and position-independent — but whether the scale is per tile, per cloud or per chunk is **undecided** | [`kernels/pointclouds.md`](../../research/kernels/pointclouds.md) §Precision — the P-05 evidence, §Borrow from, §Risks (last paragraph) | **measured** (the float32 error) + **source** (the quantum encoding); the per-tile/per-cloud/per-chunk choice is **unknown** and is named as an open question in §Consequences |
| The 1e-6 m linear default **ties the loosest** of the compared industry defaults (ACIS `SPAresabs` 1e-6 exactly; Parasolid 1e-8 units; OCCT 1e-7 m), and the 1e-9 rad angular default is **looser than either commercial kernel's**, by two orders against Parasolid and three against OCCT | [`kernels/commercial-brep-reference.md`](../../research/kernels/commercial-brep-reference.md) §Verdict | **claimed** (each figure read from the vendor's own public documentation, with URL and access date) |
| A scale- and position-derived tolerance is a shipping alternative to a fixed absolute default: `extent·1e-8 + ε·coordinate_scale·64`, measured at 1.500e-8 / 2.000e-8 on the precision set's two runnable cases | [`kernels/opencadstudio.md`](../../research/kernels/opencadstudio.md) §Tolerance, §Borrow from 4 | **measured** (the derived values) + **source** (the formula) |

## Consequences

**What this makes easier:** geometry at any distance from the project origin, within a tile,
carries the same precision guarantees. Boolean and other topological operations get a
never-wrong answer to "which side" and "do these touch", which removes an entire class of
tolerance-triggered boolean failure at its source rather than patching results afterward.

**What this makes harder:** the kernel must implement and maintain adaptive-precision predicate
arithmetic itself (`core/`, spec §7) rather than relying on plain floating-point comparisons;
every operation that constructs new geometry must be audited for where it hands off to a
predicate versus where it stays in plain f64; and f64 storage costs twice the memory and bandwidth
of f32 everywhere except the GPU upload path.

**What this commits us to:** the tolerance model is per-entity and monotonically growing, which
means every operation that touches a B-rep entity must propagate tolerance correctly or silently
reintroduce P-02's failure mode; and the precision-set spike (R-17) must pass before this ADR can
be accepted, not merely be plausible. **It did** — every f64 path passes and every float32 path
fails, which is what accepted this ADR on 2026-09-12.

**What is accepted without being measured, stated so it cannot be forgotten:**

1. **The GPU row is inferred**, from source reading across OCCT, Filament and cadkernel plus
   arithmetic on the DynLex runtime's own constants. Nothing was run. [R-20](../../risks.md#r-20--the-dynlex-gpu-path-is-argued-from-source-reading-not-measured)
   is the spike that measures it, and it is open.
2. **The exact-predicate rule has never been measured at kernel level**, because we have no kernel.
   CGAL's 4096/4096 measurement is of CGAL's predicate, not ours. The test that closes this is spec
   §9 M1's exit criterion — a predicate fuzz test against an exact-rational reference on 10⁶ random
   and degenerate inputs — and it must actually be run, not assumed.
3. **The point-cloud storage quantum is undecided.** Whether the `int32 × scale` factor is chosen
   per tile, per cloud or per chunk changes what a project mixing a 1 mm terrestrial scan with a
   5 cm airborne survey loses. `kernels/pointclouds.md` §Risks states the trade and explicitly does
   not decide it; this ADR does not either, and the decision belongs with the `pointcloud` module at
   M6.
4. **Exact-rational construction cost is attested, not measured by us.** If the question ever
   becomes live again — for a verification path, say — it needs a measurement, not this ADR's
   Option B.
5. **Half of R-17's own spike sentence was never run.** It names "each candidate's boolean **and
   tessellation**" at 500 km, and **no driver tessellates at the far location**; curved geometry is
   absent from the precision set altogether, and the set is three planar cases at one distance in
   one direction. That is what keeps [R-17](../../risks.md#r-17--precision-far-from-the-origin)
   `in progress` even though this ADR is accepted on the part it did settle — the f64/f32 population
   separation.
6. **A reference that breaks after an edit has no measurement behind it here.** The FreeCAD row above
   rests on five dated issues and the source mechanism; the one probe that ran measured a
   topology-preserving edit and explicitly does not exercise any failure class.

**What we would have to change to reverse it:** drop back to Option A, which reopens the
500 km precision-set case as an open failure, or move to Option B, which requires re-deriving the
performance targets in spec §10 against exact-construction costs instead of floating-point
construction costs.

## Sources

- [Kernel design spec](../../superpowers/specs/2026-09-09-geometry-kernel-design.md)
- [Spatial model](../../domain/spatial-model.md)
- [Known problems in geometry kernels](../../research/kernels/problems.md)
- [Kernel research synthesis](../../research/kernels/synthesis.md) — the assembled evidence and the
  decision record for this ADR
- [R-17 findings, precision at 500 km](../../../spikes/precision-set/FINDINGS.md)
- [R-16 findings, boolean robustness](../../../spikes/boolean-torture/FINDINGS.md)
