# Hosts and engines

**Decision question: do we build a standalone application, or build inside an existing host?**

This is layer 3 in [`../../architecture/layers.md`](../../architecture/layers.md). It is
independent of the kernel choice — a common source of muddled discussion.

## The trade

Adopting a host buys viewport, UI framework, tooling, extension ecosystem, and distribution.
It costs the host's object model, its performance envelope, its interaction conventions, and its
release cycle. The costs are invisible at the start of a project and dominant at the end.

## Criteria

| Criterion | Why it matters |
|---|---|
| **Scale ceiling** | Element count at which the viewport stops being interactive. Hard limit, not a tuning problem. |
| **Object model fit** | Does one building element map to one host object, and does that survive 10⁵ of them? |
| **Authoring vs. viewing** | Is the host built for creating geometry, or only for displaying it? |
| **UI control** | Can we build our own interaction model, or do we inherit theirs? |
| **License and dependency** | Copyleft obligations, commercial terms, revenue share |
| **Distribution** | Can users install our product, or must they install the host first? |
| **Extension API stability** | How often does an upgrade break us? |
| **Effort to first usable version** | The honest reason hosts are attractive |

## Candidates

- [ ] **Standalone** — TypeScript/WebGPU with a desktop shell
- [ ] **Standalone** — Rust core with a separate UI layer
- [ ] **Blender** (with or without Bonsai)
- [ ] **Godot**
- [ ] **Unreal Engine**
- [ ] **FreeCAD**

## Known blocking objections — to be verified, not assumed

Two candidates have documented problems serious enough to eliminate them. Both need
verification, because eliminating an option on a secondary source is how projects talk
themselves out of good decisions.

**Blender — scale ceiling.** Bonsai documentation reports unreasonable load times, selection
glitches and viewport lag above roughly 50,000 elements; community reports put practical trouble
at ~30k objects and unusability at 60–80k. Bonsai states it is not yet appropriate for
graphically authoring large models.

*What must be verified:* whether this is Blender's object model or Bonsai's implementation. If
the ceiling is Bonsai's, Blender reopens as a candidate. If it is Blender's `bpy` object
overhead, it is architectural and disqualifying. **This distinction decides the option.**

**Unreal Engine — import-only.** Datasmith is a visualisation pipeline; Unreal is not an
authoring environment for CAD/BIM. All modelling tooling would be written from scratch on top of
a commercial engine dependency.

*What must be verified:* whether Unreal's editor framework and its modelling toolset change this
assessment for a purpose-built application, as opposed to the standard Datasmith workflow.

## The thing a host is not needed for

The immediacy that makes real-time 3D tools attractive comes from their **interaction model**,
not their engine: direct manipulation, modal tools, gizmos, instant feedback, no dialogs. That
is reproducible on any renderer.

Adopting a host to obtain a *feel* is the expensive way to get something obtainable by design.
See [`../../ux/interaction-model.md`](../../ux/interaction-model.md).

## Sources

- [Bonsai — dealing with large models](https://docs.bonsaibim.org/guides/viewing/dealing_with_large_models.html)
- [Bonsai](https://bonsaibim.org/)
- [Datasmith CAD import documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/importing-cad-files-into-unreal-engine-using-datasmith)
