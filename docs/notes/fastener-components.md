# Metric fastener components

The connection module supplies a native, reusable metric fastener catalogue.
Use **Connections > M8-M40 library**, choose a type under the existing component
browser, and click to place it. A selected placement exposes its type parameters
in Properties. Editing a shared type updates all placements; **Make unique**
creates a separate definition for the selected placement.

## Sizes and families

The catalogue contains M8, M10, M12, M14, M16, M18, M20, M22, M24, M27, M30,
M33, M36, M39 and M40. Each size has eight initial types: fully threaded bolt,
partially threaded bolt, hex nut, plain washer, and straight, L, J and
plate-ended anchors. These are initial modelling configurations, not a list of
commercially available stock lengths. Length and thread length remain editable.
M40 is explicitly a commercial supplier size; it is never substituted by M39.

Bolts and anchors support strength classes 4.6 and 8.8, uncoated steel,
hot-dip galvanizing and electrolytic zinc plating. Nut property classes 5 and 8
are separate from the bolt class; a class 8.8 assembly requires class 8 nuts.
Plain washers carry a 200 HV reference. The finish is a material property and
visible colour, not a geometric coating-thickness allowance.

Dimensions are metres internally. Property input uses the project's current
length unit. Pitch, threaded length, grip, bend radius and tail length accept
zero or `Auto`. Auto pitch is the metric coarse pitch. Auto bolts are fully
threaded; auto anchors have a straight threaded interval of six diameters,
limited by length. Bend radius defaults to three diameters and tail length to
four diameters. The length of a bent anchor is its axial depth to the outside
of the bend centre line; it is not the developed cutting length.

Head and nut widths can use ISO or the legacy DIN series. Nominal bolt length
is measured from the bearing face under the head. Adding a head washer shifts
the bolt head and tip by the washer thickness while preserving that nominal
length. Anchor assemblies permit an under-nut washer. Plate-ended anchors use
a round end plate with outside diameter 4d and thickness d/2.

## Geometry and performance

The authoring geometry is parametric CSG. A bolt is a union of an extruded
hexagonal head and an analytic cylindrical shank. Nuts and washers subtract
analytic cylinders from their outer volumes. Bent anchors use revolved
circular rod sections and cylindrical straight sections. Each nut, washer and
rod remains a separate solid within the fastening assembly.

`connection csg definition` contains primitive/operation terms with exact
size, origin and axis parameters. Evaluating these definitions on demand produces native
B-rep solids for CAD operations. The display path tessellates the known stock
CSG boundaries directly, sharing circle samples between caps and side faces;
it does not run general booleans on every placement. These display/export
triangles are transient results, not the authoring definition. Thread detail remains a
cosmetic 3D helix at the selected pitch and can be hidden independently.
Helices use 24 segments per turn with an 8192 segment limit per fastener; very
long or unusually fine threads receive coarser sampling. Simplified nut bores
use the major thread envelope. This geometry is for BIM coordination and
detailing, not manufacturing or thread interference analysis.

Canonical component solids are generated from their parameters and their
display geometry is reused for placements during a scene rebuild. Connection
groups use the same definitions and parameters. Changing a shared type
regenerates the construction and marks its instances for rebuilding. No kernel
or compiler source changes are needed.

## Persistence and compatibility

Existing native component ids and placement records retain their meaning. The
`fastenerComponents` model store binds typed parameters to ordinary component
definitions; snapshots include this store. Native `fastenercomponent` records
carry type identity, library slot, family, diameter, length and parameters.
Connection groups use optional `connectionfastener` and
`connectiontypefastener` records after their addition records.

The parameter sequence is pitch, threaded length, bolt grade, finish, washer
layout, nut count, nut class, grip, anchor shape, bend radius, tail length,
thread visibility, dimension series and catalogue flag. Native files without
these optional records keep their existing schematic fastener representation
until explicitly upgraded in Properties. Older application binaries cannot
read the new optional records; open typed models with the updated build.

IFCX fastener instances inherit a derived display body. Each type also exports
its analytic construction in `openbim::fastenerCSG`, with the primitive and
boolean operation terms of every separate part, and retains the native typed
parameters for editable save/reopen. Connection assembly bodies
include the new solid pieces. Cosmetic lines are regenerated by the native
application and are not exported as solid thread geometry.

Command 2350 loads the catalogue. Property codes 60000-62047 address 128
connection additions with 16 slots each; 62048-62079 address reusable types.
These interface allocations are recorded in the repository work claims.

## Dimension references

- [Böllhoff ISO 4017 class 8.8 bolt table](https://eshop-tr.boellhoff.com/out/media/pdf/ISO_4017_Stahl_8.8_zdpb1___en.pdf).
- [Böllhoff manual of fastening](https://eshop-tr.boellhoff.com/out/media/pdf/the_manual_of_fastening__8100-en.pdf), DIN/ISO conversion tables: ISO head widths and ISO 4032 nut heights.
- [Schuster ISO 7089 washer table](https://www.schuster-gmbh.de/de/lieferprogramm/produkte/din-en-iso-7089/): washer bores and outside dimensions, including the 42 mm M39 bore.
- [Hamza commercial bolt](https://www.hamzafasteners.com/product/mild-steel-hex-bolt/) and [nut](https://www.hamzafasteners.com/product/mild-steel-hex-nut/) dimensions: commercial M40, 60 mm across flats, 25 mm bolt head and 31 mm nut height. Its 42/72/6 mm washer geometry is a compatible commercial selection, not an ISO 7089 M40 designation.
- [ISO 10684](https://www.iso.org/standard/36897.html): hot-dip galvanized fasteners. Electrolytic zinc plating is a separate finish reference, ISO 4042.

These references provide nominal envelope dimensions. The implementation does
not assert certification, preload suitability, tolerances, coating compliance,
anchor approval, or structural resistance. The twenty-column example is a
synthetic modelling fixture with illustrative dimensions.

## Rounded-rim review status

`tools/probes/fastener_catalogue_review.dl` exports all 120 size/family
combinations from the production definitions, with optional rounded hex rims
and exact-pitch helix points. Its second bolt family includes two washers.
The probe checks closure and positive volume of every display piece.

The rounded rim is represented by two subtractive revolved circular-profile
volumes (CSG primitive 6). Each cutting volume can be evaluated as an analytic
B-rep. The kernel currently refuses their subtraction from the hexagonal stock
with snag 1. Consequently rounding is experimental and is enabled only in the
review probe, not in default catalogue B-rep definitions. The separate CSG
detail panel described below evaluates rounded surfaces directly.
The rounded review must not be described as a validated exact final B-rep.

The 120-variant review probe completed successfully, checking every display
piece for closure and positive volume. The 16 default CSG, geometry and thread
assertions still pass. These display checks do not resolve the exact boolean
limitation above.


## CSG detail in OBS

The Connections ribbon has a **CSG detail** button beside **M8–M40 library**.
Select a placed bolt, anchor, nut, washer or connection and open the detail. The normal Properties
panel edits its existing shared type; make unique retains its existing meaning.
Right-drag within the detail to orbit, use the wheel to zoom, and press Escape
or the same ribbon button to close. Viewing does not create a model transaction.

The detail reads the selected component's dimensions, pitch, thread extent,
washer flags, nut count, grip and finish. It evaluates rounded solids directly
per pixel, without generating a triangle boundary for this detail path. This is
a component inspection panel: the normal whole-model viewport still uses its
existing renderer. Straight, L, J and plate-ended anchors use the native bend,
tail, nut and washer positions. Connections assemble their evaluated fasteners,
plates, drilled holes, welds and participating members in one bounded packet
(up to 128 parts). I, RHS, CHS and rectangular sections are supported; unsupported
profiles and twisted/tapered members are refused explicitly. Connection detail
uses Technical Colors: blue plates, orange welds and yellow fasteners. I-section
root fillets are evaluated analytically in this panel; ordinary profile display
still has its existing limitations.
Rounded head/nut relief is derived from the catalogue dimensions; exact rounded
B-rep export is still pending. Thread marks are helical lines, not cut teeth.

Ownership, scope and the follow-up for whole-scene depth, selection and sections
are recorded in [issue #77](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/77).
The renderer's parameter block follows the existing element flags, with a
separate batch and a lazily created pipeline; the normal scene parameters and
element visibility limits remain unchanged. `OBS_CSG_DETAIL=1` opens the panel
on startup for native integration checks.


The `connection_gallery` fixture writes three native models beneath
`build/connection-gallery`: the combined workbench, the full fastener library
(120 catalogue types plus 15 assembled bolts), and ten applied connections.
The latter includes five column bases, a wind-brace gusset, end plate, fin plate,
double cleat and splice. The base-plate recipe accepts stiffener plates and welds
after its mandatory plate and anchor group; it can be saved and reapplied as a
connection type. Anchor holes cut the plate, not the column. Fillet-weld nominal
size is the equal leg length; its exact solid and detail field use a triangular
prism, with throat equal to leg divided by sqrt(2). Butt welds retain their
rectangular section. The geometric distinction between leg and throat follows
[TWI's fillet-weld terminology](https://www.twi-global.com/technical-knowledge/job-knowledge/design-part-1-090).
These are illustrative modelling recipes, not a reproduction
of a supplier's approved connection or a resistance calculation.
