# Interactive view performance

**Decision question:** which work prevents 120 FPS navigation in native plans,
sections and 3D, and which measured costs belong to the CAD kernel?

**Status:** under review
**Author:** OpenAEC contributors
**Last updated:** 2026-11-04

## Summary

The first validated resident-drawing iteration removes the measured post-input
plan recording and reaches 241 FPS in mixed-system plan zoom and 200 FPS in 3D
orbit. Native cavity walls also retain their drawing after input stops. Nine of
ten navigation scenarios meet the FPS/p95 criteria; 3D wheel zoom still fails
because its adaptive-geometry path repeatedly processes fixed component meshes.
Initial loading remains slow. Kernel checks reproduce significant one-off costs
without finding a geometry failure in the tested fixtures.

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
| Work after input stops | `2cf8267` records once after settling, taking 171.959 ms; the validated resident iteration records none | Measured | `plan-after-retained/editor.log`, validated table below |
| Mixed-system 3D orbit | 43.29 submitted FPS before the resident inset and bounds hierarchy; 199.76 FPS afterward | Measured | `navigation-3d-orbit/results.json`, validated table below |
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
- **Desktop mode:** `xrandr --current` reports HDMI-2 at 1920 by 1080,
  59.96 Hz. Uncapped submission measures rendering capacity; it cannot establish
  120 physically displayed refreshes per second in that configured mode.
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

An unsampled controlled comparison folded only the plan inset through its native
UI before the same 12-second orbit. Screenshots confirm the inset is folded and
the 3D building remains visible; model hash and undo history are unchanged. The
existing build then submitted 133.56 FPS, with presented-frame p95 9.012 ms and
maximum 13.574 ms. Grid-head visibility queries still took p95 4.422 ms. This
supports retaining the inset on the GPU, but folding it is a diagnostic ablation,
not the product fix. The p95 acceptance limit still fails in this run. Evidence:
`retention-baseline-folded-inset/results.json`; reproducible with the harness's
`--fold-inset` option and process-local input shim.

### Legacy 3D wheel baseline

A separate four-second desktop wheel run on `293e172` submitted 26.85 FPS with
presented-frame p95 45.532 ms. The meshing stage alone had median 20.139 ms,
p95 25.625 ms and maximum 37.975 ms. The model and undo history stayed unchanged;
53 wheel callbacks were delivered. This is a different workload from orbiting.
The corresponding camera-tier refresh path did not change between `293e172` and
`2cf8267`. These observations motivate a separate adaptive-geometry check rather
than inferring wheel performance from the faster orbit case. Evidence:
`legacy-3d-wheel-matched-assets/results.json`.

New runs explicitly pair the executable with its build directory's shaders and
record the canvas shader hash. An isolated runtime folder links the same font
and icon assets; it prevents a run from silently loading another checkout's
`build/shaders` through its current directory.

### First-frame observations

The unsampled traces report 23.937 s for the first plan frame and 29.890 s for
the first 3D frame. The plan trace attributes 15.580 s to meshing and 5.918 s to
plan recording. Two qualitative startup samples reached general BRep boolean
classification while folding a component, and the all-pairs derived-part join
search while computing system plan outlines. Two samples identify specific work;
they do not establish percentages or which component accounts for all mesh time.
The inset previously rebuilt these system outlines independently of the main plan.

A later ten-sample startup trace used bounded API pings so sampling was no
longer delayed by a 15-second connection timeout. Three stacks were in general
BRep component folding, including camera fit and native scene creation. Seven
were in derived-part connection searches reached from system meshing. These are
qualitative stack counts, not time percentages; all timings from this sampled
run are invalid. This identifies repeated all-pairs join searches as a specific
next target alongside the one-off component folds. Evidence:
`startup-profile-detailed/startup-stack-*.txt`.

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

The same fixture was regenerated at x = 500,000 m and y = 450,000 m. Both
application loads confirmed 400 walls and 200 openings. A before-motion image
comparison found zero changed pixels across 217,800 pixels in 99 room rectangles;
the room overlapped by the local world-origin marker and all UI/view overlays
were excluded. This checks these visible orthographic wall/window drawings under
translation; it is not a full-window or arbitrary-coordinate correctness claim.

### Repeated-component comparison

An unsampled desktop orbit on the existing `2cf8267` build used
`components-100000.bim`: 100,000 placements of six definitions across ten levels
(SHA-256 `3bee500fe7b57f9999ce49ad471a90f4a45118ddddc53dc1e4e27de9335c7b35`).
The 12-second run submitted 189.34 FPS, with presented-frame p95 5.973 ms and
maximum 9.230 ms. Five of 2,273 frames exceeded 8.333 ms; none exceeded
16.667 ms. Model hash and undo history stayed unchanged. Screenshots confirm the
3D geometry is visible. This scene has no grids or visible plan inset, unlike
the slower mixed-system fixture; it does not validate 100,000 cut results,
interactive edits or plan/section completeness. Raw evidence is in
`retention-baseline-100000-orbit/results.json`.

### Native component folding

The C seam probe also accepts `--box-component-model MODEL --component-id ID`
for native definitions consisting entirely of additive, unrotated boxes. It
rejects other geometry rather than approximating it. It folds the boxes in file
order using the application's 1e-9 m boolean tolerance. An independent coordinate
cell sweep computes the analytic union volume, including overlaps.

All 23 definitions in the mixed-system fixture passed three rounds each: valid
bodies, zero topology flaws and 69 finite/index-bounded tessellation-volume
checks. The largest volume error was 1.111e-16 m3. The 64-box exposed-reinforcement
definition took median 1,608.049 ms to fold; the fourteen 24-box masonry corners
took approximately 46.5–47.3 ms each. The sum of component medians was
2,264.055 ms. These measurements include general BRep construction and unions,
with validation and tessellation outside the timed fold; per-part diagnostic
writes are included in the aggregate duration.

This reproduces a significant one-off kernel cost with actual model definitions,
but does not account for the full 15.580 s application meshing stage. Further
stage measurements are needed before attributing its remainder. No geometry
algorithm was changed. The original 450 wall/slice volume checks were rerun after
extending the probe and passed. Evidence: `kernel-native-component-summary.json`,
the per-component result directories, and
`kernel-abi-volume-regression-after-components/results.json`.

The additional `--compare-component-meshes` check tessellates each of the 23
definitions at linear tolerances of 1 m and 0.2 mm, with maximum angle 0.3 in
both cases. Every pair has the same vertex/normal counts, positions and normals
within 1e-12, and exactly the same triangle indices. Both finite-value and index
bounds checks pass, alongside the independent volume check. This is measured
evidence that these explicit faceted definitions need no camera-only remeshing;
it is not a claim about cylinders, spheres or arbitrary sketch-backed components.
Evidence: `kernel-component-lod-equivalence-summary.json` and its per-definition
result directories.

## Validated resident-drawing iteration

The native build passes `plan_replay`, `system_plan_cache`, `ray_bounds`,
`viewport_overlay` and `linear_joins` as embedded checks. `canvas_pixels` passes
separately. The shader passes SPIR-V validation for Vulkan 1.2. A native Vulkan
image test measures the retained stroke at exactly two pixels under 1x, 3x and
10x zoom; the ordinary-scaling control measures 2, 6 and 20 pixels. The CPU test
also compares retained encoding against freshly drawn fixed-width strokes at
five scales from 0.01x to 50x.

Heavy plan geometry remains resident. Lightweight annotations, room labels,
grids and selection symbols follow the current camera with fixed pixel sizes.
The inset has its own resident buffer, shares system outlines with the main plan,
and clips its geometry and camera arrow to its interior. A balanced bounds
hierarchy conservatively prunes grid-head visibility candidates while retaining
scene order. The existing exact picker is unchanged.

| Desktop scenario | Submitted FPS | Presented p95 | Maximum frame | Acceptance |
|---|---:|---:|---:|---|
| Mixed systems: plan wheel | 241.30 | 4.123 ms | 9.941 ms | Pass |
| Mixed systems: plan pan | 240.77 | 4.092 ms | 10.070 ms | Pass |
| Mixed systems: focused 2 s closeup | 227.44 | 4.181 ms | 10.453 ms | Pass |
| Mixed systems: 3D orbit | 199.76 | 5.671 ms | 11.873 ms | Pass |
| Mixed systems: 3D pan | 203.06 | 5.568 ms | 21.226 ms | Pass |
| Mixed systems: 3D wheel | 47.56 | 26.141 ms | 40.572 ms | Fail |
| Mixed systems: tiled plan wheel | 209.27 | 4.831 ms | 6.073 ms | Pass |
| 400 cavity walls: plan wheel | 622.58 | 1.874 ms | 2.567 ms | Pass |
| 400 cavity walls: plan pan | 719.17 | 1.478 ms | 4.740 ms | Pass |
| 100,000 placements: 3D orbit | 188.98 | 5.986 ms | 7.346 ms | Pass |

All plan cases record zero heavy drawings during input and after it stops, and
model hashes and undo histories stay unchanged. On the cavity-wall wheel run,
the post-input plan stage has p95 0.101 ms and maximum 0.159 ms, with zero
recordings, instead of the former 319.479 ms recording. Mixed-scene 3D orbit has
inset p95 0.047 ms and grid-head query p95 0.132 ms. Twelve of 2,398 orbit frames
exceed 8.333 ms; none exceed 16.667 ms. The p95 goal is not a promise that every
frame has the same duration.

Before/after images were inspected for geometry, fixed-width closeup output,
inset containment and separation of tiled plan/3D panes. The focused closeup uses
client point (600, 650), inside the building; the tiled plan uses (350, 650),
inside its left pane. An earlier closeup centered outside the cropped building
is excluded from visual acceptance. These runs verify a tiled plan and 3D view,
not interactive system sections. Initial mixed-scene API readiness remains
approximately 24 seconds and is still an open responsiveness problem.

Evidence: `retention-validated-*/results.json`, matching screenshots and
`pixel-stroke-native-x11/results.json`. The source snapshot is based on `04c9577`
with the validated performance patch; the executable and shader hashes are
recorded per run. A separate compiler and the existing user editor remained
active, so these are observed development-build results rather than isolated
hardware maxima.

## Acceptance criteria

These criteria are specified before the next implementation is measured:

1. On the same mixed-system model, camera-only plan zoom and pan must perform no
   heavy plan recording or model-triangle generation during input **or after
   input stops**. Live UI/annotation drawing is measured separately from model
   geometry reuse.
2. Model, view-rule and cut-plane changes must still invalidate affected geometry;
   camera changes must preserve IDs, model data, selection and undo history.
3. Each motion scenario must achieve at least 120 submitted FPS with p95 frame
   duration at most 8.33 ms. Record the maximum and frames over 16.67 ms as well.
4. Check orthographic drawings, tiled view clipping and final idle appearance
   visually; performance obtained by dropping systems or cut geometry fails.
   Fixed pixel stroke widths, lettering and selectable symbols must also stay
   aligned after an asymmetric zoom ending in a closeup. Compare retained stroke
   encoding to freshly drawn fixed-width geometry across multiple zoom scales.
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

## Sources

- [That Open Fragments API](https://docs.thatopen.com/api/%40thatopen/fragments/globals)
- [Khronos multi-draw indirect performance sample](https://docs.vulkan.org/samples/latest/samples/performance/multi_draw_indirect/README.html)
- [Khronos drawing command specification](https://docs.vulkan.org/spec/latest/chapters/drawing.html)
- Repository: `ui/shell/main.dl`, `ui/shell/bim_plan_zoom.dl`,
  `ui/panels/bim_plan_panel.dl`, `viewer/bim_native_instances.dl`,
  `tools/probes/orbit_components.py`, `tools/probes/orbit_input_shim.c`.

## Verdict

Keep resident cut drawings, fixed pixel strokes, the GPU inset and conservative
bounds queries. The measured plan, pan and orbit cases meet the FPS/p95 target;
3D wheel zoom still fails its explicit acceptance check. Keep R-01 open. The next
specific evidence needed is a native wheel run that excludes proven fixed
component geometry from adaptive work while preserving curved refinement,
responsive initial loading, and complete interactive system-section checks.
The measurements do not justify changing general kernel algorithms solely to
address camera navigation.
