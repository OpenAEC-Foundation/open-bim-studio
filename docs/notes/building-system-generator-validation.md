# Building System Generator design and planning validation

**Scope:** design/content foundation and isolated native planning primitives, not completion
of the generator UI. Coordination: [#22](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/22).

## Source

The initial implementation/content commit tested is `8a871ec3ae4ed851021d1b96343ac3e4b48aa01e`,
based on main `cfaf116d`. The expanded catalogue and native reader are validated separately below.
The existing application test repair is a separate [PR #24](https://github.com/OpenAEC-Foundation/open-bim-studio/pull/24).

## Native checks

[Linux planning run 40787327672](https://github.com/OpenAEC-Foundation/dynlex/actions/runs/40787327672)
compiled `pattern/common/tests/system_planning.dl` at `-O0`, ran the binary and compared its
output byte-for-byte with the committed expectation. **All nine assertions passed**, with an
empty compiler diagnostic file. This fixture imports standard libraries and the new planning
module only; it does not compile or exercise the full application.

The compiler artifact is from [run 40773371392](https://github.com/OpenAEC-Foundation/dynlex/actions/runs/40773371392):
DynLex `c2d32bea` plus the application's six existing patches, binary SHA-256
`a5e0723adb8d4171312f6d68118bfe305e8ec1fecb0d116f54666ac9aeb5348d`.
The runner restores it at its embedded `/home/runner/work/dynlex/dynlex` source prefix;
runtime archives are built from the same compiler source. The validation job is a build-only
workflow in the compiler fork, with no new compiler behaviour. It does not start a second
compiler on the local machine while the separate application/check bundle is compiling.

Measured cases:

- Equal zero-gap candidate units: 7200 with maximum 3300 gives 3 × 2400; exact 6600 gives
  2 × 3300; insufficient unit budget or invalid lengths refuse.
- Full-length rectangular strip cuts: 597 → 250 plus 3 kerf leaves 344; taking 340 plus 3
  kerf from that remainder leaves 1. Installed + kerf + remaining width reconciles to 597.
- Exact-fit stock requires no cut; oversize demand and negative kerf refuse; a blade overrun
  beyond a free edge consumes only available stock, never producing a negative residual.
- Rectangular remnant fit requires dimensions plus caller-supplied edge and direction
  compatibility; a geometric fit alone is insufficient.

These are candidate/feasibility primitives. They do not solve opening exclusion zones,
bearings, mass/transport, polygon nesting, rotations, edge-state derivation, stock reservations,
procurement or connections. There is no claim of global cutting optimality.

## Catalogue and repository checks

- Catalogue validation passed: 48 concept recipes, 10 families, nine scoped sources.
- Eight independently corrupted copies were refused: missing family, duplicate identity,
  tile module mismatch, brick course mismatch, unsubstantiated performance claim, nonfinite
  dimension, missing shared zone and unknown capability. These checks run on copies, not by
  changing the published catalogue.
- `scripts/check-layers.sh` passed: new native module imports only the standard library.
- `git diff --check` passed.

The initial 48 recipes were authoring data. The current expanded catalogue has a native
metadata reader as described below. No new live placement choices, complete manufacturer
pack, shared model store or UI integration is claimed. The
[design delivery matrix](../domain/building-system-generator.md#15-delivery) names the
remaining vertical slices and acceptance fixtures.

## Catalogue expansion and native metadata access

Implementation commit `77a2734c3373540d8e77a19f108a8b0076adba25` expands the catalogue
to **183 concept presets, 43 families, 83 substitution interfaces and 13 sources**.
All original 48 preset records were compared and retained unchanged. Every family
substitution resolves to an interface; disabling lining is an operation rather than
an invented substitute component. The complete inventory is in
[`localisation/nl/building-systems/INDEX.md`](../../localisation/nl/building-systems/INDEX.md).

The native reader loads bounded metadata, validates recipe shape/identity/family/status,
offers stable-ID lookup and checks caller-supplied available capabilities. It owns one
parsed document; lookup results borrow that storage. Releasing the same holder repeatedly
is safe. It does not place elements, resolve layer offsets, design structures/MEP,
validate a complete manufacturer assembly or certify a generated system.

Measured checks:

- Local native `system_catalogue`: **10 assertions PASS**, exact output, no diagnostics.
  It reads the actual complete catalogue and checks all 183 recipe records, stable-ID and
  absent-ID lookup, capability gating, malformed JSON/root refusal, unknown family refusal,
  duplicate identity refusal, unsupported approval refusal and safe release.
- Local combined `system_catalogue system_planning` bundle: **both PASS**, 19 assertions
  in one compile unit, exact output and no diagnostics. Same native-prefix compiler
  `e1127c...` as recorded in the editing-validation note.
- Independent [Linux run 40801970154](https://github.com/OpenAEC-Foundation/dynlex/actions/runs/40801970154):
  same implementation commit, pinned CI-prefix compiler `a5e0723...`; both isolated native
  fixtures PASS with exact output and empty diagnostic files.
- Authoring validation passes. Seven malformed copies are refused: missing substitution,
  inconsistent interface usage, duplicate ports, missing family, duplicate preset ID,
  unsubstantiated performance claim and invalid dimension. No published data was corrupted.
- Layer checks and whitespace checks pass; native metadata code imports standard libraries only.

This establishes native access to the content library, not activation of all 183 definitions
in the modelling interface. Geometry generation still needs the declared capabilities,
actual product/parameter bindings, compatible host/ports and model transactions.
