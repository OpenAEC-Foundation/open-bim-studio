# ADR-0004 — Build our own geometry kernel in DynLex

**Status:** proposed
**Date:** 2026-09-09

## Context

ADR-0003 committed to building on an existing geometry kernel, on the premise that a kernel is
not a differentiator and that writing one is a multi-year project that consumes the whole
effort. That premise held while candidates remained unevaluated.

Two things changed. First, DynLex — the maintainer's own language — now exists as a target
capable, in principle, of compiling and running kernel-shaped code, which was not true when
ADR-0003 was written. Second, the research phase against the candidates in
`docs/research/kernels/` produced an early finding, not a final one: every candidate evaluated so
far imposes an assumption the product cannot accept without dropping a requirement — batch-only
conversion with no cheap re-evaluation of a single changed element, float32-only paths, a single
global coordinate origin, or a licence that blocks embedding or later open-sourcing (see
`docs/research/kernels/problems.md` P-05 batch re-evaluation, and P-06 origin and licence
constraints, as the recurring shapes of the disqualifying assumption).

`docs/superpowers/specs/2026-09-09-geometry-kernel-design.md` records the resulting hypothesis in
full: a multi-representation kernel written in DynLex. This ADR proposes the first and largest
part of that hypothesis — building our own kernel at all, in DynLex specifically — as the
decision ADR-0003 already named as the reconsideration trigger: "writing our own is reconsidered
only if the research shows that no candidate can meet a requirement we are unwilling to drop."

This ADR stays `proposed` until the evidence table below is filled. Until then ADR-0003 remains
in force and no kernel code is written (spec §0, header).

## Decision

We build our own geometry kernel, written in DynLex.

The kernel is a pure DynLex library (`kernel/`) with no dependency on an existing geometry
kernel. It is developed as its own sub-project with milestones M0–M8, ahead of the UI and IFC
libraries that depend on it, because it carries the largest unknowns: boolean robustness,
precision, and performance (spec §2).

## Options considered

### Option A — build on an existing kernel (ADR-0003)
The status quo. Concentrates effort on the areas that differentiate the product — interaction
model, evaluation, drawing pipeline — and avoids the multi-year risk of a from-scratch kernel.
Rejected as the sole path because every candidate evaluated so far forces a choice between the
product's requirements and the kernel's assumptions: a kernel that cannot cheaply re-evaluate one
changed element undermines the interaction thesis (R-01) at the root, not at the edges, and no
candidate offers f64-precision paths, multi-representation breadth and a compatible licence
together. Remains available as a fallback if the DynLex evidence in this ADR fails — that
fallback is the reason the research programme keeps evaluating candidates in parallel with the
spikes below, rather than stopping once this ADR is proposed.

### Option B — write our own kernel in an established systems language
Rust, C++ or similar. Removes the language-maturity risk entirely: SIMD codegen, threading, and
memory-mapped I/O are solved problems in these ecosystems, and the kernel would not be blocked on
extending a compiler that has never carried a program this large. Rejected because it does not
serve the project's actual differentiator, which is that the whole stack — kernel, UI, IFC — is
written in one language the maintainer controls end to end, and because a systems-language kernel
still has to be bound into DynLex for the UI and app layers, reintroducing an FFI seam of exactly
the kind ADR-0003 already accepted as a cost of building on someone else's kernel. If the DynLex
evidence in this ADR fails outright — not merely falls short on one workload — this option is the
next one to evaluate, ahead of returning to Option A.

### Option C — write our own kernel in DynLex — chosen
Full control, one language across the stack, and a kernel design that can be shaped exactly to
the interaction model instead of adapted to one. Costs: DynLex has never compiled or run a
program at this scale, and the extensions in spec §8 (threading, memory-mapped allocation,
verified SIMD codegen) do not exist yet and must be built as part of the kernel effort. This is
the paper-thin line between "differentiator" and "the classic way ambitious modelling projects
fail" that ADR-0003 warned about — the evidence table below exists to keep that line honest rather
than assumed.

## Evidence

> Every claim the decision rests on, with where it is shown. An ADR with an empty cell in this
> table stays `proposed`. Evidence type is **measured** (a `spikes/*/FINDINGS.md`), **claimed**
> (documentation or a third party, with URL) or **inferred** (reasoning shown in the note).

| Claim | Where shown | Evidence type |
|---|---|---|
| No candidate can be built on without a disqualifying assumption | `kernels/occt.md` §Verdict, `kernels/ifcopenshell.md` §Verdict, `kernels/web-ifc.md` §Verdict, `kernels/manifold.md` §Verdict, `kernels/cgal.md` §Verdict | |
| DynLex compiles kernel-shaped code within the compile-time budget | `spikes/dynlex-scale/FINDINGS.md` (R-18) | |
| DynLex runs kernel-shaped code within 1.5× of C++ -O2 | `spikes/dynlex-performance/FINDINGS.md` (R-19) | |
| DynLex can be extended for threading and memory mapping | `kernels/dynlex-readiness` section of `spikes/dynlex-scale/FINDINGS.md` | |
| Per-object overhead is the cause of scale ceilings we must avoid | `kernels/problems.md` P-07, `spikes/blender-ceiling/FINDINGS.md` (R-03) | |

## Consequences

**What this makes easier:** the kernel's data model can be built around handle-addressed,
per-object operations from the start, which is what R-01 (incremental evaluation) needs and no
evaluated candidate offers natively. The whole stack shares one language, one build, one test
convention, and one set of debugging tools.

**What this makes harder:** every capability an existing kernel gives for free — boolean
robustness accumulated over decades, a validated tessellation pipeline, a tolerance model that
has survived production use — has to be built and proven from nothing, on a compiler that itself
is unproven at this scale.

**What this commits us to:** a milestone sequence (spec §9) where later milestones cannot start
before earlier ones pass their exit criteria, DynLex compiler defects fixed in dynlex rather than
worked around in the kernel (spec §8, §12), and the performance targets of spec §10 measured and
recorded rather than assumed.

**What we would have to change to reverse it:** fall back to Option A or Option B above. Reversal
after M0 discards the kernel skeleton but not the research — `docs/research/kernels/` and
`problems.md` remain valid evidence for evaluating any replacement candidate.

## Sources

- [DynLex design spec](../../superpowers/specs/2026-09-09-geometry-kernel-design.md)
- [Kernel research method](../../research/kernels/README.md)
- [Known problems in geometry kernels](../../research/kernels/problems.md)
