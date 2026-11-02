# Native component rendering

**Decision question:** After sharing component geometry on the GPU, what should
be measured before changing the native scene representation for large models?

**Status:** draft
**Author:** OpenAEC Foundation
**Last updated:** 2026-11-02

## Summary

Keep the existing GPU instancing path and measure the CPU scene separately.
It currently materialises world-space meshes before finding shared prototypes.
Camera fit and presentation waits must be corrected or identified before using
orbit results to justify a renderer rewrite.

## What it is

The native scene creates one local mesh per component definition, then stores
transformed positions for each placement in
`elements/object/scene.dl`. `viewer/bim_native_instances.dl` recovers a rigid
frame, hashes the local geometry and verifies matching vertices before sharing
GPU prototypes. Rigid placements now retain shared triangle indices; pure
translations also retain shared normals. The lists use the kernel's reference-counted ownership. `ui/panels/bim_view_panel.dl` uploads instance transforms and
retains independent element ordinals for picking and visibility.

That Open's documented alternative organises visible geometry into tiles and
uses camera-driven LOD and culling. Its model manager processes fragments with
a worker, and its model API retrieves geometry for selected item IDs on demand.
These are documented capabilities, not a measured speed comparison with this
application.

## Evaluation

| Criterion | Finding | Evidence type | Source / method |
|---|---|---|---|
| Geometry sharing | Native GPU prototypes and instance transforms already exist | inferred from source | Source paths above; `exchange/ifcx/tests/native_instances.dl` verifies reconstruction |
| CPU scene storage | World meshes remain per placement before GPU deduplication | inferred from source | `elements/object/scene.dl`, `the bim component triangles … placed by …` |
| Camera correctness | Previous fit omitted solid component instances | measured | `ui/shell/tests/fit_components.dl`; old orbit screenshots show only nearby objects |
| Worker processing | FragmentsModels uses a worker for fragment processing | claimed | [That Open model manager](https://docs.thatopen.com/api/@thatopen/fragments/classes/FragmentsModels) |
| View-dependent detail | Camera controls tile loading, culling and distant LOD | claimed | [That Open useCamera](https://docs.thatopen.com/api/@thatopen/fragments/classes/FragmentsModel#usecamera) |
| Requested geometry | Geometry can be retrieved for specified item IDs and LOD | claimed | [That Open getItemsGeometry](https://docs.thatopen.com/api/@thatopen/fragments/classes/FragmentsModel#getitemsgeometry) |

## Measurements

The reproducible native workload and orbit procedure are in
[`component-renderer-benchmark.md`](../notes/component-renderer-benchmark.md).
The generation benchmark stores real placements, not a single large mesh.
Do not compare an unfitted orbit, a synchronised presentation and an uncapped
full-scene orbit as if they were the same workload. Record build flags, the
actual selected device, presentation mode, raw timing samples and memory.
No That Open benchmark was run for this note.

A focused allocation probe retains 100,000 four-vertex native component meshes
and then regroups them five times. Both builds use `-O0`; this Linux process
measurement does not create a window or measure GPU rendering.

| Phase | Copying normals/indices (KiB RSS) | Sharing normals/indices (KiB RSS) |
|---|---:|---:|
| Retained world meshes | 49,656 | 29,356 |
| Fifth grouping pass | 60,632 | 40,336 |

These are measured process RSS values, including runtime and list overhead;
they are not sizes of the raw GPU buffers. The retained-mesh reduction is
40.9%; the fifth-pass reduction is 33.5%. In both cases repeated grouping
stabilises: automatic reference-counted cleanup rejects the hypothesis of a
per-pass temporary-batch leak. Do not manually free those containers' raw lists.

Reproduce with `build.sh probe native_instance_memory`, then
`python3 tools/probes/measure_native_instance_memory.py --binary
build/tools/native_instance_memory --out build/native-instance-memory.json`.
The measurement preserves the binary hash and synchronised phase samples.

### Desktop orbit, 2 November 2026

Measured on a Ryzen 7 9700X, 29 GiB RAM and RTX 5070 (12,227 MiB VRAM),
NVIDIA driver 595.99.02, X11/XWayland desktop. The 1440 by 900 framebuffer
includes the editor chrome. Each run fits the entire scene, waits for the
subsequent API response to establish completion of the deferred fit, settles
for three seconds, then follows the same finite process-local input trajectory
for 15 seconds. No compiler ran during these measurements. Source hashes and
zero undo steps were checked; fitted before/after screenshots were inspected.
These are individual runs, not a repeated-run confidence interval.

All runs use `-O0 -g`, automatic device selection without Vulkan loader filters,
and explicit uncapped IMMEDIATE presentation (`OBS_UNCAPPED=1`, reported mode
0, device kind 2). These are submitted frames, not monitor refresh rates or
release-build results. The frame preparation time includes prior GPU/fence/
image-acquisition waits. Normal FIFO presentation was not measured here.

| True component placements | Observed FPS | Presented p95 (ms) | GPU p95 (ms) | Peak process RSS (MiB) | API ready (s) |
|---:|---:|---:|---:|---:|---:|
| 100,000 | 180.5 | 7.194 | 4.424 | 618.4 | 3.831 |
| 250,000 | 109.8 | 10.261 | 5.230 | 1,055.6 | 7.365 |
| 500,000 | 60.6 | 17.469 | 8.605 | 1,811.8 | 14.507 |
| 1,000,000 | 35.9 | 28.775 | 13.201 | 3,277.1 | 30.820 |

Application source: `293e172`; binary SHA-256:
`bbc93e36880f26f71493f720832ba3e6af48aff4b3490238d28ffe33989cb3ee`.
Inputs are the native six-definition workloads described in the benchmark
note. One million is the largest tested workload, not an established hard
limit. Only the 100,000-placement case meets the 120 FPS target in this series.
API readiness is not first presentation or completed fit: the latter barrier
arrived at 4.994, 8.588, 15.831 and 32.324 seconds respectively.

### Mixed construction and grid-head occlusion

The mixed showcase is a materially different workload: 8,117 placements,
23 component definitions, 22 parametric systems and seven grids. Its original
label occlusion invoked the exact picker over every shown mesh for each grid
endpoint after camera motion, classifying meshes and testing triangles without
a spatial broad phase.

The [cached bounds filter](../notes/grid-head-occlusion.md) retains the exact
picker for candidate geometry, openings and spaces. Bounds follow the shown
scene's invalidation key. The `ray_bounds` test compares 208 exact picks,
including survey coordinates, and finite-distance occlusion decisions; `pick`
and `plan_inset` also pass. At the initial fitted camera, the old and new
3D-pane images are pixel-identical across 714,056 pixels. This verifies that
view, not every possible camera or model.

| Grid-head query | Observed FPS | Frame preparation p50 (ms) | Presented p95 (ms) | Peak process RSS (MiB) |
|---|---:|---:|---:|---:|
| Full exact scene, source `8d983a5` | 2.26 | 441.992 | 452.332 | 729.3 |
| Cached candidate bounds, source `293e172` | 43.05 | 22.578 | 24.792 | 735.6 |

This is about 19 times the submitted throughput on this mixed model; it still
does not meet 120 FPS. The new grid-head stage has p50 4.457 ms and p95 4.636 ms.
The old build did not log that stage separately. Do not attribute changes in
GPU timing to a new geometry-sharing algorithm: this change filters CPU queries.
API readiness is 30.878 versus 30.716 seconds; completed-fit barriers are
34.468 versus 34.247 seconds. The shared native input SHA-256 is
`de2092d0eb4a55bbbc0d3bcac3ac8c5580916308bb80fd6f4817075749a08bc6`.
The earlier binary SHA-256 is
`22835183d0ee410d2acd3b3491791b166a16b24ec2cea1ab6be077932f6077ba`.

A separate initial load comparison measured ordered settings reducing API
readiness from 78.927 to 31.000 seconds, on this same input and GPU. The linear
settings source was `9a7782d`, binary SHA-256
`c147ce112b51fb71b66abe8b3de20104e7a1267d8e1cb17c7fae0fb020827266`.
That is a load-path benefit; it did not remove the per-frame exact grid queries.

Initial orbit runs using only a fixed settling delay accidentally included
remaining deferred-fit work in their first recorded frame (2.4 to 2.7 seconds
in the mixed model). Those interval FPS values are superseded by the
barrier-controlled runs above. A disposable debugger run on `8d983a5` took
20 interrupted main-thread samples: the first eight were still in camera fit,
and the following twelve were in the exact picker called by grid-head drawing.
A compiler was active and the debugger interrupted execution, so those stacks
identify call paths rather than timing distributions. Their ignored evidence
is `build/renderer-stress/grid-stack-samples/{gdb.log,stacks.json}`.

Reproduce with `orbit_components.py --desktop --internal-orbit-lib ...
--seconds 15` and the generator commands in the benchmark note. Local ignored
evidence is retained under `build/renderer-stress/stable-{count}` and
`stable-{before,after}-grid-rays`: raw frames, host timing samples, process
memory, input/binary hashes and before/after images. The combined local report
is `build/renderer-stress/final-orbit-report.md`. The separate one-second
`dev-handoff` acceptance run verifies that the editor survives the measurement
process; it is excluded from the performance table.

## Strengths

Native GPU sharing preserves independently addressable elements and already
avoids repeated prototype uploads. The native model also separates component
definitions from placement identity and now records vertical placement without
creating one definition per masonry course.

## Weaknesses

GPU deduplication happens after expanding CPU geometry. Large native files can
therefore consume substantially more CPU memory than their compact placement
records suggest. Sharing only GPU buffers cannot remove those CPU copies.

## Risks

A prototype-plus-transform CPU scene would affect ray picking, sections,
bounds, element editing and exports. Materialisation on demand must preserve
the same world-space geometry, element IDs and revision invalidation. LOD must
not silently change fabrication or drawing geometry.

## Verdict

Retain the existing instanced GPU path and the validated grid-head bounds
filter. The fitted uncapped series reaches one million placements at 35.9 FPS;
the mixed showcase rises from 2.26 to 43.05 FPS while retaining exact candidate
picking. 120 FPS is established only for the 100,000-placement synthetic case
in this development-build series. FIFO comparison remains unmeasured.

The next proposed experiment is a CPU scene that keeps shared local geometry
and placement transforms, materialising only requested elements for precise
picking and sections. Accept it only if transformed vertices, independent
selection and revision invalidation remain equivalent and measured memory
falls on the same workload. This is a proposed experiment, not a new settled
architecture decision.
