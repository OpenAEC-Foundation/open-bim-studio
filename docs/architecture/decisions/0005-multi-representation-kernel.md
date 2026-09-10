# ADR-0005 — Four equal representations, explicit conversions, boolean dispatched per representation

**Status:** proposed
**Date:** 2026-09-09

## Context

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
| Single-representation kernels fail on the other geometry classes | `kernels/occt.md` §Weaknesses, `kernels/blender.md` §Weaknesses, `kernels/manifold.md` §Weaknesses | |
| Explicit conversions avoid documented loss | `kernels/ifcopenshell.md` §IFC geometry mapping, `kernels/web-ifc.md` §IFC geometry mapping, `problems.md` P-10, P-11 | |
| Exact arrangement is the robust mesh boolean | `spikes/boolean-torture/FINDINGS.md` (R-16), `kernels/blender.md` §Exact boolean, `kernels/libigl-openmesh.md` | |
| Implicit representation earns its place | `kernels/implicit.md` §Verdict | |

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

**What we would have to change to reverse it:** collapse to Option A or B above, which means
picking one representation as canonical, rewriting the conversion module as one-directional
derivation, and accepting whichever silent-loss failure mode that canonical representation's
existing kernel already documents.

## Sources

- [Kernel design spec](../../superpowers/specs/2026-09-09-geometry-kernel-design.md)
- [Known problems in geometry kernels](../../research/kernels/problems.md)
