# Rectangular system evaluator: first native vertical slice

**Decision question:** can a version-pinned definition/occurrence produce bounded,
deterministic construction intents and a native ceiling with one logical-cell replacement?

This slice implements an in-memory v1 evaluator and a create-only native adapter. It is
independent of the design/catalogue PR #26 and starts from main `cfaf116d`. It changes only
owned pattern code and fixtures; no editor, serializer, model record, kernel or connection
API changes. Full editable occurrence persistence and in-place regeneration remain open.

## Inputs and identities

`pattern/common/bim_system_evaluation.dl` owns definition, occurrence, cell-replacement,
part-intent and result records. Integer lengths are millimetres. Occurrence elevation is
relative to its host storey. Definition ID and version must match the occurrence's pinned
reference; only definition version 1 is supported. Library immutability/migration storage
is not implemented by a mutable in-memory record.

The first domain is an axis-aligned rectangle of reference centrelines. Pitches are exact
whole modules; frame width leaves positive clear infills. Support and infill have distinct
semantic paths. Periodic axes start at ordinal zero. A cell uses `occurrence/infill/grid/uN-vM`,
never a row-major array index. A replacement names that pair of axes and declares a bound
component/material/thickness, nominal module and caller-confirmed support compatibility.
The evaluator does not independently prove that engineering compatibility.

Before emitting anything, the evaluator refuses missing IDs, unsupported/mismatched
versions, unavailable capability/bindings, invalid dimensions, odd-millimetre joints,
partial edge modules, excessive axes/parts/replacements, unresolved cells, conflicting
bindings or duplicate targets. Limits: at most 1000 axes per direction, 10000 parts and
64 replacements; IDs/material labels/binding references are limited to 256 bytes. Rejections contain a diagnostic and an empty output list. Results own
their `parts` list; callers free it. Input lists are borrowed and never modified.

A 4800 x 3000 rectangle with 600 mm pitches, 24 x 38 mm support sections and 15 mm
mineral-fibre infills produces 15 member intents and 40 infill intents. The cell between
U2/U3 and V2/V3 has a 576 x 576 mm clear area; its 40 mm LED diffuser is an illustrative
component, not a certified luminaire. Extending V to 3600 creates a sixth row and retains
exactly one replacement at the same logical cell.

## Native boundary

`pattern/common/bim_system_materialization.dl` evaluates/validates before touching the
model, verifies the storey and creates one existing native system with planar types. It
uses numeric section/grid inputs, not a legacy recipe index or a catalogue display name.
A call creates a new placement and refuses an already-placed occurrence ID without model
changes; it is not an in-place update command.
The caller owns the transaction.

The adapter maps U/V cell ordinals to the existing native panel indices. Logical cell keys,
occurrence ID and pinned definition provenance survive as ordinary custom properties in
`OpenBIM_RectangularGeneration`. This is output provenance/selection mapping, not a new
shared file schema or a serialized editable definition graph. The six-row file has native
part code 2014 for the same logical LED cell that is code 2012 in the five-row file.

Existing system rendering supplies the visible rectangular profiles and panels. Profile
intersections remain the generic existing approximation; no hangers, continuity priorities,
connection resolution, supplier sections or actual luminaire support design are delivered.
The domain is a centreline reference rectangle, not a robust clipping boundary for the
outermost profile volume. Native semantic classification still follows the existing carrier.

## Reproduction

Configure `DYNLEX_ROOT` or `.dynlex-root.local`, then run one compiler at a time:

```sh
bash build.sh bundle system_evaluation system_materialization
```

The pure evaluation fixture checks deterministic output, logical replacement survival
across a row-count change and atomic diagnostic refusal. The native fixture checks actual
derived part/material counts, model-level atomic refusal, one-transaction Undo/Redo,
semantic mapping and IFCX reopening. It writes these separate demonstrator models:

- `build/generated-ceiling-4800x3000.ifcx`
- `build/generated-ceiling-4800x3600.ifcx`

Open either in the native desktop application. Existing builds can display the generated
file; that does not mean their UI contains the new generator command. Do not operate the
user's already-open document to verify these files: use independent processes/copies.

## Remaining boundary

Arbitrary contours/holes, clipping, negative/manual axes, rotations/slopes, multiple layers,
regions, recursion, connection intents, stock/residual planning, library bindings, migration,
editable input persistence and regeneration of an existing host remain follow-ups. New
vertex/edge/face picking is coordinated with the editor owner in issue #30; generating
semantic keys here does not implement that interaction.

**Verdict:** the pure evaluator establishes a bounded native intent graph with logical-cell
replacement; native materialization must be confirmed by the focused combined fixture and
a separate desktop-open check before this slice is reported complete.
