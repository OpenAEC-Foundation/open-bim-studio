# Prior-art synthesis

**Decision question:** Across all the tools examined, what is the actual opportunity — and which
parts of the project's premise survive contact with the evidence?

**Status:** first pass — phase 1. Covers Revit, SketchUp, Blender and Bonsai. Archicad,
Rhino/Grasshopper and Onshape are outstanding and may revise this.

---

## Summary

The premise survives, in a **weakened and more useful form**.

BIM modelling is slow for three separable reasons. Two are addressable and one is not. The
project's opportunity is real but narrower than "make BIM feel like a game engine" — and the
narrower version is the one that can actually be built.

The most valuable finding is not about kernels. It is that **the interaction mechanisms which
make low-friction tools fast are orthogonal to semantics.** They can be adopted without giving up
the data model. That is the load-bearing claim of the whole project, and the evidence supports it.

---

## 1. Why is BIM modelling slow?

The framing question. The answer is three causes, not one — and conflating them is how this
project would fail, because you cannot design away a cost that is inherent.

### Inherent to semantic modelling — not addressable

Declaring what you are building, maintaining relationships, and propagating change all cost
something. That cost *is* the coordination guarantee. Any tool keeping the semantics pays it.

**Consequence:** we should expect to be meaningfully faster, not game-engine fast. A design that
promises otherwise is quietly discarding something load-bearing.

### Data-model debt — addressable, and underrated

The reported causes of poor performance in the dominant tool are overwhelmingly *accumulation*:
unused views, in-place families, model groups, imported CAD, memory exhaustion. Firms employ
people to manage this.

This is not slow software. It is **a data model with no pressure against unbounded growth**, in
which nothing is cheap to discard and users cannot see what is costing them.

**This is the most underrated opportunity in the survey.** It is invisible in feature comparisons
because it only appears months into a project, and it is architectural — so a competitor cannot
patch it.

**Requirement:** the model stays fast when neglected. If performance depends on user discipline,
most users will not have it.

### Interface debt — addressable, and overrated

Ribbons, dialogs, learning curves. Real, and the most visible, which is why it dominates the
complaints — but also the easiest for an incumbent to fix. The dominant tool rewrote its graphics
engine in 2026, demonstrating that the visible problems are the tractable ones.

**Building a business on fixing only this would be building on the least defensible ground.**

---

## 2. What do the low-friction tools give up, and is any of it required?

| Given up | Required for our product? |
|---|---|
| Semantic model | **Yes** — it is the product |
| Coordination | **Yes** |
| Documentation output | **Yes** |
| Geometric rigour | **Yes** — see R-02 |
| Scale | **Yes** |
| Large tool sets | **No** — resist tool proliferation |
| Modality-free workflow | **No** — modality done well is *faster*, not slower |

The last row is the interesting one. Blender is heavily modal and fast *because* of it. Modality
is not the problem; **dialogs** are. A mode you enter with one key and leave with escape costs
nothing. A dialog that interrupts the gesture costs everything.

This distinction matters because "remove modes" would be the wrong lesson to draw, and an easy
one to draw.

---

## 3. The transferable mechanisms

The concrete output of this survey. All four are independent of the data model — this is the
evidence for the thesis in [`../../ux/interaction-model.md`](../../ux/interaction-model.md).

**Inference-based snapping.** Continuous inference of geometric context — endpoint, midpoint,
parallel, perpendicular, on-face, on-axis — communicated visually during the gesture. Precision
without asking for it. *The single most transferable idea in the survey*, and the reason snapping
is weighted `core`/L in
[`../../domain/capability-inventory.md`](../../domain/capability-inventory.md) rather than
treated as a convenience.

**Verb-first modal command grammar.** `[select] → [operation] → [constraint] → [number] →
[confirm]`, composable and consistent. Hands stay still, the pattern is learned once.

**Numeric input inside the gesture.** Reached independently by two very different tools, which is
evidence it is correct rather than stylistic.

**Instant unlimited undo.** Makes experimentation free, which is what makes users experiment.
Requires a command/transaction architecture from the first line of code — it is the cheapest item
in the capability inventory to build and among the most expensive to retrofit.

---

## 4. Where does every tool fail in the same way?

The opportunity, if there is one.

**Component authoring is a separate world.** In the dominant tool it is a distinct editor with
different rules, a steep learning curve, and known weakness with parametric curves. Elsewhere it
requires a scripting or visual-programming environment. **In no tool is authoring a component the
same activity as modelling.** This is a product decision everywhere, not a technical necessity —
which is why it is the clearest `diff` in the capability inventory.

**Performance degrades with model age**, and requires curation to avoid.

**Drawing production is where the effort actually goes** and is treated as downstream of the "real"
3D work in every tool's design. See [`../../domain/drawings-from-model.md`](../../domain/drawings-from-model.md)
and R-05.

**Nobody has both.** Semantic and slow, or immediate and meaningless. Bonsai is the closest
attempt at both and is scale-limited below its own domain.

---

## 5. What this changes

Concrete revisions already applied:

- **Capability inventory** — snapping/inference raised to `core`/L; undo marked 🔴 structural;
  visual component authoring marked `diff`; IFC2x3 read support raised, since almost all real
  exchange is still IFC2x3.
- **R-01 is confirmed as the critical risk.** Continuous feedback is the mechanism the entire
  interaction thesis depends on, and it requires cheap incremental re-evaluation. If R-01 fails,
  the product changes rather than merely slipping.
- **A new requirement not previously captured:** the model must stay fast without curation. This
  is architectural and belongs in the build brief.

## 6. What remains unanswered

1. **Is IFC-native authoring viable at scale?** Bonsai does it and is scale-limited. Whether that
   is the approach or the host is R-03.
2. **Can component authoring genuinely use the same interaction model as modelling?** This is our
   main claimed differentiator and it is currently an assertion, not a design.
3. **How much of the inherent cost is really inherent?** Our split between the three causes is
   reasoned, not measured. It may be too generous to the incumbents.
4. **Rhino/Grasshopper and Onshape are outstanding**, and both bear directly on question 2. Do
   them before treating this synthesis as settled.

## Sources

See the individual notes: [`revit.md`](revit.md), [`sketchup.md`](sketchup.md),
[`blender.md`](blender.md), [`bonsai.md`](bonsai.md).
