# Versioned rectangular authoring input

The rectangular generator can create a ceiling from a bounded InputV1 JSON
document, retaining that document as a deterministic native property snapshot.
This builds on PR #31's evaluator and create-only materialization adapter.
It does not introduce an interactive generator command or update an existing host.

## Authoring boundary

`pattern/common/bim_system_input.dl` parses and encodes definitions, occurrences
and cell replacements. `pattern/common/examples/ceiling-input-v1.json` is a
complete example: a 4800 x 3600 mm ceiling with 600 mm modules and illustrative
LED replacements at U1/V1 and U5/V3. Those semantic cell coordinates survive
serialization; they are not renderer part-array indices.

The root fields are exactly `schema_version`, `units`, `definition`, `occurrence`
and `replacements`. Version 1 requires integer millimetres and `units: "mm"`.
The example lists the required nested fields. Unknown, duplicate and missing
fields are refused. There are no optional serialized capability flags: runtime
capability and binding availability are supplied separately by the caller.
Support compatibility remains a caller declaration, not engineering certification.

Input is limited to 32768 bytes, nesting depth eight and 64 replacements. Text
fields must contain 1–256 bytes without ASCII control characters. Numeric
lexemes must be exact integers in the range -1000000 to 1000000; individual
dimensions and budgets undergo the evaluator's stricter validation. Decimal and
exponent forms are refused, including mathematically integral forms. A depth
preflight runs before the general recursive JSON parser. Quoted braces do not
contribute to nesting. Parse refusal does not mutate the native model.

Encoding uses fixed field order and preserves authored replacement-array order.
Repeated encoding is byte deterministic; semantically equivalent permutations
of the replacement array are not sorted into one representation. JSON quoting
is handled by the existing writer. The encoded byte bound is checked after
escaping. No timestamps, filesystem paths or runtime capability flags are added.
Callers own the decoded replacement list and free it once.

## Native persistence and rebuilding

`place bim input …` in `pattern/common/bim_system_input_placement.dl` validates
and encodes before placement. A successful create stores exactly one ordinary
`IfcText` property named `InputV1` in `OpenBIM_RectangularGeneration`, using the
existing public property setter. This boundary was approved by the editor owner
in [issue #22](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/22#issuecomment-6487422169).
There are no shared model-record, serializer or property-panel changes. The long
JSON property remains visible in existing property panels.

The caller owns the transaction. The snapshot participates in the same native
Undo/Redo and IFCX save/open mechanisms as the generated geometry. Repeating the
same occurrence ID is refused; it neither duplicates nor replaces that host.
The fixture rebuilds a separate fresh document from the reopened snapshot.
Editing the raw property does not regenerate geometry. Likewise, existing native
geometry edits do not rewrite the snapshot: it describes the creation input,
not a proven live correspondence after manual edits. Drift detection and
reconciliation are not implemented. A future regeneration command must
coordinate host identity, transactions and override policy with the editor owner
before claiming synchronized interactive editing. Selection-handle work on
existing native systems must not silently treat this snapshot as current after
changing their geometry.

## Reproduction and scope

Run one compiler at a time:

```sh
bash build.sh bundle system_input system_input_placement
```

The codec fixture covers round trips, deterministic escaping and atomic refusal
of unsupported versions/units/fields/numbers, oversized/deep trees and encoded
expansion beyond the byte budget. The native fixture covers actual part counts,
snapshot type and uniqueness, refusal without native mutation, Undo/Redo, IFCX
reopening and rebuilding both semantic LED targets from persisted input. It writes
`build/input-v1-ceiling.ifcx` and `build/input-v1-ceiling-rebuilt.ifcx`.

These are illustrative generic ceiling components. They do not provide supplier
bindings, certified luminaires, arbitrary contours, openings, connection design,
in-place regeneration or the requested corner/side selection handles. That
selection interaction is coordinated separately in issue #30.

## Validation

Implementation `42c4718` passes the combined Linux bundle: **30 assertions**
(18 codec and 12 native placement), exact expected output and **zero diagnostic
bytes**. The command took **20:21.00**, including this worktree's kernel archive,
with peak RSS **2617608 KiB** and one compiler. Later source changes are
documentation only. Toolchain SHA-256:
`e1127c229b1b934d59b5950489fba0ef11255bc18a6b33ce51862bce21baf3af`.

Measured artifact SHA-256 values:

- Bundle: `fe7cdd6e1c6234ae49810c3ab46e0b46212f1568412a02e68c8ab6210106e89b`.
- Created IFCX: `710c4b90c14ef254814cccd1320adda9a815b5ceb736d958a4cd0665b5ba0901`.
- Rebuilt IFCX: `0cc67d074ae461e5bebf80ced896145996c623f15c91dcf623b8869cc8bddb4a`.

Both IFCX files also passed independent desktop reopening in the existing Linux
app binary from `2b58b0f`. Its automation API returned the complete 808-byte
snapshot, equal to the authored JSON data, and both semantic cell properties.
Picking the two intended cells returned native part codes **2007** and **2033**,
each with material `LED diffuser`. The created model was inspected visually in
3D and left open in a separate user-facing process. The rebuilt model's temporary
verification process was closed. Existing user model windows were not operated.
These checks establish output compatibility with that app binary; they do not
add a generator command, new selection handles or synchronized regeneration to it.
