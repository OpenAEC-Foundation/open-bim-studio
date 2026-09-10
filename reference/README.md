# Reference material

External specifications and the benchmark models every candidate is measured against.

## The benchmark set

**Fixed once, used by every evaluation.** Candidates measured on different models cannot be
compared, and the temptation to benchmark each one on whatever is convenient is strong.

Defined in [`../docs/research/kernels/README.md`](../docs/research/kernels/README.md):

### 1. A realistic IFC model
Representative complexity from an open test set — a real building, not a demo cube. It should
contain the things that break implementations: curved walls, complex roofs, nested components,
non-trivial property sets.

One IFC2x3 model and one IFC4 model, so both schema paths are exercised.

#### 1a. AC20-FZK-Haus (IFC4)

- **Source:** <https://www.ifcwiki.org/index.php?title=KIT_IFC_Examples>, file
  <https://www.ifcwiki.org/images/e/e3/AC20-FZK-Haus.ifc>
- **Licence:** per the source page — "These examples are made by the Institute for Applied
  Computer Science (IAI) at the Karlsruhe Institute of Technology (KIT), and are for
  unrestricted use", with a request for attribution when used in publications.
- **SHA-256:** `70cc8ff245fc0894201d96496c031005a5cbd7a96b22d8a1b87c5a883fb77994`
  (measured: `python -c "import hashlib; print(hashlib.sha256(open('reference/models/AC20-FZK-Haus.ifc','rb').read()).hexdigest())"`)
- **Schema:** IFC4 (measured: `ifcopenshell.open(...).schema`)
- **Element count:** 127 `IfcProduct` (measured with `ifcopenshell` 0.8.4). By class: 42
  `IfcMember`, 17 `IfcOpeningElement`, 14 `IfcAnnotation`, 13 `IfcWallStandardCase`, 11
  `IfcWindow`, 7 `IfcSpace`, 5 `IfcDoor`, 4 `IfcBeam`, 4 `IfcSlab`, 3 `IfcVirtualElement`, 2
  `IfcRailing`, 2 `IfcBuildingStorey`, plus 1 each of `IfcStair`, `IfcBuilding`, `IfcSite` and
  smaller classes.
- **Notable features:** small single-family house, 2 storeys (`Erdgeschoss`,
  `Dachgeschoss`); 306 `IfcPropertySet`; 81 `IfcRelSpaceBoundary`; 22
  `IfcArbitraryClosedProfileDef` (non-rectangular member/opening profiles); no
  `IfcCircle`/`IfcTrimmedCurve` — this model's complexity is in profile shapes and openings,
  not curved geometry.
- **Why this one:** the standard KIT sample, small enough to load quickly while still
  exercising member profiles, openings and space boundaries; IFC4 schema path.

#### 1b. Schependomlaan (IFC2x3)

- **Source:** the dataset moved twice before landing — recorded here so the chain is
  reproducible: `openBIMstandards/DataSetSchependomlaan` (searched via GitHub) points to
  `buildingSMART/Sample-Test-Files`, whose repository ID (242043842) now resolves to
  `buildingSMART/Certification-datasets`, which no longer carries this dataset either. The
  file actually used came from the archived copy:
  <https://github.com/openBIMstandards/Archive-DataSetSchependomlaan>, file
  <https://raw.githubusercontent.com/openBIMstandards/Archive-DataSetSchependomlaan/master/Design%20model%20IFC/IFC%20Schependomlaan.ifc>
- **Licence:** per `LICENSE.MD` in that repository — "(C) original owners. This work is
  licensed under the Creative Commons Attribution 4.0 International License."
  (<http://creativecommons.org/licenses/by/4.0/>)
- **SHA-256:** `2c3565ca1904f2aa61adab92024cf3755b2c5b21a498144d3094d7cb58cebec7`
  (measured the same way as 1a, over `reference/models/IFC_Schependomlaan.ifc`)
- **Schema:** IFC2X3 (measured: `ifcopenshell.open(...).schema`)
- **Element count:** 3822 `IfcProduct` (measured with `ifcopenshell` 0.8.4). By class: 1262
  `IfcCovering`, 652 `IfcWall`, 282 `IfcWallStandardCase`, 279 `IfcSlab`, 277
  `IfcBuildingElementPart`, 259 `IfcWindow`, 205 `IfcDoor`, 174 `IfcBeam`, 100 `IfcSpace`, 90
  `IfcRailing`, 79 `IfcOpeningElement`, 60 `IfcFlowSegment`, 27 `IfcBuildingElementProxy`, 23
  `IfcColumn`, 14 `IfcVirtualElement`, plus smaller classes.
- **Notable features:** real Dutch housing project (Schependomlaan, Ede), 6 storeys
  (`-1 fundering`, `00 begane grond`, `01 eerste verdieping`, `02 tweede verdieping`,
  `03 derde verdieping`, `04 dak`); 11987 `IfcPropertySet`; 1675 `IfcRelSpaceBoundary`; 618
  `IfcArbitraryClosedProfileDef`; 23 `IfcCircle` and 23 `IfcTrimmedCurve` (curved geometry,
  unlike 1a); file size ~47 MB, two orders of magnitude larger than 1a.
- **Why this one:** the only real (non-demo) project among the candidates in the brief;
  IFC2x3 schema path; large enough to stress load time and memory on its own, independent of
  the synthetic scale tests below.

### 2. Synthetic scale tests
Generated models at 10k / 100k / 1M elements. Simple geometry — these measure scaling behaviour,
not geometric complexity.

The generator script belongs here, not the generated files. Reproducible beats committed.

- **Generator:** [`generate_scale_models.py`](generate_scale_models.py) — `python
  reference/generate_scale_models.py --count N --out path.obj` writes `N` unit boxes on a
  square grid as an OBJ file. Verified for `N = 10000` (`build/scale_10k.obj`, 10000 boxes,
  80000 vertex lines, 60000 face lines); `N = 100000` and `N = 1000000` use the same script
  with a larger `--count`.

### 3. A parametric change scenario
Move a wall; its openings, its junctions with adjoining walls, and every 2D view showing it must
follow.

This is the sharpest test in the set. It measures precisely what separates a viewer from a
modeller, and it is the one most likely to eliminate candidates.

- **Definition:** *to be written* — must be precise enough that every candidate is asked to do
  the same thing.

### 4. A boolean torture set
Ten pairs of closed triangle meshes with analytically known union and intersection volumes:
coplanar faces, a shared edge, a shared vertex, identical geometry, full containment, a
near-zero-thickness slab, a near-degenerate triangle, and a wall with twelve openings cut by a
multi-shell tool. Every case's expected volumes satisfy
`V(A) + V(B) = V(A union B) + V(A intersect B)`, checked numerically in the module's self-check.

- **Module:** [`boolean_torture_set.py`](boolean_torture_set.py) — `cases() -> list[Case]`,
  `signed_volume(vertices, faces) -> float`. Self-check: `python
  reference/boolean_torture_set.py` (prints each case's measured and expected volumes and
  asserts they agree).

### 5. A precision set
The `overlap_half`, `coplanar_faces` and `wall_with_openings` cases from the torture set,
reused verbatim, each carrying `offset = (500000.0, 500000.0, 0.0)`. A spike driver runs a
candidate on a case at the origin and again translated by `offset`, translates the result back,
and compares vertex positions after matching — this is the test for precision loss at
realistic distances from a projection's false origin.

- **Module:** [`precision_set.py`](precision_set.py) — `cases() -> list[Case]` (same shape as
  the torture set's `Case`, plus `offset`), `offset(vertices, delta) -> list[tuple]` to apply
  the translation. Self-check: `python reference/precision_set.py`.

## Binaries

**Do not commit large model files.** See [`../.gitignore`](../.gitignore).

For each benchmark model record instead:
- Where to obtain it, with a URL
- Its licence
- A checksum, so everyone verifies they measured the same file
- Its characteristics: element count, schema version, notable features

A `models/` subdirectory is gitignored for local copies.

## Specifications

Reference documents worth keeping links to — IFC schema documentation, national standards, file
format specifications.

Prefer stable links over copies. Where a copy is necessary, check the licence first.
