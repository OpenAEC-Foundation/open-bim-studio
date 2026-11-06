# FZK-Haus rebuilt through the MCP server

This example rebuilds the KIT FZK-Haus in Open BIM Studio by driving the application the way a
user does: ribbon buttons, clicks in the plan and rows of the properties panel, all through the
MCP server (`automation/mcp/open_bim_studio_mcp.py`). It does not use the `create_*` shortcuts.
Then it draws the house: rooms with names and numbers, exterior dimension chains, and the two
floor plans as technical drawings on A3 sheets, exported as PDF.

The reference model is `reference/models/AC20-FZK-Haus.ifc`. Its source, licence and SHA-256 are
in [`reference/README.md`](../../../reference/README.md). The model file is not in the
repository.

## Files

| File | What it does |
|---|---|
| `ifc_extract.py` | Reads the IFC's STEP text without ifcopenshell and writes `plan.json`: storeys, walls (axis, height, thickness), slabs, windows and doors with their host walls |
| `mcp_client.py` | A small stdio client for the MCP server: starts it, connects it to the app's API folder, calls its tools |
| `rebuild.py` | The rebuild, as named steps (`ALL` lists them in order) |

## Running it

From the repository root, with a dev build (`bash build.sh dev`):

```sh
mkdir -p fzk-out
python3 -I automation/examples/fzk-haus/ifc_extract.py reference/models/AC20-FZK-Haus.ifc > fzk-out/plan.json
./build/open-bim-studio-dev fzk-out/fzk-haus.ifcx --api fzk-out/api &
OBS_API=fzk-out/api OBS_OUT=fzk-out python3 automation/examples/fzk-haus/rebuild.py all
```

The app opens an empty model that it saves as `fzk-out/fzk-haus.ifcx`. The rebuild takes about
half a minute. The sheets end up as `fzk-out/drawings/A-101.pdf` and `A-102.pdf`.

- `OBS_DISPLAY` picks the X display for the MCP server (default `:0`).
- `OBS_CWD` is the folder the app runs in, where it writes exported PDFs. The default is the
  current folder.
- Run single steps by name, for example `rebuild.py spaces drawings`.

## What is rebuilt

| From the IFC | Here |
|---|---|
| Erdgeschoss ±0, Dachgeschoss +2.70 | Levels via Model > Level and the properties |
| Exterior walls 300 mm on their outer face, interior walls 240 mm on one face | Walls drawn on their centrelines with the Wall tool (clicks snap to 50 mm) |
| Base slab, upper floor | Floor tool, rectangle sketch |
| Two roof planes at 30°, eaves 0.5 m out | Two Roof sketches with Pitch, Slope toward and Top |
| Gable walls up to the ridge | Gable walls split at the ridge, each half attached to its own roof plane |
| 11 windows, 5 doors | Window and Door tools, types sized as in the IFC |
| 7 spaces, three of them parted by virtual boundaries | Room separators and Space, named as the IFC's spaces |

## Known differences

- A wall's top follows one roof plane, so each gable is two walls split at the ridge. The two
  upper windows, which sit across the ridge line in the IFC, are 0.6 m off to clear that split.
- Clicks snap to 50 mm, so interior walls can be up to 20 mm away from their IFC position.
