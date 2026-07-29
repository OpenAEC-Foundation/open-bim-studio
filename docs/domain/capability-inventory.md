# Capability inventory

**Decision question: what does "does what a professional BIM tool does" actually consist of, and
in what order do we need it?**

**Status:** first pass — phase 1. Classifications are proposed and need review; the dependency
analysis is the part to scrutinise hardest.

## How to read this

Four classes:

- `core` — the product is not credible without it
- `expected` — users will assume it exists; its absence is a complaint, not a dealbreaker
- `diff` — where we intend to be better than existing tools
- `out` — non-goal; see [`../vision/non-goals.md`](../vision/non-goals.md)

Weight: **S** (days) · **M** (weeks) · **L** (months) · **XL** (a subsystem in its own right)

The **Retrofit** column is the one that pays for this document. It marks capabilities that are
cheap if the data model anticipates them and expensive or impossible to add later:

- 🔴 **structural** — must be decided before the build starts, even if built later
- 🟡 **awkward** — retrofittable, but costly
- ⚪ **additive** — can be added any time

**A capability marked 🔴 must be resolved in the build brief even if it is out of scope for the
MVP.** That is the whole purpose of separating this column from priority.

---

## Modelling

| Capability | Class | Weight | Retrofit | Notes |
|---|---|---|---|---|
| Walls — straight, single layer | core | M | ⚪ | The first vertical slice |
| Walls — compound / layered | core | M | 🟡 | Layer structure affects junctions, sections and take-off |
| Walls — curved, tapered, stacked | expected | M | 🟡 | Curved parametrics are a known weak point in existing tools |
| Wall junctions and cleanup | core | L | 🔴 | Elements must know their neighbours; this is a graph, not a property |
| Floors / slabs | core | M | ⚪ | |
| Roofs — flat and pitched | core | L | 🟡 | Complex roofs are disproportionately hard |
| Columns and beams | core | M | ⚪ | |
| Openings — doors and windows | core | M | 🔴 | Hosted elements: an opening belongs to its host and moves with it |
| Stairs and railings | expected | L | 🟡 | Consistently among the worst-implemented features in every tool |
| Curtain walls | expected | L | 🟡 | Essentially a nested grid system |
| Spaces / rooms / zones | core | M | 🔴 | Boundary derivation from surrounding elements; also the basis of take-off |
| Site and topography | expected | M | ⚪ | Different geometry class — surfaces, not solids |
| Generic / in-place elements | expected | S | 🟡 | The escape hatch; needed early or users hit a wall |
| Free-form modelling | *undecided* | L | 🔴 | See R-07 — the unlocated seam between flexibility and valid IFC |

## Parametric components

| Capability | Class | Weight | Retrofit | Notes |
|---|---|---|---|---|
| Type / occurrence separation | core | M | 🔴 | Forced by IFC anyway. Getting this wrong is unrecoverable |
| Parameter types and validation | core | S | 🟡 | |
| Formulas between parameters | core | M | 🔴 | Requires a dependency graph — see the evaluation row |
| Evaluation and propagation | core | XL | 🔴 | **The heart of the system.** See R-01 |
| Nested components | expected | M | 🔴 | Nesting depth affects the entire evaluation model |
| Geometric constraints | expected | L | 🔴 | Constraint solver or construction rules — decide before building |
| Component libraries and sharing | expected | M | ⚪ | |
| Versioning of definitions | expected | M | 🟡 | What happens to placed instances when a definition changes |
| Visual component authoring | diff | XL | 🟡 | Where we intend to beat existing tools — see prior art on Revit families |
| Scripting escape hatch | *undecided* | L | 🔴 | R-06. Designed in, or bolted on and worse |

## Documentation

The area most likely to be underestimated. See
[`drawings-from-model.md`](drawings-from-model.md) and R-05.

| Capability | Class | Weight | Retrofit | Notes |
|---|---|---|---|---|
| Plans, sections, elevations | core | L | ⚪ | Generating the view is the easy part |
| Cut-face fill and hatching | core | M | 🟡 | Needs material data on the geometry at the cut |
| Hidden-line removal | core | L | 🟡 | Expensive and correctness-critical |
| Level of detail by view scale | expected | M | 🔴 | Elements must carry multiple representations |
| Detail views and callouts | expected | M | ⚪ | |
| **Associative dimensions** | core | L | 🔴 | Needs stable element identity *and* stable reference geometry. The single hardest retrofit in this table |
| Tags reading model data | core | M | 🟡 | |
| Text, leaders, symbols | core | M | ⚪ | |
| Line weights and styles | core | M | 🟡 | By element class and by cut/projected state |
| View-only drafting elements | expected | S | 🟡 | Annotation that exists in one view only |
| View templates | expected | M | 🟡 | |
| Sheets and title blocks | core | M | ⚪ | |
| Revision management | expected | M | 🟡 | |
| Vector export (PDF, DWG) | core | M | ⚪ | Line-weight fidelity is the difficulty |
| Schedules and take-off | expected | M | 🟡 | Cheap if the data model anticipates it |

## Data

| Capability | Class | Weight | Retrofit | Notes |
|---|---|---|---|---|
| **Stable identifiers (GUIDs)** | core | S | 🔴 | Required by IFC round-trip, associative annotation *and* change tracking. Trivial to add now, impossible later |
| Property sets | core | M | 🟡 | Extensibility must be designed, not discovered |
| Classification systems | expected | M | 🟡 | Keep generic — see [`nl-standards.md`](nl-standards.md) |
| Quantities | expected | M | 🟡 | |
| Units and precision | core | S | 🔴 | **The defining constraint, not a setting.** Millimetres over unbounded extent — see [`spatial-model.md`](spatial-model.md) |
| Revisions and change tracking | expected | L | 🔴 | |

## Interoperability

| Capability | Class | Weight | Retrofit | Notes |
|---|---|---|---|---|
| IFC export | core | L | 🟡 | **IFC2x3 first** — see the note below |
| IFC import | core | L | 🟡 | Externally authored models are messier than our own |
| Reference / linked models | core | M | 🔴 | Affects the data model and the renderer |
| Federation and coordination | expected | M | 🟡 | |
| Clash detection | out | — | — | Non-goal; tools exist |
| Round-trip fidelity | core | L | 🔴 | What survives, what is lost, what is documented as lost |

**On IFC version.** Almost all IFC exchange in current practice is still IFC2x3 — a schema
published in 2006 — even though IFC4 and IFC4x3 are supported by 2026 tooling. Targeting IFC4x3
for export while being unable to read what people actually send would be a scoping error made
out of tidiness. **Read IFC2x3 and IFC4 from day one; decide the export target deliberately.**

## Spatial extent and georeferencing

See [`spatial-model.md`](spatial-model.md). Almost entirely 🔴 — a coordinate architecture cannot
be retrofitted, because every stored coordinate would have to be reinterpreted.

| Capability | Class | Weight | Retrofit | Notes |
|---|---|---|---|---|
| **Tiled coordinate architecture** | core | M | 🔴 | 64-bit tile origins, float32 local coordinates. The minimum viable version is one tile and is cheap |
| Georeferencing (CRS + map conversion) | core | S | 🔴 | `IfcMapConversion` + `IfcProjectedCRS`. Projected cartesian CRS only |
| Camera-relative rendering | core | M | 🔴 | Required by the above; avoids GPU double precision |
| Cross-tile element handling | core | M | 🔴 | Elements spanning boundaries — see R-14 |
| Tile paging and eviction | *undecided* | L | 🟡 | **Separable from unbounded extent.** Much more expensive. See R-14 |
| Cross-tile evaluation | *undecided* | L | 🔴 | Only needed if paging is. R-14 |
| Point cloud import | *undecided* | L | 🟡 | Was a non-goal; shares the tiling machinery, so its cost drops |

**The separable question:** unbounded *extent* needs only the tiled coordinate architecture and is
cheap. *Streaming* needs paging, eviction and cross-tile evaluation, and is an order of magnitude
more work. Answer which is required before committing to the second.

## Project organisation

| Capability | Class | Weight | Retrofit | Notes |
|---|---|---|---|---|
| Levels / storeys | core | S | 🔴 | Spatial hierarchy; elements are hosted by level |
| Grids | core | S | 🟡 | |
| Phases | expected | M | 🔴 | Temporal variants in the data model |
| Design options | diff | L | 🔴 | Variant handling. Brutal to retrofit; a genuine differentiator if cheap experimentation is the thesis |
| Worksets / multi-user | out | — | 🔴 | Non-goal, but the data model choice forecloses or preserves it. **Decide knowingly** |

## Editing

Individually small, collectively decisive for whether the tool feels good.

| Capability | Class | Weight | Retrofit | Notes |
|---|---|---|---|---|
| Selection and filtering | core | M | ⚪ | Must scale to 10⁵ elements |
| Copy, array, mirror, rotate | core | M | ⚪ | |
| Align, trim, extend | core | M | ⚪ | |
| Groups and assemblies | expected | M | 🟡 | |
| **Undo / redo** | core | M | 🔴 | Requires a command/transaction architecture from the first line of code |
| Snapping and inference | core | L | 🟡 | See prior art on SketchUp — this is where low-friction modelling comes from |
| Measurement | expected | S | ⚪ | |

---

## The structural decisions

Everything marked 🔴, collected. **These must be settled in
[`../BUILD-BRIEF.md`](../BUILD-BRIEF.md) regardless of what the MVP contains**, because each one
either exists in the data model from the start or never does:

1. **Stable identifiers on everything.** Cheapest item here and the most expensive to add later.
   Three separate capabilities depend on it.
2. **Type/occurrence separation.** Forced by IFC; unrecoverable if wrong.
3. **The evaluation model** — dependency graph, propagation scope, nesting. R-01.
4. **Hosting relationships** — openings in walls, elements on levels, spaces bounded by elements.
5. **Command/transaction architecture** for undo.
6. **Multiple geometric representations per element** for level-of-detail.
7. **Reference geometry for associative dimensions** — dimensions attach to *something*, and that
   something must be stable across parametric change. This is the **topological naming problem**,
   it is unsolved in general parametric CAD, and it affects hosted openings, junctions, tags and
   component versioning as well. Proposed answer: references point at semantic entities, never at
   derived topology. See R-13 and
   [`parametric-components.md`](parametric-components.md#the-reference-problem--decide-this-first).
8. **Units and precision**, globally.
9. **Variant handling** — phases and design options. Even if unbuilt, the data model must not
   foreclose it.
10. **Linked models** in the data model and renderer.
11. **Free-modelling seam** — R-07, still unlocated.
12. **Scripting escape hatch** — R-06, designed in or absent.

## What the first vertical slice needs

From [`../roadmap.md`](../roadmap.md): one wall type, one opening, one storey, one plan, one
section, one parametric component, one IFC export — with changes propagating.

Mapped onto this inventory, that slice requires: straight compound wall · wall junctions ·
hosted opening · level · type/occurrence · formulas · evaluation and propagation · plan and
section generation · cut-face fill · associative dimension · stable identifiers · IFC export ·
undo · snapping.

That is already fourteen capabilities, four of them 🔴 and one XL. **The slice is thin in breadth
and not thin in depth** — which is the point, because it is the chain that carries the
architectural risk. It should not be mistaken for a small amount of work.

## Open questions

1. Which discipline first? This table is architecture-weighted. Structural would reorder it and
   add rebar (XL). Not yet decided.
2. Is `design options` genuinely differentiating, or an expensive distraction? It aligns with the
   cheap-experimentation thesis, which is an argument, not evidence.
3. Where exactly does free-form modelling stop? R-07 remains the largest unresolved scope
   question.

## Sources

- [Almost all IFC exchange in practice is IFC2x3](https://app.bimsupporters.com/courses/ifc/lessons/history-and-versions-of-ifc/)
- [Tekla Structures 2026 — IFC2x3, IFC4 and IFC4.3 export](https://support.tekla.com/doc/tekla-structures/2026/rel_int_enhanced_ifc_interoperability)
- [Pros and cons of parametric Revit families](https://www.majentasolutions.com/news/pros-cons-of-parametric-revit-families---and-when-to-use-them)
