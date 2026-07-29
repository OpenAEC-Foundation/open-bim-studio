# Renderers

**Decision question: how do we keep 10⁵–10⁶ building elements interactive, while supporting the
2D drawing pipeline?**

Only relevant if the standalone route wins in
[`../hosts-and-engines/`](../hosts-and-engines/) — but it must be researched *before* that
decision, because "a renderer is too expensive to build" is one of the strongest arguments for
adopting a host. That argument cannot be evaluated without knowing the cost.

## What makes BIM rendering unusual

Not a game, not a CAD viewer, and the differences drive the architecture:

- **Element counts are enormous but geometry is repetitive.** Thousands of identical windows.
  Instancing is not an optimisation, it is the design.
- **Everything must be individually selectable and identifiable.** Merging geometry for draw-call
  efficiency fights against picking and per-element state.
- **Geometry changes during interaction.** Static-scene assumptions do not hold; a dragged wall
  regenerates its mesh every frame.
- **Section cuts are a first-class view mode**, not an effect. Capped clipping with correct fill
  at the cut plane.
- **Hidden-line and non-photorealistic output is required**, because drawings are the product.
  This is the requirement most likely to be underestimated.
- **Precision matters at building scale.** Millimetres over hundreds of metres; single-precision
  float artefacts are a real concern.

## Criteria

| Criterion | Why it matters |
|---|---|
| Instancing and batching | The only way element counts work |
| Picking at scale | Per-element selection without a draw call per element |
| Dynamic geometry | Cost of regenerating meshes during interaction |
| Capped clipping | Section views |
| Line rendering | Hidden-line, silhouette, and technical drawing output |
| **Camera-relative rendering** | **Required.** Unbounded geographic extent with millimetre precision — see [`../../domain/spatial-model.md`](../../domain/spatial-model.md) |
| Depth precision | Correctness at building scale, and over geographic extent |
| Platform reach | Desktop certainly; browser possibly |
| Maturity and AI familiarity | Delivery speed |

## Candidates

- [ ] three.js (WebGL / WebGPU)
- [ ] Raw WebGPU
- [ ] bevy / wgpu (Rust)
- [ ] Filament
- [ ] The renderer inherited from a host, if a host is chosen

## Open questions

1. What is the honest effort to a renderer that handles 100k selectable elements at interactive
   frame rates? Weeks or months? This number decides the host question.
2. Does the 2D drawing pipeline share the renderer, or is it a separate geometric process
   feeding a vector output? These are very different architectures — see
   [`../../domain/drawings-from-model.md`](../../domain/drawings-from-model.md).
3. Is browser support a requirement or a bonus? It constrains the entire stack, and answering it
   late is expensive.
