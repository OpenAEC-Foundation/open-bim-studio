# Vision

## The goal in one sentence

A BIM modeller that does what a professional BIM authoring tool does — 3D modelling, parametric
components, coordinated 2D drawings, IFC exchange — while feeling like a real-time 3D
application: direct, immediate, and low-friction.

## Why this combination is the point

The two halves are usually treated as separate product categories, and the split is the problem.

**Professional BIM tools** are correct and complete. They hold a semantic model where a wall
knows it is a wall, drawings stay coordinated with the model, and data survives exchange. They
are also slow to operate: modal dialogs, deep menus, long round-trips between an intent and
seeing the result.

**Real-time 3D applications** are immediate. Direct manipulation, instant feedback, modal tools
under the fingertips, no dialog between you and the geometry. They also have no idea what a
building is. Geometry has no meaning, nothing is coordinated, and nothing survives exchange.

The bet is that the immediacy is **not** a consequence of throwing away the semantics. It comes
from the interaction model — and an interaction model can be built on top of a semantic core.
See [`../ux/interaction-model.md`](../ux/interaction-model.md).

## What "does what a professional BIM tool does" means concretely

Vague ambition produces vague scope. The capability breakdown lives in
[`../domain/capability-inventory.md`](../domain/capability-inventory.md) and is the document
that turns this vision into something countable.

At minimum, the chain that must work end to end:

```
parametric object  →  geometry  →  2D drawing  →  IFC export
        ↑                                              │
        └──────────── change propagates ───────────────┘
```

Moving a wall must update its openings, its junctions with other walls, every plan and section
that shows it, and the exported model. **That loop is the product.** Everything else is breadth.

## What "feels like a real-time application" means concretely

- Changes are visible while dragging, not after confirming.
- The common case needs no dialog.
- Tools are modal and keyboard-driven; the hands stay in place.
- The viewport is the interface, not a preview of it.
- Large models stay interactive. A real building is 10⁵–10⁶ elements, and that is the
  requirement, not a stretch goal.

## Success criteria

This vision is met when a competent modeller can:

1. Produce a coordinated set of plans and sections from a model they built in the tool.
2. Exchange that model via IFC without meaningful loss.
3. Build a parametric component without writing code.
4. Work on a real project at real scale without the tool becoming the bottleneck.
5. Prefer it to their current tool for the modelling itself — not out of ideology, but because
   it is faster.

Criterion 5 is the hard one and the only one that matters commercially. The others are
prerequisites for being taken seriously.

## Open questions

- Which discipline do we serve first? Architecture and structural have different centres of
  gravity. See [`../domain/capability-inventory.md`](../domain/capability-inventory.md).
- Is "no code" for parametric components achievable, or is a scripting escape hatch required
  from day one?
- Where is the honest line between "as flexible as a 3D suite" and "produces valid IFC"? Free
  modelling and semantic correctness pull against each other, and we have not yet located the
  seam. This belongs in [`non-goals.md`](non-goals.md) once answered.
