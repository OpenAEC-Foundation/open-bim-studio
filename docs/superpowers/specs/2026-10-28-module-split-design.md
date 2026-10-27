# Module split: one module per domain, composed by generated files

Status: catalogue approved by the maintainer on 2026-10-28; design note for the
plan `docs/superpowers/plans/2026-10-28-module-split-plan.md`. It refines §5
(layout) and §10 (sequence) of
`2026-10-27-restructuring-design.md`; the kernel seam of §6 stays as designed
and moves one stage later.

## 1. Intent

Four to six computers develop at the same time, each on its own domain, without
touching the same files. Each developer compiles and runs the tests of one
module in a minute or two. The structure leaves room for what is not built yet.

## 2. Decided by the maintainer

- The catalogue of §4: the modules, their layers and their names.
- The native file format is binary IFCX; the text format of `bim_file.dl` is
  retired after a migration.
- Localised content is data, not DynLex code: the registry reads data files.
- Collaboration is IfcGit: models versioned in git, IFC differences shown and
  merged.
- Building System is called `pattern`, with common, grids and levels.
- API, MCP and HTTP are one module, `automation`; an extension manager is a
  module of its own.
- Structural splits into common, concrete, prefab, steel, timber, rebar and
  results; architectural into common, openings and more; MEP into four.
- Empty modules with an owner are created for what comes later.

## 3. Measured

Why the current units cannot carry parallel streams: every element kind touches
the same files.

| File | Lines | What makes it a hub |
|---|---|---|
| `app/main.dl` | 3,685 | one script of 322 top-level statements; most-changed file in the history |
| `editor/bim_editor_core.dl` | 8,563 | 355 functions, the tools of every element kind |
| `model/bim_model.dl` | 4,406 | 36 record types of every domain; the model record has one list per kind |
| `formats/bim_file.dl` | 1,973 | one writer function for the whole model |
| `app/bim_ui.dl`, `editor/bim_editor.dl`, `editor/bim_editor_properties.dl`, `graphics/bim_scene.dl` | 2,000 to 3,200 each | panels, properties and scene for every kind |

Compile times are not the obstacle any more: on computer 1 (Ryzen 7 9700X, the
pinned compiler) every test program compiles and runs in 1 to 7 minutes and the
application in 12 minutes at `-O2` (issue 11). The compiler is single-threaded;
parallelism comes only from separate programs compiled at once.

Two language facts the composition relies on, verified on 2026-10-28 with the
Windows worktree compiler on three-file programs:

1. A function may call a pattern that a file it does not import defines, as
   long as the program's import closure contains the definition. Resolution is
   per program, not per file.
2. Import cycles compile.

So a service can call a generated dispatcher without importing it, and the
import-direction check stays a check on `import` lines.

A third fact, met in phase B: `local function` makes a function private to
its file. A module's helpers stay `local`; what it offers other modules and
the dispatchers is its public patterns. Two helpers of the evaluator that
every solid-building module needs (`bim element … needs signature … in …`,
`record bim build … of … signed … in …`) were local and are now public.

## 4. The catalogue

Lines are today's size of the files that move there; "new" means no code yet.
Every layer imports only layers below it; modules in one layer never import
each other, except `elements/*` and `pattern/*`, which disciplines import.

Layer 0, kernel (existing directories, four owner groups):

| Module | Directory | Contents | Lines |
|---|---|---|---|
| kernel-core | `kernel/core` + `kernel/fast` | records, vectors, curves, arena, fast polyhedron, perforations | 5,354 |
| kernel-planar | `kernel/planar` | 2D: triangulation, arrangement, offset, clipping | 5,857 |
| kernel-nurbs | `kernel/nurbs` + `kernel/space` | curves and surfaces | 5,912 |
| kernel-brep | `kernel/brep` + `kernel/acis` | solids, booleans, mesh, sweep; later the library behind the C-ABI seam | 31,754 |

Layer 1, BIM core:

| Module | Directory | Contents | Lines |
|---|---|---|---|
| bim | `bim/` | document, element identity, psets, settings, index, journal, undo, phases; the model record is generated from the modules (§5) | 4,665 |

Layer 2, services that elements build on:

| Module | Directory | Contents | Lines |
|---|---|---|---|
| viewer | `viewer/` | Vulkan, scene, instances, section caps, clash, canvas, shaders | 6,922 |
| native format | `exchange/ifcx` | binary IFCX as the native file; `bim_file.dl` (1,973) and its readings retire after the migration | 5,263 |
| ifc | `ifc/` | IFC schema, STEP reading and writing, psets, promote, native types | 4,269 |
| dxf and dwg | `exchange/dxf_dwg` | DXF and DWG reading and writing; today the DXF reference only | 719 |
| step | `exchange/step` | STEP | 690 |
| import | `exchange/import` | drawing and image import, vector underlays, caches, the Python helpers | 972 |
| views | `views/common` | view definitions, hiding, crop, section box | 1,297 |
| drawings | `views/drawings` | drawing standard, drawing rules, plan presentation, text | 1,875 |
| sheets | `views/sheets` | sheets, paper, renderer, workspace, cache | 723 |
| schedules | `views/schedules` | schedules | 344 |
| export | `views/export` | SVG, PDF | 208 |
| materials | `materials/` | section materials, hatches, library | 641 |
| localisation | `localisation/registry` + `localisation/nl` | the registry reads data files at start; NL: NEN 47, NEN 2580, doors, steel and stair sizes, system recipes, NL template, today code spread over twelve files. Author's call on formats: libraries as IFCX, standards and settings as JSON | new |
| automation | `automation/` | API, MCP, HTTP | 853 |
| extensions | `extensions/` | extension manager: content packs, locale packs, external tools through the API (author's reading) | new |
| collaborate | `collaborate/` | IfcGit | new |
| editor | `ui/editor` | selection, undo, snapping, sketch, point input, modify, the tool base | 12,046 |

Layer 3, shape classes and pattern:

| Module | Directory | Contents | Lines |
|---|---|---|---|
| linear | `elements/linear` | beam, column, duct, frame; profiles; the linear records of `bim_model.dl` | 406 |
| connection | `elements/connection` | connections, connection geometry, fastener detail | 671 |
| planar | `elements/planar` | wall, slab, roof, masonry, wall side, roof forms | 3,053 |
| object | `elements/object` | the free parametric object: component | 184 |
| pattern common | `pattern/common` | pattern record, pattern types, identity, recipes | 332 |
| pattern grids | `pattern/grids` | grids, grid controls | 376 |
| pattern levels | `pattern/levels` | levels (today in `bim_model.dl`) | new |
| pattern facade | `pattern/facade` | curtain walls, window recipes (author's call) | new |

Layer 4, disciplines:

| Module | Directory | Contents | Lines |
|---|---|---|---|
| structural common | `structural/common` | shared structural concepts | new |
| concrete | `structural/concrete` | in-situ concrete | new |
| prefab | `structural/prefab` | precast concrete | new |
| steel | `structural/steel` | steel profiles, base plate, steel connections and the steel hall of `feature/connection-module` (3,141 lines) | 135 + 3,141 |
| timber | `structural/timber` | timber and light-gauge steel framing | new |
| rebar | `structural/rebar` | reinforcement, bending schedules, reinforcement drawings | 1,309 |
| results | `structural/results` | calculation results; model checks (author's call) | 152 |
| architectural common | `architectural/common` | shared architectural concepts | new |
| openings | `architectural/openings` | windows, doors, openings, window placement | 363 |
| stairs | `architectural/stairs` | stairs, railings | 2,085 |
| spaces | `architectural/spaces` | spaces, area rules | 307 |
| mep common | `mep/common` | networks | 551 |
| hvac, piping, electrical | `mep/hvac`, `mep/piping`, `mep/electrical` | the four MEP parts (author's call on the names) | new |

Layer 5, UI on top:

| Module | Directory | Contents | Lines |
|---|---|---|---|
| properties | `ui/properties` | properties panel, pset editor, type manager, type menu, labels | 3,521 |
| panels | `ui/panels` | main UI, layout, model explorer, 3D panel, plan panel, tabs | 9,868 |
| projects | `ui/projects` | start screen, project browser, recent projects, templates, project settings, open and save (today `bim_app_files`, `bim_ui_files`, `bim_project_settings`) | 1,225 |
| shell | `ui/shell` | `main.dl`, app parts, loading, window styles, icon, demo pavilion | 5,991 |

Room for what comes, as empty modules with an owner: `architectural/finishes`,
`architectural/furniture`, `site/` (terrain, survey, point clouds,
georeferencing), `infra/` (cable and pipe routes), `quantities/`, `planning/`
(4D), `analysis/`.

Unchanged: `platform/`, `tools/`, `installer/`, `scripts/`, `lib/`, `patches/`,
`generated/`, `docs/`. All 136 product files and all 224 test programs have a
module; tests move to `<module>/tests/`.

## 5. Composition: generated, never hand-edited

DynLex has no function values, so modules cannot register themselves at run
time. Composition is static and generated, the way `generated/self_test.dl`
already works:

- Every module has a manifest, `MODULE` (plain text, one `key: value` per
  line): `name`, `layer`, `depends`, `records` (the file that defines its
  record types), `value` (a scalar the model carries, with its initial
  value), `store` (a list the snapshot clones), `shared` (a list the snapshot
  shares, such as the journal) and `point: <name> <file>` for each extension
  point it implements. Phase B's `bim/MODULE` and `elements/planar/MODULE`
  are the first two.
- `build.sh generate` runs `tools/compose_modules.py` (Python until the tooling
  stage ports it to DynLex), which writes two ignored files:
  `generated/model.dl`, the `bim model record` with one list per module store,
  importing each module's `records.dl`; and `generated/compose.dl`, one
  dispatcher per extension point that calls each implementing module's pattern
  in layer order.
- Extension points, first set: evaluation, voids (what cuts an element: openings,
  penetrations), native write and read, IFC write and read, scene meshes, plan
  lines, tools, properties, menu entries, API elements, checks, content
  registration. A module implements a point by defining the pattern with its
  own name as a literal word, for example `update bim evaluation {target} with
  planar elements of {model}`.
- Services (`bim`, `exchange/ifcx`, `ifc`, `viewer`, `views/*`, `ui/*`) call the
  dispatchers without importing `generated/` (fact 1 of §3). Programs import
  `generated/model.dl` and `generated/compose.dl` and the modules they use.
- Tool and command codes: each module owns a range (author's call: a hundred
  per module, assigned in the manifest); the reserved codes of the work board
  keep their values.
- A module test imports the generated files and its own module; the closure
  then holds every module's records (plain definitions, cheap: 29k lines of
  kernel definitions compile in 12 s) but only the functions it calls.

## 6. Ownership and the way of working

- One owner per module, in `CODEOWNERS` and in `docs/OWNERS.md`; the work
  board's claims become that table.
- Branches `mod/<module>/<topic>`; a pull request that touches one module is
  merged by its owner; a change to `bim/`, to a service's API or to the
  composition rules is its own pull request, merged before the modules that
  need it.
- `scripts/check-layers.sh` becomes the module rule: layer order, no sibling
  imports, `generated/` importable only by programs. A test fails on a
  violation.
- `build.sh test <module>` compiles and runs `<module>/tests/*.dl`, `BIM_JOBS`
  at once; CI runs a matrix over modules on Linux and the integration build
  on `main`.

## 7. Compile time, honestly

| What | Now | After the split | After the kernel seam | After more units |
|---|---|---|---|---|
| one module's tests | 1 to 7 min each, parallel | the same, with smaller closures | model-level ones about halved | the same |
| the application | 12 min at `-O2`, one thread | the same, one thread | two units in parallel, roughly halved | one process per unit |

The split gives parallel streams and fast module loops; it does not make one
program compile on more threads. That takes separate compile units (the seam of
the restructuring design, kernel first) and, for the frontend, caching in the
compiler, which stays the upstream request.

## 8. Sequence

Stage 2 of the restructuring becomes the module split (the plan's phases B to
D); the kernel seam becomes stage 3; localisation as data, the IFCX native
format and IfcGit are module owners' work from stage 2 onward; the tooling
stage is unchanged. An ADR records the module structure once the split lands.

## 9. Left to the builder

The manifest syntax; the exact dispatcher signatures; the tool code ranges;
the data formats of the localisation module; the order of moves inside the
freeze; the ADR text.

## 10. Risks

- The generated model record changes how undo copies the model: it must stay a
  value copy of the whole record. Phase B proves it on two modules.
- The voids point inverts a dependency (planar asks what cuts it); if the
  dispatcher cannot express a case, the fallback is an explicit import from
  the discipline module, recorded as an exception.
- The move is large; it runs under a freeze like stage 1, after stage 1 has
  merged, and `feature/connection-module` is rebased onto it by its author.
- A DWG reader does not exist yet; `exchange/dxf_dwg` starts with DXF.
