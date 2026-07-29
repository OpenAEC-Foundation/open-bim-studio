# Dutch standards and market context

**Decision question: what must the tool support to be usable in Dutch practice?**

## Status: empty — phase 1 artefact

## Why this has its own document

A BIM tool that produces technically valid IFC can still be unusable in a given market. Delivery
agreements, classification systems, and specification conventions are what determine whether a
model is accepted — and they are national.

Dutch practice is the nearest market and the concrete test case. Supporting it well is a
sharper requirement than "supports IFC", and it forces decisions that would otherwise stay
abstract.

Standard names are kept in Dutch; see [`../vision/glossary.md`](../vision/glossary.md).

## To research

**BIM Basis ILS** — the Dutch industry baseline for IFC delivery. Effectively the minimum
acceptance bar. Work out exactly which requirements it places on an authoring tool, and whether
compliance can be validated automatically from within the tool. *Highest priority item here.*

**NLSfB** — classification of building elements, used in specification and take-off. How
classification is assigned, stored, and exported.

**Rvb BIM-norm** — the Government Buildings Agency standard. Relevant for public-sector work.

**STABU** — specification system; the link between model elements and specification text.

**NEN standards** — which are relevant to modelling and drawing production, particularly drawing
conventions, symbols, and line weights.

## Questions

1. What does BIM Basis ILS require of an authoring tool, concretely?
2. Can ILS compliance be checked inside the tool rather than after export? Validation as a
   design feature rather than an afterthought is a genuine differentiator.
3. How is classification carried through the model and into IFC?
4. Which Dutch drawing conventions differ from defaults elsewhere — symbols, hatching, line
   weights, sheet layout? These affect the drawing subsystem directly; see
   [`drawings-from-model.md`](drawings-from-model.md).
5. What do Dutch practices most often complain about in existing tools? Local pain is the most
   actionable kind.

## Scope note

Supporting Dutch practice well is a starting position, not a limit. Keep the mechanisms generic
— classification systems, delivery specifications, and drawing conventions are all *configurable
concepts*, and hard-coding Dutch specifics would be a mistake that is expensive to undo.
