# Open BIM Studio — application and toolchain notes

For the current overview and quick start, read the [repository README](../../README.md).
The experiment described below is retained as architectural background.

The editor built from this spike is called **Open BIM Studio**: its window,
installer, command (`open-bim-studio`), menu entry and default file
(`open-bim-studio.ifcx`) carry that name. The spike's directories and DynLex
module paths (`examples/bim-slice/...`) keep their working name.

The native window frame follows the app's appearance setting. On the shipped
Linux/X11 backend, Dark requests a dark decoration and Light restores the window
manager's default; support depends on the desktop theme. Windows uses the native
DWM preference and preserves High Contrast. The title bar keeps its native
window controls. Windows builds stage `platform/windows/bim_window_style.dl`
over the Linux module; the Windows CI build script performs this step.

**Question.** Does the chain the roadmap names as the architectural risk —
*parametric → geometry → 2D → IFC, with changes propagating* — work end to end in
DynLex on the native `cadkernel` port, with stable identifiers, semantic
references and undo, and is a change re-evaluated fast enough to follow a gesture?

**Scope** — the vertical slice of `docs/domain/capability-inventory.md`, thin in breadth:

| Capability | In this spike |
|---|---|
| Level | one storey with elevation and height |
| Type/occurrence | wall types (compound layers) and opening types, occurrences reference them |
| Straight compound wall | walls on centrelines, thickness from the type's layers |
| Wall junctions | L and T joins resolved from shared end points |
| Hosted opening | an opening hosted on a wall by distance along it, voiding the wall |
| Formulas, evaluation, propagation | opening type parameters with derived values; a change re-evaluates only the dependent elements |
| Stable identifiers | 64-bit ids, never reused; deterministic IFC GlobalIds derived from them |
| Undo | every change is a transaction; unlimited undo/redo |
| Plan and section, cut-face fill | kernel plane slices of the evaluated solids |
| Associative dimension | references to semantic features (a wall side, an opening edge), never to derived topology |
| IFC export | IFC4: spatial structure, wall/opening types and occurrences, voids, extruded bodies |
| Snapping | end point, mid point, horizontal/vertical alignment and grid inference in the plan editor |

The table above describes the original experiment. The editor has since grown
multiple levels, IFC import, GPU instancing, component libraries, reinforcement,
connections and drawing sheets. Large-model acceptance criteria (R-12, R-20)
remain separate work; their presence in the editor does not establish scale.

### Reinforcement display

The 3D view defaults to reinforcement centre lines. Bars, stirrups, cages and
meshes keep their model parameters, but their display does not generate round
solids. The native GPU buffer retains the line geometry during camera movement.
Open the 3D view's **Graphics** menu and enable **Rebar with diameter** to inspect
round bars. Changing this option regenerates the display geometry; it does not
change model parameters or the solid reinforcement used for IFCX export.

The lines are depth-tested: concrete in front of reinforcement hides it. Hide
the host or use a suitable section box to inspect the cage. A click near a
visible line selects its reinforcement object. The display uses one-pixel
lines; it does not represent bar diameter in line mode.

Plan grid heads can be selected even where a beam lies on the grid line.
Selecting a curtain-wall mullion or transom highlights the member's profile
edges instead of highlighting the entire curtain wall.

**Layout.** The DynLex code is kept here as an overlay on a DynLex checkout (the
`cadkernel` fork with a built compiler):
- `overlay/examples/bim-slice/` — the slice and the editor grown from it:
  `bim_model.dl` (semantic model and transactions), `bim_index.dl` (spatial index of
  wall joins), `bim_evaluate.dl` (geometry through the kernel, incremental),
  `bim_drawing.dl` (plan, section, dimensions), `bim_ifc.dl` (IFC4 export),
  `bim_ifcx.dl` and `bim_ifcx_read.dl` (IFC5 export and import), `bim_editor.dl`
  (editor core), `bim_ui.dl` (ribbon and panels), `bim_ui_files.dl` (start screen, File
  menu, Settings and the unsaved-changes dialog), `bim_pavilion_drawings.dl` (the
  demonstration pavilion's plan, sections, elevation and A2 sheets; `main.dl --pavilion
  --export-sheets` writes every sheet as SVG and PDF), `main.dl` (the editor). Headless tests,
  timing programs and the GUI driver are in `tests/`. IFC4 output is checked with
  IfcOpenShell; IFC5 output with an independent composition in Python.
- `overlay/lib/fastkernel/` — direct polyhedral walls and prisms.
- `overlay/lib/vulkan/` — the GPU layer in DynLex (Vulkan and GLFW), and its shader
  sources in `lib/vulkan/shaders/`.
- `overlay/examples/gpu/` — the first GPU-resident view.
- `patches/lib-json-public-parse.patch` — a public parse entry for DynLex's
  `lib/json.dl`, applied by the build.
- `patches/dynlex-shader-extensions.patch` — the compiler extensions the shaders need
  (vertex attributes, sampling). Applied to a compiler checkout, they let the
  shaders be rebuilt. `shaders/` holds the SPIR-V they compile to, so the editor
  builds without them.
- `overlay/lib/cadkernel/` — the kernel modules the slice uses that differ from DynLex
  commit `bc653ad` (OpenAEC-Foundation/dynlex): the plane section and its loops, the
  constrained triangulation, robust predicates, reference-counted topology lists and
  operation tolerances, which that commit lacks, and the modules the native kernel port
  had changed since. They are DynLex's own sources (LGPL-3.0, as DynLex), kept here so the
  build is reproducible from a clean checkout of that commit.

**The compiler.** The editor was built with a DynLex compiler from commit `bc653ad`
with `patches/dynlex-compiler-local.patch` applied (numeric literal parsing and function
inference changes made locally on top of that commit). Build the compiler from a clean
checkout as DynLex's own README describes, after:

```
git -C $DYNLEX_ROOT checkout bc653ad
git -C $DYNLEX_ROOT apply $PWD/patches/dynlex-compiler-local.patch
```

`patches/dynlex-shader-extensions.patch` is needed only to rebuild the shaders.

**Local fork selection.** Put the absolute path to the local DynLex fork in
`.dynlex-root.local` (one line, no quotes). This machine-local file is ignored by
Git. An explicit `DYNLEX_ROOT` overrides it. Both the compiler and `lib/` come from
the selected checkout. `bash ./build.sh toolchain-info` prints the resolved paths,
binary hash and source revision without staging files or starting a compilation.
Editing compiler source does not update its binary; a compiler rebuild must be
scheduled separately. The source revision alone is not binary provenance.

**How to run.** Select a checkout with its compiler built at `build/dynlex`, then:

```
./build.sh app             # the editor, optimised, in build/open-bim-studio
./build.sh run --example   # open the example building (or a .bim file, or --import FILE...)
./build.sh test            # every headless test; or ./build.sh test sketch ifcx ...
./build.sh dev             # unoptimised with debug information
```

The build assembles `build/tree` (ignored by git) from the checkout's `lib/`, this
overlay, the patch and the shaders; the checkout itself is not changed.
`overlay/examples/bim-slice/README.md` describes the editor's keys and the test programs.

**Status:** run. See `FINDINGS.md` for the measurements.

**Drawing references and crop editing.** `CV` creates a plan crop. In Select,
its corner and side handles resize it; selecting a handle also reveals a centre
handle for moving the whole crop. Release commits one undoable change; Escape
cancels. `UC` removes the crop. Native annotation text keeps its screen size when
zooming the model; exported text uses paper units. An element property
`OpenBIM_Annotation.Text` overrides its tag text (for example, a window mark);
clearing that property restores the normal type label.

Views can carry registered source artwork in `OpenBIM_VectorTriangles`
properties: each ordered value is RGB followed by model-space triangle corners.
This read-only drawing reference is retained in native files and rendered in 2D,
not evaluated as model geometry. A sheet property
`OpenBIM_Drawing.SourceArtwork=true` omits the generated sheet frame and view
captions when the reference already includes them. Source artwork does not
update when building objects change; outlined source lettering scales with the
reference, unlike native annotation text.

`patches/lib-json-bounded-string.patch` bounds each decoded JSON string's
allocation by that string's encoded length. It is applied only to the staged
build tree. The `json_text_storage` regression parses an 8 MB document with
2,000 text values and exercises escaped quotes, Unicode and invalid input.

### Measuring interactive plan performance

`dev` and `dev-test` default to `-O0`. Keep compiler and optimization level the
same when measuring the effect of source changes. A combined app/self-test build:

```sh
BIM_DEBUG=0 BIM_BUILD_DIR=/tmp/obs-plan-profile \
  bash build.sh dev-test sheet_cache import_metadata_cache
OBS_PROFILE_FRAMES=1 BIM_BUILD_DIR=/tmp/obs-plan-profile \
  bash build.sh run-dev /absolute/path/to/model.ifcxb
```

`BIM_DYNLEX_COMPILER` optionally selects an absolute executable path for isolated
compiler candidates while `DYNLEX_ROOT` continues to select matching libraries.
`build.sh toolchain-info` reports the actual selected binary and its hash.

`BIM_DEV_OPT_LEVEL` accepts `0`, `1` or `2` and affects only development targets.
`BIM_DEV_OPT_LEVEL=2` enables optimization when the machine has enough build
memory; the local 16 GB optimized attempt reached its memory guard. The opt-in
frame diagnostics go to stdout; keep them disabled for normal use.
See [the plan performance investigation](PLAN-PERFORMANCE.md) for stage definitions,
reference-artwork costs, object semantics and measurement limits.

The current development work on image references, interactive sheet viewports,
and compact view tabs is tracked in [SHEET-WORKSPACE.md](SHEET-WORKSPACE.md),
including supported operations and remaining validation work.
