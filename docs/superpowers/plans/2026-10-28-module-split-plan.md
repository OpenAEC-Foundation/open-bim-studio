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
