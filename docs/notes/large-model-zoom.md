# Large-system zoom caches

Decision question: can zoom reuse unchanged system construction while preserving
its geometry, pixel-sized strokes, glazing detail and model identities?

## Reproduction

`tests/models/large-system-zoom.bim` is a synthetic native text fixture: 43 existing
recipe stations and nine additional shape stations, 58 system records including
layers. Curved carriers are polygonal; sloped tops are vertical wall contours,
not tilted workplanes. The presets are illustrative, not certified assemblies.

Fixture SHA-256:
`73e06706bc823fc61e38eed679e5c7aa058d43740d01c1ece94c0b102e33033a`.

Build an optimized development executable with the pinned compiler, then open a
**disposable copy** of the fixture with `OBS_PROFILE_FRAMES=1` and
`OBS_UI_SCALE=1`. Use a unique `--api` folder if collecting API barriers. Leave
existing user windows untouched. Compare the same viewport, model, camera and
input sequence without a compiler running during either measurement.

The Linux comparison uses a 1280 x 900 client window on a Ryzen 7 3700U. The
baseline is main `4a9ae5a261c1e8964454c651ca692e5524ed3469`, `-O2`, no debug
symbols. Compiler SHA-256:
`e1127c229b1b934d59b5950489fba0ef11255bc18a6b33ce51862bce21baf3af`.
Baseline executable SHA-256:
`0d9b69277ecbbb069845a3ac6d6478fbcedd17650cd26bd346a96f12c7a2b154`.

After resizing, visually confirming the active tab and applying Fit in that view,
run six wheel bursts at
client (700,450), alternating four positive and four negative detents. Each
detent is held for 50 ms with 200 ms between events; there are three synchronous
API state barriers after each burst. Run plan and 3D separately. Sent input is
not a frame count. The barrier protocol includes input delivery and API polling;
it is not an FPS measurement or a pure input-to-display latency measurement.

The optional Linux audit helper is `tools/probes/measure_system_zoom.py`. It
requires `python-xlib`, Pillow and `wmctrl`, and binds the exact PID, executable,
model, API folder, UI scale and client size. Select and inspect the active tab
first; its `--view` argument only labels that independently verified run. For
example, after starting your own app against `build/zoom-audit/model.bim`, set
`zoom_pid` to its observed process ID:

```sh
python3 tools/probes/measure_system_zoom.py \
  --pid "$zoom_pid" \
  --binary "$PWD/build/candidate/open-bim-studio-dev" \
  --model "$PWD/build/zoom-audit/model.bim" \
  --api "$PWD/build/zoom-audit/candidate-api" \
  --out "$PWD/build/zoom-audit" \
  --log "$PWD/build/zoom-audit/candidate-runtime.log" \
  --label candidate-plan --view plan
```

The helper saves frame traces and before/after images, and checks unchanged
native API element data, file bytes and Undo history. Visual review remains
separate from the automated checks.

## Measured comparison

Each entry aggregates the slowest `cpu_us` frame in each of the six bursts.
`cpu_us` is elapsed preparation time before presentation, not process CPU time.

| View | Median slowest frame | Maximum frame | Median burst plus three barriers |
|---|---:|---:|---:|
| Plan, baseline | 5327.4 ms | 5904.3 ms | 10.774 s |
| Plan, candidate | 65.9 ms | 69.1 ms | 1.580 s |
| 3D, baseline | 1748.6 ms | 3415.8 ms | 4.341 s |
| 3D, candidate | 28.8 ms | 46.6 ms | 1.581 s |

Plan recording accounts for almost the entire slow plan frame: e.g. 5459.6 ms
of a 5466.7 ms preparation frame. In the 3D run `plan_us` stays below 0.04 ms.
Source inspection finds that its zoom queue includes polygonal system meshes,
then re-derives their construction despite unchanged tessellation. A nominal
6 ms queue budget cannot bound one expensive reconstruction.

Both versions' six bursts in each view leave all API element data, the fixture
file hash and Undo count (zero) unchanged. The initial plan and active 3D
views were visually inspected, with matching overviews. The candidate reports
58 zoom-fixed systems and no pending zoom remeshes for this fixture. Opening
and initial construction are separate from these navigation measurements.

Fresh-process readiness in the controlled runs was 9045 ms for baseline and
9484 ms for candidate (first frames 8849 and 9294 ms). These single samples
use warm filesystem caches; this change does not establish an opening-time
improvement. The caches still build the complete construction initially.

## Bounded change

- The plan retains model-space system part outlines and their height ranges.
  Model revision, plan generation/view/storey, visibility, hidden IDs and the
  existing subpixel glazing threshold invalidate the cache. It still reprojects
  outlines and records pixel-width strokes and dashes at the current scale;
  text, picking and the canvas zoom key retain their existing behavior.
- The 3D scene classifies system profiles once per model revision. Polygonal
  systems bypass zoom re-meshing and even the queue's point scan. Round profiles,
  circular hollow profiles, ellipses and generated round point supports remain
  adaptive. Documents containing connection cuts conservatively retain the
  general path: even one base plate disables this 3D optimization for the
  document. Classification refreshes only when the document revision changes;
  drag-preview frames and display-detail changes reuse it.
- `OBS_PROFILE_FRAMES` additionally reports `meshing_us`, `zoom_pending` and
  `zoom_fixed`. These are view diagnostics, not serialized properties.

There is no model-record, native format or IFC exporter change, no display proxy
and no source-geometry simplification. Native unchanged-data checks do not
establish IFC schema/export validity. Whole-system LOD, early offscreen culling
and independent IFC validation remain separate in issue #76.

## Validation and limits

- Optimized Linux app/self-test build: `system_plan_cache`, `system_zoom_cache`
  and existing `zoom_queue` all match their expected output exactly; empty app
  and kernel compiler diagnostics, exit 0. The two new checks contain 18 explicit
  assertions. Fresh-vs-cached plan output covers pan/zoom, glazing detail, model
  commit, Undo, storey changes, committed cut height and active storey elevation; circular profiles still refine in 3D.
- Layer, local-name and whitespace checks pass. The native audit helper runs
  both plan and 3D on both executables and checks unchanged data/file/Undo.
- Native plan/3D views were visually inspected separately from the checks.
  This is Linux/X11 at UI scale 1, not a Windows/HiDPI visual certification.
- Candidate executable SHA-256:
  `d390f45633658bb0df450f78e8c6c4e6ac8e7f011e04eb131dd32a6d5ca8c4a6`
  for the timed comparison above. The revision-keyed classification follow-up
  was rebuilt with the same three tests passing exactly and empty diagnostics;
  executable SHA-256
  `2a19293dcb6f4d97819b1eb814f9689faec859a644d0e012593b579fffad8d66`.
  The performance measurements above belong to the original candidate; no
  additional native input benchmark is claimed for this follow-up.

## Verdict

On this 58-system fixture, retaining unchanged construction removes the measured
multi-second zoom stalls without reducing geometry. The comparison supports this
bounded cache fix; it does not certify all large-model workloads, faster initial
loading, new LOD/culling, or IFC export validity.
