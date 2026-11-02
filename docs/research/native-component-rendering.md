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

Retain the existing instanced GPU path. First compare fitted 100k, 250k and
500k native workloads with FIFO and explicit uncapped presentation, measuring
CPU/GPU frame times, peak RSS and startup independently. Then prototype a CPU
scene that keeps shared local geometry and placement transforms, and materialises
only requested elements for precise picking and sections. Accept that change
only if transformed vertices and independent selection remain equivalent and
measured memory falls on the same workload. This is a proposed next experiment,
not a new settled architecture decision or a claim of 120 FPS.
