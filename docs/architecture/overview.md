# Architecture overview

**Decision question: what are the components of this system, and how do they fit together?**

## Status: empty — phase 4 artefact

This document is written once the research is done and the ADRs are accepted. Writing it earlier
would freeze decisions that have not been made.

What exists now:

- [`layers.md`](layers.md) — the layered view and the working hypothesis, written to be
  falsified rather than followed.
- [`decisions/`](decisions/) — decisions that are actually settled.

## What this will contain

**Component structure.** The parts of the system, each with one clear responsibility, and the
interfaces between them. The test: can each part be understood without reading the internals of
the others, and can its internals change without breaking consumers?

**Data flow.** How a user action becomes a model change, geometry, a redraw, and updated
drawings. The flow that matters most:

```
user action → parametric change → evaluation → geometry → render
                                       ↓
                                  2D derivation → drawings
                                       ↓
                                  IFC export
```

**The evaluation system.** How change propagates, what triggers re-evaluation, and how the
dependency graph is maintained. This is the heart of the system and the main performance risk.

**Persistence.** Native format, IFC relationship, versioning.

**Threading.** What runs off the UI thread, and how that boundary is enforced.

**Extension points.** What is pluggable and what is fixed — decided deliberately rather than
discovered.

## Constraints already known

These come from the vision and non-goals and are not open for rediscovery:

- **10⁵–10⁶ elements interactive.** A requirement, not a stretch goal.
- **Geometry is derived from parametric definitions**, not stored as the source of truth.
- **Drawings are coordinated with the model** — that is the definition of the product.
- **IFC exchange without meaningful loss.**
- **Continuous feedback during interaction**, if R-01 permits it. If it does not, the interaction
  thesis changes and this document must say so explicitly rather than quietly degrade.
