# Structural Floor Plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Issue the structural floor plan of a small house from the model: one plan per storey at 1:50 on a sheet, as a PDF, by the office's drawing rules, every tag, dimension and level read from the model.

**Architecture:** The plan panel's drawing functions move down into a `plan` extension point per module and the drawings module, which records one canvas for screen and sheet with a pen table; a view range gives every element a state (cut, below, above); the view's rules are keyed by IFC entity and predefined type; derived annotation is generated per view and never stored. Step 0 first makes the drawings module model-level, so that its tests compile in half a minute.

**Tech Stack:** DynLex (`docs/notes/dynlex-guide.md`), the module composer `tools/compose_modules.py`, the kernel behind `kernel/api/kernel.dl`, the existing canvas, sheet and PDF writer.

**Spec:** `docs/superpowers/specs/2026-10-30-structural-plan-design.md` (sections 4 to 7 carry the rules, the calls and the sequence this plan follows).

**Shape of this plan:** coarse to fine, as the maintainer works. Step 0 is in tasks; steps 1 to 5 are stated as deliverables with their files and tests and are detailed when the previous step has landed, in this document.

## Global Constraints

- Repository content is English; no client or project names from the source material; no names of competing calculation software.
- One DynLex compiler per physical computer; on computer 2 tests run with `scripts/dev-windows.ps1 -Tests a,b`, on Linux with `bash build.sh test a b`.
- `scripts/check-layers.sh` stays silent: no new import against the layer order; `scripts/layer-baseline.txt` only shrinks.
- Every existing test's output stays byte-identical until a task says it changes on purpose.
- Changes in another owner's module (`elements/*`, `pattern/grids`, `ui/panels`, `ui/editor`) go as separate pull requests for that owner's review; `views/*` is computer 2's.
- Commits end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`; pull request bodies end with the Claude Code line.

## Review Focus

Input classes the spec implies and no existing test exercises; each gets its test in the task that owns the code.

1. A dimension or tag that references an element which was deleted: the anchor is invalid and nothing is drawn, no crash (Task 0.2).
2. A model without grids or without a level below or above the view's level: the plan draws, the chain dimension and the view range bounds are simply absent (Step 3, Step 4).
3. A slab without a span direction: no arrow rather than a wrong one (Step 4).
4. A file saved before the IFC-keyed rules: its drawing types load with the new rules at their defaults and its views draw as before (Step 3).
5. A tag whose placement rule finds no room (column at the sheet edge, crop): the tag is placed at its fallback offset and still printed (Step 4).

---

## Step 0: the drawings module becomes model-level

Today `views/drawings/bim_drawing_rules.dl` imports the editor and `views/drawings/bim_drawing.dl` imports `elements/planar` for the wall, masonry and opening features of dimension references. After this step the module imports neither, its three baseline edges are gone, and its tests compile without the editor.

### Task 0.1: The Drawing Rules window moves to `ui/panels`

**Files:**
- Move: `views/drawings/bim_drawing_rules.dl` → `ui/panels/bim_rules_window.dl` (with `git mv`; the header comment stays)
- Modify: `ui/shell/main.dl` (the import line of the window)
- Modify: `ui/editor/bim_editor_core.dl`, `ui/panels/bim_plan_panel.dl` (drop the import of `views/drawings/bim_drawing_rules.dl`; neither calls anything in it)
- Modify: `scripts/layer-baseline.txt` (remove `views/drawings -> ui/editor/bim_editor.dl`)

**Interfaces:**
- Consumes: nothing new.
- Produces: the same functions under the new path (`draw bim drawing rules of …`, `apply bim rules hit …`, `a bim rules hit …`, the `bim rules …` action codes, the drawing-type commands `add/duplicate/rename/delete/cycle bim editor drawing type …`).

- [ ] **Step 1: Record the baseline**

Run: `scripts/dev-windows.ps1 -Tests drawing_types,views,phases,area_plans`
Expected: four PASS lines; note the compile seconds of each.

- [ ] **Step 2: Move the file and point the three importers at it**

`git mv views/drawings/bim_drawing_rules.dl ui/panels/bim_rules_window.dl`; in `ui/shell/main.dl` replace the import; in the editor core and the plan panel delete the import line.

- [ ] **Step 3: Compile and run the same tests**

Run: `scripts/dev-windows.ps1 -Tests drawing_types,views,phases,area_plans`
Expected: four PASS lines, outputs unchanged. A DIAG naming a `bim rules …` pattern in the editor core or the plan panel means that file did call the window after all: restore that one import and say so in the commit.

- [ ] **Step 4: Shrink the baseline and check the layers**

Remove the edge from `scripts/layer-baseline.txt`. Run: `bash scripts/check-layers.sh`
Expected: no output, exit 0.

- [ ] **Step 5: Commit**

```bash
git add -A views/drawings ui/panels ui/shell/main.dl ui/editor/bim_editor_core.dl scripts/layer-baseline.txt
git commit -m "Move the Drawing Rules window out of the drawings module"
```

### Task 0.2: Dimension references resolve through a `feature` extension point

The wall, masonry and opening-side branches of `the bim feature of` are the planar module's knowledge; the grid branch is generic. They move behind a dispatcher the composer writes, in the pattern of the `build` point (first module that answers wins).

**Files:**
- Modify: `tools/compose_modules.py:29-45` (`POINTS` gains `feature`)
- Modify: `tools/tests/compose_fixture/` (one fixture manifest declares `point: feature <file>`; `expected_compose.dl` gains the dispatcher)
- Modify: `views/drawings/records.dl` (the `bim anchor record` class moves here from `bim_drawing.dl`)
- Create: `elements/planar/features.dl`
- Modify: `elements/planar/MODULE` (`point: feature elements/planar/features.dl`)
- Modify: `views/drawings/bim_drawing.dl:8-9,233-300` (the two `elements/planar` imports go; `the bim feature of` keeps the grid branch and dispatches the rest)
- Modify: `views/drawings/tests/drawing.dl` (imports `generated/compose.dl` so the dispatcher is in its closure)
- Modify: `scripts/layer-baseline.txt` (remove `views/drawings -> elements/planar/bim_evaluate.dl` and `views/drawings -> elements/planar/bim_masonry.dl`)
- Test: `views/drawings/tests/drawing.dl` (existing, output unchanged), `views/drawings/tests/stale_reference.dl` (new, Review Focus 1)

**Interfaces:**
- Consumes: `bim reference record` and `bim join index record` as today; `the bim footprint of {bim wall record} in {bim model record} using {bim join index record}`, `the bim direction of {bim wall record}`, `the bim span of {bim wall record} at {number} reaching {number}` from `elements/planar/bim_evaluate.dl`; `the bim masonry of wall {bim wall record} in {bim model record} using {bim join index record}` from `elements/planar/bim_masonry.dl`; `the bim rough width of {bim opening type record}` from `bim/bim_model.dl`.
- Produces: in `generated/compose.dl` the dispatcher
  `function resolve bim module feature of {bim reference record:target} in {bim model record:modelValue} using {bim join index record:index} into {a pointer to a bim anchor record:anchor}:` returning a boolean (true when a module handled the reference's kind, whether or not the anchor is valid);
  in `elements/planar/features.dl`
  `function resolve bim feature of {bim reference record:target} in {bim model record:modelValue} using {bim join index record:index} into {a pointer to a bim anchor record:anchor} with planar elements:` returning a boolean; it handles the masonry near end, far end and line features, the wall start, finish, exterior and interior features, and the opening left and right features, and returns false for every other kind;
  `the bim feature of …` in `views/drawings/bim_drawing.dl` keeps its signature and result.

- [ ] **Step 1: Extend the composer, test first**

Add to one fixture manifest `point: feature <that module>/features.dl`, append the expected dispatcher to `tools/tests/compose_fixture/expected_compose.dl` in the `first-true` shape of `build bim module element`, with the header and the call line
`resolve bim feature of target in modelValue using index into anchor with {module} elements`.
Run: `python -B -m unittest tools.tests.test_compose_modules`
Expected: FAIL (the golden differs).

- [ ] **Step 2: Add the `feature` entry to `POINTS`**

Header and call as in Interfaces; `"style": "first-true"`.
Run: `python -B -m unittest tools.tests.test_compose_modules`
Expected: OK.

- [ ] **Step 3: Write the stale-reference test**

`views/drawings/tests/stale_reference.dl`: build a model with one wall through the model-level constructors (as `views/drawings/tests/drawing.dl` does), make a dimension from its start to its finish feature, print `measure valid 1`; delete the wall, measure again, print `measure valid 0`, and print `line valid 0` for `the bim dimension line of` it. Expected file with those three lines.
Run: `scripts/dev-windows.ps1 -Tests stale_reference`
Expected: PASS on the unchanged code (this pins today's behaviour before the move), or FAIL with a crash, which the move must then fix.

- [ ] **Step 4: Move the anchor record and write `elements/planar/features.dl`**

Move the `bim anchor record` class to `views/drawings/records.dl`. Create `elements/planar/features.dl` importing `elements/planar/bim_evaluate.dl`, `elements/planar/bim_masonry.dl` and `views/drawings/records.dl`, with the function of Interfaces whose body is the moved branches; `no bim feature` becomes a local function there too (both files may define one; `local function` is file-private). Add the `point:` line to `elements/planar/MODULE`. Regenerate: `python -B tools/compose_modules.py --root . --out generated`.

- [ ] **Step 5: Make `the bim feature of` dispatch**

In `views/drawings/bim_drawing.dl` delete the two planar imports; `the bim feature of` tests the grid kind first as today, then:
```
set anchor to no bim feature
if resolve bim module feature of target in modelValue using index into (the address of anchor):
    return anchor
return no bim feature
```
Add `import generated/compose.dl` to `views/drawings/tests/drawing.dl`.

- [ ] **Step 6: Run the tests that resolve references**

Run: `scripts/dev-windows.ps1 -Tests drawing,stale_reference,masonry_dimensions,dimension_tool,pavilion_drawings`
Expected: five PASS lines, `drawing` and the three others byte-identical to before.

- [ ] **Step 7: Shrink the baseline and check the layers**

Remove the two planar edges from `scripts/layer-baseline.txt`. Run: `bash scripts/check-layers.sh`
Expected: silent.

- [ ] **Step 8: Commit**

```bash
git add tools/compose_modules.py tools/tests generated views/drawings elements/planar/features.dl elements/planar/MODULE scripts/layer-baseline.txt
git commit -m "Resolve dimension references through a feature extension point"
```

### Task 0.3: The editor-driven tests leave the drawings module

`decimals`, `detail`, `units`, `drawing_standard` and `scalar_input` type keys into the editor or parse its point input; they test editor behaviour and belong with it.

**Files:**
- Move: `views/drawings/tests/{decimals,detail,units,drawing_standard,scalar_input}.dl` and their `.expected.txt` → `ui/editor/tests/` (same names)

- [ ] **Step 1: Move the ten files with `git mv`**

- [ ] **Step 2: Run them from their new place**

Run: `scripts/dev-windows.ps1 -Tests decimals,detail,units,drawing_standard,scalar_input`
Expected: five PASS lines (tests are found by name under any `*/tests/`).

- [ ] **Step 3: Measure the module's own tests**

Run: `scripts/dev-windows.ps1 -Tests drawing,drawing_types,stale_reference`
Expected: three PASS lines; note the compile seconds against Task 0.1's baseline, for the pull request.

- [ ] **Step 4: Commit and open the step's pull requests**

```bash
git add -A views/drawings/tests ui/editor/tests
git commit -m "Keep the editor-driven tests with the editor"
```
One pull request for the step, reviewed by Elize, who owns every module it touches besides `tools/` and `views/` (`ui/panels`, `ui/editor`, `elements/planar`); the three tasks edit adjacent lines of `scripts/layer-baseline.txt` and would conflict as separate branches. The pull request body names the compile seconds before and after.

---

## Steps 1 to 5: deliverables, to be detailed when reached

### Step 1: The model gains what the rules name (spec §5, "the model gains")

- Deliverable: linear roles `lintel` (IfcBeam.LINTEL), `brace` (IfcMember.BRACE), `foundation beam` (IfcFooting.STRIP_FOOTING) beside column, beam and pile; the plate role `footing` (IfcFooting.PAD_FOOTING, PILE_CAP) beside floor and roof; `span` (a direction in the slab's plane, absent allowed) and `system` (in situ, hollow-core, composite) on `bim slab record`; `loadBearing` on `bim wall type record`, default true for masonry and concrete layers, false for timber frame; the IFC writer and reader carry the predefined types and `Pset_WallCommon.LoadBearing`.
- Files: `elements/linear/records.dl`, `bim/bim_model.dl` (role codes and names), `elements/planar/records.dl`, `ifc/bim_ifc_native.dl`, `ifc/bim_ifc_read.dl`, `exchange/ifcx/*` (the two fields), their tests.
- Tests: `linear_roles` (new), `slab_span` (new), an IFC round trip of each role, `ifc_read` and the ifcx tests unchanged.
- Owner: Elize (`elements/*`), the maintainer (`bim/`, `ifc/`, `exchange/`); may run on another machine beside Step 2.

### Step 2: One canvas for screen and sheet, with the pen table (spec §5, first three paragraphs)

- Deliverable: a `plan` point in the composer; the item records in `views/drawings/plan_items.dl` (cut face, outline with state, centreline with style, tag, span arrow, level circle, dimension request), each naming the IFC entity and predefined type of its element; `views/drawings/bim_plan_pens.dl` with the pen table of spec §4 per drawing standard and `record bim plan items … into {canvas} at scale …`; `plan.dl` in `elements/planar`, `elements/linear` and `pattern/grids` producing what the panel draws today for walls, plates, linears and grids; the plan panel and the sheet both record the items, the editor record gone from those functions.
- Files: `tools/compose_modules.py`, `views/drawings/{plan_items,bim_plan_pens,bim_plan}.dl`, `elements/planar/plan.dl`, `elements/linear/plan.dl`, `pattern/grids/plan.dl`, `ui/panels/bim_plan_panel.dl`, `ui/shell/bim_app_parts.dl`.
- Tests: `plan_items` (new: the items of a two-wall, one-column, one-grid model, as text), `pens` (new: widths per standard and scale); `plan_pan`, `sheets`, `pavilion_drawings`, `grid_sheet` byte-identical until Step 4.

### Step 3: The view range, the three states and the IFC-keyed rules (spec §5, "three states" and "the layered properties")

- Deliverable: `cutHeight`, `depthBelow`, `heightAbove` on the view definition with the defaults of spec §5; the state of an element (cut, below, above) decided in `views/drawings` from the element's extent; the category rules of `views/common/bim_view.dl` keyed by IFC entity and predefined type with `LoadBearing` as a key, migrated once from the native categories when a file loads; the `bim drawing type record` gains discipline, view range defaults and pen set.
- Files: `views/common/records.dl`, `views/common/bim_view.dl`, `views/drawings/records.dl`, `exchange/ifcx/*` (the new fields), `views/common/tests/*`.
- Tests: `view_range` (new: a beam above and a beam below the cut get their states; a view on a level without neighbours has no bounds), `rules_migration` (new: a file from before loads with the same visibility; Review Focus 4), `views`, `view_display`, `drawing_types` updated on purpose where the rule keys change.

### Step 4: The structural items by the rules (spec §4)

- Deliverable: hatch per material and state; centrelines dotted or not by the floor system beneath; tags by their placement rules with the fixed offset and fallback (Review Focus 5); floor fields with type, span arrow (none without a span; Review Focus 3) and top level; level circles; chain dimensions per grid direction with the total (none without grids; Review Focus 2); the load-bearing rule on the "Structural" type; beam labels, pile numbers and the pile table retired from the screen-only code into the items.
- Files: the three `plan.dl` files, `views/drawings/{bim_plan,bim_plan_tags,bim_plan_dimensions}.dl`, `views/common/bim_view.dl` (the rule), `materials/bim_hatch.dl` only if a pattern is missing.
- Tests: `structural_items` (new: the tag texts, pen widths and dimension values of a small model, as text), `plan_items` updated on purpose.

### Step 5: The pilot house, its structural plans and the sheet (spec §5, "the pilot house")

- Deliverable: `views/drawings/bim_demo_house.dl` building the house of spec §2 with the model-level constructors; `--house` in `ui/shell/main.dl`; a structural plan per storey and one A2 sheet at 1:50 per plan with the title block; `bash build.sh house-sheets` (or the Windows equivalent) writing the PDFs under `build/`; the maintainer's look with the examples beside it.
- Files: `views/drawings/bim_demo_house.dl`, `ui/shell/main.dl`, `scripts/`, `docs/domain/drawings-from-model.md` (the honest scoping, filled in from what this plan measured).
- Tests: `house_plan` (new: the items of the ground-floor plan as text), `house_sheets` (new: the PDF files exist and their text streams contain the tags).

---

## Self-review notes

- Spec coverage: §3 first-version items map to Steps 2 to 5; §4 rules to Step 4; §5 calls to Steps 0 to 3 and 5; §6 (fit with the planning round) needs no task of its own; §7's sequence is this plan's.
- The Review Focus tests are owned: 1 by Task 0.2, 2 and 5 by Step 4 (2 also by Step 3), 3 by Step 4, 4 by Step 3; they are named in those steps and get their assertions when the steps are detailed.
- Names used across tasks: `resolve bim module feature of …` (dispatcher), `resolve bim feature of … with planar elements` (implementer), `bim anchor record` in `views/drawings/records.dl`; later steps name their records when detailed.
