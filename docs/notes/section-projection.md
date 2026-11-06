# Section and elevation projection

**Question:** how do sections and elevations draw what lies beyond their plane (the
visible edges of walls, floors, roofs, windows and doors, stairs, building systems and
components), with hidden lines removed well enough for a Dutch working drawing, from
the geometry the application already has?

**Status:** sections, elevations and plans built (drawing quality plan, item 15), 6 November
2026.

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
- *Plans* (`ui/panels/bim_plan_projection.dl`): the same projection on the plan's
  horizontal plane at the cut, twice. Looking down, to the storey's floor (0.1 mm short
  of it, so that what lies on the floor is the floor's) or to the plan view's `depth`
  when it has one, the edges are drawn thin in the visible pen. Looking up, to the next
  level (0.1 mm past it, so that a roof or the floor above resting on that level is seen)
  or else the storey's own top (elevation and height), the edges are dashed in the hidden
  pen, with the dashes of a roof's edges. Looking up is the same plane with its y axis
  turned over (the depth axis is y × x); the cut polygons are mirrored for it and the
  edges turned back. Meshes that reach neither depth are left out before the projection
  welds them. What the plan already draws is not drawn twice:
  - the cut outlines hide what lies under or on them, as in a section;
  - each opening of the storey whose symbol is drawn (one reaching above the cut) hides
    its rough opening across the wall and its sills, which the symbol draws;
  - the storey's slabs and roofs (`record bim slab edges`), stairs, railings, curtain
    walls, linear elements, component instances and openings only hide; their own
    symbols draw them. Walls, free meshes, building systems and every element of
    another storey are drawn.

  `record bim plan of` records both under the hatched cut, for the live plan and a sheet's
  viewport alike. The live plan keeps the edges (`bim plan projection record`) until the
  model's revision, the evaluation's generation, the storey, the plan view, its cut
  height or depth, its rules or hidden elements, or the scene's meshes (count and builds)
  change; a sheet works them out each time it records the viewport, which happens when
  the model changes.

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

`ui/shell/tests/plan_projection` (see its expected output): in the ground floor plan (cut
at 1.2 m, a roof level at 3 m) of four walls with a window, a knee wall 0.8 m high and a
flat roof on the roof level overhanging 0.4 m:

- below the cut the knee wall's top is drawn (its faces 2 m, its ends 0.2 m), nothing of
  the walls cut normally, and nothing in the window's rough opening;
- above the cut the roof's overhang is drawn whole on all four sides, and nothing else;
- on paper the edges below are one stroke each in the 0.25 mm pen and those above are
  dashed in the 0.18 mm pen, black; a sheet's viewport and the live plan record the same
  batches;
- the edges are kept until the model changes, then worked out again.

`tools/probes/plan_projection_timing` (built at -O0, measured on this computer, 6 November
2026), the ground floor's plan of a generated tower: one storey of 312 walls, 48 windows and
a slab, 75 ms to work out (the plan's cut 1 ms, the evaluation 17 ms); five storeys of 420
walls, 120 windows and 5 slabs, 45 ms (meshes out of both depths are left out before
welding); kept, 0 ms. Both plans draw no edge (every wall is cut, every opening has a
symbol), so this measures the weighing and hiding, not a plan full of edges.

## Not done

- Plans: per-category projection pens and colours; halftone; the opening frames of an
  opening wholly below the cut (no symbol) are not drawn; a sloping roof on the next
  level is seen only up to that level (its eaves, not its verges); the storey's own
  slab and roof edges are still `record bim slab edges`' outline, not the projection's;
  imported elements keep their own plan lines; a component's folded plan lines are drawn
  without hidden-line removal.
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

Sections and elevations were not measured on a large model; plans only on generated
towers, not on the FZK-Haus.

## Verdict

Keep the exact triangle-based hidden-line removal over a painter's or raster method. It
reuses the 3D view's meshes, gives exact vector lines for PDF and SVG, and is fast
enough for a house on a sheet and, kept between frames, for a plan of a few hundred
elements (tens of milliseconds to work out at -O0). Plans now use it below and above the
cut. Measure it on the FZK-Haus before using it for dashed hidden lines in sections; that
and the per-category pens are the next steps of item 15.
