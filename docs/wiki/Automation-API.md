# Automation API

Another program — a script, a test, or an AI assistant through the MCP server — can drive the editor. The protocol is a folder; the source is [`automation/bim_api.dl`](https://github.com/OpenAEC-Foundation/open-bim-studio/blob/main/automation/bim_api.dl).

## Starting

```sh
open-bim-studio --example --api /path/to/api-folder
```

or switch it on in the app: **Collaborate > API / MCP**.

## The folder protocol

- The client writes a request to `request` in the folder (first as `request.tmp`, then renamed, so it is never read half written).
- The window reads it once a frame, removes it, does it, and writes the answer to `response` the same way.
- A request is lines: an id, a verb, then the verb's arguments, one per line.
- The answer is two lines: the id, then a JSON object with `"ok"` and what the verb returns, or `"error"`.

## Verbs

| Verb | What it does |
|---|---|
| `ping` | the API's version |
| `state` | tool, selection, message, storey, element counts, 3D cursor, `cursorFresh`, `editMode`, `sketching` |
| `elements` | the model's elements by kind |
| `buttons` | every ribbon button (also hidden discipline tabs and chooser rows): tab, group, label, key, code |
| `ribbon [TAB/]LABEL` | clicks the button as the mouse would; the window runs it on its next frame (also window commands such as Tile, Export, panels). `Tab/Label` picks between equal labels, e.g. `View/Tile`, `Sketch/Delete`; `Tab/Group/Label` between equal labels on one tab, e.g. `Collaborate/Export: Open sheet/PDF`. An exact name wins over a label that only starts with it |
| `button LABEL` | presses the button in the editor at once (tools only) |
| `key CODE` | a key or command code, as typed |
| `pointer X Y`, `click X Y` | the pointer to plan point X, Y in metres; a click there |
| `select ID` | selects an element |
| `properties`, `property CODE TEXT` | the selection's property rows; type TEXT into a row |
| `wall X1 Y1 X2 Y2`, `slab X1 Y1 X2 Y2` | a wall of the current type, a floor over a rectangle |
| `system X1 Y1 X2 Y2 [TYPE [ORIENT [PITCH [LENGTH]]]]`, `systemtypes` | a building system (TYPE -1 for none; ORIENT 0 vertical along the line, 1 horizontal over the rectangle, 2 tilted at PITCH degrees from level, LENGTH metres up the slope to the line's left); the available system types, with each recipe's orientation |
| `grid NAME X1 Y1 X2 Y2 LOW HIGH`, `gridrepeat SOURCE PATTERN [UNIT]` | a grid line; copies by a spacing pattern |
| `cursor X Y` | places the 3D cursor |
| `types [TAB]`, `typeadd`, `typeduplicate`, `typeset`, `typeapply`, `typedelete` | the type library, as in the IfcTypes window |
| `options` | tool, numeric input, ortho, modify and snap state |
| `undo`, `redo` | one step |
| `fit`, `tab N` | fit the views; show ribbon tab N (0 Home to 11 Structural) |
| `save` | File > Save on the window's next frame, to the model's file |
| `open NAME` | opens the plan or section view so named, or the sheet so numbered or named, as its tab (as the project browser does) |
| `run SENTENCE` | one sentence of the command line, e.g. `draw a wall from (0, 0) to (5, 0)` or `open the sheet "A-101"`: the same dispatch the window's command line uses (see the [user guide](User-guide.md#the-command-line)); a sentence that is not understood is refused with the closest one |

## MCP server

[`automation/mcp/open_bim_studio_mcp.py`](https://github.com/OpenAEC-Foundation/open-bim-studio/tree/main/automation/mcp) wraps the API as an MCP server for AI assistants. Its tools: `launch`, `connect`, `close`, `screenshot`, `state`, `elements`, `buttons`, `press_button` (uses `ribbon`, then returns the state), `key`, `click`, `move_pointer`, `select`, `properties`, `set_property`, `create_wall`, `create_floor`, `create_building_system`, `system_types`, `list_types`, `create_type`, `duplicate_type`, `set_type_field`, `apply_type`, `delete_type`, `tool_options`, `create_grid`, `repeat_grid`, `set_cursor`, `undo`, `redo`, `fit_view`, `ribbon_tab`, `save`, `open_view`, `run_sentence`, and `ui_window`, `ui_click`, `ui_move`, `ui_drag`, `ui_key`, `ui_type`, `ui_scroll`, which drive the window itself. `open_bim_studio_http.py` offers the same verbs over HTTP.

The plan to make this a documented, versioned interface is issue [#130](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/130).
