# DXF and DWG export

Collaborate > Export > **DWG/DXF 2D** writes the active storey's plan, and
**DWG/DXF 3D** writes the model, each as an R2000 (AC1015) DXF and DWG in the
working directory (`open-bim-studio-plan.*`, `open-bim-studio-3d.*`). Both
formats are written natively in DynLex; no converter or foreign library is
involved at run time.

## Where it lives

| File | What |
|---|---|
| `exchange/dxf_dwg/bim_cad_drawing.dl` | The drawing apart from either format: layers, lines, polylines, texts, polyface meshes, solids, in metres; the handle plan both writers share |
| `exchange/dxf_dwg/bim_sat_text.dl` | SAT 4.0 text of a closed planar polyhedron, holes included (the ACIS body of a 3DSOLID); the DXF and DWG ciphers |
| `exchange/dxf_dwg/bim_dxf_write.dl` | The R2000 ASCII DXF |
| `exchange/dxf_dwg/bim_dwg_bits.dl` | The DWG bit stream (B, BB, BS, BL, BD, DD, TV, H, CMC) and CRC-16 |
| `exchange/dxf_dwg/bim_dwg_write.dl` | The R2000 DWG: file header, header variables, classes, objects, object map |
| `ui/panels/bim_cad_export.dl` | The model as a drawing: the plan (cut polygons by category, grids, sketches, rooms with their area) and the 3D model (fast-kernel polyhedra as 3DSOLIDs, every other scene mesh as a polyface mesh, imported IFC elements included) |

The SAT, DXF and DWG writers translate the R2000 paths of cadcodec (package
`acadrust`, MPL-2.0) at `70ac6da7cf149cea6398a3d8829dd5e48b485b96`, the codec
the kernel port's ACIS module (`kernel/acis/`) was ported against. The DWG
header variables and the dimension style are generated from cadcodec's
writer source and its defaults for a new R2000 document, so their roughly
three hundred fields are not copied by hand.

## How it is checked

- `exchange/dxf_dwg/tests/cad_sat.dl`: the SAT of a box and of a frame with a
  hole, and the refusals (an open box, a two-corner loop).
- `exchange/dxf_dwg/tests/cad_export.dl`: one drawing with every entity kind,
  written as DXF and DWG into `build/tests/`.
- `ui/panels/tests/cad_export_house.dl`: the example house's plan and 3D model.
- `exchange/dxf_dwg/tests/verify_dxf_dwg.py` checks the DWG's structure
  without any CAD library (every CRC, the section sizes and sentinels, the
  object map, each object's own handle and size) and reads both files back
  with cadcodec (`tests/reference/`, built with cargo), comparing what it
  finds field by field with `cad_export.reference.txt`; every SAT body is
  parsed and validated.

Not yet checked: opening the files in AutoCAD, BricsCAD or the ODA File
Converter. cadcodec is the only reader the files have been tested with.

## Limits

- R2000 only, both formats; every current CAD program reads it.
- Entities are by layer (colour, linetype, lineweight); no hatches,
  dimensions as DIMENSION entities, blocks or paper-space layouts with
  viewports yet. Room areas and grid names are TEXT.
- A 3D element is a 3DSOLID only when the fast kernel built it as one closed
  planar polyhedron that the SAT writer accepts; walls built through the B-rep
  port (curved walls, booleans) and all other elements are polyface meshes,
  showing their triangle edges.
- Texts outside ASCII are written as `\U+XXXX`, which AutoCAD shows as the
  character; cadcodec decodes this in DWG but not in DXF.
