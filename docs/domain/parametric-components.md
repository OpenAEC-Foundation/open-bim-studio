# Parametric components

**Decision question: how are components defined, and can a modeller build one without writing
code?**

## Status: empty — phase 1 artefact

## Why this is central

This is what separates a BIM tool from a 3D modeller. A wall is not geometry that happens to be
wall-shaped: it is a definition that *produces* geometry from parameters, and reproduces it when
those parameters change.

Two consequences shape the whole architecture:

1. **Geometry is derived, not stored.** The source of truth is the parametric definition. This
   is what makes coordination possible — and what makes evaluation cost the central performance
   question.
2. **The component system is a language**, whether or not it is designed as one. Users will push
   it further than intended. An accidental language is worse than a designed one.

## What to work out

**The component model** — what a definition contains; the type/occurrence split (which IFC
already forces, see [`ifc-data-model.md`](ifc-data-model.md)); nesting and composition;
parameter types and validation; formulas and dependencies between parameters.

**Evaluation** — when re-evaluation is triggered; the dependency graph between components;
propagation to neighbours (a wall changes, its openings and junctions follow); ordering and cycle
handling; caching.

*This is where R-01 bites. Evaluation cost determines whether continuous feedback is possible,
and continuous feedback is the interaction thesis.*

**Authoring** — how a user creates a component; the boundary between visual authoring and
scripting; libraries, sharing, and versioning.

**Constraints** — whether components use a constraint solver or fixed construction rules. Sketch
solvers are well-understood technology; adopting one is a real option and a real dependency.

## The escape-hatch question

"No code required" is the goal. It may not survive real component libraries — every parametric
system of consequence eventually grows a scripting layer.

The decision that matters is not whether to have one, but **whether it is designed in from the
start or bolted on**. Bolted-on scripting layers are consistently worse: they see a data model
that was not built to be addressed programmatically.

Tracked as R-06. Decide in phase 4.

## Open questions

1. Visual authoring, scripting, or both — and if both, where is the boundary?
2. Constraint solver or construction rules?
3. How far does propagation reach? A wall's openings, certainly. Adjoining walls? Their
   openings? Where does it stop, and is that a rule or a graph traversal?
4. How are components versioned when a definition changes under existing instances?
5. Can evaluation be incremental enough for continuous feedback? See R-01.
