# Parametric steel connections

Connection nodes refer to member ids and semantic ends, never generated faces.
Each end has at most one owner. A primary host-axis reference is non-owning and
stores a fraction along the axis, allowing several secondary beams to meet a
continuous column or girder. Moving/resizing that host follows this fraction;
editing a secondary does not move its continuous primary.

Select the primary steel member, then Shift-select the secondary, and open the
**Connections** ribbon. The steel recipes provide **End plate**, **Fin plate**,
**Double cleat**, **Splice**, **Gusset**, and **End cap**. A splice needs opposite
collinear members; an end cap takes one member and starts at its finish end.
The existing Butt, Miter, custom multi-member node and Base plate remain available.
The flat recipes support I-sections, solid rectangular sections and SHS/RHS.
Splices require matching, aligned sections. End plates and cleats require a
normal approach to a profile face; fin plates and gussets seat their edges and
welds on the supporting face when the member slopes. A member intersecting
primary I-section flanges is refused with a request for a cope/different joint.
Custom nodes no longer impose the previous six-member limit. The predefined
crossing recipes take two members; base plates/end caps take one.

Select a node to edit plate sizes, fastening grids, setbacks and weld parameters
in Properties. Recipe part coordinates use the secondary section's frame: X
width, Y depth, Z inward from its participating end. Rotating the member also
rotates parts and grids. Fin/gusset plate and weld positions are projected onto
the supporting face; the plate centroid follows the member slope. Primary
profile contact uses its actual outer contour, so web connections do not float
at the flange bounding envelope. Axial cleat bolts attach to the primary; a
splice has one web through-bolt group and distributes holes between both halves. The node's Status reports failed geometry conditions;
invalid connection parts are withheld. A host's twist/taper must be zero/one
for these steel recipes. Fillet and butt welds retain their own kind, nominal
size and length; they do not generate bolt holes or heads. Their preview uses
nominal rectangular beads, not prepared weld grooves or verified throat solids.

Rename an edited recipe in Properties and choose **Save type**. **Next type**
cycles through the project's named types (the status message names the choice).
Select new hosts and choose **Apply type**. Each application remaps member slots
and owns copies of its editable parameters. Saving/applying types and editing
nodes participate in undo. A failed application does not consume ids or leave
an incomplete node. Named types persist in native files and the IFCX native
connection payload; they are not live-linked instances.

## Steel hall example

Open [examples/steel-connection-hall.bim](examples/steel-connection-hall.bim) with
the new application build. This synthetic 18 x 12 m hall has four transverse
frames: eight HEB 260 columns, eight IPE 400 half-girders, twelve IPE 200
longitudinal members and four SHS 80x80x5 diagonal braces. Sixty connection
nodes use the six recipes and base plates; 52 weld runs and the independent
plates, bolts and anchors are derived from those nodes. One named fin-plate
type is reused on twelve hosts. The DynLex generator is
`overlay/examples/bim-slice/bim_demo_steel_hall.dl` and the `steel_hall` test
regenerates the editable example without Python BIM logic.

## Persistence and regeneration

Legacy five-field `connectionmember` lines remain readable. New records add an
explicit host fraction; end references use zero. `connectiontype`,
`connectiontypemember` and `connectiontypepart` hold the named library. Addition
kinds 4 and 5 are fillet/butt welds. Styles 0/1/2 retain Butt/Miter/Base plate;
3 through 8 denote the six recipes in the order listed above. Older builds
may reject files using these new records. The full project contains its own
library, with no reference to a workstation-local preset path.

Host, profile and level changes dirty the connection nodes and participating
members in the model journal. The viewport retains unchanged connection solids
across edits. Loading a model or changing history replaces the journal and
invalidates that cache. Other scene objects still follow their existing rebuild
path; this does not claim model-wide incremental meshing or a 100k-member
latency target. Hollow member cavities are subtracted before bolt drilling, so
drilling an SHS/RHS/CHS does not fill its interior.

## Scope and validation

These are editable modelling recipes, not checked structural designs. Bolt,
weld and plate defaults do not establish resistance, buckling, fatigue, minimum
code edge distances or fabrication readiness. The gusset is rectangular; weld
beads, rods and heads are simplified. Base-plate anchor holes remain nominal
parameters in the existing recipe. Cope/notch, fish-mouth and welded CHS K-joint
recipes remain outstanding in issue #6, as do concrete/timber catalogues and
model-wide dependency indexing. The issue is not closed by this increment.

Headless suites cover recipe parameters, distinct parts, host-axis references,
ownership, movement, undo, named-type persistence and native exact round trips.
Geometry tests compare cut volumes, including a hole through both walls of a
hollow section. Full application and cache test results belong in the build
report; they must not be inferred from headless parameter checks.

Public commands: 2320–2325 recipes, 2326/2327 fillet/butt weld, 2328 Save type,
2329 Apply type, 2330 Next type. Property 8998 edits the node name. Global
setting 2400500 stores the chosen library type id. Existing part properties
10000+20*i and removal 50000+i remain in use.
