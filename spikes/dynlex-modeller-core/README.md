# Spike — the modeller core: views, categories, snapping, GPU, IFC

**Question.** Can the DynLex BIM slice grow into the core of a modeller that
works the way the maintainer wants to work with BIM? Concretely:
- views whose look follows rules per category;
- grids as model objects;
- visibility per category;
- snapping, tracking and ortho in 2D and 3D, with Blender-like control;
- dimensions;
- wall and floor types;
- a GPU-rendered 3D view;
- an IFC importer that opens large models.

Everything stays in DynLex, with no web stack. Each part below has criteria fixed
before the code, as in `spikes/dynlex-fast-kernel/`.

The intent comes from the maintainer (2026-10-05):
- a drawing or section is of a category, and rules say how it is drawn;
- grids are 3D objects, visible in 3D;
- visibility is set per category, as in Revit;
- object snaps, tracking and ortho in the 2D and 3D views, controlled like Blender;
- temporary and permanent dimensions;
- the wall and floor types of Open 2D Studio, a deprecated project used as
  inspiration for content and way of working;
- a basic UI;
- a large-model test;
- an IFC importer: first through IfcOpenShell, later as DynLex's own IFC library in
  a separate category, on which the Open CAD Studio kernel can build;
- the 3D view rendered by the GPU.

## Baseline

What exists is the BIM slice of `spikes/dynlex-bim-slice/` and
`spikes/dynlex-fast-kernel/`:
- **Model:** walls with layered types, windows, doors, slabs, storeys, spaces and
  dimensions in the model (no tool yet).
- **Evaluation:** incremental with a change journal (34 µs per edit at 99,856 walls).
- **Drawing:**
  - a plan and a section with hatched layers;
  - a 3D view with orbit, pan and zoom, a sun, and cast shadows on a ground plane;
  - selection and handles in every view;
  - a native file format and IFC4 export.
- **Rendering.** The 3D view is transformed on the CPU and streamed to the GPU every
  frame through the DynLex graphics runtime. That runtime is C, about 2,800 lines.
  It has custom DynLex shaders and 32 uniforms, but no persistent vertex buffers
  and no render-to-texture.

## Parts and criteria

The parts are ordered by dependency; each is done when its criteria hold.

### A. Categories, view rules and visibility

- Every element has a category: walls, slabs, doors, windows, grids, spaces,
  dimensions, and later imported IFC classes.
- A view is a plan, section or 3D view with a view template: per category, visible
  or hidden, line colour and weight, cut fill or hatch, and projection style.
- The view properties override the template per category (Revit's Visibility/Graphics).
- **Done when:**
  - hiding a category in a view hides it there only;
  - a test model's plan, section and 3D view draw only what their rules allow;
  - templates are saved in the native file.

### B. Grids

- A grid is a named line in plan with an extent in height. It is drawn in plan and
  section with its bubble and name, and in 3D as a vertical plane outline.
- Grids are snap targets, and walls can follow them later.
- **Done when:**
  - grids are created and edited in the plan;
  - they are visible in all three views, following part A's rules;
  - they are exported as `IfcGrid`;
  - they survive saving.

### C. Snapping, tracking, ortho, Blender-like control

- **Object snaps:** end, middle, intersection, perpendicular, nearest and grid, on
  walls, slabs, grids and dimension lines.
- **Tracking and ortho:** polar or axis tracking from acquired points, ortho
  (Shift or F8), and typed lengths along the tracked direction.
- **In 3D:** snaps on model vertices, edges and faces, with the working plane on the
  active storey.
- **Blender-like control:**
  - middle-drag orbits, Shift+middle pans, the wheel zooms;
  - G, R and S grab, rotate and scale the selection, with X/Y/Z axis constraints and
    typed values;
  - numpad 1, 3 and 7 give front, side and top views, and 5 toggles perspective;
  - H hides and Alt+H unhides;
  - A selects all, and B box-selects;
  - Shift+A adds an element.
- **Done when:**
  - every snap kind and constraint has a headless test;
  - a recorded XTEST session draws, moves and rotates elements in 2D and 3D.

### D. Dimensions

- Temporary dimensions appear on a selected element, to neighbouring references,
  and editing one moves the element.
- Permanent dimensions are model objects, which exist already. They reference
  semantic features and follow edits.
- **Done when:**
  - both kinds work in the plan, with a headless test that edits through a temporary
    dimension;
  - permanent dimensions survive saving and IFC export (as annotation).

### E. GPU-resident 3D rendering

- **Approach.** The rendering path is written in DynLex against `libvulkan`
  directly, through DynLex's C interface: persistent vertex and index buffers per
  element build, and the view transform and lighting in shaders.
- **Shadows.** Real shadows come from a shadow map, which also gives
  self-shadowing. This replaces the C runtime for this path, as the maintainer asked.
- **Done when:**
  - the example house renders identically, with self-shadowing;
  - per-frame CPU time no longer depends on the triangle count;
  - a model of at least 5 million triangles orbits at 60 frames per second on the
    reference machine's GPU;
  - no C remains in the rendering path, beyond `libvulkan`, the window system and
    the driver.

### F. IFC import and the large-model test

- **First step:** IfcOpenShell (0.9) converts an IFC file into element meshes,
  categories and properties, which the modeller opens as imported, read-only elements.
- **Then:** a DynLex IFC library, in its own category (`lib/ifc/`):
  - a STEP parser;
  - the IFC4 schema subset for building elements;
  - placements;
  - extruded, swept, B-rep and boolean geometry, through the fast kernel and the
    `cadkernel` port.
- **Done when:**
  - a large reference IFC file (to be chosen with the maintainer) opens, with the
    time to open, the memory and the frame time measured;
  - the DynLex library reads the same file to the same element count and volumes
    as IfcOpenShell, within a stated tolerance.

#### Large reference models for part F

These are kept outside the repository, in the workspace's `reference-models/`
directory, and are not redistributed. They are measured with IfcOpenShell 0.9.0.

- **HITOS (Tromsø university building), IFC2x3.**
  - Source: <https://raw.githubusercontent.com/opensourceBIM/TestFiles/master/TestData/data/HITOS_070308.ifc>.
    The repository states no licence, so the file is used for local measurement only.
  - Size: 64,095,402 bytes. SHA-256
    `fe339277c7390b4a99d327846e34239e4d853371fac6951e46503ba8faaa2dcf`.
  - 1,100,318 entities and 12,042 products with geometry: 9,203 annotations, 845
    standard-case walls, 519 openings, 363 slabs, 243 spaces, 226 windows, 208
    columns and 198 doors. IfcOpenShell opens it in 2.2 s.
- **Schependomlaan coordination model (Dutch housing project), IFC2x3.**
  - Source: `ROOT-Compleet.ifczip` from
    <https://github.com/buildingsmart-community/Sample-Test-Files> (Schependomlaan,
    BIMsight project data).
  - Permission: "All data owners have given permission to use the data for
    scientific and academic purposes".
  - The archive holds `IFC-gebouw.ifc`: 46,766,968 bytes. SHA-256
    `5c73cdd02b3add09b30cf437eb3fe01bc4631e5a60dbaf30c0b8a7b817585bb4`.
  - 671,548 entities and 3,652 products with geometry: 1,214 coverings, 934 walls,
    279 slabs, 277 element parts, 259 windows and 205 doors. IfcOpenShell opens it
    in 1.5 s.

### G. Types and a basic UI

- **Types.** The wall and floor types of Open 2D Studio (layers, materials, hatch
  patterns per NEN 47) become the modeller's type library.
- **Basic UI:**
  - a project browser (views, storeys);
  - a properties panel;
  - a type selector;
  - a category visibility dialog;
  - a toolbar.
- **Reference for the UI.** It follows the Open CAD Studio UI that a Codex branch
  adapted into an "Open BIM Studio" frontend (`OpenCADStudio/docs/open-bim-ui.md`,
  `src/modules/bim/mod.rs` and `src/ui/bim.rs` in the workspace clone). That branch
  is Rust and `iced`, so here it is rebuilt in DynLex, not linked:
  - the Fusion Black chrome: background `#1A1A1A`, text `#F2F2F2`, accent `#0696D7`,
    with a white model canvas;
  - a ribbon with tabs and groups of large tools: Objects (component, door, window,
    opening), Linear (beam, column, railing), Planar (wall, floor, roof), Systems;
  - a project explorer of 244 pixels on the left: site, building, storeys, grids, and
    views;
  - a properties panel;
  - a command line and a status bar;
  - a model assistant panel at the bottom right.
- **Content.** Types and hatches follow `open-2d-studio-survey.md`.
- **Done when:**
  - all those types are available and drawn correctly;
  - the panels edit the model through the same transactions as the tools.

## Not in scope

- Roofs, stairs, curtain walls and families.
- Collaboration and BCF.
- Choosing between the ADRs, which remains the maintainers' decision.

## Results

To be recorded in `FINDINGS.md` as parts complete.
