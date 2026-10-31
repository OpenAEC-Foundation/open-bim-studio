# Dutch type catalogue: the INB template

**Decision question:** which wall, slab, column and beam types does a Dutch model start
with besides the editor's own build-ups, and where do they come from?

Status: **runtime data, compiled in**. The [catalogue](catalogue.json) holds every wall and
slab type of the INB template of OpenAEC
([OpenAEC-Foundation/inb-template](https://github.com/OpenAEC-Foundation/inb-template),
`INB-Template 0.6.ifc`, commit `edbbf7855e661c0d0d3af980dbe9c6e6fe1f0c00`) and its column
and beam types of a solid rectangular or round profile that is not steel. Issue #92.

## What it holds (read from the template)

| IFC class | Predefined type | Role here | In the template | Imported |
|---|---|---|---|---|
| IfcWallType | STANDARD, NOTDEFINED, ELEMENTEDWALL | wall | 39 | 39 |
| IfcWallType | MOVABLE (`und`) | wall | 1 | 0: no material layer set in the template |
| IfcSlabType | FLOOR, BASESLAB, NOTDEFINED | floor | 31 | 31 |
| IfcSlabType | ROOF | roof | 2 | 2 |
| IfcColumnType | COLUMN | column | 18 | 7 (2 concrete, 5 timber) |
| IfcBeamType | BEAM | beam | 18 | 7 (3 concrete, 4 timber) |

Every wall and slab type of the template is a single material layer. The 22 steel member
types (HEA, HEB, IPE, UNP, square hollow sections) are listed under `excluded`: steel
profiles follow the profile catalogue of #95, so a model only carries the profiles it
uses. The template has no roof, covering or ceiling types of their own; its pile and door
types are outside this catalogue.

Each type keeps its template name (`kzst_100`, `kpv_200`, `BK 300x300`) and its IFC
predefined type (`ELEMENTEDWALL`, `BASESLAB`), which the IFC writer uses for the type and
for slabs of it. Thicknesses and profile sizes are in metres, rounded to a tenth of a
millimetre (the template carries single-precision noise such as 220.000015258789 mm).

Kept as the template has it, and worth a look upstream: `zandcement_50` is 70 mm thick;
`promatect_12` and `fermacell_12.5` are gypsum (`gips`) 12.5 mm; `clt_200` and `clt_220`
walls are STANDARD while the other CLT walls are ELEMENTEDWALL.

## Materials

The template's materials map to the application's by the explicit table `materials`
(`MATERIALS` in `tools/inb_type_catalogue.py`): for example `kalkzandsteen` → `sand-lime`,
`gewapendbetonprefab` → `precast concrete`, `naaldhoutvurenCLT` → `timber CLT`. The
application's names are the words its hatches and `the bim dutch name of material`
recognise. An unmapped material stops the extraction.

## Use

`ui/editor/bim_inb_types.dl` is generated from this catalogue, and `add bim type library`
(`ui/editor/bim_editor.dl`) adds it after the editor's own wall, floor, roof, ceiling and
linear types, once per model. The application reads no data files at run time (its
installation carries fonts only and a model must start the same on every machine), so the
catalogue is compiled in rather than parsed when a model opens.

    python3 -I tools/inb_type_catalogue.py extract "INB-Template 0.6.ifc" --commit <sha>
    python3 -I tools/inb_type_catalogue.py generate
    python3 -I tools/validate_type_catalogue.py

The validator checks the IFC classes and predefined types, the material mapping, positive
lengths, unique names per role, and that the generated DynLex is up to date. The test
`localisation/tests/nl_type_library.dl` loads the library and checks counts and named types.
