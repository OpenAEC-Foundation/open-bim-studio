# Open BIM Studio MCP server

An AI assistant (Claude Code, Claude Desktop, any MCP client) drives the
modeller through this server: it looks (screenshots, the editor's state, the
model's elements, the properties panel) and acts (ribbon buttons, clicks in
the plan with the active tool, keys, creating elements, setting properties,
undo).

```
assistant ──MCP (stdio)──> open_bim_studio_mcp.py ──folder──> modeller (bim_api.dl)
                                     └──────── X11 screenshots ────────┘
```

## The modeller's automation API

The modeller serves requests from a folder (`bim_api.dl`):

- start it with `--api FOLDER`, or
- switch on **Collaborate > Automation > API / MCP**; the folder is then
  `open-bim-studio-api` in the directory the modeller runs in.

The status bar shows `API FOLDER` while it is on. A client writes `request`
(as `request.tmp`, then renamed): an id, a verb and its arguments, one a line.
The modeller answers in `response`: the id, then a JSON object. The verbs are
listed at the top of `bim_api.dl` (`ping`, `state`, `elements`, `buttons`,
`button`, `key`, `pointer`, `click`, `select`, `properties`, `property`,
`wall`, `slab`, `system`, `systemtypes`, `undo`, `redo`, `fit`, `tab`).

Any program can use it, for example from a shell:

```
printf '1\nwall\n0\n0\n5\n0\n' > api/request.tmp && mv api/request.tmp api/request
sleep 0.2; cat api/response
```

## The MCP server

`open_bim_studio_mcp.py` needs Python 3.10 or later, and python-xlib and
Pillow for screenshots. Register it with Claude Code:

```
claude mcp add open-bim-studio -- python3 /path/to/mcp/open_bim_studio_mcp.py
```

Its tools:

| Tool | What it does |
|---|---|
| `launch` | starts the modeller in its own nested X server (Xephyr, display :97) with the API on, and connects; nothing appears on the desktop |
| `connect` | attaches to a running modeller's API folder (and its display, for screenshots) |
| `close` | closes what `launch` started |
| `screenshot` | the modeller's window (or the whole screen) as a PNG |
| `state`, `elements`, `properties`, `buttons`, `system_types` | what the modeller shows and holds |
| `press_button`, `key`, `click`, `move_pointer` | the ribbon, the keyboard and the mouse in the plan (metres) |
| `select`, `set_property` | the selection and the properties panel |
| `create_wall`, `create_floor`, `create_building_system` | elements directly, one undo step each |
| `undo`, `redo`, `fit_view`, `ribbon_tab` | the rest |

`launch` finds the modeller from its `binary` argument, the environment
variable `OPEN_BIM_STUDIO_BINARY`, or `open-bim-studio` on the PATH. A modeller that is
not installed finds its fonts and shaders through `OPEN_BIM_STUDIO_HOME`
(a folder with `fonts/` and `shaders/`). The modeller's output goes to
`modeller.log` in the folder `launch` makes; when the modeller stops, the
next tool call fails at once and shows the end of that log.

A first session:

1. `launch` (or `connect` with the folder);
2. `screenshot` to see it;
3. `press_button` "Wall", then `click` at (0, 0) and (6, 0) and (6, 4);
4. `key` 256 (Esc), `elements`, `select` a wall, `properties`,
   `set_property` with the Height row's code and "2800" (lengths are in the
   project's unit, millimetres by default);
5. `screenshot` again.
