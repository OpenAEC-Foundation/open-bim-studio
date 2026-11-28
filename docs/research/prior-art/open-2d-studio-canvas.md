# Open 2D Studio: the 2D canvas as the model for plan editing

**Decision question:** Which behaviours of the Open 2D Studio canvas (snap, polar tracking,
the input panel beside the cursor, the modify tools, selection, gridlines) does the plan
editor of Open BIM Studio lack, and in what order should they be brought over?

**Status:** draft
**Author:** maintainers, with an AI agent reading both code bases
**Last updated:** 2026-11-28

---

## Summary

The maintainer wants the plan editor to work as the Open 2D Studio canvas does. Most of the
tools already exist here; what is missing is the input panel beside the cursor, annotation
that follows the drawing scale on screen, a handful of snap kinds and options, and a few
tool flows that differ. Three quirks of the reference are not worth copying.

## What it is

Open 2D Studio is the foundation's earlier 2D CAD application (TypeScript, React, Tauri;
release 0.35.0 of March 2026, repository `OpenAEC-Foundation/open-2d-studio`). Its canvas is
the behavioural reference for 2D editing: two-letter commands, object snap with markers,
polar tracking, a panel beside the cursor that shows and accepts lengths and angles, and
modify tools that share the options Copy, Multiple and an axis lock.

Everything below about the reference was read in its source (release 0.35.0); nothing was
run for this note. Everything about Open BIM Studio was read in this repository at the
commit of the date above, and the two-letter commands CO, MV and RO were tried with real key
presses in a dev build.

## Evaluation

Evidence type for every row: **read in source** (not measured).

| Area | Open 2D Studio | Open BIM Studio today | Gap |
|---|---|---|---|
| Two-letter commands | 750 ms buffer; MV, CO, RO, MM, RE, AY, AL, TR, EX, OF, FL; G moves at once, E stretches | same buffer and the same letters; CI, AR, PL, EL, SP, LE, LB, IM, TL answer "not in the modeller yet" | drawing tools for circle, arc, polyline, ellipse |
| Snap kinds | endpoint, midpoint, centre, intersection, perpendicular, parallel, tangent, nearest, origin, grid; 10 px aperture (5 to 30) | end, mid, intersection, perpendicular, nearest, extension, parallel, 50 mm step; 8 px | centre and tangent, snaps on arcs, a settable aperture |
| Snap marker | 12 px glyph per kind with its own colour and a name label | 6 px glyph per kind with a label | none that matters |
| Polar | on by default, 45 degrees, steps of 5, 10, 15, 30, 45, 90; dashed ray with "Polar: N" | fixed 45 degrees; horizontal and vertical always tracked | a settable step |
| Ortho | F8, the ORTHO button, or a press of Shift as a toggle | F8, or Shift held | none |
| Object tracking | parallel and perpendicular rays to every line, extensions from nearby ends (F11) | extension and parallel from nearby segments | a toggle; otherwise close |
| Panel beside the cursor | F12; Distance and Angle for line, wall, gridline, beam; Width and Height for a rectangle; Distance for move and copy; Angle for rotate; Count and Distance for array; digits fill the first field, Tab locks and moves on, Enter applies; X, Y, dX, dY shown below | typed values show in a panel at the top left and in the command line; beside the cursor only a wall's length | the whole panel |
| Typed coordinates | plain distances and expressions only | distances, `x,y`, `#x,y`, `@dx,dy`, `@d<angle`, expressions | none (richer here) |
| Move | base point, destination; Copy option; returns to Select | the same; no prompt after MV with a selection (fixed on the date above) | none |
| Copy | repeats by default (Multiple), ends on right-click or Esc | repeats until Esc | a Multiple switch, right-click to end |
| Rotate | centre, start ray, end ray; typed angle; Copy; stays active | centre, reference direction, new direction; typed degrees; Copy; returns to Select | whether it stays active |
| Mirror | two axis points; Copy on by default; stays active | the same; returns to Select | whether it stays active |
| Array | base point, end point; Count (default 5) in the cursor panel; copies spread evenly between the two points; radial with an angle | base point, then "point at the last copy; type the total count"; linear and radial | the count and distance beside the cursor |
| Scale | origin, reference, new point, or a typed factor; Copy | the same | none |
| Trim, Extend, Offset, Fillet, Chamfer, Stretch | present; Offset previews under the pointer | present | Offset preview |
| Split, Break, Join, Explode, Lengthen, Align | disabled buttons, Align not wired to the canvas | Join, Lengthen, Split and Align work | none (ahead here) |
| Axis lock while moving | X and Y keys; Shift for 45 degree steps | X, Y and Free in the options panel | none |
| Selection box | left to right window (blue, solid), right to left crossing (green, dashed); Shift or Ctrl toggles | the same boxes; Shift adds for some kinds only | Shift or Ctrl toggling for every kind |
| Grips | square grips with axis arrows; dragging an arrow locks the axis | grips per element kind, no arrows | axis arrows |
| Right-click | ends a tool; in Select a menu with Repeat, Delete, Select All, Zoom to Fit | context commands exist | right-click to end a tool, Repeat with Enter or Space |
| Gridline label | double-click a bubble opens a text box on it; double-click a bare end adds a bubble | Name in the properties; a click on the head of the selected grid asks for the name (added on the date above) | a text box on the bubble itself |
| Gridline numbering | horizontal lines get letters, vertical ones numbers, skipping labels in use; a copy gets the next free label | by count of lines in that direction; a copy by pattern | "next free label" when drawing and copying |
| Gridline extension | 1000, 1500, 2000, 2500, 3000 mm at 1:100, 1:50, 1:20, 1:10, 1:5; nearest scale otherwise; bubble at the end of the extension | the same table, settable per scale (added on the date above) | none |
| Bubble and annotation size | paper millimetres times the drawing scale, so they grow and shrink with zoom and change at once with the scale (bubble 3 mm radius, text 3.15 mm) | grid heads, section and elevation marks, tags and labels are a fixed number of screen pixels; dimensions already follow the scale | everything but dimensions |
| Automatic grid dimensions | regenerated after every change to the gridlines | made on request (exterior dimensions, grid dimensions) | regenerate on change (to decide) |

## Not worth copying

- A typed angle of 90 points down on screen there, while the panel shows angles
  counter-clockwise. Here a typed angle stays counter-clockwise.
- The polar tolerance there is in model units and does not follow the zoom. Here it stays in
  screen pixels.
- Ortho there still allows 45 degree diagonals for lines. Here ortho stays horizontal and
  vertical.
- Array there ignores its Spacing field and divides a radial angle by the count rather than
  the count less one.

## Open questions

- Should Rotate and Mirror stay active after an action, as there, or return to Select as
  here? The reference is inconsistent itself (Move and Array return, the others stay).
- Should the grid dimensions regenerate by themselves?
- One click or two on a grid head to rename: one click would block two-letter commands on a
  grid selected by its head.

## Verdict

Bring the canvas over in this order, each step usable on its own:

1. Annotation in paper millimetres on screen: grid heads with their figure, handles and pick
   zone first, then section and elevation marks and tags.
2. The panel beside the cursor, for the tools that already take typed values (line, wall,
   grid, move, copy, rotate, array, scale, rectangle), with Tab and Enter as in the
   reference and F12 to switch it off.
3. Options shared by the modify tools: Multiple for Copy, right-click to end a tool, Enter
   or Space to repeat the last one; Array with its count and distance beside the cursor.
4. Snap: centre and tangent, snaps on arcs, a settable aperture and polar step.
5. Selection: Shift or Ctrl toggling for every kind, grips with axis arrows.
6. Gridlines: the next free label when drawing and copying, a text box on the bubble.

Provisional: the comparison rests on reading both code bases. What is missing as evidence is
the reference observed while running, for the timing and feel of the panel and of tracking;
that needs a session at the running application.
