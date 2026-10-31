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
| **Home** | Select · Build: four family buttons — **Point** (Place, Component), **Line** (Column, Beam, Pile, Frame; Pipe, Duct, Cable tray), **Plane** (Wall, Floor, Roof, Ceiling, Space), **System** (Building System and every system recipe); click the icon to repeat the last choice, the arrow for the menu · Openings (Vertical opening, Window, Opening detail, Door) · Grid · Circulation (Stair, Railing, On stair) |
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

## Modelling

- **Wall** (Home > Plane) is one tool. Its shape is chosen in the floating toolbar: Line (chain), Arc (3 points), Tangent arc, Rectangle, Circle, Pick lines; *Location line* switches between centre, exterior and interior face. `AW` starts the three-point arc. Shift keeps the wall straight.
- **Floor, Roof, Ceiling**: with a space selected they follow it; otherwise they open a sketch. In the sketch, **Pick walls (W)** takes the walls' inner faces and **From space (S)** takes a space's outline.
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
