# Read-only agreement with rectangular authoring input

**Decision question:** can the generator identify disagreement between its
stored InputV1 and the corresponding native host without changing that host?

`pattern/common/bim_system_inspection.dl` adds a host-local inspection. It is
stacked on PR #32's creation-input adapter. It does not regenerate, repair,
delete or update the inspected document, and adds no shared editor command,
model-record or serializer field.

## Compared footprint

The inspector validates the stored InputV1, then creates a reference in an
independent scratch model through the existing create adapter. It compares:

- Native start/finish, span, U/V pitches, straightness and frame material.
- Every host setting, refusing missing, extra or duplicate settings. This
  includes the local ceiling elevation, joints, panel assignments and moved axes.
- Referenced planar types by role and ordered layer material/thickness.
  Native IDs and generated display names are deliberately not identities.
- Every property in `OpenBIM_RectangularGeneration`, including semantic cell
  mappings, type tags and the decoded/canonical InputV1. Properties outside this
  set are left out of this footprint.

Missing hosts/storeys, unsupported input and unresolved panel types produce
diagnostic refusals. Nested/layer systems and openings depending on the host
are conservatively refused because the isolated v1 reference cannot express
those relations. Numerical comparison uses an absolute tolerance of 1e-9 metres;
non-finite differences do not satisfy that comparison. No approximate visual
match or material-count heuristic is used as a substitute for these checks.

## What a match means

`matches` means the inspected host-local state agrees with the **currently
stored input**, not that no person has ever edited it. Rewriting both input and
geometry consistently can agree. An equivalent planar type with a different ID
can agree. This is not an audit trail or proof of original provenance.

InputV1 stores elevation relative to a caller-chosen storey, not its ID or world
elevation. The inspector verifies that the current storey exists; it does not
diagnose moving a host to an equivalent storey or moving the storey itself.
Unrelated annotations, phasing, selection state, arbitrary external references
and manual-edit intent need separate policy. A positive result is explicitly
**not regeneration authorization** and does not resolve capability/licensing
policy. The caller must not use it to bypass the pending regeneration agreement
in issue #22 or the selection work in issue #30.

The reference creates fresh IDs/types in its own model only. The source model
is borrowed; no transaction or Undo entry is added. Scratch placement and parse
refusal remain subject to the existing input/evaluator budgets. Inspection scans
the relevant native model tables and does not claim constant cost on large files.

## Reproduction

Run one compiler at a time:

```sh
bash build.sh test system_inspection
```

The fixture exercises an untouched host with independent native IDs, native
serialization/parse, model-byte preservation, shape/grid/material/type/settings
drift, invalid input/references, semantic metadata, unsupported dependencies and
unrelated metadata. It writes two inspectable native files:

- `build/inspection-baseline.bim`: creation footprint.
- `build/inspection-manual-span.bim`: a manual 3600-to-4200 mm span change with
  the original InputV1 retained, which the inspector refuses without repair.

The manual example intentionally preserves existing native part assignments;
it does not demonstrate semantically correct in-place regeneration. Open only
copies or independent app processes, preserving active user windows.

## Validation and verdict

Implementation and fixture head `ee3fe7101f175e27d279ac2a7a5694155093c0b3`
passes **29 native assertions**, with exact expected output and **zero diagnostic
bytes**. Command duration: **1:26.27**, including this worktree's kernel archive;
peak RSS **709236 KiB**, one compiler. Later changes are documentation only.
Toolchain SHA-256:
`e1127c229b1b934d59b5950489fba0ef11255bc18a6b33ce51862bce21baf3af`.

The fixture isolates candidates using `the bim snapshot of`, not a plain model
record assignment, and clones the shared layer list before editing a type.
It confirms that the original serialized model remains identical after every
candidate check. The demonstrators include the window/door authoring defaults
required by the existing desktop loader, even for a ceiling-only model.

Artifact SHA-256 values:

- Test binary: `d26b82fbfb301564b8ddebcfb68c03070fa1407e405bd0bb0e61ec194a99633b`.
- Baseline: `75bc98d55cf8cc7accc1df99aa7901ca57f8ca27a83518f1c35bf30abdba5828`.
- Manual span edit: `aced5658be9146470cf8bccc95459f1afd461f1827ac374926628821fb22289a`.

Both native files also opened in separate existing Linux desktop processes on
app binary `2b58b0f`. The API confirms actual spans of 3.6 and 4.2 metres while
both retain InputV1's original 3600 mm span. The manual example is left visible
in 3D; the temporary baseline process was closed. Existing user windows were
not operated. This checks file compatibility and visible output; the old app
does not acquire an inspection command or warning overlay from this module.

**Verdict:** the compared host-local footprint can be checked without rewriting
the inspected document, and the manual span discrepancy is diagnosed. This is
not complete protection of arbitrary manual edits. Safe mutating regeneration
and visible shape-handle editing remain separate coordinated work.
