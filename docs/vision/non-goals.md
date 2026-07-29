# Non-goals

**Decision question: what are we explicitly not building?**

At this level of ambition, what gets crossed out determines feasibility more than what gets
written down. A scope that is only additive is not a scope.

This document is deliberately aggressive. Items can be promoted back into scope later, but only
by an explicit decision — never by drift.

## Status: draft — needs a working session

The entries below are proposed, not settled. Each needs a decision before phase 4.

## Proposed non-goals

### Analysis and calculation
We do not perform structural, energy, acoustic, or any other engineering analysis. We produce a
model that analysis tools can consume. *Rationale: each of these is a product in its own right,
and the exchange formats already exist.*

### Photorealistic rendering
Real-time viewport quality yes; offline path-traced production rendering no. Export to
dedicated visualisation tools instead. *Rationale: the visualisation market is well served and
the engineering cost is enormous.*

### Full IFC schema coverage on day one
IFC4x3 is vast. We support the subset our capability inventory requires, correctly, rather than
the whole schema, badly. *Rationale: partial-but-correct exchange is usable; broad-but-lossy is
not.*

### Being a general 3D modeller
Free-form and organic modelling is not the target even though the interaction model borrows
from tools that do it. We model buildings. *Open question: where exactly is this line? This is
the seam flagged in [`vision.md`](vision.md) and it is not yet located.*

### Multi-user real-time collaboration
Not in the first version. File-based exchange and version control first. *Rationale: real-time
collaboration constrains the entire data model architecture; committing to it early would
dominate every other decision.*

### Cloud platform, model server, common data environment
Desktop application. Integration with existing platforms via IFC, not replacement of them.

### Backwards compatibility with proprietary file formats
We read and write IFC. We do not reverse-engineer proprietary native formats. *Rationale:
legally fraught, permanently chasing a moving target.*

### Migration path from existing tools
No template converters, no family/object library migration, no view-template translation. Users
start fresh or import via IFC. *Rationale: this is where enormous effort goes to die.*

## Candidates that need a decision

These are genuinely undecided and each materially changes the architecture:

| Candidate | Why it matters |
|---|---|
| Scripting / visual programming for parametrics | Determines whether the parametric system is a closed component model or an open computational one |
| Quantity take-off and scheduling | Cheap if the data model anticipates it, expensive to retrofit |
| Point cloud import | Affects the renderer and spatial data structures profoundly |
| Rebar and detailed structural modelling | Very high effort; only in scope if structural is the first discipline |
| MEP systems | Network topology is a different data model than building elements |
| Drawing annotation depth | The gap between "generates a section" and "produces an issuable drawing" is much larger than it appears — see [`../domain/drawings-from-model.md`](../domain/drawings-from-model.md) |

## The test for adding anything back

Before promoting a non-goal into scope, answer: *does the core loop — parametric object →
geometry → drawing → IFC, with changes propagating — work end to end without it?*

If yes, it stays out until that loop is proven.
