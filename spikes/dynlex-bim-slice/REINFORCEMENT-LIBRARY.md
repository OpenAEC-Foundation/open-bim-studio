# Dutch reinforcement library (NL-R1)

The DynLex library supplies material identification and reusable geometry presets.
It does not calculate design resistance, anchorage, laps, welding suitability or code compliance.
The new library changes have not been compiled or runtime-tested.

## Editing

Select reinforcement and edit **Steel library** and **Secondary steel** in Properties.
Type a key below (case-insensitive; spaces are removed). `UNKNOWN` clears an assignment.
Main steel applies to longitudinal bars, including local extra bars, or the X mesh/area
family on both faces. Secondary steel applies to stirrups or the Y family on both faces.
Shared cage types share both material assignments. A single undo restores the whole edit.

| Keys | Reference context | Stored reference data |
| --- | --- | --- |
| B500A, B500B, B500C | NEN 6008:2008+A1:2020 | Nominal yield 500 MPa; ductility A/B/C |
| QR22, QR24 | GBV 1962 | Archival yield 2200 / 2400 kgf/cm² |
| QR32, QRN32 | GBV 1962 | Archival yield 3200 kgf/cm² |
| QR40, QRN40 | GBV 1962 | Archival yield 4000 kgf/cm² |
| QR48, QRN48 | GBV 1962 | Archival yield 4800 kgf/cm² |
| FEB220HWL | VBC 1995 context | Archival yield 2200 kgf/cm² |
| FEB400HWL, FEB400HK | VBC 1995 context | Archival yield 4000 kgf/cm² |
| FEB500HWL, FEB500HK, FEB500HKN | VBC 1995 context | Archival yield 5000 kgf/cm² |
| UNKNOWN | Unassigned | No strength or ductility inferred |

Historical entries preserve the archival table's units and designation. These values
are reference metadata, not assessed strength of existing steel. They are not converted
into modern characteristic or design values. Historical `nominalYieldMPa` remains unset
(represented internally by zero); that sentinel must never be consumed as a resistance.
Surface profile, bond, weldability and modern ductility equivalence remain unverified.
The reference context is not an assertion of manufacture date or applicable assessment code.
The original standard, drawings, certificates and/or material investigation are needed
for project-specific verification. No automatic substitution of QR/FeB with B500 occurs.

## Geometry presets

Edit **Library preset** using one of these keys. Applying a preset creates an independent
parameter copy, keeping the object's identity, placement, host, cover and material choices.
Cage presets detach the selected placement from its shared cage type; assign a type again
explicitly when desired. Local additional bars and end zones remain in place. Invalid
combinations are rejected by the existing transaction validation.

| Key | Parameters |
| --- | --- |
| CAGE_A | 3 Ø12 top, 3 Ø16 bottom, Ø8 stirrups at max 150 mm |
| CAGE_B | 4 Ø16 top, 4 Ø16 bottom, Ø8 stirrups at max 150 mm |
| CAGE_C | 2 Ø12 top, 3 Ø16 bottom, Ø8 stirrups at max 150 mm |
| MESH6_150 | Ø6 in both directions, 150 mm spacing |
| MESH8_150 | Ø8 in both directions, 150 mm spacing |
| MESH10_150 | Ø10 in both directions, 150 mm spacing |

Mesh presets apply only to mesh objects, on all active faces. These are generic patterns,
not certified supplier products; sheet sizes, edge wires and overlaps are not inferred.
Cage presets apply only to cages. Unknown or incompatible keys leave the model unchanged.
This first library is built in; custom catalog import and a searchable picker remain future work.

## Persistence

New reinforcement records contain 45 tokens, extending the previous 43-token format
with main and secondary library keys. All previously supported formats remain readable
and load with `UNKNOWN`, so old files are never silently labelled B500. Native files,
the existing IfcX extension payload and associative drawing tags retain the assignments.
This is not a standard IFC material-property mapping. NL-R1 catalog meanings must remain
stable; a materially revised classification needs a new key or a versioned migration.

## Sources

- [NEN 6008:2008+A1:2020](https://www.nen.nl/nen-6008-2008-a1-2020-nl-265616):
  publisher description establishes the B500A/B/C classes and distinct permitted surfaces.
- [Betonvereniging, Basiskennis, section 6.2.2.1](https://www.werkeninhetbeton.nl/media/31e84fdb-d78c-4042-880b-7359f419cbd1):
  nominal 500 MPa and ductility classification; no detailed norm tables are reproduced here.
- [Janna Beukers, TU Delft, 2022, appendix D, table D.11, p. 139](https://repository.tudelft.nl/file/File_c3439949-2c4a-4e29-a0d4-8ecbc28e9d9f?preview=1):
  research compilation of GBV 1962 and VBC 1995 designations and archival yield units.
  This is a research compilation, not the original historical norm. The adapter's numerical
  metadata is intentionally labelled archival; the thesis's equivalence table is not imported.
- [NEN 6008:1991](https://www.nen.nl/nen-6008-1991-nl-2873): publisher confirms the
  withdrawn steel standard and replacement by the 2008 edition. The full 1991 requirements
  were not available for inspection, so no detailed compliance claim is made.

`examples/reinforcement-library.bim` demonstrates a cage assigned `FEB500HWL`
longitudinal steel and `QR24` stirrups. It is illustrative, not an assessed existing cage.
The `reinforcement_library` regression source covers legacy migration, persistence,
invalid keys, shared materials and geometry presets; execution is pending compilation.
