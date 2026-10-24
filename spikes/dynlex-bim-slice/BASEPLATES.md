# Steel column base plates

Select a vertical steel column and choose **Connections → Column base → Base plate**.
The node owns the lower column end, including columns drawn downwards. Move or
rotate the column to regenerate the connection. Select the connection to edit
its plate dimensions and anchor grid in Properties; edits participate in undo.

The initial modelling recipe uses a 20 mm plate, extending 100 mm beyond each
side of the column envelope, and four 20 mm straight anchors in 24 mm nominal
holes. The grid lies 50 mm inside the plate edges; rods start 40 mm above the
column foot and extend 350 mm downwards. These are editable modelling defaults,
not a designed or approved connection. The plate top remains at the column foot
when thickness changes.

The recipe rejects duplicate lower-end ownership, non-steel or inclined hosts,
plates smaller than the section, anchor holes outside the plate, overlapping
holes, anchor heads intersecting the column envelope, and rods that do not reach
below the plate. These are geometry checks, not structural design checks.

The first version reuses the existing steel profile library and connection
persistence: Complex style 2 has one member, a plate and an anchor group (kind 3).
Existing multi-member connections retain their old interpretation. Older app
versions may reject files containing the new recipe.

## Current limits

- Anchor holes are retained as parameters; the plate display is solid and is not
  yet perforated. Anchors deliberately do not generate cutters in the column.
- Rods and heads are simplified circular solids; threads, washers, welds,
  stiffeners, grout and concrete support geometry are not generated.
- Only vertical columns and a centred rectangular plate/grid are supported.
  Anchor offsets are local to the column's base frame.
- No resistance, concrete breakout, weld, edge-distance or code-compliance
  calculation is performed. Host/type changes can invalidate a connection; its
  geometry is then withheld until the parameters are corrected.

Headless tests cover lower-end placement, rotation, level elevation, host
movement, dimensions, end ownership, native text round trip and undo. The
viewport and tab-drag changes have separate tests. Full app and visual checks
must be recorded separately from these tests.

## Related development on this branch

- 3D overlays now receive their pane's scissor without changing pixel projection.
  Selection-box input is bounded to the pane as well.
- View tabs can be reordered by dragging, or dropped into the drawing area to
  activate the existing tiled workspace. Floating tool panels are not implemented.
- Reinforcement has an explicit optional diameter-display button and a bending
  schedule tab. HTML/TSV reports use the generated model paths; shape sketches
  and envelope dimensions are for review, not verified fabrication dimensions.
- Twelve window-frame layouts extend the library. They use nominal rectangular
  profiles; operating sashes, hardware and profile rebates are not yet modelled.
- Opening details generate jambs, a head and a sill for straight upright walls.
  The current integration provides 3D geometry and persisted parameters; complete
  drawing/export integration and junction checks remain pending.
- The native window icon and Linux launcher identity are wired in source. A new
  app build and an interactive taskbar check are still required.

A large steel stress model with difficult connections remains to be generated
and measured after the functional checks. No performance result is claimed yet.
