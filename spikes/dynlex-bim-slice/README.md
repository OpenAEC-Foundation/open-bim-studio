# Spike — the vertical BIM slice on the native DynLex kernel

The editor built from this spike is called **Open BIM Studio**: its window,
installer, command (`open-bim-studio`), menu entry and default file
(`open-bim-studio.ifcx`) carry that name. The spike's directories and DynLex
module paths (`examples/bim-slice/...`) keep their working name.

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

**Not in scope**: other element kinds, multiple storeys, IFC import, sheets,
scale (R-12, R-20), GPU instancing.

**Layout.** The DynLex code is kept here as an overlay on a DynLex checkout (the
`cadkernel` fork with a built compiler):
- `overlay/examples/bim-slice/` — the slice and the editor grown from it:
  `bim_model.dl` (semantic model and transactions), `bim_index.dl` (spatial index of
  wall joins), `bim_evaluate.dl` (geometry through the kernel, incremental),
  `bim_drawing.dl` (plan, section, dimensions), `bim_ifc.dl` (IFC4 export),
  `bim_ifcx.dl` and `bim_ifcx_read.dl` (IFC5 export and import), `bim_editor.dl`
  (editor core), `bim_ui.dl` (ribbon and panels), `main.dl` (the editor). Headless tests,
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
./build.sh app             # the editor, optimised, in build/bim-slice
./build.sh run --example   # open the example building (or a .bim file, or --import FILE...)
./build.sh test            # every headless test; or ./build.sh test sketch ifcx ...
./build.sh dev             # unoptimised with debug information
```

The build assembles `build/tree` (ignored by git) from the checkout's `lib/`, this
overlay, the patch and the shaders; the checkout itself is not changed.
`overlay/examples/bim-slice/README.md` describes the editor's keys and the test programs.

**Status:** run. See `FINDINGS.md` for the measurements.
