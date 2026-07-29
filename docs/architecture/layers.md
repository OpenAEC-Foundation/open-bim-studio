# Layers, and the working hypothesis

**Decision question: which existing components do we build on, and at which layer?**

> **This document states a hypothesis, not a decision.** It exists so that research in phase 2
> and spikes in phase 3 have something specific to attack. If the measurements contradict it,
> the hypothesis loses. Do not cite it as settled.

## The insight: "which kernel" is three decisions, not one

Discussions about building on an existing kernel routinely conflate two independent axes. They
have different candidates, different criteria, and different risks, and they can be chosen
independently.

| Layer | Responsibility | Candidates |
|---|---|---|
| **1. Semantic / BIM kernel** | IFC schema, entities, property sets, relationships | IfcOpenShell, web-ifc |
| **2. Geometry kernel** | Solids, booleans, tessellation, exact dimensions | OCCT, CGAL, Manifold, Truck, Fornjot |
| **3. Host + UI** | Viewport, interaction, tooling, distribution | Blender, Unreal, Godot, standalone |

"Build on Blender" and "build on Unreal" are choices at **layer 3**. "A new application using
an existing kernel" is a choice at **layers 1 and 2**. Layers 1 and 2 are where reuse pays;
layer 3 is where reuse costs the most.

## Working hypothesis

> A standalone application, using **IfcOpenShell** as semantic and exact-geometry kernel,
> **Manifold** for real-time boolean operations, and its own renderer and UI layer.

### Layer 1 — IfcOpenShell is the strongest candidate

LGPL. Complete parsing support from IFC2x3 through IFC4x3. It supports multiple geometry
kernels — OCCT, CGAL, and explicitly a *hybrid* mode — which means the layer-2 choice is not
forced by the layer-1 choice.

Decisively: it builds to **WebAssembly**, so the same kernel serves a web or desktop-webview
application and a native one. This layer should not be rebuilt by anyone.

*Status: claimed by documentation, not yet measured. See `../research/kernels/`.*

### Layer 2 — hybrid, not pure B-rep

OCCT provides exact B-rep but is heavy and slow for interactive work. Manifold provides
*guaranteed-manifold* boolean operations — robustness against edge cases was a long-standing
open problem — and is already used by Blender and OpenSCAD.

Proposed split:
- **Manifold** on the interactive path, where speed and robustness beat exactness.
- **OCCT** at the edges, where exactness genuinely matters: import of externally authored IFC,
  2D derivation, export.

The unproven part is the seam between them. That is a phase-3 spike.

### Layer 3 — both obvious hosts have a blocking objection

**Blender has a hard scale ceiling.** The Bonsai documentation states that models above roughly
50,000 elements produce unreasonable load times, selection glitches, and viewport lag; community
reports put practical trouble around 30k objects and unusability at 60–80k. Bonsai itself states
it is "not yet appropriate for graphically authoring" large models. A real building is 10⁵–10⁶
elements. Working around this means bypassing Blender's object model — at which point Blender is
no longer providing the thing it was chosen for.

**Unreal Engine is import-only.** Datasmith is a visualisation pipeline, not an authoring
environment. All modelling tooling would have to be written from scratch in C++/Blueprints, on
top of a commercial engine dependency. You buy the real-time feel and pay on every other axis.

**Important consequence:** the immediacy of these tools does not come from their kernels. It
comes from their *interaction model* — direct manipulation, modal tools, gizmos, instant
feedback, no dialogs. That is reproducible without adopting their engine, and capturing it is
the job of [`../ux/interaction-model.md`](../ux/interaction-model.md).

## An evaluation criterion that follows from the build strategy

The application is to be built quickly with heavy AI assistance. That makes **how well AI models
know a given stack** a first-class selection criterion rather than an afterthought.

A stack with abundant public code and documentation produces materially better AI output than a
niche library with a handful of users. This is weighed explicitly in
[`../research/kernels/README.md`](../research/kernels/README.md).

It is a real criterion, and also a trap: it biases towards popularity over fitness. It is one
column in the matrix, not the matrix.

## What would falsify this hypothesis

State these before measuring, so the result cannot be rationalised afterwards:

1. IfcOpenShell cannot be driven incrementally — if it only supports batch conversion rather
   than incremental re-evaluation of changed elements, it is unusable on the interactive path.
2. Manifold and OCCT cannot be reconciled — if converting between them loses information needed
   for 2D derivation or export, the hybrid collapses.
3. Blender's ceiling turns out to be an addon problem rather than an architectural one — if
   Bonsai's limits come from its own implementation rather than Blender's object model, layer 3
   reopens entirely.
4. A standalone renderer proves too expensive — if reaching acceptable viewport quality and
   performance at 10⁵ elements is a multi-month project on its own, adopting a host regains its
   appeal.

Each is tracked in [`../risks.md`](../risks.md) with a corresponding spike.

## Sources

- [IfcOpenShell](https://ifcopenshell.org/) and [on GitHub](https://github.com/IfcOpenShell/IfcOpenShell)
- [Bonsai — dealing with large models](https://docs.bonsaibim.org/guides/viewing/dealing_with_large_models.html)
- [Manifold](https://github.com/elalish/manifold)
- [web-ifc / That Open Engine](https://github.com/thatopen/engine_web-ifc)
- [Datasmith CAD import documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/importing-cad-files-into-unreal-engine-using-datasmith)
