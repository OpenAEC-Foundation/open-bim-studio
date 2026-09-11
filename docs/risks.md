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
  than merely slipping. Now also measured for IfcOpenShell and web-ifc as evidence for ADR-0004's
  *build on* verdicts.

### R-14 · Parametric evaluation across unloaded tiles
The tile-based spatial model (see [`domain/spatial-model.md`](domain/spatial-model.md)) collides
with the parametric evaluation graph. A wall changes and its junctions must follow — but the
neighbouring wall may live in a tile that is not in memory. Load it every time and the paging is
pointless; skip it and the model is not valid.

This directly threatens R-01, which is already the critical risk. It also undermines a claim the
drawing and export subsystems rely on: that the model is always in a valid, exportable state.

- **Spike:** `spikes/cross-tile-evaluation/` — a model spanning several tiles with dependencies
  crossing boundaries; change an element near a seam with neighbours unloaded.
- **Pass:** cross-tile dependencies resolve correctly, or are detectably stale and repaired on
  load, without loading the whole model.
- **Fail:** correctness requires the full model in memory — in which case tiling gives extent but
  not scale, and streaming is off the table.
- **Mitigations to evaluate:** a one-tile halo (dependency edges are mostly spatially local);
  lazy resolution with staleness marking; deferred evaluation completed on load. All three change
  what "valid model" means.
- **Note:** separating *unbounded extent* from *streaming* may avoid this entirely — see open
  question 6 in the spatial model document. Extent needs only a tiled coordinate architecture;
  streaming needs paging and eviction. **Answer that question before committing to this risk.**
- **Status:** open

### R-15 · Georeferencing degrades on the IFC version people actually use
IFC4/IFC4x3 support georeferencing natively through `IfcMapConversion` and `IfcProjectedCRS`.
IFC2x3 carries the same information only through `ePset_MapConversion` and `ePSet_ProjectedCRS`
property-set conventions on `IfcSite`.

Almost all real exchange is still IFC2x3. So the geographic ambition pulls toward IFC4x3 — which
was extended for infrastructure, where extent matters — while interoperability reality pulls
toward IFC2x3.

- **Action:** explicit decision on export target, recorded as an ADR. Not a default.
- **Also verify:** IFC permits only *projected*, cartesian CRS. Geographic (lat/lon) systems are
  out of scope by the standard, and reprojection happens outside the model.
- **Status:** open

### R-13 · The topological naming problem
Anything that refers to derived geometry — an associative dimension, a hosted opening, a tag, a
component instance referencing its definition — stores a *name* for an entity that is the output
of a computation. When parameters change and the computation re-runs, that entity may have been
split, merged, or destroyed.

This is a named, well-studied, and **unsolved** problem in parametric CAD. Mature systems mitigate
rather than prevent: modern CAD ships repair tooling on the stated premise that fixing broken
references is simply the nature of history-based parametric design.

We will hit this the moment geometry is derived rather than stored — which is our entire
architecture.

- **Proposed mitigation:** references point at *semantic* entities and their named features —
  "the inner face of wall W12" — never at derived topology — "face 7 of solid 3". Buildings have
  a vocabulary that mechanical parts lack, so this option is more available to us than to general
  CAD. It requires the data model to be designed for it from the start.
- **Action:** locate the boundary where semantic references are insufficient, and decide
  explicitly what happens beyond it. Ties to R-07, which is the same boundary approached from the
  free-modelling direction.
- **Accept:** some breakage is inevitable. Plan for visible, repairable failure rather than silent
  corruption.
- **Status:** open — raised by [`research/prior-art/onshape.md`](research/prior-art/onshape.md)

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

### R-16 · Boolean robustness — ours and theirs
No boolean algorithm is trusted until it survives the torture set. The same set measures the
candidates we might build on or borrow from, and later our own kernel.

- **Spike:** `spikes/boolean-torture/` — the cases in `reference/boolean_torture_set.py` run
  through OCCT, Blender (exact), Manifold and CGAL; each result checked for closed manifold
  output and V(A∪B) + V(A∩B) = V(A) + V(B).
- **Pass (per candidate):** every case produces a valid closed result and the volume identity
  holds within 1e-9 relative.
- **Fail:** any invalid result, or a volume error above 1e-6 relative; each failure recorded
  with the input, the version and the traced cause in `problems.md`.
- **Findings:** [`spikes/boolean-torture/FINDINGS.md`](../spikes/boolean-torture/FINDINGS.md) —
  twelve candidate×setting combinations measured in one session; every failure traced to a
  `problems.md` row.
- **Status:** in progress — measured for four candidates. **Nine of the twelve candidate×setting
  combinations fail outright**; OCCT is valid on all thirty case×setting combinations but its
  `sliver` identity residual (3.33e-08 relative) sits between the pass and fail lines, which the
  criterion as written does not name; and the single pass, Blender's embedded Manifold solver,
  rests on a refusal the criterion cannot see — it returns operand A unchanged on
  `near_degenerate_triangle`, which happens to be the right answer for that case. Not resolved:
  our own kernel is not measured, the set is planar and single-operation, and the four candidates
  were handed materially different constructions of two of the ten cases.

### R-17 · Precision far from the origin
The tile-frame design assumes f64 local coordinates are necessary and sufficient.

- **Spike:** `spikes/precision-set/` — identical geometry at the origin and at 500 km, through
  each candidate's boolean and tessellation, then re-centred and compared.
- **Pass:** maximum deviation below 1e-6 m in f64 paths.
- **Fail:** deviation above 1e-4 m — which for a float32 path is the expected outcome and the
  evidence ADR-0006 needs.
- **Findings:** [`spikes/precision-set/FINDINGS.md`](../spikes/precision-set/FINDINGS.md) — nine
  candidate×path combinations measured in one session, with the local-frame mitigation measured
  on each candidate rather than assumed.
- **Status:** in progress — measured for four candidates, and the two populations are cleanly
  separated: **every f64 path passes** (OCCT 3.61e-10 m, CGAL Epick 1.29e-10 m, Manifold `Mesh64`
  3.29e-11 m, all one to three ULP of a 5e5 m coordinate) and **every float32 path fails**
  (Manifold `Mesh` 0.0186 m, CGAL f32-rounded 0.0348 m, Blender Exact 0.0348 m, Blender Manifold
  0.0435 m, Blender Fast 0.5 m), with three orders of magnitude of clear air between them and no
  candidate in between. That is the evidence ADR-0006 needs. Not resolved: the spike sentence
  names "each candidate's boolean **and tessellation**" and **no driver tessellates at 500 km**;
  the set is three planar cases of which only `wall_with_openings` discriminates; one distance in
  one direction; and our own kernel is not measured.

### R-18 · DynLex may not compile a kernel-sized program acceptably
The kernel will be the largest DynLex program. Compile time is on the inner loop of every
kernel developer.

- **Spike:** `spikes/dynlex-scale/` — generate synthetic DynLex programs of 5k, 20k and 50k
  lines in the kernel's style (classes, patterns, intrinsics); measure compile time and memory.
- **Pass:** 20k lines compile in under 30 s on the reference machine.
- **Fail:** over 120 s, or the compiler exhausts memory — a blocker to fix in dynlex before M1.
- **Findings:** [`spikes/dynlex-scale/FINDINGS.md`](../spikes/dynlex-scale/FINDINGS.md)
- **Status:** failed — **20k lines take 72.19 s** against a 30 s budget, and **50k lines take
  1146.72 s (19 minutes)**, 9.6× the fail threshold. Compile time is superlinear and worsening:
  the implied exponent is 1.89 from 5k→20k and **3.03** from 20k→50k. Memory is *not* the
  problem — 2.8 GB peak at 50k on a 32 GB machine, scaling roughly linearly — and neither is
  correctness: zero diagnostics at every size, and every binary printed exactly the value an
  independent Python computation produced. A blocker to fix in dynlex before M1, per this
  criterion's own wording. Note the reading applied: the pass line names 20k, the fail line names
  no size, and 20k alone (72.19 s) falls between the two; the findings record `failed` on the
  50k figure and set out the narrower reading. The most useful follow-up is cheap — separate
  whether the cost scales with pattern count, call-site count or lines, and whether it is
  per-file or whole-program.

### R-19 · DynLex runtime performance may fall short of native
The performance targets assume native-speed code.

- **Spike:** `spikes/dynlex-performance/` — triangle–triangle intersection over 10⁶ random
  pairs, BVH build over 10⁶ boxes, and an f64 orient3d loop, each in DynLex and C++ -O2.
- **Pass:** DynLex within 1.5× of C++ on every workload.
- **Fail:** over 3× on any — a codegen issue to root-cause in dynlex before M1.
- **Findings:** [`spikes/dynlex-performance/FINDINGS.md`](../spikes/dynlex-performance/FINDINGS.md)
- **Status:** resolved — **passes.** All three workloads ran in both languages with
  **bit-identical output**, from a shared xorshift64\* generator whose input checksum is compared
  too: triangle/triangle 1.12×, BVH build 1.21×, orient3d 1.01× (a tie within noise). Worst case
  1.21×, nothing near the 3× line. **Conditional on an explicit `-O` flag:** the compiler's
  default emitted-code optimisation level is `-O0`, not optimised, and unflagged it would fail on
  all three (8.71×, 6.49×, 21.62×) — the kernel's build must pass `-O2` or better. Not settled:
  no parallel, SIMD, boolean-pipeline or pointer-chasing workload was measured, and the compiler
  pin is dirty (see the caveat in the findings).

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

### R-20 · The DynLex GPU path is argued from source reading, not measured
[`research/renderers/gpu-paths.md`](research/renderers/gpu-paths.md) recommends a buffer layout —
persistent device-local vertex/index buffers, a per-tile instance buffer carrying the camera-relative
affine, and a CPU-side f64 subtraction at tile granularity — built entirely from reading five mature
engines' source and from arithmetic on the DynLex runtime's own constants. Nothing in it was run: the
DynLex compiler is not built in the working copy used for that research, so no DynLex program could be
executed. The runtime as it ships today cannot draw the scene the kernel targets at all — its 32 MiB
per-frame transient arena holds at most 25,890 boxes, against a 10⁵-box target.

- **Spike:** `spikes/dynlex-gpu-path/` — build the DynLex compiler, add index and instance buffers to
  the graphics runtime, and draw 10⁵ instanced boxes at a tile offset of 500 km from the coordinate
  origin. Measure frame time, bytes uploaded per frame, and the coordinate error against an f64
  reference computation.
- **Pass:** 60 fps sustained and coordinate error under 1e-3 m.
- **Fail:** below 30 fps, or coordinate error above 1e-2 m.
- **Status:** open — named in `renderers/gpu-paths.md` §Risks as the measured counterpart that note's
  own arithmetic does not substitute for.

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
