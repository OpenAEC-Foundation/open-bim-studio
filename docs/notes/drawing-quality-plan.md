# Drawing quality plan

**Question:** what stands between Open BIM Studio and professional, BIM-correct Dutch floor plans, sections and sheets, and in which order do we close it?

**Method:** a read-only audit of plan, section, sheet and BIM code on 5 November 2026 (main 74d8cfa), driven by rebuilding the KIT FZK-Haus through the automation API; 71 claimed gaps were each checked against the code before ranking. File and line references are to that commit.


Items are ordered by impact first, then by effort (S, then M, then L). Duplicates from the verified findings are merged into each item. All file references are against obs-merge origin/main (74d8cfa).

## High impact, effort S

### 1. Print sheets as NEN technical drawings: black on white, with steel and concrete still visible
- **Why it matters:** A-101 prints red and tan wall fills and blue windows, while its legend says "Cut element, hatched". When the technical palette is on, solid NEN concrete and steel print as empty white, the same as air.
- **Change:**
  - In `record bim sheet viewport` (ui/shell/bim_app_parts.dl:1088-1110), force the technical presentation for sheet output. Also make setting 2400400 default to 1 for drawing-type plans in `add bim view of kind` (views/common/bim_view.dl:216-231).
  - Check the palette in the places that still use fixed colours:
    - the column cut hatch in `draw bim linears in plan` (ui/panels/bim_plan_panel.dl:1678), which passes `plain false`; pass `plainCuts` instead
    - opening detail edges (3572-3573)
    - grid lines and heads (741-756), which turn blue when technical is on; update ui/panels/tests/plan_presentation.dl:37-39 to match
    - storey below (1425) and pile tips (1915-1916)
  - In the `isPlain` branch of `draw bim hatch` (bim_plan_panel.dl:245-251), stop forcing every fill to white. Steel stays solid black. Concrete gets a grey tone or its NEN black-and-white hatch (materials/bim_hatch.dl:129-139).
- **Effort:** S

### 2. Decide hatch density in paper millimetres, not canvas units
- **Why it matters:** At 1:100 every NEN 47 line hatch (spacing 0.03-0.08 m) and every insulation zigzag on a band of about 60 mm or less is dropped on the PDF. The SVG uses a different cut-off, so the outputs disagree.
- **Change:**
  - In `draw bim hatch` (bim_plan_panel.dl:270-276), compute `spacing * transform's scale / canvas's paperScale` when paperScale > 0. Compare that against a threshold in mm (about 0.5 mm).
  - Apply the same test to the band width in `append bim zigzag` (materials/bim_hatch.dl:404-408).
- **Effort:** S

### 3. Draw sections on sheets in section coordinates, with NEN level marks and cross-references
- **Why it matters:**
  - An uncropped section is framed and centred on the plan footprint.
  - Its level lines span the wrong length.
  - The peil triangles are 12 mm wide and blue, and they come out 2.83 times larger in SVG than in PDF.
  - Section numbers can repeat, and the marks name no sheet.
- **Change:**
  - **Extent:** add a section branch to `the bim model extent of view` (views/sheets/bim_sheet.dl:64-86). It runs from 0 to the line's run, and in height from the lowest level to the highest wall top.
  - **Level lines:** in `draw bim levels in section` (bim_app_parts.dl:493-520), scale every length by `the bim symbol scale`, draw in 0,0,0, and skip levels outside the extent.
  - **Level mark:** give `append bim level mark` (views/drawings/bim_drawing_standard.dl:135-170) a scale parameter.
  - **Grid line:** start the line at headRadius × symbolScale (bim_plan_panel.dl:983).
  - **Numbering:**
    - Number new sections as max + 1, not count + 1 (bim_view.dl:229-243), and give a duplicated view a new number (bim/bim_model.dl:902).
    - Allow letters (A-A).
    - The divided head writes the number of the sheet that places the view (bim_plan_panel.dl:895-913).
    - Title style 1 uses the view's `detail`, not `index + 1` (bim_app_parts.dl:1553).
- **Effort:** S

### 4. Add a north arrow and peil marks to plans
- **Why it matters:** These are standard on a Dutch plan sheet. True north is stored, but only the IFC writer uses it. The `bim level marks annotation` rule is never read.
- **Change:**
  - **North arrow:** add a new `draw bim north arrow`, rotated by `the bim project north of` (bim/bim_project_settings.dl:104-108). Call it from the plan branch of `record bim sheet viewport` and from the live plan in main.dl.
  - **Plan level mark:** gate it on `bim level marks annotation` (bim_view.dl:492). Place it with the existing `append bim level mark` and `the bim level text of` ('P', 'P -0,020', plus the NAP value when the project is georeferenced).
- **Effort:** S

### 5. Fix the IFC STEP placement and type errors
- **Why it matters:** Windows on upper floors and in gable walls drop to ground level in IFC. Wall occurrences contradict their own type, and untyped slabs carry no material.
- **Change:**
  - **Openings** (ifc/bim_ifc.dl:764): place the opening relative to the storey placement at the sill height. For a plain wall, use sill − baseOffset relative to `wallLocal`.
  - **Wall PredefinedType** (bim_ifc.dl:706): take it from `the bim kept predefined type`, as slabs already do (802).
  - **Slabs:** associate an IfcMaterial with untyped slabs (645-653), and give typed slabs an AXIS3 IfcMaterialLayerSetUsage.
  - **Follow-up (effort M):** rotate the wall placement along the wall and add an 'Axis' representation. Fix the layer sense to `.POSITIVE.` with offset −t/2 (114-120, 701-717).
- **Effort:** S (the follow-up is M)
- **Status (5 November 2026):** the opening placement, the wall PredefinedType and the untyped slab's IfcMaterial are done, proven by `ifc/tests/ifc_placement.dl`. Still open: the AXIS3 IfcMaterialLayerSetUsage for typed slabs, and the M follow-up (wall placement rotation, 'Axis' representation, layer sense).

## High impact, effort M

### 6. Make the sheet viewport draw the same plan as the live view, for its own storey
- **Why it matters:**
  - A first-floor sheet printed while the editor is on the ground floor shows the ground floor's room outlines and areas.
  - Sheets have no slab or roof edges, no NEN 2580 area annotations, no pile or beam annotations, and no imported elements.
- **Change:**
  - In `record bim sheet viewport` (bim_app_parts.dl:1087-1102), rebuild `shown's spaces` with `the bim spaces of … on level` for the viewport's own level, as bim_editor_core.dl:1050 does. This part is S.
  - Make a canvas version of `draw bim slabs` (bim_plan_panel.dl:1462-1541).
  - Move the live plan's draw sequence (main.dl:3472-3533) into one shared plan-recording function that both paths call. It covers annotations, area measures, imported-mesh plan lines and the sketchy flag.
- **Effort:** M (the rooms fix is S)

### 7. Size the viewport frame from what the view actually draws
- **Why it matters:**
  - The title 'Erdgeschoss 1:100' sits on the overall dimension chain.
  - The overlap and border checks miss dimension chains and marks.
  - A schedule's frame is the building's wall extent instead of its table.
- **Change:**
  - **Plans:** in `the bim model extent of view` (bim_sheet.dl:64-86), include wall thickness, the chain offsets (bim_exterior_dimensions.dl:15-21), the elevation marks 3 m out, grid heads and labels. A simpler route is to take the bounds of what was recorded on the canvas.
  - **Schedules:** in `the bim frame of viewport` (bim_sheet.dl:97-102), use the table rectangle: 180 mm wide, 9 mm + 6 mm per row (bim_app_parts.dl:1014-1034). This part is S.
  - **Title:** place it below the annotation extent (bim_app_parts.dl:1551).
  - The placement fault check (bim_sheet.dl:271-298) and the snapping (bim_sheet_workspace.dl:153-179) then follow automatically.
- **Effort:** M

### 8. Set up one NEN-ISO 128 pen table in paper mm, and write the PDF with real stroked lines
- **Why it matters:**
  - The cut outline (0.25 mm) is as thin as door leaves and window panes.
  - Room-separation lines and sketches (1.5) are heavier than the cut.
  - A 0.50 mm pen override prints at about 0.36 mm.
  - The PDF draws every line as filled triangles, which leaves notches at rectangle corners.
- **Change:**
  - Add a pen table per line role and scale: cut 0.5, visible 0.25, hidden, hatch and dimension 0.13-0.18, sheet border 0.7.
  - Base `the bim cut line width under` (bim/bim_model.dl:479-486) and `record bim strokes` (viewer/bim_canvas.dl:62-66, 145) on that table.
  - Fix the 0.35/0.25 mismatch in `the bim pixel width of weight` (views/common/bim_category_tree.dl:487-492).
  - Reassign widths:
    - door leaves and panes (bim_plan_panel.dl:629-638)
    - stairs, with dashed treads thinner and dashes in paper mm (2085-2091, 2172-2174)
    - room-separation lines thin and dashed, or left off the print (2410-2436)
  - **PDF:** for stroked batches, write `w` / `J` / `j` / `S` (views/export/bim_pdf.dl:55-68) instead of the triangles from viewer/bim_canvas.dl:91-106.
- **Effort:** M
- **Status (6 November 2026):** done for paper, proven by `views/export/tests/pdf_pens.dl`. The pen table is `bim/bim_pens.dl`: cut 0.50, visible 0.25, hidden 0.18, hatch 0.13, dimension 0.18, thin 0.18, frame 0.35 and border 0.70 mm. `record bim pen … strokes` (viewer/bim_canvas.dl) takes the pen's width when the canvas has a paper scale and keeps the pixel width on screen. Pens now apply to the cut outlines, hatching, door leaves (visible), panes (thin), stairs (visible and hidden, with a thin walking line), linears, opening details, dimensions, leaders, the sheet border, the title block, the legend and the schedule table. A weight override is a quarter millimetre per symbol unit, so 0.50 mm prints at 0.50 mm. Each stroked batch keeps its width, and the PDF and SVG writers draw it as stroked lines: segments that join become one subpath, and a rectangle closes with `h`/`Z`. Still open: dashes are still in canvas units rather than paper millimetres (stairs, demolished work, linears above the cut); the pens do not vary by scale; section-only strokes (levels, marks, grids) keep their pixel widths; and the screen keeps its pixel widths, so its cut is not twice as heavy as the visible lines.

### 9. Give rooms a name, number and NEN 2580 area everywhere
- **Why it matters:** A-101 shows '12.98 m2' with no name or number. Small rooms (WC, meterkast) lose their label. IFC exports IfcSpace named 'Space 12.98 m2', and the room schedule is one total.
- **Change:**
  - **Plan labels** (`draw bim space labels`, bim_plan_panel.dl:1580-1608):
    - Format the area with `the bim decimal text … under` (bim_drawing_standard.dl:47-58) and write 'm²'.
    - Show name and number.
    - Gate the labels on `bim room labels annotation` (bim_view.dl:486).
    - Give small rooms a leader instead of dropping them (1594).
    - Keep the anchor clear of door swings, or store a movable label position on the space record (bim_model.dl:2134).
  - **Numbering:** converting a region gives a storey-based number such as 0.01, not `nextId` (ui/editor/bim_editor.dl:119).
  - **Stale outlines:** re-derive or flag an explicit space whose outline no longer matches its walls (architectural/spaces/bim_spaces.dl:304-325).
  - **Multi-storey walls:** let walls that rise from a lower storey bound rooms on upper storeys (bim_spaces.dl:71, 177).
  - **IFC STEP** (ifc/bim_ifc.dl:992-1009):
    - Write the explicit spaces with Name = number, LongName = name, their own height and Qto_SpaceBaseQuantities.
    - Filter derived regions with `the bim unsaved regions`.
  - **IFCX:** add LongName and use NetFloorArea (exchange/ifcx/bim_ifcx.dl:1476-1495).
  - **Schedule:** one row per room, across all storeys (views/schedules/bim_schedule.dl:218-224).
- **Effort:** M

### 10. Title block, project data, revisions and sheet typography
- **Why it matters:**
  - The stempel shows only the name, number, scale, format and a fixed 'Open BIM Studio'.
  - There is no project, opdrachtgever, phase, date or revision.
  - All text is 7 pt.
  - The labels are in English, Helvetica is not embedded, and SVG drops ß, ² and ø.
- **Change:**
  - **Project data:**
    - Add settings codes for project name and number, opdrachtgever, architect and phase (bim/bim_project_settings.dl:13-44).
    - Use them in IFC (bim_ifc.dl:527-532) and IFCX (bim_ifcx.dl:858).
  - **Sheet record:** add a revision list plus date and drawn/checked by (views/sheets/records.dl:9-18, `set bim sheet` in bim_sheet.dl:219-234).
  - **Stempel:**
    - Redraw `record bim sheet frame` (bim_app_parts.dl:1141-1192) with those fields and a revision table.
    - Follow NEN-EN-ISO 5457: a 20 mm margin on the left, a 0.7 mm border and centring marks (1155-1163, bim_sheet.dl:285-286).
  - **Text heights:**
    - Add a height in mm to `bim canvas text record` (viewer/bim_canvas.dl:21-34).
    - Use it per label in bim_pdf.dl:53-90 and bim_svg.dl:60-66: 2.5 mm for dimensions and rooms, 3.5 mm for titles, 5-7 mm for the drawing number.
  - **Dutch text:** put Blad, Schaal, Legenda and Diverse through `the bim message … defaulting to` and add the keys to localisation/messages/nl.json.
  - **Fonts:**
    - Embed osifont in the PDF (bim_pdf.dl:112, 147) and centre text on real glyph widths (74-75).
    - Keep UTF-8 in the SVG (bim_svg.dl:10-29).
  - **File names:** project_number_revision.pdf, written next to the model (main.dl:3012, 3038; bim_app_parts.dl:1335, 1357-1360).
- **Effort:** M
- **Status:** largely done (`mod/views/title-block`, 6 November 2026). Project data are properties of element 0 (set "Project data"), typed on the new Project data page of Model > Project settings and in the project's properties (codes 12820-12824); IFC writes IfcProject Name (number), LongName and Phase and the client and architect as IfcActor, IfcX the project's name, and STEP strings escape non-ASCII as `\X2\`. A sheet's date, drawn and checked by and its revisions are sheet properties (sets "Title block" and "Revisions"), typed in the sheet's properties (12825-12828, "Add revision"). The frame follows NEN-EN-ISO 5457 (20 mm filing margin, 0.7 mm, centring marks); the stamp is 180 by 48 mm with a revision table over it (`views/sheets/bim_title_block.dl`). Canvas labels carry a height in mm, used by PDF, SVG and the sheet on screen (1.8 captions, 2.5 values and default, 3.5 titles and viewport titles, 7 drawing number). Sheet, Scale, Legend, Diverse, Contents and the legend entries come from the catalogue with Dutch entries; the SVG keeps UTF-8. Test: `views/sheets/tests/title_block`. Left: osifont embedded in the PDF and centring on real glyph widths (the PDF still names Helvetica, WinAnsi only); file names project_number_revision.pdf.

### 11. Clean up wall T-junctions in the cut outline
- **Why it matters:** At every inner wall on A-101, the outer wall's inner face line runs straight through the junction, so the walls do not read as one mass.
- **Change:** in `draw bim hatched cut faces` (bim_plan_panel.dl:303-365, 430-441), replace the exact-edge match with collinear-overlap subtraction. For each edge, remove the intervals covered by opposite-direction collinear edges of other wall rings, and draw only what is left. This handles L-joints and T-joints alike.
- **Effort:** M
- **Status:** done. `append bim uncovered parts of wall edge` subtracts the stretches that other walls' cut edges cover on the same line with their wall on the other side; `collect bim wall edges of` turns every wall ring anticlockwise first, so the rule does not depend on the kernel's loop direction. ui/panels/tests/wall_junctions.dl measures a T junction, a butt L corner and a mitred L corner. Left: only walls are joined this way (a column or slab cut against a wall still draws its line), and a wall hidden by the view rules still interrupts its neighbour's line, as the exact match did.

### 12. Draw real window and door symbols
- **Why it matters:**
  - Windows are three fixed lines with the glass off-centre, no frame and no sills.
  - Window sills are never compared with the cut height.
  - Doors cannot be handed and are drawn too wide.
  - Double doors draw as a single leaf of about 1.69 m.
- **Change:**
  - **Windows:**
    - In `append bim window panes` (bim_plan_panel.dl:559-571), read `openingType`'s frame and sill (architectural/openings/records.dl:16-17). Draw the kozijn at its position and depth, the glass centred in it, a vensterbank inside and a waterslag outside.
    - In `draw bim openings in plan` (573-646), compare sill and head with the cut height and draw dashed or omit when above.
  - **Doors:**
    - Add hand and swing fields to `bim opening record` (records.dl:21-28) and a flip action.
    - Make the leaf the clear width, not the rough width (bim/bim_model.dl:1451-1453), drawn with thickness.
    - Draw the frame, and a threshold on exterior doors.
    - Read the `leaves` setting (bim_model.dl:1777) for double doors.
- **Effort:** M
- **Status:** done on `mod/architectural/opening-symbols` (6 November 2026). The symbol is `the bim plan symbol of opening` (architectural/openings/bim_opening_symbol.dl), drawn by `draw bim openings in plan`; hand and swing are opening settings 2402520–2402521 with Flip hand/Flip swing (2475–2476) and Hand/Opens property rows (12830–12831); tests `opening_symbols` and `opening_symbols_editor`. Left: the opening type has no frame depth or position, so the frame is a fixed 114 mm on the wall's line (a type parameter would make it real); outer walls are found by a ray test, so a wall facing another wing reads as inner (no sills, no threshold); Mirror does not yet flip a door's hand; IFC export does not yet write the hand as `OperationType`.

### 13. Hatch floors and roofs per layer in cuts
- **Why it matters:** A cut slab or roof shows only its thickest layer's material. A roof whose thickest layer is insulation gets no zigzag, because its band is unbounded.
- **Change:** in `the bim hatch bands of` (bim_plan_panel.dl:210-228), add a plate branch with one bounded band per layer, parallel to the plate and taking pitch and heading into account. The alternative is to cut `the bim layer solids of plate` (elements/planar/bim_evaluate.dl:1471-1500) in the cut source in views/drawings/bim_drawing.dl:116-128. Either way the zigzag at line 262 then fires.
- **Effort:** M
- **Status (6 November 2026):** done on `mod/views/plate-layer-hatch` by the first route. `the bim plate hatch bands of … cut by` (materials/bim_hatch.dl) gives a typed plate one bounded band per layer where any view plane cuts it, from the plate's own geometry: a pitched plate is the flat one sheared along its heading, so each layer face is a plane and its line in the view plane gives the band. A plan crosses a pitched roof in bands across its heading (thickness over slope wide), a section in bands parallel to the roof; a plane parallel to a flat plate lies in one layer, which covers the cut. `the bim hatch bands of` (ui/panels/bim_plan_panel.dl) now takes the view's plane and uses these bands for plates, so every layer gets its own NEN 47 pattern and the insulation its zigzag, in black with the hatch pen on technical drawings and sheets. Test: `ui/panels/tests/plate_layer_hatch` (a two-layer roof pitched 1 in 2 in plan and section, a three-layer floor in section, the flat case). Left: a roof reshaped by its roof form (`bim plate … takes a roof form`, a curved cross-section) keeps one band of its thickest layer, since its layers are no longer planes; a layer's edge reach past or short of the outline (`bim layer edge setting`) is not drawn, because the cut is of the plate's whole solid, not of `the bim layer solids of plate`; an untyped plate stays one band of its material.

## High impact, effort M to L

### 14. Dimensioning: facade-wide chains, readable text, and height chains in sections
- **Why it matters:**
  - Collinear wall segments get separate overall dimensions, so no facade is dimensioned corner to corner.
  - Chain offsets double at 1:50.
  - Text overlaps on short segments.
  - Extension lines have no gap or overshoot.
  - Sections have no height dimensions and no peil marks for maaiveld, foundation, goot or nok.
- **Change:**
  - **Exterior chains:** in `add bim exterior dimensions` (ui/editor/bim_exterior_dimensions.dl:112-208), group the collinear exterior segments of each facade. Store the offsets in paper mm (8/14/20) and resolve them per view scale, not as model metres (15-21).
  - **Dimension text:** in `record bim dimension text` (viewer/bim_canvas.dl:283-289), compare the text width with the segment and move or stagger the text when it does not fit.
  - **Extension lines:** add about a 1.5 mm gap and a 2 mm overshoot (bim_plan_panel.dl:2276-2295).
  - **Sections:** give `bim dimension record` a view id and vertical references (views/drawings/records.dl:38-47). Draw dimensions in the section paths (bim_app_parts.dl:636-639, 1117-1138), with automatic chains for floor-to-floor, sill and head, and ridge. Add element-height peil marks and a ground line in `draw bim levels in section` (495-520).
- **Effort:** M (plan chains and text), L (section heights)

### 15. Build a 2D hidden-line projection for plans, sections and elevations
- **Why it matters:**
  - Plans show nothing below the cut (parapets, slab edges, steps) and nothing dashed above it (roof overhang, beams).
  - Sections are hatched slivers floating on white, with no windows, doors, stairs or components and no view depth.
  - Elevations are empty frames on a sheet.
- **Change:**
  - In views/drawings/bim_drawing.dl:116-128, keep the cut polygons and add visible projected edges within a view depth. In plans, edges below the cut are thin and edges above it dashed.
  - Bound the section to its line (0..run) and add depth and flip fields to the view record (views/common/records.dl:14-35).
  - Add openings, stairs, systems and instances to the evaluation used for sections (elements/planar/bim_evaluate.dl:59-62).
  - Clip the section to its crop on the sheet.
  - **Elevations:** add a branch to `record bim sheet viewport` for elevation views (detail 1-4) that uses this projection. Also handle elevations in the viewport title (bim_app_parts.dl:1546), the extent (bim_sheet.dl:77-86) and the scale text (247), and draw a ground line and level marks.
- **Effort:** L

## Deferred

These findings are verified but ranked below the 15 above:
- NEN 2580 GO ignoring free height under 1.5 m, voids and shafts (architectural/spaces/bim_spaces.dl:141-266), effort L
- Stair break line and walking-line start mark (bim_plan_panel.dl:2127-2177), effort M
- Legend showing a generic hatch instead of the materials on the sheet, and the elevation-mark sample leaving its row (bim_sheet.dl:104-206), effort M
- Elevation level text in the 3D view ignoring the drawing standard (ui/panels/bim_view_panel.dl:1842-1898), effort M
- Roof and gable-wall schedule areas based on plan geometry (bim_schedule.dl:150-196), effort S
- IfcStairFlight with riser and tread data, and component instances and systems in IFC STEP, effort M
- IFC import of roof slabs and IfcSpace, effort M
- Elongated paper formats, effort S
- Rooms in the CAD export (ui/panels/bim_cad_export.dl:106-122), effort S
## Verdict

Work the list top down: items 1-5 (effort S) first, then 6-13. Item 15 (a hidden-line projection) is the largest single step toward complete sections and elevations and needs its own design note before code.
