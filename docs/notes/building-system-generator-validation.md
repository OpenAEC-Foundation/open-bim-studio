# Building System Generator design and planning validation

**Scope:** design/content foundation and isolated native planning primitives, not completion
of the generator UI. Coordination: [#22](https://github.com/OpenAEC-Foundation/open-bim-studio/issues/22).

## Source

The implementation/content commit tested is `8a871ec3ae4ed851021d1b96343ac3e4b48aa01e`,
based on main `cfaf116d`. Later documentation-only commits do not change that native fixture.
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

The 48 recipes remain authoring data. No native importer, new live menu choices, complete
manufacturer pack, new shared model store or UI integration is claimed. The
[design delivery matrix](../domain/building-system-generator.md#15-delivery) names the
remaining vertical slices and acceptance fixtures.
