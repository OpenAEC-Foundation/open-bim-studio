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
- **Findings:** [`spikes/incremental-evaluation/FINDINGS.md`](../spikes/incremental-evaluation/FINDINGS.md)
  — IfcOpenShell and web-ifc measured on two reference models; xBIM read but not run (no .NET SDK
  on the machine).
- **Status:** open — **confirmed as the critical risk by phase 1**, and now measured for the
  two implementations that could be run, but **not at its own scale.** The FINDINGS say which status
  the evidence supports and this entry follows it: "R-01 should stay **open**, because its own
  criterion has not been tested at its own scale" — while no longer being open *for lack of evidence
  about existing implementations*
  ([`spikes/incremental-evaluation/FINDINGS.md`](../spikes/incremental-evaluation/FINDINGS.md)
  §What the risk status should become). The prior-art synthesis found
  that continuous feedback during a gesture is the mechanism the entire interaction thesis rests
  on, and it requires cheap incremental re-evaluation. If R-01 fails, the product changes rather
  than merely slipping.

  **web-ifc fails, size-independently.** The only working route from an edit to updated geometry is
  to discard and re-open the model — 266.8 ms on a 3,822-element file. `ResetCache`, the one call
  designed to avoid that, exists in the C++ source but is **not registered in the WASM bindings** and
  throws in the shipped 0.0.77 build; it is model-wide in any case. The warm path returns **stale**
  geometry at 0.03 ms, and the write demonstrably reached the model.

  **IfcOpenShell passes at the median and fails in the tail.** Single-element re-evaluation is real
  and genuinely does not reprocess the model — median **1.63 ms** and **2.06 ms**, 1,044× and 5,488×
  cheaper than a full iteration for a typical wall — but **5.7%** of elements on the real building
  exceed the 16 ms frame budget, p95 is **16.96 ms**, and the worst element takes **553.97 ms**, five
  times the 100 ms *fail* threshold. A modeller must be interactive when the user drags *the window*,
  not only the median wall. There is also no dependency tracking and no automatic invalidation: one
  cache has no erase at all and the other only a manual `remove(GlobalId)` the caller must drive.

  **What keeps this open is two specific measurements, not an open-ended worry:** (1) does a
  per-element cost independent of model size survive at **100k elements** — the larger benchmark
  model is 3,822 `IfcProduct`, **4%** of the criterion's size — and (2) what does the **dependency
  fan-out** of a single wall move add, since this spike moved one placement and re-evaluated one
  element. The synthetic scale models in `reference/` cover the first; benchmark case 3 in
  `reference/README.md` ("a parametric change scenario") is still marked *to be written* and covers
  the second. The consequence clause above is already indicated for both implementations, on
  different grounds.

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
- **Correction to this entry's wording, recorded 2026-09-12, not resolved.** The paragraph above
  says the IFC2x3 convention is carried "on `IfcSite`". The reference implementation writes it on the
  **`IfcProject`**: `ifcopenshell.api.georeference.add_georeferencing` attaches `ePSet_ProjectedCRS`
  and `ePSet_MapConversion` to the `IfcProject` for IFC2X3, and for IFC4 and later builds an
  `IfcProjectedCRS` plus one of `IfcMapConversion` / `IfcMapConversionScaled` / `IfcRigidOperation`
  with `SourceCRS` set to the `IfcGeometricRepresentationContext` whose `ContextType` is `"Model"`
  ([`research/kernels/ifcopenshell.md`](research/kernels/ifcopenshell.md) §Georeferencing).
  **Which placement real exporters actually use is a separate measurement and has not been made** —
  the discrepancy is recorded here rather than resolved, because reading one implementation does not
  establish what the ecosystem does. The useful design finding from the same source is the *shape*:
  a **single API that degrades**, where the caller asks for georeferencing and the library decides
  which convention the schema supports — the right shape for our own `ifc/` layer.
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
- **Status:** open — raised by [`research/prior-art/onshape.md`](research/prior-art/onshape.md).
  **Partly addressed 2026-09-12** by
  [`research/kernels/freecad-topological-naming.md`](research/kernels/freecad-topological-naming.md),
  which supplies the mechanism and dated first-party evidence this entry previously asserted from
  general knowledge: FreeCAD's element map does not give a topological entity a persistent
  *identity*, it gives it a persistent **name string**, reconstructed after every recompute by
  walking which OCCT-reported "generated" or "modified" sub-shape each new sub-shape came from. That
  survives the common case — measured directly on a dimension change — and fails when a face splits
  into pieces distinguishable only by an arbitrary index, when the merge set changes, or when a
  feature is inserted earlier in the history. FreeCAD's own 1.0 release notes call it "not completely
  solved", and three of the five cited issues were filed *after* 1.0 shipped.

  **The design consequence the note adds, which this entry did not have:** memory-safety handle
  stability and recompute-identity are **different problems at different layers**, and the kernel
  spec's generational handles (§6) do not touch the second one. The proposed mitigation above —
  semantic references — is unchanged and is still the available answer; what is now evidenced is why
  no purely geometric scheme substitutes for it. The risk stays **open** because the boundary the
  Action names, where semantic references become insufficient, is still unlocated (see also R-07).

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
- **Findings:** [`spikes/blender-ceiling/results/blender.md`](../spikes/blender-ceiling/results/blender.md),
  read into [`research/kernels/blender.md`](research/kernels/blender.md) §Object-count ceiling
  (R-03, partial).
- **Status:** in progress — **half answered, and it is the half the register was uncertain about:
  the ceiling is Blender's, not Bonsai's.** Measured headless through `bpy` with no add-ons, one
  moved object costs **16.3 ms at 10 000 objects** and **332.1 ms at 100 000** — about twenty frames
  — while the first full evaluation of the 100k scene costs 11.5 s and the scene occupies 6.2 GB
  (≈63–65 kB per object). The same 1.2 M triangles held as **one** object cost **0.018 ms** per
  update, so what is being counted is Blender datablocks, not geometry volume — and no add-on can
  avoid that, because one IFC element must be one datablock for the element to be selectable and
  attributable at all.

  **What is not answered is R-03 as written**, which is about *viewport* interactivity: this is a
  headless measurement, so draw-call batching, the outliner and selection are unmeasured — all of
  which can make the number worse and none of which can make it better. A headless driver cannot
  close that gap; a viewport measurement would be a different spike. The figure above is therefore a
  **lower bound** that already consumes a frame budget at 10k objects. Blender is out as a *build
  on* candidate on three independent grounds anyway (licence, float32 storage, no embedding path),
  so this risk's remaining half no longer blocks a decision — it is kept for P-07, where it is the
  evidence that per-object overhead is the scale ceiling to design against.

### R-04 · Standalone renderer effort may be prohibitive
"Too expensive to build" is the strongest argument for adopting a host. It cannot be weighed
without a number.

- **Spike:** `spikes/renderer-scale/` — 100k individually selectable instanced elements, with
  capped section clipping.
- **Pass:** 60 fps with picking, reached in under two weeks of effort.
- **Fail:** below 30 fps, or the effort estimate exceeds a month.
- **Status:** open — `spikes/renderer-scale/` has not been run. **Partial evidence (2026-10-15)**
  from a different spike, [`docs/notes/findings.md`](notes/findings.md)
  §A real building, which draws a real building through its own Vulkan renderer written in DynLex:
  16,506 imported elements, 1,668,688 triangles, each element selectable by an ordinal carried in
  its vertices. *Measured* there: the wireframe frame on the whole model takes 21.5 ms of CPU time
  (80 ms before its edges moved to the GPU), and while zooming a 130,944-triangle storey 74 of 83
  stack samples wait on the GPU or the display. **Added (2026-10-16)**, §The 3D view in slots: an
  imported element made of one IFC mapped item is drawn as an instance of its shape (*measured* on
  Sixty5: 5,719 meshes, 1,096,799 of 1,627,128 triangles, as instances of 362 shapes); the section
  box is a cut in the fragment shaders and storey isolation a flag per element, so neither writes
  the mesh again. It still does **not** test this criterion: the instances are imported elements,
  not 100k generated ones; the cut is not capped; picking time and GPU frame time were not
  measured, the fps figure the criterion names was not taken, and the effort was not recorded in a
  form that answers "under two weeks".

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
  twelve candidate×setting combinations measured in one session, plus three added afterwards for
  `cadkernel`; every failure traced to a `problems.md` row.
- **Status:** in progress — measured for five candidates. The fifteen candidate×setting combinations
  split **11 FAIL / 3 neither-pass-nor-fail / 1 PASS**. The three that are neither are OCCT's three
  settings: OCCT is valid on all thirty case×setting combinations but its
  `sliver` identity residual (3.33e-08 relative) sits between the pass and fail lines, which the
  criterion as written does not name. The single pass is Blender's embedded Manifold solver, and it
  rests on a refusal the criterion cannot see — it returns operand A unchanged on
  `near_degenerate_triangle`, which happens to be the right answer for that case. The fifth
  candidate, `cadkernel` at `953d546b`, fails at all three settings for a different reason from
  every other: it **refuses** rather than answers wrongly — 7/10 valid and correct at the derived
  tolerance and at 1e-9, 6/10 at 1e-6, with an identity residual of exactly 0 on every case that
  ran, the only candidate whose residual is 0 at every setting; CGAL's f32-rounded row is also 0
  on the cases it completed, and like Manifold's and CGAL's figures, cadkernel's excludes the
  cases it refused (three). Not resolved: our own kernel is not measured, the set is planar and
  single-operation, and the five candidates were handed materially different constructions of two
  of the ten cases — `cadkernel` refuses both of those two outright.

  **The set must be extended before it is run against our own kernel (added 2026-09-12).** All ten
  cases are built from **bit-identical** coordinates, which is exactly the input class a symbolic
  tie-break wins: the set cannot distinguish exact predicates from a bit-equality tie-break, and
  `research/kernels/problems.md` P-03 states that no ADR may cite the 9/10 as evidence that it can.
  Cases whose coordinates are *not* bit-identical must be added, or the M5 run cannot tell which of
  the two mechanisms our own kernel implements. This is `problems.md` **N-01**'s mitigation and it
  is now named there and scheduled at spec §9 M5. Two further extensions the findings identify, both
  cheap once the driver exists: at least one curved-surface pair (**P-12**, where OCCT's own tracker
  concentrates and this set has nothing), and at least one *chained* sequence — OCCT's Probe A is
  the only chained measurement in the programme, and what it shows is that over eight fuzzy fuses
  the maximum entity tolerance rose **once** and then **plateaued**, while the *excess volume* grew
  linearly to 2.67e-5 m³; no other candidate was measured that way at all, so whether tolerance
  compounds anywhere is still unmeasured.

### R-17 · Precision far from the origin
The tile-frame design assumes f64 local coordinates are necessary and sufficient.

- **Spike:** `spikes/precision-set/` — identical geometry at the origin and at 500 km, through
  each candidate's boolean and tessellation, then re-centred and compared.
- **Pass:** maximum deviation below 1e-6 m in f64 paths.
- **Fail:** deviation above 1e-4 m — which for a float32 path is the expected outcome and the
  evidence ADR-0006 needs.
- **Findings:** [`spikes/precision-set/FINDINGS.md`](../spikes/precision-set/FINDINGS.md) — nine
  candidate×path combinations measured in one session, plus two added afterwards for `cadkernel`,
  with the local-frame mitigation measured on each candidate rather than assumed.
- **Status:** in progress — measured for five candidates, and the two populations are cleanly
  separated: **every f64 path passes** (OCCT **2.65e-10 m at its default setting and 3.61e-10 m at
  fuzzy=1e-5**, CGAL Epick 1.29e-10 m, Manifold `Mesh64` 3.29e-11 m, all one to three ULP of a 5e5 m
  coordinate) and **every float32 path fails**
  (Manifold `Mesh` 0.0186 m, CGAL f32-rounded 0.0348 m, Blender Exact 0.0348 m, Blender Manifold
  0.0435 m, Blender Fast 0.5 m), with three orders of magnitude of clear air between them and no
  candidate in between. That is the evidence ADR-0006 needs. `cadkernel`'s two f64 rows pass at
  **0 m** but **add no evidence**: they are measured on the two cases whose coordinates make the
  500 km offset exact in f64, on which every other f64 candidate also measured 0 m, and the one
  discriminating case is the one its constructor refuses. Not resolved: the spike sentence
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
  the implied exponent is 1.89 from 5k→20k and **3.03** from 20k→50k (the 50k figure is a single,
  19-minute run, not repeated — see the caveat in the findings). Memory is *not* the
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
  too: triangle/triangle 1.12×, BVH build 1.23×, orient3d 1.01× (a tie within noise, but a *mixed*
  PRNG+determinant figure — orient3d's clock starts before generation, and a PRNG-only diagnostic
  measured separately puts most of that 1.01× in the random draws, not the determinant; the
  *derived*, noise-sensitive determinant-only ratio stayed in the 1.0–1.2× range across repeated
  measurements — see the findings' finding I1). Worst case 1.23×, nothing near the 3× line.
  **Conditional on an explicit `-O` flag:** the compiler's default emitted-code optimisation level
  is `-O0`, not optimised — checked in-repo, not just asserted, by comparing a no-flag build
  against an explicit `-O0` build after neutralising the linker's embedded build timestamp — and
  unflagged it would fail on all three (9.09×, 6.78×, 21.14×) — the kernel's build must pass `-O2`
  or better. Not settled: no parallel, SIMD, boolean-pipeline or pointer-chasing workload was
  measured, and the compiler pin is dirty (see the caveat in the findings).

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

  **The precondition is met, the experiment is not run (2026-10-15).** The DynLex compiler is built
  and runs a Vulkan renderer in [the application](notes/findings.md):
  its own context (`graphics/vulkan/context.dl`) replaces the fixed per-frame arena with a growing
  stream buffer, and keeps a persistent indexed mesh whose vertices are stored relative to the
  scene's centre, with the centre-minus-camera shift computed in binary64 on the CPU and passed as
  shader parameters. After this session's changes a camera change uploads no mesh data; that is by
  construction, read from the code, not a measured byte count. The figures measured there (see R-04)
  are for one scene origin and no instance buffer, so they say nothing yet about the per-tile
  instance layout, the 500 km coordinate error, or 10⁵ instances — which is still this spike.

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
