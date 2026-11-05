# Status

**As of 5 November 2026, `main` after `c53760a`.** This page is updated by hand; the [issues](https://github.com/OpenAEC-Foundation/open-bim-studio/issues) and the commit log are the source of truth.

## Where we stand

- `main` builds on Linux (`build.sh dev`, about 10 minutes) and the dev build starts with the example building.
- The tests that cover each change pass on `main`; a small set of older tests is known to fail and is tracked.
- Everything below has passed its tests, but most of it has **not yet been checked by eye in the running app**. That review is the next step; remarks go into issues.
- 33 issues were closed on 31 October and 9 more since; 49 are open.

## Finished on 31 October

**Ribbon and window**
- Lean ribbon: no duplicate buttons. Home and View each went from 40 to 21 buttons, and the viewport buttons became one Viewport menu.
- Discipline menu (Common 3D, Architectural, Structural, MEP, Civil) chooses which tabs show; new tabs Wood/Steel Framing, Fabrication and Structural (#4).
- One Create view button with a chooser (#110); one Import and one Export button with format lists (#151, part of #120).
- Model tab with a Project settings window and a Levels page (#119).
- Version and source commit in the title bar and on the start screen (#29).

**Modelling**
- One Wall tool with shapes in the floating toolbar: line, arc, tangent arc, rectangle, circle, pick lines; Floor/Roof/Ceiling by sketch, Pick walls or From space (#101).
- Wall top constraint: up to a level with an offset, or attached to a floor, roof or ceiling (#107).
- Gizmo: the up arrow lifts the whole selection, tilt rings about X and Y, Placement rows in the properties (part of #137).
- A moved 3D cursor is the base point for Move and Wall (#90).
- Structural tab with piles and pile tip levels that set the piles' toe levels (#138).

**Sketches**
- Circle, ellipse, rectangle; arcs by start–end–radius, centre and tangent; typed lengths and radii; Trim/Extend; window and crossing box selection; dragging points and edges (#89).

**Views and sheets**
- Section marks with INB arrowheads, selectable in the plan (#106).
- Crop region: select, resize with handles, edit as a sketch (#98).
- Visibility/Graphics category tree with colour and line-weight overrides (#124).
- 3D view: GPU/CPU and frame-rate status, display mode as one choice, a Sun panel (#113).
- Drag views from the project browser onto a sheet; viewport actions on the selected viewport (#128, #112).

**Properties and types**
- Groups that fold, instance and type rows apart, optional property sets (#96); choices as drop-down menus (#99).
- IfcTypes window redesigned: family tabs, filter, layer table with materials and a section to scale (#91).
- 86 types from the INB template in the Dutch type library; 40 mm cavity in the default cavity wall (#92).

**Automation**
- API `ribbon` verb presses any button as a click, `Tab/Label` addressing, more state (#148, part of #130). See [Automation API](Automation-API.md).

**Later on 31 October**
- Home's Build group is four family buttons: Point, Line, Plane and System, with the system recipes in the System menu (#105).
- Drawing types: an MEP branch and the design phases VO/DO/TO under Structural plan and Floor plan (part of #123).
- Gizmo settings and navigation styles (Revit, Blender, SketchUp, Rhino mouse) in the Settings window (#137).

**Kernel**
- Sweep and multi-segment swept blend in the kernel API (#141).

## Since 31 October

**Views, grids and levels**
- Sheetviews: books of sheets with page numbering, a contents page and one PDF per book (#135; books generated from a rule still wait on assemblies, #134).
- Grids: plus handles per side, a spacing pattern (4 x 5400), renumbering a direction, shared grid heights; straight IFC grid axes import as editable grids (#59, #60, #62 in part).
- Levels as storeys relative to the project datum, with the datum height shown and a level's own outline kept (#64, #45).
- Drawing types: area plans BVO, GO and VVO by NEN 2580 beneath Area plan, and a Fabrication Drawings branch (Steel, Precast Concrete, CLT, Wood/Steel Framing, Other) (#123).

**Types and data**
- Profile catalogue: every standard profile as data per series, browsable in the type window; parametric profiles in the open property set `OpenAEC_ProfileParameters`; IFC linear types carry their profile (#95 in part).
- Schedules defined by SQL over the model: a query engine with tested parsing and column order (#129 in part).
- Interface catalogues in UTF-8 with locale settings, and native text shaping tested for Lao (#157, #104 in part).

**Modelling**
- Stairs: quarter-turn winder layouts generated from the stair's parameters; property codes reserved for editable stair geometry (#145, #160 in progress).
- Building systems: better selection, placing similar and picking in elevations; explicit placement commands reserved.

**Performance and measurement**
- Plan and 3D navigation measured stage by stage: the plan is replayed during wheel zoom and rebuilt when input settles, display geometry stays resident across zoom levels, shared component buffers, and a discrete GPU preferred. Stress models up to one million component instances, with recorded orbit timings.
- Kernel checks of wall and slice volumes and general BRep wall booleans against independent analytic values.

**Exchange and release**
- The nine connection types round-trip through binary IFCX (#85).
- Calendar versions (year.week) in every Windows build (#3).
- Research note on USD BRep exchange (#156).

## In progress

| Issue | Work |
|---|---|
| [#145](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/145), [#160](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/160) | Stairs: editable stair geometry, winders, the stairwell reserved before the stair is generated |
| — | Navigation speed in plan and 3D: measured per stage, with frame and cache budgets |

## Open, by area

| Area | Issues |
|---|---|
| Views (rest) | #123 trade categories for MEP, the kinds of fabrication drawing, a project-wide current phase |
| Modelling | #97 openings as one object with edge rules · #108 sloped work plane · #115 free geometry · #134 assemblies and groups · #145 stairs and stair cores · #160 stair generator · #146 standard object library |
| Types and data | #93 classification per type · #95 profiles (drawing own profiles) · #104 language and a complete Dutch version · #66 IFC first · #161 IFCX model construction apart from its serialization |
| Building systems | #30, #68–#72, #76, #125 |
| Views and drawings | #56–#58 one view object and the structural plan · #61–#63 grids and level extents · #65 georeferencing · #127 Drawing Rules preview · #129 schedules by SQL · #133 2D drafting sheet · #135 sheet books by rule |
| Window and layout | #100 Blender-style areas · #111 windows and tabs |
| Exchange and collaboration | #120 IFC Git and OpenAEC Cloud · #144 fabrication formats · #5 IFCCAD export · #77 analytic fastener detail |
| Automation and AI | #130 API as a documented interface · #131 in-app DynLex chatbot · #132 several people in one model |
| Release | #39 installer signing · #162 licence review and REUSE lint in CI |

## Known gaps

- Most of the new UI has only been checked by tests and by compiling, not by eye.
- Windows: the fixes for resolution and blurry icons (#41, #42) were made on Linux and not yet checked on a 4K Windows screen.
- A few older tests fail on `main` (tracked); `properties` and `system_editing` need their expected output refreshed.
