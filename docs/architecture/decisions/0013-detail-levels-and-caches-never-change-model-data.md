# ADR-0013 — Detail levels and caches never change model data

**Status:** accepted
**Date:** 2026-10-31 (decided in #76 and #77, recorded here)
**Deciders:** the maintainer

## Context

Large models need representations chosen per view: round shapes meshed to the zoom, coarse proxies
for building systems far away (#76), analytic rendering of connection details (#77). Each of these
keeps derived data. If any of it flows back into the model, what the user sees decides what is
saved and exported.

## Decision

Detail levels, proxies, tessellations and caches are derived, view-side data. They never change
the native model or what is written to IfcX or IFC. Export and save always work from the model
itself, never from a representation chosen for display.

## Options considered

### Display-only derived data (chosen)
The model stays the single source; a cache can be thrown away at any time.

### Caching exported representations in the model
Faster export, but the exported geometry would depend on the last zoom level.

## Evidence

| Claim | Where shown | Evidence type |
|---|---|---|
| Meshes are reused per element id and serial between frames | #76, the viewer owner's assessment of `main` 4c341b5 | claimed (code reading) |
| The rule was decided in the issues | #76, #77 | claimed (issue comments) |

## Consequences

**What this makes easier:** detail and caching can change freely without touching exchange.

**What this makes harder:** a slow derivation cannot be "saved" into the model to speed up the
next export.

**What this commits us to:** tests that export the same model at different view states and compare
the files.

**What we would have to change to reverse it:** a new ADR, and versioning cached representations in
the file format.
