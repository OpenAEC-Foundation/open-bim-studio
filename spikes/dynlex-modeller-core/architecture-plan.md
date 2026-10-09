# Open BIM Studio: architecture and build plan

**Status:** working plan, 2026-10-09.

The maintainer asked for a complete BIM modeller, including building services
(installations) and sheets. The work is to be planned, one thing at a time,
on a sound architecture. This note sets out that architecture and the order of
the work. `element-model.md` stays the detailed note for the element
families. `FINDINGS.md` records what each step proved.

## 1. Principles

1. **One small core.**
   - The model knows a few geometric families.
   - The type decides what an element is (its role, its IFC class).
   - The UI tool picks the role.
   - A new kind of building part is a new role or type, not a new record,
     wherever the geometry allows.
2. **Reuse the same base elements.** There are four base elements:
   - linear (a profile along an axis);
   - planar (a layered plate);
   - hosted (a void and its filling);
   - free form (a component or a mesh).

   Everything new is built from them. A stair, a railing, a curtain wall, a
   duct run or a fitting adds no new geometry family. It is a *generator*: a
   few parameters whose evaluation yields ordinary base elements, with their
   types, materials, IFC classes, plan drawing, schedules and files.
   Annotation (dimensions, tags, marks) and documentation (views, sheets) are
   not building elements. They live in their own layer.
3. **IfcX is the vocabulary.**
   - Every record has an IfcX form: class, properties, `openbim::` parameters
     and geometry.
   - The `.bim` text form is the same data, one line per record.
   - A property shown in the UI is a property stored.
4. **Everything evaluates incrementally.** An element's geometry is a function
   of its record, its type and the elements it depends on. A signature per
   element decides whether it is built again.
5. **Exact where it matters, fast where it can be.**
   - The fast kernel handles planar polyhedra, followed during a drag.
   - The cadkernel handles B-reps and exact booleans.
   - Meshes are for display only, with level of detail.
6. **Every feature runs the whole chain:**
   - model record;
   - evaluation;
   - plan, section and 3D;
   - schedule;
   - `.bim` and IfcX, written and read back;
   - editor tool and properties;
   - headless test with exact checks.

   A feature is done when that chain holds and its test passes.
7. **One thing at a time.** Each milestone below is finished (chain, test,
   notes, commit) before the next starts.

## 2. Layers

| Layer | Holds | Files |
|---|---|---|
| UI | window, ribbon, browser, properties, view tabs and tiles, sheets | `main.dl`, `bim_ui.dl`, `bim_text.dl`, `bim_canvas.dl` |
| Editor | tools as staged gestures, snapping, selection, transactions | `bim_editor.dl` |
| Documentation | views, templates, annotation, schedules, sheets, export | `bim_view.dl`, `bim_drawing.dl`, `bim_schedule.dl`, *`bim_sheet.dl`* |
| Model | records with stable ids, types, systems, journal | `bim_model.dl`, *`bim_system.dl`* |
| Evaluation | geometry per element, joins, spaces, networks | `bim_evaluate.dl`, `bim_scene.dl`, `bim_component.dl`, `bim_spaces.dl`, *`bim_network.dl`* |
| Files | `.bim`, IfcX write and read, IFC export | `bim_file.dl`, `bim_ifcx.dl`, `bim_ifcx_read.dl`, `bim_ifc.dl` |
| Kernels | cadkernel (B-rep), fastkernel (polyhedra) | `lib/cadkernel`, `lib/fastkernel` |
| GPU | Vulkan, MSAA, smooth shading | `lib/vulkan` |

New files are in *italics*. A module may use the layers below it and never
those above.

## 3. Four base elements, and generators

| Base element | Geometry | Roles (from the type) | State |
|---|---|---|---|
| **Linear** | a profile along a 3D axis | column, beam, mullion, skirting, pipe, duct, cable tray, rail, post, stringer | built (pipe so far) |
| **Planar** | a layered plate on a surface | wall, floor, roof, ceiling, tread, landing, panel | plates built, walls separate |
| **Hosted** | a void in a planar element, and its filling | door, window, opening | built |
| **Free form** | sketch faces, meshes, components (CSG and mesh parts as B-rep) | mass, furniture, equipment, terminal, fitting | built |

**What everything else is made of:**

| Thing | Made of | IFC |
|---|---|---|
| Stair | generator: treads and landings are planar, stringers are linear | `IfcStair` aggregating `IfcStairFlight`, `IfcSlab` (LANDING) |
| Ramp | generator: a pitched planar plate | `IfcRamp` aggregating `IfcRampFlight` |
| Railing | generator along a path: posts and rails are linear | `IfcRailing` aggregating `IfcMember` |
| Curtain wall | generator on a wall's surface: mullions are linear, panels are planar | `IfcCurtainWall` aggregating `IfcMember`, `IfcPlate` |
| Pipe, duct, cable tray | linear, its role from the type, with a connector at each end | `IfcPipeSegment`, `IfcDuctSegment`, `IfcCableCarrierSegment` |
| Fitting (elbow, tee, reducer) | derived at a network node as a free-form component (CSG of the segment profiles) | `IfcPipeFitting`, `IfcDuctFitting` |
| Equipment, terminal | free-form component whose type lists connectors | `IfcFlowTerminal`, `IfcEnergyConversionDevice` … |
| Room | the space found from bounding planar elements | `IfcSpace` |

**A generator** is one record of a few parameters, such as a stair's path,
riser count, going, width and type.
- Its evaluation yields base elements that are derived, not stored. They are
  drawn, scheduled, written and clash-checked like any other element.
- It stays one element to select and edit, and one aggregate in IFC.
- Its parts take their types from a generator type: a stair type names its
  tread plate type, its stringer profile and its railing type.

The core therefore grows by roles, types and generators. Each new kind of
building part reuses the base elements' geometry, plan drawing, hatching,
schedules and file forms.

## 4. Building services (MEP)

Installations are networks, not single elements. The plan adds three things
on top of the families.

1. **Systems.** A `bim system record`:
   - id, name;
   - discipline: water, drainage, heating, ventilation, electrical;
   - a colour.

   In IfcX it is `IfcDistributionSystem` with `PredefinedType`. Elements are
   assigned to it (`IfcRelAssignsToGroup`).
2. **Connectors.** A typed port on an element: a point, a direction, a size, a
   system kind.
   - Segments are ordinary linear elements with role pipe, duct or cable
     tray; their connectors sit at the axis ends.
   - Equipment and terminals are components whose type lists their
     connectors.
   - In IfcX they are `IfcDistributionPort`, related by `IfcRelConnectsPorts`.
3. **The network.**
   - Connectors that coincide are joined into nodes; the segments are edges.
     The evaluation derives the network each time (`bim_network.dl`).
   - Fittings are *derived* at nodes: an elbow where two segments meet at an
     angle, a tee where three meet, a reducer where sizes differ. Each is a
     free-form component (a CSG of the meeting profiles), generated like a
     stair's parts, and written as `IfcPipeFitting` / `IfcDuctFitting`.
   - The network gives flow direction from the source and per-system
     schedules (length per size, fitting counts).
   - It also gives connectivity checks: open ends, wrong system kinds.

**Routing in the editor.** The pipe and duct tools draw segments the way walls
are drawn, chaining from click to click.
- A click starting on a connector snaps to it and takes its size and system.
- Rises are typed as a height or drawn in 3D.

**Clashes.** A check compares elements of different disciplines, by bounding
box and then exact solids. It lists the pairs that intersect, as a
schedule-like view.

## 5. Views, sheets and output

**Views become records.** Each view has:
- a kind (plan, ceiling plan, section, elevation, 3D, schedule);
- a level or cut;
- a crop box;
- a scale;
- a detail level;
- a template (the category rules that exist today).

The project browser and the view tabs list views, not view kinds. A storey
can then have several plans, such as a furnished one and a services one.

**Sheets.**
- A `bim sheet record` holds a size (A0–A4, portrait or landscape), a
  number, a name and a title block (project, drawing, scale, date, author).
- It also holds viewports. Each viewport places one view at the view's scale,
  with its crop.
- A sheet is drawn by recording each view into a canvas, as the plan already
  is, scaled into its viewport, and then the title block.
- Schedules are placed as tables.

**Export.** The canvas recording is vector data, so a sheet exports as PDF
and SVG without rasterising. The PDF writer emits:
- lines with widths and colours;
- filled polygons;
- text in Osifont.

**IfcX.** `openbim::view`, `openbim::sheet` and `openbim::viewport` records.
These are documentation, not building elements.

## 6. Annotation

- **Dimensions** keep their references to semantic features (a wall's face or
  end), not to derived topology, so they survive edits. This is the answer to
  the topological naming problem in the risk register.
- **Tags** show a property of the element they point at (a door's type, a
  room's name and area) and move with it.
- **Section and elevation marks** are the view records seen in plan.

## 7. Order of work (one at a time)

Each step is finished before the next starts. The finishing criterion of each
is its test.

| # | Step | Done when |
|---|---|---|
| 1 | **Solid part properties**: an instance's parts listed and the last part typed | `solid_tool` test resizes a part and the volume follows |
| 2 | **Annotation tools**: the Annotate tab's Dimension and Text, aligned and linear dimensions on walls, tags for doors, windows and rooms | test: dimension values follow a moved wall; tags show type and area |
| 3 | **Views as records**: several plans per storey, crop, scale, templates; browser and tabs on view ids; file and IfcX | test: two plans of one storey with different rules round-trip |
| 4 | **Sheets**: sheet record, title block, viewports, schedule tables; sheet tab | test: a sheet with a plan and a schedule at 1:100 round-trips; viewport transform exact |
| 5 | **PDF/SVG export of sheets** | test: the PDF parses and its line count and text match the sheet |
| 6 | **Walls as planar elements** (step 4 of `element-model.md`) | every existing wall test passes on the planar record |
| 7 | **Stairs** (generator of planar and linear elements): straight, L and U flights, landings, IfcStair | test: riser height and going exact, solids closed, IFC aggregation |
| 8 | **Railings** (generator of linear elements along a path, on stairs and slab edges) | test: posts at spacing, top rail length exact |
| 9 | **Curtain walls** (generator on a wall: linear mullions, planar panels) | test: panel count and areas exact |
| 10 | **MEP systems and connectors** | test: segments joined into a network; open ends listed |
| 11 | **MEP routing tools and derived fittings** | test: elbow and tee at the right nodes; lengths per size in a schedule |
| 12 | **Equipment and terminals** (free-form components with connectors) | test: a radiator connected to supply and return |
| 13 | **Clash check** across disciplines | test: a duct through a beam is reported, a duct beside it is not |
| 14 | **Materials and type editor** (layers, profiles, naming rules applied) | test: an edited type renames by the rules and its elements follow |
| 15 | **Scale**: a 10,000-element model edits interactively | timing test within the budget of R-12 |

After each step:
- the full suite runs;
- `FINDINGS.md` gains a short section;
- the work is committed;
- the app is installed and restarted.

## 8. What stays open

- **Push access:** GitHub authentication is needed to push.
- **DynLex issues:** compile time and memory per test (5–8 min, up to 4.6 GB)
  limit how many tests run at once. This is the largest drag on the loop and
  is drafted as an issue for the DynLex repository.
- **Streaming of very large models** is out of scope for now, as the roadmap
  decides.
