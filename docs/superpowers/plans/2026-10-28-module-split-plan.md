# Module split: the plan, coarse to fine

**Spec:** `docs/superpowers/specs/2026-10-28-module-split-design.md`. Only the
next phase is written in steps; later phases get their steps when they start.

**Constraints:** repository content in English; no competing calculation
software named; the pinned compiler of stage 1 until stage 3; one freeze at a
time; `PROMPTS.md` and `f2.html` are the maintainer's.

## Phases

| Phase | What | Who | Done when |
|---|---|---|---|
| A | Stage 1 merges: Linux results in, PR 10 out of draft, merged, tagged | computer 1 and this one | `main` is the one tree |
| B | Composition spike: manifests, the generator, the generated model record and two dispatchers for `bim` and `elements/planar`, on a branch, no freeze | one computer | a planar test passes against generated files; undo still copies the model; a module test's compile time is measured |
| C | The move: every file to its module, records out of `bim_model.dl`, imports rewritten, all hubs generated, layer check v2, CODEOWNERS, tests inside modules, workflows | one computer, freeze | full test set passes on Linux, Windows workflow green, the pavilion opens |
| D | Open the floor: `docs/OWNERS.md`, empty modules with owners, `feature/connection-module` rebased into `structural/steel` | all computers | each computer runs its module's test loop |
| E | Kernel seam (the restructuring design §6), `kernel/brep` as the first library | the kernel computer | model-level tests halve; the application builds as two units |
| F | Owners' projects: IFCX native format and the text format retired, localisation as data, IfcGit, DXF and DWG, extension manager | module owners, in parallel | each its own pull request and tests |
| G | More compile units where measurement says so; compiler frontend caching upstream | the compiler computer | the application compiles as several processes |

## Phase B in steps

1. Write `tools/compose_modules.py`: reads every `*/MODULE` manifest, writes
   `generated/model.dl` and `generated/compose.dl`. Test: a fixture with two
   manifests produces the expected two files (golden files in `tools/tests/`).
2. Give `bim/` and `elements/planar` a `MODULE` and a `records.dl`: `bim`
   stores `nextId`, `journal`, `settings`, `properties`, `phases`, `phasings`;
   `planar` stores `wallTypes`, `walls`, `slabs`. The other lists stay in the
   hand-written record for the spike.
3. Generate; make `update bim evaluation` call the generated evaluation
   dispatcher for walls and slabs; keep every other kind as it is.
4. Run `build.sh test evaluate wall_base plate_layers`: PASS, unchanged
   expected output. Run `build.sh test journal`: undo still copies the model.
5. Measure: compile time of one planar test against the generated files, on
   computer 1, into `docs/notes/build-times.md`.
6. Decide: if steps 3 and 4 hold, phase C starts; if the generated record
   breaks undo or a dispatcher cannot be written, the fallback of the design's
   §10 applies and this plan is revised before any move.

## Phase C, the inventory it executes

The file-to-module table of the design's §4 and the test-to-module table in
the maintainer's catalogue (224 tests, none left over); the moves are `git mv`
in one commit, the import rewrite a second, the generated hubs a third, so
history follows the files.

Done 2026-10-28: phases B, C (the mechanical part and, by the module owner,
the records and stores of every module) and D are on `main`; the scene point
is composed and order-free. Phase E starts on computer 2, which owns the
kernel groups.

## Phase E in steps: the kernel seam

Status 2026-10-28, late: steps 1 to 4 are on `main`. The library exposes what
the application uses: extrusion of a curve chain, the boolean combination,
the mesh and the mass properties of a mesh, the sphere, the cylinder, the
faceted solid (flat face encoding) and the visible edges as a wire set; bodies
cross as handles with retain and release; `tools/kernel_client.py` writes the
client; five round-trip tests under `kernel/api/tests` compare every result
with the shared source. Face keys, bounds, slice, section and node pointers
are used by tests only and stay unexposed until a module needs them. Step 5,
the application side, is the modules' owner's pull request.

The library is `kernel/brep` with `kernel/acis` (31,754 lines); `kernel/core`,
`kernel/fast`, `kernel/planar` and `kernel/nurbs` stay shared source, imported
by the library and by every program. The compiler: the pinned `c2d32bea` with
the six patches carries `--emit-object --no-main` and `exposed function`
(commit `f54f8475` is its ancestor; the Windows worktree compiler has them
too), so the seam needs no compiler change. Design: the restructuring design
§6; this phase keeps its order, library side first, application side last.

1. **Link test.** `kernel/api/exposed.dl` with one exposed function that
   returns a scalar (`the obskernel version`), compiled with
   `--emit-object --no-main` into `build/kernel/libobskernel.a`; a test
   program `kernel/api/tests/link.dl` calls it through
   `@intrinsic("call", "obskernel", "<symbol>", …)` and prints the value.
   `build.sh kernel` builds the archive; `build.sh test link` links against
   it. Done when the test passes on Linux and Windows. This fixes the symbol
   mangling in `tools/kernel_client.py` (Python until the tooling phase).
2. **Mesh round trip.** `kernel/api/types.dl` holds `cad mesh` (positions,
   normals, triangles) as shared source; an exposed function fills a
   caller-provided mesh from a unit cube made inside the library; the test
   compares the triangle count and the volume with the shared-source mesh of
   the same cube. Done when the layouts agree (design §14's stop condition).
3. **Body handles.** `kernel body` in `kernel/api/client.dl`: a managed class
   holding an opaque pointer, with `retain:` and `release:` calling exposed
   library functions. Exposed: extrusion of loops along a direction, sphere
   body, cylinder body, faceted solid from a polyhedron, combination of two
   bodies by kind, body placed by a placement; queries: mass properties,
   bounds, face keys, bounded face edges, plane slice, plane section,
   wireframe, mesh at a tolerance; planar: triangulation of loops,
   arrangement of tagged lines. One pattern path, concrete types each.
   `tools/kernel_client.py` writes the natural-language wrappers; a test
   checks the generated file is current.
4. **Library tests.** `kernel/api/tests/` exercise every exposed function
   against the shared-source result on the same input, so the seam is proven
   before any application code uses it.
5. **Application side**, one pull request reviewed by the modules' owner:
   `bim solid record` and `bim element geometry record` hold a `kernel body`;
   the call sites in `elements/planar`, `elements/connection`,
   `structural/steel` and `viewer` use the client's patterns (the sentences
   stay the same; only the value's type changes). The full test set and the
   application must pass unchanged.
6. **Measure**, on the Linux machine: the library build, the application
   build as two units, and the model-level tests, into `build-times.md`.
   Stop condition: if a model-level test's compile time does not halve, stop
   and revisit the seam before cutting further units.
