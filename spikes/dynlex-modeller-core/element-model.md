# The element model: one linear element, one planar element, types decide

**Status:** proposal from the maintainer (2026-10-09), partly built in the
BIM slice.

**Maintainer's request.**
- Everything is stored in IfcX, the format and the properties.
- A linear object (column, beam, skirting, mullion, pipe) is basically the
  same element.
- A planar element (ceiling, wall, floor, roof) is basically the same
  element, so that the core of the application stays very simple.
- The UI and the type decide whether you draw a column or a wall.

## The question

Can the model's core shrink to a few geometric families, with everything an
element *is* carried by its type? And can IfcX be the model's own vocabulary,
so that the core no longer knows walls, slabs, columns and beams as
separate records?

## The families

| Family | Geometry | Roles (from the type) | IFC4x3 class per role |
|---|---|---|---|
| Linear element | a profile swept along a straight 3D axis | column, beam, mullion, skirting, pipe, generic | `IfcColumn`, `IfcBeam`, `IfcMember`, `IfcCovering` (SKIRTINGBOARD), `IfcPipeSegment`, `IfcBuildingElementProxy` |
| Planar element | a layered plate along a surface | wall, floor, roof, ceiling | `IfcWall`, `IfcSlab` (FLOOR), `IfcSlab` (ROOF), `IfcCovering` (CEILING) |
| Free form | points and faces | mass, mesh | `IfcBuildingElementProxy` |
| Hosted | a void through a planar element | door, window, opening | `IfcDoor`, `IfcWindow`, `IfcOpeningElement` |
| Annotation | curves and text | grid, dimension, text, line | `IfcGridAxis`, `IfcAnnotation` |

A type holds:
- the role, and from it the IFC class;
- the profile (linear) or the layers (planar), and the material.

The tool in the UI only picks the role. The type selector lists the types of
that role.

## Linear element: built (2026-10-09)

- **Type.** `bim linear type record`: name, role, width, depth, round,
  material.
- **Element.** `bim linear record`: type, storey, axis start and finish in 3D
  (heights above the storey), and a turn about the axis.
- **Geometry.** The profile ring sits at both ends of the axis. The width
  lies level across the axis (along x when the axis is upright) and the
  depth square to both. The sides are flat and the two ends close the solid.
  The plan outline is the hull seen from above.
- **Plan.**
  - An upright element the cut plane passes through is cut: hatched in its
    material, with a black outline.
  - One above the cut is dashed.
  - One below the cut is a thin line.
- **Files.**
  - In `.bim`: `lineartype` and `linear` lines.
  - In IfcX: a type node (`IfcColumnType`, `IfcBeamType` and so on)
    carrying `openbim::lineartype`. Each element inherits it and carries its
    IFC class, `Length`, `Volume`, its body in the type's material, and
    `openbim::linear`.
- **Editor.**
  - The ribbon's Column, Beam, Mullion, Skirting and Pipe tools set the
    role.
  - A column or mullion stands for its storey's height. A beam or pipe runs
    under the storey above, and a skirting on the floor; each chains on from
    click to click.
  - A library of ten types is added once.
  - Selection, box selection, properties (angle typed, profile typed on the
    type), move, copy, rotate, mirror and delete all work.
- **Checked.**
  - `tests/linear.dl`:
    - volumes exact (0.27 m³ column, 0.48 m³ beam, a sloping round pipe);
    - closed solids;
    - a resized type followed by its elements;
    - `.bim` and `.ifcx` round trips.
  - `tests/linear_tool.dl`: the tools, the type selector, properties, box
    delete and undo.

## Planar element: plan

The existing wall carries a lot that must survive:
- L and T joins with mitres;
- hosted openings;
- curves in plan;
- lean and bow in section;
- layered solids;
- incremental evaluation by signature.

The slab is simpler: an outline at a level, of a thickness and a material.
The plan converts the simplest first and keeps every test passing at each
step:

1. **Planar type.** A type with a role (wall, floor, roof, ceiling) and
   layers. The existing wall types and floor types become planar types of
   their role. Files keep `walltype` and add `planartype`.
2. **Floor as planar element.** A boundary on a horizontal surface at a
   height, its layers stacked downward. It replaces `bim slab record`, and
   `slab` lines in old files still read.
3. **Roof and ceiling.** Roof: the same element on a sloped plane (pitch and
   direction), its layers stacked along the normal. Ceiling: a floor's
   geometry hung under the storey above, with role ceiling.
4. **Wall as planar element.** A plate standing on a centreline (straight or
   arc), its layers across, with joins and hosted openings. The current wall
   evaluation becomes the planar element's "standing" placement. Lean and
   bow stay as they are; they are already a shaping of the upright plate.
5. **Retire `bim wall record` and `bim slab record`**, once the tests pass
   on planar elements and old files read into them.

## IfcX as the vocabulary

- **Already the case.** The editor saves `.ifcx` by default. Every element
  carries an IFC class and IFC properties (`bsi::ifc::prop::…`), with its
  parameters in `openbim::…`; the model reads back from these records.
- **Next.** The properties window reads and writes by the same attribute
  names, so that a property shown is a property stored. A type's properties
  live on its type node and are inherited, as IfcX composes them.

## Not decided

Whether a planar element's surface may be curved beyond an arc in plan and a
bow in section; for example, a free-form shell would be a free-form element
with layers.
