# Section and elevation projection

**Question:** how do sections and elevations draw what lies beyond their plane (the
visible edges of walls, floors, roofs, windows and doors, stairs, building systems and
components), with hidden lines removed well enough for a Dutch working drawing, from
the geometry the application already has?

**Status:** first step built (drawing quality plan, item 15), 6 November 2026.

## Approach

**Source geometry.** The projection works on triangle meshes in model coordinates, the
ones the 3D view already makes, so nothing is tessellated a second way:

- the evaluated walls and plates (`append bim mesh of` on each evaluation geometry);
- the scene meshes of the element modules (stairs, railings, building systems, linear
  members, placed components, face sketches, free meshes, opening details), less those
  that hold lines (reinforcement and masonry lines);
- a frame (kozijn) and infill for every door and window
  (`architectural/openings/bim_opening_view.dl`). The wall's solid only has the rough
  opening cut out, and the opening type has no 3D frame. The frame is the type's frame
  width wide and 114 mm deep, on the wall's line, as the plan symbol draws it. The infill
  (glass or leaf) is one sheet on the frame's middle. It hides what lies behind it and
  draws no edge of its own. A window system hosted in the opening and shown, or an
  opening detail, replaces both.

Category rules, phases and HH-hidden elements of the view apply per mesh.

**Edges drawn** (`views/drawings/bim_projection.dl`). The corners of each mesh are welded
by place: a key on a grid of 1/2^20 of the mesh's extent, sorted. Each triangle side is
keyed by its welded ends and sorted, so the faces that share a side lie next to each
other. A side is drawn when:

- it is an open border (one face), or more than two faces meet on it;
- or two faces meet on it, at least one faces the viewer, and either:
  - the faces fold: more than 60 degrees between them, or more than one degree with
    different normals stored at the shared corners (a smoothly shaded curve stores the
    same normal on both sides and draws no line between its facets);
  - or one face looks toward the viewer and the other does not (a curve's outline).

Coplanar triangles of one face draw nothing between them.

**Hidden-line removal.** Every triangle is cut to the depths from 0 (the plane) to the
view depth and kept as an occluder in drawing coordinates. A grid indexes the
occluders: about one cell per triangle, at most 128 by 128. Each drawn edge is then:

1. cut to the view's width (the section line from 0 to its run) and depth;
2. cut against every occluder whose box its box touches and whose nearest corner is in
   front of the edge's farthest point. Within a triangle's outline (widened by 0.1 µm, so
   that the triangles of one face leave no gap), the part of the edge lying more than
   0.1 mm behind the triangle's plane is taken out. The edge depth and the plane depth
   are both linear along the edge, so this is exact;
3. cut against the view's cut polygons, which stand on the plane at depth 0 in front of
   everything beyond. A piece is taken out when its middle lies inside a cut (even-odd
   over the element's loops) or on a cut's outline, which the cut pen draws already.

The pieces that remain and are at least 0.1 mm long are the visible edges. This is not a
painter's approximation: for a polyhedral scene it is exact up to the tolerances above.
Its cost is the number of edges times the occluders in their cells.

**Views.**

- *Sections:* the line runs from 0 to its run, with the view record's new `depth` (0: no
  limit). The live section panel and the section on a sheet draw the edges in the
  visible pen, under the cut fills. The panel keeps them until the model's revision, the
  evaluation's generation, the section's view or line, or the scene's mesh count change.
- *Elevations* (model views with `detail` 1 to 4): the line is a section line a metre
  outside the model's plan extent on the side shown. It runs the full width plus a metre
  past each end and looks inward (`the bim elevation line of`). On a sheet the elevation
  draws:
  - its edges above the ground line;
  - the ground line itself, in the cut pen at peil (the storey at 0), since the model
    has no maaiveld;
  - its levels as short dashed lines right of the building, with the peil mark and the
    name and height;
  - its title, its extent (`the bim extent of elevation`) and its share in the title
    block's scale text.

  Section and elevation extents now also reach a pitched plate's highest corner.

## Measured

`ui/shell/tests/section_projection` (see its expected output):

- In a section, a window in the back wall shows its rough opening and its frame's inside,
  in place to the millimetre.
- A low wall in front hides exactly the stretch of the sill, jamb and wall foot behind
  it.
- The wall behind the section line draws nothing.
- A view depth short of the back wall leaves it out.
- Hiding the windows' category removes the frame but not the opening.
- In the south elevation of a two-storey box, both storeys' south walls and the window
  are drawn, and nothing of the north walls.
- On a sheet that elevation is 100 by 80 mm at 1:100, black, with a ground line and both
  levels named.

## Not done

- Plans: nothing below the cut drawn thin, nothing above it dashed.
- Hidden edges drawn dashed in sections.
- A section clipped to its crop on the sheet.
- A view flip field.
- Section-only pens per category: the per-category projection line weight and colour
  overrides (`bim projection weight field`) are not read yet.
- Sills (vensterbank, waterslag) and door leaf details.
- A real maaiveld height.
- Elements cut by the section that the evaluation does not hold (stairs, components,
  systems) leave their cut open. Their far faces look away, so little shows through, but
  their cut is not filled.
- The live section recomputes on every frame of a drag, since the evaluation changes.

Large models were not measured.

## Verdict

Keep the exact triangle-based hidden-line removal over a painter's or raster method. It
reuses the 3D view's meshes, gives exact vector lines for PDF and SVG, and is fast
enough for a house on a sheet. Measure it on the FZK-Haus before using it in plans
(below and above the cut) and for dashed hidden lines. Those are the next steps of item
15.
