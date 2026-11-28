# Profile catalogue and parametric profiles

**Decision question:** which standard profiles can a linear type (column, beam, pile,
member) take without the model carrying all of them, and how is a drawn or parametric
profile stored so that other IFC tools can read it? Issue #95.

## The catalogue

One JSON file per series, `NN-name.json`; `NN` is the series code and the order of the
catalogue. `tools/profile_catalogue.py generate` compiles them into
`elements/linear/bim_profile_catalogue_data.dl` (the application reads no data files at
run time); `--check` reports whether that file is current. `bim_profile_catalogue.dl`
reads one series when it is asked for and makes a profile a linear type only when it is
used (`add bim catalogue profile`), keeping the profile's catalogue key at setting
2000007 of the type, so a model carries the profiles it uses.

| Code | Series | Material | Profiles | Source |
|---|---|---|---|---|
| 1-7 | IPE, IPN, HEA, HEB, HEM, UPN, UPE | steel | 143 | The table that was in `structural/steel/bim_steel_profiles.dl` (EN 10365 dimensions), moved here unchanged |
| 8-13 | L (equal, unequal), T, SHS, RHS, CHS | steel | 34, 50, 17, 100, 117, 90 | The first 32, 28, 10, 43, 23 and 44 from that same table (EN 10056-1, EN 10055, EN 10210), unchanged; the further sizes from Open FEM Studio, see below |
| 14 | SLS | timber | 4 | 38 mm planed softwood; 38x89, 38x184 and 38x235 are in the INB template |
| 15 | Concrete | concrete | 15 | Common sizes on a 50 mm grid, **not a standard** |
| 16 | Concrete round | concrete | 7 | Common diameters on a 50 mm grid, **not a standard** |
| 17 | IFC | steel | 12 | One example of each IFC parametric profile kind, to start a profile of one's own |
| 18 | HEAA | steel | 24 | Open FEM Studio, app table |
| 19 | HD | steel | 42 | Open FEM Studio, app table |
| 20-22 | DIE, DIL, DIN | steel | 30, 22, 30 | Open FEM Studio, steel-profiles table |
| 23 | DIR | steel | 29 | Open FEM Studio, app table |
| 24 | UAP | steel | 9 | Open FEM Studio, app table |
| 25 | CFRHS | steel | 261 | Open FEM Studio, app table |
| 26 | Cw | steel | 22 | Open FEM Studio, app table |
| 27 | Strip | steel | 97 | Open FEM Studio, steel-profiles table |
| 28 | RD | steel | 17 | Open FEM Studio, steel-profiles table |

### Series and sizes from Open FEM Studio

Taken from [Open FEM Studio](https://github.com/OpenAEC-Foundation/open-fem-studio)
at commit `b97959d`, dimensions only (no section properties), by a one-off
conversion:

- **The steel-profiles table**, `src-tauri/crates/steel-profiles/data/profiles.json`,
  which is LGPL-3.0-or-later there (that crate's `Cargo.toml` and the licence
  table of that repository's README): the series DIE, DIL, DIN, Strip and RD, and
  the further sizes of L (2 equal, 22 unequal), SHS (57), RHS (94) and CHS (46).
- **The app table**, `src/data/steelprofile.json`, which has no licence statement
  of its own there and falls under that repository as a whole, AGPL-3.0-or-later
  (`LICENSE.md`): the series HEAA, HD, DIR, UAP, CFRHS and Cw, and 7 further T
  sizes. The steel-profiles table does not hold these.

They are included here by decision of the OpenAEC Foundation's maintainers on
2026-11-28, as publisher of both projects.

What the conversion did and did not do:

- A size both tables and this catalogue hold keeps the value it had here. They
  differ in the root radius of eight unequal angles (here / steel-profiles table):
  L 30x20x3 4 / 3.5, L 40x20x4 4 / 3.5, L 50x30x5 5 / 4.5, L 70x50x6 7 / 6,
  L 100x50x6 8 / 9, L 100x50x8 8 / 9, L 150x75x9 12 / 10.5, L 150x100x10 12 / 13.
- A further size is appended at the end of its series file, not sorted in: a
  profile's place in its series is part of its catalogue key, which a model keeps.
- Where the steel-profiles table holds a series, only its sizes are taken; the
  app table's further angles and hot-finished hollow sections are left out (its
  angle radii and hollow corner radii do not agree with the other table).
- CFRHS takes the larger of the app table's two corner radii as the outer corner
  radius (2 t for most sizes, 2.5 t or 3 t for the others); one row without a
  wall thickness is left out. The table's values are **not checked against
  EN 10219** here.
- T sections are drawn without fillets, like the ones that were here. A Cw is
  drawn as an IFC C shape with square corners: depth, width, wall thickness and
  lip.
- HEAA is the series the standard writes as HE 100 AA. DIE, DIL, DIN and DIR
  are historic wide-flange series, kept for existing buildings.
- Not taken: the historic I sections with tapered flanges (`N.P.`, `B`), Sigma
  sections (no profile kind draws them) and the section properties.

A series file holds `code`, `series` (short name), `title`, `standard`, `material`,
`profile` (the IFC profile kind: Rectangle, Circle, IShape, LShape, UShape, TShape,
CShape, ZShape, RectangleHollow, CircleHollow, Ellipse, Trapezium, or `by profile` with
a `profile` field per row), `column` (whether its profiles are columns too),
`type_name` (`catalogue`: a type made from it keeps the profile's name; `rules`, the
default: the naming rules name it), `units` (mm) and `profiles`, one array each in the
order of `fields`: `name`, then `h` depth, `b` width, `tw` web or wall thickness, `tf`
flange thickness (a hollow section's outer corner radius), `r` fillet radius, `fourth`
(a C shape's lip, a trapezium's top width), or `d` for a diameter.

The steel series keep the codes of `bim steel series setting` (1 IPE to 13 CHS, 18
HEAA to 28 RD), so types from before the catalogue are recognised by series and size.
The naming rules name a steel type by its series and size; an HD and a Cw keep their
catalogue name (`type_name`: `catalogue`), which their size alone does not tell.

**Not yet in the catalogue:** the further series of the INB library (`INB-Library
0.1.ifc` in [inb-template](https://github.com/OpenAEC-Foundation/inb-template): K, BB,
HB and others, 1668 beam and column types). They need an extraction script like
`tools/inb_type_catalogue.py` run on that file.

## OpenAEC_ProfileParameters

A drawn or parametric profile is the linear type's open property set
`OpenAEC_ProfileParameters` (the `OpenAEC_` prefix of
[ADR-0010](../../../docs/architecture/decisions/0010-ifcx-as-the-reference-schema.md)),
next to its geometry. In IFC the set is one of the type's `HasPropertySets`; the
geometry is the type's profile in its `IfcMaterialProfileSet`, an
`IfcArbitraryClosedProfileDef`, or an `IfcArbitraryProfileDefWithVoids` when it has
holes. A reader that does not know the set still gets the profile.

| Property | IFC type | Meaning |
|---|---|---|
| `ProfileName` | IfcLabel | The profile's name; also the name of its IFC profile definition |
| `ProfileSeries` | IfcLabel | The series it belongs to, empty for none |
| *name* | IfcLengthMeasure | A parameter and its value, in the file's length unit (metres). Every length measure of the set is a parameter, in the order given |
| *name*`.Expression` | IfcText | When the parameter follows the others: an expression in them, such as `b/4` or `(h-tf)/2` |
| `Outline` | IfcText | The outline's points, `x,y; x,y; ...`, each coordinate an expression in the parameters, in metres from the member's axis (x along the type's width, y along its depth) |
| `Void1`, `Void2`, ... | IfcText | The holes' points, written as the outline |

Expressions hold numbers (metres), parameter names (a letter or underscore, then
letters, digits or underscores), `+ - * /`, a unary minus and brackets. Driven
parameters are evaluated pass after pass until they settle; an expression that does not
settle (a cycle), names an unknown parameter or divides by zero is refused, as is a
profile whose outline or a hole encloses no area. A refused change changes nothing.

Example, a window frame section with a rebate that follows its width:

```
ProfileName   IfcLabel          Frame 68x114
ProfileSeries IfcLabel          Window frames
b             IfcLengthMeasure  0.068
h             IfcLengthMeasure  0.114
r             IfcLengthMeasure  0.017
r.Expression  IfcText           b/4
Outline       IfcText           0,0; b,0; b,h-r; b-r,h-r; b-r,h; 0,h
Void1         IfcText           b/4,h/4; b/2,h/4; b/2,h/2; b/4,h/2
```

The API is `elements/linear/bim_profile_parameters.dl`: `make bim linear type …
parametric named … in series … with … outline … voids …`, `set bim profile parameter …
of type … to …` (a value) or `… expression …`, `regenerate bim profile of type …` and
`save bim drawn profile of type … as parametric named …`, which turns a drawn outline
into a profile in its width `b` and depth `h`, every point scaling with them.

**Open:** constraints between sketch lines (parallel, equal) are not part of the set;
the first step has driven dimensions only. Reading the set back from an IFC file onto a
type is not done yet: the IFC reader puts a type's sets on its occurrences.

## Verdict

Provisional: the catalogue as compiled-in data per series and the open property set
above. The set's name follows ADR-0010; whether parametric profiles need constraints
beyond driven dimensions is the maintainer's open question in #95.
