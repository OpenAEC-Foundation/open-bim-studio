# `precision-set`

**Question (R-17):** does a candidate kernel give the same answer for the same geometry placed
500 km from the origin as it does at the origin? 500 km is a plausible distance from a national
projection's false origin to a project site, so this is not a synthetic extreme.

**Pass / fail** are fixed in [`../../docs/risks.md`](../../docs/risks.md) R-17, written before any
driver ran: pass is a maximum deviation below 1e-6 m; fail is above 1e-4 m — which for a float32
path is the expected outcome and is the evidence ADR-0006 needs.

The cases are fixed in [`../../reference/precision_set.py`](../../reference/precision_set.py):
three cases reused verbatim from the boolean torture set, each carrying
`OFFSET = (500000.0, 500000.0, 0.0)`.

## Layout

```
occt_driver.py         the OCCT driver (reuses the helpers in ../boolean-torture/occt_common.py,
                       so the construction method is identical between the two spikes)
blender_driver.py      the Blender driver (runs inside Blender's own Python)
results/<candidate>.md raw results, one file per candidate
FINDINGS.md            assembled across candidates once they have all run
```

## Running the OCCT driver

```bash
pip install cadquery-ocp==8.0.1.0.0      # bundles OCCT 8.0.1
python spikes/precision-set/occt_driver.py
```

from the repository root. It writes [`results/occt.md`](results/occt.md).

The driver builds each case twice — once at the origin, once with the offset applied to the input
coordinates, which is what a real project does — runs the boolean on both, translates the far
result back by −offset, and reports the worst nearest-neighbour vertex distance and the volume
difference. Matching is nearest-neighbour rather than by index, because a kernel is free to emit
vertices in any order.

Operands are rebuilt for every repeat at both locations: `BOPAlgo` mutates its arguments by default,
so reusing one pair would compare a near result from pristine operands against a far result from
operands a dozen booleans old.

## Running the Blender driver

```bash
"C:/Program Files/Blender Foundation/Blender 5.0/blender.exe" --background \
    --factory-startup --python spikes/precision-set/blender_driver.py -- --repeats 5
```

from the repository root. It writes [`results/blender.md`](results/blender.md). Operands are
rebuilt for every repeat, every solver and both locations here as well.

For a candidate that stores vertex positions in **float32**, the question is decided before any
boolean runs, so this driver reports three things rather than one:

1. the float32 round trip of the coordinates themselves — write, read back, compare — which is the
   storage cost with no algorithm involved;
2. the boolean result near vs. far, matched nearest-neighbour after translating back;
3. the same far case with the 500 km carried by the **object transform** instead of the vertex
   data, which measures whether a local frame rescues the result — the mitigation ADR-0006
   proposes, measured on the candidate instead of assumed.

## Rules

Spike code is throwaway (see [`../README.md`](../README.md)).
