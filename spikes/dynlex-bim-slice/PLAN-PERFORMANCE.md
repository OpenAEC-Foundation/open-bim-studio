# Plan interaction performance

Decision question: which work must run during plan interaction, and which work
belongs to a model, view or layout change?

## Evidence and scope

The native model plan, a registered vector reference and a sheet are different
workloads. Count reference triangles and draw batches as well as building objects.
Private model inventories, traces and screenshots stay outside this repository.

The investigated development binary used `-O0`. Its native-plan stack samples during
pointer movement repeatedly reached `the bim promoted count` through managed string
retain/list access. Other samples reached ribbon text measurement and presentation
inside the Intel Vulkan driver. These are qualitative hotspot observations, not
statistical percentages or evidence that all drawing is CPU rasterized.

## Findings and changes

| Path | Finding | Treatment |
|---|---|---|
| Main-loop import metadata | Linked IFC path and promoted GlobalId count scanned the model properties every frame, including native-only models. | `bim_import_cache.dl` refreshes these values when the document revision changes. |
| Native plan | Existing CPU/GPU recordings persist; panning shifts them. Scale changes invalidate recording. | Preserve the panning cache. Separate zoom decoding costs from ordinary pointer work. |
| Vector references | Coordinates stored as property strings are split, parsed and transformed when the view is recorded. | Repeated decoding on zoom remains a follow-up; bulk drawing data should not burden general metadata lookups. |
| Sheets | CPU recordings persisted, but every drawn frame replayed/streamed their vertices and text again. | A full sheet now retains the GPU canvas until its recording changes. |
| Sheet invalidation | Previous key omitted vertical placement, framebuffer size and session viewport visibility. | `bim_sheet_cache.dl` includes them, along with revision, sheet ID and exact density/placement. |
| Pointer queries | Snapping/hover work runs each rendered frame over a plan. Nearby segment intersection uses a nested pair loop. | Profile before caching: invalidation must cover camera/model/view/tool state as well as the pointer. |
| Plates and selection | Static plate edges are emitted each frame; selecting a component can expand unrelated component sketches. | Candidates for subsequent static recording and selected-instance-only queries. |
| Property panel and ribbon | Rows and caption layout are calculated every frame. Property/setting lookups use linear scans. | Measure these stages; avoid assigning percentages from isolated stack samples. |

The Vulkan context has one resident canvas buffer. A full sheet owns it; switching
back to a plan changes the owner key and restores the plan upload. Tiled plan+sheet
mode keeps the plan resident and replays the sheet separately. Replacing that same
buffer twice in one frame would corrupt the other pane. Multi-canvas slots remain
separate work.

Document revisions increase on new/open/commit/undo/redo. The import metadata cache
belongs to one editor's document lifecycle. It does not persist in model files or
share state across editors. Import filtering still follows the existing promoted
count behavior; this change does not introduce a different IFC filtering policy.

## Diagnostics and validation

`OBS_PROFILE_FRAMES=1` prints optional `OBS_FRAME` diagnostics to stdout. Fields:

- `view`, `sheet`: plan view ID and whether a sheet is active;
- `pointer_us`: pointer/snap query work;
- `plan_us`, `rerecorded`: static plan recording/upload and plate drawing;
- `sheet_us`: sheet recording/upload/replay;
- `properties_us`: property row generation and drawing;
- `cpu_us`: frame preparation before presentation;
- `presented_us`: elapsed CPU time through presentation, including waits;
- `gpu_us`: the renderer's existing GPU timer, a separate measurement.

Stage times are microseconds. They do not constitute an end-to-end input-latency
measurement. Normal runs do not print these diagnostics or read additional stage
clocks. Runtime comparisons must record compiler and optimization level; `dev` and
`dev-test` default to `-O0`, while `app` uses `-O2`. `BIM_DEV_OPT_LEVEL=2` allows an
optimized combined app/self-test build.

Use the same model, viewport size, panels, zoom and event path. Record idle,
pointer motion, pan, wheel zoom, component selection and view switching separately.
Verify the active view after switching: short synthetic clicks can be missed under
load. Discard wrong-view runs. Sent events and process CPU consumption are not FPS.

`sheet_cache` checks reuse and invalidation after edits, sheet switches, density
changes, vertical movement, framebuffer resize and hidden-element changes.
`import_metadata_cache` checks link/promotion state after commit, undo and redo,
and that unchanged frames reuse the inspected metadata. Headless tests do not
establish correct GPU rendering: app switching, tiled views, resizing, hiding and
visual checks are required separately.

## Object intelligence

Selectability, native parameters and building semantics are different properties.
Native walls/plates/members, hosted openings and generated frame systems can have
editable parameters and relationships. An explicit space polygon does not by itself
prove automatic boundary following. A 2D component of editable lines is not a
semantic 3D stair or sanitary object. Registered source artwork and sheet borders
remain references. Audit actual host links and IFC classes rather than inferring
intelligence from appearance or a generic component label.

## Provisional verdict

Runtime evidence supports eliminating repeated import metadata scans. Sheet
streaming and reference coordinate decoding are independent costs established by
code inspection. The cache changes require app/visual validation before claiming a
speedup or pixel equivalence. Preserve building parameters and address these render
and metadata paths before simplifying the building model. Semantic conversion of
2D details is separate from rendering optimization.

The triangle replay now preserves batch order and per-vertex RGB in one triangle
draw, followed by the existing label draws. Previously each recorded colour batch
started a separate GPU draw despite sharing its pipeline and clip. Incomplete
trailing triangles are discarded within each source batch, matching standalone
triangle-draw behavior and preventing cross-batch triangles. CPU canvas contents
and SVG/PDF serialization are unchanged. The optional diagnostics also expose
`canvas_batches`, `canvas_vertices` and total `draw_batches` for runtime checking.

The batching argument relies on triangle-list assembly and strict primitive order:
[Vulkan drawing commands](https://docs.vulkan.org/spec/latest/chapters/drawing.html#drawing-primitive-order)
and [rasterization order](https://docs.vulkan.org/spec/latest/chapters/primsrast.html#primsrast-order).
The current canvas vertex shader reads attributes without vertex-index side
effects; the pipeline does not request relaxed rasterization order. Keeping each
batch's complete triangles in sequence preserves their framebuffer operation order.
This is a correctness argument; visual validation remains a separate check.

## Upstream compiler compatibility

Upstream DynLex `95d87e0e` was fetched into an isolated clean worktree and its C++
compiler built successfully. The optimized BIM app/self-test compile then aborted
with `cached class instantiation request refers to a missing instantiation`.
This is an internal compiler invariant failure, not a low-memory guard stop.
The candidate was not selected as the default BIM toolchain. App validation uses
the previously working compiler with the same CAD libraries. No compiler source
changes are included in this rendering change.

Stage clocks measure elapsed wall time, including scheduling. In particular,
`cpu_us` labels preparation elapsed before presentation; it is not process CPU time.
`presented_us` includes waiting. Process CPU comparisons must be measured separately
(e.g. process accounting counters) and must not be conflated with these durations.

The local `-O2` app attempt with the previously working compiler reached the
available-memory guard on a 16 GB machine and produced no usable app. The active
control candidate instead uses `-O0`, matching the baseline, with both cache
fixtures. This isolates source changes from optimization-level effects. Separate
IR emission/optimization is a compiler/toolchain follow-up; it has not been
implemented or validated here.

## Controlled runtime comparison (24 October 2026)

The baseline and candidate used the same compiler, `-O0`, model and 1440 × 900
window. No compiler ran during measurement. Four seconds of pointer motion used
2.21 → 0.81 process CPU seconds in the native plan and 3.63 → 1.07 on the native
sheet. Pan gestures plus settling used 2.56 → 0.89 CPU seconds for the native plan;
alternating native-plan zoom used 2.85 → 1.38. Reference artwork zoom remains a
hotspot (5.00 → 3.84). These are workload CPU comparisons, not measured FPS or
end-to-end latency, and do not establish fast viewport manipulation.

Both cache fixtures passed (14 assertions) in the combined application build.
A 904 × 608 sheet-content screenshot region matched the baseline exactly
(549,632 pixels, zero differences); the SVG output was byte-identical. This checks
render preservation, not geometric fidelity to the private source drawings.

Next scope: independent retained sheet/view canvases, camera-only sheet pan/zoom,
and selectable sheet viewports with move/copy and viewport-title types. The current
single-canvas tiled fallback still streams sheet geometry. Imported raster images
must be retained textures, separate from physical model geometry.
