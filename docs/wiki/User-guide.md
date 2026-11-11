# User guide

This page describes Open BIM Studio as it is on `main` (31 October 2026 (evening)). It is a guide to where things are, not a complete manual.

## Starting

- `open-bim-studio --example` opens the example building: two storeys on piles with grids, layered walls, windows and doors.
- Without `--example` the start screen offers new models from templates, **Open...** (`.ifcxb`, `.ifcx`, `.bim`) and recent files.
- The window title and the bottom of the start screen show the version and source commit, for example `Open BIM Studio 2026.44 dev (fec6f42)`. Quote it in bug reports.

## The window

- **Ribbon** at the top, with tabs. At the end of the tab row is the **Discipline** menu.
- **Project browser** on the left: views, sheets, schedules, families.
- **View area** in the middle: plans, sections, 3D, sheets and schedules as tabs.
- **Properties** panel on the right: the selection's properties, in groups that fold.
- **Floating toolbar** at the top of the active view: the actions of the active tool, the open sketch or the selection.

## Disciplines and ribbon tabs

The Discipline menu chooses which tabs the ribbon shows; the choice is remembered.

| Discipline | Tabs shown |
|---|---|
| Common 3D, Architectural, Civil | Home, Sketch, Modify, View, Model, Collaborate |
| Structural | the above plus Concrete+Rebar, Structural Steel, Wood/Steel Framing, Fabrication, Structural |
| MEP | the above common tabs plus MEP |

| Tab | Groups (buttons) |
|---|---|
| **Home** | Select · Build: four family buttons — **Point** (Place, Component), **Line** (Column, Beam, Pile, Frame; Pipe, Duct, Cable tray), **Plane** (Wall, Floor, Roof, Ceiling, Space), **System** (Building System and every system recipe); click the icon to repeat the last choice, the arrow for the menu · Openings (Window and Door; Floor/roof opening, cut in a selected floor or roof; Opening detail, the reveals and sill of a selected opening) · Grid · Circulation (Stair, Railing, On stair) |
| **MEP** | Piping (Pipe) · HVAC (Duct) · Electrical (Cable tray) · Systems |
| **Sketch** | Free geometry: Select, Draw, Shape (Push/Pull, Split face, Offset), Transform, Components, Solids (Box, Cylinder, Sphere, Add, Cut, Intersect) |
| **Modify** | Move, Copy, Rotate, Mirror, Array, Scale · Trim, Extend, Offset, Fillet, Chamfer, Stretch, Split, Align, Join, Lengthen, Explode · Similar, Delete · Make editable (IFC) |
| **View** | Annotate (Dimension, Text, Tag, Tag all) · **Create view** (a chooser: a plan per drawing type, Section, 3D/Section, Schedule, Duplicate) · Windows (Tile, Tabs, Crop, Uncrop) · Drawing types (Automatic, Drawing Rules) · Phasing (Demolish) · Sheets (New sheet, Place view, Place schedule, **Viewport** menu) · Display (Visibility, Detail) · 3D mode (Section box, Box from selection, Isolate storey) |
| **Model** | Project (Settings, IfcTypes) · Levels (Level, Levels) · Checks (Decimals, Round to mm) · Library (Export, Import, NL doors) |
| **Collaborate** | **Import** (a chooser: DWG/DXF, PDF, Image, IFC, Storeys from IFC, IfcX) · **Export** (active plan as DWG/DXF; open sheet as PDF/SVG; model as IFC, IFC 4.3, IFC5, 3D DWG/DXF) · Clashes · API / MCP |
| **Concrete+Rebar** | Bar, L bar, U bar, Cage, Mesh, Area · 3D reinforcement |
| **Structural Steel** | Butt, Miter · Base plate · Node, Plate, Bolts, Screws · steel recipes (End plate, Fin plate, Double cleat, Splice, Gusset, End cap) · welds and connection types |
| **Wood/Steel Framing** | Building System, Frame |
| **Fabrication** | Bending schedule · M8–M40 fastener library, CSG detail · IFC 4.3 and 3D DWG/DXF for production |
| **Structural** | Piles (Pile, Pile tip level) · Pile plan, Drawing Rules · Frame (Grid, Column, Beam, Structural plan) |

Buttons with a key can also be typed, for example `PI` for Pile, `CV` for Crop, `DV` for Duplicate view. Zooming (`ZR`, `ZP`), Fit (`F`) and storey up/down (Page Up/Page Down) are keys only.

## The command line

The strip at the bottom left is a command line in DynLex's own style: you type
English sentences. Press `:` or Ctrl+L, or click the box, to give it the keys;
while it has them, keys and letters go to it and not to the tools (the letter
shortcuts such as `CO` work again once it lets go). Without the keys it shows
the active tool's prompt, as before.

- As you type, the list above the box shows the sentences that fit, with their
  open places: `draw a wall from (x, y) to (x, y)`. The greyed text after the
  caret is what **Tab** adds: the rest of the word, or the next word.
- **Up**/**Down** pick another suggestion; on an empty line they go through the
  sentences run before. **Enter** runs the line; **Escape** clears it, and on an
  empty line gives the keys back (as do Enter on an empty line, a click
  elsewhere, and Ctrl+L).
- On an empty line the list shows the last sentences with their answers.
- A tool's prompt stays in the list's first row while the line has the keys,
  so a sentence can be typed while a tool runs. A dialog that opens (the type
  manager, the project window, a file screen) takes the keys from the line.
- "a", "an" and "the" may be left out; a full stop at the end is fine.
- **Points** are `(x, y)` in metres; a coordinate may carry its unit, as in
  `(5000 mm, 0)`. **Values** for properties are in the project's length unit,
  as the properties panel reads them (millimetres by default).
- A sentence that is not understood is answered with the closest one and the
  word where it goes astray.

| Sentence | What it does |
|---|---|
| `draw a wall from (0, 0) to (5, 0)` | a wall of the current type on the active storey |
| `draw a floor from (0, 0) to (5, 4)` | a floor over that rectangle (`slab` also reads) |
| `draw a section from (2, -1) to (2, 5)` | a section line, as two clicks with the Section tool |
| `draw a grid from (0, 0) to (0, 10)` | a grid line, as two clicks with the Grid tool |
| `place a door at (2.5, 0)`, `place a window at …` | the Door or Window tool, clicked there |
| `place the cursor at (1, 2)` | the 3D cursor |
| `start the wall tool` | any tool by its ribbon label (`start the curtain wall tool`) |
| `press "View/Section"` | any ribbon button by its label, `Tab/Label` or `Tab/Group/Label` |
| `select the wall 162`, `select 162`, `select nothing` | selection; the kind is checked |
| `set the height of the selected wall to 3000` | a property by its label; the kind is checked |
| `set the name of the selected space to "Küche"` | text values in quotes |
| `set the name to "Ground floor"` | a property of the selection, or of the storey and plan when nothing is selected |
| `delete the selected wall` | |
| `open the view "A-A"`, `open the sheet "A-101"` | a plan, section, elevation or sheet as its tab (`plan`, `section`, `elevation` also read) |
| `export the sheet to PDF`, `export the sheet to SVG` | the open sheet |
| `show the View tab` | a ribbon tab |
| `fit the view`, `save`, `undo`, `redo`, `escape` | |

The same sentences run through the automation API (`run SENTENCE`) and the MCP
server (`run_sentence`). A line starting with `>` is kept for real DynLex code,
which needs a JIT that is not built yet.

## Modelling

- **Wall** (Home > Plane) is one tool. Its shape is chosen in the floating toolbar: Line (chain), Arc (3 points), Tangent arc, Rectangle, Circle, Pick lines; *Location line* switches between centre, exterior and interior face. `AW` starts the three-point arc. Shift keeps the wall straight.
- **Floor, Roof, Ceiling**: with a space selected they follow it; otherwise they open a sketch. In the sketch, **Pick walls (W)** takes the walls' inner faces and **From space (S)** takes a space's outline.
- **Building System** (Home > System): the floating toolbar places it **Vertical** (two clicks, like a wall), **Horizontal** (sketch its outline on the plan like a floor, Tab makes it) or **Tilted** (type the pitch from horizontal and Enter, click the line, then the side it rises to or type its length up the slope). A floor or ceiling recipe chosen without an orientation lies level: click its line, then the side it spans to. In the properties, *Orientation (click)* switches a placed system, *Pitch* and *Base above storey* adjust it; changing the recipe keeps the orientation.
- **Wall joins**: where two walls meet, the plan shows a small blue icon in the corner (L where two ends meet, T where an end meets another wall's side), while the Select tool is active and walls are shown; icons never print on sheets or PDFs. Click the icon to select the join; its properties show the kind and the two walls. *Join style (click)* goes Automatic (an L is mitred, a T butts against the host), Mitre, Butt, Square off; for a Butt or Square off at an L, *Runs through (click)* swaps which wall runs through (at a T the host always does). *Not joined (click)* keeps both ends square and free, so neither wall is cut and the plan draws a line between them. Each click is one undo step, and plan, section, 3D, quantities and IFC follow. Delete does not remove a join; use *Not joined*. With a wall selected its end handles still drag the ends: a press selects the join only on the icon itself.
- **Wall ends**: a selected wall shows square handles at its ends in the plan; dragging one makes the wall longer or shorter along its own axis (at least 0.1 m). Walls joined at that end go along, so the join holds.
- **Spaces** are selected on their edge only: click just inside the room, close to its outline. A click elsewhere on the floor selects what lies there, or nothing; the wall along the edge keeps a click on its own body.
- **Section lines**: a selected section (its line clicked in the plan, or chosen in the project browser) shows handles at both ends; dragging one makes the section longer or shorter without turning it (at least 0.5 m).
- **Wall top**: in the properties, *Top constraint* is Unconnected, a level (with a *Top offset*) or a floor, roof or ceiling above; the wall follows when that level or element changes.
- **Piles** take their toe level from the nearest **pile tip level** (Structural tab), a point with a NAP level and a source.
- **Settings** (File menu): the Gizmo page (local or global axes, size, handles, move and turn steps) and the Navigation page (Open BIM Studio, Revit/AutoCAD, Blender, SketchUp or Rhino mouse).
- **3D cursor**: a moved 3D cursor is the base point of the next Move and the first point of Wall and other creation tools.
- **Gizmo**: the arrows move, the up arrow lifts the whole selection, the rings tilt about X and Y. Position and rotation can also be typed in the *Placement* group of the properties.

## Sketches

Tab on a floor, roof, ceiling, wall profile, building system or crop region opens its outline as a sketch. Tab again finishes it (one undo step).

- Draw: line, rectangle (R), circle (C), ellipse (E), arc by start–end–radius (D), arc by centre (O), tangent arc (N).
- Type a value while drawing (digits, Enter): a length, a radius, the ellipse's semi-axes, a rectangle's width then height.
- Trim/Extend to a corner (T): click two lines on the parts to keep.
- Box selection: left to right selects what lies inside, right to left also what it touches; Shift adds. Drag a point or edge to move it; K switches an arc between keeping its bulge and keeping its radius.

## Views and sheets

- **Create view** lists a plan per drawing type — including the MEP plans and the VO/DO/TO phases of the structural and floor plans — and the other view kinds.
- **Crop region**: click a plan's crop frame to select it; drag its handles, or Tab / *Edit sketch* to give it any outline.
- **Visibility/Graphics** (View > Visibility): a category tree by IFC class (walls and floors split into structural and non-structural) with overrides for shown, halftone, colour and line weight, inherited along the drawing types.
- **3D view**: the status button at the bottom right shows GPU/CPU and frame rate (click for details); the display mode is one drop-down; the Sun panel sets a fixed angle or a place and time.
- **Sheets**: drag a plan, section or schedule from the project browser onto an open sheet; it snaps to other viewports and a 5 mm grid. Right-click a viewport (or use the floating toolbar) to activate it, open its view, change its title type, move, copy or delete it.

## Properties and types

- The properties panel shows **Instance** and **Type** rows apart (type rows are marked); groups fold by name and stay folded. Choices are drop-down menus. *Add property set* offers IFC common sets, manufacturer, warranty and condition sets, or an own set.
- **IfcTypes** (Model tab, or *Edit type* in the properties) shows the types by family: Layered (wall, floor, roof, ceiling), Profiled (column, beam, pile), Openings and Profiles. Type to filter; the layer table edits function, material, thickness and core, with a section to scale.
- The Dutch type library holds 86 types from the INB template (walls, floors, roofs, columns, beams); the default cavity wall has a 40 mm cavity.
- **Model > Settings** opens the Project settings window (units, decimals, georeferencing) and **Levels** its levels page.

## Files and exchange

- Projects are saved as IfcX (`.ifcx`, binary `.ifcxb`); `.bim` still opens.
- IFC goes in (as read-only elements that *Make editable* turns into model elements) and out (IFC, IFC 4.3, IFC5).
- Plans export as DWG/DXF, sheets as PDF/SVG, the model in 3D as DWG/DXF.
