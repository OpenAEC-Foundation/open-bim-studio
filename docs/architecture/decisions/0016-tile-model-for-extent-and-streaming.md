# ADR-0016 — Tile model for unbounded extent and streaming

**Status:** proposed — the choices below are hypotheses until the R-14 spike has run
**Date:** 2026-11-05
**Deciders:** the maintainer

## Context

On 31 October the maintainer decided to design for unbounded extent and streaming together, so the
data model does not rule streaming out; on 5 November they asked for the whole tile model as an ADR
now, with the spike later ([`open-questions.md`](../../open-questions.md), round 2, question 4).

[`domain/spatial-model.md`](../../domain/spatial-model.md) sets out the tile model and its three
hard problems: elements crossing tiles, evaluation across unloaded tiles ([R-14](../../risks.md)),
and precision at the seams. [ADR-0006](0006-f64-local-coordinates-in-tile-frames.md) fixed f64
local coordinates in tile frames; [ADR-0011](0011-hubs-are-order-free-and-keyed-by-element-id.md)
made element id, not position, the key of everything a hub keeps.

The template's rule applies: an ADR with an empty evidence cell stays `proposed`. Nothing below is
measured, so this ADR records the design to test, not a settled one.

## Decision (proposed)

1. **What a tile is.** A tile is a coordinate frame and a unit of loading. It is never a semantic
   boundary: the IFC spatial hierarchy and the tile grid are independent.
2. **Grid.** A fixed square grid per project, anchored at the project's CRS origin. Tile size is a
   project constant, to be chosen from the spike; adaptive subdivision is not used.
3. **Membership.** Every element belongs to exactly one tile, the one holding its placement origin.
   Its geometry may extend beyond the tile (overhang); elements are never split at a boundary.
4. **Persistence.** The tile key is stored with each element, so a file can be read one tile at a
   time.
5. **References across tiles** go by stable element id only (ADR-0011), never by pointer or
   position, so a reference to an unloaded element remains valid.
6. **Loading.** Loading a tile loads its neighbours' boundary elements (a one-tile halo) as
   read-only context. Unloading a tile drops its elements and derived data (ADR-0013); unsaved
   edits block unloading.
7. **Evaluation across unloaded tiles.** A dependency on an element outside the loaded set is
   resolved lazily: the dependent result is marked stale and completed when the tile loads.
8. **Validity.** Saving and exporting require no stale results; the application loads what it
   needs to resolve them first. "The model is always valid" then holds for what is saved and
   exported, not for every in-memory state.
9. **Seams.** Conversions between tile frames are done in f64 and never round-tripped through
   float32; junctions across a seam use the tolerance of ADR-0006.

## Options considered

### Assign-to-one-tile with overhang (proposed)
Keeps the semantic model whole; the overhang bounds the tile's effective size.

### Split elements at tile boundaries
Damages the semantic model, which is the product.

### Large elements outside the grid
A second class of element with its own rules everywhere.

## Evidence

| Claim | Where shown | Evidence type |
|---|---|---|
| A one-tile halo covers most dependencies | — (R-14 spike, `spikes/cross-tile-evaluation/`, not run) | — |
| Lazy, stale-marked evaluation keeps editing responsive | — (R-14 spike, not run) | — |
| f64 tile frames give enough precision | [ADR-0006](0006-f64-local-coordinates-in-tile-frames.md), R-17 | measured |

## Consequences

**What this makes easier:** a single-tile project is the minimum version and needs no paging; the
format is ready for paging from the first file.

**What this makes harder:** every dependency edge must tolerate an unloaded target; save and export
gain a "resolve stale results" step.

**What this commits us to:** running the R-14 spike before multi-tile projects are supported, and
choosing the tile size from it.

**What we would have to change to reverse it:** before multi-tile files exist, only this ADR;
afterwards, the file format.
