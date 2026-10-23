# Roof and editing work in progress

This branch is not part of the Linux 0.1.1 preview release.

Current follow-ups (23 October):
- Curved-wall plan hatch: preserve duplicate clipping corners before removing
  collinear vertices. `plan_ring` passed three checks; the native plan view
  no longer shows missing triangular pieces in the layered curved-wall fixture.
- Sketch toolbar Line/L: route unmodified keys to the active boundary sketch
  before global view shortcuts. The L key and a real toolbar click were verified
  in the native window: drawing asks for the next point without opening Visibility.
- Three-point arc wall: command 2384, start/end/through point, preview and one
  native wall/undo transaction. Currently centreline placement and at most a
  semicircle. `arc_wall_editor` passed five checks; API placement and undo were
  also verified in the native app. Elliptical wall
  placement remains to implement; boundary ellipse support is not that feature.
- IFC 4.3 ADD2: command 2383 and separate ribbon export, schema-aware point-list
  serialization, preserving the IFC4 entry point. `ifc43` writes both fixtures;
  `tests/verify_ifc43.py` validates the files with IfcOpenShell without compiling.
  Independent validation found duplicate type relationships in the old exporter.
  They are now grouped per wall type. Plates export their evaluated geometry
  (height, pitch, typed thickness and openings) and native planar IFC role.
  The validation fixture checks a pitched floor with an opening against explicit
  volume/height values. The final R9 native output passed independent IFC4.3
  schema/EXPRESS, identifiers, relationships and geometry validation against
  the IFC4 reference, including the explicit pitched-floor volume and heights.
- The R6 app build passed its IFC43, arc-wall and ring-cleaning tests without
  diagnostics (14:38, peak 8,948,852 kB RSS). Independent schema validation is
  the gate for publishing the exporter.

- Dimension labels: rotated canvas glyphs and PDF/SVG output. The small bundle
  `dimension_text`, `svg`, `pdf_text_encoding` passed. The GUI compiles; visual
  checks of rotated dimension labels remain open.
- Trim: beam candidate selection, axis endpoint updates and hover outlines are
  drafted. Full editor tests and visible/ray-hit consistency remain to be checked.
- Vertical openings: command 2382, tool 28, rectangular preview and the existing
  host opening kernel are connected. Two API clicks create a floor opening
  immediately; undo removes it and keeps a pre-existing opening.
- Roof forms: `bim_roof_forms.dl` is an uncompiled prototype for sampled sections
  extruded or swept along plan paths. Evaluation, movement, persistence validation,
  GUI/API integration and tests are not complete. Do not expose it as finished.
- Roof grips: identified base-level coordinates in `the bim grips of`; use the
  actual roof top, slope and curved profile consistently for display and picking.
- Edit Sketch: Tab opens point/edge selection; G previews a move, Esc cancels
  that move, and Tab validates and commits the contour. Endpoint, midpoint,
  nearest and local alignment snapping use the host plane, including sloped
  roofs. The boundary core run passed 40 checks in the full app build. A live
  MCP-driven floor-point move kept the model unchanged during preview, committed
  a 500 mm displacement with Enter/Tab, and restored the outline with undo.
  Ellipse segments and persistence are a draft, not an exposed drawing tool yet.
- Local gizmo: object-origin frames and local-axis dragging are implemented in
  source. Frame and roof-height regression checks passed in `boundary_move`.
  In the full app, a mouse drag along a wall's local X handle moved both ends
  630 mm in X with no Y displacement; undo restored the original wall. XYZ and
  the local origin label were visually checked. Sloped-roof GUI dragging still
  needs its own visual check.
- Section-box materials: scene meshes carry material names; native layered walls
  and plates supply individual cut solids even in coarse display. Cut fills,
  diagonal/crossed hatching and insulation zigzags use the existing drawing
  standard patterns. Dutch material names are recognised. Pattern strokes are
  clipped against cap triangles, preserving holes. Camera movement does not
  regenerate the cap cache. Mesh reuse also compares material names, since two
  materials can share a display colour but require different hatches.
  Imported meshes without material metadata retain a generic fallback.
  `section_caps` passed all 12 checks alongside `boundary_move` (40 checks),
  without compiler diagnostics in the full app build. In a native X11 window,
  the wall cut shows its separate material bands and leaves the opening empty.
  Changing NEN to DIN updates cap fills and strokes immediately; undo restores
  the previous appearance. Layer generation is now isolated in
  `bim_section_materials.dl` for headless wall/floor opening and cache tests.
  The additional floor test exposed missing settings in the evaluation snapshot:
  layer reconstruction lost through-openings. Evaluation now copies settings,
  checks settings-only edits and undo/reopen journals, and includes layer
  materials and offsets in geometry signatures even when total thickness stays
  unchanged. All 14 section-material checks passed. In the native window, the
  floor cut stays open in coarse and fine display, including after adding
  another opening and undoing it.
  Reproducible GUI examples: `examples/section-materials.bim` (wall materials
  and a window) and `examples/section-floor-opening.bim` (a box cut through a
  layered floor opening). The latter must retain an empty notch across all
  cut layers, including after switching between coarse and fine display.
- Graph Explorer: investigate real relation data, navigation and node selection.

The final R9 development build passed `ifc43`, `evaluate` and
`section_materials` without diagnostics in 14:13, peaking at 8,894,524 kB RSS.
The local preview is `build/sketch-ifc43-20261023/run.sh`; verification evidence
is stored beside it. It is an unoptimised Linux development binary, not a release certification.
Windows validation, Sketch Trim, ellipse drawing UI and roof forms remain open.

Keep private project data outside the public repository. Preserve the running
user project. Do not include unverified branch changes in a release.
