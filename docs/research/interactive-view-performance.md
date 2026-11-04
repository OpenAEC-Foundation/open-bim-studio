# Interactive view performance

**Decision question:** which work prevents 120 FPS navigation in native plans,
sections and 3D, and which measured costs belong to the CAD kernel?

**Status:** under review
**Author:** OpenAEC contributors
**Last updated:** 2026-11-04

## Summary

Exploratory traces identify repeated plan recording as the main cost of the old
plan zoom path. Retained replay removes that work during wheel input, but a
172 ms recording after input stops remains outside the 8.33 ms frame budget.
The mixed-system 3D scene remains below target; stack samples identify CPU replay
of its small plan inset as a repeated cost.

## What it is

The application has separate semantic evaluation, triangle generation, 2D drawing
recording, UI overlays and GPU submission paths. A slow frame does not establish
a CAD-kernel defect: the stage that consumes time must be measured first.

Native 3D instances already share prototype geometry and preserve placement IDs.
Equivalent reuse in a section requires a prototype plus the cutting plane in its
local coordinates: differently cut instances cannot share the same cut result.
This is an architectural inference, not a completed implementation or measurement
of 2D instance rendering.

## Evaluation

| Criterion | Finding | Evidence type | Source / method |
|---|---|---|---|
| Camera-only plan motion | Old recording repeats every moving frame; retained replay avoids it during input | Measured | `OBS_FRAME plan_us/rerecorded/meshing_us` |
| Work after input stops | The current retained implementation records once after settling, taking 171.959 ms | Measured | Last frames of `plan-after-retained/editor.log` |
| Mixed-system 3D orbit | 43.29 submitted FPS, 23.706 ms p95 presented-frame duration | Measured | `navigation-3d-orbit/results.json` |
| 3D triangle regeneration during orbit | 0.001 ms p95 in the meshing stage | Measured | `meshing_us`; does not measure every possible kernel call |
| Shared geometry, LOD and culling | Relevant techniques for large BIM scenes | Claimed by upstream documentation | [That Open Fragments](https://docs.thatopen.com/api/%40thatopen/fragments/globals) |
| Indirect draw aggregation | Can reduce CPU draw submission overhead where supported | Claimed by upstream documentation | [Khronos multi-draw sample](https://docs.vulkan.org/samples/latest/samples/performance/multi_draw_indirect/README.html) |

## Measurements

- **Hardware:** NVIDIA GeForce RTX 5070; local Linux X11 desktop.
- **Builds:** native development builds, application `-O0 -g`, kernel archive `-O2`.
- **Versions:** old application `293e172`, retained-plan application `2cf8267`.
- **Model:** generated public `systems-showcase-final.bim`, 22 systems,
  8,117 component placements, 23 component definitions, four levels.
- **Viewport:** 1440 by 900 pixels; immediate presentation, `OBS_UNCAPPED=1`.
- **Method:** an owned disposable process uses a process-local GLFW input shim.
  The user's existing editor is left open. Source model hash and undo history
  must remain unchanged. Raw evidence stays under ignored `build/renderer-stress/`.
- An independent DynLex compiler and the user's editor were active during these
  exploratory runs. These are observed conditions, not isolated hardware maxima.

| Exploratory test | Submitted FPS | Plan stage p50 | Presented frame p95 | Mesh stage p95 |
|---|---:|---:|---:|---:|
| Old plan zoom | 5.41 | 178.130 ms | 183.902 ms | 0.001 ms |
| Retained plan zoom during input | 255.49 | 0.025 ms | 4.027 ms | 0.001 ms |
| Retained build, 3D orbit | 43.29 | 0.032 ms | 23.706 ms | 0.001 ms |

The wheel shim delivers callbacks at most every 50 ms from the app's own input
query. A blocked loop consequently receives fewer callbacks: 66 in the old run,
231 in the retained run. The builds also differ in wheel gain. These runs
establish stage costs and observed interaction behavior; they are not a matched
constant-cadence physical input-latency experiment. The reported callback-to-
present-submit time excludes the operating system's input queue, display scanout
and pixel response. Submitted FPS is not the monitor's refresh rate.

Screenshots before and after each run were inspected. Model hashes and native
undo histories were unchanged. The Xvfb smoke run verified input and cache
behavior but is excluded from the desktop performance comparison because its
presentation timing differed substantially.

### Direct kernel seam probe

The old and retained builds contain byte-identical kernel archives:
`7b7edfbd081987bfe84949657b2056450b13a88154e49a96e922b0e08e6791c9`.
There are no kernel source changes between the two application revisions.
The observed plan speedup therefore does not require a kernel-library change.

`tools/probes/kernel_abi_timing.py` links a small C driver against that existing
archive, without invoking or changing the DynLex compiler. It only passes scalar
values, an explicitly three-double Vec3 input and opaque body handles across the
existing exposed seam. It releases every owned body. Each case constructs a
6 by 0.36 by 3 m faceted wall and optionally performs one or four sequential
rectangular through-opening differences. Each of 15 results is required to be
non-null and have zero topology flaws; validation runs outside the timed region.

| General BRep operation | Origin | Median | Observed p95 | Maximum |
|---|---|---:|---:|---:|
| Wall only | Local | 0.006 ms | 0.008 ms | 0.016 ms |
| Wall + one opening | Local | 0.635 ms | 0.946 ms | 0.996 ms |
| Wall + four openings | Local | 7.030 ms | 10.153 ms | 10.176 ms |
| Wall only | Survey 500/450 km | 0.005 ms | 0.006 ms | 0.012 ms |
| Wall + one opening | Survey 500/450 km | 0.913 ms | 0.936 ms | 0.938 ms |
| Wall + four openings | Survey 500/450 km | 6.602 ms | 8.474 ms | 9.910 ms |

That initial run checks topology, not the resulting volume or all application
wall fast paths. It reproduces no kernel failure in those six cases and does not
establish universal kernel correctness. A later volume/tessellation check is
reported separately below. Four general BRep
booleans can exceed one 120 FPS frame budget even on this machine; model edits
and camera-only frames must remain separate workloads.

### Plan and vertical slice checks

The same C seam probe also constructs a horizontal plane at z = 1.2 m and a
vertical plane at x = 3 m relative to each wall. It checks `valid`, `divided`,
both returned body handles and zero topology flaws on each side, and releases
both handles. The shared plain Slice layout was checked against the native
archive's stores (valid/divided bytes 0/1, snag at 4, handles at 8/16) and guarded
with C static assertions; no managed-list output layout is assumed.

All 180 slices passed these checks. For the four-opening wall, median horizontal
slice time was 9.355 ms locally and 9.356 ms at survey coordinates; the vertical
slice medians were 3.953 and 3.947 ms. These operations alone can exceed the
camera-frame budget and reinforce the need to reuse cuts. No volume or cap-area
assertion is claimed by this probe.

### Qualitative 3D stack samples

Ten GDB samples from the owned disposable process found seven stacks in
`replay bim canvas` and `add gpu vertex`, with the application call at the
plan inset's CPU replay. Two samples were in grid-head ray candidate queries;
one was in the presentation driver. These counts are qualitative observations,
not statistically reliable percentages. Timing from the debugger run is marked
invalid. The unsampled 3D run above remains the quantitative baseline.

### First-frame observations

The unsampled traces report 23.937 s for the first plan frame and 29.890 s for
the first 3D frame. The plan trace attributes 15.580 s to meshing and 5.918 s to
plan recording. Two qualitative startup samples reached general BRep boolean
classification while folding a component, and the all-pairs derived-part join
search while computing system plan outlines. Two samples identify specific work;
they do not establish percentages or which component accounts for all mesh time.
The inset previously rebuilt these system outlines independently of the main plan.

The local GNOME `org.gnome.mutter check-alive-timeout` setting is 5,000 ms. The
application contains no matching unresponsive warning of its own. A blocked
first frame of this duration is consistent with the desktop warning; that is an
inference, not an observed window-manager ping trace. No desktop-global setting
was changed.

The acceptance harness was checked against `2cf8267` with
`--motion zoom-plan --require-retained-plan`: it correctly rejected the one
post-input recording, retained its results and closed only its owned test process.

### Independent tessellation and volume validation

A subsequent stricter run retained the topology/slice checks and tessellated all
90 walls and all 360 slice halves. It validates finite vertices, triangle index
bounds and signed triangle volume against independently computed rectangular
solid/void volumes, with tolerance max(1e-6 m3, one part per million). All 450
checks passed; the maximum volume error was 2.515e-10 m3. Mesh generation across
these results had median 0.182 ms and observed maximum 0.717 ms.

This extension uses the shared native Mesh record (three list pointers and an
owner pointer), plain list headers and explicit sole-owner release. The archive's
mesh stores were inspected at offsets 0, 8, 16 and 24, and the Vec3/Triangle/list
layouts and ownership match `kernel/api/types.dl` and the compiler's `lib/list.dl`.
C static assertions reject incompatible native sizes; this is a native x86-64
diagnostic, not a new stable cross-language SDK. No compiler or kernel archive is
modified. Analytic volumes are checked independently rather than taken from the
same kernel mass-property implementation.

### Native cavity-wall fixture

`tools/probes/generate_native_walls.py --rooms 100` generates 400 four-layer
walls with 200 hosted windows in editable BIM-SLICE format. The application API
confirmed those exact counts and no undo entries. On `2cf8267`, first-frame mesh
work took 102.945 ms and plan recording 317.552 ms. Camera motion used retained
replay, but the post-input recording still took 319.479 ms. These stage timings
came from an Xvfb functional run; its presentation FPS is not compared with the
desktop measurements. This reproduces the post-scroll hitch with actual native
walls, independently of the component-heavy showcase.

## Next-iteration acceptance criteria

These criteria are specified before the next implementation is measured:

1. On the same mixed-system model, camera-only plan zoom and pan must perform no
   plan recording or triangle generation during input **or after input stops**.
2. Model, view-rule and cut-plane changes must still invalidate affected geometry;
   camera changes must preserve IDs, model data, selection and undo history.
3. Each motion scenario must achieve at least 120 submitted FPS with p95 frame
   duration at most 8.33 ms. Record the maximum and frames over 16.67 ms as well.
4. Check orthographic drawings, tiled view clipping and final idle appearance
   visually; performance obtained by dropping systems or cut geometry fails.
5. Run kernel operations separately, recording correctness and timing together.
   Do not infer the critical 100k-element edit criterion R-01 from this smaller
   mixed-system scene or from a camera-only benchmark.

## Strengths

Stage timing separates a large CPU recording cost from inexpensive triangle
regeneration. Raw traces, binary/model hashes and screenshots permit the exact
scope of the observation to be checked.

## Weaknesses

The exploratory wheel delivery is tied to the app loop and the two wheel gains
differ. The 3D trace leaves much CPU work outside named stages. GDB samples are
qualitative only and invalidate quantitative timing from those sampled runs.

## Risks

Sharing cuts with an incomplete key can show stale geometry or reuse the wrong
intersection. Removing all zoom invalidation also needs a deliberate annotation
and detail policy; otherwise geometry can stay correct while labels or line
weights change unexpectedly. A faster plan alone does not establish performance
of sections, edits, exports or million-component models.

## Verdict

Remove the remaining camera-triggered plan recording, and profile the mixed-scene
3D CPU path before changing kernel algorithms. Keep R-01 open. The missing
specific evidence is the measured no-recording post-input path, GPU retention of
the plan inset, further kernel cases beyond the rectangular wall/void fixtures,
and repeated 120 FPS navigation checks including tiled sections.

## Sources

- [That Open Fragments API](https://docs.thatopen.com/api/%40thatopen/fragments/globals)
- [Khronos multi-draw indirect performance sample](https://docs.vulkan.org/samples/latest/samples/performance/multi_draw_indirect/README.html)
- [Khronos drawing command specification](https://docs.vulkan.org/spec/latest/chapters/drawing.html)
- Repository: `ui/shell/main.dl`, `ui/shell/bim_plan_zoom.dl`,
  `ui/panels/bim_plan_panel.dl`, `viewer/bim_native_instances.dl`,
  `tools/probes/orbit_components.py`, `tools/probes/orbit_input_shim.c`.
