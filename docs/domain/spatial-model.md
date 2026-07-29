# Spatial model: georeferencing, tiling and precision

**Decision question: how does the model stay millimetre-accurate while covering unbounded
geographic extent?**

**Status:** first pass — phase 1. Added after the requirement that the tool also behave as a
tile-based, GIS-like database supporting effectively unbounded coordinates.

---

## The reframe: you never want large coordinates

The requirement is usually stated as "support infinitely large coordinates". The correct
implementation is the opposite: **never let a coordinate get large.**

Large coordinates and fine precision are mutually exclusive in floating-point arithmetic. Accuracy
halves for every power of two away from the origin. At Earth's radius — about 6,371 km — a 32-bit
float resolves roughly **0.38 metres**. For a tool that must hold millimetres over hundreds of
metres, that is not a degradation; it is total failure. Objects far from the origin visibly
vibrate as positions snap to the nearest representable value.

So unbounded extent is achieved by having **many local origins**, not one distant one. Every
coordinate stays small because it is measured from a nearby reference point. The reference points
themselves are held in high precision.

That is what tiling is *for*. It is a precision strategy first and a streaming strategy second.

## IFC already does this — and it is the strongest argument for the approach

IFC's georeferencing model is precisely this pattern, which is a useful confirmation that the
approach is not exotic.

`IfcMapConversion` combined with `IfcProjectedCRS` describes how a model's **local engineering
coordinate system** sits within a real-world projected CRS:

| Field | Meaning |
|---|---|
| `Eastings`, `Northings`, `OrthogonalHeight` | Where the local origin sits in the projected CRS |
| `XAxisAbscissa`, `XAxisOrdinate` | Rotation from local axes to CRS axes |
| `Scale` | Unit conversion into the CRS |

The model itself stays in local coordinates near its own origin. Georeferencing is **metadata
describing where that local frame sits** — the model is never re-expressed in world coordinates.

This is exactly the floating-origin pattern, standardised, and it means our tiling design and IFC
export are aligned by construction rather than by translation.

Two constraints come with it:

- **Only projected, cartesian CRS are permitted.** No geographic (latitude/longitude) coordinate
  systems. Reprojection happens outside the model.
- **IFC2x3 has no native support.** The same information is carried in `ePset_MapConversion` and
  `ePSet_ProjectedCRS` property sets on `IfcSite` — a convention, not a schema feature. Since
  almost all real exchange is still IFC2x3 (see
  [`capability-inventory.md`](capability-inventory.md)), **georeferencing degrades on the format
  people actually use.** This tension is real and needs an explicit decision.

IfcOpenShell exposes a georeferencing API, which is a further point in favour of the layer-1
hypothesis in [`../architecture/layers.md`](../architecture/layers.md).

## Proposed architecture

### Three coordinate frames, kept distinct

| Frame | Storage | Purpose |
|---|---|---|
| **Geographic / projected CRS** | 64-bit, per project | Where the project is on Earth |
| **Tile origin** | 64-bit, per tile | Anchor for a region of the model |
| **Local coordinates** | 32-bit, relative to tile origin | Everything geometric |

Geometry is authored, stored and evaluated in **local** coordinates only. A tile a few hundred
metres across keeps float32 precision far below a millimetre. Extent becomes unbounded because
tiles are unbounded in number, not because any single coordinate is large.

### Rendering

Camera-relative. Compute the transform from tile origin to camera in doubles on the CPU, hand the
GPU a small float offset. Standard practice in geospatial and large-world rendering, and it
avoids GPU double precision entirely — which matters, because GPU doubles are slow or absent.

Depth precision needs separate attention; it is already flagged in
[`../research/renderers/README.md`](../research/renderers/README.md).

### What a tile is — and is not

**A tile is a coordinate frame and a unit of paging.** It is *not* a semantic boundary. A
building belongs to a site and a storey; it does not belong to a tile. The IFC spatial hierarchy
and the tile grid are **independent decompositions of the same model**, and conflating them would
be a serious error — it would make the tile grid visible in the data model, where it does not
belong.

## Where this gets hard

Three genuine problems, honestly stated.

### Elements that cross tile boundaries

A retaining wall, a road, a long beam. Options: assign to one tile and allow geometry to extend
beyond it; split geometry at the boundary; or maintain a separate class of large elements outside
the tile grid.

None is clean. Splitting damages the semantic model, and the semantic model is the product.
**Assign-to-one-tile with overhang is probably right**, since tiles are a coordinate and paging
concept rather than a containment one — but the overhang bounds the tile's effective size and
therefore its precision guarantee.

### Evaluation across unloaded tiles — the serious one

This is where the requirement collides with existing architecture.

Our parametric evaluation depends on a dependency graph: a wall changes, its openings and
junctions follow. **Tiling means parts of that graph may not be in memory.** If a wall's neighbour
lives in an unloaded tile, we cannot evaluate the junction without loading it — and if we always
load it, the paging is not doing its job.

This directly threatens R-01, which is already the critical risk. Recorded as R-14.

Plausible mitigations, none yet evaluated: dependency edges are mostly spatially local, so a
one-tile halo may suffice; cross-tile dependencies could be resolved lazily and marked stale;
evaluation could be deferred for unloaded regions and completed on load. **All three change what
"the model is always valid" means**, which is a claim the drawing and export subsystems currently
rely on.

### Precision at the seams

Two elements in adjacent tiles that must meet exactly are expressed relative to different
origins. The conversion between them is exact in doubles, but any float32 round-trip introduces
error at exactly the place users inspect most closely — the junction. Tolerance handling at tile
boundaries needs to be explicit.

## Consequences for existing decisions

| Document | Change |
|---|---|
| [`capability-inventory.md`](capability-inventory.md) | Georeferencing, tiling and paging added as 🔴 structural |
| Units and precision | Escalated: this is now the *defining* constraint, not a global setting |
| [`../research/kernels/README.md`](../research/kernels/README.md) | Numeric precision becomes an evaluation criterion — a kernel that works only in float32 is disqualified |
| [`../research/renderers/README.md`](../research/renderers/README.md) | Camera-relative rendering becomes a requirement, not an option |
| [`../vision/non-goals.md`](../vision/non-goals.md) | Point cloud import moves closer to scope — it shares the tiling and paging machinery |
| IFC version strategy | IFC4x3 gains weight: it was extended for infrastructure, which is where geographic extent actually matters |

That last row is a genuine tension with the phase 1 finding that almost all real exchange is
IFC2x3. **Geographic ambition pulls toward IFC4x3; interoperability reality pulls toward IFC2x3.**
This needs an explicit decision rather than a default.

## Scope warning

This requirement is larger than it appears. A tile-based, georeferenced, paged spatial database is
a substantial subsystem, and combining it with BIM authoring is more than either on its own.

It is also **structural** — it cannot be retrofitted. A model built around a single origin with
float32 coordinates cannot later become a tiled one; every stored coordinate would have to be
reinterpreted.

So the honest position: **decide it now, build it early in a minimal form, do not defer it.** The
minimum viable version is a single tile with a 64-bit origin and a documented `IfcMapConversion`.
That is cheap, and it means the coordinate architecture is right from the first line of code even
though paging and multi-tile evaluation come much later.

## Open questions

1. Tile size? Trades precision headroom against paging granularity and cross-boundary frequency.
2. Fixed grid or adaptive subdivision?
3. Does the tile grid appear in the persistence format, or is it derived on load?
4. How do cross-tile dependencies evaluate, and what does "valid model" mean when part is
   unloaded? R-14.
5. IFC4x3 or IFC2x3 as the export target, given the georeferencing gap?
6. Is *streaming* required, or only unbounded extent? These are separable, and the second is much
   cheaper.

Question 6 is worth answering first. **Unbounded extent needs only a tiled coordinate
architecture. Streaming needs paging, eviction, and cross-tile evaluation** — an order of
magnitude more work. The requirement as stated may only need the first.

## Sources

- [IfcMapConversion — IFC 4.3 documentation](https://ifc43-docs.standards.buildingsmart.org/IFC/RELEASE/IFC4x3/HTML/lexical/IfcMapConversion.htm)
- [How to georeference a BIM model](https://medium.com/@stijngoedertier/how-to-georeference-a-bim-model-1905d5154cfd)
- [Coordinating IFC models with world coordinate system information](https://helpcenter.bimcollab.com/en/articles/326917-coordinating-ifc-models-with-world-coordinate-system-information)
- [ifcopenshell.api.georeference](https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/georeference/index.html)
- [Floating origin](https://en.wikipedia.org/wiki/Floating_origin)
- [Emulating double precision on the GPU to render large worlds — Godot](https://godotengine.org/article/emulating-double-precision-gpu-render-large-worlds/)
- [Large worlds — Flax documentation](https://docs.flaxengine.com/manual/editor/large-worlds/index.html)
- [GeoBIM benchmark: reference study of IFC software support](https://arxiv.org/pdf/2007.10951)
