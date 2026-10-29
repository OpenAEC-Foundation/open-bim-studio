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

## Reproduce from native source

`pattern/common/bim_ceiling_demo.dl` builds the same bounded example through existing
system and planar-type APIs. It resolves the ceiling recipe by name, refuses a missing
storey before changing the model and replaces only zero-based cell 12. The caller owns
the transaction. It intentionally remains an example adapter, not the generic evaluator.

Run `bash build.sh test ceiling_demo` with the configured native toolchain. The fixture
creates an ordinary editor document, exercises replacement transactions, saves
`build/ceiling-led-reproducible.ifcx` and opens that file into a second native editor.
The generated file can also be opened in the desktop application:

```sh
./build/open-bim-studio /absolute/path/to/build/ceiling-led-reproducible.ifcx
```

The seven assertions cover atomic refusal, one host, horizontal extent/elevation,
one LED type among forty cell assignments, Undo, Redo and persisted host/replacement
identity. These checks do not establish luminaire engineering or catalogue placement.

### Measured source reproduction

Implementation `2790f0a0f4c44099ec6f20b2bbe61150c333e208` passes all seven assertions
locally with exact expected output and an empty compiler diagnostic file. Native compiler
SHA-256: `e1127c229b1b934d59b5950489fba0ef11255bc18a6b33ce51862bce21baf3af`.
The single-test command, including the worktree's kernel archive build, took **23:00.07**,
peak RSS **2,539,588 KiB**. No second compiler ran on this machine.

Generated IFCX SHA-256:
`85d00fc010b46d453f13f827e9d5ffa31be70f80046614243c607382c44b6240`.
Test binary SHA-256:
`d4438881fa511d8c7fc5bbc41165fdb6e00f8fbf8590ab673c71fe253b41e9e1`.

An independent desktop process using the existing `2b58b0f` application binary opens
the generated file with one system and the LED material in cell 13 (part code 2012).
The parser normalizes the illustrative type name to **Led diffuser 40**; the initial
external verifier expected the unnormalized authoring name and was corrected to check
the selected cell, actual material and normalized name. No model/library change was
needed. The verification process closes only its own temporary window; existing user
windows are retained. This is local source-test plus desktop-open evidence, not an
independent CI run of this new fixture.

## Corner selection follow-up

Existing boundary sketch code already has endpoint selection and **G** movement,
separate edge selection, preview cancellation and incident-edge joining. The existing
`ui/editor/tests/boundary_move.dl` exercises this for floor/roof/wall hosts; those tests
were inspected, not newly rerun as part of the ceiling fixture.

The requested general vertex/edge/face selection for Building Systems, including derived
features and stable identity in plan/3D, is tracked in
[issue #30](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/30) and contract
section 7.1. Shared editor/picking changes belong to the editor owner. The existing endpoint
path should be reused; an outline-only overlay does not complete that requirement.

This demonstrates geometric substitution. It does not provide a real luminaire product,
photometric simulation, electrical design, tested fixture support/hangers, generic semantic
classification, arbitrary contours or activation of all 183 catalogue presets. Those remain
explicit generator/integration work. Next delivery should pair backend changes with a visible
native example and exact reproduction steps, so progress is inspectable in the application.

One visible integration concern remains: selection overlays/grips for a flat system appear
near the carrier's origin rather than on the selected flat panel. This needs coordination
with the editor/view owner; the demo does not change shared UI code to mask it.
