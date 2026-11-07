# Section and elevation projection

**Question:** how do sections and elevations draw what lies beyond their plane (the
visible edges of walls, floors, roofs, windows and doors, stairs, building systems and
components), with hidden lines removed well enough for a Dutch working drawing, from
the geometry the application already has?

**Status:** sections, elevations and plans built (drawing quality plan, item 15), 6 November
2026. The plans' shared code is compiled and tested headless; the live plan's wiring in
`ui/shell/main.dl` (its cache and call) has not been compiled yet, as the application was not
built on the branch. Flush edges (a facade face triangulated with T-vertices, and walls of
one finish stacked flush on two storeys) draw no false joint since 6 November 2026
(`ui/shell/tests/projection_flush_joints`).

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

**Flush edges.** An edge is not drawn where, seen in the view, the faces on both sides of
it look toward the viewer and lie in one plane (within 0.1 mm, and a quarter of a degree
between their normals). The rule, decided for item 15 on 6 November 2026:

- Only a *one-sided* edge can be flush: one with exactly one face beside it looking toward
  the viewer, that is an open border, or an outline or fold against faces turned away (a
  wall's front face against its top). It is flush over the stretch where another one-sided
  edge on the same line has a face looking the same way, in the same plane, on the other
  side of the line.
- That other face must be of the *same mesh*, or of a mesh showing the *same finish*. The
  same mesh covers T-vertices in a face's triangulation (a triangle side from one window's
  sill corner to the next window's, met by two triangles on the other side), slivers whose
  corners lie on one line (now left out of the side keys), and a frame's touching rails
  and posts. The same finish covers two elements meeting flush, such as the walls of two
  storeys stacked on one outer face.
- A projection mesh names its faces' finishes (`finishes`, `faceFinishes`). A section or
  elevation (`the bim projection meshes of`) gives a plate's faces its material, and a
  wall's faces toward its exterior its first layer's material, those toward its interior
  its last layer's (a face counts as toward a side when its normal is within 45 degrees
  of the side's horizontal normal, radial on a curved wall), and its ends, top, foot and
  reveals its whole build-up. So a brick outer leaf stacked on a brick outer leaf meets
  flush whatever the inner leaves are; brick under render keeps its joint, as does any
  mesh without finishes (stairs, components, systems, frames against walls).
- An outline against the background, a true fold and a reveal have no coplanar face
  beyond them, so they stay. Two faces of one mesh meeting on a side with more faces (two
  touching solids) draw nothing there when the only two faces toward the viewer are
  coplanar.

The one-sided edges are hashed by their line in the drawing: its angle (bins of 0.1 mrad,
the angle first turned by an odd 0.414 rad so that the two ends of the angle range fall on
no usual direction) and its offset from the origin (bins of 1 mm). Each edge looks up the
nine bins around its own (and, near either end of the angle range, those at the other end
with the offset turned over), sorted keys and a binary search, so the search costs
O(n log n) for n edges.

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
  - each opening of the storey whose symbol is drawn (one reaching above the cut, its
    category shown, its phase not hidden, its wall not hidden) hides its rough opening
    across the wall and its sills, which the symbol draws; along a curved wall that
    rectangle reaches further across by as much as the inner face falls away from the
    tangent at the opening's ends;
  - every other element of the storey but its walls only hides: slabs and roofs
    (`record bim slab edges`), stairs, railings, curtain walls, linear elements,
    component instances, openings, masses and free meshes (`draw bim sketches of`) are
    drawn by the plan's own symbols. The storey's walls and every element of another
    storey are drawn.

  `record bim plan of` records both under the hatched cut, for the live plan and a sheet's
  viewport alike. The live plan keeps the edges (`bim plan projection record`) until the
  model's revision, the evaluation's generation, the storey, the plan view, its cut
  height or depth, its rules or hidden elements, or a fingerprint of the scene's meshes
  (their elements, corner counts and first and last corners; a scene mesh carries no
  build serial) change; a sheet works them out each time it records the viewport, which
  happens when the model changes. The record also keeps each evaluated element's
  triangles with its build serial and signature, so that a build after a change (a frame
  of a drag) tessellates only the elements built again. A plan's view depth is typed as
  the plan view's View depth (property 12840, as for sections).

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

Since flush edges are left out, the frame of the window in that section and elevation no
longer draws the butt joints of its posts and rails (four short edges each, 50 mm long, in
the frame's front face), and the posts' inner edges stop at the rails: the section's window
draws 4 edges instead of 7, the elevation's 4 instead of 8. Every check of the test passes
as before.

`ui/shell/tests/projection_flush_joints` (see its expected output), the south elevation of
a house of 320 mm cavity walls (brick, insulation, sand-lime) with an interior wall
meeting the south wall at a T, and in the south wall, as on the FZK-Haus, a window 2000 by
1200 on an 800 sill, a window 1000 by 1000 on the same sill, a door and a window on a 950
sill:

- *Reproduced first, with the projection as it was:* the fast wall's outer face was
  triangulated with a T-vertex. A triangle below the first two windows has a side from
  the first window's sill corner to the second's (drawing x 1250 to 3750 at 800). The
  triangles above the sill line meet it in two pieces, the first window's sill and the
  stretch between the windows. That side was taken as an open border and drew a line 400
  mm long between the windows at sill height. The same openings in a wall of one 200 mm
  layer, or in that wall cut to a gable contour (the boolean path), were triangulated
  without it, so the T-vertex depends on the face's exact corners.
- Now the stretch between the windows draws nothing, at sill or head height, and nor do
  the stretches between the small window and the door and between the door and the last
  window. The sills, heads and jambs, the facade's foot and its top are drawn whole. The
  rest of the old border, along the first window's sill, is still drawn, on top of the
  sill's own edge.
- A first floor of the same walls stacked flush draws no joint at 3 m. Nor does one with
  the same brick outside and a timber inner leaf. One rendered outside keeps the joint
  over the facade's whole width (8.32 m).

`ui/shell/tests/plan_projection` (see its expected output): in the ground floor plan (cut
at 1.2 m, a roof level at 3 m) of four walls with a window, a knee wall 0.8 m high and a
flat roof on the roof level overhanging 0.4 m:

- below the cut the knee wall's top is drawn (its faces 2 m, its ends 0.2 m), nothing of
  the walls cut normally, nothing in the window's rough opening, and nothing of a raised
  floor and a free mesh on the same storey (the plan's own symbols draw them);
- above the cut the roof's overhang is drawn whole on all four sides, and nothing else;
- on paper the edges below are one stroke each in the 0.25 mm pen and those above are
  dashed in the 0.18 mm pen, black; a sheet's viewport and a live plan working its own
  edges out record the same batches; on screen they are grey;
- a plan view depth of 0.3 m leaves the knee wall (0.4 m below the cut) out, 0.5 m sees it;
- the edges are kept until what they show changes, then worked out again, tessellating
  only the elements built again (one, after the knee wall is raised).

`tools/probes/plan_projection_timing` (built at -O0, measured on this computer, 6 November
2026), the ground floor's plan of a generated tower:

| Model | No edge drawn | Every third wall lowered below the cut | Again, every mesh kept | Kept |
|---|---|---|---|---|
| 1 storey, 312 walls, 48 windows, 1 slab | 74 ms | 72 ms (190 edges below) | 70 ms | 0 ms |
| 5 storeys, 420 walls, 120 windows, 5 slabs | 45 ms | 22 ms (46 below, 16 above) | 22 ms | 0 ms |

(The plan's cut takes 1 ms, the evaluation 17 to 25 ms.) Keeping the meshes saves little:
for walls, tessellating is cheap and the welding and hiding is the cost, so a frame of a
wall drag pays nearly the whole time. Not measured at -O2 nor on the FZK-Haus.

With flush edges (the same probe, -O0, this computer, 7 November 2026, other compilers
running beside it) the plans took 81, 76 and 74 ms on one storey and 47, 24 and 23 ms on
five, against 74, 72, 70 and 45, 22, 22 before: within 10 %, part of it the machine's
load. The probe now also projects the south elevation of the whole tower, every
evaluated wall and slab as one mesh of one finish. A throwaway build of the probe that
also ran the projection as it was, on the same meshes in the same program, measured:

| Model | Elevation, flush edges | Edges | Before | Edges |
|---|---|---|---|---|
| 1 storey, 312 walls, 48 windows, 1 slab | 57 ms | 99 | 47 ms | 112 |
| 5 storeys, 420 walls, 120 windows, 5 slabs | 65 ms | 177 | 51 ms | 302 |

So the line hash and the one-sided edges' bookkeeping cost 10 to 14 ms at -O0 on 300
to 420 meshes, about a quarter of the projection. The edges left out (13 on one storey, 125 on
five) are joints between flush faces of different elements, all of one finish in the
probe, the stacked storeys' facades among them; which joint is which was not checked.

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

- Plans: the live plan's wiring in `ui/shell/main.dl` is not compiled yet; a drag works
  the edges out again every frame.
- Flush edges: plans give their meshes no finishes, so in a plan only faces of one mesh
  meet flush (two joined wall tops of one type still draw their joint below the cut).
  Elements other than walls and plates (stairs, components, systems, opening frames) have
  no finish and keep every joint with another element. A wall's faces are told apart by
  their normals, not by the layer they bound: a face leaning more than about 45 degrees
  off a side counts as an end. Where the rest of a T-vertex border runs along a real
  outline, both are drawn, one on the other. Measured only on generated towers and the
  test house, not on the FZK-Haus itself.

Sections and elevations were not measured on a large model; plans only on generated
towers, not on the FZK-Haus.

## Verdict

Keep the exact triangle-based hidden-line removal over a painter's or raster method. It
reuses the 3D view's meshes and gives exact vector lines for PDF and SVG. Plans now use it
below and above the cut. Provisionally it is fast enough, kept between frames, for a plan
of a few hundred elements: measured at -O0 on generated towers, 20 to 75 ms to work out,
with up to 190 edges. Leaving out flush edges (same plane, faces toward the viewer on both
sides, one mesh or one finish) is kept: it removes the false joints of T-vertex
triangulations and of stacked storeys for about a quarter more time. What is missing to settle it: a measurement on the FZK-Haus and at
-O2, and the cost of a frame of a drag in the running application. Those, and the
per-category pens, are the next steps of item 15.
