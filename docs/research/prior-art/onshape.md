# Onshape and history-based parametric CAD

**Decision question:** What does mature parametric CAD know about re-evaluating a model after a
change, and which of those problems will we inherit?

**Status:** draft — phase 1
**Last updated:** 2026-07-29

---

## Summary

The most technically consequential note in the prior-art survey. Mechanical CAD has spent three
decades on the problem we are about to walk into, and it has a name: **the topological naming
problem**. It is unsolved in general.

It is not a mechanical-CAD curiosity. It is the reason associative dimensions are hard, the
reason parametric components break when their definitions change, and a direct constraint on our
evaluation architecture. **We should design for it explicitly rather than discovering it in
month four.**

## The topological naming problem

### What it is

A parametric model is a *recipe*, not a shape. Each feature refers to entities produced by
earlier features — "extrude *this face*", "dimension to *that edge*", "place a window on *this
wall face*".

Those references must be stored by name. But the entities they name are **outputs of a
computation**, and when a parameter changes, the computation runs again and may produce a
different set of entities. The face you referred to may have been split into two, merged with a
neighbour, or ceased to exist.

The literature states the problem as identifying entities in an initial parametric model and
matching them in the re-evaluated model — assigning persistent names to entities that "may not
exist or that may cut into different parts" in the new geometry.

### Why it matters to us

The moment geometry is **derived** rather than stored, anything referring to that geometry has
this problem. And our entire architecture is built on geometry being derived — see
[`../../domain/parametric-components.md`](../../domain/parametric-components.md).

Concretely, in our capability inventory:

| Capability | How the problem appears |
|---|---|
| Associative dimensions | The dimension attaches to a face or edge. After a parametric change, is it still the same one? |
| Hosted openings | An opening is placed on a wall face. The wall changes; which face is it now on? |
| Wall junctions | Junction cleanup produces geometry that later operations refer to |
| Component definition versioning | Instances hold references into a definition that has changed |
| Tags and annotation | Anything anchored to model geometry |

This is why associative dimensions were flagged as the single hardest retrofit in
[`../../domain/capability-inventory.md`](../../domain/capability-inventory.md). That instinct now
has a name and a literature.

### How the industry handles it

Nobody has solved it. The strategies are all mitigations:

**Persistent naming schemes.** Name entities by their generative history rather than by index —
"the face created by feature 3 from edge 2" — so names survive re-evaluation where possible.
Considerable literature; partial success.

**Repair rather than prevention.** Onshape's approach is instructive: rather than claiming
robustness, it provides tooling to find and fix broken references, on the stated premise that
repairing features as changes happen "is the nature of parametric, history-based CAD design".

That is an honest admission from a modern, well-resourced system built without legacy
constraints. **If they could have prevented it, they would have.**

**Avoid the problem structurally.** Do not let features refer to derived topology at all. Refer
instead to *stable abstractions* — a wall's centreline, a level, a grid intersection, a named
parameter — which are inputs rather than outputs and therefore do not move under re-evaluation.

### The strategy this suggests for us

The third option is more available to us than to mechanical CAD, and this is the useful insight
of the note.

Mechanical CAD must let users select arbitrary faces, because a machined part has no vocabulary
beyond its topology. **A building does.** Walls have centrelines, faces have sides, storeys have
levels, grids have intersections, openings have hosts. These are semantic references that exist
in the model *independently of the geometry produced from them*.

> **Proposed principle: references point at semantic entities and their named features, never at
> derived topology.** A dimension attaches to "the inner face of wall W12", not to "face 7 of
> solid 3".

This is a real advantage of building a domain-specific modeller rather than a general one — and
it is only available if the data model is designed for it from the start. It is exactly the kind
of decision that must be in the build brief.

It is not free. It constrains what users can dimension to and what components can reference, and
the boundary between "expressible semantically" and "requires raw topology" is not yet located.
Anything falling outside inherits the full problem.

## Feature history versus direct modelling

The second lesson. History-based parametric CAD replays a recipe; direct modelling edits geometry
in place. History gives you parametric power and the naming problem; direct modelling gives you
freedom and no update semantics.

This is the same tension as R-07 — the unlocated seam between free modelling and semantic
validity — arriving from a different direction. **Two independent lines of enquiry landing on the
same boundary is evidence the boundary is real** and needs an explicit decision rather than a
compromise.

## What else transfers

- **Constraint solvers are mature technology.** 2D sketch solvers are well understood and
  adopting one is a realistic option. Relevant to the undecided constraint question in the
  capability inventory.
- **Cloud-native architecture** — noted and out of scope; see
  [`../../vision/non-goals.md`](../../vision/non-goals.md).
- **Repair tooling as a product feature.** If breakage is inevitable, making it visible and
  fixable beats pretending it will not happen. Worth considering rather than dismissing as an
  admission of defeat.

## Verdict

Adopt the semantic-reference principle; treat the topological naming problem as a first-class
architectural constraint rather than an implementation detail.

Requirements from this note:

1. **References point at semantic entities, not derived topology.** 🔴 structural — this must be
   in the data model from the start.
2. **Locate the boundary** where semantic references are insufficient, and decide what happens
   beyond it. Ties to R-07.
3. **Assume some breakage** and plan for visible, repairable failure rather than silent
   corruption.
4. Evaluate an existing 2D constraint solver rather than writing one — phase 2.

New risk R-13 records this.

## Sources

- [Tackling history-based errors in parametric CAD](https://www.onshape.com/en/blog/tackling-history-based-errors-parametric-cad-repair-manager)
- [A mechanism for persistently naming topological entities in history-based parametric solid models](https://www.sciencedirect.com/science/article/abs/pii/S0010448596000401)
- [Mechanisms of persistent identification of topological entities in CAD systems: a review](https://www.sciencedirect.com/science/article/pii/S1110016818300814)
- [Identification of topological entities and naming mapping for parametric CAD model exchange](https://koreascience.kr/article/JAKO200503018236985.page)
