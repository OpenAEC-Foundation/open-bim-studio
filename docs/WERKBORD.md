# Work board — two computers

## How this board works (from 31 October 2026)

**Claims are made per module in GitHub issues.** Ownership per module is in
[OWNERS.md](OWNERS.md); cross-module claims and decisions go in
[#13](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/13). This board only holds
**code reservations** (command, property, setting and tool codes) and **handovers between
computers**. Do not add new task claims here. See [the working agreements and start
instructions](TWEE-COMPUTERS.md).

Previous rule (reference date 23 October 2026, superseded by the rule above): current claims
went via an issue/draft PR with task, owner, branch and files; the board was updated as soon as
a task was handed over or completed; an old claim did not disappear automatically because a
session dropped out.

## Code reservations

These codes stay reserved even though the claims that reserved them are closed. Do not reuse a
reserved number for another function. Record new public command codes in advance.

| Code / range | Kind | Reserved for | Reserved by (date) |
|---|---|---|---|
| **2228** | command | Bending schedule | PC1, `feature/steel-baseplates` (24 October) |
| **2229** | command | Optional reinforcement diameter display | PC1, `feature/steel-baseplates` (24 October) |
| **2270** | command | Linked PNG image import | PC1, image references (26 October) |
| **2271–2279** | commands | Sheet board, viewport title types, move/copy/delete, deactivate, and fit | PC1, interactive sheets (26 October) |
| **2313** | command | **Base plate** | PC1, `feature/steel-baseplates` (24 October) |
| **2314** | command | Opening detail | PC1, `feature/steel-baseplates` (24 October) |
| **2320–2330** | commands | Steel recipes, welds and reusable connection types | Connection module, `feature/connection-module` (26 October) |
| **2350** | command | Fastener-library placement entry, if needed | `stagiairopenaec1`, `mod/elements-connection/fastener-components` (29 October) |
| **2360** | command | Sketch Split | Computer 1, restructuring stage 1 (27 October) |
| **27** | tool id | Sketch Split | Computer 1, restructuring stage 1 (27 October) |
| **2400100–2400105** | settings on the opening | Opening-detail settings | PC1, `feature/steel-baseplates` (24 October) |
| **2400400** | view setting | Technical plan palette (unfilled room interiors, black room labels, blue plan grids) | PC1, plan presentation (24 October) |
| **2400410** | setting | Grid head | PC1, sheet paper units (24 October) |
| **2400600–2401599** | settings on the sheet | Viewport title type metadata | PC1, interactive sheets (26 October) |
| **12600–12604** | properties | Opening detail | PC1, `feature/steel-baseplates` (24 October) |
| **12610** | property | Toggles the technical plan palette | PC1, plan presentation (24 October) |
| **12611** | property | Grid head | PC1, sheet paper units (24 October) |
| **60000-62047** | properties | Connection additions, sixteen slots per connection addition | `stagiairopenaec1`, fastener components (29 October) |
| **62048-62079** | properties | Reusable connection types (recorded in [notes/fastener-components.md](notes/fastener-components.md), not originally on this board) | `stagiairopenaec1`, fastener components |

Identifiers with a fixed meaning that must stay compatible:

- Complex style **2** denotes a one-column base plate; addition kind **3** denotes an anchor
  group. Existing styles remain unchanged.
- Existing connection kind/style IDs and 10000-series properties retain their meanings. Native
  older-file defaults must remain explicit.
- Window recipes are appended after the existing 21 entries so stored indices remain stable;
  timber and Reynaers window recipes use append-only recipe indices 33–42.

## Assignments and handovers

| Date | What | From | To | Notes |
|---|---|---|---|---|
| 28 October 2026 | `pattern/common`, `pattern/grids`, `pattern/facade` | Elize (broad module claim) | Nino (@nino2-aec), Linux machine `aia07-MP50` | Coordination [#22](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/22); recorded in [OWNERS.md](OWNERS.md) |
| 30 October 2026 | Views and drawings (`views/*`) | — | Computer 2 | [#67](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/67); recorded in [OWNERS.md](OWNERS.md) |
| 31 October 2026 | Compiler memory and compile time (proposed as `pc2/compiler-memory`; separate DynLex fork, baseline first) | Proposed, never claimed | **Computer 2** (assigned) | Bears on R-18 ([risks.md](risks.md)) and ADR-0004. No branch exists yet; open a claim in a GitHub issue when work starts |
| 31 October 2026 | Windows/Linux builds and installers (proposed as `pc2/build-installers`; CI/build/installer, no modelling code) | Proposed for PC2, never claimed | **Maintainer** | No branch exists |

## Kept, pending

These are **not** closed by the decision of 31 October; their fate is decided separately
([open-questions.md](open-questions.md), question 39).

| Item | State on 31 October 2026 | Status |
|---|---|---|
| Branch `restructure/one-tree` | One commit not on `main`: `e41bedd` "Record the stage 1 build times measured on the Linux machine" | Kept, pending |
| Probe commit on `mod/elements-connection/fastener-components` | One commit not on `main`: `663f348` "Add a direct implicit CSG fastener rendering probe"; the rest of the branch is on `main` (PR #25) | Kept, pending |

Left as-is, not closed and not yet moved to an issue:

| Task | Owner | Branch | Files / boundary | Status (23 October) |
|---|---|---|---|---|
| Assemble and publish release | PC1 / coordinator | `main` | Integration, tested artefacts, tags | Blocked on app/installation tests |

## Review of the board — 31 October 2026

Since the module split of 28 October, ownership is per module in [OWNERS.md](OWNERS.md) and
claims go per module. The review of 31 October found that several entries on this board
predated that and referred to branches or files that no longer existed in that form. The
review itself released nothing — under the old rule a claim ended only when its owner said
so — and put the question to the maintainer ([open-questions.md](open-questions.md),
questions 38–40). The maintainer decided on 31 October 2026 to close the stale claims, keep
the code reservations, translate the board to English and move claims to per-module GitHub
issues. That decision has been carried out on this board. Findings and outcome:

- The table of 23 October named files by their old flat paths and `main` as branch. All rows
  marked "integrated locally" or "code present" still listed an open app/GUI check.
  *Outcome:* closed (work on `main`); remaining checks belong in the module's issues.
- `feature/steel-baseplates` (PC1 claims of 24 and 26 October) had no remote branch; its units
  (base plate, fastener detail, plan presentation, image import) were on `main` in their
  modules. Command and property numbers reserved there (2228, 2229, 2270–2279, 2313, 2314,
  2400100–2401599, 12600–12611) stay reserved. *Outcome:* claims closed; numbers listed under
  [Code reservations](#code-reservations).
- `pc2/compiler-memory` and `pc2/build-installers` were proposed and never claimed; no branches
  existed. *Outcome:* compiler memory assigned to computer 2; builds and installers to the
  maintainer (see [Assignments and handovers](#assignments-and-handovers)).
- `feature/connection-module`, `restructure/modules` and `mod/pattern/ownership` were fully
  merged into `main`; `restructure/one-tree` held one unmerged commit (stage 1 build times) and
  `mod/elements-connection/fastener-components` one unmerged probe commit. *Outcome:* the claims
  on the merged branches are closed; the two unmerged commits are
  [kept, pending](#kept-pending).
- Views and drawings (`views/*`) moved to computer 2 on 30 October (#67). *Outcome:* recorded
  as a handover.

## Closed claims (31 October 2026, maintainer decision)

Each claim below was closed by the maintainer on 31 October 2026. The original text is kept,
translated, as a record. File names are as written at the time; most refer to the flat paths
from before the module split, and the units now live in their module directories (see
[OWNERS.md](OWNERS.md)). Code numbers mentioned here stay reserved (see
[Code reservations](#code-reservations)).

### Task table of 23 October 2026

| Task | Owner | Branch | Files / boundary | Status (23 October) | Closed because |
|---|---|---|---|---|---|
| Sketch ribbon and integration | PC1 / Codex | `main` | `bim_ui.dl`; integration after separate reviews | Integrated locally; app check open | Work is on `main`; app check belongs in the module's issue |
| Split face + undo + exact side start | PC1 / cursor_fix | `main` | `bim_editor.dl`, `bim_editor_core.dl`, related tests | Integrated locally; editor compile stopped because of memory | Work is on `main`; remaining check belongs in the module's issue |
| 3D side-face selection, drag and Split gesture | PC1 / render_diagnosis | `main` | `main.dl`, pick helper, `bim_scene.dl`, related tests | Integrated locally; pick core PASS, GUI check open | Work is on `main`; GUI check belongs in the module's issue |
| Native window style, section box, properties and viewcube | PC1 / Codex | `main` | App/UI; no concurrent PC2 edits | Code present; full new app check open | Work is on `main`; app check belongs in the module's issue |
| Roof/floor contour: keep the elevation plane | PC1 / Codex | `main` | `bim_model.dl` + `plate_anchor` | Integrated locally; 17 checks PASS | Work is on `main` |
| Floor openings | PC1 / Codex | `main` | Openings core; GUI still incomplete | Core integrated; 24 checks PASS, GUI still incomplete | Core is on `main`; the GUI work belongs in the module's issue |
| Compiler memory and compile time | PC2, after task acceptance | `pc2/compiler-memory` | Separate DynLex fork; baseline first | Proposed / not yet claimed | Proposal replaced by the assignment to computer 2 (see Assignments and handovers) |
| Windows/Linux builds and installers | PC2, after task acceptance | `pc2/build-installers` | CI/build/installer; no modelling code | Proposed / not yet claimed | Never claimed; assigned to the maintainer instead |

The ninth row, "Assemble and publish release", is not closed; see [Kept, pending](#kept-pending).

### Building Systems ownership — 2026-10-28

**Closed:** `mod/pattern/ownership` is fully merged into `main` (PR #23) and the ownership is
recorded in [OWNERS.md](OWNERS.md); further pattern work is claimed in module issues.

Nino (@nino2-aec), Linux machine `aia07-MP50`, takes `pattern/common`,
`pattern/grids` and `pattern/facade`. Coordination and handover from Elize's
broad module claim: [#22](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/22),
with cross-module decisions in #13 and steel/connection interfaces in #6.
Ownership branch: `mod/pattern/ownership`, based on `main` `c5fdfc8`.
Product changes follow on `mod/pattern/<topic>` branches after checking for
active work in these paths. First task: establish the existing pattern test
baseline with the pinned toolchain. Kernel, steel connections and shared
editor/renderer changes remain with their existing owners unless separately
coordinated. No implementation or validation result is claimed by this entry.

### Module split — 2026-10-28

**Closed:** `restructure/modules` is fully merged into `main` (tag `restructure-modules`).

Branch `restructure/modules`, following [the design](superpowers/specs/2026-10-28-module-split-design.md)
and [the plan](superpowers/plans/2026-10-28-module-split-plan.md): every unit has
moved to its module, tests are per module, owners are in [OWNERS.md](OWNERS.md).
Claims go per module from now on; the freeze of stage 1 is lifted as soon as this
branch is on `main`.

### Connection fastener components — 2026-10-29

**Closed:** the branch's work is on `main` (PR #25) and the connection module's ownership is in
[OWNERS.md](OWNERS.md). The one unmerged probe commit is [kept, pending](#kept-pending);
command 2350 and properties 60000-62047 stay reserved.

Owner: `stagiairopenaec1`, Linux workstation `aia08` (Codex).
Task branch: `mod/elements-connection/fastener-components`, from `main`
`cfaf116`. The connection module ownership is recorded in `OWNERS.md` and
`CODEOWNERS`; other module ownership is retained. Public coordination:
[connection claim](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/6#issuecomment-6482914412),
[cross-module scope](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/13#issuecomment-6482914774).

Scope: native bolt, nut, washer and anchor components, sizes M8-M40,
explicit thread pitch and thread extent, classes 4.6/8.8 for external
fasteners, separate nut class, hot-dip/electrolytic zinc finish and optional
washer layouts. Commercial M40 dimensions stay distinct from standard M39.
Geometry, catalogue and parameter records belong in `elements/connection`.
Connection-only integration regions: the steel recipe factories,
`viewer/bim_scene.dl` fastener solids/lines, native connection read/write in
`exchange/ifcx/bim_file.dl`, and connection rows/edits in
`ui/properties/bim_editor_properties.dl`. A library placement entry may touch
`ui/editor/bim_editor.dl` and `ui/panels/bim_ui.dl`. No kernel, compiler,
Building Systems or unrelated rendering changes are claimed.

Reserved: command **2350** for a fastener-library placement entry if needed;
property codes **60000-62047**, sixteen slots per connection addition.
Existing connection kind/style IDs and 10000-series properties retain their
meanings. Native older-file defaults must remain explicit. Validation starts
with at most three focused checks per bundle, followed by application and
GUI/save/reopen checks. Status: claimed; implementation and verification pending.

### Restructuring stage 1 — computer 1 — 2026-10-27 (completed; tag `restructure-stage-1` at the merge)

**Closed:** stage 1 is merged (tag `restructure-stage-1`) and its freeze was lifted when
`restructure/modules` reached `main`. The branch `restructure/one-tree` itself, with one
unmerged commit, is [kept, pending](#kept-pending). Command 2360 and tool id 27 stay reserved.

Branch `restructure/one-tree`, following
[the design](superpowers/specs/2026-10-27-restructuring-design.md) and
[the plan](superpowers/plans/2026-10-27-restructuring-stage-0-1.md).
Files: all of `spikes/dynlex-bim-slice`, `.github/workflows`, `CLAUDE.md`,
`README.md` and `docs/`. Freeze: no other branch touches these files until
the stage 1 pull request is merged. Computer 2: only review of the workflow
and patch parts and running the Windows workflow; no concurrent edits.
Status: the move is on the branch; the freeze ends at the merge of the stage 1
pull request.

`origin/feature/connection-module` (25 commits, pushed until 2026-10-27 08:16,
before this claim) touches moved files and adds new modules under the old path.
After the stage 1 merge that branch must be rebased onto main, with the new
files placed per unit; a trial merge gives 42 conflicts.

Command `2360` and tool id `27` are reserved for Sketch Split. Do not reuse
these numbers for another function. Record new public command codes in advance.
See [the working agreements and start instructions](TWEE-COMPUTERS.md).

### PC1 claim — 24 October 2026

**Closed:** `feature/steel-baseplates` has no remote branch; its units (base plate, fastener
detail, plan presentation, window recipes, paper units) are on `main` in their modules. The
command, setting and property numbers reserved here stay reserved.

Codex owns `feature/steel-baseplates`: the single-column base-plate recipe,
connection validation and its ribbon/properties integration. Command **2313** is
reserved for **Base plate**. Complex style **2** denotes a one-column base plate;
addition kind **3** denotes an anchor group. Existing styles remain unchanged.
Files: `connections.dl`, `bim_connections.dl`, `bim_baseplate.dl`,
`bim_editor.dl`, `bim_editor_properties.dl`, `bim_ui.dl`, and related tests.

The same PC1 task fixes selection overlay clipping and adds view-tab dragging in
`main.dl`, `bim_workspace_tabs.dl` and `graphics/vulkan/context.dl`.
The Vulkan change separates overlay scissoring from its full-window projection;
mesh viewports and the batch record layout are unchanged. PC2 should not edit
these files concurrently. Full application/interactive validation is pending.

Additional PC1 scope on this branch: commands **2228** (bending schedule),
**2229** (optional reinforcement diameter display) and **2314** (opening detail).
Opening-detail settings use **2400100–2400105** on the opening; properties use
**12600–12604**. Window recipes are appended after the existing 21 entries so
stored indices remain stable. The application icon module and the two installer
asset lists are included in the user-requested taskbar-icon work.

Validation snapshot: `baseplate`, `workspace_tabs`, `viewport_overlay` PASS;
`connections_model` PASS in the preceding bundle. `opening_detail`,
`bending_schedule` and `reinforcement_schedule` are still running. Full app,
GUI, installer and large-steel-model checks remain pending. This is a development
branch, not a release or fabrication-ready connection library.

#### PC1 — fastener thread preview and service-network isolation

**Closed:** part of `feature/steel-baseplates`; `bim_fastener_detail.dl` is on `main` in
`elements/connection`.

`feature/steel-baseplates`: PC1 owns `bim_fastener_detail.dl`, the connection
line-mesh insertion in `bim_scene.dl`, and connector grouping in
`bim_network.dl`. Cosmetic thread is a bounded helix on the exposed start of
the fastener, with approximate pitch; it is not a manufactured thread profile.
It retains the connection's selection ID and uses the existing GPU line path.
Service connectors must share both their linear role and system assignment;
coincident pipes, ducts and cable trays must not form cross-discipline fittings.
Validation: `fastener_detail`, `network_isolation` and `fastener_scene` PASS
in `/tmp/obs-fastener-network-r3`, without compiler diagnostics. The isolated
fastener check also passes with only connection-kernel imports. Full application
visual inspection and the existing broad `network` regression remain pending.
The thread preview covers at most two diameters, with 192 line segments per
fastener; distant-view performance has not yet been measured.

#### PC1 — timber and Reynaers window recipes

**Closed:** part of `feature/steel-baseplates`; the `window_recipes` check is on `main` in
`architectural/openings`.

PC1 extends `bim_system_types.dl` with append-only recipe indices 33–42,
updates `system_types.expected.txt`, and adds the lightweight `window_recipes`
check. Sources and explicit schematic-geometry limits are in
`docs/notes/window-systems.md`. No model schema or new command codes.
Validation: `window_recipes` PASS (seven checks, no compiler diagnostics) in
`/tmp/obs-window-recipes`. Full gallery and GUI validation remain pending;
no new application build has been launched.

#### PC1 — technical plan presentation and registered reference review

**Closed:** part of `feature/steel-baseplates`; `bim_plan_presentation.dl` is on `main` in
`views/drawings`. Setting 2400400 and property 12610 stay reserved.

PC1 owns `bim_plan_presentation.dl`, the palette branches in
`bim_plan_panel.dl`, the view property in `bim_editor_properties.dl`, and
`tests/plan_presentation.*`. View setting **2400400** enables a technical
palette: unfilled room interiors, black room labels and blue plan grids.
Property **12610** toggles it. Section and 3D grids retain their existing style.
The plan recording key now includes the view ID, so view-local presentation
changes cannot reuse another view's cached plan. Screen and sheet plan drawing
use the same palette helpers. Full app/check build PASS in `/tmp/obs-plan-presentation-app` with no compiler
diagnostics; `plan_presentation` PASS (six checks). Live plan and SVG sheet
export inspected: technical colours and view-local persistence confirmed.
A registered private reference comparison still shows substantial geometric,
annotation and sheet-layout differences; visual equivalence is not established.
Private reference review data is kept outside the repository.

#### PC1 — sheet paper units, grid ends and custom frames

**Closed:** part of `feature/steel-baseplates`; the `paper_units` check is on `main` in
`views/sheets`. Setting 2400410 and property 12611 stay reserved.

PC1 owns the paper-unit member in `bim_canvas.dl`, grid/dimension symbol scaling
in `bim_plan_panel.dl` and `bim_drawing_standard.dl`, the sheet context/template
branches in `bim_app_parts.dl`, and the grid-head property in
`bim_editor_properties.dl`. Grid head setting **2400410**, property **12611**.
`OpenBIM_Drawing.CustomFrame=true` supports an independent frame viewport;
all-hidden template views no longer draw model annotations. View-bound vector
artwork is now included when recording sheets, as it already is in plan views.
Details: `docs/notes/drawing-fidelity.md`.

`paper_units` and existing `dimension_text` PASS in
`/tmp/obs-paper-units-check`. The full application with `paper_units`, `grid_sheet`, `plan_presentation`
PASS in `/tmp/obs-paper-plan-app-r3` (24 assertions, no compiler diagnostics).
Earlier staged compiles were stopped to complete template isolation checks.
Live plan, grid-head controls and SVG sheet export were inspected. The
registered private comparison improves, but complete source equivalence is
not established. A static frame template is reported separately from native
model geometry; it is not counted as model-detail completeness.
Private project source-frame and measured grid-chain data stay outside Git.

### PC1 claim — plan performance and object audit, 24 October 2026

**Closed:** part of `feature/steel-baseplates`, which has no remote branch; `bim_sheet_cache.dl`
and `bim_import_cache.dl` are on `main` (`views/sheets`, `exchange/import`). The upstream
compiler compatibility findings below are kept as a record.

Codex investigates native plan/source reference/sheet interaction separately on
`feature/steel-baseplates`. Files: `main.dl`, new `bim_sheet_cache.dl`, cache fixture,
`PLAN-PERFORMANCE.md`. Full-sheet resident GPU cache and opt-in frame-stage logging
are under validation. Preserve tiled views; do not replace two panes' GPU buffers
in one frame. Private project model/audit/screenshots remain outside Git.
Latest upstream DynLex `95d87e0e` was fetched and built in an isolated worktree;
compatibility checks are running with the existing CAD fork libraries. The dirty
CAD compiler/library checkout and default toolchain selection remain unchanged.

The same plan-performance claim includes `bim_import_cache.dl` and its fixture,
`bim_canvas.dl` triangle replay batching, and `build.sh`/README support for an
explicit optimized development/self-test build (`BIM_DEV_OPT_LEVEL=2`). An initial
cache fixture compile diagnosed uncast 32-bit test IDs where 64-bit IDs were
required; corrected before the optimized candidate compile. No app-ready claim yet.

Upstream compiler compatibility result: clean `95d87e0e` compiler builds, but the
BIM app compile aborts on a missing class-instantiation cache entry (13m13s,
peak 2.4 GiB; not an out-of-memory stop). Keep the default CAD fork/toolchain.
The optimized rendering candidate is rebuilding with the previously working
compiler. Core inspection points to the built-in list class; a trial rollback
cache-cleanup difference exists between upstream and the local fork and needs
an isolated compiler regression test before upstream adoption.

#### PC1 — image references and interactive sheets (26 October 2026)

**Closed:** part of `feature/steel-baseplates`; `bim_images.dl` and `bim_sheet_workspace*.dl` are
on `main` (`exchange/import`, `views/sheets`). Commands 2270–2279 and settings
2400600–2401599 stay reserved.

PC1 owns image-reference import, `bim_images.dl`, `bim_image_data.dl`,
`graphics/vulkan/images.dl`, the related canvas/context shaders and tests.
Command **2270** is reserved for linked PNG image import. This is in progress,
not yet a validated application feature. Physical drawing content must still
come from editable 3D objects; raster references are explicitly 2D underlays.

The user prioritizes sheet interaction: cursor-anchored fast pan/zoom, real
selectable viewports, move/copy and selectable viewport-title types. Work must
reuse resident GPU drawing data while navigating or previewing a move. Actual
interaction/frame measurements are required before claiming a high frame rate.
The open application contains unsaved user edits and must be preserved.

26 October candidate update: commands **2271–2279** are reserved for sheet board,
viewport title types, move/copy/delete, deactivate, and fit. Viewport title type
metadata uses **2400600–2401599** on the sheet. PC1 also owns
`bim_sheet_workspace*.dl`, `bim_sheet_renderer.dl`, `bim_workspace_tabs.dl`,
`bim_app_parts.dl` and their integration in `main.dl`/`bim_ui.dl`.
The tested render checkpoint **9b0767c** was pushed. Candidate details and explicit
validation gaps are in `docs/notes/sheet-workspace.md`.

### Connection module development — 2026-10-26

**Closed:** `feature/connection-module` is fully merged into `main`. Commands 2320–2330 stay
reserved.

The explicit module assignment extends this session to issue #6 on
`feature/connection-module`, based on `1768c2d`. Scope: connection kernel,
BIM adapter, native connection persistence, connection commands/properties,
headless tests and a synthetic steel hall example. Command range 2320–2330
is reserved for steel recipes, welds and reusable connection types. Existing
base-plate style 2 and anchor kind 3 remain compatible. No compiler changes.

The required full-build repair also renames local identifiers in sheet paper
recording and plan/mesh helpers to avoid DynLex pattern-word capture. These are
identifier-only changes; sheet/layout behaviour is unchanged.

The build repair includes `build.sh` and `tools/check_dynlex_locals.py`: a fast
application-source preflight for these proven local/pattern-name collisions,
with focused Python regression tests. It does not modify the compiler or the
active source snapshots/build scripts.

GUI validation exposed a connection-hole meshing hotspot in the overlay's
`lib/cadkernel/brep_append.dl`. The connection task also owns its bounded
face-component traversal repair and geometric regression checks: direct
arena-slot membership and adjacency, preserving seed and breadth-first order.
The compiler checkout is unchanged. Application readiness still requires the
full steel-hall scene and GUI checks.

### Compiler and drilled display geometry — 2026-10-27

**Closed:** part of the connection-module session, which is fully merged; `bim_plate_mesh.dl`,
`bim_swept_perforations.dl` and the perforation kernel (`kernel/fast/perforation.dl`) are on
`main`.

The explicit performance assignment extends this session to an isolated DynLex
compiler worktree. The connection task also covers `bim_plate_mesh.dl`,
`bim_swept_perforations.dl`, `overlay/lib/fastkernel/perforation.dl`, their scene
integration and geometry tests. `bim_profiles.dl` is included for the missing
rounded-box tangent points exposed by the hollow-brace drilling checks. Product geometry remains DynLex. The fast display
path accepts closed planar stock and separate through-bores; unsupported
cuts retain the existing general BREP path. Validation must establish volumes,
closed meshes, complete hall rendering and actual editor interaction.

`build.sh` and `toolchain.sh` accept an explicit `BIM_DYNLEX_COMPILER` for isolated
candidate benchmarking. Compiler-binary hashes must be recorded separately from
the library checkout commit. Compiler regression checks and application GUI
checks remain separate acceptance conditions. One compiler runs per machine.
