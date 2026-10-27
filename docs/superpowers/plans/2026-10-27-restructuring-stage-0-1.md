# Restructuring stages 0 and 1 (secure the work, freeze and move) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Secure every open piece of work, then move the application and the kernel out of `spikes/dynlex-bim-slice` into the unit directories of the design, with the same tests passing on the same compiler.

**Architecture:** Stage 0 is git work on computer 1: commit the staged canvas-editing work, land the two open pull requests, archive and delete the rest. Stage 1 is one branch, `restructure/one-tree`, under a work-board freeze: the kernel is seeded from the fork's port branch plus this repository's overlay, every application file is moved with `git mv`, imports and path strings are rewritten, the overlay and tree assembly are replaced by compiling from the repository root with two generated import files, and the build, CI, installer and documentation follow. No kernel seam yet; that is stage 2's plan.

**Tech Stack:** DynLex (fork `codex/cadkernel-port` at `c2d32bea` with the six patches of `patches/`), bash, PowerShell, GitHub Actions, git, `gh`.

**Spec:** `docs/superpowers/specs/2026-10-27-restructuring-design.md` (§3 current state, §5 layout, §6.5 build, §10 stages 0 and 1, §11 measurements, §12 constraints, §15 answers).

## Global Constraints

- Repository content in English; no assistant transcripts anywhere; no names of competing calculation software.
- Compiler: the fork's `codex/cadkernel-port` at commit `c2d32bea`, built in place in its checkout, with the six compiler patches applied; `.dynlex-root.local` or `DYNLEX_ROOT` names that checkout.
- Computer 1 does every task here; computer 2 reviews the workflow and patch parts of the pull requests and runs the Windows workflow, and makes no concurrent edits from Task 5 until Task 14 merges.
- No behaviour change: every test keeps its `expected.txt`; the move commit contains only renames, import rewrites and path-string rewrites.
- File names and natural-language patterns do not change, except `bim_window_style.dl`, which becomes `graphics/window_style_linux.dl`, and `platform/windows/bim_window_style.dl`, which becomes `graphics/window_style_windows.dl`.
- `PROMPTS.md` at the root and the untracked `f2.html` are the maintainer's; never add, modify or delete them.
- The research spikes beside `spikes/dynlex-bim-slice` stay untouched.
- Only `spikes/dynlex-bim-slice/build/` and other ignored output may be deleted from disk without a `git mv`.

## Review Focus

- A fresh checkout without `generated/` must build: every `build.sh` command and the Windows script run `generate` first, and Task 12's first step deletes `generated/` before `build.sh test platform`.
- The import rewrite must not change line endings or whitespace: Task 8 checks that every changed `.dl` line is an `import` line or a listed path string, and that no file gained CRLF.
- Run from the repository root, the program must find fonts, icons, shaders, the import script and the review models at their new paths, and an installed copy (`OPEN_BIM_STUDIO_HOME`) must be unaffected: Task 12 opens the pavilion from the root and Task 8's diff filter proves the installed-copy branch of `main.dl` is untouched.
- The kernel fixtures must produce the same output after only their import lines changed: Task 12 runs a filtered fixture set and compares against the unchanged `expected.txt`.
- Old build trees on disk (`spikes/dynlex-bim-slice/build/`, `build/windows-local/`) must not be read by the new build: Task 10 asserts `build.sh` never references `build/tree`.

---

### Task 1: Commit the canvas-editing work (stage 0)

**Files:**
- Commit: the 90 staged files on `codex/canvas-editing-and-automation`, plus the untracked `spikes/dynlex-bim-slice/overlay/examples/bim-slice/tests/modify_scale_profiles.dl` and `.expected.txt`.

- [ ] **Step 1: Confirm the branch and the staged set**

Run: `git status --short | grep -vE "^(M |A |R )" ` from the repository root.
Expected: exactly ` M PROMPTS.md`, `?? docs/superpowers/specs/2026-10-27-restructuring-design.md`, `?? docs/superpowers/plans/2026-10-27-restructuring-stage-0-1.md`, `?? f2.html` and the two `modify_scale_profiles` files. If anything else appears, stop and report it.

- [ ] **Step 2: Add the two untracked test files and the design documents**

```bash
git add spikes/dynlex-bim-slice/overlay/examples/bim-slice/tests/modify_scale_profiles.dl spikes/dynlex-bim-slice/overlay/examples/bim-slice/tests/modify_scale_profiles.expected.txt docs/superpowers/specs/2026-10-27-restructuring-design.md docs/superpowers/plans/2026-10-27-restructuring-stage-0-1.md
git diff --cached --stat | tail -1
```
Expected: `94 files changed`.

- [ ] **Step 3: Commit and push**

```bash
git commit -m "Add canvas editing tools, the type manager and automation adapters

Canvas Modify and Edit tools with point entry, grid controls, the IfcTypes
manager, the MCP and HTTP adapters, their tests, and the restructuring
design and stage 0-1 plan.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
git push -u origin codex/canvas-editing-and-automation
```
Expected: push accepted; `git status --short` shows only ` M PROMPTS.md` and `?? f2.html`.

- [ ] **Step 4: Open the pull request**

```bash
gh pr create --base main --title "Add canvas editing tools, the type manager and automation adapters" --body "Canvas editing, point entry, grid controls, the IfcTypes manager and the automation adapters, on top of #7. Review the workflow, patch and MCP changes from computer 2.

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```
Expected: a PR URL; note its number as `CANVAS_PR`.

### Task 2: Land PR 7 and the canvas PR, sync main

- [ ] **Step 1: Merge PR 7**

Run: `gh pr view 7 --json state,mergeable,reviewDecision`.
Expected: `OPEN`, `MERGEABLE`. Then `gh pr merge 7 --merge` (no squash: keep the commits).

- [ ] **Step 2: Merge the canvas PR after computer 2's review**

Computer 2 reviews the workflow, patch and MCP files of `$CANVAS_PR` (they are its territory on the work board). Then `gh pr view $CANVAS_PR --json mergeable,reviewDecision` → `MERGEABLE` and not `CHANGES_REQUESTED`; then `gh pr merge $CANVAS_PR --merge --delete-branch`.

- [ ] **Step 3: Fast-forward local main**

```bash
git switch main
git pull --ff-only origin main
git log --oneline -3
```
Expected: the two merge commits on top of `583ea9d`; `git status` clean apart from `PROMPTS.md` and `f2.html`.

- [ ] **Step 4: Delete the local topic branches**

```bash
git branch -D codex/canvas-editing-and-automation fix/windows-app-compile
```

### Task 3: Branch hygiene

- [ ] **Step 1: Tag the two stale spikes as archives**

```bash
git tag -a archive/spike-bim-slice-linear-members origin/spike/bim-slice-linear-members -m "Archived 2026-10-27: linear members, profile library and generic connections spike; superseded by the connections and reinforcement modules on main"
git tag -a archive/codex-dynedra-dwg-viewer origin/codex/dynedra-dwg-viewer -m "Archived 2026-10-27: DynLex DWG viewer spike, not integrated"
git push origin archive/spike-bim-slice-linear-members archive/codex-dynedra-dwg-viewer
```

- [ ] **Step 2: Show the maintainer what the archives hold, and wait for a yes**

Run: `git log --oneline --stat origin/main..origin/spike/bim-slice-linear-members | head -40` and the same for `origin/codex/dynedra-dwg-viewer`. Report the three commits and file lists of each; proceed only on the maintainer's confirmation that nothing in them is still wanted.

- [ ] **Step 3: Delete the remote branches that are merged or archived**

```bash
git push origin --delete codex/interaction-reinforcement-2026-10-21 codex/windows-port-v0.1 codex/windows-release-0.1.1 feature/reinforcement-module research/kernel-programme review/reinforcement-base-e5aeaaa spike/dynlex-bim-slice work/plate-anchor work/plate-openings work/project1357-integration work/side-push work/sketch-split feature/steel-baseplates feature/roof-forms-and-dimensions spike/bim-slice-linear-members codex/dynedra-dwg-viewer
git branch -D codex/dynedra-dwg-viewer
git fetch --prune
```
Expected: `git branch -r` lists `origin/HEAD` and `origin/main` only.

- [ ] **Step 4: Close PR 2**

```bash
gh pr close 2 --comment "Merged into main through the consolidation of 2026-10-23; closing the stale pull request."
```

### Task 4: Baseline measurements on the pre-move tree

**Files:**
- Create: `docs/notes/build-times.md` (committed in Task 12 on the restructuring branch).

The measurements take about five hours and compile memory forbids a second compiler on the machine; run them from a separate worktree of `main` and do Tasks 5 to 10 (file moves and edits only, no compiling) meanwhile. Do not start Task 11 until this task's runs have finished.

- [ ] **Step 1: Make the baseline worktree**

```bash
git worktree add ../obs-baseline main
cd ../obs-baseline/spikes/dynlex-bim-slice
echo "$DYNLEX_ROOT" > .dynlex-root.local
bash build.sh toolchain-info
```
Expected: the compiler path, its SHA-256 and source HEAD `c2d32bea`. Record all three.

- [ ] **Step 2: Measure, in this order, each with `/usr/bin/time -v`**

```bash
/usr/bin/time -v bash build.sh app 2> ../../build-app-O2.time
/usr/bin/time -v bash build.sh dev 2> ../../build-app-O0.time
for t in ifc_read editor sketch; do /usr/bin/time -v bash build.sh test $t 2> ../../build-test-$t.time; done
/usr/bin/time -v bash build.sh test 2> ../../build-test-all.time
```
Expected: each `.time` file ends with `Elapsed (wall clock) time` and `Maximum resident set size`; `build.sh test` prints PASS for every test (record any FAIL by name: it is the baseline, not a blocker).

- [ ] **Step 3: Write the table**

Create `docs/notes/build-times.md` in the restructuring worktree (Task 5) with one table: columns `target | stage | wall time | peak RSS | compiler | date`, one row per measurement, stage `before stage 1`. Keep the `.time` files out of git.

### Task 5: Freeze claim and branch

**Files:**
- Modify: `docs/WERKBORD.md` (claim section at the top of the table's notes).

- [ ] **Step 1: Claim the tree on main**

Add to `docs/WERKBORD.md`, directly under the table, a section `## Restructuring stage 1 — computer 1 — 2026-10-xx` stating: branch `restructure/one-tree`; files: the whole of `spikes/dynlex-bim-slice`, `.github/workflows`, `CLAUDE.md`, `README.md`, `docs/`; freeze: no other branch edits these until the stage 1 pull request is merged; computer 2: review and the Windows workflow only. Commit on `main` with message `Claim the tree for restructuring stage 1` and push.

- [ ] **Step 2: Create the branch**

```bash
git switch -c restructure/one-tree
```

### Task 6: Seed kernel/ from the fork and the overlay

**Files:**
- Create: `kernel/core/`, `kernel/planar/`, `kernel/nurbs/`, `kernel/space/`, `kernel/brep/`, `kernel/acis/`, `kernel/fast/`, `kernel/tests/`, `kernel/reference/`, `kernel/docs/`, `kernel/LICENSE`, `kernel/cadkernel.dl`.
- Move (`git mv`): the 27 `spikes/dynlex-bim-slice/overlay/lib/cadkernel/*.dl` and 4 `overlay/lib/fastkernel/*.dl`.

**Interfaces:**
- Produces: the folder of every kernel file, which Task 8's import rewrite derives from the tree by basename. Basenames are unique across `kernel/`.

- [ ] **Step 1: Extract the port's kernel, fixtures and notes at `c2d32bea`**

```bash
git -C "$DYNLEX_ROOT" fetch origin codex/cadkernel-port
mkdir -p /tmp/kernel-seed && git -C "$DYNLEX_ROOT" archive c2d32bea lib/cadkernel tests/required tests/cadkernel docs | tar -x -C /tmp/kernel-seed
ls /tmp/kernel-seed/lib/cadkernel | wc -l
```
Expected: `124` (123 `.dl` files and `LICENSE`).

- [ ] **Step 2: Place the port's files by folder**

Folder lists (basenames without `.dl`):
- `core`: core plane transform2 frame angle bounds2 geometry2 curve2 polyline2 arclength2 containment2 intersect2 snap2 construct2 cross2 arena pair_index gradient deviation2
- `planar`: triangulate2 constrained2 arrangement2 band2 tessellate2 tessellation offset2 clip2 area2 arc_fit2 centerline2 fillet2 geom2d
- `nurbs`: nurbs2 nurbs3 nurbs_builder spline knot_compaction
- `space`: space curve3 helix alignment arc_union3 line_union3 endpoint_join3 source_join3 lengthen3 polyline_approximation3 arclength3 polygon3 polygon3_mesh planar3
- `brep`: every file whose name is `brep` or starts with `brep_`
- `acis`: every file whose name is `acis` or starts with `acis_`
- `kernel/` itself: `cadkernel.dl`, `LICENSE`

Copy each file from `/tmp/kernel-seed/lib/cadkernel/` to its folder. A file that matches no list is an error: stop and report it.

- [ ] **Step 3: Move the overlay's kernel files over the port's**

For the 21 overrides (`arena brep_append brep_boolean brep_bounds brep_classify brep_geometry brep_imprint brep_make brep_mesh brep_pcurve brep_place brep_slice brep_split brep_sweep brep_topology constrained2 nurbs2 nurbs3 spline tessellation triangulate2`): `git mv -f spikes/dynlex-bim-slice/overlay/lib/cadkernel/NAME.dl kernel/FOLDER/NAME.dl` so the overlay version replaces the port copy. For the six overlay-only files: `brep_section` → `kernel/brep/`, `operation_tolerance` and `topology_list` → `kernel/core/`, `robust2`, `section_loops`, `spade_cdt2` → `kernel/planar/`. The four `overlay/lib/fastkernel/*.dl` → `kernel/fast/`.

- [ ] **Step 4: Fixtures, reference material and notes**

- `/tmp/kernel-seed/tests/required/cadkernel_NAME/` → `kernel/tests/NAME/` for all 214 directories (strip the `cadkernel_` prefix; keep `main.dl`, `expected.txt`, `compile_timeout_seconds.txt` and any other file as is).
- `/tmp/kernel-seed/tests/cadkernel/verify.py` → `kernel/tests/verify.py`; the rest of `/tmp/kernel-seed/tests/cadkernel/` (README and the per-topic directories with `reference.rs`, `verify.py`, `probe.dl`, `source-tests.txt`) → `kernel/reference/`.
- `/tmp/kernel-seed/docs/cadkernel-*.md` and `cadkernel-performance.json` → `kernel/docs/` with the `cadkernel-` prefix removed.

- [ ] **Step 5: Verify counts and staging**

```bash
git add kernel
find kernel/core kernel/planar kernel/nurbs kernel/space kernel/brep kernel/acis kernel/fast kernel -maxdepth 1 -name "*.dl" | sort -u | wc -l
ls kernel/tests | wc -l
git diff --cached -M --name-status | grep -c "^R.*overlay/lib/"
```
Expected: `133` kernel source files (123 from the port including `cadkernel.dl`, 6 overlay-only, 4 fast), `215` entries in `kernel/tests` (214 fixtures and `verify.py`), and `31` renames from `overlay/lib/`.

### Task 7: Move the application, assets, tests, tools, scripts and notes

**Files:** every remaining file under `spikes/dynlex-bim-slice/`, by `git mv`. `S` below is `spikes/dynlex-bim-slice/overlay/examples/bim-slice`.

**Interfaces:**
- Produces: the unit of every application file, which Task 8 derives from the tree by basename.

- [ ] **Step 1: Application modules**

- `model/`: bim_model bim_index connections reinforcement reinforcement_library reinforcement_area bim_evaluate bim_stair bim_window_construction bim_system_identity bim_network bim_profiles bim_spaces bim_masonry bim_component bim_connections bim_connection_geometry bim_fastener_detail bim_baseplate bim_reinforcement bim_reinforcement_schedule bim_bending_schedule bim_grid_pattern bim_view bim_sheet bim_system_types bim_stair_types bim_project_settings bim_plan_presentation bim_drawing_standard bim_checks bim_opening_detail bim_window_actions bim_window_placement bim_clash bim_schedule bim_hidden bim_modify_geometry bim_roof_forms bim_steel_profiles bim_point_input bim_drawing (41)
- `formats/`: bim_file bim_step bim_ifc_psets bim_import bim_ifc_read bim_ifc_native bim_ifc_promote bim_import_cache bim_ifc bim_ifcx bim_ifcx_binary bim_ifcx_read bim_dxf_reference bim_library bim_vector_data bim_image_data bim_sheet_cache bim_svg bim_pdf (19); plus `S/import/` → `formats/import/`
- `graphics/`: bim_text bim_canvas bim_application_icon bim_scene bim_native_instances bim_hatch bim_section_caps bim_section_materials bim_section_gpu bim_vector_gpu bim_vector_reference bim_images bim_drawing_rules bim_reinforcement_drawing bim_pavilion_drawings bim_demo_pavilion (16); `S/bim_window_style.dl` → `graphics/window_style_linux.dl`; `spikes/dynlex-bim-slice/platform/windows/bim_window_style.dl` → `graphics/window_style_windows.dl`; `spikes/dynlex-bim-slice/overlay/lib/vulkan/*.dl` → `graphics/vulkan/`; `overlay/lib/vulkan/shaders/*.dl` and `spikes/dynlex-bim-slice/shaders/*.spv` → `graphics/shaders/`; `overlay/examples/gpu/` → `graphics/gpu_example/`
- `editor/`: bim_editor_core bim_editor bim_editor_properties bim_editor_psets bim_editor_wall_side bim_editor_window_placement bim_boundary_sketch bim_modify_preview bim_modify_options bim_section_box bim_push_pick bim_crop bim_type_manager bim_type_menu bim_type_text bim_type_labels bim_grid_controls bim_app_files bim_ui_files bim_model_explorer bim_demo_pavilion_editor (21)
- `app/`: main bim_ui bim_ui_layout bim_plan_panel bim_view_panel bim_app_parts bim_sheet_paper bim_sheet_workspace bim_sheet_workspace_ui bim_sheet_renderer bim_workspace_tabs bim_loading (12); `S/fonts/` → `app/fonts/`; `S/icons/` → `app/icons/`
- `automation/`: bim_api; `S/mcp/` → `automation/mcp/` (the `__pycache__` is ignored and is not moved)
- `platform/`: `S/platform/obs_platform.c` → `platform/obs_platform.c`

Count check after the moves: `ls model formats graphics editor app automation | grep -c "\.dl$"` → `112`: the 111 application files (41 + 19 + 17 including `window_style_linux` + 21 + 12 + 1) and `window_style_windows.dl`.

- [ ] **Step 2: Tests, tools, installer, scripts, patches, workflows**

- `S/tests/*` → `tests/` (the `.dl`, `.expected.txt`, `.py` files and `fixtures/`); `S/test_support/` → `tests/support/`; `spikes/dynlex-bim-slice/examples/*.bim` → `tests/models/`
- `S/tools/*.dl` → `tools/probes/`; `spikes/dynlex-bim-slice/tools/*.py` → `tools/`
- `S/installer/` → `installer/`
- `spikes/dynlex-bim-slice/build.sh`, `toolchain.sh` → repository root; `spikes/dynlex-bim-slice/ci/build-windows-app.ps1` → `scripts/build-windows-app.ps1`
- `spikes/dynlex-bim-slice/patches/` → `patches/`
- `spikes/dynlex-bim-slice/ci/windows-app.yml`, `windows-compiler.yml`, `windows-release.yml` → `.github/workflows/` (`git mv -f`, replacing the two existing copies)
- Notes to `docs/notes/`, lower-case names: `BASEPLATES.md` → `baseplates.md`, `DRAWING-FIDELITY.md` → `drawing-fidelity.md`, `FINDINGS.md` → `findings.md`, `PLAN-PERFORMANCE.md` → `plan-performance.md`, `REINFORCEMENT-LIBRARY.md`, `REINFORCEMENT-SCOPE.md`, `ROOF-EDITING-WIP.md`, `SHEET-WORKSPACE.md`, `VECTOR-RENDERING.md`, `VIEW-TABS.md`, `WINDOW-SYSTEMS.md`, `WINDOWS.md` → `windows-port.md`, `spikes/dynlex-bim-slice/README.md` → `application-and-toolchain.md`, `ci/WINDOWS-RELEASE.md` → `windows-release.md`, `S/README.md` → `module-guide.md`, `S/mcp/README.md` → `automation/README.md`, `S/icons/README.md` → `app/icons/README.md`, `S/PROMPTS.md` → `docs/notes/prompts-bim-slice.md`, `S/installer/licenses` stays inside `installer/`.
- `spikes/dynlex-bim-slice/.gitignore` is deleted; its line `.dynlex-root.local` is added to the root `.gitignore` in Task 9.

- [ ] **Step 3: Nothing left behind**

```bash
git status --short | grep "spikes/dynlex-bim-slice" | grep -v "^R" 
ls spikes/dynlex-bim-slice
```
Expected: the first prints nothing; the second lists only ignored output (`build/`), which is then removed with `rm -rf spikes/dynlex-bim-slice`.

### Task 8: Rewrite imports and path strings

**Files:**
- Modify: every `.dl` file under `kernel/`, `model/`, `formats/`, `graphics/`, `editor/`, `app/`, `automation/`, `tests/`, `tools/`; `.gitattributes`.

**Interfaces:**
- Consumes: the trees produced by Tasks 6 and 7.
- Produces: import paths of the form `kernel/<folder>/NAME.dl`, `<unit>/NAME.dl`, `graphics/vulkan/NAME.dl`, `graphics/shaders/NAME.dl`, `tests/NAME.dl`, `tests/support/NAME.dl`, `tools/probes/NAME.dl`.

- [ ] **Step 1: Build the basename map from the tree and rewrite imports**

Write a one-off script (not committed) that, for every `.dl` file under the directories above, maps `lib/cadkernel/NAME.dl` and `lib/fastkernel/NAME.dl` to the unique `kernel/**/NAME.dl`, `lib/vulkan/NAME.dl` to `graphics/vulkan/NAME.dl`, `lib/vulkan/shaders/NAME.dl` to `graphics/shaders/NAME.dl`, `examples/bim-slice/NAME.dl` to the unique `<unit>/NAME.dl` (with `bim_window_style.dl` → `graphics/window_style_linux.dl`), `examples/bim-slice/tests/NAME.dl` → `tests/NAME.dl`, `examples/bim-slice/test_support/NAME.dl` → `tests/support/NAME.dl`, `examples/bim-slice/tools/NAME.dl` → `tools/probes/NAME.dl`, and `examples/gpu/NAME.dl` → `graphics/gpu_example/NAME.dl`; a basename that resolves to zero or more than one file is an error. Rewrite only lines matching `^import `, preserving the file's line endings.

- [ ] **Step 2: Rewrite the path strings**

Exact replacements, nowhere else:
- `app/main.dl`: `"examples/bim-slice/fonts/osifont.ttf"` → `"app/fonts/osifont.ttf"`; `"examples/bim-slice/import/drawing_to_lines.py"` → `"formats/import/drawing_to_lines.py"`; both `"tests/games/fonts/LiberationMono-Regular.ttf"` → `"app/fonts/LiberationMono-Regular.ttf"`; the `--example` lookup `"examples/bim-slice/models/"` → `"tests/models/"`.
- `tests/images.dl`: the three `"examples/bim-slice/tests/fixtures/..."` → `"tests/fixtures/..."` and `"examples/bim-slice/tests/images.dl"` → `"tests/images.dl"`.
- `tests/support/reinforcement_fixture.dl`: `"examples/bim-slice/models/"` → `"tests/models/"`.
- `kernel/tests/verify.py`: the fixture root `tests/required` and prefix `cadkernel_` → `kernel/tests` and no prefix; the repository root detection → this repository's root; the default compiler → `$DYNLEX_ROOT/build/dynlex` read from `.dynlex-root.local` or `DYNLEX_ROOT`.
- `.gitattributes`: `spikes/dynlex-bim-slice/patches/*.patch` → `patches/*.patch`.

Then copy the fork's `tests/games/fonts/LiberationMono-Regular.ttf` and `LICENSE-LiberationFonts` (from `/tmp/kernel-seed` after extending the Step 1 archive of Task 6 with `tests/games/fonts`, or from `$DYNLEX_ROOT`) into `app/fonts/` and `git add` them.

- [ ] **Step 3: Verify nothing old remains and nothing else changed**

```bash
grep -rnE "examples/bim-slice|lib/cadkernel|lib/fastkernel|lib/vulkan|tests/games/fonts|examples/gpu" --include="*.dl" --include="*.py" kernel model formats graphics editor app automation tests tools | grep -v "kernel/docs"
git diff -M --cached --stat | tail -1
git diff -M --cached -U0 -- '*.dl' | grep -E "^[+-]" | grep -vE "^(\+\+\+|---)" | grep -vE "^[+-]import " | grep -vE "osifont|drawing_to_lines|LiberationMono|tests/models|tests/fixtures|tests/images"
git ls-files -z kernel model formats graphics editor app tests | xargs -0 file | grep -c CRLF
```
Expected: the first and third print nothing; the last prints `0`.

### Task 9: Generated files, main.dl hooks, the move commit

**Files:**
- Create: `generated/` (ignored), written by `build.sh generate` (Task 10): `generated/platform.dl`, `generated/self_test.dl`.
- Modify: `app/main.dl`, `.gitignore`.

**Interfaces:**
- Produces: `generated/platform.dl` containing exactly one line, `import graphics/window_style_linux.dl` or `import graphics/window_style_windows.dl`; `generated/self_test.dl` defining the pattern `run bim app checks` (a function with no effect by default; the bundled tests for `dev-test`). `app/main.dl` imports both.

- [ ] **Step 1: Edit `app/main.dl`**

Replace `import examples/bim-slice/bim_window_style.dl` (already rewritten by Task 8 to `import graphics/window_style_linux.dl`) with `import generated/platform.dl`, add `import generated/self_test.dl` after it, and insert, immediately before the line `set startedAt to the bim microseconds now`, the five lines that `build.sh dev-test` used to inject with awk:

```
set appCheckArguments to the command line arguments
if appCheckArguments' length > 0:
    if (the argument at 0 in appCheckArguments) = (the string form of "--self-test"):
        run bim app checks
        @intrinsic("call", "libc", "exit", nothing, 0)
```

- [ ] **Step 2: Write the two generated files by hand once, to check they compile**

`generated/platform.dl`: `import graphics/window_style_linux.dl`. `generated/self_test.dl`: a definition of `function run bim app checks:` whose `execute:` body does nothing observable (the implementer picks the smallest statement the compiler accepts, for example `ignore 0`); note the statement for Task 10's generator.

- [ ] **Step 3: `.gitignore`**

Add, under the build-output section: `generated/`, `.dynlex-root.local`, `*.time`. Remove the four `spikes/**/` lines that only served the deleted spike if no other spike needs them (keep `spikes/**/node_modules/`, `target/`, `build/`, `dist/`, `__pycache__/`, `.venv/`, `venv/`: other spikes use them).

- [ ] **Step 4: The move commit**

```bash
git add -A kernel model formats graphics editor app automation platform tests tools installer patches scripts docs/notes .github/workflows build.sh toolchain.sh .gitignore .gitattributes
git status --short | grep -vE "^(R|A|M|D) " 
git commit -m "Move the application and kernel into unit directories

The kernel is seeded from the DynLex fork's codex/cadkernel-port at
c2d32bea (lib/cadkernel, its fixtures and notes) with this repository's
overlay files replacing 21 of them and adding 6; the fast kernel and the
Vulkan layer were already this repository's. Application modules move to
model/, formats/, graphics/, editor/, app/ and automation/; tests, tools,
installer, scripts, patches and notes follow. Imports and path strings are
rewritten; patterns and file names are unchanged, except the two window
style modules. Per-OS and self-test variation now goes through the
generated/ imports instead of rewriting sources.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```
Expected: the `grep` prints only ` M PROMPTS.md` and `?? f2.html`; the commit succeeds; `git show --stat -M HEAD | grep -c "=>"` is at least `300`.

### Task 10: build.sh, toolchain.sh, the Windows script, workflows and installers

**Files:**
- Modify: `build.sh`, `toolchain.sh`, `scripts/build-windows-app.ps1`, `.github/workflows/windows-app.yml`, `windows-compiler.yml`, `windows-release.yml`, `installer/make-installer.sh`, `installer/make-windows-package.ps1`, `tools/bundle_tests.py`.
- Create: `lib/json.dl` (the fork's `lib/json.dl` at `c2d32bea` with `patches/lib-json-public-parse.patch` and `patches/lib-json-bounded-string.patch` applied), `lib/README.md` (one paragraph: overrides tied to upstream PRs, to be deleted when merged).

**Interfaces:**
- Produces: `build.sh generate|app|dev|dev-test NAME..|run|run-dev|test [NAME..]|bundle [NAME..]|probe NAME|run-probe NAME|installer OUT|toolchain-info`, run from the repository root; `BIM_BUILD_DIR` (default `build/`), `BIM_DEBUG`, `BIM_DEV_OPT_LEVEL` keep their meaning.

- [ ] **Step 1: `build.sh`**

Delete the tree assembly (`rsync`, the JSON patching, the font copy, the `ln -sfn` of the compiler, `cd "$tree"`). Add a `generate` function that writes `generated/platform.dl` (Linux module unless `BIM_PLATFORM=windows`) and `generated/self_test.dl` (the no-op from Task 9 Step 2) and is called at the start of every command except `toolchain-info`. Compile from the repository root with `"$root/build/dynlex"` and the new paths: `app/main.dl`, `tests/NAME.dl`, `tools/probes/NAME.dl`; shaders `cp graphics/shaders/*.spv "$out/shaders/"` and the program's `shaderDirectory` stays `build/shaders` (so `BIM_BUILD_DIR` other than `build/` must still produce `build/shaders`: keep that copy unconditional); the platform shim from `platform/obs_platform.c`; `dev-test` wraps the bundle made by `tools/bundle_tests.py make tests app_checks NAME..` into `function run bim app checks:` / `execute:` and writes it to `generated/self_test.dl` instead of editing `main.dl`; `bundle` and `test` read `tests/`; `installer` calls `installer/make-installer.sh`. Add `BIM_JOBS` to `test`: run up to that many tests concurrently with `xargs -P` (default 1).

- [ ] **Step 2: `toolchain.sh`**

Unchanged logic; the error messages name the repository root instead of the spike.

- [ ] **Step 3: `scripts/build-windows-app.ps1` and the three workflows**

Replace the tree assembly and the window-style copy with: write `generated\platform.dl` containing `import graphics/window_style_windows.dl` and the no-op `generated\self_test.dl`; copy `graphics\shaders\*.spv` to `build\shaders`; compile `app/main.dl` and `tests/NAME.dl` from the repository root with the compiler built in the fork checkout; the platform shim from `platform/obs_platform.c`; patches from `patches/`; the package script with explicit folders (Step 4). In the workflows, every `spikes/dynlex-bim-slice/...` path becomes the new one, the "Assemble the slice" step becomes the generate-and-copy step above, and `windows-app.yml` keeps `workflow_dispatch` so computer 2 can run it on the branch. `grep -rn "spikes/dynlex-bim-slice\|examples/bim-slice\|overlay" .github scripts` must print nothing.

- [ ] **Step 4: Installers**

`installer/make-installer.sh` and `installer/make-windows-package.ps1` take the font folder `app/fonts` (now including LiberationMono and its licence), `app/icons`, `build/shaders`, `formats/import` and `installer/licenses` instead of deriving them from a tree; the installed layout (`bin/`, `fonts/`, `shaders/`, `icons/`, `import/`, `licenses/`) is unchanged, so `main.dl`'s installed-copy branch is untouched.

- [ ] **Step 5: `lib/json.dl` override**

```bash
mkdir -p lib && git -C "$DYNLEX_ROOT" show c2d32bea:lib/json.dl > lib/json.dl
patch -p1 lib/json.dl < patches/lib-json-public-parse.patch
patch -p1 lib/json.dl < patches/lib-json-bounded-string.patch
grep -c "the JSON document parsed from\|Bound storage by this encoded string" lib/json.dl
```
Expected: `2`. The two JSON patches stay in `patches/` until stage 3 has upstreamed them; `lib/README.md` names them as the source of the override.

- [ ] **Step 6: Verify the build script without compiling anything heavy**

```bash
rm -rf generated
bash build.sh toolchain-info
bash build.sh generate && cat generated/platform.dl && grep -c "run bim app checks" generated/self_test.dl
grep -n "build/tree\|rsync\|examples/bim-slice\|overlay" build.sh scripts/build-windows-app.ps1 installer/*.sh installer/*.ps1
```
Expected: the compiler info; `import graphics/window_style_linux.dl`; `1`; the last `grep` prints nothing.

- [ ] **Step 7: Commit**

```bash
git add build.sh toolchain.sh scripts .github/workflows installer tools/bundle_tests.py lib patches .gitignore
git commit -m "Build from the repository root without a staged tree

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

### Task 11: Layering repairs (design §5)

**Files:**
- Create: `model/bim_mesh.dl`, `model/bim_text_file.dl`, `scripts/check-layers.sh`.
- Move: `graphics/bim_section_gpu.dl` → `app/`; `graphics/bim_drawing_rules.dl` and `graphics/bim_images.dl` → `editor/`; `model/bim_clash.dl` and `model/bim_schedule.dl` → `graphics/`.
- Modify: `graphics/bim_scene.dl`, `formats/bim_import.dl`, `formats/bim_ifc.dl`, `formats/bim_ifcx.dl`, `formats/bim_file.dl`, `model/bim_steel_profiles.dl`, and every importer of a moved file.

**Interfaces:**
- Produces: `scripts/check-layers.sh`, which exits non-zero when an `import` crosses a unit boundary upward. Allowed targets per unit: `kernel` → `kernel`, `lib`; `model` → `model`, `kernel`, `lib`; `formats` and `graphics` → themselves, `model`, `kernel`, `lib`, and `formats` ↔ `graphics` both ways; `editor` → `editor`, `graphics`, `formats`, `model`, `kernel`, `lib`, `app` (the nine editor-to-app edges the design leaves); `app` → everything; `automation` → everything; `tests` and `tools` → everything.

Pure code motion: no pattern changes, no behaviour change; each repair is its own commit, verified by the test that imports the touched modules. Order is the builder's. A repair that turns out to need more than moving a file, or moving helpers and the record type they operate on, is not done here: record it in `docs/notes/layering.md` with the edge and the reason, and leave the edge.

- [ ] **Step 1: Write `scripts/check-layers.sh` and run it on the moved tree**

The script scans `^import ` lines of every `.dl` file under the unit directories and reports each forbidden edge as `FILE: import PATH`. Run: `bash scripts/check-layers.sh`.
Expected: exactly the edges listed in design §5 (`bim_import`, `bim_ifc`, `bim_ifcx` → `graphics/bim_scene.dl`; `bim_steel_profiles` → `formats/bim_file.dl`; `bim_clash` → `graphics/bim_scene.dl`; `bim_section_gpu` → `app/bim_view_panel.dl`; `bim_drawing_rules`, `bim_images` → `editor/bim_editor.dl`), plus `model/bim_schedule.dl` → `model/bim_clash.dl` once clash has moved. Anything else is a finding to report before continuing.

- [ ] **Step 2: Move the four files that belong higher up**

`git mv graphics/bim_section_gpu.dl app/`, `git mv graphics/bim_drawing_rules.dl graphics/bim_images.dl editor/`, `git mv model/bim_clash.dl model/bim_schedule.dl graphics/`; rewrite their importers' `import` lines. Verify: `bash scripts/check-layers.sh` no longer lists those edges; compile `bash build.sh test clash schedule images view_display` → PASS. Commit: `Move section GPU, drawing rules, images, clash and schedule to their units`.

- [ ] **Step 3: Mesh records down to model**

In `graphics/bim_scene.dl`, find the record type and the helpers the three format modules use (`the bim reference text of`, `the bim label text of`, `the bim mesh shape of`, `the bim level index of`, `the bim storey elevation of`, `the bim prototype of imported mesh`, `the bim meshes of`); move the record type and those helpers unchanged into `model/bim_mesh.dl`, import it from `bim_scene.dl` and the three format modules, and drop their `bim_scene` imports. If a helper reads scene state beyond the record, stop and record per the rule above. Verify: `bash scripts/check-layers.sh` is silent on those edges; `bash build.sh test ifc ifcx ifc_read model` → PASS. Commit: `Move mesh records from the scene to the model`.

- [ ] **Step 4: File-content helpers down to model**

Identify the `bim file` patterns `model/bim_steel_profiles.dl` uses; move those helpers (plain file-content reading, no `.bim` format knowledge) into `model/bim_text_file.dl`, imported by both `formats/bim_file.dl` and `bim_steel_profiles.dl`. Verify: `bash scripts/check-layers.sh` prints nothing at all; `bash build.sh test steel_library file` → PASS. Commit: `Move file-content helpers below the formats`.

### Task 12: Compile, run and measure (the done criterion on Linux)

Start only after Task 4's runs have finished; one compiler at a time.

- [ ] **Step 1: Fast headless checks**

Run: `rm -rf generated && bash build.sh test platform ui_layout plan_pan text_glyphs`
Expected: four `PASS` lines (these four do not import the kernel; a failure here is a path or import problem).

- [ ] **Step 2: Kernel fixtures from the new location**

Run: `python3 -B kernel/tests/verify.py --compiler "$DYNLEX_ROOT/build/dynlex" --filter 'core' --filter 'arena*' --filter 'brep_boolean*' --optimization O0`
Expected: every selected fixture passes against its unchanged `expected.txt`.

- [ ] **Step 3: Development build and the pavilion**

Run: `bash build.sh dev && bash build.sh run-dev --example`
Expected: the window opens with the demonstration pavilion, the fonts render (no "Could not load the font"), the plan and 3D views draw; close the window; exit code 0. Then `bash build.sh dev-test sheet_cache import_metadata_cache` → both PASS through the generated self-test.

- [ ] **Step 4: The full test set**

Run: `/usr/bin/time -v bash build.sh test 2> build-test-all-after.time`
Expected: the same PASS set as Task 4 Step 2 (any test that failed before may still fail; no new failure).

- [ ] **Step 5: Optimised application and the after-measurements**

Run the Task 4 Step 2 commands against this tree (`app`, `dev`, the three tests, the full set from Step 4) and add their rows to `docs/notes/build-times.md` with stage `after stage 1`. The numbers should match the baseline within noise: stage 1 changes layout, not unit size.

### Task 13: Documentation and ADRs

**Files:**
- Modify: `CLAUDE.md`, `README.md`, `docs/roadmap.md` (line 102), `docs/TWEE-COMPUTERS.md` (lines 8, 43–58, 116), `docs/WERKBORD.md` (path mentions and the freeze claim), `docs/notes/application-and-toolchain.md` (the build section), `docs/notes/windows-release.md` (the snapshot's commit).
- Create: `docs/architecture/decisions/0007-kernel-source-lives-in-this-repository.md`, `docs/architecture/decisions/0008-compile-units-with-c-abi-seams.md`, `docs/notes/README.md`, `docs/notes/build-times.md` (from Tasks 4 and 12), `docs/notes/layering.md` if Task 11 left an edge.

- [ ] **Step 0: Identify the fork commit behind the v0.1 source snapshot**

```bash
mkdir -p /tmp/snapshot && gh release download v0.1 --pattern "Open-BIM-Studio-0.1-source.tar.gz" --dir /tmp/snapshot && tar -xzf /tmp/snapshot/Open-BIM-Studio-0.1-source.tar.gz -C /tmp/snapshot
for c in $(git -C "$DYNLEX_ROOT" log --format=%h origin/codex/cadkernel-port -- src/cpp lib | head -40); do git -C "$DYNLEX_ROOT" archive "$c" src/cpp | tar -t | sort > /tmp/a.txt; (cd /tmp/snapshot/*/ && find src/cpp -type f | sort) > /tmp/b.txt; diff -q /tmp/a.txt /tmp/b.txt > /dev/null && echo "candidate $c"; done
```
For each candidate, `diff -r` the snapshot's `src/cpp` against `git archive` of that commit; the commit with no differences is the snapshot's. Record it in `docs/notes/windows-release.md` as "The v0.1 source snapshot is the fork at COMMIT (verified by directory diff on DATE)". If no commit matches, record the nearest and the differing files.

- [ ] **Step 1: `CLAUDE.md`**

First paragraph: the application lives in the unit directories `kernel/`, `model/`, `formats/`, `graphics/`, `editor/`, `app/`, `automation/`, `content/` (content from stage 4), with `tests/`, `tools/`, `installer/`, `platform/`, `patches/` and `lib/` as the design describes; `build.sh` at the root builds it; the compiler is a separate checkout named by `.dynlex-root.local`. Replace the "Do not add product code, scaffolding, or build tooling during phases 0–3" bullet with: product code lives in the unit directories; experiments stay in `spikes/`, clearly marked as throwaway. Keep every other rule.

- [ ] **Step 2: `README.md`, roadmap, two-computer documents**

`README.md`: the build section runs from the repository root (`cd open-bim-studio`, `bash ./build.sh ...`), the layout tree at lines 160–180 shows the unit directories, every `spikes/dynlex-bim-slice/...` link points at `docs/notes/...`. `docs/roadmap.md` line 102 and `docs/TWEE-COMPUTERS.md`: ownership by unit directory (computer 1: `app/`, `editor/`, `model/`, `graphics/`, `formats/` and their tests; computer 2: `build.sh`, `toolchain.sh`, `scripts/`, `.github/workflows/`, `installer/`, `platform/`, `patches/`, `lib/`; agree first: `kernel/`, `graphics/vulkan/`, `graphics/shaders/`). `docs/WERKBORD.md`: paths updated and the freeze claim marked as closing with this pull request.

- [ ] **Step 3: ADR-0007 and ADR-0008**

From `docs/architecture/decisions/_template.md`, status `accepted`, date 2026-10-27, deciders: the maintainer. ADR-0007 "Keep the kernel source in this repository": context (four copies, §3 of the design), decision (§2.4), options (A: in the fork's `lib/`; B: here, chosen), evidence (the copy table, the overlay diff count), consequences (the fork's copies to retire by agreement, provenance commit `c2d32bea`), sources (the design, dynlex PRs 8 and 12). ADR-0008 "Compile units joined by C-ABI seams": context (R-18, issue 13, one unit of 102k lines), decision (§2.3 and §6), options (A: wait for a compiler module system; B: seams, chosen; C: files only, rejected as it changes nothing), evidence (R-18 numbers, `--emit-object` commit `f54f8475`), consequences (no inlining across seams, generated client, measurements of §11), sources.

- [ ] **Step 4: `docs/notes/README.md`**

One line per note: what it is, its original name and date. Include `build-times.md`.

- [ ] **Step 5: Verify and commit**

```bash
grep -rn "spikes/dynlex-bim-slice" --include="*.md" . | grep -vE "^./(docs/notes|docs/superpowers|docs/recovery|spikes|kernel/docs)/"
git add CLAUDE.md README.md docs
git commit -m "Describe the unit layout and record ADR-0007 and ADR-0008

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```
Expected: the `grep` prints nothing.

### Task 14: Pull request, the Windows workflow, merge

- [ ] **Step 1: Push and open the pull request**

```bash
git push -u origin restructure/one-tree
gh pr create --base main --title "Restructure the tree into unit directories (stage 1)" --body "Stage 1 of docs/superpowers/specs/2026-10-27-restructuring-design.md: the kernel seeded from the fork's port at c2d32bea plus the overlay, application modules in unit directories, builds from the repository root, generated per-OS imports, documentation and ADR-0007/0008. Same compiler, same tests. Computer 2: please review build.sh, scripts/, .github/workflows, installer/ and patches/, and run the Windows app workflow on this branch.

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```

- [ ] **Step 2: Windows workflow (computer 2)**

Computer 2 runs `gh workflow run windows-app.yml --ref restructure/one-tree` and reports the run URL. Expected: the four headless checks pass and the ZIP and MSI artifacts are produced. A failure is fixed on this branch by computer 1 (application side) or computer 2 (workflow side), each on its own files.

- [ ] **Step 3: Merge and lift the freeze**

After review: `gh pr merge --merge --delete-branch` (a merge commit, so the rename history of Task 9 stays one commit). Then `git switch main && git pull --ff-only`, `git tag -a restructure-stage-1 -m "Tree restructured into unit directories; same compiler, same tests"` and `git push origin restructure-stage-1`. Remove the baseline worktree: `git worktree remove ../obs-baseline`. Stage 2's plan starts from here.
