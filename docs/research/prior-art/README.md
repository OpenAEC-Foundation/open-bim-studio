# Prior art

**Decision question: what do existing tools get right, what do they get wrong, and what do we
take from each?**

> **Naming note.** This repository has an explicit exception to the maintainer's global rule
> against naming commercial software: BIM and 3D tools may be named here. Comparative analysis
> written as "package A" and "package B" is worthless. The exception does not extend to
> geotechnical or structural calculation packages, or to client and project names. See
> [`../../../CLAUDE.md`](../../../CLAUDE.md).

## How to write these notes

Not feature lists. Marketing material already exists and is not useful to us.

Each note answers three questions:

1. **What does this tool do genuinely well**, that users would miss?
2. **What does it do badly**, and is that an accident of implementation or a consequence of its
   architecture? *This distinction is the valuable part* — architectural weaknesses are the ones
   we can actually avoid.
3. **What do we take, and what do we deliberately reject?**

A note that only lists weaknesses has failed. Tools with large user bases are doing something
right, and finding out what is harder and more useful than cataloguing complaints.

## Tools to cover

**BIM authoring**
- [ ] Revit — the capability benchmark; also the source of most complaints about friction
- [ ] Archicad — different interaction philosophy, particularly around drawing production
- [ ] Bonsai (Blender-based) — the closest existing open-source attempt
- [ ] FreeCAD BIM workbench
- [ ] Vectorworks, Allplan — worth a shallow pass

**Real-time and general 3D**
- [ ] Blender — the interaction model we want to learn from
- [ ] Unreal Engine — real-time feel at scale
- [ ] SketchUp — the strongest counter-example: modelling so low-friction that non-experts use
      it, at the cost of everything else. The most instructive tool on this list.

**Parametric and computational**
- [ ] Rhino + Grasshopper — the reference for accessible parametric modelling
- [ ] Onshape — modern constraint-based CAD; also a lesson in cloud-first architecture

**Interoperability**
- [ ] Speckle — model exchange and versioning
- [ ] IFC tooling ecosystem generally

## Cross-cutting questions

Answer these after the individual notes, in a synthesis document:

1. Why is BIM modelling slow? Is it inherent to semantic modelling, or accumulated interface
   debt? **The entire premise of this project depends on the answer.**
2. What do the low-friction tools give up, and is any of it actually required?
3. Which capabilities do users complain about the absence of, versus which do they actually use?
4. Where does every tool on this list fail in the same way? That is where the opportunity is.
