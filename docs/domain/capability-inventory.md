# Capability inventory

**Decision question: what does "does what a professional BIM tool does" actually consist of, and
in what order do we need it?**

This document turns an unbounded ambition into a countable list. Until it exists, scope
discussions have nothing to be about and phase 4 cannot happen.

## Status: empty — phase 1 artefact

The structure below is the shape to fill, not the content.

## Method

1. **Enumerate**, discipline by discipline. Comparison against existing tools is legitimate here
   — see the naming note in [`../research/prior-art/README.md`](../research/prior-art/README.md).
2. **Classify** each capability:
   - `core` — the product is not credible without it
   - `expected` — users will assume it exists
   - `differentiating` — where we intend to be better
   - `out` — a non-goal; move it to [`../vision/non-goals.md`](../vision/non-goals.md)
3. **Estimate** implementation weight: small / medium / large / subsystem.
4. **Note dependencies.** Many capabilities are cheap if anticipated in the data model and
   expensive to retrofit. Flag those — they are the ones that must be decided before the build,
   even if they are not built first.

Step 4 is the one that pays for this document.

## Table format

| Capability | Class | Weight | Depends on | Notes |
|---|---|---|---|---|
| | | | | |

## Areas to cover

**Modelling** — walls, floors, roofs, columns, beams, stairs, railings, curtain walls, openings,
site and topography, spaces and zones.

**Parametric components** — component definition, type vs. occurrence, nested components,
parameter types, formulas, constraints, libraries and reuse.

**Documentation** — plans, sections, elevations, details, schedules, sheets, annotation,
dimensioning, tagging, hatching, line weights, view templates, title blocks, printing and
export.

**Data** — property sets, classification, quantities, identifiers, revisions.

**Interoperability** — IFC import and export, reference models, federation, coordination,
change tracking.

**Project organisation** — levels, grids, phases, design options, worksets or equivalent.

**Editing** — selection, filtering, copy/array/mirror, alignment, grouping, undo.

## Prioritisation

The first vertical slice is defined in [`../roadmap.md`](../roadmap.md) — the whole chain,
minimally, rather than any area broadly. Use this inventory to decide what comes after that
chain works.

The ordering question that matters: **which capabilities are cheap now and expensive later?**
Those go early regardless of user-facing priority.
