# Restructuring: one tree, one compiler line, compile units with a kernel seam

Status: design, 2026-10-27. Written for the builder who plans the work; the
maintainer decided the points in §2 and the rest is this document's proposal.

## 1. Intent

Open BIM Studio is one DynLex program of about 102,000 lines compiled as a
single unit. The compiler's cost grows superlinearly with unit size, so every
application build takes 40 to 51 minutes at `-O2`, every headless test 3 to 18
minutes, and one test program has peaked at 9.6 GB of compiler memory. The
kernel source exists in four places, the compiler fork has two diverged lines,
and the application lives under a historical `spikes/` path in 111 flat files
with 16 loose notes. The maintainer wants a tool that is future-proof and can be
developed very fast; that requires a structure where a change compiles in
minutes, the kernel has one home, and country-specific content does not live
inside generic code.

## 2. Decided by the maintainer

1. **One language.** DynLex for the application, the kernel and the product
   tooling. Exceptions are listed in §7 and are closed, not open-ended.
2. **Generic versus localised content are separated.** The kernel and model
   know concepts (a drawing standard, a type library, an area rule, a template);
   `content/` supplies the instances per market.
3. **Compile units joined by C-ABI seams**, the kernel first.
4. **The kernel source moves to this repository under `kernel/`.** The DynLex
   fork keeps the compiler and the generic standard library only.

## 3. Current state (measured 2026-10-27 unless dated otherwise)

Sizes of the import closure of `main.dl` (overlay over the fork's
`codex/cadkernel-port` tree): 180 files, 101,871 lines, of which 67,362
application, 27,799 `lib/cadkernel`, 2,615 `lib/vulkan`, 1,431 `lib/fastkernel`,
2,664 standard library. Only two files exceed 5,000 lines
(`bim_editor_core.dl` 8,563; `brep_mesh.dl` 5,378).

Compile cost, as recorded in `spikes/dynlex-bim-slice/FINDINGS.md`, risk R-18 and
dynlex issue 13: 20k lines in 72 s and 50k lines in 1,147 s (R-18, exponent
about 3); the application 40 to 51 minutes at `-O2`; `tests/ifc_read.dl` 13 to
18 minutes at `-O0`; one editor test peaking at 9.6 GB (issue 13, fixed on the
fork since 2026-10-16). The compiler is single-threaded.

Test set: 231 test programs, 220 with expected output, each compiling its own
closure (the editor tests about 71,000 lines each).

Copies of the kernel:

| Where | What |
|---|---|
| fork `codex/cadkernel-port`, `lib/cadkernel/` | 124 files; the port's home; last kernel commit 2026-09-24 |
| fork `master`, `lib/bim/` | a 63-file subset extracted from PR 8 with small integration fixes against the port (6 to 18 lines per file, made so it compiles under `master`'s precedence rules), merged 2026-10-23 (PR 12) |
| this repository, `spikes/dynlex-bim-slice/overlay/lib/cadkernel/` | 27 files: 21 override port files (42,870 differing lines) and 6 exist only here (`brep_section`, `operation_tolerance`, `robust2`, `section_loops`, `spade_cdt2`, `topology_list`); the fast kernel (4 files) and the Vulkan layer (5 files, 12 shader sources) exist only here. This is the kernel the application actually compiles |
| the v0.1 source snapshot | the tarball both Windows workflows unpack; its fork commit is not recorded, only a checksum |
| local checkouts | the Windows checkout of the fork is at 2026-09-07 and 2026-09-24 |

The fork's kernel tests are not one set: `tests/cadkernel` holds 351 DynLex
programs, 126 Python verifiers and 122 Rust reference programs pinned to the
upstream Rust crate; the runnable fixtures are the 214 directories
`tests/required/cadkernel_*`, driven by `tests/cadkernel/verify.py`.

Compiler lines in the fork: `master` (2026-10-26) has the compile-time
optimisations, `--incremental`, `--emit-object`, scope rules and the issue-13
fix, and no `lib/cadkernel`. `codex/cadkernel-port` (2026-10-23) has the
kernel and the issue-13 fix and none of the speed work. Three compiler commits
exist only on the port (`ea793094` variable storage, `8e321958` expression
grouping, `42a88886` compute dispatch). Six compiler patches live in
`spikes/dynlex-bim-slice/patches/`; at least two (`pattern-reference-index`,
`windows-compiler-stack`) are not on `master`. Two `lib/json.dl` patches are
applied at build time.

The application imports seven generic library files (`std`, `text`, `list`,
`string`, `sort`, `json`, `atomic`); all exist on both fork lines.

Branches in this repository: `origin/main` (2026-10-27) is the baseline.
Open: `fix/windows-app-compile` (PR 7, four commits ahead), and 90 files /
9,301 lines of canvas-editing work that are staged but uncommitted on one
machine. Already contained in `origin/main`: `feature/steel-baseplates`,
`feature/roof-forms-and-dimensions` and twelve older branches. Stale with
unmerged content: `spike/bim-slice-linear-members` (three commits, 2026-10-09)
and `codex/dynedra-dwg-viewer` (three commits, 2026-09-24). PR 2 is open but
its branch is merged.

What the application takes from the kernel (exact pattern match of the
kernel's 1,437 public patterns against the application sources): 161 patterns,
of which the great majority are vector arithmetic and list operations on
topology lists. The heavy operations are few: extrusion, sphere and cylinder
bodies, faceted solids from polyhedra, boolean combination, placement, mass
properties, bounds, plane slice, plane section, wireframe, body mesh, face keys
and bounded face edges, 2D triangulation, and arrangement of tagged lines. The
fast kernel (prisms, walls, curved walls, polyhedra, 1,431 lines) is called
directly and its polyhedra are read field by field by the scene, the file
writers and the editor.

The `--emit-object --no-main` mode with `exposed function` exists on both fork
lines (commit `f54f8475`, verified by `scripts/test_object_output.py`): a
definition-only library becomes a native object; exposed functions get
external linkage and C-ABI scalar attributes; everything else is internal, so
two units that both contain `lib/std.dl` do not clash. The symbol name is the
pattern text plus `_callable` plus the argument types, encoded; the consumer
calls it with `@intrinsic("call", "<library>", "<symbol>", <return type>,
arguments...)`, the way `obs_platform` is called today.

Import resolution (fork `master`, `compiler.cpp`): the importing file's
directory, then that file's resolution root, then the working directory, then
the compiler's own source tree (`PROJECT_SOURCE_DIR`), then `/usr/share/dynlex`.
A program compiled from this repository's root therefore finds `model/x.dl`
here and `lib/std.dl` in the fork checkout without any tree assembly, and a
file placed at `lib/json.dl` here shadows the fork's.

Localised content today sits inside generic modules: the NL door library, the
NEN 47 drawing standard and Dutch material names in `bim_model.dl`; Dutch
standard sizes and the Reynaers recipes in `bim_system_types.dl`; the Dutch
steel library in `reinforcement_library.dl`; Dutch stairs in
`bim_stair_types.dl`; NEN 2580 area rules in `bim_spaces.dl` and the plan panel;
NEN 47 hatches in `bim_hatch.dl`; the NL template in `bim_app_files.dl`.

## 4. Goals, non-goals, anti-goals

Goals:

- A change to application code compiles without recompiling the kernel; the
  kernel compiles once per kernel change and is cached.
- Units compile as separate compiler processes, so a build uses several cores
  and no single process needs the memory of the whole program.
- The kernel has one authoritative source tree, with its tests and notes.
- The repository layout names the units; a new contributor finds model, kernel,
  formats, graphics, editor, app and content without reading history.
- National content is added or changed without touching generic code.
- The compiler fork has one line; this repository carries no compiler patches.

Non-goals (this design does not do them, later designs may):

- Splitting model, formats, editor or UI into their own units. The layout
  prepares for it; the seam work here is the kernel only.
- A DynLex module system with typed interfaces. That is compiler work, and the
  only route to units of a few thousand lines; it is requested upstream, not
  built here.
- Renaming files or patterns. Directories change; file names and the natural
  language patterns inside the code do not.
- Any behaviour change in the editor. The restructured program must pass the
  same tests with the same expected output.

Anti-goals (this would be failure even if it compiled):

- A fifth copy of the kernel, or a period in which two copies are both edited.
- A seam that forces per-vertex or per-vector calls across the ABI; vector
  arithmetic stays source-shared.
- Losing the uncommitted canvas-editing work or any open branch content.
- Breaking the Linux release build while adding the new structure.

## 5. Target layout

> Superseded on 2026-10-28 by the module layout of
> `2026-10-28-module-split-design.md` §4; the layering below describes stage 1
> and stays as the record of that stage.

```
open-bim-studio/
  kernel/
    core/        shared source, compiled into every unit: vectors, planes,
                 transforms, frames, angles, bounds, 2D curves, tolerance,
                 topology lists, arena keys (about 3,500 lines)
    brep/        topology, make, place, append, boolean, split, sweep, slice,
                 section, imprint, classify, bounds, geometry, pcurves,
                 intersect, loft, mass, blend, press-pull, thicken, revolve, shell
    nurbs/       nurbs2, nurbs3, builder, spline, knot compaction, arclength
    planar/      triangulate2, constrained2, spade_cdt2, robust2, arrangement2,
                 band2, section loops, tessellation, polyline2, offset2, clip2
    acis/        SAT/SAB reading and history reconstruction (not yet used by
                 the application; compiled into the library, no seam needed)
    fast/        the fast kernel: shared source, compiled with the application
    api/         exposed.dl (the library's entry and exposed functions),
                 types.dl (result records shared by both sides),
                 client.dl (generated natural-language wrappers)
    tests/       the DynLex fixtures with expected output (tests/required/
                 cadkernel_* and tests/cadkernel/*.dl), run by a DynLex runner
    reference/   the Rust reference programs and their Python verifiers: the
                 external oracle the port was proved against (§7), not run by
                 default
    docs/        the fork's cadkernel-*.md notes (16 files)
  model/         semantic model, index, evaluation, systems, stairs, network,
                 reinforcement, connections, spaces, types, settings, checks
  formats/       bim file, IFC, IFCX and binary IFCX, STEP, DXF reference,
                 PDF, SVG, images, vector data, import and caches
  graphics/      vulkan/ (the overlay's five files), shaders/ (DynLex sources
                 and prebuilt SPIR-V), text, canvas, icon, and one window
                 style module per OS (window_style_linux.dl,
                 window_style_windows.dl)
  editor/        editor core, properties, psets, sketch, modify, type manager,
                 grid controls, section box, pick, crop, model explorer, files
  app/           main.dl, UI, layout, plan and view panels, app parts, sheets,
                 workspace tabs, loading
  automation/    the request/response API and the MCP and HTTP adapters (DynLex)
  content/
    common/      international template and basic types; the framework
                 instances that are not national
    nl/          NL doors, NEN 47 standard and hatches, NEN 2580 rules, Dutch
                 steel and profile library, Dutch stairs, Dutch system sizes,
                 Reynaers recipes, NL template
  platform/      obs_platform.c, the per-OS C shim (the one sanctioned C file)
  tools/         DynLex tools: kernel client generator, test bundler, icon maker
  tests/         application tests, expected output, support, fixtures
  installer/     installer assets and package scripts
  lib/           temporary overrides of fork library files, each tied to an
                 open upstream PR; empty is the goal
  generated/     the only generated DynLex sources (ignored, written by
                 build.sh generate), see §6.5
  scripts/       the Windows build script; build.sh and toolchain.sh stay at
                 the root as the entry points
  docs/          as today, plus notes/ for the spike notes and two new ADRs
  .github/workflows/   the single place for CI; no copies under ci/
```

`spikes/dynlex-bim-slice` is removed; the research spikes beside it stay as
they are. The directory names are the unit names. The dependency
direction is `app → editor → graphics/formats → model → kernel`, and
`app → content → model`: the application imports `content/index.dl`, content
imports model concepts, and nothing below `app` imports content. `kernel/core`
and `kernel/fast` are importable from anywhere above the kernel. Imports change
from `examples/bim-slice/x.dl` to `model/x.dl` and from `lib/cadkernel/x.dl` to
`kernel/<part>/x.dl`; patterns and file names do not change. The move is one
commit made with `git mv` so history follows the files.

The seed of `kernel/` (author's call): the port at `c2d32bea` (whose kernel
files are those of `bc653ad0`; the later commits touch the compiler only) plus
this repository's 27 overlay files, because that pair is what compiles and
passes the test set today. The `lib/bim` integration fixes are folded in during stage
3, when the kernel first compiles under `master`'s compiler, and the fork commit
behind the v0.1 snapshot is identified and recorded in stage 1 so that the
Windows release is known to build the same kernel.

Known layering violations to repair during the move, so that later unit cuts
are possible: `bim_import`, `bim_ifc` and `bim_ifcx` import `bim_scene` for mesh
labels and storey elevations (move those two helpers down to model);
`bim_steel_profiles` imports `bim_file` (move the file helper it needs into
model or formats); `bim_clash` imports `bim_scene`; `bim_section_gpu` imports
`bim_view_panel`; `bim_drawing_rules` and `bim_images` import `bim_editor`. The
editor-to-UI imports (nine edges) are left; editor and app are one unit.

## 6. The kernel seam

### 6.1 Units

- `kernel/brep`, `kernel/nurbs`, `kernel/planar` and `kernel/acis` compile once
  into the static library `obskernel` (`libobskernel.a`) from
  `kernel/api/exposed.dl` with `--emit-object --no-main -O2`.
- `kernel/core`, `kernel/fast` and `kernel/api/types.dl` are shared source: they
  are imported by the library and by every program that uses the kernel. They
  contain only plain-data records, vector and curve arithmetic, the topology
  list type, the fast kernel, and the result records of §6.3. They carry no
  B-rep algorithm.
- The application, the test programs and the tools import `kernel/api/client.dl`
  and the shared source, never `kernel/brep`, `kernel/nurbs`, `kernel/planar`
  or `kernel/acis`. A test that checks this import rule is part of the test set.

### 6.2 What crosses the seam

Every exposed parameter and every return value is a scalar or a pointer. That
is the part of the `exposed` and `@intrinsic("call")` path the compiler
verifies today (`scripts/test_object_output.py`, `applyNativeScalarABI`); no
aggregate crosses by value in either direction, so the seam needs no compiler
change.

| Kind | How it crosses | Examples |
|---|---|---|
| Scalars | by value | counts, flags, tolerances, parameters, status codes |
| Plain-data records defined in `kernel/core` | by pointer to caller-owned storage, in and out | `cad vector3`, `cad plane`, `cad placement`, `cad key`, `cad tolerance` |
| Lists of plain data | pointer to the first item plus count; never a DynLex list value | polygon loops, tagged lines for arrangement, polyhedron positions |
| Bodies | opaque: the library keeps a `cad body` boxed on the heap and hands out a pointer; the application holds it in a managed class `kernel body` whose retain and release call exposed library functions | every solid in `bim solid record`, `bim element geometry record` and component solids |
| Managed result records | the record's class definition moves to `kernel/api/types.dl`, so both units compile the same layout and the same retain/release code; the callee writes a retained value through a caller-provided pointer | `cad mesh` (positions, normals, triangles), wireframes, section and slice polylines, mass properties |

Lists inside shared result records are ordinary compiler lists backed by
`malloc`; both units link the same C runtime, so a release in one unit of
memory allocated in the other is sound. The round-trip test of §14 proves the
shared-layout assumption for `cad mesh` before anything else is built on it.

### 6.3 Exposed functions, first version

Derived from the measured usage in §3. Lifecycle: body retain, body release.
Construction: extrusion of loops along a direction, sphere body, cylinder body,
faceted solid from a polyhedron, combination of two bodies by kind (union,
difference, intersection), body placed by a placement. Queries: mass
properties, bounds, face keys of a body, bounded face edges of a face, plane
slice, plane section, wireframe, body mesh at a tessellation tolerance.
Planar: triangulation of loops, arrangement of tagged lines into regions.
About twenty functions. Every exposed function takes and returns only the
kinds of §6.2 and has one pattern path and concrete types, which is what the
compiler requires of `exposed`.

The exposed patterns keep the kernel's existing natural-language form wherever
the types allow it, so that `kernel/api/client.dl` offers the same sentences
the application already uses; call sites then change only where a value's type
changes from `cad body` to `kernel body`.

### 6.4 The generated client

`tools/kernel_client.dl` reads `kernel/api/exposed.dl` and writes
`kernel/api/client.dl`: for every exposed function, a function with the same
pattern whose body is the `@intrinsic("call", "obskernel", "<symbol>", ...)`
with the same types. The symbol is the compiler's: the pattern text plus
`_callable` plus each argument type's name, encoded as the compiler encodes
them (`codegenTypes.cpp`, `getPatternFunctionName`; `codegenInternal.h`,
`encodeLLVMNameComponent`). A test compiles a three-function library with
`--emit-object`, generates its client, links a program against it and runs it,
so a mangling mismatch fails at link time, never at run time. The generated
file is committed; the test also checks it is current.

Requested upstream, not required: a compiler option that writes the exposed
symbols and their signatures as a manifest, or an explicit symbol clause on
`exposed function`. Either retires the mangling code in the generator.

### 6.5 Build

- `build.sh kernel` compiles the library into `build/kernel/` and archives it;
  the cache key is the hash of `kernel/**`, the compiler binary and the flags.
  `build.sh app`, `dev`, `test` and `probe` run `kernel` first and link with the
  library name `obskernel`, exactly as `obs_platform` is linked today
  (`LIBRARY_PATH` on Linux; the dependency `lib` folder on Windows).
- Compiles of independent targets run as separate processes; `build.sh test`
  runs up to `BIM_JOBS` tests at once (default: the smaller of the core count
  and the memory budget divided by the largest test's measured peak).
- The compiler runs from the repository root with the program path; there is
  no staged tree, no overlay, no `rsync`. `lib/` here holds only shadowing
  overrides tied to upstream PRs.
- The compiler is a fork checkout with its compiler built in place, which is
  what `toolchain.sh` already demands: the compiler then finds `lib/` through
  its own source tree. A compiler binary staged elsewhere cannot resolve
  `lib/` and is not a supported configuration until the fork gains a
  library-root option, which stage 3 requests (author's call).
- Stages 1 and 2 pin the port line's tip (`c2d32bea`) with the six patches
  applied, so that the move and the seam change one thing at a time; stage 3
  moves the pin to `master` (author's call). A pin may name any pushed fork
  commit.
- Per-OS and per-build variation never rewrites a committed source. `build.sh
  generate` (and the Windows build script) writes two small files into the
  ignored `generated/` directory: `platform.dl`, which imports the OS's window
  style module, and `self_test.dl`, which defines `run bim app checks` as a
  no-op or, for `dev-test`, as the generated test bundle. `app/main.dl`
  imports both and carries the `--self-test` argument handling permanently.
  Every build command runs `generate` first; a developer invoking the compiler
  by hand runs it once. Behaviour that differs only in which C symbol is
  called goes into `platform/obs_platform.c` (author's call).
- The incremental mode of the fork's `master` (`--incremental <cache>`) is used
  for the application unit in addition; it reuses native partitions, not
  frontend work, so it complements the seam rather than replacing it.
- The Windows workflow builds the kernel library in the same job as the
  platform shim and stages it with the toolchain's libraries.

### 6.6 Expected effect, to be measured

Extrapolated from R-18's curve, not measured: the application unit shrinks
from about 102k to about 76k lines (kernel out, shared core in), which the
exponent puts at roughly 40 % of today's compile time; a model-level test such
as `ifc_read` shrinks from 51k to about 26k lines, roughly one eighth of its
time; the kernel library compiles once at about 29k lines. The measurements in
§11 replace these numbers before any of them is quoted.

## 7. One language: the sanctioned exceptions

- `platform/obs_platform.c`: C, because the symbols differ per operating system
  and DynLex calls them by name. Platform integration only, which includes
  socket plumbing (listen, accept, read, write) when the HTTP adapter needs
  it; protocol logic stays in DynLex. No BIM logic.
- `build.sh`, `toolchain.sh`, the installer scripts and the CI workflows: shell
  and PowerShell.
- External oracles in tests that validate output with an independent
  implementation: the IFC verification scripts (Python) and the kernel's Rust
  reference programs with their Python verifiers under `kernel/reference/`.
  Development only, never shipped, never a product function, not run by
  default and not part of CI; a Rust toolchain is therefore not a CI
  dependency (author's call).

Everything else that is Python today moves to DynLex in `tools/` or
`automation/`: the test bundler, the icon maker, the kernel test runner, the
drawing and mesh import helpers, the HTTP and MCP adapters and their test. That
is stage 5 in §10; until then the Python versions stay where they are and are
not extended. The compiler pattern check belongs to the fork and goes there in
stage 3.

## 8. Generic and localised content

The generic code defines the concepts and a registry each:

- drawing standards (symbols, line work, hatches, level marks) with the
  international standard in `content/common`, NEN 47 in `content/nl`;
- type libraries (doors, stairs, building-system recipes and sizes, steel
  profiles, reinforcement steel) as data files in DynLex, one per market;
- area rules (the NEN 2580 computation becomes an area rule instance);
- model templates (international in common, NL in nl);
- material naming per language.

`content/common/index.dl` and `content/nl/index.dl` each register their
instances; `content/index.dl` imports both and `app/main.dl` imports it. One
executable carries every market; the project setting that today picks the
Dutch or the international template picks the registered content at run time
(author's call). Generic code must not name a country, a national standard or
a vendor; a test greps for that.

## 9. The compiler line

`master` of the fork is the line. The three port-only compiler commits and the
six patches in `spikes/dynlex-bim-slice/patches/` (in the versions this
repository's working tree carries, which are the latest) become pull requests
to `master`, as do the two `lib/json.dl` patches and a request for a
library-root option and an exposed-symbol manifest. The compiler computer makes
these pull requests. This repository pins the fork commit it builds with
(`.dynlex-root.local` locally; the workflow pins the commit, not a release
tarball). When the pinned commit contains them all, the `patches/` directory
and the `lib/` overrides are deleted. Until then the pin may stay on the port
line; stage 3 is simply not done.

Once `kernel/` here is authoritative, `lib/cadkernel` on `codex/cadkernel-port`
and `lib/bim` on `master` must leave the fork, or be marked frozen snapshots
with a pointer here; otherwise the fourth copy stays alive. The fork has other
contributors, so this is an agreement to obtain, not a commit to make.

## 10. Sequence

Each stage is one pull request to `main`, verified before the next starts.

0. **Secure the work.** Commit the staged canvas-editing work as one branch on
   top of `fix/windows-app-compile`, exactly as it is (its workflow, patch and
   MCP changes included; the compiler computer reviews those parts in the pull
   request rather than the work being split while uncommitted; author's call).
   Land PR 7, then that branch; fast-forward every local `main`. Tag and delete
   the merged branches; close PR 2; tag the two stale spikes as archives and
   delete the branches, after confirming nothing in them is still wanted.
1. **Freeze and move.** Claim the whole tree on the work board; no parallel
   branch during this stage. One commit of `git mv` into §5, import rewrite,
   `build.sh` and workflows pointed at the new paths, the overlay and tree
   assembly removed, the generated-file mechanism of §6.5, CLAUDE.md, README
   and roadmap corrected, the spike notes under `docs/notes/`, ADR-0007
   (kernel lives here) and ADR-0008 (compile units with C-ABI seams). Done
   when the full test set passes, the Linux application builds and opens the
   demonstration pavilion, and the Windows workflow builds from the tree.
2. **Kernel seam.** `kernel/api/types.dl` extracted; `exposed.dl`; the
   generator and its link test; the mesh round-trip test; `kernel body` in the
   application; `build.sh kernel` with caching; parallel tests. Done when the
   test set passes against the library and the measurements of §11 are
   recorded.
3. **One compiler line.** Upstream PRs by the compiler computer; the `lib/bim`
   fixes folded into `kernel/`; pin `master`; delete patches and overrides; the
   fork's kernel copies retired by agreement.
4. **Content split.** `content/common` and `content/nl`; registries; the
   country-name test.
5. **Tooling and adapters to DynLex.** Test bundler, kernel test runner, icon
   maker, import helpers, the HTTP and MCP adapters; socket plumbing in the
   shim where needed.
6. **Later, separate designs:** formats and model as units.

Stages 3, 4 and 5 can run in parallel with each other after stage 2.

## 11. Measurements that belong with the work

Before stage 1 and after each stage, on the same machine, recorded in
`docs/notes/build-times.md`: wall time and peak memory of the application at
`-O2` and `-O0`, of `ifc_read`, `editor` and `sketch` tests, of the kernel
library, and of the full test set with the chosen parallelism. The extrapolated
numbers in §6.6 are replaced by these.

## 12. Constraints

- Repository content in English; conversation language does not change what is
  written to disk.
- No names of competing calculation software anywhere; BIM and 3D software may
  be named.
- The two-computer rule: computer 1 owns stage 0 and stage 1 with a freeze
  (§15); stages 2 to 5 are claimed per stage on the work board; compiler PRs
  are the compiler computer's.
- Large binaries stay out of the repository; prebuilt SPIR-V is small and stays.
- The v0.1 Linux release and its workflow must keep building from the tagged
  snapshot; the new workflows build from the tree.

## 13. Left to the builder

- The exact split of `kernel/brep` and `kernel/planar` files into folders, as
  long as `core` stays small and algorithm-free.
- The shape of the exposed function patterns beyond §6.3, the error reporting
  convention across the seam (status codes versus result records), and the
  memory budget heuristic for parallel tests.
- Whether the generator parses `exposed.dl` with the compiler's language server
  or with its own line parser.
- Order of the layering repairs in §5.
- The ADR texts, within the decisions of §2.

## 14. Risks and stop conditions

- Shared-layout assumption: a managed result record crossing by pointer relies
  on both units lowering the same class the same way; the link test of §6.4 and
  a round-trip test of a mesh across the seam must pass before stage 2
  proceeds. If they fail, the fallback is accessor functions over the seam
  (pointer and count per array), which costs functions but no compiler work.
- No inlining across the seam: a hot path that turns out to call the library
  per vertex is a design error to fix by batching, not by moving code back.
- Standard-library drift between the fork lines: the seven imported files exist
  on `master`, but behaviour may differ; stage 3 is done only when the test set
  passes on the pinned `master` compiler.
- If stage 2's measurements show less than a halving of a model-level test's
  compile time, stop and revisit the seam before cutting further units.

## 15. Open with the maintainer

Two questions the builder check raised that only the maintainer can answer;
their answers go here when given.

1. Which computer owns stage 0 and the stage 1 freeze? Stage 1's done criterion
   is a Linux build and a Windows workflow run; the work board gives CI to the
   compiler computer and the application to the other.
   **Answer (maintainer, 2026-10-27): computer 1 does stage 0 and the stage 1
   freeze.** Computer 2 reviews the workflow and patch changes in the stage 0
   and stage 1 pull requests and runs the Windows workflow for stage 1's done
   criterion; it makes no concurrent edits during the freeze.
2. Who merges in the fork, and is a weeks-long wait on the nine upstream pull
   requests acceptable? If not, stage 3 keeps the pin on the port line longer
   and the patches directory stays until the fork catches up.
   **Answer (maintainer, 2026-10-27): a wait of weeks is acceptable; stage 3
   waits for the fork.** Who merges in the fork was not stated; the plan
   assumes the compiler computer opens the pull requests and the fork's
   maintainers merge them, and stages 4 and 5 proceed meanwhile.
