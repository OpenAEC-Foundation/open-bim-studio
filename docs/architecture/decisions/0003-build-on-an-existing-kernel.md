# ADR-0003 — Build on an existing kernel

**Status:** accepted
**Date:** 2026-07-29

## Context

The project targets professional BIM capability — 3D modelling, parametric components,
coordinated 2D drawings, IFC exchange — built in a short, concentrated effort.

Geometry kernels and IFC implementations are among the most expensive software artefacts in the
industry. Commercial geometry kernels represent decades of development. IFC covers several
schema generations with substantial ambiguity and well-known implementation disagreements.

Neither is a differentiator for this project. Nobody will choose this tool because of its
boolean algorithm. They will choose it for its interaction model and its coordination — the
areas where existing tools are weak.

## Decision

We build on existing kernels rather than writing our own. This applies to both the semantic/BIM
layer and the geometry layer.

Writing our own is reconsidered only if the research in `docs/research/kernels/` shows that no
candidate can meet a requirement we are unwilling to drop — and that reconsideration requires a
new ADR, not a quiet change of course.

Which kernels remains open; see `docs/architecture/layers.md` for the working hypothesis and
`docs/research/kernels/` for the evaluation.

## Options considered

### Build on existing kernels — chosen
Effort goes into the parts that differentiate. Costs us dependency on external projects, their
release cycles, their licences, and their architectural assumptions — and those assumptions may
not fit interactive editing, which is exactly what risk R-01 is about.

### Write our own geometry kernel
Rejected. Full control and a perfect fit for our evaluation model, but it is a multi-year
project on its own and would consume the entire effort. It is also the classic way ambitious
modelling projects fail: the kernel becomes the product and the application never arrives.

### Write our own IFC implementation
Rejected. IFC's ambiguities and the disagreements between implementations are exactly the kind of
accumulated knowledge that existing libraries encode. Reimplementing means rediscovering every
interoperability problem the ecosystem already solved.

## Consequences

**Easier:** effort concentrates on the interaction model, the evaluation system, and the drawing
pipeline — the areas that determine whether this product is worth using.

**Harder:** we inherit architectural assumptions that may not suit interactive editing. Kernel
selection becomes correspondingly critical, which is why `docs/research/kernels/` is the
decisive research area and why incremental evaluation is weighted critical there.

**Commits us to:** licence compatibility across the whole stack (risk R-11), and to the release
cadence and continued existence of upstream projects.

**To reverse:** would require accepting a multi-year timeline, which contradicts the premise of
the project.
