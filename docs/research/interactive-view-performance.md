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
The mixed-system 3D scene also remains below target and needs separate profiling.

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
specific evidence is the measured no-recording post-input path, sampled 3D call
stacks, separate correct kernel-operation timings, and the repeated 120 FPS
navigation checks including tiled sections.

## Sources

- [That Open Fragments API](https://docs.thatopen.com/api/%40thatopen/fragments/globals)
- [Khronos multi-draw indirect performance sample](https://docs.vulkan.org/samples/latest/samples/performance/multi_draw_indirect/README.html)
- [Khronos drawing command specification](https://docs.vulkan.org/spec/latest/chapters/drawing.html)
- Repository: `ui/shell/main.dl`, `ui/shell/bim_plan_zoom.dl`,
  `ui/panels/bim_plan_panel.dl`, `viewer/bim_native_instances.dl`,
  `tools/probes/orbit_components.py`, `tools/probes/orbit_input_shim.c`.
