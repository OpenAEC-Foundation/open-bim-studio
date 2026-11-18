# ADR-0018 — Keep model validation in `bim/` and stop rebuilding IFCX documents through text

**Status:** proposed
**Date:** 2026-11-18
**Deciders:** the maintainer (proposed; not yet accepted)

## Context

Opening an IFCX or IFCXB document runs two readers for one document. The
importer (`exchange/ifcx/bim_ifcx_read.dl`, `the bim native text of ifcx`) maps
every `openbim::` record in the JSON value tree back to a `.bim` text line, and
the native parser (`exchange/ifcx/bim_file.dl`, `the bim model parsed from`)
tokenises those lines again and builds the `bim model record`:

```
bytes -> JSON value tree -> .bim text -> tokens -> model
```

The text step buys nothing on this path: the JSON tree already holds the same
records with the same values in the same order. It also means the JSON writer is
a prerequisite for binary reading, and that model construction is reachable only
through a text parser.

The model-wide checks are in the middle of this. Ids ascending, unique and below
`next`; references that resolve; wall types with layers; one connection node per
member end; dimension features that belong to their element — none of these are
properties of a file format. They sat inside the text parser, so any second
reader would have had to copy them.

This is the separation requested in issue #161, and it supports ADR-0010
(IFCX as the reference schema).

## Decision

Model invariants live in `bim/`, not in a format reader, and every reader that
produces a `bim model record` validates through them.

`bim/bim_validation.dl` holds `the bim reference fault of`: empty when the model
is sound, otherwise the first fault, worded for the user. The `.bim` parser
calls it after its line loop and keeps no copy of its own.

The IFCX importer follows: it maps `openbim::` records straight to typed records
through one shared logical mapping, then calls the same function. Until that
mapping exists the text bridge stays, because a half-converted reader would
either lose record kinds or bypass validation — both worse than the current
double conversion.

The reader that writes IFCX will use the same mapping, so that writing stops
generating JSON text for a CBOR encoder to re-read.

## Options considered

### Option A — keep the text bridge and share nothing
Cheapest, and what main does today. Rejected because every new reader has to
reach the model through a text parser, and the invariants stay duplicated or
unavailable. It also makes the JSON writer a prerequisite for binary reading.

### Option B — shared validation in `bim/`, then one logical mapping used by both encoders — chosen
`bim/` owns the invariants; `exchange/ifcx` owns syntax, the mapping and the
codecs; `ui/editor` keeps its readiness rules. Validation is called once per
read, on the finished model, by both the text and the IFCX routes. The rejected
alternative inside this option was to validate per record as it is constructed:
it cannot see cross-record facts (unique ids, member ends) and would have to run
twice.

### Option C — a generic document model between all formats
Rejected. It would give every format a common graph, at the cost of a universal
document model that the issue explicitly does not ask for, and it would move
IFCX composition semantics into a layer that knows nothing about them.

### Option D — dump runtime structs for the binary path
Rejected. Bytes-in-memory-layout would skip the logical contract, break on any
layout change and bypass validation entirely.

## Evidence

| Claim | Where shown | Evidence type |
|---|---|---|
| The `.bim` parser's model-wide checks are self-contained and reachable from `bim/` | this change: `bim/bim_validation.dl`, parser calls it | measured (compiles; tests below) |
| Moving the checks leaves the `.bim` and IFCX routes behaving as before | `psets`, `sheets`, `demo_pavilion`, `stairs`, `views`, `network` pass | measured (app `f62b051` + this branch, DynLex 0.0.3, sha256 `f8c86666c32fc6f3…`) |
| IFCX opening currently serialises and reparses `.bim` text | `the bim native text of ifcx` -> `the bim model parsed from` | inferred (code) and claimed (issue #161) |
| Direct construction needs the per-record construction written once, not twice | generator is ~314 lines, parser ~970 lines for the same records | inferred (code) |

## Consequences

**What this makes easier:** a second reader can be written without a text
detour; the invariants have one home and one wording; the editor's readiness
rules stay separate from IFCX validity.

**What this makes harder:** `bim/` now depends on nothing new but is on the
critical path for every reader, so a change to the checks is a change to every
format. `docs/OWNERS.md` makes that a `bim/` pull request of its own.

**What this commits us to:** keeping model invariants out of format readers, and
running the shared check on every completed model.

**What we would have to change to reverse it:** move `the bim reference fault of`
back into `bim_file.dl` and import the parser from the importer. Nothing else
depends on the function.

## Sources

- [Issue #161 — Separate native IFCX model construction from JSON/CBOR serialization](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/161)
- [ADR-0010 — IFCX as the reference schema](0010-ifcx-as-the-reference-schema.md)
- `docs/OWNERS.md` — module owners and the `bim/` change rule
