# DynLex reinforcement and modular connections spike

An experimental extension of the native BIM slice. The implementation and tests are DynLex. It uses the existing shell build entry point and cadkernel, without Python or an additional geometry runtime.

## Reinforcement

The Reinforcement ribbon offers straight, L and U bars, rectangular cages and rectangular two-direction meshes. Bars retain marks and analytic centreline lengths; bends use a constant centreline radius with tangent-fit validation. Cages contain four longitudinal bars and rounded rectangular closed hoops. Mesh wires occupy two touching layers. Cover is measured to the outside of the steel.

Select a rectangular linear host before choosing Cage to derive its envelope, endpoints and section rotation. Otherwise use two plan clicks; Mesh takes opposite rectangle corners. Dimensions use the current project units. The properties panel edits diameters, spacing, cover, envelope, start/end coordinates, bend radius and mark. Hosted envelope dimensions and coordinates are derived from the host. The existing Tag tool creates associative notations, and the quantity schedule reports count, length and steel volume.

## Connections

The Connections ribbon separates Simple butt/miter joints from Complex nodes. Shift-click to select 2–6 linear elements with endpoints meeting within 1 mm, then choose a connection. Simple joints require exactly two members; Complex nodes support 2–6. The active (last-clicked) selected member is the primary; a butt joint stops the secondary at the primary section envelope. Each member end belongs to at most one node. Moving a connected endpoint moves the linked endpoints in the same transaction.

A node contains independent member references and their setbacks, plus a list of independently keyed additions. Plates, bolt groups and screw groups are separate addition kinds. Screw pilot diameters may be smaller than the shaft; bolt clearance holes cannot be smaller than the shaft. Every member gets a derived trim plane; fastening groups add derived circular cuts. Hole previews use twelve-sided cylindrical approximations and cadkernel subtraction; the editable definition retains the exact nominal diameter.

Select the purple node cross in plan or an addition in 3D. The properties panel edits member setbacks and each addition's dimensions, grid, position, host member and axis, and can remove an addition. Offsets are relative to the current primary endpoint in world-axis directions; axis components are dimensionless. New additions initially target the second member. Plates default to 12 mm; bolt groups to 20 mm shafts with 22 mm holes; screws to 6 mm shafts, 4 mm pilot holes and 40 mm length. These are editable geometric defaults, not design prescriptions.

## Persistence and exchange

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
