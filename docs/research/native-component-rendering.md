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
includes the editor chrome. Each run fits the entire scene, then follows the
same finite process-local camera trajectory for 15 seconds. No compiler ran
during these measurements. All runs use `-O0 -g`, automatic device selection
and explicit uncapped IMMEDIATE presentation (`OBS_UNCAPPED=1`, reported mode
0, device kind 2). These are submitted frames, not monitor refresh rates or
release-build results. Before/after screenshots were inspected for whole-scene
fit; source hashes and zero undo steps were checked.

| True component placements | Observed FPS | Presented p95 (ms) | GPU p95 (ms) | Peak process RSS (MiB) | API ready (s) |
|---:|---:|---:|---:|---:|---:|
| 100,000 | 178.1 | 7.150 | 4.305 | 617.6 | 3.852 |
| 250,000 | 109.3 | 10.401 | 5.221 | 1,055.4 | 7.384 |
| 500,000 | 59.8 | 17.560 | 8.552 | 1,811.5 | 14.647 |
| 1,000,000 | 35.0 | 28.992 | 13.155 | 3,276.9 | 30.637 |

Application source: `8d983a5`; binary SHA-256:
`22835183d0ee410d2acd3b3491791b166a16b24ec2cea1ab6be077932f6077ba`.
Inputs are the native six-definition workloads described in the benchmark
note. One million is the largest tested workload, not an established hard
limit. Only the 100,000-placement case meets the 120 FPS target in this series.
Normal FIFO presentation was not measured in this series.
These initial runs predate the deferred-fit API barrier. Their first recorded
frame includes remaining transition work (notably 325.687 ms at one million
placements); they should be repeated with the barrier before interpreting
them as steady orbit throughput.

The mixed showcase is a materially different workload: 8,117 placements,
23 component definitions, 22 parametric systems and seven grids. On the
identical legacy native input, ordered settings reduce API readiness from
78.927 to 31.000 seconds, but moving-camera throughput stays at 1.87 versus
1.93 FPS (presented p95 458.500 versus 454.768 ms). Both builds automatically
select the same RTX 5070. This does **not** establish a renderer FPS benefit
from the settings index. The earlier source is `9a7782d`, binary SHA-256
`c147ce112b51fb71b66abe8b3de20104e7a1267d8e1cb17c7fae0fb020827266`.
The shared input SHA-256 is
`de2092d0eb4a55bbbc0d3bcac3ac8c5580916308bb80fd6f4817075749a08bc6`.

Inspection identifies a separate candidate for measurement: grid-head
occlusion invokes the exact picker over every shown mesh for each endpoint
after camera motion. That picker classifies every mesh and tests its triangles
without a spatial broad phase. Its cost is not represented by the grid-free
component workload. A conservative cached bounds filter should be tested
against unchanged exact picking before attributing the mixed-scene delay to
GPU instancing.
The first mixed-scene samples include 2.4 to 2.7 seconds of deferred fit and
initialisation. Thus the observed interval FPS above is conservative and is
not a clean steady-orbit comparison. Frame p95 is much less affected, but a
barrier-controlled rerun is required for the grid optimisation comparison.

Reproduce with `orbit_components.py --desktop --internal-orbit-lib ...
--seconds 15` and the generator commands in the benchmark note. Local ignored
evidence is retained under `build/renderer-stress/indexed-{count}` and
`settings-{before,after}-desktop`: raw frames, host timing samples, process
memory, input/binary hashes and before/after images. The combined local report
is `build/renderer-stress/indexed-orbit-report.md`.

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

Retain the existing instanced GPU path. The fitted uncapped component series
now reaches one million placements; the mixed showcase remains CPU-bound
during camera motion. First validate a spatial broad phase for its grid-head
queries and repeat the identical mixed-scene orbit. FIFO comparison remains
unmeasured. Then prototype a CPU
scene that keeps shared local geometry and placement transforms, and materialises
only requested elements for precise picking and sections. Accept that change
only if transformed vertices and independent selection remain equivalent and
measured memory falls on the same workload. This is a proposed next experiment,
not a new settled architecture decision or a claim of 120 FPS.
