# Open BIM Studio automation

The editor has a native model API, a stdio MCP adapter, and an optional
loopback HTTP adapter. Model operations run inside the editor and do not
require mouse input or window focus. Windows UI tools additionally capture
and operate the visible application window.

```text
MCP client -- stdio --> open_bim_studio_mcp.py -- UTF-8 folder --> editor
HTTP client -- 127.0.0.1 --> open_bim_studio_http.py -----------^
                              Windows capture/input --> bound app window
```

## Start the editor and attach

Start the editor with `--api FOLDER`, using an absolute folder path whose
parent already exists. For a native Windows development build:

```powershell
& 'C:\path\open-bim-studio-dev.exe' --example --api 'C:\path\api'
```

Alternatively, switch on **Collaborate > Automation > API / MCP** in the
editor. Its default folder is `open-bim-studio-api` under the editor's
working directory. The status bar shows `API FOLDER` while enabled.

Use Python 3.10 or later. Run the MCP adapter with:

```powershell
python -u C:\path\mcp\open_bim_studio_mcp.py --api-folder C:\path\api
```

Configure those command/arguments in an MCP client; the client starts the
stdio server on demand. `OPEN_BIM_STUDIO_API_FOLDER` is an alternative to
`--api-folder`. Without either setting, call the `connect` tool with
`{"folder":"C:/path/api"}`. A configured folder is used when the first model
tool is called; MCP initialization does not wait for the editor.

For multiple Windows app instances, pass `--pid 1234` or supply `pid` to
`connect` / `ui_window`. An existing instance must have the executable name
`open-bim-studio.exe` or `open-bim-studio-dev.exe` and the app window title.
Instances started by `launch` bind to the exact executable and process id.
Native file handling currently works best with an ASCII API-folder path on
Windows; request and response contents are UTF-8.

## MCP tools

| Tools | Purpose |
|---|---|
| `launch`, `connect`, `close` | Start/attach; close only processes this adapter launched |
| `state`, `elements`, `properties`, `buttons`, `system_types` | Inspect the model/editor |
| `create_wall`, `create_floor`, `create_building_system` | Native model creation, one undo step each |
| `create_grid`, `repeat_grid`, `set_cursor` | Grid creation/repetition and the model cursor |
| `select`, `set_property`, `undo`, `redo` | Native selection, properties and transactions |
| `list_types`, `create_type`, `duplicate_type`, `set_type_field`, `apply_type`, `delete_type` | Native IfcTypes library and undoable definition edits |
| `tool_options` | Active numerical input, units, ortho and modification options |
| `press_button`, `key`, `click`, `move_pointer` | Native editor commands and plan points in metres |
| `fit_view`, `ribbon_tab` | Native view fitting and ribbon tab selection |
| `screenshot` | MCP `image/png` content; optional `save_to` path |
| `ui_window`, `ui_click`, `ui_move`, `ui_drag`, `ui_key`, `ui_type`, `ui_scroll` | Windows window binding and visible UI control |

Model creation and plan coordinates use metres. `set_property` values use
the project's displayed unit, millimetres by default. `create_grid` accepts
`name, x1, y1, x2, y2, low, high` in metres. `repeat_grid` accepts `source`
(the grid id as a string, or `selected`), a `pattern` such as `5000 3x5400`,
and optional `unit_code` (0 mm, 1 cm, 2 m; otherwise the project unit).
`set_cursor` accepts `x,y` in metres and places the 3D cursor at z=0;
`state` returns `cursor3D: [x,y,z]`.

`press_button` sends editor commands; window/chrome-only buttons require
`ui_click`. `elements` lists storeys, walls, floors, systems, openings and
grids. Direct file open/save/export and full view management are not native
API verbs yet.

### Windows screenshot and UI coordinates

Windows capture and input use `ctypes` and the standard library, without
extra Python packages. `screenshot` restores/focuses the bound app and
captures its **visible client area**, including the rendered Vulkan canvas.
The whole client area must be on screen and uncovered. This visible-screen
capture avoids the black Vulkan content produced by offscreen GDI window
rendering. `whole_screen: true` is refused on Windows.

`ui_window` returns the bound process/window identity and `client_width` /
`client_height`. All UI coordinates are **physical pixels relative to the
top-left corner of the screenshot**, excluding the operating system title
bar. Mixed-DPI displays use the same physical coordinate space for capture
and input. Reinspect after resizing the window.

Example MCP tool arguments:

```json
{"name":"screenshot","arguments":{}}
{"name":"ui_click","arguments":{"x":120,"y":80}}
{"name":"ui_key","arguments":{"key":"ctrl+a"}}
{"name":"ui_type","arguments":{"text":"Ground floor"}}
{"name":"ui_key","arguments":{"key":"enter"}}
{"name":"ui_scroll","arguments":{"x":250,"y":400,"steps":-3}}
```

UI calls verify process identity and foreground focus. They refuse ambiguous
instances, out-of-bounds/covered click points, physical modifier keys held
by the user, and system/window-switching shortcuts. Focus changes abort
subsequent input. Modal dialogs are not targeted; close them before using
these tools. A closed/replaced window requires an explicit reconnect.
Screenshots and UI calls need an interactive desktop; model tools can work
while the app is covered or minimized.

### Launch and Linux support

`launch` finds the binary through its `binary` argument,
`OPEN_BIM_STUDIO_BINARY`, or `open-bim-studio` on PATH. Windows opens the
native app visibly. Linux retains the nested Xephyr display (default `:97`)
and optional `display`, `width`, `height` arguments. Linux screenshots need
`python-xlib` and Pillow; native `ui_*` tools are Windows-only.

An uninstalled binary finds `fonts/` and `shaders/` through
`OPEN_BIM_STUDIO_HOME`. Windows also detects those folders beside the
executable. Output goes to `modeller.log` in the temporary launch folder;
a stopped process is reported with the end of that log. `close` and stdio
EOF terminate only processes launched by this adapter.

## Optional loopback HTTP API

```powershell
python C:\path\mcp\open_bim_studio_http.py --api-folder C:\path\api --pid 1234 --port 8765
Invoke-RestMethod http://127.0.0.1:8765/health
Invoke-RestMethod http://127.0.0.1:8765/api -Method Post -ContentType application/json -Body '{"verb":"state"}'
Invoke-RestMethod http://127.0.0.1:8765/api -Method Post -ContentType application/json -Body '{"verb":"wall","arguments":[0,0,5,0]}'
Invoke-RestMethod http://127.0.0.1:8765/tools/screenshot -Method Post -ContentType application/json -Body '{}'
```

- `GET /health`: adapter status/configuration; use native `ping` to check
  that the editor is actually answering.
- `POST /api`: `{"verb":"state","arguments":[]}` forwards a native command
  and returns its JSON response. Supported verbs: `ping`, `state`,
  `elements`, `buttons`, `button`, `key`, `pointer`, `click`, `press`,
  `release`, `select`, `properties`, `property`, `wall`, `slab`, `system`,
  `systemtypes`, `grid`, `gridrepeat`, `cursor`, `types`, `typeadd`,
  `typeduplicate`, `typeset`, `typeapply`, `typedelete`, `options`, `undo`,
  `redo`, `fit`, `tab`.
- `POST /tools/NAME`: the body is the MCP tool's argument object; returns
  its MCP content blocks, including base64 PNGs for screenshots.

The HTTP server binds only `127.0.0.1`; there is no external bind option.
It accepts JSON POST bodies up to 1 MiB with a single Content-Length,
rejects browser Origin/cross-site requests and unexpected Host values, and
does not enable CORS. It has no authentication layer; callers are local
processes in the user's session. Stop it with Ctrl+C or terminate the helper
process when finished.

## Native folder transport and verification

A request contains an id, verb and arguments, one per line. Publish
`request.tmp` by atomically renaming it to `request`. The editor removes it
and publishes `response`: the same id followed by a JSON object with `ok`
and result fields, or `error`. Arguments cannot contain embedded newlines.

The adapters serialize calls using a thread lock plus an OS-owned
`transport.lock` file in the API folder. Separate MCP/HTTP processes using
these adapters can safely share the single native slot; locks are released
automatically when a process exits. Raw folder clients must implement the
same locking protocol or run without other clients. The lock file itself
may remain after exit. Model selection/state is shared across clients.

Headless Python verification from the repository root, without opening or
controlling the editor:

```powershell
python -B -m unittest discover -s spikes/dynlex-bim-slice/overlay/examples/bim-slice/mcp -p test_mcp.py -v
```

The checks cover protocol validation, Unicode/framing, real loopback HTTP
forwarding to a stub native responder, concurrent bridge processes, window
identity/coordinate checks and refusal paths. A live native Windows smoke
test must additionally check screenshot contents (including the canvas),
UI input and a create/undo model roundtrip on the target graphics driver.

## Background IfcTypes editing

`list_types` reads definitions directly; `create_type`, `duplicate_type`,
`set_type_field`, `apply_type` and `delete_type` reuse the native IfcTypes
manager. Library editing creates no temporary model occurrences. IDs are
stable native model IDs, not row positions. A deletion refuses referenced
types. Successful definition changes have a native undo step.

Tabs: 0 Wall, 1 Slab, 2 Roof, 3 Ceiling, 4 Column, 5 Beam, 6 Pile,
7 Opening, 8 Profiles. Omitting `tab` from `list_types` lists all tabs;
catalog profiles also occur under their role tab. Creating on tab 8 makes
a plain beam type, editable on tab 5, matching the manager's Add action.

`list_types` returns `id`, `tab`, `family`, `role`, `name`, `ifcClass`,
`material`, `width`, `depth`, `sill`, `round`, `layerCount`, `useCount`,
`nlsfb`, `omniclass` and `layers` (material/thickness). Returned dimensions
are **metres**. For openings, depth is height and round identifies a door;
for planar types, width is total thickness.

`set_type_field` accepts a string value. Field 0 is name, 1 material,
2 width or planar layer thickness, 3 depth or opening height, 4 opening
sill, 5 NL-SfB, 6 OmniClass. Optional `layer` is zero-based and defaults to
0. Editing lengths uses **project units**, reported as `lengthUnit`:
0 millimetres, 1 centimetres, 2 metres. Unsupported fields are refused.

Native folder verbs are `types [TAB]`, `typeadd TAB`,
`typeduplicate TAB ID`, `typeset TAB ID FIELD VALUE [LAYER]`,
`typeapply TAB ID` and `typedelete TAB ID`. For example, HTTP POST `/api`
with `{"verb":"typeset","arguments":[0,123,2,"250",0]}` changes the
first wall layer to 250 project units. `typeapply` sets the drawing default
and changes a compatible selected occurrence; an incompatible selection
is retained.

`tool_options` (native `options`) reads the current tool, numeric input,
lengthUnit, orthoOn/orthoHeld, modify count/radial/sweep/copyMode/factor/
radius/chamfer/axis, and snap label/point. It does not change editor state.

### Hover and drag gestures

`ui_move {"x":400,"y":300}` moves the pointer without clicking, for hover
and native snapping. `ui_drag` operates in screenshot/client pixels, for
example `{"from_x":400,"from_y":300,"to_x":700,"to_y":500,"button":"left"}`.
Use left for selection/gizmos, or the app's configured middle/right button
for pan. The optional `steps` is 1–120 (default 12); `duration_ms` is
0–2000 (default 180). Normal app gestures should use a visible duration so
the app can process its mouse-down and intermediate frames.

Both drag endpoints and the interpolated path are checked before pressing.
Each step rechecks app identity, foreground, client geometry and occlusion.
If focus changes or the window moves/resizes, the gesture stops without
refocusing another window. A finally block releases the synthetic button
on success or failure, including failed movement or mouse-down injection.
Release physical modifier keys and mouse buttons before either tool;
modifier injection is unsupported. HTTP uses the same tools at
`POST /tools/ui_move` and `POST /tools/ui_drag`.

Click and key/chord tools send down and up in separate Windows input calls,
with a fixed 80 ms hold for the native editor's frame polling and a 40 ms
released interval between gestures. Focus/identity are checked throughout;
on failure, finally blocks release every synthetic key/button, including
partially accepted input batches. Unicode text still uses character events.
Drag also holds its initial point for 80 ms before motion, even with
`duration_ms: 0`, and allows a released frame after the gesture.

While the editor has a provisional move, rotate, drag, grab or push gesture,
native `wall`, `slab`, `system`, `property`, `grid`, `gridrepeat`, type-library
writes, `select`, `undo` and `redo` return `ok:false` with an active-gesture
error. Their MCP tools report the same refusal. Finish or cancel the gesture
first; refusal preserves geometry, selection, input and undo/redo state.
Read operations, `tool_options`, cursor placement and native
`key`/`pointer`/`click`/`press`/`release` gesture controls remain available;
`key` with Escape (256) cancels the original provisional transaction.
