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
- Edit Sketch: existing boundary mode already uses Tab to enter/finish. Add an
  explicit contextual label and finish/cancel controls without changing that rule.
- Graph Explorer: investigate real relation data, navigation and node selection.

Keep private project data outside the public repository. Preserve the running
1357 study. Do not include unverified branch changes in a release.
