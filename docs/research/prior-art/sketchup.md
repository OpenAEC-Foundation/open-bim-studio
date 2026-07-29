# SketchUp

**Decision question:** What exactly makes modelling low-friction, and how much of it is
compatible with a semantic model?

**Status:** draft — phase 1
**Last updated:** 2026-07-29

---

## Summary

The most instructive tool in the prior-art list, because it is the clearest natural experiment:
it removed almost everything a BIM tool has and became something architects reach for anyway.
Understanding *what it removed* separates the friction that is load-bearing from the friction
that is merely inherited.

Its central mechanism — **inference** — is transferable to a semantic model and is where
low-friction modelling actually comes from.

## What it is

A direct-manipulation 3D modeller aimed at architectural massing and early design. Minimal
toolbar, small tool set, famously gentle learning curve — students reportedly reach basic
competence within hours, against weeks for BIM tools.

It has no semantic model, no coordination, no parametrics, and no real documentation output.
Architects use it anyway, at scale, particularly early in design.

## Why it is fast — the actual mechanisms

Not "a simpler interface". Specific, identifiable, and mostly transferable:

### Inference — the important one

The cursor continuously infers geometric relationships from context — on-face, on-edge,
endpoint, midpoint, parallel, perpendicular, on-axis — and communicates them visually as you
move. You get accuracy without asking for it and without entering coordinates.

**This is where the speed comes from.** It replaces the entire "select a snap mode, then act"
cycle with a single continuous gesture, and it means precision costs nothing.

It is also fully compatible with a semantic model. Inference is about geometric context, not
about meaning. **This is the single most transferable idea in the prior-art survey.**

### A very small tool set

Push/pull, line, rectangle, circle, arc, move, rotate, scale, offset. Nearly all modelling is
combinations of these, so the tools are always in muscle memory. Compare with a ribbon of
hundreds of commands, of which any user knows a few dozen.

The trade is real: the small tool set is *why* it cannot do what BIM tools do.

### Push/pull

One gesture converts 2D to 3D. It maps directly onto how buildings are conceived — draw the
footprint, pull it up. Discoverable within seconds and never stops being useful.

### Type-while-you-drag

Numeric input goes into a single field during the gesture, without stopping to click into a
dialog. Precision without modality.

### Immediate feedback

Everything happens during the gesture. Nothing is confirmed.

## What it gave up, and whether we can keep it

The productive question. Each row is a test of whether the friction was load-bearing:

| Given up | Consequence | Can we keep it? |
|---|---|---|
| Semantic model | No coordination, no data, no exchange | **Must keep** — it is the product |
| Parametrics | Nothing updates when anything changes | **Must keep** |
| Documentation | Drawings are a separate exercise | **Must keep** |
| Solid modelling rigour | Geometry is surfaces; non-manifold results are routine | **Must keep** rigour — see R-02 |
| Scale | Struggles with large detailed models | **Must keep** scale |
| A large tool set | Cannot express what BIM elements require | Partly — resist tool proliferation |

So: **we cannot adopt what SketchUp gave up. We can adopt how it behaves.** Inference,
type-while-you-drag, immediate feedback and gestural tools are all orthogonal to semantics.

That is the encouraging finding of this note, and it is direct support for the thesis in
[`../../ux/interaction-model.md`](../../ux/interaction-model.md): the immediacy lives in the
interaction model, not in the absence of a data model.

## The caution

SketchUp is easy partly *because* it does little. Some of its speed is genuinely a consequence
of having no semantics — no declaration of what you are building, no relationships to maintain,
no validity to preserve.

Any estimate of how fast a semantic tool can feel must subtract that portion. See the
inherent-cost analysis in [`revit.md`](revit.md).

**We should expect to land between the two, not at the SketchUp end.**

## Verdict

Adopt the mechanisms, reject the trade.

Concrete requirements taken from this note:

1. **Inference-based snapping is a core capability, not a convenience.** Marked `core`/L in
   [`../../domain/capability-inventory.md`](../../domain/capability-inventory.md), and it earns
   that weight.
2. **Numeric input during the gesture**, never in a dialog.
3. **Keep the tool set small.** Resist adding a tool for every element type; prefer one gesture
   parameterised by what is being made.
4. **Every action shows its result while it happens.** This is what forces R-01 to be resolved
   — continuous feedback requires cheap re-evaluation.

Point 4 is the load-bearing connection between this note and the technical risk register: the
interaction model is not a UI concern, it is a constraint on the geometry architecture.

## Sources

- [Revit vs SketchUp, 2026](https://www.novatr.com/blog/revit-vs-sketchup)
- [Revit vs SketchUp — fundamental differences](https://www.harmony-at.com/en/blog/revit-vs-sketchup)
- [Which CAD program should I use](https://robertmannarchitect.com.au/blogs/design-advice/which-cad-program-should-i-use-autocad-sketchup-vectorworks-revit-or-archicad)
