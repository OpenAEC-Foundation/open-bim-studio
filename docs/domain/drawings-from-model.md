# Drawings from the model

**Decision question: what does it actually take to produce an issuable drawing from a 3D model,
and how large is that subsystem?**

## Why this document exists separately

This is the most underestimated part of BIM software, and the gap has a specific shape:

> Generating a section is easy. Producing a drawing somebody can build from is a subsystem.

The distance between those two is mostly annotation, conventions, and control — not geometry. It
may be comparable in size to the entire 3D modelling effort. Scoping it honestly is risk R-05.

It also gets deferred naturally: 3D modelling demos well and drawings do not, so drawings arrive
last and the architecture has already made their decisions for them.

## Status: empty — phase 1 artefact

## What must be scoped

### View generation
- Cut plane semantics: what is cut, what is seen beyond, what is hidden
- Hidden-line removal — expensive and correctness-critical
- Projection: plan, section, elevation, axonometric, detail callouts
- Level of detail as a function of view scale
- Cut-face fill and material hatching

### Annotation
The bulk of the work, and the part with no geometric interest:
- Dimensions — and crucially, dimensions that stay associated as the model changes
- Tags reading model data
- Text, leaders, symbols
- Line weights and styles by element class and by cut/projected state
- Drafting elements that exist only in the view

### Coordination
The property that distinguishes a BIM tool from a 3D modeller with a section tool:
- Every view reflects the current model
- Annotation survives model change, or fails visibly rather than silently
- View templates and their propagation

### Sheets and output
- Sheet composition, title blocks, revision management
- Vector export (PDF, DWG) with correct line weights
- Print scaling

## The architectural question this document must answer

**Does the drawing pipeline share the 3D renderer, or is it a separate geometric process
producing vector output?**

These are fundamentally different architectures, and the choice is hard to reverse:

- **Shared** — reuse the scene and clipping; fast, but hidden-line quality and vector export
  fidelity are constrained by the renderer.
- **Separate** — a geometric process computing exact 2D from exact 3D; higher quality and clean
  vector output, but a second geometry pipeline to build and keep consistent.

This connects directly to the layer-2 kernel decision: exact 2D derivation is one of the few
places where exact B-rep genuinely earns its cost. See
[`../architecture/layers.md`](../architecture/layers.md).

## Open questions

1. How large is this really? An honest estimate before roadmapping.
2. What is the minimum for an *issuable* drawing, as opposed to a readable one?
3. Do annotations live in the semantic model, in the view, or in a separate document model?
4. What does IFC carry of all this, and what is necessarily ours to own?
