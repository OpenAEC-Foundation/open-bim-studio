# Blender

**Decision question:** Which parts of its interaction model are transferable to a BIM tool, and
which depend on having no semantic model?

**Status:** draft — phase 1
**Last updated:** 2026-07-29

---

## Summary

The reference for the interaction half of this project's ambition. Its speed comes from a
**modal, keyboard-first command grammar** that is almost entirely orthogonal to what is being
modelled — which means it transfers.

Blender as a *host* is evaluated separately in
[`../hosts-and-engines/README.md`](../hosts-and-engines/README.md) and is currently blocked on
the scale ceiling (R-03). This note is about the interaction model only. **Keeping those two
questions apart is important:** rejecting Blender as a host says nothing about its interaction
design.

## The command grammar

The mechanism worth stealing, and it is a genuine grammar rather than a set of shortcuts:

```
[select] → [operation] → [axis constraint] → [numeric input] → [confirm]
     G/R/S          X/Y/Z              type a number         click / Enter
```

`G` grabs. `G X` grabs along X. `G X 5` moves five units along X. `G X X` moves along the
object's local X. Every operation composes with every constraint the same way.

Four properties make this fast, and each is separable:

**Verb-first, hands stationary.** The keyboard issues commands; the mouse manipulates. The hands
do not travel to a toolbar or a menu.

**Composable and consistent.** Learning the pattern once gives you every combination. Contrast
with a ribbon, where each command is a separate thing to find and remember.

**Modal with immediate exit.** An operation is live until confirmed or cancelled, and escape
always works. Experimentation costs nothing, which is what makes users experiment.

**Numeric input inside the gesture.** Same idea as SketchUp's type-while-you-drag, reached
independently — which is evidence it is the right answer rather than a stylistic choice.

## What transfers, and what does not

| Element | Transfers? | Note |
|---|---|---|
| Verb-first modal commands | **Yes** | Independent of what is being modelled |
| Axis constraints | **Yes** | Building modelling is more axis-aligned, not less |
| Numeric input during gesture | **Yes** | Confirmed by SketchUp arriving at the same design |
| Instant, unlimited undo | **Yes** | But see the retrofit warning below |
| Everything-is-editable | **Partly** | Constrained by semantic validity |
| Direct mesh/vertex editing | **No** | Geometry is derived from parameters, not authored |
| Non-destructive modifier stack | **Concept transfers** | Close to a parametric evaluation graph — worth studying properly |
| Free topology | **No** | Conflicts with valid IFC — R-07 |

The modifier stack deserves a dedicated look during phase 2. It is a user-facing,
non-destructive, ordered evaluation graph that users manage successfully — which is close to what
a parametric component system needs to expose, and evidence that users can handle an explicit
evaluation model when it is presented well.

## The undo warning

Blender's undo is instant and effectively unlimited, and that is a large part of why it feels
safe to experiment in.

This is not a feature that can be added later. It requires a command/transaction architecture
from the first line of code, which is why undo is marked 🔴 structural in
[`../../domain/capability-inventory.md`](../../domain/capability-inventory.md) despite being an
unglamorous **M**.

## What it does not have

Stated plainly, because the appeal of Blender's feel can obscure how much is missing: no
semantic model, no coordination, no drawing production, no exchange, no scale for BIM element
counts (R-03), and — with the Bonsai addon — a documented authoring ceiling well below a real
building. See [`bonsai.md`](bonsai.md).

## On "gamification"

The originating brief used this word, and Blender is the likely referent. Nothing about Blender
is gamified in the points-and-badges sense. What it has is **responsiveness and a control scheme
that rewards fluency** — the same properties that make a well-designed game feel good to operate.

That reading is recorded in [`../../ux/interaction-model.md`](../../ux/interaction-model.md) and
still needs confirming with the maintainers rather than assuming.

## Verdict

Adopt the command grammar. It is the most concrete, most transferable finding in the prior-art
survey, and it is independent of the host decision.

Requirements taken from this note:

1. **Verb-first modal commands with axis constraints and in-gesture numeric input.** This is the
   interaction spine, not a shortcut layer added later.
2. **Command/transaction architecture from day one** for instant unlimited undo.
3. **Study the modifier stack** as a model for exposing parametric evaluation to users — phase 2.

## Sources

Blender's interaction model is best assessed by use. Specific interaction traces belong in
[`../../ux/interaction-model.md`](../../ux/interaction-model.md) per the method described there;
this note records the structural observations only.
