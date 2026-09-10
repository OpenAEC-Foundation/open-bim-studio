# ADR-0006 — f64 local coordinates in tile frames, exact predicates for topology

**Status:** proposed
**Date:** 2026-09-09

## Context

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
CGAL Nef-polyhedra approach. Removes floating-point error as a category entirely. Rejected because
exactness on every construction, not only on predicates, is the documented cause of the
performance and memory cost that makes this approach impractical for interactive use
(`kernels/cgal.md` §Measurements, `problems.md` P-03) — the product's performance targets (spec
§10) assume construction stays in floating point and only topological *decisions* are exact.

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
| float32 local coordinates fail the precision set | `spikes/precision-set/FINDINGS.md` (R-17) | |
| Floating-point topology decisions cause invalid booleans | `problems.md` P-01, `kernels/occt.md` §Known problems, `kernels/blender.md` §Carve history | |
| Exact rational everywhere is too slow | `kernels/cgal.md` §Measurements, `problems.md` P-03 | |
| Tolerant B-rep accumulates tolerance | `kernels/occt.md` §Tolerance model, `kernels/freecad-topological-naming.md` | |
| Camera-relative f32 is sufficient on the GPU | `renderers/gpu-paths.md` | |

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
be accepted, not merely be plausible.

**What we would have to change to reverse it:** drop back to Option A, which reopens the
500 km precision-set case as an open failure, or move to Option B, which requires re-deriving the
performance targets in spec §10 against exact-construction costs instead of floating-point
construction costs.

## Sources

- [Kernel design spec](../../superpowers/specs/2026-09-09-geometry-kernel-design.md)
- [Spatial model](../../domain/spatial-model.md)
- [Known problems in geometry kernels](../../research/kernels/problems.md)
