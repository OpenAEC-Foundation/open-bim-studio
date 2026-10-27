# Native canvas editing

## Outcome

The native editor provides the same usable editing workflow as the 2D reference:
choose a tool, select geometry, define a base or pivot, inspect a live preview,
enter an exact value when needed, and confirm or cancel. Home exposes the tools
directly. Native model semantics and transactional undo remain authoritative.

## Canvas

- Grid placement can snap to the exact 3D cursor; the world origin remains visible.
- Nearest snapping is disabled by default and never activates on passive hover.
- Extension tracking is available by default. Holding Shift temporarily constrains
  directions orthogonally; F8 remains the latched alternative.
- A selected grid retains its dash-dot pattern. Grid bubbles retain a fixed pixel
  radius when the model zooms. A plus control adds parallel grids from cumulative
  current-unit spacing patterns such as `5000 3000 3x5400`.
- Toolbar icons and hit regions remain legible at desktop resolutions.

## Editing

Home exposes Move, Copy, Rotate, Mirror, Array, Scale, Trim, Extend, Offset,
Fillet, Chamfer, Stretch, Split, Align, Join and existing component operations.
Array supports linear and radial placement, with count including the original.
Scale supports a pivot, graphical reference and a positive numerical factor.
Copy, mirror and array show geometry previews without changing document state.
Tools reuse existing multi-selection and model operations; unsupported geometry
is refused clearly and atomically instead of partially changing the selection.

Point entry supports absolute `x,y` and `#x,y`, relative `@dx,dy`, polar
`@distance<degrees`, and scalar distance along the pointer direction. Values use
the current length unit. Invalid input stays editable and preserves the model.
Existing scalar expression input remains available. Enter confirms and Escape
cancels; a canceled preview must preserve an existing redo history.

## Types

An IfcTypes manager opens without selecting an occurrence. It lists native type
families, previews the selected type and edits its actual model definition.
Create, duplicate, rename, dimension/material/layer edits and deletion of unused
types are real undoable operations. Applying a compatible type updates a selected
occurrence or the default for the corresponding drawing tool. Used types cannot
be deleted. IFC and IFCX exports preserve the correct type classes and bindings.

## Automation and development

The native API supports model operations while the app is in the background.
A stdio MCP adapter exposes those operations and PID-bound Windows UI input and
client screenshots. A loopback HTTP adapter shares the same dispatch and locking.
The local dev launcher enables the API and identifies the target process.
Existing user windows and unsaved models remain untouched.

## Verification

Use native headless tests for geometry, snapping, input, undo/redo, type changes
and export relationships. Run at most three native tests per bundle and one
DynLex compiler per machine. Verify MCP protocol/transport and HTTP independently,
then test the actual native app, its UI previews and screenshot output.
