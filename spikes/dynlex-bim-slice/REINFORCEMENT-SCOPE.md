# DynLex reinforcement and modular connections spike

An experimental extension of the native BIM slice. The implementation and tests are DynLex. It uses the existing shell build entry point and cadkernel, without Python or an additional geometry runtime.

## Reinforcement

The Reinforcement ribbon offers straight, L and U bars, rectangular cages, Area reinforcement and rectangular two-direction meshes. Bars retain marks and analytic centreline lengths; bends use a constant centreline radius with tangent-fit validation. Cages have independent top and bottom bar counts and diameters, defaulting to 3 D12 above and 3 D16 below, plus rounded rectangular closed hoops. Mesh wires occupy two touching layers. Cover is measured to the outside of the steel.

Select a rectangular linear host before choosing Cage to derive its envelope, endpoints and section rotation. Otherwise use two plan clicks; Mesh and Area take opposite rectangle corners. Dimensions use the current project units. The properties panel edits diameters, spacing, cover, envelope, start/end coordinates, bend radius and mark. Hosted envelope dimensions and coordinates are derived from the host. The existing Tag tool creates associative notations, and the quantity schedule reports count, length and steel volume.

### Cage types and local detailing

Set **Cage type (shared)** to `A`, `B`, `C` or another name. Assigning an existing type adopts its top/bottom counts, diameters, stirrup diameter and spacing, cover and bend radius. Editing those values updates every placement of that type in one undo transaction; the entire edit is refused if it does not fit any placement. `-` leaves a cage independent. This prototype stores synchronized type parameters on placements, rather than maintaining a separate catalog of unused types.

Local **Start/End zone length** and **Start/End stirrup spacing** add denser stirrups at the cage ends without changing the shared type. Zone length zero disables that end zone. Intervals are redistributed to remain within the specified maximum spacing and a boundary hoop is generated only once. **Extra top/bottom count**, diameter, **Extra from/to** describe a local range measured along the cage axis; the extra steel occupies a second row with a 20 mm clear gap. Extra counts zero disable these rows. These local fields remain unchanged by a type edit. The current UI supports one extra-bar range and two end zones per placement.

### Area and mesh reinforcement

**Area** distributes individual bars in two directions on either or both concrete faces. **Mesh** is a separate object with an editable mesh-type label and two crossing wire directions; the label does not select a manufacturer's catalog or calculate a standard mesh specification. Each remains a single selectable object. Use **Surface** (`Floor` or `Wall`) and **Faces** (`Bottom`/`Top`, `Front`/`Back`, or `Both`). The near and far faces have independent diameters and maximum spacings. Width means surface width for floors and height for walls; Depth is concrete thickness. Dimensions and curvature use project length units.

A nonzero signed **Curve radius** bends a free-standing region cylindrically along its developed X length. Bars follow the offset surface and retain analytic lengths; displayed curved paths target a 1 mm chord error. A radius of zero is flat. A surface cannot wrap beyond half a circle. This implementation does not support doubly curved or arbitrary freeform surfaces.

Select an upright wall (straight or circular) or a level rectangular floor and then choose Area/Mesh to attach it to the host. The envelope and wall curvature follow host changes. A hosted placement receives an associative plan tag. The ordinary Tag tool also annotates free-standing objects. Tags report faces, directions, diameters and spacings; cage tags additionally report type and local detailing, using the same definitions as the 3D paths.

Host limits are explicit: inclined/bowed walls, walls with openings, pitched floors and nonrectangular floor contours are currently refused. Adding an unsupported feature to an existing host invalidates its derived reinforcement rather than drawing steel through a void. Automatic opening trimming, net laps and panel layout remain unimplemented. These are geometric modeling tools, without anchorage, lap-length or structural design verification.

## Connections

The Connections ribbon separates Simple butt/miter joints from Complex nodes. Shift-click to select 2–6 linear elements with endpoints meeting within 1 mm, then choose a connection. Simple joints require exactly two members; Complex nodes support 2–6. The active (last-clicked) selected member is the primary; a butt joint stops the secondary at the primary section envelope. Each member end belongs to at most one node. Moving a connected endpoint moves the linked endpoints in the same transaction.

A node contains independent member references and their setbacks, plus a list of independently keyed additions. Plates, bolt groups and screw groups are separate addition kinds. Screw pilot diameters may be smaller than the shaft; bolt clearance holes cannot be smaller than the shaft. Every member gets a derived trim plane; fastening groups add derived circular cuts. Hole previews use twelve-sided cylindrical approximations and cadkernel subtraction; the editable definition retains the exact nominal diameter.

Select the purple node cross in plan or an addition in 3D. The properties panel edits member setbacks and each addition's dimensions, grid, position, host member and axis, and can remove an addition. Offsets are relative to the current primary endpoint in world-axis directions; axis components are dimensionless. New additions initially target the second member. Plates default to 12 mm; bolt groups to 20 mm shafts with 22 mm holes; screws to 6 mm shafts, 4 mm pilot holes and 40 mm length. These are editable geometric defaults, not design prescriptions.

## Persistence and exchange

Legacy 20-field reinforcement records remain readable with their original four-bar cage geometry and diameter. New records append layer, type, local-detail and surface fields; the same extended record is retained by the IfcX payload.

Native records are `reinforcement`, `connection`, `connectionmember` and `connectionpart`. Undo snapshots own their parameter lists; derived bars, voids and display segments are not stored as model elements. Deleting a host removes its dependent reinforcement and nodes.

IfcX exports steel geometry as well as the editable parameters in the optional `openbim::project.reinforcementV1` and `connectionsV1` string payloads. The native reader restores those parameters. These payloads are Open BIM Studio extensions. This change does not add reinforcement/connection support to the separate IFC4 exporter.

## Prototype limits

- No structural resistance, anchorage or code-compliance calculation.
- Cages use ideal closed hoops without fabrication hooks. Freeform path generation is available in the core, but the UI offers straight/L/U shapes only.
- No mesh opening trimming, overlaps, arbitrary cage layouts, fabrication shape codes or complete bar bending schedule.
- Fastener heads and shafts are schematic; threads, nuts, washers and countersinks are not yet represented.
- Display paths and B-rep surfaces are tessellated for rendering. Bent bars are drawn as connected round segments, not a continuous swept B-rep.
- Connection additions translate with the node; their stored axes do not automatically rotate with a changed host direction. Changing a host can make existing detailing invalid and requires review.
- Scene generation uses the existing rebuild path; large cages and dense fastening grids have not been performance-qualified. Use modest grids while evaluating the spike. The unoptimised four-hole geometry fixture took approximately 15 seconds on the development machine; hole generation needs optimisation before interactive use with dense grids.

## Build and validation

Use a separate worktree and its own ignored build directory. The compiler and standard library are shared read-only inputs. To reduce debug-generation overhead while another build runs:

```sh
DYNLEX_ROOT=/path/to/dynlex BIM_DEBUG=0 bash ./build.sh dev
DYNLEX_ROOT=/path/to/dynlex bash ./build.sh test reinforcement connections reinforcement_model connections_model connections_geometry reinforcement_editor
```

The tests exercise analytic bar lengths, bend rejection, cover, distributions, vertical/rolled hosts, node cardinality, distinct bolts/screws, native/IfcX round trips, associative tags, parameter editing, undo, endpoint propagation and geometric hole removal. Compiler diagnostics, failed test processes and output mismatches all fail the shell runner.

Development baseline: local commit `e5aeaaa`; feature branch `feature/reinforcement-module`. Upstream publication must preserve the existing local development commits separately from this module's diff.

For a local preview, `bash ./build.sh run-dev --example` opens the baseline example. With no arguments, `run-dev` supplies `--example` because the current native entry point assumes a nonempty argument list. After the editor test creates its review model, use `bash ./build.sh run-dev "$PWD/build/reinforcement-connections-demo.bim"`. Set `BIM_BUILD_DIR` consistently if the native binary was built elsewhere.

The development build was compiled with `BIM_DEBUG=0` and visually checked: both ribbons, cage placement, mark/diameter editing, and IfcX save/reopen. The compiler still reports the pre-existing repeated `along` pattern warning in `main.dl`. Compilation peaked above 7 GB RAM; the small example used about 80 MB after opening and 360 MB after editing and save/reopen. These observations are not large-model capacity estimates.

Verified headless suites: `reinforcement`, `connections`, `reinforcement_model`, `connections_model`, `connections_geometry`, `reinforcement_editor`, plus the existing `model`, `file` and `journal` regressions. The editor suite checks 21 assertions and writes a compact review model; a copy is included at `examples/reinforcement-connections.bim`. The combined unoptimised geometry/export portion can take minutes, so this build should be treated as a functional prototype rather than a performance-qualified detailing release.

The combined review model was also opened and inspected in plan and 3D. Node selection exposes independent plate/screw fields, including the smaller pilot hole, and the properties panel scrolls to the remaining fields. Initial generation took about two minutes in the unoptimised native build; afterwards this model used about 90 MB RAM. The current synchronous geometry rebuild blocks the UI during that initial calculation.

## Object interaction and zoom caching

A cage is one model definition and one scene mesh with a shared pick identity for every longitudinal bar and hoop. Free-standing reinforcement exposes a single move/rotate gizmo; a transform updates its endpoints in one transaction, and undo restores the complete cage. Hosted reinforcement continues to derive its position from its host. In 3D, selection highlights the complete reinforcement object.

When only the camera's level of detail changes, scene generation retains the existing fixed-detail reinforcement, connection additions and perforated member meshes. It still refines unperforated round members. Model revisions and active drag updates invalidate this reuse so parameter edits and undo cannot display stale geometry. Initial hole construction remains synchronous and is not accelerated by this cache.

Regression coverage in `reinforcement_object` checks one scene identity, 3D picks on a bar and hoop, a shared gizmo, translation of every generated point, single-step undo, and reuse across 18 zoom-detail levels. The complete headless fixture took 0.03 seconds after compilation on the development machine; cached sentinel meshes ensure this path does not invoke hole booleans.

For a reinforcement-only inspection, press **L** (Visibility) and turn off Walls and Slabs in the 3D column while leaving Other visible. This hides the concrete hosts without deleting them; the reinforcement stays associated. The plan and 3D visibility columns are independent.

Area generation estimates the tessellated path size before allocating it and refuses regions exceeding a 50,000-point preview budget. The limit is a guard against oversized inputs, not a large-model performance guarantee. Split a dense region into smaller regions or increase its spacing.

Additional regressions: `reinforcement_area` checks independent faces and diameters, curved wall paths, face selection, distinct mesh notation and the pre-allocation size guard. `reinforcement_details` covers shared cage edits with local exceptions, native legacy/new records, host-derived wall/floor areas, cascading deletion and undo. Its review fixture is generated in the selected build directory as `reinforcement-details.bim`.

Review models are included at `examples/reinforcement-cage.bim` (one type-A cage with 3 D12 top and 3 D16 bottom) and `examples/reinforcement-details.bim` (A/B/C cages, a local extra-bar/stirrup zone, curved wall area, floor area, curved free-standing floor area and a separate mesh). The four focused suites `reinforcement`, `reinforcement_area`, `reinforcement_object` and `reinforcement_details` pass 50 assertions in total.

## Dutch material and preset library

See [REINFORCEMENT-LIBRARY.md](REINFORCEMENT-LIBRARY.md) for NL-R1 keys, historical
units, provenance, editable material assignments and generic cage/mesh presets.
The new source extends persistence to 45 tokens and includes a source-only regression
suite. Library changes have not been compiled or runtime-tested; the earlier 50 passing
assertions predate these changes and do not validate the library.

## Reinforcement schedule and notation API (step 1)

`bim_reinforcement_schedule.dl` derives grouped quantity rows from generated bars.
Rows stay separate by owner and semantic family; exact diameter and analytic length
must match before quantities are combined. The TSV report includes owner, mark,
count, diameter, individual/total centreline lengths, main or secondary steel, and
shape descriptions. Invalid geometry refuses the complete report instead of returning
partial quantities. Variable stirrup end zones deliberately omit a single spacing.
All displayed spacing values from generators are marked as maxima.

Callouts read the existing project drawing-standard setting. NEN mode uses the
project convention `pos 3: 5 ø12-150 K` (K lower, B upper); other modes use explicit
English positions and `@` spacing. Wall faces remain front/back. UTF-8 output and an
explicit ASCII diameter option are available. The current ASCII UI atlas is unchanged.
These are backend APIs and a review-report format; they are not yet connected to a new
UI command or substituted for existing assembly tags.

This is a quantity schedule, not an approved bending schedule: shape codes are
`UNVERIFIED`, hoop descriptions identify omitted hooks, and lengths do not include
new lap or anchorage allowances. Fabrication dimensions, verified shape-code mapping,
EC2 edition/National Annex selection and anchorage checks belong to subsequent steps.
No EN 1992 design calculation has been introduced by this change.

Norm reference: [ISO 3766:2003](https://www.iso.org/standard/34171.html) covers
reinforcement representation and shape/bending schedules and replaces ISO 4066:1994.
The [NEN adoption/correction](https://www.nen.nl/nen-en-iso-3766-2004-c11-2004-en-116973)
and [NEN 47 catalog entry](https://www.nen.nl/nen-47-1970-nl-7779) identify the
requested drawing references. Public catalog information does not verify detailed
shape-code tables or the project's K/B convention, so this implementation makes no
claim of complete ISO/NEN compliance.

Source-only tests `reinforcement_schedule` and `reinforcement_notation` cover grouping,
quantity conservation, material separation, refusal, Dutch/English callouts and
project-standard persistence. Both passed the coordinator's bundle for 03bf304.

## Native reinforcement examples

Five review models in `examples/` have matching `reinforcement_example_*` tests:

| Model | Test suffix | Contents |
|---|---|---|
| `reinforcement-beam.bim` | `beam` | 3 top bars of 12 mm, 3 bottom bars of 16 mm, extra top bars and dense end stirrups |
| `reinforcement-column-footing.bim` | `column` | Vertical eight-bar cage and two-face footing area reinforcement |
| `reinforcement-floor-field.bim` | `floor` | Two-face mesh with different diameters and two sample edge U-bars |
| `reinforcement-wall-opening.bim` | `wall` | Eight explicit straight edge bars, four per face, clear of a 1 m square opening |
| `reinforcement-pile-foundation.bim` | `piles` | Four vertical pile cages and two-face pile-cap area reinforcement |

The build staging copies these actual files to `examples/bim-slice/models/`.
Tests load them through `bim_file.dl`, generate every reinforcement object,
compare schedule counts and total lengths, and check canonical save/load stability.
They import the file and reinforcement modules without the editor. Each test also
checks its model-specific parameters; the wall test verifies aperture clearance
and refusal of automatic area reinforcement on the perforated host.

These are geometric review fixtures, not engineered or fabrication-ready designs.
They do not design anchorage into supports, laps, structural capacity or stirrup
hooks. The two slab U-bars illustrate individual objects, not a complete perimeter
distribution. Wall edge bars are explicit free bars and do not follow later opening
edits automatically. Run these five new tests through the coordinator before merging.
