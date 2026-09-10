# `boolean-torture`

**Question (R-16):** does a candidate kernel's boolean survive coplanar faces, shared edges,
touching vertices, identical operands, containment, a near-zero-thickness slab, a near-degenerate
triangle and a wall cut by twelve openings — producing a valid closed result each time, with
`V(A∪B) + V(A∩B) = V(A) + V(B)`?

**Pass / fail** are fixed in [`../../docs/risks.md`](../../docs/risks.md) R-16, written before any
driver ran: pass is every case valid and the volume identity within 1e-9 relative; fail is any
invalid result or a volume error above 1e-6 relative.

The cases are fixed in [`../../reference/boolean_torture_set.py`](../../reference/boolean_torture_set.py)
and are the same ten pairs for every candidate. A driver may not add, drop or adjust a case.

## Layout

```
occt_common.py        shared OCCT helpers (mesh -> solid, boolean, volume, tolerance)
occt_driver.py        the OCCT driver
blender_driver.py     the Blender driver (runs inside Blender's own Python)
results/<candidate>.md raw results, one file per candidate, written by that candidate's driver
FINDINGS.md           assembled across candidates once they have all run
```

`FINDINGS.md` is written from the `results/` files, not from a single run.

## Running the OCCT driver

```bash
pip install cadquery-ocp==8.0.1.0.0      # bundles OCCT 8.0.1
python spikes/boolean-torture/occt_driver.py
```

from the repository root. It writes [`results/occt.md`](results/occt.md) and prints a one-line
summary. `--repeats N` changes how many times each boolean is timed (the fastest is reported);
**each repeat rebuilds its operands**, because `BOPAlgo` mutates its arguments by default and a
loop over one pair would time progressively degraded input (Probe B measures exactly that).

Besides the torture set the driver runs four probes into the same results file:

| Probe | Question |
|---|---|
| A | Does fuzzy tolerance growth compound over a chain of booleans? |
| B | Does a boolean raise the tolerance of its *input* shapes? |
| C | Is a sewing tolerance below `Precision::Confusion()` honoured? (BREP output hashed) |
| D | How thin a solid will `BRepPrimAPI_MakeBox` build? |

The construction method — triangle soup to `TopoDS_Solid` — is documented in `occt_common.py` and
is part of the measurement: a case whose operands OCCT cannot build is a finding about OCCT.

## Running the Blender driver

```bash
"C:/Program Files/Blender Foundation/Blender 5.0/blender.exe" --background \
    --factory-startup --python spikes/boolean-torture/blender_driver.py -- --repeats 5
```

from the repository root. It writes [`results/blender.md`](results/blender.md).
`--factory-startup` is **not optional**: without it every add-on in the user's configuration is
loaded into the measured process. Blender's boolean modifier is non-destructive, but the driver
still **rebuilds both operand objects for every solver, every operation and every repeat**, so no
measurement can inherit state — including anything a previous `Mesh.validate()` changed.

Each case runs against all three solvers the 5.0 RNA exposes (`EXACT`, `FLOAT`, `MANIFOLD`) for
union and intersection. Besides the torture set the driver runs five probes into the same file:

| Probe | Question |
|---|---|
| A | Does the Fast solver's *Overlap Threshold* change what happens to the 1e-7 m `sliver`? |
| B | What does each solver do with a twelve-shell cutting tool, including `DIFFERENCE`? |
| C | What do `use_self` and `use_hole_tolerant` cost when the input does not need them? |
| D | `touching_vertex`: which solver loses an operand, and does perturbing the contact fix it? |
| E | Is a solver's output identical across repeated runs of identical input? |

The construction method is part of the measurement here too, and differs deliberately from the
OCCT driver where the representations differ: `wall_with_openings` B is built as **one mesh object
with twelve disconnected shells** — the natural reading of the benchmark for a mesh kernel —
where the OCCT driver had to sew it into a compound of twelve solids.

## Rules

Spike code is throwaway (see [`../README.md`](../README.md)). Standard library plus the candidate's
own bindings only; nothing here is a design proposal for `kernel/`.
