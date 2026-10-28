# Interactive drawing workspace

Development work on `feature/steel-baseplates`; full application validation is
pending. This document describes the candidate, not a published release.

## View tabs

Tabs name their actual view; sheet tabs use the sheet number. Names fit within
88–180 pixel tabs, with a separate close target. Overflow is reachable with the
arrow buttons and the mouse wheel over the strip. Activating an overflow tab
reveals it. Reordering preserves view identity. Changing a plan storey opens or
focuses its matching view tab rather than repurposing another tab.

A tiled sheet remains a sheet when the plan pane receives focus; the right pane's
caption and rendered content must agree. This fixes an existing case where a
sheet caption could sit above a 3D rendering.

## Sheets and viewports

Under the drawing ribbon, **All sheets** opens a board of real sheets. The board
uses the same retained drawing data as individual sheets; offscreen cards are
culled. Double-click a sheet to open it. Middle drag pans and the wheel zooms
about the pointer. **Fit sheet** resets the camera.

On an individual sheet, click a viewport to select it. Drag it to move it;
Ctrl-drag previews a copy. **Move viewport** and **Copy viewport** allow a picked
destination; Escape cancels. **Delete viewport** removes the placement, keeping
the model view. Title types are **Title**, **Title + line**, and **No title**.
The second includes the viewport number and a horizontal title line.

Double-click a plan viewport to activate its model for editing. Click outside
or use **Deactivate** to return to paper editing. Section activation opens the
linked section in its own tab. Schedule activation and the full set of in-place
section editing tools remain follow-up work.

Viewport copies reference the same model view. They are placements, not copied
building geometry. Camera changes and drag previews do not edit the document;
accepted placement/type changes use normal transactions and undo.

## Retained rendering

Paper, sheet framing, and each viewport have independent GPU canvas buffers.
Drawings are recorded in canonical paper units (one unit/mm). Camera changes and
viewport drag previews upload only a 16-byte instance transform, without parsing
source coordinates or restreaming drawing vertices. Different sheets and tiled
panes can use different transforms in the same frame. The shader does not use an
oversized Vulkan viewport or one mutable shared camera uniform.

Changes in document revision or view-local visibility regenerate the affected
visible sheet cache. The current invalidation is conservative: even a placement
commit invalidates the sheet's recording. First-time recording of a detailed
sheet is still synchronous; this needs separate latency measurements.

## Image references

**Collaborate → Import → Image** adds a linked PNG as a view-owned 2D object.
It is initially 5 metres wide, with the image's aspect ratio. Instance selection,
position, rotation, move, hide and duplicate remain available. PNG decoding and
GPU upload happen on import/cache miss; pan and zoom reuse the RGBA texture.
The image layer uses two triangles, independently of image resolution.

Limits: 8192 pixels per side, 16 megapixels decoded, 64 MiB encoded input, and
256 MiB of resident RGBA payload across images. These limits do not represent the
application's total memory footprint. Missing or invalid files are negatively
cached instead of being retried every frame. Linked files must remain accessible;
they are not embedded in the model. External file changes are not watched.
JPEG import, an image-specific scale/crop properties panel, and raster embedding
in PDF/SVG export remain follow-up work. Physical building objects continue to
come from editable 3D model geometry, not raster references.

The decoder calls the simplified libpng 1.6 API from DynLex. Its layout and output
format follow the [libpng 1.6 header](https://github.com/pnggroup/libpng/blob/v1.6.43/png.h).
Linux requires `libpng16.so.16`; Windows dependency/name mapping needs validation
before a Windows installer is released.

## Validation and coordination

- `images`: 17 checks passed (RGBA, palette, alpha, limits, view scope, native/IfcX roundtrip).
- `sheet_workspace`: 12 checks passed (camera anchoring, viewport copy/type/delete, persistence).
- `workspace_tabs`: 15 checks passed (reordering, bounded widths, overflow and shrinking).
- `viewport_overlay`: existing 7 checks passed with the extended GPU batch record.
- GPU probe: independent red/green image textures and canvases at three transforms,
  followed by a blue canvas-text sample, visually checked on Vulkan. The probe
  also forces vertex-buffer growth beyond 100,000 vertices and transform-buffer
  growth beyond 40 draws, with an additional clipped 100× zoom draw.
- Full app build, integrated UI interaction, export regression and frame-rate
  measurements are pending. These headless checks do not establish a high FPS.

The two changed SPIR-V assets were rebuilt using isolated DynLex `95d87e0e` plus
this repository's shader extensions. Native app compilation still uses the
previously working compiler; the upstream native compiler is not promoted.

Commands **2270–2279** are reserved for images and sheet workspace operations.
Sheet viewport title settings use **2400600 + viewport index**, stored on the
sheet. Index shifts on delete and copy preserve this metadata. No model-format
version bump is needed.

The integrated app attempt `/tmp/obs-sheet-tabs-app-r6` was stopped by the memory
guard at 619,852 KiB available memory. No compiler diagnostics were produced,
but there is no usable binary and the combined self-tests did not run. The
existing user application and its unsaved edits were preserved. A further heavy
build needs a different memory/build strategy; it is not automatically retried.

The app-only retry r7 stopped on an operand-grouping diagnostic in the SVG paper
corner constructor. Coordinate member expressions at that call and the new
sheet renderer are now parenthesized explicitly. The full app remains unvalidated;
pushing this development snapshot to main is not a release or an installer build.
