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
Editing the raw property does not regenerate geometry. A future regeneration
command must coordinate host identity, transactions and override policy with
the editor owner before claiming synchronized interactive editing.

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

Implementation `42c4718` passes the 18 focused codec assertions with exact
expected output and empty diagnostics. The combined native bundle is pending;
its intended checks above must not be read as a recorded pass.
