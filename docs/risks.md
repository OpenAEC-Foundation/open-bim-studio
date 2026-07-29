# Risk and uncertainty register

**This is the backlog.** Open uncertainties are the work. If something is not here, it is not
tracked.

Each entry names a specific experiment and a pass/fail criterion written *before* the experiment
runs. Criteria written afterwards get rationalised into agreement with whatever happened.

**Status values:** `open` · `in progress` · `resolved` · `accepted` (we proceed despite it)

---

## Critical — these can invalidate the whole approach

### R-01 · Incremental evaluation may not exist in any candidate kernel
A kernel that converts a whole model fast but cannot cheaply re-evaluate a *single changed
element* is a viewer engine, not a modeller engine. Most IFC tooling was built for viewing, so
this capability is often absent and rarely documented.

- **Spike:** `spikes/incremental-evaluation/` — load a model, change one wall's parameters,
  measure the cost of regenerating only affected geometry.
- **Pass:** single-element re-evaluation under 16 ms on a 100k-element model.
- **Fail:** re-evaluation requires reprocessing the model, or exceeds 100 ms.
- **If it fails:** we write our own evaluation layer over a geometry kernel, and the semantic
  kernel becomes I/O only. Significant scope increase.
- **Status:** open — **confirmed as the critical risk by phase 1.** The prior-art synthesis found
  that continuous feedback during a gesture is the mechanism the entire interaction thesis rests
  on, and it requires cheap incremental re-evaluation. If R-01 fails, the product changes rather
  than merely slipping.

### R-02 · The Manifold ↔ OCCT seam may lose information
The hybrid hypothesis assumes fast mesh booleans on the interactive path and exact geometry at
the edges. Conversion between the two may lose what 2D derivation and IFC export need.

- **Spike:** `spikes/geometry-seam/` — wall with openings through mesh boolean, converted for
  section derivation and IFC export; compare against the exact path.
- **Pass:** section geometry and exported IFC are dimensionally correct within tolerance.
- **Fail:** loss requires maintaining two parallel representations of every element.
- **Status:** open

### R-03 · Blender's ceiling may be architectural or may be Bonsai's
Documented limits around 30–80k objects. Whether this is Blender's object model or Bonsai's
implementation decides whether Blender is a candidate at all.

- **Spike:** `spikes/blender-ceiling/` — generate 100k trivial objects directly via `bpy`,
  bypassing Bonsai. Measure viewport interactivity and selection.
- **Pass (for Blender):** interactive at 100k objects → the ceiling is Bonsai's, Blender reopens.
- **Fail:** viewport degrades regardless → architectural, Blender is out.
- **Status:** open

### R-04 · Standalone renderer effort may be prohibitive
"Too expensive to build" is the strongest argument for adopting a host. It cannot be weighed
without a number.

- **Spike:** `spikes/renderer-scale/` — 100k individually selectable instanced elements, with
  capped section clipping.
- **Pass:** 60 fps with picking, reached in under two weeks of effort.
- **Fail:** below 30 fps, or the effort estimate exceeds a month.
- **Status:** open

---

## High — these shape the architecture

### R-12 · Performance may degrade with model age rather than model size
Phase 1 prior art found that reported performance problems in the dominant BIM tool are
overwhelmingly *accumulation* — unused views, in-place families, groups, imported CAD — rather
than raw element count. Firms employ people to manage this. It is architectural: a data model
with no pressure against unbounded growth.

Our benchmark set measures scale, not age. A model that is fast at 100k fresh elements may still
degrade over a project's life, and we would not find out until far too late.

- **Action:** add an ageing scenario to the benchmark set — repeated edit/undo/delete cycles,
  orphaned views, unused definitions — and measure drift. Design the data model so unused things
  are genuinely cheap.
- **Pass:** performance after a simulated project lifetime is within 20% of the fresh model.
- **Status:** open — raised by [`research/prior-art/synthesis.md`](research/prior-art/synthesis.md)

### R-05 · 2D drawing production is systematically underestimated
Generating a section is easy. Producing an *issuable* drawing — annotation, dimensions, tags,
hatching, line weights, view templates — is a large subsystem. It may be larger than the 3D
modelling work.

- **Action:** scope it honestly in [`domain/drawings-from-model.md`](domain/drawings-from-model.md)
  before committing to a roadmap.
- **Status:** open

### R-06 · Parametric components may require a scripting escape hatch
"No code required" may be unachievable for real component libraries. If scripting is needed, it
must be designed in from the start, not bolted on.

- **Action:** research how existing parametric systems handle the boundary; decide in phase 4.
- **Status:** open

### R-07 · The free-modelling / semantic-correctness seam is unlocated
Flexibility and valid IFC output pull against each other. We have not established where the
boundary sits, and it affects the core data model.

- **Action:** resolve in [`vision/non-goals.md`](vision/non-goals.md) before phase 4.
- **Status:** open

### R-08 · Browser support may or may not be a requirement
It constrains the entire stack. Deciding late is expensive.

- **Action:** explicit decision, recorded as an ADR, before phase 3 spikes are designed.
- **Status:** open

---

## Medium

### R-09 · The AI-familiarity criterion may bias us toward popularity over fitness
A legitimate criterion that rewards the wrong thing if over-weighted.

- **Mitigation:** one column in the matrix, never a tiebreaker on its own. Where it changes a
  ranking, say so explicitly in the note.
- **Status:** accepted, monitored

### R-10 · The build strategy assumes AI capability that does not yet exist
The premise is that AI assistance will be strong enough to compress the build. If it is not,
this preparation still has value but the timeline does not hold.

- **Mitigation:** the preparation output is useful to human developers too. The build brief must
  not assume an AI reader exclusively.
- **Status:** accepted

### R-11 · Licence compatibility across the stack is unverified
LGPL, MPL, and commercial components combined into one product, with possible open-sourcing
later. Not yet checked as a whole.

- **Action:** licence compatibility review once the shortlist exists.
- **Status:** open

---

## Resolved

*None yet.*

---

## How to use this file

- Adding a risk requires naming the experiment or decision that would close it. A risk without
  one is a worry, and worries do not belong in a backlog.
- Claim work by putting your name next to an entry.
- When resolved, move it to the Resolved section with a link to the finding. Do not delete —
  the reasoning is the value.
