# FINDINGS — the vertical BIM slice on the native DynLex kernel

## The question, restated

Does *parametric → geometry → 2D → IFC, with changes propagating* work end to end in
DynLex on the native `cadkernel` port, with stable identifiers, semantic references and
undo? Is a change re-evaluated fast enough to follow a gesture? The second half is the
mechanism behind R-01. Its criterion is single-element re-evaluation under 16 ms on a
100k-element model, and failure above 100 ms. This spike measures against that
criterion for its own element kinds. It does not change the status of R-01, which
belongs to the risk register.

## Hardware, OS and versions

*Measured.*

| | |
|---|---|
| CPU | Intel Core i7-10710U, 12 logical CPUs |
| Memory | 15 GiB |
| OS | Linux 6.14 |
| Kernel | native DynLex port of `cadkernel` at `953d546b68aef4b6692566a1a9b077fc5bd9fb4f` (see `spikes/dynlex-cadkernel-port/`) |
| DynLex | compiler 0.0.3, binary SHA256 prefix `211dd49f9e7caf92`; measurements at `-O2` |
| IFC check | IfcOpenShell 0.9.0 |

**Reference model.** None from `reference/`. The slice cannot import IFC (out of
scope), so every model was generated in code: the test models in
`examples/bim-slice/tests/` and the synthetic room grids of `scale_timing.dl`.

**Method.**
- Every number below comes from a program in `examples/bim-slice/tests/`, built at
  `-O2` and run from the repository root on an otherwise idle machine. Timings use
  the monotonic clock around the measured calls only.
- Medians and maxima are taken over the steps or moves stated. Kernel comparisons
  are medians of seven whole-process runs.
- `examples/bim-slice/README.md` gives the commands.

## What was built

All items in the README's scope table were built, with two differences. Snapping infers
horizontal and vertical alignment with the chain start, not perpendicularity. Sections
are produced and tested headless, but the interactive editor shows only the plan. The
code is in `examples/bim-slice/` of the DynLex checkout used for the kernel port.

- **Model.** Levels, compound wall types, walls on centrelines, parametric opening types
  with derived rough sizes, hosted openings, and dimensions whose ends reference
  semantic features (a wall end or side, an opening edge). Ids are 64-bit and never
  reused. Every change is a transaction, with unlimited undo and redo over model
  snapshots.
- **Geometry.** Footprints with L joins (side lines cut at their crossings) and T joins
  (cut at the host's facing side). Each wall is extruded through the kernel, and each
  opening is a kernel boolean difference.
- **Drawings.** Plans and sections are kernel plane slices of the evaluated solids; cut
  faces are filled. Dimensions are measured between resolved features and survive
  edits that move their walls.
- **IFC4 export.** Spatial structure, wall types with material layer sets, walls with
  layer-set usage, opening elements with voids, and windows with fills. Extruded bodies
  use the evaluated footprints. GlobalIds are deterministic, derived from the element
  kind and id.
- **Editor.** An event-driven core for tools, inference snapping, numeric length input
  during a gesture, end-point dragging with joined walls following, delete and undo. A
  native window shows the plan on the left and a shaded 3D view on the right, with a
  status bar giving the walls rebuilt and the time per change.

## Correctness — measured

- **Headless tests** compare complete printed results with expected files, and the
  values agree with hand calculations. Examples:
  - wall volumes 5.1152 / 3.84 / 5.76 / 3.84 / 0.9025 m³ with joins and openings;
  - a plan of 7 cut polygons totalling 6.222 m²;
  - a clear width of 2.89 m that becomes 2.39 m after the partition moves;
  - an opening pushed past its host's end reported as status 3, not clipped.
- **Incremental equals fresh.** A chain of five incremental evaluations matches a
  fresh evaluation wall by wall, in signature and status. An incrementally updated
  plan matches a fresh cut polygon by polygon, in area and position.
- **IFC.** IfcOpenShell reads the export as IFC4 with the expected entity counts,
  unique GlobalIds, storey containment, wall types and layer-set usages. Its own
  geometry engine reproduces every wall volume, openings subtracted, to within 1e-6 m³.
- **Interaction.** `drive_gui.py` drove the built editor through XTEST on a nested X
  server (Xephyr). The steps were:
  - draw four walls, one corner placed by a typed length;
  - place two windows and drag a corner with the joined walls following;
  - undo, redo and hover (showing the associative length, 6.000 m);
  - orbit the 3D view and export by key.

  Screenshots after each step showed the expected plan, 3D view and status bar.
  IfcOpenShell read the exported file back with 4 walls, 2 openings and 2 windows.

## Following a gesture — measured

Plans were first cut with the ported plane slice, which was too slow once walls carried
openings. A planar section operation was then added to the kernel (below), and plans use
it, falling back to the slice for solids it refuses. Both are reported.

**One room.** Four walls with two windows, drawn through the editor. One corner is
dragged in 200 steps (`drag_timing.dl`, three runs). The 0.05 m grid snap leaves most
steps on the same point; 15 steps change the model.

| Per step | Plan by slice: median / max | Plan by section: median / max |
|---|---:|---:|
| Changing step: evaluation and plan update (4 walls rebuilt, 4 re-cut) | 21.7–22.4 / 24.0–26.9 ms | 3.59–3.68 / 3.8–5.1 ms |
| Changing step: tessellation of the rebuilt walls for the 3D view | 2.06–2.08 / 2.6–3.4 ms | 1.99–2.09 / 2.4–2.4 ms |
| Unchanged step: evaluation and plan | 0–1 / 3–27 µs | 0–1 / 4–14 µs |

**Where the time goes.** One wall, cut at 1.2 m; the figures are medians over repeated
calls:

| Operation | Wall with a window | Plain wall |
|---|---:|---:|
| Extrusion and opening difference | 1.78 ms | 0.011 ms |
| Plan slice | 6.7–6.9 ms | 1.77 ms |
| Planar section | 5.1 µs | — |
| Signature | 1–2 µs | 1–2 µs |

With the slice, the plan dominated. The slice is two boolean intersections with
half-space boxes in the pinned source. With the section, the opening's boolean
difference dominates the rebuild.

**Kernel calls compared with Rust.** `wall_slice_workload.{dl,rs}` runs the same inputs
against the pinned crate, both at `-O2`. The figures are per operation: the median of
seven process runs over 400 or 200 iterations. Face counts are identical.

| Operation | DynLex | Rust | Ratio |
|---|---:|---:|---:|
| Window difference | 1.72 ms | 1.89 ms | 0.91× |
| Plan slice | 6.13 ms | 10.05 ms | 0.61× |

The port was not the bottleneck; the slice algorithm was.

## The planar section — built and measured

`lib/cadkernel/brep_section.dl` is a native extension of the port; the pinned source has
no such operation. It finds the closed loops in which a plane meets a closed body of
planar faces bounded by line edges, from the faces and edges, without splitting the
body. It follows the slice's rule that a plane missing or only touching the body has no
section.

**Method.**
- **Classification.** Vertices are classified by signed distance; a vertex within the
  operation tolerance counts as positive, as if the plane were moved infinitesimally.
- **Crossings.** Each crossing edge gives one point, computed from the edge itself, so
  both faces sharing the edge get the identical value.
- **Per face.** Crossings are sorted along the face's line of intersection with the
  plane, with an explicit tie-break for vertices on the plane, and paired in turn. This
  bounds the parts of that line inside the face, holes included.
- **Loops.** Pieces link into loops through their shared edges, with no distance
  matching. Outer loops run counter-clockwise and holes clockwise.
- **Refusals.** Curved faces or edges, a crossing face parallel to the plane, odd
  crossings and open boundaries are refused with distinct codes. The BIM view then
  uses the slice.

**Verification against the ported slice** (`tests/cadkernel/brep_section/`).
- **Bodies and planes.** Random cuboids, oblique concave prisms, prisms with notches,
  cuboid unions and walls with windows, cut by random planes; a fifth of the planes
  pass through a vertex.
- **Checks.** The section must bound the slice's caps on the negative part: equal net
  area, boundaries lying on each other, and equal perimeter. Where the slice does not
  divide, the section must be empty.
- **Results.** 5,000 cases at O2 (4,754 divided, 846 of them through a vertex, 246 empty
  on both sides) and 1,000 at O0 passed all three checks at 1e-9 relative. The worst
  O2 deviations were 4.45e-15 (area), 4.27e-14 (boundary) and 7.53e-14 (perimeter).
- **Fixture.** A required fixture with analytic cases passes O0/O2: a hole, an island in
  the hole, a plane through two edges, a pyramid at half height and at its apex,
  separate lumps, a wall at its sill, and two refusals.
- **Cost.** Over the 5,000 cases the section took 46 ms in total and the slice 61 s.

## Scale — measured

`scale_timing.dl` builds models of separate rooms, four walls each with L joins, on one
level and without openings. It moves one corner of the first room 20 times. Every move
examines 4 walls, rebuilds 3 and re-cuts 3 in the plan, at every size.

| Walls | First evaluation | First plan (slice / section) | Evaluation per move, median / max | Plan update per move, slice: median / max | Plan update per move, section: median / max |
|---:|---:|---:|---:|---:|---:|
| 4 | <1 ms | 8 ms / <1 ms | 0.07–0.09 / 0.13–0.19 ms | 5.7 / 7.9 ms | 7 / 14 µs |
| 100 | 2 ms | 0.25 s / <1 ms | 0.07–0.08 / 0.14–0.17 ms | 5.4 / 7.6 ms | 7 / 8 µs |
| 400 | 7–9 ms | 0.72 s / 1 ms | 0.07–0.09 / 0.11–0.14 ms | 5.4 / 6.4 ms | 7 / 9 µs |
| 1,600 | 31–37 ms | 2.9 s / 11 ms | 0.09–0.11 / 0.21–0.25 ms | 5.5 / 6.0 ms | 8 / 30 µs |
| 6,400 | 128–146 ms | 12.8 s / 31 ms | 0.12–0.16 / 0.19–0.82 ms | 6.1 / 7.6 ms | 8 / 10 µs |
| 99,856 | 2.3–2.7 s | 215 s / 0.47 s | 1.17–1.25 / 2.3–3.8 ms | 6.1 / 7.1 ms | 10 / 22 µs |

Ranges span the two runs (slice and section); evaluation does not depend on the plan
method. On 99,856 walls a corner move now costs about 1.3 ms at the median and under
4 ms at most for evaluation and plan together. The process peaked at 1.49 GB resident
with that model and its plan; memory was not optimised.

**How this was reached.** The first version cached each wall's solid by a signature of
its inputs and was correct, but it was not incremental at scale:

| Version | 1,600 walls, evaluation | 99,856 walls, evaluation |
|---|---:|---:|
| Signature cache only | 103 ms | not run (quadratic) |
| Record diff, spatial index and serials, index copied each time | 0.68 ms | 66 ms |
| Index updated in place | 0.23 ms | 28 ms |
| Evaluation lists also updated in place | 0.11 ms | 1.17 ms |

The first version recomputed every wall's signature on every change. Each footprint
searched all walls for joins, and each cache lookup was linear. The plan view had the
same shape: 29 ms at 1,600 walls, and 25.9 ms at 99,856 walls until removing and
re-inserting entries was replaced by replacing them in place.

What made evaluation incremental:

1. **Change detection.** The evaluation keeps a private snapshot of the model, compared
   record by record. This is a merge over id-ordered lists, about 10 ns per wall. It
   yields the changed walls, wall types, levels, openings and opening types.
2. **Dependents.** A spatial hash of wall centrelines finds the walls that can join a
   changed wall, before and after the change.
3. **Rebuilds.** Only those walls compute a signature; a changed signature means a
   rebuild and a new serial number.
4. **Downstream caches.** The plan and the 3D meshes key on the serial, and each
   evaluation update lists the walls it changed.
5. **In-place updates.** The index, the wall-geometry list, the snapshot and the plan
   are updated in place by binary search. A remaining O(n) pass of about 10 ns per
   wall is the 1.2 ms at 100k.

## Follow-up: the fast planar kernel

Walls are now built directly by a light planar kernel when possible; see
`spikes/dynlex-fast-kernel/FINDINGS.md`. The room drag step fell from 5.7 ms to
0.11 ms, a wall with a window builds in 2.9 µs instead of 1.94 ms, and memory at 100k
walls fell from 1.49 GB to 315 MB. The measurements in this file are those of the port
path.

Doors and slabs followed on the fast kernel, also described there:
- door types, exported as `IfcDoor`;
- slabs, evaluated incrementally like walls, picked in 3D and exported as `IfcSlab`;
- spaces derived from the walls, exported as `IfcSpace`;
- selection in the plan and the 3D view;
- storeys, with the storey below outlined in the plan, and each element contained
  in its own storey in IFC;
- a native text file format that keeps ids and reads back the exact numbers. A
  round trip of the example house 500 km away gives identical text and geometry.

The example house now has three doors, a ground slab and a first floor.

**Interactive speed: text, not geometry.** The user reported that the plan lagged.
Timings per frame phase (O2, in a nested X server) showed the cause.

- **Text.** The font module rendered each character with FreeType and uploaded it
  as a texture. Each upload waits for the graphics device to finish. The status line
  alone cost 6.7 ms, and the frame 28.8 ms of CPU time.
- **The fix.** A glyph atlas renders the printable characters once at start. A line
  of text is then one batch of textured triangles. The frame fell to 4.3 ms.
- **What remains.** Most of the remaining time is one framebuffer-size query, a
  synchronous round trip to the X server; this is slower in the nested server used
  for the measurement than on a desktop.
- **Other changes.** The loop's fixed 8 ms sleep was removed, because presenting
  already waits for the display's refresh. The status bar shows the CPU time of each
  frame.

**Panning, second round.** The user still felt lag when panning the plan. With
hatching and grids added, a pan frame took about 10.7 ms. Medians per phase over
about 1,300 frames of a recorded pan:

- **Recording the plan.** Panning only shifts the plan, so the plan (spaces, the
  storey below, hatched cuts, door and window symbols, grids and labels) is now
  recorded once as coloured triangles and labels (`bim_canvas.dl`). It is replayed
  shifted, and recorded again only when the revision, the plan's evaluation
  generation, the storey, the zoom or the plan's view rules change.
- **Recording the 3D view.** The 3D view is recorded the same way, as depth-tested
  triangles. It is recomputed only when its camera, the meshes, the selection or
  its rules change.
- **Round trips to the X server.** After the recordings a frame took 5.8 ms, of
  which 4.5 ms were round trips: GLFW asked for the framebuffer size and the cursor
  position on every call. The DynLex graphics runtime (`src/runtime/graphicsRuntime.c`)
  now keeps both current from GLFW's callbacks, and the frame start reads the
  cached size too.
- **Result.** A pan frame now takes **1.1 ms of CPU time** (median, nested X
  server). Replaying the plan takes 0.5 ms of that.

## Far from the origin — measured

`far_origin.dl` builds the same house twice: around the origin, and moved far away.
The house has six walls, seven windows and three spaces, and is turned by the same
angle in both copies. Every derived result of the far copy is moved back by the offset
and compared with the near copy. One corner of each is then moved 5 cm.

| Offset (m) | Turn | Plan points | Section points | Wall volumes | Space areas |
|---|---:|---:|---:|---:|---:|
| 500,000 / 500,000 | 0 | 2.6e-11 m | 2.6e-11 m | 1.4e-9 m³ | 5.8e-10 m² |
| 500,000.123 / 499,999.987 | 0.3 rad | 3.7e-10 m | 1.6e-10 m | 2.3e-9 m³ | 7.5e-10 m² |
| 155,000 / 463,000 | 1.1 rad | 2.8e-10 m | 5.2e-11 m | 1.2e-9 m³ | 2.9e-10 m² |

- **Agreement.** All walls evaluate in both copies, with the same number of plan,
  section and space polygons.
- **The edit.** The 5 cm edit rebuilds the same walls (4 or 5) in both copies, and the
  moved volumes agree to 1.9e-9 m³.
- **Speed.** Full evaluation (17–21 ms) and the edit (15–19 ms) take the same time near
  and far.
- **Why it works.** At 500 km the working coordinates keep about 10 decimal digits
  below the metre, and every step here works in binary64 world coordinates.

The editor shows such a model correctly once its camera is centred on it. The plan and
3D projections subtract the camera centre in binary64 before converting to the
graphics pipeline's single precision. The F key fits the camera to the model, and
`--example X Y` opens the example house at those coordinates.

**Not covered.**
- The IFC export writes the large coordinates directly. It does not use a local
  placement or a map conversion, though IFC files are commonly georeferenced that way.
- The kernel's operation tolerance grows with coordinate size. Its effect on booleans
  between nearly touching elements far from the origin was not probed.

## What this means for R-01

For the element kinds of this slice, on this machine, R-01's criterion is met, with and
without openings:

- **At scale.** On a 99,856-wall model a single wall edit with its join fan-out
  re-evaluates, with the plan updated, in about 1.3 ms at the median and under 4 ms at
  most.
- **With openings.** In the room whose walls carry windows, a changing drag step takes
  3.6–3.7 ms, against the 16 ms budget.
- **Flat cost.** Cost per change is flat in model size apart from the cheap diff.
- **What dominates now.** The opening's boolean difference (1.8 ms per wall with a
  window) and the 3D tessellation (about 2 ms for the room).

Plan cutting with the ported slice met the criterion only for walls without openings:
22 ms for the room with windows. The gap was closed by a kernel operation that the
ported source does not have. The evidence for the unmodified port is therefore the
slice column. The kernel needed one operation suited to interactive drawing, and it
was small: 361 lines.

Limits of this evidence:

- the models are synthetic (separate rooms, one level, no openings at scale);
- only one kind of edit was measured;
- there is one element family;
- the 3D view tessellates and draws every wall each frame, which this spike does not
  scale;
- the planar section handles planar faces with line edges only. Curved walls, which
  this slice does not have, would fall back to the slice and its cost.

Hosts and openings are still found by scanning the openings list for each examined
wall, which is O(openings) per examined wall.

## DynLex observations

- **Language pitfalls found here.**
  - `and`/`or` do not short-circuit. This caused three out-of-range reads at index −1
    in this spike, all in "first element" checks.
  - A local variable may not share a word with its function's pattern. This caused
    several compile errors, each reported on the call rather than on the variable.
  - A class name inside a pattern breaks the pattern.
  - Literals default to 32 bits.
- **Runtime behaviour.**
  - The graphics runtime refuses an empty triangle batch, which aborts the program.
  - Font drawing positions must be integers.
  - libc `clock()` counts all threads, including the Vulkan driver's.
  - Shifting elements in a managed list retains and releases each one. Replacing in
    place rather than removing and re-inserting turned the 100k plan update from
    25.9 ms into 6.1 ms.
- **Compile times** stay long (R-18). The editor takes 3 min 53 s at `-O2`, and each
  headless test 3–5 min at `-O0`.

## Consolidation notes (2026-10-13)

- **One join, many roles.** Mullions, transoms, beams and columns now share one derived
  join (`the bim end cuts of parts`, `bim_network.dl`): each end is cut by a plane found
  from where the elements lie. Nothing about joins is stored. The services network's
  connectors and nodes already gave pipes and ducts their fittings; the new joins sit
  next to it and use the same "derive, don't store" rule.
- **A table per feature costs six to eight edits.** Wall base and top level, building
  system panels and grid lines, and a view's display each needed the record or table,
  every constructor, the `.bim` writer and reader, and the IfcX writer and reader. A
  record's field can be set on a local copy (`set copy's field to …`) and the copy put
  back, which avoids repeating whole constructors; the older code repeats them.
  One generic mechanism for extra element data is the main consolidation target.
- **Whole millimetres.** Moved grid lines are stored as whole millimetres, so the file
  carries no long decimals. The same rule fits the wider wish to avoid needless
  decimals while editing.
- **DynLex names.** A local may not share a word with a pattern the function calls. This
  session hit it again in `cuts`, `rank`, `frame`, `toward`, `reach`, `along` and
  `display`.
- **Two more DynLex traps.**
  - A vector literal with commas (`a cad vector3 with x 0.0, y 0.0 and z 0.0`)
    passed as an `@intrinsic("construct", …)` argument is split at its commas;
    it needs brackets.
  - A parameter named like a word of its own pattern (`bim kind {integer:kind} has
    control points`) leaves calls unresolved, reported far from the cause.
- **`main.dl` is compiled only by the application build.** A slip there costs a
  40-minute `-O2` build. `build.sh dev` (`-O0`) type-checks it first.
- **Element settings.** Building system panel types and moved grid lines now live in
  one table of element settings (element, code, whole-number value), with one `.bim`
  line kind and one IfcX attribute for all of them. Older files still read. The rule:
  data read on every evaluation (a wall's base and top) stays a record field, since a
  table scan per element would not scale; rarely read extra data goes in settings.
- **Modules.**
  - `main.dl` (5,800 lines) became four files: the plan panel, the 3D and section
    panels, the application's parts, and the loop itself (1,560 lines).
  - `bim_editor.dl` (6,900 lines) became three layers: the core, the properties
    window, and what only the window drives (keys, two-letter commands, box
    selection, files, the type library).
  - Imports cannot be cyclic, so shared helpers (projection, edges) moved down to the
    lowest panel module.
  - Eight functions no longer called anywhere were removed.
- **Connections.** Joins between linear elements are now detected as connection
  records (which end meets which element, at an end or along its body) before any
  cut is made. Each end can choose a kind (automatic, mitre, butt, through, open),
  kept as an element setting. Later connection details (plates, bolts) can read the
  same records.
- **One building system, many systems.** Curtain walls, masonry, timber frames,
  floors and ceilings share one generator:
  - a pattern (grid or running bond);
  - joints of a chosen width and depth (none at width 0);
  - cells of a planar type, or none;
  - point objects as short rods at the grid's nodes.
  - Layers are building systems that follow a host's line, height and curve, offset
    across its face; nested systems fill a host's panel.
  - All of it is element settings. The record changed only for the curve.
- **Openings in a building system.** An opening can be hosted by a system, which
  follows its opening rule: cut and frame, replace panels, or ignore. Everything that
  looks up an opening's host wall checks that the host is valid, so a system host
  needed no other change.
- **A third DynLex trap.** Reading a member of a call's result inside a larger
  expression (`the length of ((the bim handles of …)'s values)`) gave a garbage value
  at `-O0`. Binding the result to a local first works. Drafted as an issue in
  `~/dynlex-issues/7-temporary-field-garbage.md`.
- **Memory.** A second Claude session compiling in its own clone, plus two compiles
  here, got one of them killed for memory. With another session active, compiles run
  one at a time.

## A real building, its colours, and a 3D view that the camera does not rebuild (2026-10-15)

**Model.** Sixty5, Strijp-S, Eindhoven: a residential building completed in 2020,
published as IFC2x3 per discipline under CC BY 4.0 in the buildingSMART community
sample files
([source](https://github.com/buildingsmart-community/Community-Sample-Test-Files/tree/main/IFC%202.3.0.1%20(IFC%202x3)/SDK%20-%20S1),
mirrored per file at
[huggingface.co/datasets/sylvainHellin/ifc-bench](https://huggingface.co/datasets/sylvainHellin/ifc-bench/tree/main/projects/sixty5)).
The architecture file is 342,657,851 bytes. *Measured* with IfcOpenShell 0.9.0: 19
storeys; one typical storey (`02 tweede verdieping`) holds 1,320 elements, among them
527 walls, 95 doors, 67 windows and 66 furnishing elements. Not added to
`reference/`: the benchmark set there is fixed, and this note does not change it.

**Import.** *Measured* on the hardware above, through the 3D view's import message,
two runs each, the DynLex STEP reader at `-O2`: 16,506 elements, 1,668,688
triangles, 16.77 s and 16.77 s before this session's changes, 16.88 s and 16.97 s
after (about 1% more, for the colour groups and the storey bookkeeping). Peak
resident memory 1.41 GB (`/usr/bin/time -v`, before the changes). A profile of the
import (60 stack samples) is 70% `the cad triangulation of`, before and after alike.

**Colours per item.** Furnishing elements showed black: a kitchen block's items are
styled black paint, red granite and pine, and the reader gave each element the first
colour it met. It now draws each item in its own `IfcStyledItem` colour, else in the
colour of the item it is part of (a mapped item, a boolean result), else in the
category's, and an element becomes one scene mesh per colour, as a wall shown in
layers already was. `tests/ifc_read.dl` covers an item set of three colours, a
mapped item styled as a whole (with its cache kept per inherited colour) and a
boolean styled as a whole.

**A cut cap left out.** The same test exposed a fault older than these changes: a wall
clipped by a half space at y = −8 m lost the cap on its cut (14 triangles and 133
litres instead of 200); the identical wall at y = −5 m kept it. The cut's ring has a
point where each side face's diagonal crossed the plane; at −8 m rounding left those
points just off their neighbours' line, and the triangulation produced nothing. Such
points are now dropped before triangulating (*measured*: all four variants closed at
200 litres; the cap is 2 triangles instead of 6).

**Zooming hitched.** *Measured* by sampling the editor's stack under `gdb` (SIGINT
every 70 ms while scrolling the wheel in and out, 84 samples per run) on the storey
above (130,944 triangles):
- Before: 36% of samples in work the camera caused: the ground and shadows were
  projected again on the CPU for every triangle at each camera change (models up to
  150,000 triangles get shadows), and the recording was streamed to the GPU vertex by
  vertex every frame.
- With shadows switched off the same work was absent, which settled the cause.
- After: the ground and shadows are triangles in the world, computed when the shown
  meshes change and kept in the GPU mesh as its first indices (unlit, element ordinal
  −2), drawn only when the camera looks down. 74 of 83 samples wait on the GPU or the
  display; none is in the projection or the stream.

**Edges.** *Measured* on the whole model in the wireframe mode, the status bar's frame
time: 80 ms before, 21.5 ms after. The feature edges were projected and streamed on
the CPU every frame; they are now a second index list of lines between the GPU mesh's
own vertices, drawn through the same camera. The faces are pushed back by a depth bias
(constant 2, slope 1.5) so that hidden-line edges lie in front of them. Welding by
position and finding feature edges were written twice (the GPU upload and the plan's
folded components); both now use one welding and one edge function.

**Storeys.** Imported elements now carry the storey that contains them: IFC through
`IfcRelContainedInSpatialStructure`, else the whole they are a part of
(`IfcRelAggregates`), followed up to an `IfcBuildingStorey` at its placement's height;
IfcX through the `IfcBuildingStorey` node above them. *Isolate storey* (View) keeps in
the 3D view what belongs to one storey, native elements by their level and imported
ones by their storey, matched by elevation; Page Up and Page Down over the 3D view step
through the storeys. On Sixty5 it showed `00 begane grond` merged with the native
`Ground floor` at 0, and stepped to `02 tweede verdieping`.

**Imports in the plan (2026-10-16).** *Storeys from IFC* (Collaborate > Import)
adds a storey to the model for each imported storey it lacks, so each gets a plan;
the plan cuts the imported elements of its storey at the cut height, with their
edges below the cut thin and grey, through the same function as folded
components. *Observed* on Sixty5 in the running build: the storeys were added
(`03 derde verdieping` at 10,900 mm, 3,200 mm up to the next) and Page Up showed
its plan with walls, kitchens and sanitary items; zooming that plan reported a
frame time of 16 ms. The cut is drawn as lines, not filled, and sections do not
show imports.

**Smaller findings.**
- `shaders/mesh_fragment.spv` was older than its source (changed 2026-10-12, binary
  2026-10-09); rebuilt. The shaders build with the compiler that carries the shader
  extensions (`~/dynlex-shader`, run from its checkout so that its `lib/shader.dl`
  is found).
- A view cube was added to the 3D view (26 directions).
- DynLex: a local named like a word of a pattern called in its own assignment
  (`set part to the bim ifc part in …`) leaves the call unresolved; `the bim ifc
  part`, `size`, `length`, `a`, `from` all had to be renamed. Compiling
  `tests/ifc_read.dl` at `-O0` takes 13 to 18 minutes and the application at `-O2` 51
  minutes, before and after these changes alike.

## The 3D view in slots: zoom, filters in the shaders, instances (2026-10-16)

**Question.** Zooming the 3D view on Sixty5 lagged. Reading the code showed why: each
time the zoom crossed a level of detail, the whole model was meshed again and written to
the GPU as one mesh. That cost was not measured before the change, and only the "after"
below is a measurement. The same single mesh meant that isolating a storey, toggling a
category or moving the section box also wrote the model again.

**What changed.**
- **Slots.** The GPU keeps the model in four mesh slots: the ground and shadows, the
  imported elements, the shapes imported elements share, and the native elements. Each
  slot is written again only when what it holds changes.
- **Flags.** Which elements show (the 3D view's categories, its phase, an isolated
  storey) is a float per element ordinal in the shaders' storage buffer. The vertex
  shaders read it and move a hidden element's corners out of view, its shadow included.
- **The section box** is a cut in the fragment shaders. The shader compiler got a
  `shader discard` intrinsic for it (`llvm.spv.discard`, SPIR-V `OpKill`, in
  `patches/dynlex-shader-extensions.patch`).
- **Instances.** An IFC element made of exactly one mapped item places its mapped
  representation's mesh. The import keeps the shape once, in its own coordinates, and
  each element's transform. The GPU welds and smooths each shape once and draws it
  with one instanced draw. The meshes in the world stay for picking, the plan and the
  section.
- **A zoom queue.** Zooming past a level of detail queues the native round shapes to be
  meshed again. The shapes covering most of the 3D view come first, in classes a factor
  of two apart; shapes outside the view count a sixty-fourth. Each frame takes from the
  queue for at most 6 ms, in chunks sized to about a quarter of that, and only meshes
  that come out different count as a change.

**Measured** on the hardware above, Sixty5 with the native conversion of the same day
(903 native elements; 15,460 imported, 1,627,128 triangles), in a 1440 × 900 window:
- **Uploads.** Writing all four slots once took 377, 389, 403 and 410 ms in four runs.
- **Zoom.** 12 wheel steps in, from the whole building to a few balconies: the
  status bar's upload count stayed at 1. The levels of detail are a factor of two
  apart, so that zoom crossed several of them.
- **Filters.** Isolating a storey, Page Up three storeys, turning the section box on,
  dragging its top face and turning it off: the upload count stayed at 1, with frames
  of 14 to 17 ms over the whole building.
- **Instances.** 5,719 meshes, 1,096,799 of the 1,627,128 triangles (67%), are drawn
  as instances of 362 shapes. A count of faces in the STEP text beforehand had
  estimated 65%.
- **The cost of a cut.** It showed in a fixed view: *Fit*, then 12 wheel steps, then
  four frame-time samples. Fragment shaders without discard took 24.9 to 28.8 ms. The
  same shaders with the box test, box off, took 31.0 to 31.7 ms, since a shader that
  can drop fragments loses the GPU's early depth test. The cut now has its own six
  pipelines (faces, edges, wires, each plain and instanced), drawn only while the box
  is on. With them, the box off took 24.1 to 27.2 ms. The faces' and edges' shading is
  one shader library (`lib/vulkan/shaders/mesh_shading.dl`) that both variants import.
- **Tests.** `tests/zoom_queue.dl`: three columns, two of them round, meshed coarse, and
  then the first two made again fine. The round one came out as the fine mesh made
  whole (468 corners), the square one as it was, and the untouched round one stayed
  coarse (132). `tests/ifc_read.dl`: of the small file's mapped items, only the green
  column (one mapped item) places a shape, 11,000 mm along x; the columns of two mapped
  items do not. Both pass in a bundle with `pick`, `editor`, `linear_tool`, `curtains`,
  `ifc_native` and `views`.

**Not measured.** The GPU's own frame time and the GPU memory saved by instances. The
zoom queue in the running editor on a model with many native round shapes; Sixty5's
native elements are walls and floors. The time picking takes to clip the model to the
box after a drag ends, when its list is filtered again.

**Left as it is.**
- Shadows (models of up to 150,000 triangles) show whole elements even where the box
  cuts them.
- The cut has no cap.
- A new view mode or halftone writes the imported elements again, since their colours
  are in their vertices.
- An instance's normal is turned by its axes, not by their inverse transpose, so a
  non-uniform scale shades slightly wrong.
- Kept meshes are found by their position in the list. Should an element come out in
  another number of meshes, everything is made again.

**DynLex.** A local named like a literal word of its own function's pattern turns into
a parameter of that function: "'queue' is a parameter because it was used here". In
`the bim zoom queue of …` a local `queue` cost a 15-minute build; `shade` and `outside`
did the same in the shaders. The compile memory and the variation in build time follow
from the clones of type-inference trials, which are not freed until the parse context
goes (reported as dynlex#13).

## Review of the running build (2026-10-19)

The maintainer ran the `-O2` build of 2026-10-16 with `--import` of the Sixty5
architecture file.

- **Navigation.** *Observed* by the maintainer: zooming and orbiting are smooth.
- **Start-up.** The editor is not usable until the import has finished. The window
  opens first, but the IFC import runs before the first frame, then the meshing and
  the GPU upload follow. *Measured* in that run, from the import message: 12,489 ms
  for the import (15,460 elements, 1,627,128 triangles; 715 walls, 143 openings and
  188 floors made native). The status bar gave 393 ms for the last upload. The time to
  the first frame without an import was not measured. The maintainer's requirement:
  the editor is interactive within 1 s of starting. Anything slower loads in the
  background, behind a loading screen that names the step under way and counts the
  steps.
- **Isolate storey out of reach.** *Observed* by the maintainer: in a smaller window,
  *Isolate storey* does not show. The cause, read from the code: the ribbon lays its
  groups out from the left at full size, with no compact form and no overflow, so the
  groups past the window's right edge are drawn off screen. Under View > All, *3D mode*
  is the seventh of eight groups.
- **Wanted next.** A realistic view: transparent glass and shadows that elements cast
  on each other (a shadow map), as proposed on 2026-10-16.

## Start-up in the background, the triangulation, and a realistic view (2026-10-19)

**The import's time.** Sixty5's architecture import took 12.5 s (above). Sampling its
stack under `gdb` every 100 ms, with the callee-saved registers recorded, showed two
calls of `the cad triangulation of` that took about 5 s each (*measured*, under the
debugger). Each was a face of about 1,800 corners: the registers holding the ring
stayed the same while a count fell from 1,812. The ear clipping
(`lib/cadkernel/triangulate2.dl`, ported from cadkernel) tests every corner against
every other point for each ear it cuts, which is O(n³). The overlay's copy now keeps,
for each corner, whether it turns left and how many points lie in its triangle. A cut
changes the triangles of its two neighbours only; every other corner loses at most the
cut point. That makes it O(n²), with the same ears in the same order.
- *Measured* against the toolchain's version, on the same driver: identical output for
  600 random rings, with holes, and rounded to whole numbers so that points repeat and
  lie in line. A comb of 1,804 corners took 6.04 s before and 0.054 s after.
- The toolchain's own triangulation tests (`cadkernel_triangulate2` and its ownership
  test) pass with the overlay's copy. `tests/triangulate_comb.dl` keeps the comb.
- Sixty5's import took 5,482 ms after the change, with the same 15,460 elements and
  1,627,128 triangles.

**Start-up.** A loading screen counts the steps of the start (the window, the fonts,
the editor). A file given with `--import` is then read on a POSIX thread while the
editor runs. A card over the canvas names the step under way, how far it is, and the
time so far. *Measured* on Sixty5 with the `-O2` build:
- From the first statement to the first frame shown: 221 ms. Of that, the window
  (Vulkan, its pipelines) took 182 ms, the fonts 37 ms, the editor below 1 ms.
- The window was on screen 0.35 s after `build.sh run` was started. That figure
  includes copying the tree; the 221 ms does not include the process's own start.
- The editor answered during the import: frames of 3 to 16 ms in the status bar.
- The import's thread took 5.5 s. The frame that takes its result then meshes the 903
  native elements (25 ms) and writes the GPU's slots (400 ms), so it stalls for about
  0.4 s.

**DynLex and threads.** `the function named "…$"` gives an exposed function's C
address, and `pthread_create` runs it. A function reached only that way is compiled
without its list code: any list append in it, however deep, stops the compiler with
"runtime call argument produced no value". Calling the function directly first, in a
branch that never runs, works around it. DynLex counts references to strings and
lists without atomics, so the thread works on an editor and an import record of its
own, and the window's thread touches them only after it has joined the thread.

**The ribbon in a narrow window.** A tab's groups that do not fit become compact (their
buttons small, three to a column), from the last group back. When even that is too
wide, arrows scroll the ribbon by a group. Sub-tabs that would run into the tabs are
left out. *Observed* at 1,000 pixels wide: View showed Create, Windows, Drawing types
and Phasing with an arrow, and three clicks on it brought *Section box*, *Isolate
storey* and *Realistic* into view.

**The realistic view (removed the same day).** It was built and measured as below, then
taken out at the maintainer's decision: the editor is to be as lean as it can be, and a
realistic view may come later as an extension installed through the Open AEC
installer. Its code is kept as `patches/overlay-realistic-view.patch`. It was reached
through View > 3D mode > Realistic, the 3D view's Graphics menu, or Ctrl+5.
- **Shadows.** The sun lights the faces through a shadow map: the model is drawn
  from the sun into a depth image of 4096 × 4096. The faces' shader compares each
  point against it, averaging four texels.
- **When the map is drawn.** The sun is fixed in the world, so the map is drawn
  again only when the model or what shows changes, not when the camera moves.
- **Sky and glass.** The sky lights every face, more from above. Glass, an IFC
  surface style's transparency, is blended over the other faces. It is more opaque
  and reflects the sky at a glancing angle (Schlick's approximation), and it carries
  the sun's highlight.
- **Cost at start-up.** Its ten pipelines and the map are made the first time the
  view is chosen, so the start does not pay for them. Choosing it writes nothing to
  the GPU again: the upload count stayed at 1.

*Observed* on Sixty5: the parapets cast their shadows on the terraces. With one
storey isolated, the map was drawn again and the walls' shadows fell across the
floors. The status bar's frame time was 16 to 22 ms. That is the CPU's time per
frame, not the GPU's.

**Tests.** A bundle of `ifc_read`, `zoom_queue`, `pick`, `editor`, `linear_tool`,
`curtains`, `ifc_native`, `views`, `triangulate_comb`, `api` and `reinforcement_editor`
passes. It was run by hand: `build.sh bundle` stops on two warnings in `api.dl`'s
prints, which are older than these changes.

**Not measured.**
- The GPU's time for the shadow pass or for the realistic faces.
- The start without an import, and the start on another machine.

**Left as it was then** (the first two are resolved in the next section; the others
went with the realistic view):
- The frame that takes the import's result stalls for about 0.4 s.
- Collaborate > Import > IFC still imports in the window's thread.
- Glass is blended in the order it was written, not sorted by depth.
- The ground is only drawn for models of up to 150,000 triangles, so on Sixty5 the
  map shades no ground.
- Native elements have no glass yet: a curtain wall's panels are opaque.

## The GPU's uploads off the window's thread, and frames only when needed (2026-10-19)

The maintainer's requirements after the review:
- Uploads to the GPU happen in the background and no faster than the GPU takes them.
- Frames are paced by vsync where the GPU is not the limit.
- The time a frame takes is shown, so that it can still be optimised, but no
  computing power is spent while nothing changes.

**The import's upload.** The import's thread now writes the imported elements for
the GPU into buffers of its own: vertices, indices, edges and instances, in
host-visible memory that the GPU reads directly.
- It makes those buffers through a device record of plain pointers, so that it
  touches no list the window's thread counts. Creating Vulkan objects needs no lock.
- The window's thread then installs them, once the GPU is idle, and adds the walls
  and floors the thread found to the model, as one undoable step.
- Collaborate > Import > IFC starts the same job. The model may be edited during
  the import: the walls and floors are added to the model as it is then.
- The window's thread draws at most one frame ahead of the GPU: each frame waits
  for the one before. Presenting waits for the display (FIFO).

*Measured* on Sixty5:
- The thread took 4,501 ms in all, of which 549 ms were the GPU's buffers.
- The frame that took the result spent 5 ms on it, against about 400 ms before.
- The first 3D frame after it wrote the native elements and the ground in 12 ms.
- Same model as before: 15,460 elements, 1,627,128 triangles.
- From the first statement to the first frame: 95 to 107 ms.

**The colours a view mode or the rules change.** The hidden line view's grey is a
shader parameter, and the halftone of the 3D view's rules is a value of each
element's flag (2: faint), both applied by the vertex shaders.
- The imported elements are written with their feature edges whatever the view
  mode, so a new import is the only thing that writes them again.
- The native elements are written again when edges become needed.
- *Measured:* switching to Hidden wrote only the native elements, in 14 ms.

**Frames on demand.** When twenty frames in a row saw no input, no edit, no camera
still settling and no drag, the loop waits for the window's next event instead of
drawing (`glfwWaitEventsTimeout`). It wakes on its own only while there is
something to update:
- a running import, four times a second for its card;
- a letter waiting for its second, ten times a second;
- the automation API, ten times a second;
- work in the zoom queue keeps it drawing.

*Measured*, the editor's CPU time over 10 s without input, from `/proc`:
- Before (`--example`): 6.1 to 7.5 % of one core.
- After: 0 ticks, both with `--example` and with Sixty5 imported.
- After 10 s of rest, a scroll was answered and drawn at once.

**Frame times.** The status bar shows the last frame's time on the CPU (the work
before presenting) and on the GPU (two timestamps around the frame's commands,
`vkCmdWriteTimestamp`). *Measured*:

| Situation | CPU | GPU |
|---|---|---|
| Plan view while the import ran | 0.3 ms | 1.5 to 2.2 ms |
| Whole of Sixty5 in the 3D view, shaded | 15.8 ms | 13.5 ms |
| Whole of Sixty5 in the 3D view, hidden line | 21.4 ms | 15.5 ms |

**The row of tabs in a narrow window.** It leaves out the title, then closes up,
then letters its tabs smaller. *Observed:* all ten tabs fit at 1,000 pixels without
the title, and at 880 with smaller letters.

**A start without arguments aborted.** `the argument at 0` was read in a condition
`(length > 1) and (… = "--import")` even with no arguments. DynLex's `and`
evaluates both sides, so the list's bounds check stopped the program. The committed
`main.dl` has the same condition (read from the code; that build was not run without
arguments). The first argument is now read only when there is one, and a start
without arguments runs.

**Tests.** `build.sh bundle` with `ifc_read`, `zoom_queue`, `pick`, `editor`,
`linear_tool`, `curtains`, `ifc_native`, `views`, `triangulate_comb`, `api` and
`reinforcement_editor` passes. The working tree had the bracketed prints of
`tests/api.dl` by then, so it ran without stopping on warnings.

## The properties panel (2026-10-19)

The maintainer reported that the properties panel does not work well. Checked in
the running build with Sixty5 imported:

- **An imported element showed the wrong things.** *Observed:* with an imported
  IfcBeam selected, the panel showed a wall type to choose, the active storey, a
  view, the project and the element's phases. Nothing about the beam itself. The
  cause, read from the code: the panel's rows come from the editor, which does not
  hold the import, so an imported selection fell through to the rows shown with
  nothing selected. The window now builds those rows from the import: IFC class,
  GlobalId, name, storey and its elevation, read only. The type box names the IFC
  class and opens no list, and there are no phase rows (setting a phase would have
  written phasing for an id that is not in the model). *Observed* after the change:
  an IfcWall from Sixty5 shows its class, GlobalId and storey (`00 begane grond`,
  0 mm).
- **The view shown was not the active one.** *Observed:* with the 3D tab active, the
  panel showed *Section 2*, the view last chosen in the project browser. Now, when
  another tab is made active (or its plan moves to another storey), the panel shows
  that tab's view. An elevation chosen in the browser keeps showing in the 3D tab.
  *Observed* after the change: switching from the plan to the 3D tab gives
  `3D`, `3D view`.
- **Names and values ran into each other.** *Observed:* "Drawing standar",
  "Coordinate syste", "Phase demolishe": the label column is 88 pixels and the field
  was drawn over the rest. Labels and values that do not fit are now cut short with
  "...", and the whole row shows beside the pointer. A GlobalId (22 characters) does
  not fit the value column.
- **Rows under the wrong heading.** *Observed:* the view's *Drawing type* and *Phase*
  came after *Georeferencing*. They were added after all the other rows. They now
  sit under *View*.
- **A selected level.** *Observed:* a level picked in the 3D view showed the view,
  project, units and georeferencing, a wall type to choose, and phases. A level now
  shows only its own rows, with *Level* in the type box.

Typing a value (the 3D view's scale), folding a heading and scrolling worked as
before. Once during the test the active tab changed to the plan with nobody
clicking it on purpose. The same steps did not reproduce it.

**Tests.** `properties`, `project_settings`, `plates`, `linear_tool`,
`type_editor`, `solid_tool`, `editor`, `views` and `pick` pass, in three bundles of
three. One bundle of all nine ran out of memory: the watchdog stopped it at 1.1 GB
available, from 10.6 GB at the start.
