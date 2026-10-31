**English** · [Nederlands](README.nl.md)

<div align="center">

# Open BIM Studio

**Native BIM modelling, parametric components and model-based drawings, built on its own CAD kernel in DynLex.**

[![Release](https://img.shields.io/github/v/release/OpenAEC-Foundation/open-bim-studio?include_prereleases&label=preview&color=D97706)](https://github.com/OpenAEC-Foundation/open-bim-studio/releases)
[![Windows release](https://github.com/OpenAEC-Foundation/open-bim-studio/actions/workflows/windows-release.yml/badge.svg)](https://github.com/OpenAEC-Foundation/open-bim-studio/actions/workflows/windows-release.yml)
[![License: MPL-2.0](https://img.shields.io/badge/license-MPL--2.0-blue)](#license)

### [Download the preview](https://github.com/OpenAEC-Foundation/open-bim-studio/releases)

![The example building in the 3D view: two storeys of layered walls with windows on piles, the grid, and a small plan inset](docs/images/readme/hero.png)

</div>

Open BIM Studio is an [OpenAEC Foundation](https://github.com/OpenAEC-Foundation) application for creating and editing building models. You model walls, floors, roofs, columns, beams, piles, reinforcement and steel connections, inspect them in 2D and 3D, and develop plans, elevations, schedules and sheets from the same model.

It runs as a native desktop application with a Vulkan/GLFW interface on Linux; a Windows port is in the repository. The application and its CAD kernel are written in [DynLex](docs/notes/dynlex-guide.md).

> **Development preview.** `main` is the shared development baseline, not a production release. Features and file formats are still evolving. A successful compiler build does not establish that the app, the installer or every modelling workflow has been tested.

## Try it

Install the [Linux preview](#download) and start it with the example building:

```sh
~/.local/bin/open-bim-studio --example
```

It opens a two-storey building on piles with grids, layered walls, windows and doors. Draw a wall from the **Home** tab, drag a grip with **Select**, switch to the **3D** tab, or open an elevation or a quantity schedule from **Views** on the left.

## Download

Every preview is on the [releases page](https://github.com/OpenAEC-Foundation/open-bim-studio/releases). The latest is [0.1.1](https://github.com/OpenAEC-Foundation/open-bim-studio/releases/tag/v0.1.1).

| Platform | Installer |
|----------|-----------|
| **Linux** (x86-64) | `Open-BIM-Studio-0.1.1-linux-x86_64.run` |
| **Windows** | Not in a release yet; see [Windows release](docs/notes/windows-release.md) |
| **macOS** | Not available |

To install or update, run `bash Open-BIM-Studio-0.1.1-linux-x86_64.run`. It replaces `~/.local/share/open-bim-studio` and its launcher; your project files are stored apart from it. Back up projects before trying a preview.

The installer is signed with the OpenAEC OpenPGP key (`.asc`, with the public key and fingerprint in the release) and listed in `SHA256SUMS`; `VERIFICATION.txt` explains the check. Linux needs glibc 2.38 or newer, an X11 session (or XWayland) and Vulkan support.

## Why use it?

- **Free and open.** MPL-2.0 source. No licence fees, no account, no lock-in.
- **Open formats.** Projects are saved as IFCX; IFC goes in and out.
- **One model, all outputs.** Plans, sections, elevations, 3D, schedules and sheets are derived from the model, not drawn beside it.
- **Parametric where it counts.** Wall and building-system types, hosted windows, stairs, reinforcement cages and steel joints keep their parameters and can be edited later.
- **Structural detail in the same model.** Reinforcement with position labels and bending schedules, and steel connections with plates, bolts and welds.
- **Scriptable.** A local API and an MCP adapter let other programs and AI assistants drive the editor.

## Screenshots

| | |
|---|---|
| ![Structural plan of the example building with grids and hatched layered walls](docs/images/readme/plan.png) **Plan with grids and layered walls** | ![North elevation of the example building with storey levels and grid heads](docs/images/readme/elevation.png) **Elevation derived from the model** |
| ![Steel hall in 3D: columns, rafters, purlins and bracing](docs/images/readme/steel-3d.png) **Steel hall with parametric connections** | ![Plan of cages, wall and floor reinforcement with position labels](docs/images/readme/reinforcement.png) **Reinforcement with position labels** |
| ![Quantity schedule listing walls, windows, doors, floors, piles and spaces](docs/images/readme/schedule.png) **Quantity schedule** | |

The images are made by `python3 tools/build_readme_images.py` from the models in this repository.

## Modelling

| Area | Current implementation |
|---|---|
| Building model | Levels, grids, layered walls, floors, roofs, ceilings, openings, beams, columns, piles and persistent Spaces |
| Parametric systems | Building-system types with frames and panels, hosted window systems, stairs, railings and component libraries |
| Direct editing | Selection, grips, numerical properties, snapping, transforms, boundary editing with Tab, Push/Pull and face splitting |
| Reinforcement | Parametric bars, cages, stirrups, area reinforcement and meshes; position labels, schedules and NL/international notation |
| Connections | Parametric steel joints, member cuts, plates, bolts, welds and reusable connection types |
| Views and drawings | Plans, sections, 3D views, section boxes, dimensions, tags, drawing standards, sheets and PDF/SVG output |

These are implemented areas, not a claim that every combination is complete or validated.

- **Reinforcement.** Bars are shown as depth-tested centre lines by default to keep 3D fast; the Graphics menu shows their diameters. See [reinforcement scope](docs/notes/reinforcement-scope.md) and the [reinforcement library](docs/notes/reinforcement-library.md).
- **Steel connections.** Recipes for end plates, fin plates, cleats, splices, gussets and base plates, and named types you can reuse. See the [steel connection guide](docs/notes/connections.md) and the [editable steel hall](tests/models/steel-connection-hall.bim).

## Interoperability

| Format | Open | Save / export |
|--------|------|---------------|
| **IFCX binary** (`.ifcxb`) | Yes | Yes, the editor's project format |
| **IFCX** (`.ifcx`, JSON) | Yes | Yes |
| **IFC** (`.ifc`) | Yes | Yes |
| **BIM text** (`.bim`) | Yes | Yes, used by fixtures and development tools |
| **DXF** (`.dxf`) | As reference geometry | No |
| **PDF / SVG** | Drawing-import helpers | Yes, drawings and sheets |

Supported IFC elements become editable native objects; other imported geometry stays read-only. DXF entity coverage is incomplete. The application cannot yet rebuild every source drawing or imported object as parametric geometry, so keep your source files when testing round trips. IFC/IFCX support is evolving and is not a certification claim.

## MCP

The editor serves a local automation API through a folder (`--api FOLDER`, or **Collaborate > Automation > API / MCP**). A stdio MCP adapter and an optional loopback HTTP adapter sit on top of it. An assistant can read the model, create walls, floors, grids and building systems, edit properties and types, press ribbon commands, undo and redo, and take screenshots. Every model change is one undo step in the editor you are looking at, and the API and adapters run only on your own computer. See [automation/README.md](automation/README.md).

## Testing and reliability

- **256 headless application tests.** Each is a DynLex program in a module's `tests/` folder with a checked-in expected output (`*.expected.txt`); `build.sh test` compiles, runs and compares them.
- **218 kernel test programs** in `kernel/tests/`. The last authoritative run passed 173 of 212 fixtures; the 39 failures predate the module split and are listed in [`kernel/tests/KNOWN-FAILURES.md`](kernel/tests/KNOWN-FAILURES.md).
- **43 Python tests** for the MCP and HTTP adapters in `automation/mcp/test_mcp.py`.

Count sources: files matching `*/tests/*.expected.txt` outside `kernel/`, `*.dl` files under `kernel/tests/`, and `def test_` in `test_mcp.py`. The [consolidation report](docs/CONSOLIDATIE.md) records the tested baseline and known failures; it is not a general green build badge.

## Current limitations

- **Not a production release.** File formats can still change between previews.
- **Windows has no tested installer yet.** The native port and the ZIP/MSI pipeline are in the repository.
- **The Linux app needs X11.** It runs under XWayland, not as a native Wayland client.
- **Plate openings have no finished GUI workflow.** The geometry is integrated.
- **Large models are slow.** Large-model performance and full GUI regression coverage are active work.
- **Imports are not fully parametric.** Unsupported IFC elements stay read-only, and DXF entity coverage is incomplete.
- **Full builds are heavy.** A full compilation can approach or exceed 10 GB of RAM.

Found something? [Open an issue](https://github.com/OpenAEC-Foundation/open-bim-studio/issues).

## Under the hood

The application is written in DynLex, a programming language of English-like sentences that compiles to native code. It has its own CAD kernel (`kernel/`) for planar, NURBS and B-rep geometry, a semantic BIM model with transactions and undo (`bim/`), and a Vulkan renderer (`viewer/`). The code is split into modules in six layers, from kernel to UI; each module declares itself in a `MODULE` manifest, and `scripts/check-layers.sh` guards the import direction. A small C shim (`platform/`) bridges the operating system.

## Contributing

- **Try it on a real project** and report bugs or missing features as an [issue](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/new). Include the app commit or version, OS, GPU and driver when relevant, steps to reproduce, what you expected and what happened, and a small generic sample model.
- **Write code.** Read [CONTRIBUTING.md](CONTRIBUTING.md), the [two-computer agreement](docs/TWEE-COMPUTERS.md) and the [task board](docs/WERKBORD.md). Start a short task branch from `main`, keep product code in DynLex, include tests and remaining limitations in the PR, and coordinate changes to shared model, editor, renderer and file-format code. Compiler work belongs in the DynLex repository.

Keep private project drawings, customer models, credentials and local toolchain paths out of this public repository. Repository content and commit messages are in English.

## Quick start (developers)

```sh
git clone https://github.com/OpenAEC-Foundation/open-bim-studio.git
cd open-bim-studio
export DYNLEX_ROOT="/absolute/path/to/dynlex-cadkernel"   # a built, compatible DynLex checkout
export BIM_BUILD_DIR="$PWD/build/local-dev"
bash ./build.sh toolchain-info                             # paths and compiler hash; compiles nothing
BIM_DEBUG=0 bash ./build.sh dev
bash ./build.sh run-dev --example
```

Requires:

- A **DynLex fork checkout** at the pinned commit (`codex/cadkernel-port` at `c2d32bea` with the patches of `patches/`), built in place at `build/dynlex`. An arbitrary upstream compiler is not a supported substitute. See the [toolchain notes](docs/notes/application-and-toolchain.md).
- Bash, a C compiler and `ar` for the native platform bridge; Python 3 for test bundling and drawing-import helpers.
- Vulkan/GLFW runtime support and fonts (the installer expects Noto Sans).
- Enough RAM. Run **one DynLex compiler per physical computer** and use separate build directories.

Open BIM Studio is part of the [OpenAEC Foundation](https://github.com/OpenAEC-Foundation) family of apps.

### Building and running

To open a project, replace `--example` with its path: `bash ./build.sh run-dev /absolute/path/to/project.ifcxb`. The development executable is `$BIM_BUILD_DIR/open-bim-studio-dev`; `bash ./build.sh app` and `bash ./build.sh run --example` build and run the optimised application. `OBS_CSG_DETAIL=1` opens the experimental fastener CSG detail panel at startup; see [the fastener guide](docs/notes/fastener-components.md#csg-detail-in-obs).

Instead of `DYNLEX_ROOT` you can save the compiler-checkout path on one line in `.dynlex-root.local` (ignored by Git; `DYNLEX_ROOT` wins). Record both the source commit and the compiler-binary hash when you report a build.

`build.sh` compiles from the repository root: imports such as `bim/x.dl` resolve here, `lib/std.dl` in the compiler checkout, and a file under `lib/` here shadows the checkout's (see `lib/README.md`). Every build command first runs `build.sh generate`, which composes the model record and dispatchers from the `MODULE` manifests into `generated/` (`tools/compose_modules.py`) and copies the prebuilt shaders to `build/shaders`. It does not edit the compiler checkout.

On Windows, `scripts/dev-windows.ps1 -Tests evaluate,wall_base` compiles, runs and compares named tests, `-Kernel` builds the kernel library and runs its seam tests, and `-App` builds the application into `build\windows-app`. It reads the toolchain from `.dynlex-windows.local.ps1` (see `scripts/dev-windows.example.ps1`) and the compiler from `.dynlex-root.local`.

### Tests

Start with a small headless bundle rather than the whole suite:

```sh
bash ./build.sh bundle ui_layout text_glyphs plan_pan
```

Use at most **three tests per bundle**: tests that import the full editor or view stack are expensive even without a window. A bundle compiles once, runs its checks and compares them with the expected output; investigate any compiler diagnostic or runtime failure. A release additionally needs a full app build and interactive and installation checks on its target platform.

The README images are made with `python3 tools/build_readme_images.py` (Xvfb, Mesa's software Vulkan and Pillow; no GPU needed), and `--check` verifies them.

### Code organisation

```text
kernel/        CAD kernel: core/, planar/, nurbs/, space/, brep/, acis/, fast/, tests/, reference/, docs/
bim/           The BIM core: document, element identity, psets, settings, index, undo
viewer/        Vulkan layer, shaders, scene, instances, section caps, clash, canvas
exchange/      ifcx (the native binary format), dxf_dwg, step, import (drawings, images, caches)
ifc/           IFC schema, STEP reading and writing, psets, promote
views/         common, drawings, sheets, schedules, export (SVG, PDF)
materials/     Section materials, hatches, library
localisation/  Country content as data (registry, nl); empty until stage 4
automation/    The request/response API and the MCP and HTTP adapters
ui/            editor (the tool framework), properties, panels, shell (main.dl, fonts, icons)
elements/      linear, connection, planar, object: the shape classes
pattern/       common, grids (Building System)
structural/    rebar, steel, results
architectural/ openings, stairs, spaces
mep/           common (networks)
platform/      obs_platform.c, the per-OS C shim
generated/     The model record and dispatchers composed from the MODULE manifests
tests/         Example and review models (tests/models/)
tools/         Module composer, test bundler, probes, icon maker, README images, GPU example
installer/     Linux installer and Windows package scripts and licences
patches/       Compiler patches until they are upstream
lib/           Overrides of the compiler checkout's library (lib/README.md)
scripts/       The Windows build script and the layer check
build.sh       Local build, run, test and installer entry point
docs/          Architecture, decisions, research, notes, coordination and status
```

`bim/bim_model.dl` holds semantic objects and transactions; `elements/planar/bim_evaluate.dl` derives geometry; the drawing and scene modules produce 2D and 3D representations. The `bim_editor*.dl` files in the element, discipline and `ui/properties/` modules implement editing operations, and `ui/panels/bim_ui*.dl` and `ui/shell/main.dl` connect them to the native interface. `docs/OWNERS.md` names the owner per module, the [module guide](docs/notes/module-guide.md) gives more context, and the [module-split design](docs/superpowers/specs/2026-10-28-module-split-design.md) explains the layout.

The repository began as a research programme. Its [vision](docs/vision/vision.md), [architecture](docs/architecture/overview.md), [ADRs](docs/architecture/decisions/) and [research](docs/research/README.md) remain available; older plans may predate the current implementation.

## License

The application source files carry MPL-2.0 notices. Dependencies and bundled assets have their own terms; the DynLex runtime uses LGPL-3.0. When you redistribute builds, consult each component's source notices, the [installer licence bundle](installer/licenses/README.txt), and the font and icon notices.

## Trademarks

This README names products and technologies of others, such as Windows, macOS, Linux and Vulkan. Open BIM Studio is an independent project and is not affiliated with, endorsed by or sponsored by their owners.
