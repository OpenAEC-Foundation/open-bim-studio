# Rhino and Grasshopper

**Decision question:** Grasshopper is the most successful parametric authoring tool architects
actually use. Why does it work, and can its approach carry our component system?

**Status:** draft — phase 1
**Last updated:** 2026-07-29

---

## Summary

The strongest evidence that non-programmers will build parametric logic — **and** the strongest
evidence that visual programming does not remove the difficulty, it relocates it.

The conclusion for us is uncomfortable but clarifying: Grasshopper is the wrong model for
component authoring, and the right model for the escape hatch. **The two should not be the same
system.**

## What it is

A visual dataflow environment inside Rhino. Users wire components into a graph; geometry is
produced by evaluating it. Widely adopted in architectural practice, in teaching, and as the
de facto language of computational design.

## Why it works

**No syntax.** The single largest barrier to programming is removed. Visual programming makes
abstract concepts tangible without users being blocked by syntax, and the design process becomes
a visual flow that is easier to depict, understand, and modify.

**The graph is the program and the documentation.** Logic is visible rather than inferred from
code. Someone else's definition can be read.

**Immediate feedback.** Change a slider, watch the geometry update. The same continuous-feedback
property identified in [`sketchup.md`](sketchup.md) and [`blender.md`](blender.md), reached again
from a third direction.

**It is a real language.** Not a restricted wizard. Users are not blocked by a ceiling the
designers imposed, which is why it survived contact with professional practice.

## Where it breaks down

And it does — this is the part that matters for our differentiator claim.

**The learning curve is steep despite having no syntax.** Consistently reported. The difficulty
was never the syntax; it is *decomposing a problem into operations on data*. That is programming,
and it remains hard when drawn instead of typed.

**Learning resources collapse past the beginner stage.** Abundant introductory material, sparse
intermediate and advanced material. This is a symptom, not an accident: the beginner cases are
genuinely easy and the real ones are genuinely hard.

**Large definitions become unreadable.** The property that makes small graphs legible — seeing
everything at once — is what makes large ones incomprehensible. Visual programming scales worse
than text, not better. Text has abstraction mechanisms that graphs largely lack.

**It sits beside the model, not inside it.** Grasshopper produces geometry; it is not how you
edit the building. Switching between them is a context switch.

## What this means for our differentiator

We claimed in [`synthesis.md`](synthesis.md) that component authoring should use the same
interaction model as modelling — because in every tool examined it is a separate world. Grasshopper
sharpens that claim into something buildable, by showing what *not* to do.

**Grasshopper is a separate world too.** A capable one, but visual programming is still
programming, and adopting it as the primary component-authoring route would reproduce the exact
problem we identified in Revit's family editor: a distinct environment with different rules, in
which a competent modeller is a beginner.

The distinction that resolves this:

| Task | Right tool |
|---|---|
| "This window's frame width is a parameter, and the sill follows the wall thickness" | **Modelling gestures** — the common case |
| "Generate a facade panel layout from a surface with attractor-driven variation" | **A computational graph** — the exceptional case |

The first is 95% of components in practice and should not require a graph. It is
*parameterising a model you already made* — a modelling activity, expressible with modelling
gestures.

The second is genuine computation, and no gesture-based interface will express it.

> **Proposed position: gesture-based parameterisation as the primary path, a computational graph
> as the escape hatch. Not one system stretched to cover both.**

This is a concrete answer to R-06 (whether a scripting escape hatch is needed) and it says the
escape hatch is needed — but that it must be the *secondary* path, entered deliberately, rather
than the route everyone is pushed down. That is precisely where the incumbents went wrong.

## Rhino itself

Briefly, since Grasshopper is the reason it appears here. NURBS-based, permissive about
geometric validity, strong at free-form. Its permissiveness is why architects reach for it and
why its output needs cleaning before it is buildable — the same trade documented in
[`sketchup.md`](sketchup.md).

Relevant to R-07 as another data point: the tools architects choose for design are consistently
the ones that let them make invalid geometry.

## Verdict

Adopt the lesson, not the interface.

1. **Two paths, deliberately separated.** Gesture-based parameterisation for the common case; a
   computational graph as an escape hatch. Answers R-06.
2. **Visual programming does not make programming easy** — it removes syntax, which was never
   the hard part. Do not plan on it as an accessibility strategy.
3. **Immediate feedback confirmed from a third independent direction.** Strong support for R-01
   being the critical risk.
4. **If we build a graph escape hatch, plan for large-definition legibility** — abstraction,
   grouping, reuse. This is where Grasshopper struggles most.

## Sources

- [Empowering design through visual programming languages](https://novedge.com/blogs/design-news/empowering-design-through-visual-programming-languages-bridging-complexity-and-creativity)
- [The best way to learn Grasshopper for architecture](https://hopific.com/the-best-way-to-learn-grasshopper-for-architecture/)
- [Mastering parametric BIM with Grasshopper programming](https://www.e-zigurat.com/en/blog/visual-programming-grasshopper/)
- [Grasshopper for architects: a comprehensive guide](https://www.numberanalytics.com/blog/grasshopper-for-architects-comprehensive-guide)
