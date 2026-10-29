# Visible ceiling and interchangeable panel demonstration

**Decision question:** can the existing native application show the ceiling/panel replacement
workflow before the new generic evaluator and catalogue placement UI are integrated?

**Measured on Linux, 29 October 2026:** yes. A separate synthetic model was created in the
native application, displayed in its 3D workspace, saved as IFCXB and reopened successfully.
This uses the existing application binary from source `2b58b0f`, not an application build
containing the new catalogue or generic evaluator. It is a visible baseline demonstration,
not a claim that the new generator UI has been completed.

## Model and interaction

- One ceiling system, 4800 × 3000 mm, level at 2600 mm, 600 × 600 nominal modules.
- Existing `Systeemplafond 600x600` recipe; 24 × 38 mm generic members and mineral-fibre
  infills. Profile geometry is a generic approximation, not a complete manufacturer's T-grid.
- One infill, panel 13 / bay 3 / row 3, replaced by a separately defined planar type named
  `LED-paneel 600x600 - demonstratie`, with an illustrative 40 mm layer.
- Clear infill dimensions reported by the application: 576 × 576 mm. The name describes a
  nominal module; actual luminaire edge/support dimensions still require product input.
- The replacement changes the selected cell only and retains the parent system identity.
- Native Undo restores the mineral-fibre infill; Redo restores the LED demo type.
- Saving and opening the IFCXB in a fresh process retains the same system and panel override.

The actions use the application's native system/type/selection/property APIs and ordinary
transactions. Python only orchestrates those commands and records responses; it implements
no model geometry. The file, screenshots and response reports remain local build artifacts.
The main visible demo window is left open, and the separate original example model is retained.

## Reproduce through the interface

1. Create an empty project and place the existing 600 × 600 ceiling building-system type.
2. In the type manager, create a ceiling/planar type for the replacement demo infill; set its
   name, material label and illustrative thickness.
3. Select an individual ceiling panel; use its panel-type property to choose the replacement.
4. Verify Undo and Redo, then save and reopen the model.

This demonstrates geometric substitution. It does not provide a real luminaire product,
photometric simulation, electrical design, tested fixture support/hangers, generic semantic
classification, arbitrary contours or activation of all 183 catalogue presets. Those remain
explicit generator/integration work. Next delivery should pair backend changes with a visible
native example and exact reproduction steps, so progress is inspectable in the application.

One visible integration concern remains: selection overlays/grips for a flat system appear
near the carrier's origin rather than on the selected flat panel. This needs coordination
with the editor/view owner; the demo does not change shared UI code to mask it.
