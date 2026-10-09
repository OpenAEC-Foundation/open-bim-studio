# FINDINGS — the modeller core

Work in progress. Each part of the README is recorded here when its criteria
have been checked.

| Part | Status |
|---|---|
| A. Categories, view rules and visibility | criteria met (2026-10-05) |
| B. Grids | criteria met (2026-10-05) |
| C. Snapping, tracking, ortho, Blender-like control | not started |
| D. Dimensions | not started |
| E. GPU-resident 3D rendering | criteria met except self-shadowing: the editor draws through DynLex's own Vulkan layer, with no C graphics runtime; 5 million triangles at 61 fps; the shadow map is open |
| F. IFC import and the large-model test | import through IfcOpenShell measured on two large models; IFC5 (IfcX) import and export written in DynLex and checked against an independent composition |
| G. Types and a basic UI | first UI: the Open BIM Studio chrome (ribbon, explorer, command line, status bar) in DynLex; the Open 2D Studio types are open |

## A. Categories, view rules and visibility

`examples/bim-slice/bim_view.dl` defines seven categories:
walls, floors, doors, windows, spaces, grids and dimensions.

**Rules per view.**
- Each of the three views (plan, section, 3D) holds a rule per category: visible
  or hidden, and halftone.
- A view starts from its kind's template. The section hides spaces; the 3D view
  hides spaces and dimensions.
- The L key opens a panel of check boxes. A change applies to that view only.

**What follows the rules.**
- In the plan, section and 3D view, walls (with their hatched layers), floors, the
  storey below, spaces, and door and window symbols.
- Halftone draws a category halfway to white.
- Hidden categories cannot be hovered or selected: in the plan through the editor,
  and in 3D because picking only sees shown meshes.

**Saving.** The rules are written to the native file as `viewrule` records and
restored on opening.

**New plan symbols.** Doors show their leaf open into the room with a swing.
Windows show their glass between the wall faces.

**Checked by:**
- `tests/view.dl`: templates, a toggle in one view only, each element's
  category, a hidden category passed over by selection, and rules surviving a
  save and an open;
- a recorded XTEST session that hides walls in 3D and sets windows to halftone
  in the plan.

## B. Grids

**The model.**
- A grid is an element with a name, a plan line and an elevation range (by
  default a metre beyond the storeys).
- The I key draws grids with two clicks. Names are automatic: numbers for
  north-south grids, letters for the others.
- Grids are selected on their line and deleted with Delete.
- Dragging a grid end with the select tool moves it, with snapping and undo.
- The example house has grids 1–3 and A–C.
- `tests/editor.dl` draws a grid, drags its end and undoes the drag.

**Drawing.**
- **Plan:** a dash-dot line with a head at each end.
- **Section:** where the section line crosses a grid, a vertical dash-dot line
  with its head on top.
- **3D:** the grid plane outlined, with its head.
- All follow part A's rules.

**Export.**
- The native file writes `grid` records.
- IFC gets one `IfcGrid`, with the numbered lines as V axes and the lettered as U
  axes. IfcOpenShell reads it with the right tags, curves and storey.
- IFC4 requires both axis lists, so a model with grids in one direction writes
  no `IfcGrid`.

**Not yet.** Grids are not snap targets (part C), and walls do not follow them.

## F, first step: import through IfcOpenShell, measured

**How it works.**
- `examples/bim-slice/import/ifc_to_mesh.py` triangulates an IFC file with
  IfcOpenShell's geometry iterator (12 threads, world coordinates). It writes a
  little-endian BIM-MESH file: per element the category code, the label (IFC
  class, GlobalId, name), binary64 vertices and triangle indices.
- The editor opens such a file with `--import FILE`. `bim_import.dl` reads it into
  read-only, flat-shaded scene meshes.
- Imported elements take part in the 3D view's category rules, colours, picking and
  fit. The categories grew from seven to fourteen: columns, beams, roofs, stairs,
  railings, furniture and other were added.
- Selecting an imported element shows its label.
- Imported elements are not cut in the plan or section yet.

**Measurements.** Reference machine, release build, in a nested X server with
software presentation, so the frame figure is CPU time before presenting:

| | Schependomlaan | HITOS |
|---|---:|---:|
| Elements, triangles | 3,504, 260,078 | 2,317, 371,598 |
| Products without a mesh | 69 | 3 |
| IfcOpenShell: open + triangulate | 1.3 + 6.1 s | 2.2 + 13.5 s |
| DynLex import of the BIM-MESH file | 59 ms | 76 ms |
| Peak memory of the editor | 243 MB | 276 MB |
| 3D frame, CPU time | 16.9 ms | 19.6 ms |

**What the measurement showed.**
- The first attempt aborted with "the active graphics frame exceeds its transient
  vertex capacity". The runtime streams every vertex every frame, through 32 MB at
  24 bytes each, about 1.4 million vertices. Schependomlaan with its cast shadow
  did not fit.
- **Until part E, the 3D view:**
  - leaves out faces turned away from the viewer;
  - casts shadows only for models of up to 150,000 triangles;
  - stops at a vertex budget of 1,050,000 per frame and shows how many triangles
    it left out, instead of aborting.
- The frame time is the CPU transforming and streaming every triangle every frame;
  that is what part E removes.

## Curved walls (maintainer request, 2026-10-06)

Not one of the README's parts: the maintainer asked for walls that can be made
round, and for the 3D view to follow a wall end while it is dragged.

**Model.**
- A wall carries a bulge: the signed distance from its chord's middle to its
  centreline's middle, positive toward the exterior side.
- Its centreline is then a circular arc of at most a half circle.
- Bulge 0 is a straight wall. The file format writes the bulge only when it is
  not 0, so existing files and their tests are unchanged.

**Geometry.**
- The sides follow the exterior and interior arcs in straight pieces. The number
  of pieces keeps the chord error within 0.5 mm on the outer side, from 2 up to
  256 pieces.
- L and T joins use the arc's tangent at the wall's end; against a curved host,
  the tangent at the foot of the joining end.
- The fast kernel builds a curved wall directly as a closed planar polyhedron
  (`lib/fastkernel/curved_wall.dl`), openings included:
  - each opening has radial jambs and spans its rough width along the centreline;
  - jamb corners lie on the side pieces, so the plan outline does not depend on
    the openings.
- The port's extrusion and booleans remain the fallback.
- Plan and section hatching follow the layers as rings: one band per layer per
  piece in plan, and up to two intervals per ring in a section.
- IFC exports the same outline as an extruded profile, and each opening as a
  radial ring sector.

**Editing.** Selecting a wall shows handles in the plan and in 3D: the two ends,
and an orange middle handle that bends the wall so that its arc passes over the
pointer.

**Checked:**
- **Volume.** A free arc wall is within 0.017 % of its exact ring-sector volume.
- **Window.** A radial window removes 0.6447 m³, against 0.6448 m³ exact.
- **Closed solids.** Both solids pass the fast kernel's closed-polyhedron check.
- **Joins.** The mitred L join with a straight wall lands where the tangent lines
  cross.
- **Persistence.** The bulge survives the file exactly.
- **Space.** A room closed by an arc gets a space of 24.91 m², which is the
  rectangle plus the arc's segment, less the pieces.
- **IFC.** The upper wall in `verify_ifc.py` is curved with a radial window.
  IfcOpenShell measures it at 5.532121 m³, against 5.532120 m³ native, within the
  script's 10⁻⁶ m³.
- **Regressions.** All 11 headless tests pass, including the new `curved`, and the
  outputs for straight walls are unchanged.

**Speed while bending** a wall with a door, in the editor:

| Build path | Frame |
|---|---:|
| Port's booleans | 235 to 470 ms (0.46 to 1.6 s per rebuild) |
| Direct curved-wall construction | 6.9 ms |

**3D during a drag.**
- The 3D recording was keyed on the document revision, which changes only when a
  drag ends, so the 3D view lagged until release.
- The recording is now keyed on a counter of mesh rebuilds, and the 3D view
  follows every step of a drag.

## A model of 500,000 walls (maintainer request, 2026-10-06)

The maintainer asked for an imaginary model with 500,000 walls and floors in it.

**The model.** `--generate N` builds a tower of storeys until it holds at least
N walls. Each storey has:
- 50 × 50 rooms of 4 m × 4 m;
- cavity walls on the facade, with a window in each;
- sand-lime partitions inside;
- a floor slab.

At N = 500,000 that is 99 storeys: 504,900 walls, 19,800 windows and 99 slabs.
`tests/large_model.dl` times the steps headless.

**Two scaling faults found and fixed.**

1. **The join index was 2D.** Storeys stacked over the same plan shared every
   cell, so each join lookup visited the walls of all 99 storeys.
   - Evaluation was quadratic: 4.0 s at 51,000 walls and 15.6 s at 102,000.
   - The index now keys its cells by level too.
   - Evaluation now takes 0.9 s and 2.1 s for those sizes.
2. **Each wall's signature and solid scanned every opening of the model.** They
   now go through an index of openings per wall when more than 32 walls are
   examined. A single edit still scans, which is cheaper than indexing.

**Measured, release build, reference machine:**

| Step at 504,900 walls | Time | Peak memory |
|---|---:|---:|
| Generate the model | 38 ms | 41 MB |
| First evaluation (all fast-kernel solids) | 15.3 s | 1.56 GB |
| Plan cut and the 2,500 spaces of the ground floor | 0.56 s | 1.56 GB |
| Scene meshes (6,535,188 triangles) | 4.9 s | 2.49 GB |
| Move one wall: incremental rebuild, plan and spaces | 283 ms (1 element rebuilt) | 2.55 GB |

**In the editor:**
- Hover and snapping searched every wall on each pointer move. They now ask the
  spatial index for the walls of the active storey near the pointer.
- The 3D view's category filter ran every frame. It now runs only when the meshes
  or the rules change.
- Room labels are left out where a room is too small on screen to hold one.
- With those changes a frame takes about 28 ms. That time is the CPU streaming
  the recorded plan (382,000 vertices) and the 3D view (up to its budget) to the
  GPU every frame.
- The 3D view leaves out about 3.1 million triangles to stay within the
  runtime's per-frame vertex capacity. The vertex budget now accounts for what
  the plan uses: the first attempt overflowed that capacity and aborted.

**Still open.** These are the GPU-resident rendering of part E, and incremental
spaces:
- persistent GPU buffers for the plan and the 3D view, so that a frame does not
  depend on the model's size;
- spaces derived incrementally, so that an edit does not re-derive a storey's
  2,500 rooms.

## E. GPU-resident 3D rendering: first results (2026-10-06)

**The shader language.** DynLex's shader language had one vertex input (the
position) and no textures. Two extensions were made, in a private compiler copy,
and checked with `spirv-val --target-env vulkan1.3`:
- **Vertex inputs.** `@intrinsic("shader input", "Attribute1")` to `"Attribute7"`
  are vertex inputs at locations 1 to 7.
- **Texture sampling.** `@intrinsic("shader sample", binding, u, v)` samples a 2D
  texture: a sampled image at `binding` and its sampler at `binding + 1`. It
  goes through LLVM's `llvm.spv.resource.sample`.
- **SPIR-V patcher.** It now adds the resource variables to the entry point's
  interface, as SPIR-V 1.4 and later require.

**The renderer.** `lib/vulkan/structs.dl` and `lib/vulkan/renderer.dl` call
libvulkan and GLFW directly through DynLex's C interface. DynLex classes have C
layout, which was checked by offsets.
- **Objects:** instance, device, swapchain, depth buffer, render pass, and one
  pipeline from DynLex-compiled shaders.
- **Buffers:** persistent vertex and index buffers, written in place through a
  mapping, at 20 bytes per vertex.
- **Uniforms:** one binding per float. The view matrix and the lighting are
  computed in the vertex shader.
- **Test program:** `examples/gpu/gpu_view.dl` loads the example house, a
  BIM-MESH import or the generated tower.

**Measured** on the reference machine's Intel UHD Graphics (CML GT2), in a
1280 × 820 window, with HITOS (371,598 triangles, 1,114,794 vertices):

| Step | Result |
|---|---:|
| Write the buffers | 29 ms |
| Display-synchronised presenting | 60 fps |
| Presenting without waiting for the display (`--uncapped`) | 172 fps |
| Frame time, uncapped | 5.7 ms |

The 5.7 ms uncapped frame is mostly the GPU itself. The previous CPU-streamed
view took 19.6 ms of CPU time for the same model, and had to leave triangles out
above 1.05 million vertices.

**Open:**
- moving the editor itself onto this renderer, its plan and text included;
- the 5-million-triangle criterion, measured on the generated tower;
- the shadow map, which texture sampling now makes possible.

## Wall layers in 3D (maintainer request, 2026-10-06)

- **Fine detail.** The 3D view has a detail level. At fine, each wall shows its
  type's layers as separate solids in their materials' colours, so they show in
  reveals and at wall ends.
- **How the layers are built.** The fast kernel builds each layer directly:
  - each layer's footprint lies between its offsets, with its ends on the wall's
    end lines, so mitred joins mitre every layer;
  - on curved walls, each layer gets its own arc with the openings at the same
    angles.
- **Coarse detail** shows each wall as one solid. Models of 50,000 walls or more
  start coarse.
- **Checked.** The three layers of a curved cavity wall with a window are each
  closed, and their volumes add up to the wall's (5.5312 m³).

### E, continued: the 5-million-triangle criterion (2026-10-06)

Three changes took the generated tower to the criterion.

1. **Parameters in one storage buffer.** The parameters now sit in one storage
   buffer instead of a uniform buffer per float. A new shader intrinsic,
   `shader buffer read`, reads a float of a storage buffer at a run-time index,
   through `llvm.spv.resource.getpointer`. Back faces are culled.
2. **Shared corners.** A new intrinsic, `shader derivative x/y`, uses `llvm.spv.ddx`
   and `llvm.spv.ddy`. With it, the fragment shader takes the face's normal from
   the screen-space change of the position.
   - Corners are then stored once per element instead of once per face.
   - The 504,900-wall tower needs 4,237,992 vertices instead of 12,674,376.
3. **Drawing order.** The tower is drawn top storey first, so the depth test
   rejects hidden faces early.

**Measured** on the reference GPU, 1280 × 820, presenting without waiting for the
display, with the camera orbiting from above:

| Model | Triangles | Frames per second |
|---|---:|---:|
| HITOS, per-face vertices | 371,598 | 184 |
| HITOS, shared corners | 371,598 | 305 |
| Tower of 392,700 walls, drawn bottom first | 5,082,924 | 52 |
| Tower of 392,700 walls, drawn top first | 5,082,924 | **61** |
| Tower of 504,900 walls | 6,535,188 | 54 |

The criterion holds for this tower in this view.

**Caveats:**
- The drawing order is fixed. A view from below would need the order reversed,
  for example by sorting per-storey draw ranges each frame.
- The editor still draws through the C graphics runtime.
- The shader-language extensions live in a patch outside the repository:
  `dynlex-shader-extensions.patch` in the workspace.

### E, continued: the editor on the DynLex Vulkan layer (2026-10-06)

`lib/vulkan/context.dl` and `lib/vulkan/graphics.dl` replace the C graphics
runtime for the editor. They keep the drawing patterns of `lib/graphics.dl`, so
the editor's drawing code was left as it was. The built editor contains no symbol
of the C runtime; before, it contained 80.

**What the layer provides:**
- One growing vertex stream per frame, drawn in batches by three pipelines: flat,
  flat with depth testing, and text. The runtime's fixed limit of 1.4 million
  vertices per frame is gone.
- The glyph atlas as a Vulkan texture, uploaded through a staging buffer with
  layout transitions and sampled by a DynLex shader.
- A persistent canvas buffer. The recorded plan is written there once and drawn
  shifted by two shader parameters, so panning costs no CPU work for the plan.
- A persistent mesh for the 3D view:
  - corners are shared per element;
  - the camera and lighting are parameters;
  - the selected element is highlighted by comparing a per-vertex element ordinal
    in the fragment shader, so a selection change uploads nothing;
  - the mesh is drawn in the 3D panel through the viewport and scissor, so the
    CPU no longer clips triangles.
- **Unchanged.** The ground and the cast shadows are still recorded on the CPU
  and drawn under the mesh.

**Measured** on the reference machine's display:

| Model | Frame time |
|---|---:|
| Example house | 16.5 ms (the display's 60 Hz) |
| Generated tower, 504,900 walls, ground floor plan and full 3D view | about 18 ms |

For the tower that is about 55 fps, set by the GPU drawing 6.5 million
triangles. Before, the C runtime ran at 28 ms per frame and left 3.1 million
triangles out.

**Open:**
- When the shown meshes change, the whole mesh is written again. During a drag
  on a very large model that rewrite is the cost; incremental updates per
  element are next.
- Self-shadowing through a shadow map.

## G, first step: the Open BIM Studio UI in DynLex (2026-10-06)

The maintainer asked for the Open BIM Studio interface that a Codex branch
adapted from Open CAD Studio. `bim_ui.dl` rebuilds it in DynLex on the GPU layer,
after the branch's ribbon and panels and a screenshot of the running branch.

**The chrome**, in Fusion Black (#1A1A1A, text #F2F2F2, accent #0696D7) around the
white canvas:
- **Top bar.** Quick-access buttons (save, open, undo, redo) and the ribbon tabs
  BIM, Modify, Annotate, View and Manage.
- **Ribbon.** Groups of large buttons with icons drawn in DynLex. On the BIM tab
  these are Select, Planar, Objects, Linear and Systems, as in the branch.
- **Buttons.** A button sends the editor the command its key sends, so the
  ribbon and the keys share one dispatch. Tools the editor does not have yet,
  such as roof, column, beam and facade, are dimmed.
- **Document bar.** One tab naming the open file.
- **Project explorer** (244 pixels):
  - the model's counts;
  - the storeys (a click activates one);
  - the views;
  - the selection's properties.
- **Command line and status bar.**

**Checked in a nested X server:**
- the ribbon's Wall button starts the wall tool, and two clicks draw a wall;
- a click on a storey in the explorer makes it active;
- the View tab shows its groups.

All 12 headless tests pass. Snapping and hover, which now ask the evaluation's
spatial index, fall back to the storey's walls while the model is newer than the
evaluation.

**Not yet:**
- the model assistant panel;
- the types library of Open 2D Studio;
- editing properties in the panels.

## Sketch tab and components (maintainer request, 2026-10-07)

The maintainer asked for a Sketch ribbon tab that works like SketchUp: lines,
faces, push/pull, splitting faces, and components that repeat like groups.

**Sketch elements** are model elements on a storey:
- a **line** (two points);
- a **face** (a simple closed outline), which push/pull raises into a mass;
- a **text** (an anchor and its words).

They are saved in the native file, undone like any other edit, picked in plan
and in 3D, and drawn on the GPU layer. A mass is a fast-kernel prism; a flat
face is drawn from both sides.

**The tools**, each on the Sketch tab and on a key:

| Tool | Key | What it does |
|---|---|---|
| Line | N | Draws a chain of lines. Coming back to the first point closes the chain into a face. |
| Rectangle | R | Draws four lines and their face. |
| Text | Ctrl+T | Places a text. |
| Push/Pull | P | Raises a face. Move the pointer or type a height, then click or press Enter. |
| Move | M | Moves the selection. |
| Delete | Delete | Deletes the selection. |

**Splitting.** A line whose two ends lie on the edges of a face, and which runs
through it, splits the face in two, as in SketchUp. A mass keeps its height on
both parts.

**Components:**
- **Making one.** Select sketch elements; Shift-click adds to the selection.
  Ctrl+G makes a component of them. Its parts are kept once, in the
  component's own coordinates, with the lower-left corner of their extent as
  its origin. One instance replaces the selected elements.
- **Placing.** Ctrl+I places more instances.
- **Editing.** Ctrl+E opens the selected instance for editing. Its parts
  become ordinary sketch elements where the instance stands, and the usual
  tools (lines, splitting, push/pull) apply. Ctrl+E closes the component
  again: what was drawn becomes its parts, and every instance follows.
- **Exploding.** Ctrl+U explodes an instance into free elements.
- **Instances** can be moved, deleted and undone. They are saved as
  `component`, `part` and `instance` records. The schedule counts them per
  component, with their footprint area and volume.

**Checked:**
- `tests/sketch.dl` drives the whole sequence headless:
  1. a rectangle pushed to 2 m;
  2. a line splitting it into two masses;
  3. both made into a component and placed three times;
  4. one instance edited, so that all three gain the new part;
  5. the file written and read back to the same text;
  6. an instance exploded, then the explosion undone.
- The same sequence works in the GUI in a nested X server: a diagonal drawn in
  one instance appears in all three.

## IFC5 (IfcX) in DynLex (maintainer request, 2026-10-07)

The maintainer asked for deep IfcX integration now. Both directions are written
in DynLex. They follow the `ifcx_alpha` format of the buildingSMART IFC5
development repository.

**Export** (`bim_ifcx.dl`; Ctrl+X, or "IFC5 export" on the Manage tab):
- **Structure.** A root node, then the project, site and building, one storey
  per level, and the storey's elements below it. Grid lines are
  `IfcGridAxis` curves under the building.
- **Walls.** Each wall carries its type name, height, width, length and
  volume. It has one body per layer. Each layer body reaches its material
  node through `inherits`. A material node carries `bsi::ifc::material` and
  its colour.
- **Doors and windows** are children of their host wall. Each inherits a door
  or window type node that carries its name, width and height.
- **Slabs** carry their depth, net area and volume.
- **Spaces** carry their net area and their boundary as a closed curve.
- **Sketch elements.** Faces and masses become proxies with bodies. Lines
  become annotation curves. Texts become annotations with their words.
- **Components** are written once, as type nodes holding their parts. Each
  instance inherits its component and places it with a `usd::xformop`. The
  geometry is not repeated however often a component is placed.
- **Paths** are UUIDs derived from a project key, a kind and the element id.
  An unchanged element keeps its path across exports, so a later layer can
  add to it. The header id names each export.

**Import** (`bim_ifcx_read.dl`; `--import a.ifcx [b.ifcx ...]`):
- **Layers.** One or more files are read as layers. They are flattened by
  path, and a later opinion wins. A null child or inheritance removes it.
- **Composition.** A node takes what each inherited node composes to, then
  its own children, then its own attributes. An opinion at an instance path
  (`root/child/...`) overrides that one occurrence. A reference with a tail
  descends into the composed children.
- **Meshes.** Every composed mesh becomes a read-only element, placed by the
  transforms along its path and coloured by its `diffuseColor`. Its category
  comes from the nearest IFC class above it.
- **Parsing.** The JSON is parsed by DynLex's own `lib/json.dl`. Coordinates
  are read from the number text with `strtod`, so they are exact.

**Checked:**
- **The export.** `tests/verify_ifcx.py` composes the exported file
  independently. It checks:
  - the header;
  - that every path is a unique UUID and that every reference resolves;
  - the spatial structure;
  - the layered walls reaching their materials;
  - both component instances receiving the component's body through
    inheritance.

  A Python port of the reference composition finds no attribute outside the
  published schemas (`ifc@v5a`, `prop@v5a`, `usd@v1`).
- **The import.** `tests/verify_ifcx_read.py` composes the same files in
  Python and compares the mesh count, the triangle count and the extent.
  They agree on:

  | Input | Meshes | Triangles | Read in |
  |---|---|---|---|
  | The slice's own export | 36 | 1,507 | 47 ms |
  | Hello-wall | 12 | 184 | 11 ms |
  | Hello-wall with a fire-rating layer | 12 | 184 | 12 ms |
  | Building-Architecture | 10 | 1,067 | 46 ms |
  | Building-Structural | 16 | 1,490 | 60 ms |
  | Building-Hvac | 5 | 1,064 | 30 ms |
  | Architecture, Structural and Hvac federated as layers | 27 | 1,949 | 120 ms |
  | Infra-Electrical | 8 | 1,040 | 28 ms |
  | The georeferenced bridge deck | 1 | 12 | 1 ms |

  The federated model has fewer meshes than the three files read apart
  (27, not 31), because the files share nodes by path and composition merges
  them.
- **The GUI.** The editor opened the three federated building files in the
  nested X server and drew them in their IfcX colours.

**Not yet:**
- `usd::usdgeom::basiscurves` and point clouds are not drawn on import.
- Imported elements stay read-only.
- Export writes meshes, not parametric geometry; the IFC5 alpha has none yet.

## Two-letter commands, drawing in 3D, view modes (maintainer requests, 2026-10-07)

**Two-letter commands.** The Open 2D Studio command table is taken over:
- A letter that can start a command waits 750 ms for its second letter, as in
  Open 2D Studio. After that it acts alone. G acts at once when something is
  selected.
- Working commands:

  | Command | Keys |
  |---|---|
  | wall | WA |
  | window | WO |
  | slab under the selection | SL |
  | grid | GL |
  | move | MV, G |
  | select | MD |
  | line | LI |
  | rectangle | RC |
  | text | TX |
  | zoom all | ZA |
  | copy (repeats until Esc) | CO, CC |
  | create similar | CS |

- **Create similar** starts the tool for the selection's kind, with its type:
  a wall of the same wall type, an opening of the same type, a grid, a sketch
  element of the same kind, or another instance of the same component.
- **Copy** copies the selection. A wall keeps its type, its bulge and its
  openings.
- The others (RO, MM, TR, EX, OF, RE, FL, DI and the drawing primitives) say
  on the command line that they are not in the modeller yet. On the Modify
  tab they are dimmed.
- `tests/commands.dl` checks the timing, the commands, copying and create
  similar.

**Drawing in 3D:**
- With a drawing tool active, the pointer in the 3D panel runs over the active
  storey's plane, through a ray from the pixel. This applies to line,
  rectangle, text, wall, opening, grid, move, copy and place.
- A click draws instead of orbiting; Shift and the middle button still orbit.
- The 3D panel shows the snapped point and the rubber bands.
- **Push/pull** picks the face or mass under the pointer by ray. Moving the
  pointer up or down the screen sets the height, through the screen's view of
  the vertical.
- Checked in the nested X server: a rectangle drawn on the ground in 3D and
  pulled up into a mass there.

**View modes** (Ctrl+1 to 4, or the View tab):
- **Shaded.**
- **Shaded with edges.**
- **Hidden line:** a white model with edges.
- **Wireframe.**

Edges are the model's feature edges: a triangle edge used once, or one between
faces that turn by more than 15°. They are found when the scene is uploaded,
from the welded corners. They are drawn at the depth the GPU mesh has there,
so the mesh hides those behind it, except in wireframe.

**Levels and grids in 3D:**
- Each level is a dash-dot rectangle around the model at its elevation, with
  its name and height; the active storey is darker.
- Grid lines lie flat at datum level (peil 0), with a head at each end.
- A selected grid shows its plane, see-through, from its low to its high
  elevation.
- In the plan, a grid being drawn shows its line and both heads.

**Bending keeps T joins.** Bending a wall now slides every wall end that meets
it along its length onto the new arc:
- Before this, a partition stopped short of a wall bent away from it. Its two
  rooms became one region with a slit around the partition end, and the plan
  filled that region wrongly.
- Where the partition's line crosses the circle twice, the crossing on the arc
  itself is taken.
- `tests/bend_joins.dl` bends the example's south wall out and in. The rooms
  stay three, until the arc reaches the cross wall behind it.

## Modify tools, Escape, IfcX curves (maintainer requests, 2026-10-07)

**One transform for every change.** A move, a turn about a point and a mirror
in a line are one transform record, applied to every kind of element:
- walls, grids, slabs and sketch elements;
- instances, which take the turned heading.

A move or a rotation is placed from the snapshot its transaction keeps, so the
preview follows the pointer without drifting. A mirrored wall is laid the
other way round, so that its exterior side follows. Its openings are measured
again from the new start: an opening 1.5 m along a 6 m wall lands 4.5 m along
the mirror image.

**The tools** (Modify tab, or two-letter commands):

| Tool | Keys | How it works |
|---|---|---|
| Rotate | RO | Pick the centre, then a reference direction and the new direction; or type degrees and Enter. |
| Mirror | MM | Two points on the mirror line; a mirrored copy is made, as in Revit and AutoCAD. |
| Offset | OF | Type a distance; click a straight wall or line, then the side. |
| Trim | TR | Pick the boundary (a straight wall, a line or a grid), then each piece to cut back; the side clicked stays. |
| Extend | EX | As Trim; the end nearer the click runs on to the boundary. |

Copy and mirror share one routine that copies through any transform.

**Escape leaves the command**, as in CAD: it cancels the gesture under way and
returns to selecting.

`tests/modify.dl` checks each of these with exact coordinates:
- a typed 90° turn;
- a mirror in x = 1;
- a 1.5 m offset;
- an extend and a trim to x = 10;
- the mirrored wall's opening;
- that Escape returns to selecting.

**IfcX polylines.** The reader now also places `usd::usdgeom::basiscurves`, such
as space boundaries, axes and alignments, and the 3D panel draws them.
`verify_ifcx_read.py` checks their segment count against its own composition.
It agrees on the buildingSMART examples, among them:

| Input | Meshes | Triangles | Curve segments |
|---|---|---|---|
| Hello Wall | 12 | 184 | 2 |
| Railway (simple) | 11 | 29,318 | 229 |
| Roadway | 1,343 | 219,652 | 1,037 |

**Where the code is.** The editor now lives in
`spikes/dynlex-bim-slice/overlay/` and builds with `spikes/dynlex-bim-slice/build.sh`
against a DynLex checkout.

## C, first step: snapping and tracking as in Open 2D Studio (2026-10-08)

**Snap kinds.** Snapping follows the Open 2D Studio rules recorded in
`open-2d-studio-survey.md`:
- **Sources:** end points and middles of wall centrelines, sketch lines, face
  edges and grid lines.
- **Intersections** of those pieces.
- **Perpendicular:** the foot from the point being drawn from.
- **Nearest:** a point on an edge, offered only when no other snap is near.

**Which snap wins.** The nearest candidate within the tolerance (8 pixels)
wins. Within a tenth of the tolerance, the lower kind wins, in this order:
end, mid, intersection, perpendicular.

**Tracking.** Without an object snap, the pointer tracks from the last point
of the gesture under way:
- the point tracked from is the last point of a wall chain, a line chain, a
  rectangle, a grid line, a move, a copy, a rotation or a mirror;
- horizontal and vertical rays always;
- polar rays every 45° (F10);
- ortho (F8) constrains to the nearer axis;
- lengths along a ray are rounded to 5 cm, as the grid is.

F3 turns snapping off. The status bar shows ortho and polar.

**Glyphs.** Each kind has the glyph and colour Open 2D Studio uses:
- end: a green square;
- mid: a cyan triangle;
- intersection: a yellow cross;
- perpendicular: an orange foot;
- nearest: a pink diamond;
- tracking: a dashed ray from the point tracked from.

**Checked.** `tests/snapping.dl` checks each kind, the tracking rays, ortho and
snapping off at exact coordinates.

**Not yet:**
- tangent and parallel snaps;
- extension rays from nearby end points;
- crossings between two tracking rays;
- the X and Y constraints of a move.

## Wall type library (part G, 2026-10-08)

The Open 2D Studio wall types are in the editor, with their Dutch names and
layer build-ups:
- **Layered:** Spouwmuur 360 and 300, HSB Buitenwand, Metal Stud Binnenwand
  and Massieve Binnenwand.
- **Single material:** concrete, calcium silicate, masonry, timber frame,
  steel and insulation.

How they behave:
- **Cavities.** A cavity is an air layer: it takes its place in the wall but is
  not hatched and is no solid in 3D.
- **Materials.** Timber, steel and gypsum have NEN 47 style hatching and
  colours.
- **In the explorer.** The project explorer lists the types. A click makes one
  current for new walls, or gives it to the selected wall, as an edit that
  can be undone.

`tests/types.dl` checks the library, the cavity and a change of type.

**Not yet:**
- the floor types;
- the "aligned on the exterior" reference line of the layered types;
- grouped layers with their own gaps beyond one cavity.

## IFC5 (IfcX) as the editor's own file (maintainer request, 2026-10-08)

The maintainer asked for everything to be saved in `.ifcx`: JSON, with IFC 4.3
classes where they exist and extensions where needed. The editor now saves
and opens `.ifcx` as its own file.

**IFC gives** the classes and the spatial structure, the type nodes elements
inherit, materials, geometry and quantities:
- `IfcProject`, `IfcSite`, `IfcBuilding` and `IfcBuildingStorey`;
- `IfcWallType` with `IfcWall` inheriting it;
- `IfcWindowType` and `IfcDoorType` with `IfcWindow` and `IfcDoor` inheriting
  them;
- `IfcSlab`, `IfcSpace`, `IfcGridAxis` and `IfcAnnotation`;
- `IfcBuildingElementProxyType` with `IfcBuildingElementProxy` for components
  and their instances;
- `bsi::ifc::prop` quantities, `bsi::ifc::material` with colours, and
  `usd::usdgeom` meshes and curves.

**The extension.** An `openbim::` namespace, declared in the file's
`schemas`, carries what IFC has no parametric attribute for:

| Record | What it holds |
|---|---|
| project | next id, length units, the views' rules |
| level | elevation, height |
| walltype | layers: material and thickness |
| wall | centreline, height, bulge, type, storey |
| openingtype | width, height, sill, frame, door or window |
| opening | type, host wall, offset along it |
| slab | outline, thickness |
| grid | ends, low, high |
| sketch | kind, points, height, words |
| component | its parts |
| instance | component, origin, angle |
| dimension | its two semantic references |

Numbers are written with 17 significant digits.

**Reading.** The reader rebuilds the native text from these records and reads
it as any saved model is read, with the same checks.

**Saving.**
- Ctrl+S now saves `.ifcx`.
- A native `.bim` file still opens, and is then saved next to itself as
  `.ifcx`.

**Checked.** `tests/ifcx_native.dl` saves an example building with a
component, sketch elements, a bent wall, the wall type library, millimetre
units and a changed view rule, then opens it in a new editor. The model comes
back identical, compared as native text, and so do the units and the rule.
`verify_ifcx.py` composes the file independently: one root, 109 nodes, and
every reference resolves.

## Edit mode: Blender's grab with SketchUp's picking (maintainer request, 2026-10-08)

The maintainer asked for sketch geometry that combines Blender and SketchUp:
Tab into the mesh, and points moved with G along X, Y or Z.

**Entering.** Tab on a selected line, face or mass enters edit mode. The
element's points are shown in the plan and in the 3D panel; a mass shows them
at its foot and its top. The points are picked as in SketchUp:
- a click near a point picks it;
- a click on an edge picks its two ends;
- a click inside a face picks all of it;
- Shift adds to what is picked, and A picks all.

**Grabbing.** G grabs the picked points, as in Blender:
- they follow the pointer, with snapping;
- X, Y and Z constrain the move to an axis (pressing the same key again frees
  it);
- a typed distance in the project's units (with - for the other way) places
  them exactly;
- Z on a face or mass changes its height;
- a click or Enter places them, and Esc cancels.

A grab that would make a face cross itself is refused. Tab or Esc returns to
object mode. It works in the 3D panel as well, where the pointer runs over
the storey's plane.

**Checked.** `tests/edit_mode.dl`:
- a corner moved 1 m along X;
- an edge moved -0.5 m along Y;
- the whole face raised 2.5 m along Z into a mass;
- a crossing grab refused;
- Esc and undo.

**Not yet.** Sketch elements are still flat outlines with a height, not general
meshes: points move in plan and the top moves as a whole. Free 3D vertices,
extruding faces from a mesh, and loop cuts need a general mesh element.

## Properties window, type selector, pushing sides (maintainer requests, 2026-10-08)

**Properties window.** The left panel is split, as in Revit: the project
browser above, the properties below.
- **Type selector.** The window opens with a type selector: the type of the
  selection, or of what the active tool draws next. A click opens the list of
  that category's types, which are wall, door and window, floor or component
  types. Choosing one gives it to the selected element, or makes it current.
- **Rows.** Under the selector, the selection's properties are shown in the
  project's units, and those that can change sit in fields:

  | Selection | Rows | Can be typed |
  |---|---|---|
  | Wall | height, curvature, length, width, storey | height, curvature |
  | Opening | offset, type's width, height and sill | all four |
  | Slab | thickness, area | thickness |
  | Face or mass | height, area | height |
  | Instance | angle | angle |
  | Grid | name, length | none |
  | Nothing | the active storey | elevation, height |

- **Typing a value.** A click on a field begins typing; Enter applies it as
  one edit that can be undone; a value the model refuses leaves it unchanged.

**Pushing a side.** Push/pull that starts on a mass's side in the 3D panel
pushes that side, as in SketchUp:
- the side's two corners are joined to their moved copies, and points left
  on a straight line or doubling back are taken out, so a rectangle grows or
  shrinks and an L-shape gains a step;
- the pointer follows across the level of the click;
- a typed distance (negative pulls in) places it exactly;
- a side pulled in past the far side, or a crossing face, is refused.

**Lines on faces.** In the 3D panel the pointer lies on the face or mass under
it, so lines snap to the points and edges of faces where they are seen.

**Checked:**
- `tests/properties.dl` covers the rows of a storey, a wall and an opening,
  typed values in millimetres, and a refused value.
- `tests/side_push.dl` covers a side pushed out 1 m and in 0.5 m, and a
  refused pull.

**Not yet.** Lines on a mass's top or side stay on the storey's plane; sketch
geometry is not a general 3D mesh (see edit mode above).

## Free meshes: Tab into a mass, push/pull any face (2026-10-08)

This follows the edit-mode request: free 3D vertices and SketchUp's push/pull
on any face.

**The element.** A free mesh is a new model element on a storey:
- its points are in 3D, relative to the storey;
- each face is a loop of point numbers, turning anticlockwise seen from
  outside;
- faces need not be convex or quite flat. Each face is triangulated in its
  own plane (the Newell normal) and keeps its own points.

**Making one.** Tab on a mass turns it into a mesh, as one edit that can be
undone. The mass's foot, top and a side per edge become faces. Edit mode then
works on the mesh:
- in the plan, a click picks the highest point, the highest edge or the face
  seen there;
- in the 3D panel, a click picks the point nearest the pointer on screen, or
  the face under it;
- G grabs with X, Y and Z, and Z now moves single points in height, so a top
  can be tilted.

**Push/pull of a face.**
- In the 3D panel, any face can be pushed; it follows the pointer along the
  face's normal as seen on screen.
- In the plan, the face on top is pushed.
- When every face touching the pushed face runs along the push, the face
  moves and they stretch, so a box stays eight points.
- Otherwise the face is extruded, and each of its edges grows a side.
- A typed distance places it exactly; a negative distance pulls it in.

**Stored.**
- In `.bim`, a mesh is a `mesh` line: the points, then the faces as counts
  and point numbers.
- In IfcX, a mesh is an `IfcBuildingElementProxy` with its triangulated body,
  its volume, and an `openbim::mesh` record from which it is read back
  exactly.
- It is drawn in the plan (top faces filled, all edges), shown in the 3D
  panel, and can be selected, deleted and listed in the properties window
  (points, faces, volume).

**Checked.** `tests/mesh.dl`:
- a 4 × 3 × 2.5 m mass made a mesh (30 m³);
- a top corner raised 1 m (32 m³);
- undo;
- the top pushed 1 m, which moves the face (42 m³);
- the mesh saved and read back as `.bim` and as `.ifcx`;
- a side pushed out 2 m (63 m³);
- a corner raised, then the top extruded (12 points, 10 faces);
- deletion.

**Modify, refusal, lines on faces.**
- **Modify tools.** Move, copy, rotate and mirror work on meshes, with Shift
  adding meshes to the selection. A mirror turns every face loop round, from
  the same first point, so the faces keep facing out. The triangulation of a
  face that is not quite flat stays the same, so the volume is kept exactly.
- **Refusals.** A push or a grab is refused when afterwards the mesh would
  enclose no volume, or a face would turn round. This covers pushing a face
  through the far side of the mesh.
- **Lines on faces.** With the line tool in the 3D panel, the pointer over a
  mesh face snaps to its outline: corners, then edge middles, then any point
  on an edge.
  - The first click starts a line across that face, and a click on the same
    face's outline cuts the face in two along it.
  - A point on an edge becomes a new point of the mesh, in the face on the
    other side of that edge as well, so the mesh stays closed.
  - Each half can then be pushed on its own. Its other half does not run
    along the push, so the pushed half is extruded and a step appears, as in
    SketchUp.
  - A cut along a single edge is refused.

**Checked further** in `tests/mesh.dl`:
- a push through the floor refused;
- a mirrored copy keeping its volume (84.3 m³);
- the copy moved 2 m;
- a 4 × 3 × 3 m block's top cut in two from edge middle to edge middle
  (10 points, 7 faces);
- a cut along one edge refused;
- one half pushed up 1 m (14 points, 11 faces, 42 m³).

**Not yet:**
- There are no loop cuts and no merging of points.
- Meshes cannot be put in components.
- A line on a face must run from outline to outline; a line ending inside a
  face, or crossing several faces, does not cut.

## Selection boxes, the left button in 3D, floor materials (maintainer requests, 2026-10-08)

**Selection boxes.** In the plan and in the 3D panel, dragging with the select
tool draws a selection box, as in AutoCAD and Revit.
- **Window.** Dragged to the right, it is drawn solid blue and takes what
  lies wholly inside it.
- **Crossing.** Dragged to the left, it is drawn dashed green and also takes
  what it touches: an element with a point inside it, or with an edge through
  it.
- **Shift** adds to the selection.

The box tests the edges of each element:
- walls at foot and top, with their uprights (a curved wall through its
  middle);
- slab outlines;
- grid lines at datum level;
- sketch faces and masses as prisms, lines and text anchors;
- instances' parts;
- every edge of a mesh.

In the plan these are seen from above, on the active storey. In 3D they are
projected as the camera sees them. Hidden categories are passed over.

**Several elements at once.** What a box takes is one selection of several
elements of any kind. It is outlined in both views; move, copy, rotate,
mirror and delete act on all of it, and delete is one undoable edit.

**The left button in 3D** now selects, by a click or a box, as in Revit and
Blender. Orbiting moved to the right button and Shift with the middle
button, and the middle button pans.

**Floor materials.** A floor type carries a material: concrete, or timber for
"Vloer hout". A slab has a material, concrete unless set:
- choosing a floor type for a selected slab sets its thickness and material,
  and the type selector shows the type a slab matches;
- the material shows in the properties window, the slab's cut hatch, its 3D
  colour at the fine detail level, a copy, `.bim` (at the end of the slab
  line, only when it is not concrete, so older files read as before) and
  IfcX (`openbim::slab` and the body's material).

**Checked:**
- `tests/box_select.dl`:
  - a window around a wall and a line;
  - a crossing over two walls;
  - the same box as a window taking nothing;
  - Shift adding;
  - the three moved together;
  - all deleted in one edit and undone.
- `tests/floor_types.dl`:
  - a slab given "Vloer hout 200" (timber), with its properties;
  - read back from `.bim` and `.ifcx`;
  - a copy keeping its material;
  - undo.

**Extension and parallel snapping.** After the object snaps and before
tracking, two kinds from Open 2D Studio and AutoCAD are offered.
- **Extension.** Past either end of a straight piece within reach (25 pick
  radii), the pointer snaps onto that piece's line. A dashed line is drawn
  from the end it extends.
- **Parallel.** While drawing, the line from the previous point snaps
  parallel to a piece within reach. Pieces along a polar ray are left out,
  since tracking already offers those directions. A dashed line is drawn
  from the previous point.

Lengths along either are rounded to 5 cm, as on a polar ray. Checked in
`tests/snap_extension.dl`: an extension past a sloping line's end, a point
off it falling to the grid, and a second line drawn parallel to the first.

**The name.** The editor is now called Open BIM Studio:
- the window title;
- the installed command `open-bim-studio`, its menu entry and its install
  directory;
- `OPEN_BIM_STUDIO_HOME`, with `BIM_SLICE_HOME` still read for earlier
  installs;
- the default file `open-bim-studio.ifcx` and the exports;
- the IFC header and project.

The spike keeps its working name in its paths.

## Drawing quality after Open 2D Studio; walls leaning and round in section (maintainer requests, 2026-10-08)

**Drawing quality.** The maintainer asked for drawing quality close to Open 2D
Studio's, pixel for pixel, not its layout. Its canvas renderer
(`src/engine/renderer`) and the AEC extension's renderers were read for their
literal values. The editor now follows them:

- **Anti-aliasing.** The Vulkan layer draws with multisampling:
  - 4 samples where the device's framebuffers take 4 for colour and depth,
    else 2 or 1 (`VkPhysicalDeviceLimits`, read at its byte offsets);
  - a transient multisampled colour image, resolved into the swapchain image
    in the render pass;
  - every pipeline at that sample count.

  Lines, hatching, text and the 3D view lose their staircase edges, as on a
  browser canvas.
- **Canvas.** The background is white. The grid is off by default (F7 shows
  it) and adaptive:
  - minor lines every 0.1 m, coarsened ×5 below 10 px and refined below
    100 px;
  - every fifth line major;
  - minor `#d0d0d0` at 0.5 px, major `#b0b0b0` at 1 px.
- **Elements.** Cut outlines are 1 px black hairlines. Hatch lines are 0.5 px.
  Hatching follows NEN 47 in Open 2D Studio's colours:
  - masonry `#D4908F` with black lines;
  - calcium silicate `#C8C0B0` / `#A8A090`;
  - timber `#F0DCB9`;
  - insulation `#FFFDE0` with a zigzag;
  - concrete solid `#C0C0C0`;
  - steel solid black.

  The line spacing is on the model (80 mm masonry, 75 mm timber), so a
  hatch scales with the drawing; below 2.5 px only the background shows.
- **Selection.** The selection is green `#00B400` and hover is `#00bfff`.
  Grips are 6 px green squares with a white border.
- **Selection boxes.** The window is filled `rgba(0,120,215,.15)` with an 80 %
  border. The crossing is filled green with a 6/3 px dashed border, 1 px.
- **Snap markers.** Markers are 12 px, drawn three times: a dark halo
  (5.5 px, 35 %), a black outline (3.5 px), then the colour (1.8 px).
  - end point: green square;
  - mid point: cyan triangle;
  - intersection: yellow cross;
  - perpendicular: orange foot;
  - parallel: orange bars;
  - nearest: pink diamond;
  - tracking: a cyan cross and ring.

  The name sits in a dark box at (+12, −12), in the snap's colour. Tracking,
  extension and parallel lines are 1 px dashed 6/4, coloured by kind, with a
  ring at their origin.
- **Pointer.** The system pointer is used, as in Open 2D Studio: a crosshair
  while a tool draws, else the arrow. The plan-wide crosshair and pick box
  are gone.

- **Fonts.** Text in the drawing (grid names, area labels, sketch text,
  level labels) is lettered in osifont, Open 2D Studio's ISO 3098 CAD font.
  It is LGPL-3.0 with the GPL font exception and kept with its licence note
  in `examples/bim-slice/fonts`; grid names are centred in their heads.
  Snap labels use the 11 px face.
- **Grid lines.** Grid lines are black 1 px hairlines in Open 2D Studio's
  dash-dot (0.5 m dash, 0.1 m dot, 0.15 m gaps, scaled with the drawing),
  with black heads; halftone grey where the view rules say so.

The UI chrome keeps Open BIM Studio's own look.

**Walls leaning and round in section.** A wall carries `lean` (its top
shifted along the exterior normal) and `rise` (its middle height bowed out).
A point at height z shifts sideways by lean·t + rise·4t(1−t), with
t = z/H: along the exterior normal for a straight wall, radially for a wall
round in plan.

The evaluated solid is the upright wall shaped:
- **Bands.** Every face that is not level is cut into bands at every point's
  height (16 more for a rise). A band of a face with holes is cut into its
  pieces between the holes, so each piece stays flat.
- **Closed.** Points on another piece's edge are put into that edge, so the
  polyhedron stays closed.
- **Shift.** Then every point shifts.

Plan cuts, sections, 3D, the layers at fine detail and IFC all show the
shaped wall, with its openings. Both values are typed in the properties
window ("Lean (top)", "Bow (section)", negative inward). They are stored at
the end of the `.bim` wall line and in `openbim::wall`.

Checked in `tests/shaped_wall.dl`:
- a 4 m wall leaning 0.6 m and bowed 0.3 m, each a closed polyhedron of
  exactly the upright volume (2.4 m³), shifted where expected;
- with a window;
- round in plan and in section;
- a lean as high as the wall refused;
- `.bim` and `.ifcx` round trips.

**Joins.** A straight wall's end joined to another straight wall also slides
along the wall, so that the end stays on its partner as both shift. The shift
d = D·n + s·u must also shift the partner's face by the partner's own D'
(d·n' = D'), which gives s = (D' − D·(n·n')) / (u·n').
- The slide is whole over an end's corners, a mitred end too, and in
  proportion between the ends. A shift along the wall keeps every side face
  flat.
- An upright wall joined to a leaning one is shaped by its end alone, and a
  partner's shape is part of a wall's signature.

Checked: an L corner keeps its two joint corners shared at the top, upright,
with both walls leaning, with one leaning, and at half height with one bowed;
every solid is closed.

**Not yet.** Joins with walls round in plan keep their ends unslid. The plan's
door swings stay at the foot.

## One linear element; types decide what it is (maintainer request, 2026-10-09)

The maintainer asked:
- that everything be stored in IfcX;
- that every linear object (column, beam, skirting, mullion, pipe) be
  basically one element, and every planar one (wall, floor, roof, ceiling)
  another;
- that the UI and the type decide which you draw.

The plan and the planar element's steps are in `element-model.md`. The
linear element is built: a type (role → IFC class, profile, material) and an
element (storey, 3D axis, turn). Details, behaviour and checks are recorded
there, with `tests/linear.dl` and `tests/linear_tool.dl`.
