# Parametric components

**Decision question: how are components defined, and can a modeller build one without writing
code?**

**Status:** first pass — phase 1. The reference model and the two-path proposal are the settled
parts; evaluation mechanics are still open.

The [Building System Generator proposal](building-system-generator.md) develops the layered,
recursive construction case: domains, patterns, overrides, component interfaces and stock
planning. Its delivery matrix distinguishes implemented behaviour from proposed contracts.

## Why this is central

This is what separates a BIM tool from a 3D modeller. A wall is not geometry that happens to be
wall-shaped: it is a definition that *produces* geometry from parameters, and reproduces it when
those parameters change.

Two consequences shape the whole architecture:

1. **Geometry is derived, not stored.** The source of truth is the parametric definition. This is
   what makes coordination possible — and it is also what creates the reference problem below.
2. **The component system is a language**, whether or not it is designed as one. Users will push
   it further than intended. An accidental language is worse than a designed one.

---

## The reference problem — decide this first

**The topological naming problem** is the central technical constraint on this subsystem, and it
is unsolved in general parametric CAD. Full analysis in
[`../research/prior-art/onshape.md`](../research/prior-art/onshape.md); risk R-13.

In short: a parametric model is a recipe, and features refer to entities that earlier features
*produced*. When parameters change, those entities may be split, merged, or destroyed — and every
reference to them is now pointing at something that may not exist.

This affects associative dimensions, hosted openings, wall junctions, tags, and component
versioning. It is not a detail; it is the reason those capabilities are hard.

### Proposed principle

> **References point at semantic entities and their named features, never at derived topology.**
>
> A dimension attaches to "the inner face of wall W12", not "face 7 of solid 3". An opening hosts
> on "wall W12, exterior side", not on a computed face.

Semantic entities are *inputs* to evaluation, not outputs, so they survive re-evaluation by
construction.

This option is more available to us than to mechanical CAD, and it is the clearest architectural
advantage of building a domain-specific modeller. A machined part has no vocabulary beyond its
topology. **A building does** — centrelines, sides, levels, grid intersections, hosts.

It is not free. It constrains what users can dimension to and what components can reference. The
boundary between "expressible semantically" and "requires raw topology" is not yet located, and
anything outside it inherits the full problem. That boundary is R-13, and it is the same boundary
R-07 approaches from the free-modelling side — **two independent lines of enquiry reaching the
same place, which is evidence it is real.**

---

## Authoring: two paths, deliberately separated

The main proposal of this document, and our claimed differentiator. Derived from
[`../research/prior-art/rhino-grasshopper.md`](../research/prior-art/rhino-grasshopper.md) and
[`../research/prior-art/revit.md`](../research/prior-art/revit.md).

**The problem in every existing tool:** authoring a component is a separate environment with
different rules, in which a competent modeller is a beginner. This is true of family editors and
equally true of visual programming — visual programming removes *syntax*, which was never the
hard part. Decomposing a problem into operations on data is programming whether you type it or
draw it.

**The distinction that resolves it:**

| Task | Path |
|---|---|
| "The frame width is a parameter, and the sill follows the wall thickness" | **Gestural parameterisation** — the common case |
| "Generate a facade layout from a surface with attractor-driven variation" | **Computational graph** — the exceptional case |

The first is roughly 95% of components in practice. It is *parameterising a model you already
made* — a modelling activity, expressible with modelling gestures, and it should never require a
graph.

The second is genuine computation and no gestural interface will express it.

> **Position: gestural parameterisation as the primary path; a computational graph as an escape
> hatch, entered deliberately.** Not one system stretched to cover both, and not everyone pushed
> down the programming route.

This answers R-06: the escape hatch is needed, but it must be secondary. Making it primary is
precisely where the incumbents went wrong.

**Status: this is a position, not a design.** How gestural parameterisation actually works is
unspecified and is the most important open design question in the project — it is the
differentiator. Phase 4.

---

## Still to work out

**The component model** — what a definition contains; the type/occurrence split (forced by IFC
anyway, see [`ifc-data-model.md`](ifc-data-model.md)); nesting and composition; parameter types
and validation; formulas and dependencies between parameters.

**Evaluation** — when re-evaluation triggers; the dependency graph between components;
propagation to neighbours (a wall changes, its openings and junctions follow); ordering and cycle
handling; caching.

*This is where R-01 bites. Evaluation cost determines whether continuous feedback is possible,
and continuous feedback is now confirmed as the mechanism the whole interaction thesis rests on —
three independent prior-art notes reached it separately.*

**Constraints** — constraint solver or fixed construction rules. 2D sketch solvers are mature
technology and adopting one is realistic; evaluate rather than build in phase 2.

**Definition versioning** — what happens to placed instances when a definition changes. Directly
exposed to R-13.

## Open questions

1. **How does gestural parameterisation actually work?** The differentiator, currently an
   assertion. Highest-value open design question in the repository.
2. Where is the boundary beyond which semantic references are insufficient? R-13.
3. How far does propagation reach? A wall's openings, certainly. Adjoining walls? Their openings?
   Is that a rule or a graph traversal?
4. Constraint solver or construction rules?
5. Can evaluation be incremental enough for continuous feedback? R-01.
