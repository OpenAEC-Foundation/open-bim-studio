# Kernels — evaluation method and candidates

**The decisive research area.** Everything downstream is speculation until this is settled.

Read [`../../architecture/layers.md`](../../architecture/layers.md) first: "kernel" covers two
independent layers, and conflating them wastes effort.

## Weighting matrix

Every candidate is scored on the same axes. Record unknowns as unknown.

| Criterion | Why it matters | Weight |
|---|---|---|
| **License** | LGPL / MPL / commercial — determines whether open-sourcing later is possible | High |
| **IFC coverage** | Schema versions supported; round-trip loss | High (layer 1) |
| **Geometry model** | Exact B-rep vs. mesh; boolean robustness; NURBS support | High |
| **Incremental evaluation** | Can it re-evaluate one changed element, or only convert in batch? | **Critical** |
| **Numeric precision** | 64-bit internally? A kernel that works only in float32 is **disqualified** — see [`../../domain/spatial-model.md`](../../domain/spatial-model.md) | **Critical** |
| **Performance** | Load time and memory at 10k / 100k / 1M elements | High |
| **Embeddability** | Language bindings, WASM, native, threading model | High |
| **2D derivation** | Section and projection support, hidden-line removal | Medium |
| **Maturity** | Community, release cadence, bus factor | Medium |
| **AI familiarity** | Volume of public code and documentation — see note below | Medium |

### On incremental evaluation

This is weighted critical because it is the axis most likely to be silently fatal. A kernel that
converts a whole model quickly but cannot cheaply re-evaluate a *single changed element* is a
viewer engine, not a modeller engine. Most IFC tooling was built for the viewing case, so this
capability is often absent and rarely documented.

**Test it explicitly for every candidate.** Do not infer it from load-time benchmarks.

### On AI familiarity

The build strategy depends on AI assistance, so how well models know a stack genuinely affects
delivery speed. It is a legitimate criterion.

It is also a trap: it rewards popularity over fitness. It is one column, not the matrix. A
kernel that is a poor technical fit does not become a good one by being well documented.

## Benchmark set

Defined once in [`../../../reference/`](../../../reference/), used by every candidate:

1. **A realistic IFC model** from an open test set — representative complexity, not a demo cube.
2. **Synthetic scale tests** at 10k / 100k / 1M elements.
3. **A parametric change that forces re-evaluation** — move a wall, and require that its
   openings, its junctions with adjoining walls, and every 2D view showing it follow.

Test 3 is the sharpest. It measures precisely what separates a viewer from a modeller, and it is
the one most likely to eliminate candidates.

## Candidates

### Layer 1 — semantic / BIM kernel
- [ ] IfcOpenShell — *current hypothesis*
- [ ] web-ifc (That Open Engine)

### Layer 2 — geometry kernel
- [ ] OCCT (Open CASCADE Technology)
- [ ] CGAL
- [ ] Manifold — *current hypothesis for the interactive path*
- [ ] Truck
- [ ] Fornjot

Layer 3 candidates are evaluated in [`../hosts-and-engines/`](../hosts-and-engines/).

## Questions every candidate note must answer

1. Can it re-evaluate a single changed element without reprocessing the model?
2. What exactly happens to geometry on an IFC round trip?
3. Can it be driven from the language of our host, in-process, without a subprocess or a file?
4. What is its threading model, and can geometry evaluation move off the UI thread?
5. What breaks first at scale — memory, load time, or evaluation time?
6. **What numeric precision does it use internally, and can it be configured?** float32-only is
   disqualifying.
7. **Can it operate on a subset of the model** — one tile, one region — or does it require the
   whole model? This decides whether tiling is possible at all. See R-14.
8. Who maintains it, and what happens to us if they stop?

## Output of this directory

A completed matrix and a shortlist of two, carried into phase 3 spikes. See
[`../../roadmap.md`](../../roadmap.md).
