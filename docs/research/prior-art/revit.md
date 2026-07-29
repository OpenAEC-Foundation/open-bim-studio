# Revit

**Decision question:** Why is modelling in the dominant BIM tool slow — is that inherent to
semantic modelling, or is it accumulated interface and data-model debt?

**Status:** draft — phase 1
**Last updated:** 2026-07-29

---

## Summary

Revit is the capability benchmark and the source of the friction this project exists to remove.
The friction is **not one problem**: it comes from three separable causes, and only two of them
are avoidable. Treating them as one is the mistake that would sink this project — you cannot
design away a cost that is inherent to what BIM is.

## What it is

The dominant BIM authoring platform in architecture and structural engineering. Parametric
object model, coordinated views, family-based component system, mature IFC support. Its
capability set is what "professional BIM tool" means in practice, which is why
[`../../domain/capability-inventory.md`](../../domain/capability-inventory.md) is largely a
description of it.

## The three causes of friction

Separating these is the analytically important move.

### 1. Inherent to semantic modelling — not avoidable

Some cost is the price of the model being meaningful:

- You must declare *what* you are making before you make it. A wall is not discovered from
  geometry; it is asserted.
- Elements are constrained by relationships. That constraint is the coordination guarantee — it
  is the feature, experienced as friction.
- Change propagates, and propagation costs computation. See R-01.

**Any tool that keeps the semantics pays this.** A design that assumes otherwise is assuming the
project away.

### 2. Data-model debt — partly avoidable

The performance complaints have a specific and revealing shape. Reported root causes are
overwhelmingly *accumulation*: unused views, in-place families, model groups, imported CAD, and
RAM exhaustion driving page-file thrashing.

This is not "the software is slow". It is **a data model with no pressure against unbounded
growth**, in which nothing is cheap to discard and users have no visibility into what is costing
them. Firms employ people to manage this.

*Evidence type: claimed — widely reported across independent sources, not measured by us.*

The instructive detail: Autodesk rebuilt the graphics engine in the 2026 release. That was the
part that could be fixed by rewriting a component. The accumulation problem cannot be, because
it is the data model.

**What we take from this:** a model that stays fast when neglected, not one that requires
curation. If performance depends on discipline, most users will not have it.

### 3. Interface debt — avoidable

Ribbons, modal dialogs, deep option trees, and a widely criticised learning curve. This is
thirty years of accreted decisions, not a necessity. It is the part
[`../../ux/interaction-model.md`](../../ux/interaction-model.md) targets.

## The family system

The most instructive subsystem, because it is where Revit's ambition and its failure are both
clearest.

Families are genuinely parametric, genuinely powerful, and reliably reported as hard: a steep
learning curve, confusing constraint behaviour, difficulty with nested components, and
particularly poor handling of parametric curves — arcs, circles and ellipses are noted as
difficult to control "in a reliable and stable way". Geometry creation inside the family editor
is also described as limited compared with general modelling tools.

The pattern that matters: **the family editor is a separate environment with different rules
from the main modelling environment.** A user competent in one is a beginner in the other. That
is a product decision, not a technical necessity, and it is why component authoring stays the
preserve of specialists.

**What we take:** component authoring should use the same interaction model as modelling. This
is why visual component authoring is marked `diff` in the capability inventory — it is a place
where being better is achievable, not merely desirable.

## Strengths worth preserving

Easy to lose sight of while cataloguing complaints. A tool does not achieve this position by
being bad:

- **Coordination genuinely works.** Change the model, every drawing follows. This is the
  product, and it is hard.
- **Schedules and take-off derive from the model** rather than being maintained alongside it.
- **The type/occurrence model is correct**, and the industry's mental model is now shaped by it.
- **Mature IFC support** and a large body of institutional knowledge.
- **Documentation output is genuinely issuable** — the bar we must clear, and higher than it
  looks.

## Weaknesses — architectural versus incidental

| Weakness | Architectural or incidental? |
|---|---|
| Performance degrades with model age | **Architectural** — no pressure against accumulation |
| Family editor is a separate environment | **Architectural** — a product decision, deeply embedded |
| Limited geometry creation | **Architectural** — constrained by the kernel and the family model |
| Parametric curves unreliable | **Architectural** — constraint model, not a bug |
| Steep learning curve | Incidental — interface accretion |
| Dialog-heavy workflow | Incidental |
| Viewport performance | Incidental — demonstrably, since it was rewritten in 2026 |

Only the architectural ones are opportunities. The incidental ones are things a competitor can
fix and so can Autodesk — and in the viewport case, did.

## Verdict

Revit defines the capability bar and supplies the clearest evidence for the project's premise —
but a weaker version of that premise than the framing assumes.

**BIM modelling is not slow only because of interface debt.** A substantial part is data-model
debt, and a real part is inherent to semantic modelling. The opportunity is in the first two.

This tempers the ambition usefully: we should expect to be **meaningfully faster, not
game-engine fast**, while keeping the semantics. Any design claiming otherwise is probably
discarding something that turns out to be load-bearing.

Three concrete requirements follow, and all three are now reflected in the capability inventory:

1. Performance must not depend on model hygiene.
2. Component authoring must not be a separate environment.
3. Coordination must be preserved without exception — it is the reason the category exists.

## Sources

- [5 most common Revit problems architects face](https://integratedbim.com/5-common-revit-problems-and-how-to-fix-them/)
- [Why your Revit model is slow](https://graitec.com/us/blog/why-your-revit-model-is-slow-and-how-to-fix-it-2/)
- [Revit performance fixes, 2026](https://www.bimcopilot.com/blog/revit-performance-18-fixes-2026)
- [Pros and cons of parametric Revit families](https://www.majentasolutions.com/news/pros-cons-of-parametric-revit-families---and-when-to-use-them)
- [Taming parametric curved geometry in the family editor](https://www.autodesk.com/autodesk-university/class/Taming-Parametric-Curved-Geometry-Revit-Family-Editor-2022)
