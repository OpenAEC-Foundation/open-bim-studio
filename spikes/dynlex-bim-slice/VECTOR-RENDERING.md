# Retained vector references

Imported drawing artwork stays separate from editable building elements. The
new plan path decodes `OpenBIM_VectorTriangles` properties at document refresh,
retains model-space triangles, and uploads the active view once. Pan and zoom
then change a GPU instance transform. They do not parse property strings,
transform every triangle on the CPU, or upload another vertex buffer.

Unchanged payloads survive unrelated document edits. Invalid payloads are cached
as invalid and contribute no partial triangles. Reimports preserve painter
order. A local origin reduces float precision loss for large coordinates.
Sheets use the same decoded data when their resident viewport layer is rebuilt;
sheet navigation then reuses that layer. Physical geometry and annotations
keep their separate editing and rendering paths.

The Vulkan context allocates canvas slots for all resident layers, so a vector
view and sheet viewports cannot claim the same buffer. Slot zero belongs to
the ordinary plan canvas. Only one active vector-view slot is retained.

Validation:

- `vector_cache`: initial decode, revision reuse, payload changes, invalid data,
  stable geometry identity and document replacement.
- `vector_reference`: compatibility, model-to-paper coordinates, colours and
  atomic rejection of malformed input.
- `sheet_paper`: page dimensions and canonical paper coordinates.
- `tools/vector_canvas_probe.dl`: manual Vulkan regression with a display;
  camera-only frames, unrelated revisions, slot allocation, large coordinates
  and removed artwork.
- `tools/vector_navigation_benchmark.dl`: manual Vulkan navigation benchmark.
  Pass a UTF-8 file containing one RGB/triangle payload per line. Project data
  is external to the repository. Output gives triangle count, upload count,
  240-frame elapsed time and presentation rate after warm-up.

The standalone GPU benchmark isolates imported artwork. It does not establish
whole-editor or sheet frame rates; those also include model geometry, text,
UI and interaction. Full application validation is tracked separately.

Local isolated measurement, 26 October 2026: the 1357 source view contains
146,789 triangles in 3,619 payloads. After warm-up, 240 pan/zoom frames took
4.00009 seconds (59.9987 presented fps), with one upload in total. This is a
presentation-limited GPU-layer result, not a before/after whole-editor score.
The benchmark used a separate hidden 1280 × 900 Vulkan window and `-O0`.

Full-app validation on `6759607` also passed (Linux, `-O0`, 1440 × 900):

| Content | Pan presented fps | Zoom presented fps | Sheet rerecords |
|---|---:|---:|---:|
| 1357 vector plan, view 1067 | 60.99 | 60.83 | n/a |
| Source sheet BP-22 | 60.73 | 52.61 | 0 |
| Model/frame sheet BP-22-M | 60.91 | 55.68 | 0 |

Each sample ran for about four seconds. Sheet zoom used alternating wheel input
at approximately 60 Hz; the plan zoom sample used input at approximately 8 Hz
and continued presenting between events. Frame rates are local observations,
not guarantees across GPUs or projects. `cpu_us` in the frame log includes
presentation pacing; process CPU time was measured separately. PNG/image
interactions and every viewport operation are not covered by these measurements.

The same app passed the new opening property action, duplicate prevention and
undo/redo through its file API. The original user model was preserved; tests
used a separate file copy and process.
