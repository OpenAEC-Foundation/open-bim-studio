# IFC data model

**Decision question: how much of IFC do we adopt as our internal model, and where do we
deliberately diverge?**

## Status: empty — phase 1 artefact

## Why this is a decision and not a given

Three positions, with very different consequences:

**IFC as the internal model.** Round-trip fidelity is guaranteed and exchange is trivial. But
IFC is an exchange schema, not an editing schema: it is verbose, its parametric support is
limited, and it was not designed for interactive modification.

**Our own model, IFC at the boundary.** Optimised for editing and evaluation, translated on
import and export. Better interactively; every translation is a chance to lose information.

**Hybrid.** Our model holds the parametric and editing state; IFC entities are retained
alongside for fidelity. More memory, more complexity, less loss.

The choice is coupled to the layer-1 kernel decision — a semantic kernel that already holds an
IFC model pulls toward the first option. See [`../architecture/layers.md`](../architecture/layers.md).

## What to write up

Only to the depth we actually need. This is not a re-statement of the specification.

**Structure** — entity model and inheritance; the spatial hierarchy (project → site → building →
storey → space); the relationship objects that carry most of the meaning.

**Type vs. occurrence** — IFC separates component definition from placed instance. This maps
directly onto a parametric component system, and getting it wrong is expensive to correct later.
*Cover this properly; it is the entry most likely to be load-bearing.*

**Geometry representation** — the representation types IFC allows (swept solids, B-rep,
tessellation, CSG), which ones we produce, and what each costs.

**Properties** — property sets, standard versus custom, quantities, classification.

**Schema versions** — IFC2x3 versus IFC4 versus IFC4x3; what is still required in practice
versus what is current.

**Known pain points** — where IFC is ambiguous, where implementations disagree, where round
trips lose information. This section is worth more than the descriptive ones.

## Open questions

1. Which schema version do we target for export, and which must we read?
2. Does IFC's parametric support cover our component model, or must we carry parametrics
   outside it?
3. What do we lose on a round trip, and is that acceptable?
4. How do drawings and annotation relate to IFC — what does it carry, and what is ours?
   See [`drawings-from-model.md`](drawings-from-model.md).

## Sources

- [IfcOpenShell](https://ifcopenshell.org/)
- buildingSMART IFC specifications
