# BIM slice

A thin vertical slice of a BIM modeller on the native DynLex port of
`cadkernel`: semantic walls, doors, windows and slabs, geometry through the kernel, plan
and section drawings, associative dimensions, IFC4 export and an interactive
plan editor, with incremental re-evaluation throughout. It is the code of the
Open BIM Studio spike `spikes/dynlex-bim-slice/`, which records the question
and the measurements.

| File | Contents |
| --- | --- |
| `bim_model.dl` | Levels, compound wall types, walls on centrelines, parametric window and door types, hosted openings, slabs on a level, grids and dimensions with semantic references. Stable 64-bit ids, never reused; transactions with undo and redo; a journal of the ids every edit touches. |
| `bim_index.dl` | Spatial hash index of wall centrelines, used to find the walls that can join a wall. |
| `bim_evaluate.dl` | Footprints with L and T joins and the incremental evaluation, which compares only the journalled elements when it can. Walls are straight or curved (a circular arc set by its bulge). Both are built directly by the fast planar kernel (`lib/fastkernel/wall.dl` and `curved_wall.dl`, with radial jambs in curved walls) when it accepts them, and otherwise by extrusion and boolean voids through the port. Slabs are prisms built by the fast kernel; they join nothing and depend only on themselves and their level. |
| `bim_drawing.dl` | Plan and section views from the kernel's planar section (`lib/cadkernel/brep_section.dl`), with the plane slice as fallback for solids the section refuses, updated per rebuilt wall; dimensions measured between semantic features. |
| `bim_ifc.dl` | IFC4 export: spatial structure with one storey per level, each containing its own elements, wall types with layer sets, walls, openings filled by doors and windows, and slabs, with deterministic GlobalIds. |
| `bim_spaces.dl` | Spaces derived from the walls through the kernel's 2D arrangement, identified by their bounding walls; exported as `IfcSpace`. |
| `bim_scene.dl` | The 3D scene: one mesh per wall or slab, cached per build, and picking of walls, slabs, openings and spaces along a ray. A space's floor is picked only when it lies clearly in front of the slab it stands on. |
| `bim_file.dl` | The native file format: the model as text, one record per line, keeping every id and writing numbers that read back exactly; reading refuses malformed files, naming the fault. |
| `bim_ifcx_binary.dl` | IfcX in a compact binary encoding, the editor's own file (`.ifcxb`): the IfcX JSON document as CBOR (RFC 8949) with string references (tags 256 and 25) and decimal fractions (tag 4), read back into the same JSON values; `tests/verify_ifcx_binary.py` checks it with an independent reader. |
| `reinforcement.dl` | Parametric reinforcement, apart from the editor and the file: straight, L and U bars, rectangular cages with closed hoops, end zones and extra bars, as definitions in metres with cover to the outside of the steel; the bar paths are derived from them. |
| `reinforcement_library.dl` | Bar identification data (NL-R1): diameters and marks, not a design resistance table (see `REINFORCEMENT-LIBRARY.md`). |
| `reinforcement_area.dl` | Area reinforcement and meshes on a floor or wall surface, flat or bent to a signed radius, bars in two directions on one or both faces. |
| `bim_reinforcement.dl` | Reinforcement in the model: stored in transactions, hosted on a beam, column, wall or floor whose shape it follows, tagged, scheduled and drawn from the same derived paths. |
| `connections.dl` | Modular steel connections: a node of 2 to 6 member ends, each trimmed by its own void, with plates, bolts and screws as separate parts; independent of the editor. |
| `bim_connections.dl` | Connections in the model: built from selected member ends, moving with them, their parts named linear elements under the node's id. |
| `bim_connection_geometry.dl` | The voids of a connection carried out on the members' solids (holes through plates and profiles). |
| `bim_editor.dl` | Editor core driven by abstract events: tools, inference snapping, numeric input during a gesture, dragging with joins, undo. |
| `bim_view.dl` | Categories (walls, floors, doors, windows, spaces, grids, dimensions) and view rules: per view (plan, section, 3D) each category visible or hidden, and halftone, starting from the view kind's template. |
| `bim_hatch.dl` | Hatching of cut faces as geometry: a wall's cut divided into its type's layers (bands parallel to the wall in plan, or where a section crosses it), and per material a fill, hatch lines or a zigzag, clipped to the cut. |
| `bim_import.dl` | Imported elements: a BIM-MESH file (written from IFC by `import/ifc_to_mesh.py`) read into read-only scene meshes in their categories, with their labels. |
| `bim_step.dl` | STEP physical files (ISO 10303-21), the text form of IFC: an index of the instances read once, each instance's arguments parsed only when asked for (numbers, strings with their escapes, enumerations, references, typed values, nested lists). |
| `bim_ifc_read.dl` | IFC read directly (IFC2X3, IFC4, IFC4X3): placements, units, polygonal and triangulated face sets, faceted breps, extrusions of arbitrary and parametric profiles, revolutions, swept disks, curves with arcs, mapped items, half-space clipping, openings cut by the kernel's booleans and styled colours, as read-only imported elements (`--import FILE.ifc`, Collaborate > Import > IFC). `tests/verify_ifc_read.py` compares each element's box with IfcOpenShell's. |
| `bim_drawing_standard.dl` | The project's drawing standard (NEN 47, DIN 1356, BS 1192 / ISO 128, US NCS / ANSI) as it shows on the drawings: dimension ends (ticks, dots, arrows), level marks and their text, section heads and the decimal comma. |
| `bim_boundary_sketch.dl` | The boundary sketch, one object for the outline of every planar element, as Revit's sketch mode: Tab on a floor, roof or ceiling opens its outline in the plan, on a wall or building system its profile on its face in 3D, as lines and arcs (L, A; Esc picks, Delete removes); Tab chains them into one closed loop that becomes the element's outline (arcs in pieces within half a millimetre, found back through the corner at their middle). A building system's grid lines stop at its contour, its panels are cut to it and a frame runs along its edges; a wall is cut to it. |
| `bim_system_types.dl` | Building system types, as Revit's curtain wall types: curtain walls, window frames, timber frame (HSB) with its boards as layers, masonry in Dutch formats and bonds, sand-lime elements, standing-seam zinc, timber cladding, HPL panels, hollow-core floors 150 to 400 mm and a suspended ceiling. The type selector lists them; a system remembers its type and shows "(custom)" once changed. |
| `bim_stair_types.dl` | Stair and railing types (timber, hardwood, precast concrete, steel stairs; steel, timber, stainless and strip railings): the parts' linear types, material, height and baluster spacing; "(custom)" once a part is changed. |
| `bim_project_settings.dl` | The project's settings after Bonsai's project setup: units (length, decimals, area, angle, currency) and georeferencing (EPSG, map origin, true north), kept as settings of the project and written to IFC (IfcMonetaryUnit, TrueNorth, IfcProjectedCRS, IfcMapConversion, the OBS_ProjectSettings property set). |
| `bim_ifc_native.dl` | IFC elements made native on import: straight walls (centre line, thickness and layers from IfcMaterialLayerSetUsage, openings with door and window types), slabs, columns, beams and piles become the model's own elements, so grips, joins, Tab's sketch and the properties work on them; the rest stays imported read-only. |
| `bim_api.dl` | The automation API: requests in a folder (`--api FOLDER`, or Collaborate > Automation > API / MCP), answered in JSON: state, elements, ribbon buttons, keys, clicks in the plan, selection, properties, creating walls, floors and building systems, undo. `mcp/` holds the MCP server that drives it. |
| `bim_schedule.dl` | The quantity schedule: per wall type the count, centreline length, net face area and volume; per door and window type the count and rough area; the slabs' area and volume; the spaces' area; as rows and as comma-separated text. |
| `bim_canvas.dl` | Recorded drawings: coloured triangles and labels in pixels, and depth-tested triangles, replayed into a frame. The plan is replayed shifted while it is panned, and the 3D view is replayed until its camera, meshes, selection or rules change. |
| `bim_text.dl` | Text through a glyph atlas: the printable characters are rendered once into one texture, and a line of text is one batch of textured triangles. |
| `bim_ui.dl` | The application chrome after the Open BIM Studio frontend of Open CAD Studio, in Fusion Black: a top bar with quick-access buttons and ribbon tabs; ribbon groups of tool buttons that send the editor the commands its keys send (tools not available yet shown dimmed); a project explorer with the storeys, views and the selection's properties; a command line and a status bar. |
| `bim_loading.dl` | The start-up's loading screen, and an `--import` read on a thread of its own while the editor runs, with a card naming its step and how far it is. |
| `main.dl` | The interactive application: explorer left, plan editor in the middle, the GPU-resident 3D view or the section right, inside the chrome. |

## Running the editor

From the repository root:

```sh
for pair in screen_vertex:vertex canvas_vertex:vertex flat_fragment:fragment text_fragment:fragment mesh_vertex:vertex mesh_instance_vertex:vertex mesh_fragment:fragment mesh_cut_fragment:fragment edge_fragment:fragment edge_cut_fragment:fragment; do
  ./build/dynlex lib/vulkan/shaders/${pair%%:*}.dl --emit-spirv --shader-stage=${pair##*:} -o build/shaders/${pair%%:*}.spv
done
./build/dynlex examples/bim-slice/main.dl -O2 -o build/bim-slice
./build/bim-slice
```

The shaders need the shader-language extensions of `examples/gpu/README.md`,
with `shader discard` (`patches/dynlex-shader-extensions.patch`). The face and
edge fragment shaders share `lib/vulkan/shaders/mesh_shading.dl`, imported by
its path from the root, so they compile from a tree that holds both the
compiler's `lib/shader.dl` and this `lib/vulkan/shaders/`.

**Fonts and shaders.** The application loads
`tests/games/fonts/LiberationMono-Regular.ttf` and the shaders in `build/shaders`.
When `$BIM_SLICE_HOME` is set, it loads `$BIM_SLICE_HOME/fonts` and
`$BIM_SLICE_HOME/shaders` instead.

**Drawing.** It draws through `lib/vulkan/graphics.dl`: DynLex calling libvulkan
and GLFW directly, with no C graphics runtime.
- The 3D view keeps the model on the GPU in four mesh slots: the ground and
  shadows, the imported elements, the shapes imported elements share (an IFC
  element made of one mapped item), drawn in instances, and the native
  elements. Each slot is written again only when what it holds changes. Each
  element's distinct corners are stored once, and the camera, the lighting and
  the highlight of the selection are shader parameters. Which elements show
  (the 3D view's categories, its phase, an isolated storey) is a flag per
  element that the vertex shaders read, as is its halftone (the 3D view's
  rules) and the hidden line view's grey, so that none of these writes the
  model again; the section box is a cut in the
  fragment shaders, drawn by their own pipelines only while the box is on.
  Its feature edges (Hidden and Wire) are a second index list of lines
  between the same vertices, drawn through the same camera; the faces are
  pushed back by a depth bias so that the edges on them stay in front.
- Zooming past a level of detail queues the native round shapes to be meshed
  again: each frame takes from the queue for at most 6 ms, the shapes that
  cover most of the 3D view first, and the view shows what is made so far.
- The recorded plan is a persistent GPU buffer, drawn shifted while it is
  panned.
- Everything else streams through one buffer that grows as needed. `./build/bim-slice --generate 500000` builds an imaginary tower of at least that many walls (99 storeys of 50 x 50 rooms, with facade windows and a slab per storey) for testing at scale; `./build/bim-slice --example` opens an
example house with a ground slab and a first floor; `--example X Y` places it at plan coordinates X and Y metres,
for instance 500000 500000.

**Starting and importing.** A loading screen names each step of the start
and counts them (the window, the fonts, the editor). The editor then runs
while a file given with `--import`, or chosen with Collaborate > Import >
IFC, is read on a thread of its own: a card over the canvas names the step
under way, how far it is and the time so far. The thread reads the file,
finds the walls and floors to make native, reads the other elements and
writes them for the GPU into buffers of its own. When it is done, the
window's thread adds the walls and floors to the model (one undoable step)
and installs the buffers. The first frame prints the time it took and its
parts, which also open the 3D view's import message. The thread is a POSIX
thread started on an exposed function; DynLex counts references without
atomics, so nothing else touches what the thread makes until it has
finished.

**Frames.** Presenting waits for the display (vsync), so the editor never
draws more frames than it shows. When nothing changes (no input, no edit,
the camera settled, no work queued), the loop sleeps until the window's
next event instead of drawing the same frame again. A running import, a
letter waiting for its second and the automation API wake it a few times a
second. The status bar shows the last frame's time on the CPU (the work
before presenting) and on the GPU (timestamps around its commands).

**The ribbon in a narrow window.** When a tab's groups are wider than the
window, they become compact from the last one back (their buttons small,
three to a column); when even that does not fit, arrows at the ribbon's ends
scroll it by a group. The row of tabs leaves out the title, then closes up,
then letters its tabs smaller; sub-tabs that would run into the tabs are
left out.

**The properties panel.** With nothing selected it shows the active storey,
the active tab's view (its drawing type and phase among the view's rows), the
project, its units and its georeferencing. A view chosen in the browser shows
until another tab is made active. A level that is selected shows only its
own rows. An imported element shows its IFC class, GlobalId, name and storey,
read only, taken from the import (the editor does not hold it); it has no
type to choose and no phases. Names and values that do not fit are cut short
with "...", and the whole row shows beside the pointer.

### Importing IFC

`--import model.ifc` (or Collaborate > Import > IFC) reads IFC directly
(`bim_ifc_read.dl`) as read-only elements in their categories. Each element is
drawn in the surface colours styled onto its items, one mesh per colour, and
belongs to the storey that contains it. Collaborate > Import > Storeys from IFC
adds a storey to the model for each imported storey it lacks (undoable), so
each gets a plan; the plan cuts the imported elements of its storey at its cut
height, with their edges below the cut thin and grey, as it draws folded
components (lines only: the cut is not filled; the section does not show
imports yet). `--import model.bimmesh` opens a file converted
by `import/ifc_to_mesh.py` through IfcOpenShell; `--import a.ifcx b.ifcx`
composes IfcX layers.

The 3D view keeps the model, its feature edges and, for models of up to
150,000 triangles, the ground with the shadows on it on the GPU; moving the
camera, zooming, isolating a storey and the section box only set the
shaders' parameters. The import message says how much is drawn in instances.

### Installer

```sh
source .cache/bootstrap/env.sh
examples/bim-slice/installer/make-installer.sh build/bim-slice ../installers/bim-slice-installer.sh
../installers/bim-slice-installer.sh
```

A development build (unoptimised, with debug information) installs side by side as
`bim-slice-dev`, with its own menu entry:

```sh
./build/dynlex examples/bim-slice/main.dl -O0 -g -o build/bim-slice-dev
examples/bim-slice/installer/make-installer.sh build/bim-slice-dev ../installers/bim-slice-dev-installer.sh dev
```

`make-installer.sh` writes a self-extracting installer. It copies the binary, every
library the binary links against from outside the system library directories (here
GLFW and the Vulkan loader from the bootstrap toolchain), and the font with its
licence.

Running the installer:

- installs into `~/.local/share/bim-slice`;
- links `~/.local/bin/bim-slice`;
- adds an applications-menu entry, with an action that opens the example house.

The installed copy does not refer to this repository, its caches or temporary build
files. It needs only the system's libc, X11, FreeType and a Vulkan driver. Running the
installer again replaces it; `~/.local/share/bim-slice/uninstall` removes it.

| Input | Action |
| --- | --- |
| W | Wall tool: click the start, click each next corner; type a length and press Enter to place the next corner along the pointer's direction |
| O | Opening tool: click on a wall to place a window there |
| D | Opening tool with the door type: click on a wall to place a door there |
| B | Add a 0.25 m slab under the selected space, following its outline |
| I | Grid tool: click the start and the end; grids running north-south are numbered 1, 2, 3..., the others lettered A, B, C... Grids show in the plan with heads at both ends, in the section where it crosses them, and in 3D as outlined planes; they export as `IfcGrid` |
| L | Visibility panel: per category, check boxes for visibility in the plan, the section and the 3D view, and halftone in the plan. The rules are saved with the model |
| Page Up / Page Down | Make the storey above or below active; Page Up on the top storey adds a storey on it. The plan cuts the active storey and outlines the walls of the storey below. Over the 3D view with a storey isolated: isolate the storey above or below |
| View > Isolate storey | Show in the 3D view only what belongs to one storey: native elements by their level, imported ones by the storey that contains them (IFC and IfcX). It starts at the active level; again shows all |
| View cube (3D view, top right) | Turns with the camera; a click on a face's middle looks from that side, on a border strip from that edge, on a corner square from that corner |
| S | Select tool: drag a wall end, and the walls that share it follow; or drag a wall by its body, and the ends of the walls joined to it (at its ends and in T joins) follow; drag a selected wall's orange middle handle to bend it into an arc (at most a half circle; back onto the chord to straighten it) |
| Delete | Delete the selected wall, opening or slab, or else the wall under the pointer; a wall goes with its openings |
| Z / Y | Undo / redo |
| X | Export `bim-slice.ifc` to the working directory |
| Ctrl+S / Ctrl+O | Save the model (Save as… asks for a name while it has none; `.ifcxb` binary IfcX by default, `.ifcx` IfcX JSON or native `.bim`) / open a model picked in a dialog. File > New starts from a template (Dutch: mm, NL storeys and types; international: metres). The ten most recent files and the application's settings are kept in `~/.config/open-bim-studio`. A new or opened model in place of one with unsaved changes asks first. Opening clears the undo history |
| Escape | Cancel what is under way (a wall chain, typed input, a grid or section being placed, the visibility panel) and clear the selection; it never closes the editor |
| Ctrl+Q | Quit (as does the window's close button) |
| C | Section tool: click two points; the right panel shows the section |
| V | Switch the right panel between the 3D view and the section |
| [ ] / ; ' | Make the window type narrower / wider, lower / higher; every window of the type follows, and a change that would not fit a wall is refused |
| Right- or middle-drag in the plan, wheel | Pan the plan; zoom it toward the pointer |
| Plan symbols | Doors show their leaf open into the room with its swing; windows their glass between the wall faces |
| Plan and section | Cut walls show their type's layers, filled and hatched by material (brick diagonal, insulation zigzag, concrete crossed, sand-lime fine diagonal); slabs cut in the section are concrete |
| 3D view | Lit by a fixed sun from the south-west; seen from above, the model stands on a ground plane with its cast shadow |
| Drag in the 3D view (left or right button), or Shift+middle-drag | Orbit about the model's middle, also from below; Shift-drag or middle-drag pans, the wheel zooms toward the pointer |
| K | Switch the 3D view's detail level: fine shows each wall's layers as separate solids in their materials' colours (also in reveals and wall ends), coarse each wall as one solid; models of 50,000 walls or more start coarse |
| T | Show the quantity schedule in the right panel instead of the 3D view; E then writes it to `bim-schedule.csv` |
| Handles in the 3D view | The ends of a selected wall and the corners of a selected slab show handles; dragging one moves it across its storey's plane, with snapping, joined walls following, and undo |
| Left click in the section | Select the wall or slab whose cut lies under the pointer; it is drawn in the selection colour |
| - / = | Zoom the plan |
| F | Fit the plan and the 3D view to the model |
| Left click in the 3D view | Select the wall, slab, door or window, or space under the pointer |
| Left click in the plan (select tool, away from wall ends) | Select the opening, wall, slab (click its edge) or space under the pointer; Escape clears the selection |
| Selected slab in the plan | Drag a corner handle to move it; drag an edge's middle handle to add a corner there; Delete removes the corner under the pointer. An outline that would cross itself, or keep fewer than three corners, is refused |

Snapping, in priority order: wall end points, wall mid points, horizontal or
vertical alignment with the chain start, then a 0.05 m grid. Wall points snap on
every storey, so walls can be stacked; hovering, dragging and selecting act on the
active storey only. Hovering a wall shows its length, measured between its start
and finish features.

The status bar shows:
- the storey and the tool;
- the snap;
- the walls and slabs rebuilt by the last change, and the time it took;
- the document revision;
- the time the last frame took before it was presented;
- the last message.

Presenting waits for the display's refresh, so the loop runs at its rate.

## Tests

Headless tests print results that must equal their `.expected.txt` file:

```sh
for test in model evaluate drawing editor spaces pick file journal hatch view curved schedule; do
  ./build/dynlex examples/bim-slice/tests/$test.dl -O0 -o build/bim-$test
  ./build/bim-$test | diff - examples/bim-slice/tests/$test.expected.txt
done
```

`schedule` checks a room's quantities (wall length, net face area, room area) against hand-computed values and prints the example house's schedule and its CSV.
`curved` checks a free arc wall against the exact volume of its ring sector (within 0.05 %), a room closed by an arc
with mitred L joins, a window in the arc against the exact radial void (within 0.1 %), both as closed polyhedra, the
bulge kept to a half circle, the bulge surviving the file, the room's space reaching into the arc, and one hatch band
per layer per piece of the arc.
`view` checks the view templates, toggling a category in one view, each
element's category, hidden categories passed over by selection, and view rules
surviving a save and an open.
`hatch` checks a cavity wall's layer bands in plan and in a section, a cut clipped
to them, and hatch lines and a zigzag against their exact lengths.
`journal` evaluates 400 random edits with undo and redo along the model's
journal and by full comparison, and requires them to agree after every step.
`evaluate` checks a chain of incremental evaluations, including slabs added and
deleted, against a fresh one element by element; `drawing` checks an incrementally updated plan against a fresh cut;
`pick` picks walls, windows, the ground slab and spaces along rays near the
origin and 500 km away, and selects and deletes through the editor; `editor`
also adds a slab under a selected room with B and changes storeys; `file` writes
and reads the example house near the origin and 500 km away, compares text and
evaluated geometry, saves and opens through the editor, and checks the refusals.

`verify_ifc.py` builds `tests/ifc.dl`, exports IFC and checks it with
IfcOpenShell, including:
- every wall's volume, with openings subtracted by IfcOpenShell's own geometry;
- an L-shaped slab's volume and height;
- two storeys, each containing its own elements;
- the grid's U and V axes and their curves.

It needs `ifcopenshell` (0.9 was used).

`drive_gui.py` drives the built editor with real X11 input through XTEST:
drawing walls (one by typed length), placing windows, dragging a corner, undo,
redo, hover, orbit and IFC export, saving a screenshot after each stage and
checking the exported file with IfcOpenShell. Run it against a nested X
server, never the desktop session, because XTEST moves the pointer of the
display it is sent to:

```sh
Xephyr :97 -screen 1400x900 &
DISPLAY=:97 python3 examples/bim-slice/tests/drive_gui.py build/bim-slice build/bim-slice-shots
```

It needs `python-xlib`, Pillow and `ifcopenshell`, and refuses to run while a
`bim-slice.ifc` exists in the repository root.

## Measurements

Build these at `-O2`; they print medians and maxima in microseconds.

- `large_model.dl N` generates the imaginary tower of at least N walls (500,000 by
  default) and times the first evaluation, the ground floor's plan and spaces,
  the scene meshes and one incremental edit, with the peak memory.
- `drag_timing.dl` draws a room of four walls with two windows through the
  editor and drags a corner in 200 steps, timing evaluation with the plan
  update, and tessellation of the rebuilt walls.
- `scale_timing.dl` builds models of separate four-wall rooms from 4 to
  99,856 walls and moves one corner 20 times, timing the evaluation and the
  plan update per move, and the first full evaluation and plan.
- `fast_timing.dl` times the fast kernel against the port: a wall with one and with
  four windows, and the tessellation of a room. `fast_differential.dl N` builds every
  wall of N random models both ways and compares status, volume and sections.
- `far_origin.dl` builds the example house near the origin and 500 km away,
  turned, and prints the largest deviations between the two after moving the
  far results back, and the evaluation times.
- `wall_slice_workload.dl` and `wall_slice_workload.rs` time the window
  difference (mode 0) and the plan slice (mode 1) of one wall in DynLex and in
  the pinned Rust crate; mode 2 times the planar section, in DynLex only. Build the Rust side against a `cadkernel` library compiled at the same
  optimisation level, as `tests/cadkernel/performance/` does, and run both
  with `<mode> <iterations>`; their face counts must agree.
