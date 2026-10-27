# Native Canvas Editing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Deliver a usable native local dev app with consistent canvas editing,
an IfcTypes manager, and model/UI automation.

**Architecture:** Keep geometry and transactions in the native editor. Add focused
modules for point parsing, preview rendering, grid spacing and the type manager.
Keep MCP/HTTP adapters separate from native document semantics.

**Tech Stack:** DynLex, Vulkan, Python standard library, Windows native input.

**Spec:** `docs/superpowers/specs/2026-10-26-canvas-editing.md`

## Global Constraints

- Native model coordinates are metres; input uses the active length unit.
- One DynLex compiler per machine; at most three tests per native bundle.
- No user-model loss or modification of an unrelated running app instance.
- English repository content; no private project data or conversation logs.
- Preserve existing positional record constructors when extending their state.

## Review Focus

- Invalid or incomplete numeric input leaves geometry and redo history unchanged.
- Multi-selection operations refuse unsupported members without partial copies.
- Modal input does not leak into canvas gestures or keyboard commands.
- Previews and final geometry use identical transforms, counts and units.
- Type edits round-trip with role-correct IFC classes and occurrence relations.

### Task 1: Grid and snapping behavior

**Files:** `bim_editor_core.dl`, `bim_plan_panel.dl`, `bim_view_panel.dl`,
`bim_section_gpu.dl`, new `bim_grid_pattern.dl`, new `bim_grid_controls.dl`,
`main.dl`, and corresponding native tests under the application overlay.

- [x] Add cursor, nearest-hover, extension, ortho, spacing and bubble tests.
- [x] Observe the cursor regression before implementation.
- [x] Implement common snapping, fixed screen symbols and atomic spacing batches.
- [x] Run native grid_cursor_snap, snapping_modes and grid_pattern checks.
- [ ] Run sketch_ortho and grid_screen_symbols with API regression tests.
- [x] Verify selection styles and plus controls in the native app.

### Task 2: Editing operations and exact input

**Files:** `bim_editor_core.dl`, `bim_editor.dl`, new `bim_point_input.dl`,
new `bim_modify_preview.dl`, `bim_ui.dl`, `main.dl`, native editing tests.

**Interfaces:** `the bim point input of inputText relative to basePoint along
pointerPoint metres per unit unitScale` returns `{valid, point}`. Preview rendering
uses `draw bim modification preview of editor in view inView in layout with camera
in frame`. Existing commands remain; 2016 Scale, 2017 Fillet, 2025 Array and
2390–2394 Chamfer/Stretch/Join/Lengthen/Split use the normal editor command path.

- [x] Add tests for strict coordinates, linear/radial arrays, scale and corner edits.
- [x] Implement atomic geometry operations and cancelable preview state.
- [x] Integrate numerical input for drawing and modification tool stages.
- [x] Add Home groups, tool options and visible input feedback.
- [ ] Verify preview/final agreement, cancel, undo and redo with mixed selection.

### Task 3: IfcTypes manager and export

**Files:** new `bim_type_manager.dl`, `bim_ifc.dl`, `bim_ui.dl`, `main.dl`,
native type-manager/export tests.

**Interfaces:** `a new bim type manager` creates state with `open`. Command 3901
opens it via `open bim type manager in statePtr for editorPtr`. Separate click,
key, character, scroll and draw functions operate this state. Main owns modal
event routing; the module owns type edits and transactions.

- [x] Verify role-correct type objects and occurrence bindings in classic IFC.
- [x] Implement export fixes and manager operations without dummy occurrences.
- [x] Wire the manager into Home and Manage; consume all input while open.
- [x] Verify native duplicate/edit/apply/delete/undo and classic IFC type bindings.
- [x] Verify type changes round-trip through IFCX.

### Task 4: API, MCP and local dev delivery

**Files:** `bim_api.dl`, `mcp/open_bim_studio_mcp.py`, new `mcp/windows_ui.py`,
new `mcp/open_bim_studio_http.py`, `mcp/test_mcp.py`, local build launchers.

- [x] Implement PID-bound UI input/screenshots and serialized UTF-8 transport.
- [x] Implement loopback HTTP and native grid/cursor operations.
- [x] Run 43 protocol, HTTP, transport and Windows binding tests successfully.
- [x] Compile a new `-O0` dev executable in a separate output directory.
- [x] Launch with its own API folder and verify actual native background edits.
- [x] Verify launcher configuration, reuse and background MCP on the new instance.
- [ ] Repeat screenshot and physical UI acceptance on the final executable.
- [ ] Run `git diff --check`, review scope, and document actual verification.


## Verification

- Native x64 development executable built with `-O0`; source hashes and the
  exact compiler artifact are retained with the local build. Its ten PE files
  passed architecture and runtime dependency checks.
- Live native API smoke: 32 calls passed, including grid batches, type edits,
  Unicode names and undo/redo. Original model counts, types and cursor were
  restored. Background stdio MCP exposed 39 tools and returned live state,
  type definitions and tool options. The launcher reused the same app process.
- Adapter suite: 43 tests passed for transport, protocol, loopback HTTP,
  strict JSON, process binding and Windows input argument handling.
- Type manager: all 87 Unicode, layout and IFCX save/open assertions passed.
- Compiler regression checker: reference invalidation, accessor precedence and
  self-cycle rejection passed. The 600-class precedence check completed in
  1.340 seconds on the local Windows machine, under its 30-second CI budget.
- Current-executable screenshot and physical UI acceptance remain pending.
