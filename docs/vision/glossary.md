# Glossary

**Decision question: which terms do we use, in which sense, so that documents and future code
agree?**

Ambiguous vocabulary is expensive. "Kernel" alone has caused enough confusion to justify this
document — see the first entry.

Dutch terms are kept where the Dutch is the accurate term (national standards, regulatory
concepts). Everything else is English.

## Architecture terms

**Kernel** — dangerously overloaded. This repository always qualifies it:
- **Semantic kernel** — the layer that knows what a wall *is*: IFC schema, entities, property
  sets, relationships.
- **Geometry kernel** — the layer that computes shapes: solids, booleans, tessellation.
- **Host** — the application or engine providing viewport, UI, and distribution.

Never write "the kernel" unqualified. See [`../architecture/layers.md`](../architecture/layers.md).

**B-rep (boundary representation)** — a solid described by its exact bounding faces, edges, and
vertices, with curved surfaces represented analytically. Exact but computationally heavy.

**Mesh** — a solid approximated by triangles. Fast and simple; exactness is lost.

**Manifold mesh** — a mesh that bounds a well-defined solid: every edge borders exactly two
faces, no self-intersections, no holes. Non-manifold results are the classic failure mode of
mesh boolean operations.

**Boolean operation** — union, difference, or intersection of solids. Cutting a window opening
out of a wall is a boolean difference. Robustness here is a core technical risk.

**Tessellation** — converting exact geometry into a mesh for display.

**Parametric object** — an element defined by parameters and rules rather than by fixed
geometry. Its geometry is *derived*, and re-derived when parameters change.

**Evaluation / re-evaluation** — recomputing derived geometry after a change. The cost and
scope of re-evaluation is the central performance question of the whole system.

**Constraint solver** — a component that satisfies geometric relationships (parallel,
perpendicular, distance) rather than storing fixed coordinates. Standard in sketch-based CAD.

## BIM terms

**IFC (Industry Foundation Classes)** — the open, vendor-neutral data model for building
information. The exchange format we commit to. See
[`../domain/ifc-data-model.md`](../domain/ifc-data-model.md).

**IFC4x3** — the current major schema generation, extending coverage to infrastructure.

**Property set (Pset)** — a named group of properties attached to an IFC entity. The main
carrier of non-geometric information.

**Type object vs. occurrence** — IFC separates the definition of a component from each placed
instance of it. This distinction maps directly onto how a parametric component system must be
built, and getting it wrong is expensive.

**Spatial structure** — the containment hierarchy: project → site → building → storey → space.
Every physical element lives somewhere in it.

**Federated model** — several discipline models referenced together rather than merged into one
file.

**LOD (Level of Development / Detail)** — how much information an element carries at a given
project stage. Note the two competing expansions; state which is meant.

**Take-off** — deriving quantities from the model.

## Drawing terms

**View** — a derived 2D representation of the model: plan, section, elevation, detail.

**Cut plane** — the plane at which a plan or section slices the model. What is cut, what is
seen beyond, and what is hidden are separate questions with separate rules.

**Annotation** — drawing content that is not model geometry: dimensions, tags, text, symbols,
hatching. The bulk of the work in producing an issuable drawing.

**Coordination** — the guarantee that every view reflects the current model. The property that
distinguishes a BIM tool from a 3D modeller with a section tool.

## Dutch standards and context

**NLSfB** — Dutch classification system for building elements, widely used in specifications and
take-off.

**BIM Basis ILS** — *Informatie Leverings Specificatie*; the Dutch industry baseline agreement
for IFC delivery. Effectively the minimum bar for exchange acceptance in Dutch practice.

**Rvb BIM-norm** — the Dutch Government Buildings Agency BIM standard.

**STABU** — Dutch specification system for construction works.

**NAP** — *Normaal Amsterdams Peil*; the Dutch national height datum. Level heights in Dutch
drawings are given relative to it ("peil = NAP +5.420").

**RD** — *Rijksdriehoeksmeting*; the Dutch national grid for x/y coordinates (EPSG:28992).
Together with NAP it is the local coordinate reference system a Dutch project is georeferenced
in (IfcProjectedCRS with IfcMapConversion).

**Stramien** — the structural grid of a building: the lettered and numbered grid lines
(IfcGrid, IfcGridAxis). English text uses "grid"; the Dutch word appears in the maintainers'
requests.

**KW and FB coding** — two Dutch coding schemes for window frames (*kozijnen*) on drawings and in
frame schedules. Which convention or standard each refers to is still to be confirmed (issue #68);
until then the terms are named, not defined.

See [`../domain/nl-standards.md`](../domain/nl-standards.md).

## Terms we avoid

- **"The kernel"** unqualified — see above.
- **"Real-time"** without a number — state the target frame rate and model size.
- **"Large model"** without a number — state the element count.
- **"Like Revit"** as a requirement — name the specific capability instead. Comparison is fine
  in prior-art analysis; it is not a specification.
