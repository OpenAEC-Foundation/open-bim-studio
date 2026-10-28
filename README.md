# Open BIM Studio

**Native BIM modelling, parametric components and model-based drawings — built in DynLex.**

Open BIM Studio is an [OpenAEC Foundation](https://github.com/OpenAEC-Foundation)
project for creating and editing building models, inspecting them in 2D and 3D,
and developing drawings, reinforcement details and schedules from the same model.
The application uses a native Vulkan/GLFW interface and a CAD kernel implemented
in DynLex.

> **Development preview.** `main` is the shared development baseline, not a
> production release. Features and file formats are still evolving. A successful
> compiler build does not establish that the app, installer or every modelling
> workflow has been tested.

[Download the preview](https://github.com/OpenAEC-Foundation/open-bim-studio/releases)
· [Report an issue](https://github.com/OpenAEC-Foundation/open-bim-studio/issues)
· [Build instructions](#build-from-source-linux)
· [Development board](docs/WERKBORD.md)

## What is in the modeller?

| Area | Current implementation |
|---|---|
| Building model | Levels, grids, layered walls, floors, roofs, ceilings, openings, beams, columns, piles and persistent Spaces |
| Parametric systems | Building-system types with frames and panels, hosted window systems, stairs, railings and component libraries |
| Direct editing | Selection, grips, numerical properties, snapping, transforms, boundary editing with Tab, Push/Pull and face splitting |
| Reinforcement | Parametric bars, cages, stirrups, area reinforcement and meshes; position labels, schedules and NL/international notation |
| Connections | Parametric steel joints, member cuts, plates, bolts, welds and reusable connection types |
| Views and drawings | Plans, sections, 3D views, section boxes, dimensions, tags, drawing standards, sheets and PDF/SVG output |
| Interchange | IFC import/export, IFCX and binary IFCX project persistence, native DXF reference geometry and drawing-import helpers |
| Automation | A local request/response API and an MCP adapter for driving editor operations |

These are implemented areas, not a claim that every combination is complete or
validated. In particular, the plate-opening geometry is integrated but its GUI
workflow is unfinished. Large-model performance and full GUI regression coverage
remain active work.

Reinforcement is displayed as **depth-tested centre lines by default** to reduce
3D rendering work. The Graphics menu can display bar diameters when needed.
The model retains its reinforcement parameters independently of this display mode.
See [reinforcement scope](docs/notes/reinforcement-scope.md) and the
[reinforcement library](docs/notes/reinforcement-library.md) for details.

See the [steel connection guide](docs/notes/connections.md) and the
[editable 3D steel hall](tests/models/steel-connection-hall.bim)
for the connection recipes, named types and current modelling limits.

## Try a packaged preview

The published [v0.1 preview](https://github.com/OpenAEC-Foundation/open-bim-studio/releases/tag/v0.1)
contains a **Linux x86-64 installer**, a demonstration pavilion, a source snapshot,
release notes and checksums. It predates the current `main` branch.

Download `Open-BIM-Studio-0.1-linux-x86_64.run` from that release and run:

```sh
bash Open-BIM-Studio-0.1-linux-x86_64.run
```

Read the release notes and verification file before testing. The graphics driver
must support Vulkan; the current Linux application uses X11/GLFW.

**Windows:** the native port and ZIP/MSI packaging pipeline are in the repository.
A tested Windows installer is not included in v0.1. Follow the
[Windows release instructions](docs/notes/windows-release.md) and
[workflow results](https://github.com/OpenAEC-Foundation/open-bim-studio/actions/workflows/windows-release.yml)
for its current status.

## Build from source (Linux)

The application lives in module directories at the root, one per domain in six
layers: `kernel/`, `bim/`, the services (`viewer/`, `exchange/`, `ifc/`, `views/`,
`materials/`, `localisation/`, `automation/`, `ui/editor/`), the shape classes
(`elements/`, `pattern/`), the disciplines (`structural/`, `architectural/`,
`mep/`) and the UI (`ui/properties/`, `ui/panels/`, `ui/shell/`); each module
holds its tests in `tests/` and declares itself in a `MODULE` manifest.
`docs/OWNERS.md` names the owner per module, `scripts/check-layers.sh` guards
the import direction, and `docs/superpowers/specs/2026-10-28-module-split-design.md`
is the design.

### Prerequisites

- A **DynLex fork checkout** at the pinned commit (`codex/cadkernel-port` at
  `c2d32bea` with the patches of `patches/`), built in place at `build/dynlex`;
  the compiler finds its own `lib/`. An arbitrary upstream compiler is not a
  supported substitute. See the [toolchain notes](docs/notes/application-and-toolchain.md).
- Bash, a C compiler and `ar` for the small native platform bridge.
- Python 3 for existing test-bundling and drawing-import helpers. BIM product
  logic, tools and geometry are written in **DynLex**, not Python.
- Vulkan/GLFW runtime support and fonts; the DynLex checkout supplies its
  dependencies. The Linux installer additionally expects the Noto Sans fonts.
- Enough free RAM. Full compilations can approach or exceed **10 GB**. Run
  **one DynLex compiler per physical computer** and use separate build directories.

### Configure, build and run

```sh
git clone https://github.com/OpenAEC-Foundation/open-bim-studio.git
cd open-bim-studio

# Use your compatible, already-built DynLex checkout.
export DYNLEX_ROOT="/absolute/path/to/dynlex-cadkernel"
export BIM_BUILD_DIR="$PWD/build/local-dev"

# Reports paths and the compiler hash; does not compile anything.
bash ./build.sh toolchain-info

# Development build, without debug symbols to limit memory use.
BIM_DEBUG=0 bash ./build.sh dev
bash ./build.sh run-dev --example
```

To reopen a project, replace `--example` with its path:

```sh
bash ./build.sh run-dev /absolute/path/to/project.ifcxb
```

The development executable is `$BIM_BUILD_DIR/open-bim-studio-dev`.
`build.sh` compiles from the repository root: imports such as `bim/x.dl`
resolve here, `lib/std.dl` in the compiler checkout, and a file under `lib/`
here shadows the checkout's (see `lib/README.md`). `build.sh generate` writes
the two import files of `generated/` (the platform's window style and the
self-test entry) and copies the prebuilt shaders into `build/shaders`; every
build command runs it first. It does not edit the compiler checkout.

Alternatively, save the absolute compiler-checkout path on one line in
`.dynlex-root.local`. That machine-local file is ignored by Git; an explicit
`DYNLEX_ROOT` takes precedence. Record both the source commit and compiler-binary
hash when reporting a build.

For an optimised application, use `bash ./build.sh app`, then
`bash ./build.sh run --example`. Rebuilding the DynLex compiler is a separate task.

## Tests and validation

Start with a small headless bundle rather than compiling the whole test suite:

```sh
# Run after configuring DYNLEX_ROOT and BIM_BUILD_DIR as above.
bash ./build.sh bundle ui_layout text_glyphs plan_pan
```

Use at most **three tests per bundle**. Tests importing the full editor or view
stack can be expensive even when they do not open a window. A bundle compiles
once, executes its checks and compares their output with checked-in expectations;
compiler diagnostics and runtime failures must be investigated.

A release additionally needs a full app build, interactive checks and installation
checks on its target platform. The [consolidation report](docs/CONSOLIDATIE.md)
records the tested baseline, known failures and remaining validation; it is not
a general green build badge. Some historical research results apply only to the
commit and fixtures stated in those reports.

## Files and interoperability

| Format | Role |
|---|---|
| `.ifcxb` | The editor's compact binary IFCX project format |
| `.ifcx` | JSON IFCX exchange and project data |
| `.bim` | Native text representation used by fixtures and development tools |
| `.ifc` | IFC interchange; supported elements can become editable native objects, while other imported geometry can remain read-only |
| `.dxf` | Native reference geometry import; entity coverage is incomplete |
| PDF / SVG | Drawing and sheet output; additional helpers support drawing import |

IFC/IFCX support is evolving and is not a certification claim. The application
cannot yet reconstruct every source drawing or imported object as fully
parametric, editable geometry. Preserve source files when testing round trips.

## Code organisation

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
tests/         Headless tests with expected output, support, fixtures, models
tools/         Test bundler, probes, icon maker, the GPU example
installer/     Linux installer and Windows package scripts and licences
patches/       Compiler patches until they are upstream
lib/           Overrides of the compiler checkout's library (lib/README.md)
scripts/       The Windows build script and the layer check
build.sh       Local build, run, test and installer entry point
docs/          Architecture, decisions, research, notes, coordination and status
.github/workflows/   GitHub Actions workflows
```

`bim_model.dl` holds semantic objects and transactions; `bim_evaluate.dl` derives
geometry; drawing and scene modules produce 2D and 3D representations.
`bim_editor*.dl` implements editing operations, while `bim_ui*.dl` and `main.dl`
connect them to the native interface. The detailed
[module guide](docs/notes/module-guide.md)
provides more context.

The repository began as a research programme. Its
[vision](docs/vision/vision.md), [architecture](docs/architecture/overview.md),
[ADRs](docs/architecture/decisions/) and [research](docs/research/README.md)
remain available. Older plans may predate the current implementation.
The inactive source recovery material that lived under `docs/recovery/` was removed on 2026-10-27; it stays in the history before that date.

## Contributing and reporting issues

1. Start a short task branch from current `main` and claim a bounded task.
2. Keep BIM product changes in DynLex. Develop the compiler in its separate repo.
3. Coordinate changes to shared model, editor, renderer and file-format code.
4. Include a reproducible example, relevant tests and remaining limitations in the PR.
5. Merge back to `main`; remove a completed task branch after verification.

See [CONTRIBUTING.md](CONTRIBUTING.md), the
[two-computer agreement](docs/TWEE-COMPUTERS.md) and [task board](docs/WERKBORD.md).
Repository content and commit messages are written in English.

For an issue, include the application commit/version, OS, GPU/driver when relevant,
steps to reproduce, expected/actual behaviour and a small generic sample model.
Keep private project drawings, customer models, credentials and local toolchain
paths out of the public repository.

## Licensing

Application source files carry MPL-2.0 notices. Dependencies and bundled assets
have their own terms; the DynLex runtime uses LGPL-3.0. Consult each component's
source notices and the [installer licence bundle](installer/licenses/README.txt),
plus the font and icon notices, when redistributing builds.
