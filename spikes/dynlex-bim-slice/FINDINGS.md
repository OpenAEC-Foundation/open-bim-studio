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

## Linear members and joints — built and measured

*Measured* by `tests/framing.dl`, `framing_evaluate.dl` and
`framing_editor.dl` on a different machine from the rest of this note (AMD
Ryzen 7 3700U, 13 GB, Linux Mint 22.3), with the compiler of `README.md` plus
`patches/dynlex-pattern-family-cache.patch`.

**Geometry.** A member is its profile's section swept along its axis between
two end planes (`lib/fastkernel/member.dl`); every side face stays planar, so
the fast kernel builds butt cuts, mitres and plate setbacks without booleans.
Every solid in the three tests is closed (`the fast flaw of` is 0).

| Check | Result |
|---|---|
| Free IPE 300 beam, 6 m, square ends | volume 0.032478 m³ = section area x length (same to 6 decimals) |
| Mitred corner, IPE 300 column and beam | volumes unchanged by the mitre (0.016239 and 0.032478 m³), as the halving plane through the axis requires |
| Butt corner | column runs on to z = 3.150 (half the beam's depth past the node), beam starts at the column's face, x = 0.150; swapped: the reverse |
| End plate in a T, IPE 300 into an HEA 200 | beam starts at face + gap + plate (x = 20.117); plate 170 x 320 x 15 mm with 6 holes of 22 mm, volume 0.000783 m³ against 0.000782 for the exact circles |
| Section areas against the profile database | IPE 300 5413 mm² (database 5381, +0.6 %), HEA 200 5429 (5383, +0.9 %), UNP 200 3239 (3220), L 100x100x10 1923.5 (1920), CHS 168.3x8.0 4002.9 (exact circle 4028, −0.6 %): the root radii in three straight pieces per quarter turn, tubes in 32 |

**Incremental evaluation** (`framing_evaluate.dl`, two portal frames, 7
members and 6 joints): after every step the updated evaluation equals a fresh
one element by element (signatures and statuses). Elements rebuilt per step:

| Step | Rebuilt (of 13) |
|---|---|
| unchanged | 0 |
| a column and its beam's end moved 0.5 m | 2 (the other column's cut depends only on the beam's direction and section) |
| the tie beam raised 0.2 m | 3 (the beam and both plates; the columns run through) |
| thicker end plates | 3 (both plates and the beam) |
| heavier columns (HEA 240 to HEB 300) | 8 (the mitred beam is not rebuilt: a mitre does not depend on the section) |
| mitres made butt joints | 3 |
| a beam deleted with its two plates | 0 |
| the same model with a new journal | 0 |

**Scale** (`framing_scale.dl` at `-O2`, the editor's steel example: HEB 300
columns through every storey, IPE 450 and IPE 360 beams butt jointed to them,
IPE 300 secondary beams on end plates, CHS braces; wall times):

| Building | Members / joints | First evaluation | Inner column moved 0.1 m | End plates thicker | Save / read | IFC4 export |
|---|---|---|---|---|---|---|
| 2 x 2 bays, 1 storey | 27 / 34 | 1.9 ms | 0.2 ms (5 rebuilt) | 0.6 ms (12) | 0.2 / 0.2 ms | 0.38 MB |
| 4 x 3 bays, 2 storeys | 110 / 178 | 10.8 ms | 0.4 ms (9) | 4.2 ms (72) | 0.5 / 0.6 ms | 1.9 MB, 54 ms |
| 12 x 10 bays, 4 storeys | 1679 / 3070 | 246.5 ms (4749 solids, none failing) | 1.1 ms (17) | 58.3 ms (1440) | 6.0 / 7.0 ms | 35 MB, 1.05 s |

Two scaling faults were found by this test and fixed: a member found its
joints by scanning every joint (now `the bim joint index of`, a per-member
index built once per evaluation and per export), and the IFC writer appended
every entity to one growing string, copying the whole file each time (1.9 MB
took 74.9 s; it now collects lines and joins them once: 54 ms).

**Not done.** Members are not exported to IFC5 (IfcX). Connection types are
offered as four templates; their parameters cannot yet be edited in the
editor. At a point where three members meet, the first joint at an end
decides its cut. No cope cuts, notches, welds or curved members.

**Compile time.** The editor's compile with the framing records did not finish
within 300–600 s per test at `-O0` with the unpatched compiler; it spent the time
in `resolvePatterns`, recomputing pattern families per precedence edge (gdb
backtraces in `patternResolution.cpp`). With the family cache it compiles in
231 s at `-O0` (4.4 GB peak).

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
