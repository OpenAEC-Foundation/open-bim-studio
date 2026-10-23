# Roof and editing work in progress

This branch is not part of the Linux 0.1.1 preview release.

- Dimension labels: rotated canvas glyphs and PDF/SVG output. The small bundle
  `dimension_text`, `svg`, `pdf_text_encoding` passed. Full GUI build pending.
- Trim: beam candidate selection, axis endpoint updates and hover outlines are
  drafted. Full editor tests and visible/ray-hit consistency remain to be checked.
- Vertical openings: command 2382, tool 28, rectangular preview and the existing
  host opening kernel are connected in source; API/MCP entry points remain open.
- Roof forms: `bim_roof_forms.dl` is an uncompiled prototype for sampled sections
  extruded or swept along plan paths. Evaluation, movement, persistence validation,
  GUI/API integration and tests are not complete. Do not expose it as finished.
- Roof grips: identified base-level coordinates in `the bim grips of`; use the
  actual roof top, slope and curved profile consistently for display and picking.
- Edit Sketch: Tab opens point/edge selection; G previews a move, Esc cancels
  that move, and Tab validates and commits the contour. Endpoint, midpoint,
  nearest and local alignment snapping use the host plane, including sloped
  roofs. The boundary core run passed 40 checks; GUI validation remains
  open. Ellipse segments and persistence are a draft, not an exposed tool yet.
- Local gizmo: object-origin frames and local-axis dragging are implemented in
  source. Frame and roof-height regression checks passed in `boundary_move`; the
  projected GUI interaction still needs an app build and visual check.
- Section-box materials: scene meshes carry material names; native layered walls
  and plates supply individual cut solids even in coarse display. Cut fills,
  diagonal/crossed hatching and insulation zigzags use the existing drawing
  standard patterns. Dutch material names are recognised. Pattern strokes are
  clipped against cap triangles, preserving holes. Camera movement does not
  regenerate the cap cache. Mesh reuse also compares material names, since two
  materials can share a display colour but require different hatches.
  Imported meshes without material metadata retain a generic fallback.
  `section_caps` passed all 12 checks alongside `boundary_move` (40 checks),
  without compiler diagnostics. The later material-name reuse guard has static
  review only. Full GPU/app validation remains open; do not describe this as
  release-tested.
- Graph Explorer: investigate real relation data, navigation and node selection.

Keep private project data outside the public repository. Preserve the running
1357 study. Do not include unverified branch changes in a release.
