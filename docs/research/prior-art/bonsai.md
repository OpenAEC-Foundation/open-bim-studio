# Bonsai (formerly BlenderBIM)

**Decision question:** The closest existing attempt at what we want — what does it get right,
where does it stop, and why?

**Status:** draft — phase 1
**Last updated:** 2026-07-29

---

## Summary

The most important prior art in this survey, because it is the same idea already built: native
IFC authoring inside a real-time 3D application. It works, it is used in practice, and it has a
**documented ceiling well below the scale of a real building**.

Understanding whether that ceiling is Blender's or Bonsai's is the single most decision-relevant
question in the host evaluation. It is risk R-03 and it should be tested early and cheaply.

## What it is

An addon making Blender a native IFC authoring environment, built on IfcOpenShell. Native in a
strong sense: IFC is the working format rather than an export target, which avoids the
round-trip loss that afflicts tools exporting from a proprietary model.

## What it gets right

**IFC as the native format.** The most interesting architectural decision here, and a direct
input to the open question in
[`../../domain/ifc-data-model.md`](../../domain/ifc-data-model.md). If it holds at scale, the
"our own model with IFC at the boundary" option loses much of its appeal.

**Reuse of an existing kernel.** IfcOpenShell for semantics and geometry, Blender for viewport
and UI. Exactly the strategy accepted in
[`../../architecture/decisions/0003-build-on-an-existing-kernel.md`](../../architecture/decisions/0003-build-on-an-existing-kernel.md),
which makes Bonsai a working demonstration that the strategy is viable — and a source of
evidence about where it runs out.

**Open source, open standards**, with no proprietary format lock-in.

**Genuine authoring**, not viewing. Drawing generation, schedules, property editing, and
classification are all present.

## Where it stops

**Scale.** The documentation reports unreasonable load times, selection glitches and viewport lag
above roughly 50,000 elements; community reports put practical trouble around 30k objects and
unusability at 60–80k. Bonsai itself states it is "not yet appropriate for graphically authoring"
large models, while noting that *linking* large federated models is fine.

*Evidence type: claimed — project documentation and community reports, not measured by us.*

A real building is 10⁵–10⁶ elements. **The tool is below its own domain's scale.**

**Blender's interaction model is a general 3D one.** It was designed for mesh authoring, not
building modelling. Users get Blender's excellent command grammar (see [`blender.md`](blender.md))
applied to a domain it was not shaped for.

**The learning curve is Blender's**, which is not gentle, and is unfamiliar to the architects and
engineers who are the audience.

## The question that decides the host evaluation

**Is the ceiling Blender's object model, or Bonsai's implementation?**

The distinction is decisive and the two possibilities lead in opposite directions:

- **If it is Blender's** — the per-object overhead in `bpy`, the dependency graph, the viewport's
  handling of many distinct objects — then it is architectural. No addon can fix it, Blender is
  disqualified as a host, and by extension so is the whole "build inside an existing 3D
  application" strategy for anything at BIM scale.
- **If it is Bonsai's** — how it maps IFC entities onto Blender objects, or how it synchronises
  state — then Blender reopens as a serious candidate, and much of the work here has already
  been done for us.

This is R-03, and `spikes/blender-ceiling/` is designed to answer exactly it: generate 100k
trivial objects directly via `bpy`, bypassing Bonsai entirely, and measure viewport
interactivity and selection.

**It is a cheap spike with a high-value result** — it either eliminates a branch of the host
decision or reopens it. Run it early.

## What we take regardless of the outcome

- **IFC-native as an architectural option**, with Bonsai as evidence it is workable.
- **IfcOpenShell as a proven semantic kernel** in an authoring context, not just a converter.
  This is meaningful support for the layer-1 hypothesis in
  [`../../architecture/layers.md`](../../architecture/layers.md) — though it does not yet answer
  the incremental-evaluation question, which is R-01 and remains the critical unknown.
- **The domain-fit lesson.** A general 3D interaction model applied to building modelling is
  better than a dialog-driven one and still not the same as one designed for the domain. We
  should take Blender's *grammar*, not Blender's *tools*.

## Verdict

Bonsai is the strongest evidence that this project's strategy is sound and the clearest evidence
of where it runs out.

It validates: existing-kernel reuse, IFC-native authoring, and IfcOpenShell in an authoring role.

It leaves open: whether any host-based approach can reach building scale, and whether
IfcOpenShell supports the incremental evaluation continuous feedback requires.

Both open questions have spikes. Neither should be settled by reasoning.

## Sources

- [Bonsai — dealing with large models](https://docs.bonsaibim.org/guides/viewing/dealing_with_large_models.html)
- [Bonsai](https://bonsaibim.org/)
- [Bonsai on Blender Extensions](https://extensions.blender.org/add-ons/bonsai/)
- [IfcOpenShell Blender integration](https://deepwiki.com/IfcOpenShell/IfcOpenShell/4-blender-integration-(bonsai))
- [How to open large IFC files in Bonsai — OSArch community](https://community.osarch.org/discussion/2821/how-to-open-large-ifc-files-in-bonsai)
