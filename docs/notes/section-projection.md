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
  coplanar and lie on either side of it; two lying over each other on one side of it
  leave it an outline.

The one-sided edges are hashed by their line in the drawing and by their depth: the
line's angle (bins of 0.1 mrad, the angle first turned by an odd 0.414 rad so that the two
ends of the angle range fall on no usual direction), its offset from the hash's origin
(bins of 1 mm), and
every depth bin of 250 mm its ends reach. An edge reaching through more than 32 depth
bins (running steeply into the depth) is keyed once, in a deep bin that every edge also
searches. The angle and depth bins are hashed together into 2^16 slots, the offset kept
below them so that neighbouring offsets follow each other. Each edge scans, for each
depth bin it reaches and the deep bin, the three angle bins around its own over three
offset bins (and, near either end of the angle range, those at the other end with the
offset turned over): sorted keys and a binary search per scan. Edges on one line in the
drawing but at different depths, such as the storey lines of every wall parallel to an
elevation, no longer meet. The cost is O(n log n) plus, for each edge, the edges that
share its line, depth bin and hash slot: those on nearly its line in space (a long facade
whose windows all sit on one sill line) and the rare hash collision. That last term is not
bounded in principle, but it no longer grows with the depth of the building.
The origin is the first corner of the first outlined mesh in the drawing, rounded to the
nearest point of a 64 m grid (`the bim flush origin of`): near the model, so that a model
far from its own origin keeps its lines apart, and fixed by the meshes rather than by the
edges, so that a projection worked out again in part keys alike (below). The first version
took the first one-sided edge's start, which a part projection would have moved. Rounded
to the nearest rather than down, a model about its origin keeps 0 when a corner crosses
it: rounded down, the plan drag test's front wall moved the origin from -64 m to 0 and
the update fell back to a whole projection.

**Flush edges in the kept projection.** A live plan updates the edges it keeps during a
drag (`update bim kept projection`, *Measured* below), and the update stays exact with
flush edges:

- An edge's flush stretches depend on the one-sided edges of other outlined meshes on its
  line. A partner takes a stretch away only where it overlaps the edge over a length
  (`take bim stretch` ignores an empty overlap, so one that only touches the edge's end
  takes nothing), within the flush tolerance of 0.1 mm across. So the partner's mesh box
  and the edge's mesh box touch within 0.1 mm, inside the box slack of 1 mm, and when a
  mesh changes, appears or goes (by its old box and its new one) every mesh whose flush
  stretches it can change is among those worked out again.
- The meshes worked out again are worked out among the meshes whose boxes touch theirs,
  as before. The outlined ones among them that name finishes now give their edges as
  flush partners without being drawn again (a draw flag per mesh in the projection), so
  each edge worked out again meets the same partners as in a whole projection; before,
  they were passed as not outlined and gave none, which would have drawn the joints a
  whole projection leaves out. A mesh without finishes can be no other mesh's partner (the
  same finish must be named on both sides), so its edges are not worked out at all when it
  is not drawn: a plan's update, whose meshes name none, costs what it did.
- The meshes are matched on their finishes and faces' finishes as well as their
  triangles, so a change of material alone is found.
- The hash is keyed around the same origin in the whole projection and in the part, so
  every pair of edges is found flush or not alike: the hash's bins are not conservative
  (two edges within the tolerance may fall more than a bin apart), so the result depends
  on the origin in near-degenerate cases. When an edit moves the origin, the update works
  the edges out whole. The scan visits the partners in the same order in both, since a
  part's meshes keep the whole's order.
- The edges per mesh are counted after the flush stretches are taken out (every piece of
  a mesh's candidate edges), so the edges a mesh keeps can be replaced per mesh even when
  another mesh took stretches of them away.

Plans still give their meshes no finishes (*Not done*), so in a plan only the faces of one
mesh meet flush and no flush status there depends on another mesh; the elevation case is
covered by `ui/shell/tests/projection_flush_joints`.

Measured with `tools/probes/plan_projection_timing` after the merge (-O0, this computer, 7
November 2026, one other compile running beside it), six drag frames each, updated against
worked out whole: one storey of 312 walls, a lowered wall 3.5 ms against 76 ms and a
full-height wall 4.0 to 4.5 ms against 76 ms; two storeys of 624 walls, a lowered wall 5.8
ms against 118 ms and a full-height wall 12 to 13 ms against 118 ms. Before plans skipped
the meshes without finishes as partners, the two-storey full-height wall took 21 to 22 ms
a frame (every mesh above the cut touches the slab worked out again, and all their edges
were worked out as partners). Against the drag's own measurement before the merge (3.4,
3.7, 5.5 and 11.7 ms; 71 and 108 ms whole) the updates cost the same within the noise; the
whole plan took 7 to 9 % more in this run, under other load, in line with the plans within
10 % that the flush edges were measured at above. The
probe's south elevation now runs after the drags have moved two walls, so its 41 ms (297
meshes, 104 edges) on one storey and 92 ms (610 meshes, 160 edges) on two are not
comparable with the 99 and 177 edges above.

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
- A section across the house at y 3 looking south cuts the interior wall and sees the
  south wall's inner face, which the interior wall meets at a T beyond the cut, with the
  openings in it. Between the openings, between the door and the T and beyond the last
  window that face draws nothing: no edge, and no sill or head line running on. The
  inner face shows the T only as split pieces of its foot line (drawing x 4655 to 4830
  and 4830 to 4840), which lie on the foot and draw nothing extra. The same test run
  against the projection before the depth hash gives the same output, so these cases
  and the two below guard the flush rule rather than show a change; whether the
  projection before flush edges drew a false line on that inner face was not checked.
- A first floor of the same walls stacked flush draws no joint at 3 m. Nor does one with
  the same brick outside and a timber inner leaf. One rendered outside keeps the joint
  over the facade's whole width (8.32 m), and so do the same walls set back 3 mm and the
  same walls turned a little (the east end 40 mm further north): they do not lie in the
  ground floor's plane.
- Kept while editing (`update bim kept projection` on the elevation's meshes, 7 November
  2026): with the same walls stacked flush, the first floor's south wall moved 3 mm back
  shows the joint (8.32 m), moved flush again loses it, given render outside without its
  triangles changing shows it, and brick again loses it. Each update works out 9 of the 17
  meshes again, the ground floor's unchanged south wall among them, and equals a fresh
  projection to the bit, its counts per mesh adding up to its edges and equal to the fresh
  projection's mesh by mesh. On three storeys of the same walls, the top storey's south
  wall moved 3 mm back works the middle storey's south wall out again but not the ground
  floor's, which only lends its edges as flush partners: the joint at 6 m appears, the one
  at 3 m stays away, and the update equals a fresh projection, edges and counts per mesh.

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

During a drag (or another continuous edit) the live plan therefore updates the edges it keeps
(`update bim kept projection`): a mesh's visible edges depend only on its own triangles, on
the occluding triangles whose boxes touch its edges' boxes and on the cut polygons whose boxes
touch them, so only the meshes changed and those whose drawing box touches the box of a mesh or
cut polygon changed, added or gone are worked out again, among the meshes and cut polygons
touching them; the rest are copied. The edges equal a whole projection to the bit
(`ui/panels/tests/plan_projection_drag` checks every frame), and the plan is worked out whole
again when the edit ends. The same probe, against a whole projection that keeps its
tessellated meshes (-O0, six frames): one storey of 312 walls, a lowered wall 3.4 ms a frame
updated against 71 ms worked out whole, a full-height wall 3.7 ms against 71 ms; two storeys,
where the next floor's slab is seen above the cut over the whole plan, 5.5 ms and 11.7 ms
against 108 ms (a full-height wall's cut changes what is seen above, so the slab is worked
out again on every frame). The application itself was not run.

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

That line hash keyed only the line in the drawing, so every one-sided edge on one storey
line met every other, at any depth: quadratic in the walls parallel to the view. With the
depth bins (the same probe, -O0, this computer, 7 November 2026, against a build of the
previous commit in the same conditions; the same edges drawn in each case):

| Model | Elevation, line and depth hash | Line hash only | Edges |
|---|---|---|---|
| 1 storey, 312 walls, 48 windows, 1 slab | 40 to 41 ms | 57 to 58 ms | 99 |
| 5 storeys, 420 walls, 120 windows, 5 slabs | 42 ms | 65 ms | 177 |
| 8 storeys, 2496 walls, 2488 meshes | 356 to 357 ms | 887 to 899 ms | 486 |
| 20 storeys, 6240 walls, 960 windows, 6244 meshes | 799 ms | 2727 ms | 1146 |

The plans of that run: 82, 78 and 75 ms on one storey, 48, 25 and 24 ms on five. On one and
five storeys the elevation now takes less than the 47 and 51 ms measured for the
projection without flush edges the day before; those were other runs under other load, so
the flush handling's remaining cost at that size is within the noise, not shown to be
zero. Without flush edges the 8- and 20-storey elevations were not measured.

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
- Sills and door leaf details on the projected frame beyond the cut. Where the section
  line cuts a door or window they are drawn by its cut detail
  (`architectural/openings/bim_opening_section.dl`, drawing quality plan item 15).
- A real maaiveld height.
- Elements cut by the section that the evaluation does not hold (stairs, components,
  systems) leave their cut open. Their far faces look away, so little shows through, but
  their cut is not filled.
- The live section recomputes on every frame of a drag, since the evaluation changes.

- Plans: the live plan's wiring in `ui/shell/main.dl` is not compiled yet; during a drag
  the live plan updates its kept edges (only the meshes near the change), while the live
  section and elevations still work theirs out whole on every frame.
- Flush edges: plans give their meshes no finishes, so in a plan only faces of one mesh
  meet flush (two joined wall tops of one type still draw their joint below the cut). Left
  so on purpose when the flush edges met the kept projection (7 November 2026): the
  finishes are given in `ui/shell/bim_view_projection.dl`, a layer above the plan's
  projection (`ui/panels/bim_plan_projection.dl`), so plans need that code moved down
  first; and whether a plan should drop the joint of two wall tops of one type below the
  cut is a drafting choice the plan tests' expected output would have to be reviewed for.
  The kept projection already handles finishes, so it needs no change for it.
  Elements other than walls and plates (stairs, components, systems, opening frames) have
  no finish and keep every joint with another element. A wall's faces are told apart by
  their normals, not by the layer they bound: a face leaning more than about 45 degrees
  off a side counts as an end. Where the rest of a T-vertex border runs along a real
  outline, both are drawn, one on the other. Measured only on generated towers and the
  test house, not on the FZK-Haus itself.

Sections were not measured on a large model, elevations and plans only on generated
towers (up to 20 storeys), not on the FZK-Haus.

## Verdict

Keep the exact triangle-based hidden-line removal over a painter's or raster method. It
reuses the 3D view's meshes and gives exact vector lines for PDF and SVG. Plans now use it
below and above the cut. Provisionally it is fast enough, kept between frames, for a plan
of a few hundred elements: measured at -O0 on generated towers, 20 to 75 ms to work out,
with up to 190 edges. Leaving out flush edges (same plane, faces toward the viewer on both
sides, one mesh or one finish) is kept: it removes the false joints of T-vertex
triangulations and of stacked storeys. Hashed by line and depth, its search grows with
the edges that share a line in space rather than a line in the drawing; a 20-storey
generated tower's elevation takes 0.8 s at -O0 with it. What is missing to settle it: a measurement on the FZK-Haus and at
-O2, and the cost of a frame of a drag in the running application. Those, and the
per-category pens, are the next steps of item 15.
