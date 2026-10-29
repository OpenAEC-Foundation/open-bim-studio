# Independent rectangular change preview

**Decision question:** can a taller ceiling proposal retain both logical LED
cells while leaving the original native host and document untouched?

`pattern/common/bim_system_preview.dl` returns a separate proposal document.
It is stacked on PR #33's read-only inspection and PR #32's InputV1 adapter.
It does not regenerate an existing host or add a shared editor command.

## Proposal boundary

The caller supplies an existing host/model, proposed InputV1 JSON and external
runtime capability/binding availability. Before creating any output, the helper
requires the source's documented host-local footprint to agree with its stored
input and validates the proposal through the existing bounded codec/evaluator.

The occurrence identity and the entire pinned definition must stay unchanged.
Redefining material, pitch, section, binding or other definition content under
the same version is refused. This first preview can change occurrence extents,
relative elevation and part budget; it is not a definition-migration mechanism.

Every existing replacement must remain at its U/V target with the same declared
component, material, thickness, nominal module and support flag. Omission or
implicit modification requires a separate policy and is refused. Array order
does not define identity. Additional explicit replacements are allowed within
the evaluator's limits. Unresolved targets, insufficient budgets, unsupported
input and unavailable runtime capabilities/bindings emit a diagnostic and an
empty proposal model. Caller-declared support is still not engineering proof.

## Independent document

Successful output owns a fresh native model with one host on a copy of the
selected storey's name/elevation/height, minimum native authoring defaults and
the proposed InputV1. It does not copy the rest of the source document or its
unrelated metadata. No source setter, transaction or Undo operation is used.
The original host ID, geometry and metadata remain in the source document.

The proposed model uses the same semantic occurrence identity in a separate
document. Numeric IDs are document-local; they are not global references or a
merge protocol. Combining the documents or applying the proposal to the source
requires a separately coordinated update command. Existing create-only duplicate
occurrence refusal is not bypassed here.

A 4800 x 3600 mm ceiling becomes a separate 4800 x 4200 mm proposal. The two
LED targets stay at `ceiling-json-a/infill/grid/u1-v1` and `u5-v3`. Their native
part codes change from **2007/2033** to **2008/2038** as the row count changes.
The proposal contains 2 LED panels, 54 tiles and 17 frame members. This differs
from retaining the original row-major panel indices after a manual span edit.

The helper's source inspection remains host-local and cannot establish all
historical edits or external relations. That does not authorize overwriting
the source. No shared warning overlay, click-to-preview workflow, corner/side
handles, in-place regeneration, general polygons or product certification are
delivered by this module.

## Reproduction and evidence

Run one compiler at a time:

```sh
bash build.sh test system_preview
```

The fixture checks retained semantic targets and native bindings/counts,
unchanged source bytes, independent output tables, deterministic proposals,
native serialization, omitted/changed overrides, definition/identity policy,
new replacements, reordered input, invalid domains/budgets and runtime gates.
It writes separate native demonstrators and the complete proposed input:

- `build/preview-source.bim`
- `build/preview-proposal.bim`
- `build/preview-proposal-input-v1.json`

Implementation `33c9c3b417e47fb94e72ca50d8a76c36606a16d7` passes **26 native
assertions**, with exact expected output and **zero diagnostic bytes**. Command
duration: **1:26.71**, including this worktree's kernel archive; peak RSS
**709008 KiB**, one compiler. Later changes are documentation only.
Toolchain SHA-256:
`e1127c229b1b934d59b5950489fba0ef11255bc18a6b33ce51862bce21baf3af`.

Artifact SHA-256 values:

- Test binary: `7b621cbefe1f921a416513d5d140c77d9b0bae6b6a383ad9f077571b32eb479b`.
- Source native model: `36406e36a6190a5b6bbe58bc335b852f572091e3a0cb1606e321fcaa13660db7`.
- Proposal: `3903b95fb93cbee62762683cce0fcdbfabdd201e05ea7fa5b4a96816f4b15a1f`.
- Proposed input: `39ee988cf4183ca2aeaa8d9ab040c6f4ee120f4d620b0055878a694acc2043f1`.

Both native files also opened in separate existing Linux desktop processes on
app binary `2b58b0f`. The API returns the complete 808-byte snapshots, equal to
their authored source/proposal JSON, and the same two semantic cell keys. Native
picking confirms LED material on parts **2007/2033** in the source and
**2008/2038** in the proposal. The proposal was visually checked in 3D and left
open in a separate process; the temporary source-verification process was closed.
Existing user windows were not operated. These are output-compatibility checks;
the old app does not acquire a preview command or regeneration behaviour.

**Verdict:** the taller proposal retains both logical LED replacements in a
separate native document, with the original native data unchanged. Applying it
to the existing host and improving visible shape-handle selection remain
coordinated work with the editor owner in issues #22 and #30.
